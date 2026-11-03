"""Validate bounded, local cases before numerical work begins."""

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .physics import Track


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path(root, name):
    if not isinstance(name, str):
        raise ValueError("Case paths must be strings.")
    resolved = (root / name).resolve()
    if Path(name).is_absolute() or not resolved.is_relative_to(root.resolve()):
        raise ValueError("Case inputs must be relative paths inside the case directory.")
    if not resolved.is_file():
        raise ValueError(f"Missing case input: {name}")
    return resolved


def axis_values(value, name, cap=10000):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{name} must be [minimum, maximum, step].")
    start, stop, step = np.asarray(value, dtype=float)
    if not np.isfinite([start, stop, step]).all() or step <= 0 or stop < start:
        raise ValueError(f"{name}: invalid finite range or step.")
    count = int(np.floor((stop - start) / step + 1e-8)) + 1
    if count > cap:
        raise ValueError(f"{name}: exceeds {cap} samples.")
    return start + np.arange(count) * step


def load_tracks(path, max_gap_s):
    grouped = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"track_id", "time_s", "east_m", "north_m", "up_m"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Track CSV needs columns: {', '.join(sorted(required))}")
        for row in reader:
            name = row["track_id"].strip()
            if not name or len(name) > 128:
                raise ValueError("Track IDs must contain 1 to 128 characters.")
            grouped.setdefault(name, []).append(
                [float(row[key]) for key in ("time_s", "east_m", "north_m", "up_m")]
            )
    tracks = {}
    for name, rows in grouped.items():
        samples = np.asarray(rows)
        # Deliberately do not sort: out-of-order evidence must be repaired explicitly.
        tracks[name] = Track(name, samples[:, 0], samples[:, 1:], max_gap_s)
    if not tracks:
        raise ValueError("Track CSV is empty.")
    return tracks


@dataclass
class Event:
    name: str
    start_s: float
    end_s: float
    source_hz: np.ndarray
    track_ids: list[str]


@dataclass
class Case:
    path: Path
    config: dict
    audio_path: Path
    tracks_path: Path
    tracks: dict
    events: list[Event]
    observers: np.ndarray
    offsets: np.ndarray
    c: float
    hashes: dict


def load_case(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    if config.get("schema_version") != 1:
        raise ValueError("Only case schema_version 1 is supported.")
    if config.get("coordinate_system") != "local_enu_m":
        raise ValueError("Convert tracks and observers to one local_enu_m frame first.")
    if not config.get("provenance") or not config.get("time_basis"):
        raise ValueError("Document provenance and time_basis in the case.")
    audio_path = local_path(path.parent, config["audio"])
    tracks_path = local_path(path.parent, config["tracks"])
    max_gap = float(config.get("max_track_gap_s", 5))
    if not np.isfinite(max_gap) or not 0 < max_gap <= 30:
        raise ValueError("max_track_gap_s must be in (0, 30]; sparse data need review.")
    tracks = load_tracks(tracks_path, max_gap)
    offsets = axis_values(config["clock_offset_s"], "clock_offset_s", 1001)
    c = float(config.get("sound_speed_m_s", 343))
    if not np.isfinite(c) or not 300 <= c <= 370:
        raise ValueError("sound_speed_m_s must be between 300 and 370.")
    hashes = {"case": digest(path), "audio": digest(audio_path), "tracks": digest(tracks_path)}
    if "observers" in config:
        observer_path = local_path(path.parent, config["observers"])
        with observer_path.open(newline="", encoding="utf-8-sig") as stream:
            observers = np.asarray(
                [
                    [float(row[k]) for k in ("east_m", "north_m", "up_m")]
                    for row in csv.DictReader(stream)
                ]
            )
        hashes["observers"] = digest(observer_path)
    else:
        grid = config["grid"]
        east = axis_values(grid["east_m"], "grid.east_m")
        north = axis_values(grid["north_m"], "grid.north_m")
        if len(east) * len(north) > 20_000:
            raise ValueError("Grid exceeds 20,000 points; use a smaller local study area.")
        observers = np.array([[e, n, float(grid.get("up_m", 0))] for n in north for e in east])
    if (
        observers.ndim != 2
        or observers.shape[1] != 3
        or not len(observers)
        or not np.isfinite(observers).all()
    ):
        raise ValueError("Observers must be finite N x 3 coordinates.")
    if len(observers) > 20_000 or np.max(np.linalg.norm(observers, axis=1)) > 50_000:
        raise ValueError("This local solver supports <=20,000 observers within 50 km of origin.")
    events = []
    for item in config["events"]:
        start, end = float(item["start_s"]), float(item["end_s"])
        if not np.isfinite([start, end]).all() or start < 0 or end - start < 10:
            raise ValueError("Each event needs a finite, nonnegative window >=10 seconds.")
        frequencies = axis_values(item["source_hz"], "source_hz", 201)
        if frequencies[0] <= 20 or frequencies[-1] >= 1800:
            raise ValueError("Source tones must be in (20, 1800) Hz.")
        ids = item["track_ids"]
        if not ids or len(set(ids)) != len(ids) or any(x not in tracks for x in ids):
            raise ValueError("Event has empty, duplicate, or unknown track IDs.")
        events.append(Event(str(item["name"]), start, end, frequencies, ids))
    if not 1 <= len(events) <= 4 or len({e.name for e in events}) != len(events):
        raise ValueError("Use one to four uniquely named independent flyovers.")
    ordered = sorted(events, key=lambda e: e.start_s)
    if any(a.end_s > b.start_s for a, b in zip(ordered, ordered[1:], strict=False)):
        raise ValueError("Independent event windows must not overlap; harmonics are one event.")
    alternatives = int(np.prod([len(e.track_ids) for e in events]))
    if alternatives > 256:
        raise ValueError("More than 256 flight assignments; narrow candidate tracks first.")
    work = len(observers) * len(offsets) * sum(len(e.track_ids) * len(e.source_hz) for e in events)
    if work > 20_000_000:
        raise ValueError("Search exceeds 20 million line trials; narrow the grid/clock/tones.")
    return Case(
        path, config, audio_path, tracks_path, tracks, events, observers, offsets, c, hashes
    )
