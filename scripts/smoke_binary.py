"""Exercise the bundled executable from outside the source tree, without PYTHONPATH."""

import argparse
import gzip
import io
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve()
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    with tempfile.TemporaryDirectory(prefix="doppler-native-smoke-") as directory:
        root = Path(directory)
        env["MPLCONFIGDIR"] = str(root / "matplotlib")

        def run(*items):
            return subprocess.run(
                [str(executable), *items],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=180,
            )

        print(run("--version").stdout.strip())
        run("capture-adsb", "--help")
        run("normalize-adsb", "--help")
        run("download-day", "--help")
        with tarfile.open(root / "traces.tar", "w") as archive:
            for identity, offset, north in [("a00001", 0, False), ("a00002", 920, True)]:
                points = []
                for t in range(0, 182, 2):
                    distance = (t - 90) * 80
                    lat = 32.3 + (distance / 110900 if north else 0)
                    lon = -110.8 + (
                        0 if north else distance / (111320 * math.cos(math.radians(32.3)))
                    )
                    points.append(
                        [t + offset, lat, lon, 4500, 155, 0, 0, 0, None, "adsb_icao", 1400 / 0.3048]
                    )
                raw = gzip.compress(
                    json.dumps(
                        {"icao": identity, "timestamp": 1793620800, "trace": points}
                    ).encode()
                )
                member = tarfile.TarInfo(f"traces/01/trace_full_{identity}.json")
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
        run(
            "index-archive",
            "traces.tar",
            "--bounds",
            "32.29",
            "-110.81",
            "32.31",
            "-110.79",
            "--start",
            "2026-11-02T12:00:00Z",
            "--end",
            "2026-11-02T13:00:00Z",
            "--output",
            "index",
        )
        run(
            "shortlist",
            "index/index.sqlite",
            "--interval",
            "920",
            "--grid-km",
            "1",
            "--receiver-height",
            "400",
            "--output",
            "screen",
        )
        screening = json.loads((root / "screen/screening.json").read_text())
        assert screening["status"] == "complete" and screening["counts"]["candidates"] > 0
        run(
            "export-candidate",
            "index/index.sqlite",
            "screen",
            "--candidate",
            "1",
            "--output",
            "handoff",
        )
        run("demo", "--output", "case")
        run("inspect", "case/recording.wav", "--output", "inspection.png")
        run("run", "case/case.json", "--output", "report", "--quiet")
        result = json.loads((root / "report" / "results.json").read_text())
        top = result["rows"][0]
        assert result["accepted_location"] is False
        assert [event["track_id"] for event in top["events"]] == ["A", "B"]
        assert (top["east_m"], top["north_m"]) == (100, -200)
        assert "data:image/png;base64," in (root / "report" / "report.html").read_text(
            encoding="utf-8"
        )
        print(
            "Bundled CLI passed: archive indexing, shortlist, handoff, audio inspection, matching and report."
        )


if __name__ == "__main__":
    main()
