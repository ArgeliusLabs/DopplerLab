"""Make classroom sensitivity manifests beside an existing case; preserve originals."""

import argparse
import copy
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    base = json.loads(args.case.read_text(encoding="utf-8-sig"))
    variants = {}
    one = copy.deepcopy(base)
    one["events"] = one["events"][:1]
    one["title"] = "One flyover: inspect competing explanations"
    variants["one-event"] = one
    for name, speed in [("cold", 331), ("warm", 355)]:
        changed = copy.deepcopy(base)
        changed["sound_speed_m_s"] = speed
        changed["title"] = f"Sound-speed sensitivity: {speed} m/s"
        variants[name] = changed
    paths = [args.case.parent / f"case-{name}.json" for name in variants]
    if any(path.exists() for path in paths):
        parser.error("A variant already exists; preserve it or use a fresh case directory.")
    for path, config in zip(paths, variants.values(), strict=True):
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
