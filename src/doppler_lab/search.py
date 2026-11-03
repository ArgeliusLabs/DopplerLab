"""Exhaustive search over a declared local grid and one shared recording clock."""

import itertools
import time

import numpy as np

from .audio import line_scores, read_audio, spectrogram


def prepare(case):
    fs, audio, metadata = read_audio(case.audio_path, channel=case.config.get("channel", 0))
    settings = case.config.get("spectrogram", {})
    spec = spectrogram(audio, fs, **settings)
    indices = []
    for event in case.events:
        if event.end_s > metadata["duration_s"]:
            raise ValueError(f"Event {event.name} extends beyond the recording.")
        ix = np.flatnonzero((spec.times >= event.start_s) & (spec.times <= event.end_s))
        if len(ix) < 20 or (spec.times[ix[-1]] - spec.times[ix[0]]) < 0.9 * (
            event.end_s - event.start_s
        ):
            raise ValueError(f"Event {event.name}: not enough complete FFT windows.")
        indices.append(ix)
    return spec, indices, metadata


def search(case, spec=None, indices=None, progress=None):
    started = time.perf_counter()
    if spec is None:
        spec, indices, metadata = prepare(case)
    else:
        metadata = {"note": "Caller supplied a control spectrogram."}
    tracks = {name: track.sample() for name, track in case.tracks.items()}
    for track in tracks.values():
        if np.any(np.linalg.norm(track.velocities, axis=1) >= 0.9 * case.c):
            raise ValueError(f"Track {track.name} has unsupported interpolation velocity.")
    assignments = [
        combo
        for combo in itertools.product(*(e.track_ids for e in case.events))
        if len(set(combo)) == len(combo)
    ]
    if not assignments:
        raise ValueError("No assignment uses distinct tracks for independent events.")
    rows, evaluated, unsupported = [], 0, 0
    for number, observer in enumerate(case.observers):
        curves = {key: track.propagation(observer, case.c)[:2] for key, track in tracks.items()}
        best = None
        for offset in case.offsets:
            event_choices = []
            for event, ix in zip(case.events, indices, strict=True):
                choices = {}
                for track_id in event.track_ids:
                    arrival, ratios = curves[track_id]
                    ratio = np.interp(
                        spec.times[ix] + offset, arrival, ratios, left=np.nan, right=np.nan
                    )
                    evaluated += len(event.source_hz)
                    if not np.isfinite(ratio).all():
                        unsupported += len(event.source_hz)
                        continue
                    scores = line_scores(spec, ix, ratio, event.source_hz)
                    unsupported += int(np.count_nonzero(~np.isfinite(scores)))
                    k = int(np.argmax(scores))
                    if np.isfinite(scores[k]):
                        choices[track_id] = {
                            "name": event.name,
                            "track_id": track_id,
                            "source_hz": float(event.source_hz[k]),
                            "contrast_db": float(scores[k]),
                        }
                event_choices.append(choices)
            for assignment in assignments:
                if not all(
                    key in options for key, options in zip(assignment, event_choices, strict=True)
                ):
                    continue
                events = [
                    options[key] for key, options in zip(assignment, event_choices, strict=True)
                ]
                score = float(np.mean([event["contrast_db"] for event in events]))
                if best is None or score > best["score_db"]:
                    best = {
                        "east_m": float(observer[0]),
                        "north_m": float(observer[1]),
                        "up_m": float(observer[2]),
                        "clock_offset_s": float(offset),
                        "score_db": score,
                        "events": events,
                    }
        if best is not None:
            rows.append(best)
        if progress and (number % 50 == 0 or number == len(case.observers) - 1):
            progress(number + 1, len(case.observers))
    rows.sort(key=lambda row: row["score_db"], reverse=True)
    warnings = [
        "Scores are line contrast, not probabilities or calibrated confidence.",
        "This is a bounded hypothesis search, not a verified location.",
        "Source tone is assumed constant within each event; wind is not modeled.",
    ]
    if unsupported:
        warnings.append(
            "Some line trials were unsupported. Missing alternatives limit conclusions."
        )
    if len(case.events) == 1:
        warnings.append("One event can leave mirror locations and clock/location ambiguity.")
    if metadata.get("clipped_sample_fraction", 0) > 0.001:
        warnings.append("Audio has samples near full scale; inspect clipping before interpreting.")
    if rows and min(e["contrast_db"] for e in rows[0]["events"]) < 3:
        warnings.append("At least one event has weak contrast (<3 dB heuristic, uncalibrated).")
    if rows:
        top = rows[0]
        for axis, column in (("east_m", 0), ("north_m", 1)):
            extent = case.observers[:, column]
            if np.ptp(extent) > 0 and top[axis] in (min(extent), max(extent)):
                warnings.append(f"Leading point touches the {axis} search boundary.")
        if len(case.offsets) > 1 and top["clock_offset_s"] in (case.offsets[0], case.offsets[-1]):
            warnings.append("Leading clock offset touches the declared search boundary.")
        for event, fitted in zip(case.events, top["events"], strict=True):
            if len(event.source_hz) > 1 and fitted["source_hz"] in (
                event.source_hz[0],
                event.source_hz[-1],
            ):
                warnings.append(f"{event.name}: fitted source tone touches its search boundary.")
    status = "hypothesis_only" if rows else "no_supported_candidate"
    return (
        {
            "schema_version": 1,
            "status": status,
            "accepted_location": False,
            "candidate_count": len(case.observers),
            "supported_candidate_count": len(rows),
            "clock_trials_per_candidate": len(case.offsets),
            "line_trials_evaluated": evaluated,
            "unsupported_line_trials": unsupported,
            "elapsed_s": time.perf_counter() - started,
            "audio_metadata": metadata,
            "analysis_settings": {
                "model_sample_step_s": 0.25,
                "analysis_sample_rate_hz": 4000,
                "core_offsets_hz": [-0.5, 0, 0.5],
                "flank_offsets_hz": [-6, 6],
                "frame_contrast_clip_db": [-30, 30],
                "sound_speed_m_s": case.c,
                "window_s": spec.window_s,
                "hop_s": spec.hop_s,
            },
            "track_diagnostics": {
                name: {
                    "max_interpolated_speed_m_s": float(
                        np.max(np.linalg.norm(t.velocities, axis=1))
                    ),
                    "max_input_gap_s": float(np.max(np.diff(case.tracks[name].times))),
                }
                for name, t in tracks.items()
            },
            "warnings": warnings,
            "rows": rows,
        },
        spec,
        indices,
    )


def rank_distinct(rows, minimum_separation_m=300, limit=10):
    """Retain spatial alternatives; adjacent grid points are not independent matches."""
    selected = []
    for row in rows:
        if all(
            np.hypot(row["east_m"] - other["east_m"], row["north_m"] - other["north_m"])
            >= minimum_separation_m
            for other in selected
        ):
            selected.append(row)
        if len(selected) >= limit:
            break
    return selected
