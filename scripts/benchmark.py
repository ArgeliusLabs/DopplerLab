"""Re-run the declared search for each condition, including all nuisance fits.

Run from a checkout after installing the package. No truth is sent to search.
"""

import argparse
import copy
import json
import platform
from dataclasses import replace
from pathlib import Path

import numpy as np

from doppler_lab import __version__
from doppler_lab.audio import spectrogram
from doppler_lab.case import load_case
from doppler_lab.report import new_output, write_report
from doppler_lab.search import prepare, search
from doppler_lab.synthetic import create_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = new_output(args.output)
    case = load_case(create_case(output / "case"))
    spec, indices, baseline_metadata = prepare(case)
    conditions = [
        ("baseline", case, spec),
        ("sound-speed-331", replace(case, c=331), spec),
        ("sound-speed-355", replace(case, c=355), spec),
        ("one-event", replace(case, events=case.events[:1]), spec),
        (
            "reversed-time",
            case,
            replace(spec, db=spec.db[:, ::-1], whitened=spec.whitened[:, ::-1]),
        ),
    ]
    for seed in (100, 101, 102):
        audio = np.random.default_rng(seed).normal(0, 0.05, 4000 * 200)
        control = spectrogram(audio, 4000, **case.config["spectrogram"])
        conditions.append((f"noise-{seed}", case, control))
    excluded = replace(
        case, events=[replace(case.events[0], track_ids=["A-decoy"]), case.events[1]]
    )
    conditions.append(("true-first-track-excluded", excluded, spec))
    drift_case = load_case(create_case(output / "drift-case", source_drift_hz=4))
    drift_spec, _, _ = prepare(drift_case)
    conditions.append(("source-drift-4hz-per-minute", drift_case, drift_spec))
    truth = json.loads((case.path.parent / "truth.json").read_text())
    results = []
    for name, trial_case, trial_spec in conditions:
        # Keep exported configuration faithful to the actual numerical inputs.
        config = copy.deepcopy(trial_case.config)
        config["sound_speed_m_s"] = trial_case.c
        config["events"] = config["events"][: len(trial_case.events)]
        for item, event in zip(config["events"], trial_case.events, strict=True):
            item["track_ids"] = event.track_ids
        trial_case = replace(trial_case, config=config)
        result, _, ix = search(trial_case, trial_spec, indices[: len(trial_case.events)])
        top = result["rows"][0]
        error = float(
            np.hypot(
                top["east_m"] - truth["observer_enu_m"][0],
                top["north_m"] - truth["observer_enu_m"][1],
            )
        )
        summary = {
            "condition": name,
            "best_score_db": top["score_db"],
            "minimum_event_score_db": min(e["contrast_db"] for e in top["events"]),
            "east_m": top["east_m"],
            "north_m": top["north_m"],
            "horizontal_error_m": error,
            "clock_offset_s": top["clock_offset_s"],
            "track_ids": [e["track_id"] for e in top["events"]],
            "elapsed_s": result["elapsed_s"],
            "unsupported_trials": result["unsupported_line_trials"],
            "locations_within_2db_of_peak": sum(
                row["score_db"] >= top["score_db"] - 2 for row in result["rows"]
            ),
            "effective_configuration": config,
            "input_sha256": trial_case.hashes,
        }
        results.append(summary)
        print(
            json.dumps(
                {
                    k: v
                    for k, v in summary.items()
                    if k not in ("effective_configuration", "input_sha256")
                }
            ),
            flush=True,
        )
        if name == "baseline":
            result["audio_metadata"] = baseline_metadata
            write_report(trial_case, result, trial_spec, ix, output / "baseline-report")
    record = {
        "version": __version__,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "input_sha256": case.hashes,
        "results": results,
        "note": "Synthetic engineering checks. Three noise controls do not calibrate a false-match "
        "rate. All controls rerun the complete declared grid/clock/tone/track search.",
    }
    (output / "benchmark.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
