"""Explicit geographic/time conversion for user-prepared, licensed track CSVs."""

import csv
from datetime import datetime
from pathlib import Path

import numpy as np

from .physics import geodetic_to_enu


def parse_utc(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Timestamps require Z or an explicit UTC offset.")
    return stamp.timestamp()


def import_tracks(source, destination, origin, time_origin):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError(f"Output already exists: {destination}")
    reference = parse_utc(time_origin)
    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {
            "track_id",
            "timestamp_utc",
            "latitude_deg",
            "longitude_deg",
            "height_ellipsoid_m",
        }
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Import CSV needs {sorted(required)}; pressure altitude is not accepted."
            )
        rows = list(reader)
    if not rows:
        raise ValueError("No track samples to import.")
    xyz = geodetic_to_enu(
        [float(r["latitude_deg"]) for r in rows],
        [float(r["longitude_deg"]) for r in rows],
        [float(r["height_ellipsoid_m"]) for r in rows],
        origin,
    )
    if np.any(np.linalg.norm(xyz, axis=1) > 50_000):
        raise ValueError("Keep this local case within 50 km of its origin; tile larger data.")
    times = [parse_utc(r["timestamp_utc"]) - reference for r in rows]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["track_id", "time_s", "east_m", "north_m", "up_m"])
        for row, t, pos in zip(rows, times, xyz, strict=True):
            writer.writerow([row["track_id"], f"{t:.6f}", *(f"{v:.6f}" for v in pos)])
    return len(rows)
