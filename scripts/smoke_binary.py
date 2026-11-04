"""Exercise the bundled executable from outside the source tree, without PYTHONPATH."""

import argparse
import gzip
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def terrain_fixture(root):
    """Small invented DEM/geoid; no network and no real elevation-data dependency."""
    folder = root / "fictional terrain"
    (folder / "grids").mkdir(parents=True)
    values = (400 + np.arange(64)[:, None] + np.arange(64)[None, :]).astype("float32")
    for name, crs, transform, data in [
        ("dem.tif", "EPSG:4269", from_origin(-110.83, 32.33, 0.001, 0.001), values),
        (
            "grids/geoid.tif",
            "EPSG:4326",
            from_origin(-112, 34, 0.5, 0.5),
            np.full((8, 8), -30, dtype="float32"),
        ),
    ]:
        with rasterio.open(
            folder / name,
            "w",
            driver="GTiff",
            width=data.shape[1],
            height=data.shape[0],
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(data, 1)
            if "geoid" in name:
                dst.update_tags(TYPE="VERTICAL_OFFSET_GEOGRAPHIC_TO_VERTICAL")
                dst.set_band_description(1, "geoid_undulation")

    def record(path):
        return {
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    info = {
        "schema_version": 1,
        "status": "complete",
        "provider": "fictional native fixture",
        "source_crs": "EPSG:5498",
        "target_crs": "EPSG:4979",
        "bounds": [32.27, -110.825, 32.325, -110.77],
        "sampling": "bilinear",
        "limitations": ["Invented DEM/geoid; never use for real observations."],
        "tiles": [record(folder / "dem.tif")],
        "operation": {
            "axis_order": "latitude_longitude_height",
            "accuracy_m": 0,
            "pipeline": "+proj=pipeline +step +proj=axisswap +order=2,1 "
            "+step +proj=unitconvert +xy_in=deg +xy_out=rad "
            "+step +proj=vgridshift +grids=geoid.tif +multiplier=1 "
            "+step +proj=unitconvert +xy_in=rad +xy_out=deg "
            "+step +proj=axisswap +order=2,1",
            "grids": [record(folder / "grids/geoid.tif")],
        },
    }
    (folder / "terrain.json").write_text(json.dumps(info), encoding="utf-8")
    return folder


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
            try:
                return subprocess.run(
                    [str(executable), *items],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=180,
                )
            except subprocess.CalledProcessError as error:
                print(error.stdout or "", flush=True)
                print(error.stderr or "", file=sys.stderr, flush=True)
                raise

        print(run("--version").stdout.strip())
        terrain_fixture(root)
        point = json.loads(
            run(
                "terrain-point",
                "fictional terrain",
                "--latitude",
                "32.3195",
                "--longitude",
                "-110.8195",
                "--microphone-height",
                "2",
            ).stdout
        )
        assert abs(point["receiver_height_ellipsoid_m"] - 392) < 1e-5
        run(
            "prepare-observers",
            "fictional terrain",
            "--bounds",
            "32.29",
            "-110.81",
            "32.31",
            "-110.79",
            "--spacing-m",
            "500",
            "--output",
            "observers",
        )
        prepared = json.loads((root / "observers/observers.json").read_text())
        assert prepared["status"] == "complete" and prepared["observer_count"] > 4
        run("capture-adsb", "--help")
        run("normalize-adsb", "--help")
        run("download-day", "--help")
        run("download-window", "--help")
        run("review-media", "--help")
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
            "--terrain",
            "fictional terrain",
            "--output",
            "screen",
        )
        run(
            "subset-index",
            "index/index.sqlite",
            "--bounds",
            "32.295",
            "-110.805",
            "32.305",
            "-110.795",
            "--output",
            "subset",
        )
        screening = json.loads((root / "screen/screening.json").read_text())
        assert screening["status"] == "complete" and screening["counts"]["candidates"] > 0
        assert screening["terrain"]["provider"] == "fictional native fixture"
        run(
            "filter-candidates",
            "screen",
            "--speed-a",
            "70",
            "90",
            "--speed-b",
            "70",
            "90",
            "--slant-a",
            "800",
            "1500",
            "--slant-b",
            "800",
            "1500",
            "--output",
            "filtered",
        )
        filtered = json.loads((root / "filtered/screening.json").read_text())
        assert filtered["status"] == "complete" and filtered["counts"]["candidates"] > 0
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
            "Bundled CLI passed: DEM/geoid reading, observers, archive indexing, terrain shortlist, handoff, audio inspection, matching and report."
        )


if __name__ == "__main__":
    main()
