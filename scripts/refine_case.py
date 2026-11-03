"""Refine a flat local grid around the reported leader, without reading truth."""

import argparse
import json
from pathlib import Path

from doppler_lab.case import digest, load_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    case = load_case(args.case)
    report = json.loads(args.results.read_text(encoding="utf-8"))
    if "observers" in case.config:
        parser.error(
            "Terrain-aware receiver sets require explicit refinement; this helper is flat-only."
        )
    if args.output.exists() or args.output.resolve().parent != case.path.parent:
        parser.error("Output must be a new manifest in the same case directory.")
    if report["input_sha256"]["case"] != digest(args.case) or not report["rows"]:
        parser.error(
            "Results must come from this exact manifest and contain a supported candidate."
        )
    config = dict(case.config)
    best = report["rows"][0]
    grid = {}
    for axis in ("east_m", "north_m"):
        lo, hi, old_step = config["grid"][axis]
        if old_step <= 25:
            parser.error(
                "The source grid is already <=25 m; choose a deliberate further refinement."
            )
        grid[axis] = [max(lo, best[axis] - 150), min(hi, best[axis] + 150), 25]
    grid["up_m"] = best["up_m"]
    config["grid"] = grid
    lo, hi, _ = config["clock_offset_s"]
    clock = best["clock_offset_s"]
    config["clock_offset_s"] = [max(lo, clock - 1), min(hi, clock + 1), 0.25]
    config["title"] = "Local refinement of one candidate mode"
    config["refinement"] = {
        "parent_case_sha256": digest(args.case),
        "parent_results_sha256": digest(args.results),
        "limitation": "Only the leading spatial mode was refined; alternatives remain.",
    }
    args.output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
