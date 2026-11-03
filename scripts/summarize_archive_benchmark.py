"""Publish aggregate benchmark measurements, never provider trajectories or private audio."""

import argparse
import json
import platform
from importlib.metadata import version
from pathlib import Path

from doppler_lab.case import digest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a new benchmark output filename.")
    download = read("work/archive-2026-11-02/download.json")
    if download["status"] != "complete":
        raise ValueError("Download did not complete.")
    rows = []
    for name, measurement, directory, manifest_name in [
        ("conus_index", "bench-conus-index", "conus-2026-11-02-streamed", "index.json"),
        ("europe_index", "bench-europe-index", "europe-2026-11-02-streamed", "index.json"),
        ("tucson_subset", "bench-tucson-subset", "tucson-index-2026-11-02", "index.json"),
        (
            "conus_screen",
            "bench-conus-screen-complete",
            "conus-screen-complete-2026-11-02",
            "screening.json",
        ),
        (
            "europe_screen",
            "bench-europe-screen-complete",
            "europe-screen-complete-2026-11-02",
            "screening.json",
        ),
        ("tucson_screen", "bench-tucson-screen", "tucson-screen-2026-11-02", "screening.json"),
    ]:
        measured = read(f"work/{measurement}.json")
        manifest = read(f"work/{directory}/{manifest_name}")
        if measured["exit_code"] != 0 or manifest["status"] != "complete":
            raise ValueError(f"{name} is not a completed successful run.")
        counts = {key: value for key, value in manifest["counts"].items() if key != "input_parts"}
        row = {
            "stage": name,
            "elapsed_s": measured["elapsed_s"],
            "sampled_peak_rss_bytes": measured["sampled_peak_rss_bytes"],
            "command": measured["command"],
            "counts": counts,
            "manifest_sha256": digest(ROOT / f"work/{directory}/{manifest_name}"),
            "output_bytes": sum(
                p.stat().st_size for p in (ROOT / "work" / directory).iterdir() if p.is_file()
            ),
        }
        for key in [
            "index_bytes",
            "index_sha256",
            "bounds",
            "padding_km",
            "max_gap_s",
            "interval_s",
            "tolerance_s",
            "grid_km",
            "radius_km",
            "receiver_height_m",
            "sound_speed_m_s",
            "speed_bounds_m_s",
            "max_pairs",
            "max_passages",
            "receiver_nodes",
            "passage_generation_s",
            "candidates_sha256",
        ]:
            if key in manifest:
                row[key] = manifest[key]
        if "source_commit" in measured:
            row["source_commit"] = measured["source_commit"]
            row["source_sha256"] = measured["source_sha256"]
        rows.append(row)
    machine = read("work/bench-conus-index.json")
    filtered = read("work/tucson-filter-demonstration/screening.json")
    if filtered["status"] != "complete":
        raise ValueError("Illustrative candidate filtering did not complete.")
    result = {
        "schema_version": 1,
        "tool_version": "0.2.0.dev1",
        "archive_utc_date": "2026-11-02",
        "run_date": "2026-11-03",
        "source_release": download["release_url"],
        "source_license": download["license"],
        "download_bytes": download["received_bytes"],
        "download_elapsed_s": download["elapsed_s"],
        "source_parts": download["parts"],
        "archive_layout": read("work/archive-layout.json"),
        "environment": {
            k: machine[k]
            for k in [
                "platform",
                "processor",
                "logical_cpus",
                "system_ram_bytes",
                "sample_interval_s",
            ]
        },
        "reporting_environment": {
            "python": platform.python_version(),
            "packages": {
                name: version(name)
                for name in ["numpy", "scipy", "matplotlib", "ijson", "certifi", "psutil"]
            },
            "note": "Recorded when aggregating the completed runs, not by each original timing wrapper.",
        },
        "measurements": rows,
        "filter_demonstration": {
            "hypothetical_constraints": True,
            "counts": filtered["counts"],
            "bounds": filtered["filter_bounds"],
            "internal_elapsed_s": filtered["elapsed_s"],
            "timing_scope": "Internal filtering only; excludes CLI startup and input hashing.",
            "source_candidates_sha256": filtered["source_candidates_sha256"],
            "candidates_sha256": filtered["candidates_sha256"],
        },
        "accepted_location": False,
        "audio_validation_performed": False,
        "notes": [
            "Single development runs with warm filesystem caches and other development/benchmark tasks running concurrently.",
            "Indexing measurements began before the final development commit; screening commands record source hashes.",
            "A hypothetical 920-second interval and a flat 0 m ellipsoid receiver height were used for performance testing.",
            "The first US screening pilot was stopped when observed counts projected beyond its 10-million passage budget. Its time is excluded from the successful rerun and partial files remain local.",
            "The earlier full-record JSON reader stopped at its size limit; the measured index runs use the streaming reader.",
            "Peak process-tree RSS is sampled every 0.2 seconds and can miss short-lived peaks.",
            "The global archive is reused; do not charge its download separately for each region.",
            "Only supported full ICAO trace filenames are parsed; other names, including non-ICAO addresses prefixed with ~, are excluded.",
            "Gzip footer sizes describe expanded trace bytes; expanded JSON copies were not written.",
            "These are acquisition and geometric screening measurements, not real-recording location accuracy.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote aggregate measurements to {args.output}")


if __name__ == "__main__":
    main()
