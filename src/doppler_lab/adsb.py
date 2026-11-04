"""Bounded ADS-B acquisition and explicit readsb geographic normalization."""

import csv
import hashlib
import json
import math
import re
import ssl
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import certifi

from . import __version__
from .importers import parse_utc

API = "https://api.adsb.lol/v2/point"
LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"


def utc(value=None):
    return datetime.fromtimestamp(time.time() if value is None else value, UTC).isoformat()


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def new_folder(path):
    path = Path(path)
    if path.exists():
        raise ValueError(f"Choose a new output directory: {path}")
    path.mkdir(parents=True)
    return path


def capture(output, latitude, longitude, radius_nm=20, duration_s=600, interval_s=10):
    """Keep original response text, timestamps, errors and hashes; no audio capture."""
    if not number(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be finite and within [-90, 90].")
    if not number(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be finite and within [-180, 180].")
    if type(radius_nm) is not int or not 1 <= radius_nm <= 25:
        raise ValueError("Use an integer radius from 1 to 25 nautical miles for a local case.")
    if not number(duration_s) or not 2 <= duration_s <= 1800:
        raise ValueError("Capture duration must be 2 to 1800 seconds.")
    if not number(interval_s) or not 2 <= interval_s <= 10:
        raise ValueError("Polling interval must be 2 to 10 seconds.")
    output = new_folder(output)
    url = f"{API}/{latitude:.6f}/{longitude:.6f}/{radius_nm}"
    manifest = {
        "schema_version": 1,
        "provider": "adsb.lol-v2",
        "url": url,
        "attribution": "Aircraft data from adsb.lol; ODbL 1.0, separate from the code license.",
        "license_url": LICENSE_URL,
        "started_utc": utc(),
        "duration_requested_s": duration_s,
        "interval_s": interval_s,
        "tool_version": __version__,
        "snapshots": 0,
        "errors": [],
        "status": "capturing",
    }
    log = output / "snapshots.jsonl"
    start, consecutive_errors = time.monotonic(), 0
    try:
        with log.open("x", encoding="utf-8", newline="\n") as stream:
            while time.monotonic() - start < duration_s:
                request_start = time.monotonic()
                requested = utc()
                try:
                    request = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": f"ArgeliusDopplerLab/{__version__}",
                            "Accept": "application/json",
                        },
                    )
                    with urllib.request.urlopen(
                        request,
                        timeout=15,
                        context=ssl.create_default_context(cafile=certifi.where()),
                    ) as response:
                        body = response.read(10_000_001)
                    if len(body) > 10_000_000:
                        raise ValueError("Provider response exceeds 10 MB.")
                    received = utc()
                    data = json.loads(body)
                    if not isinstance(data, dict) or not isinstance(data.get("ac"), list):
                        raise ValueError("Unexpected provider response; expected v2 ac array.")
                    now = data.get("now")
                    if not number(now) or abs(now / 1000 - parse_utc(received)) > 60:
                        raise ValueError(
                            "Provider timestamp is stale or local clock differs by over 60 s."
                        )
                    record = {
                        "requested_utc": requested,
                        "received_utc": received,
                        "body_sha256": hashlib.sha256(body).hexdigest(),
                        "body_utf8": body.decode("utf-8"),
                    }
                    stream.write(json.dumps(record, allow_nan=False) + "\n")
                    stream.flush()
                    manifest["snapshots"] += 1
                    consecutive_errors = 0
                except (OSError, ValueError, urllib.error.URLError) as error:
                    manifest["errors"].append({"utc": utc(), "error": str(error)})
                    consecutive_errors += 1
                    if isinstance(error, urllib.error.HTTPError) and error.code in {401, 403, 429}:
                        raise ValueError(
                            f"Provider returned HTTP {error.code}; stopped without retrying."
                        ) from error
                    if consecutive_errors >= 3:
                        raise ValueError(
                            "Three consecutive acquisition errors; capture stopped."
                        ) from error
                remaining = duration_s - (time.monotonic() - start)
                delay = interval_s - (time.monotonic() - request_start)
                if remaining > 0 and delay > 0:
                    time.sleep(min(delay, remaining))
        manifest["status"] = "complete"
    except KeyboardInterrupt:
        manifest["status"] = "interrupted"
    except (OSError, ValueError):
        manifest["status"] = "failed"
        raise
    finally:
        manifest["ended_utc"] = utc()
        manifest["elapsed_s"] = round(time.monotonic() - start, 3)
        manifest["snapshots_sha256"] = (
            hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None
        )
        (output / "capture.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    return manifest


def capture_points(source, counts):
    """V2 now is milliseconds; seen_pos is seconds. Never use local receipt as fix time."""
    with Path(source).open(encoding="utf-8-sig") as stream:
        for line in stream:
            record = json.loads(line)
            body = record["body_utf8"].encode("utf-8")
            if hashlib.sha256(body).hexdigest() != record["body_sha256"]:
                raise ValueError("Capture response hash mismatch.")
            data = json.loads(body)
            now = data.get("now")
            if not number(now) or not 1e12 <= now <= 4e12:
                raise ValueError("Expected v2 now in Unix milliseconds.")
            for ac in data.get("ac", []):
                counts["input_points"] += 1
                age = ac.get("seen_pos")
                if not number(age) or not 0 <= age <= 3:
                    counts["stale_or_missing_position_age"] += 1
                    continue
                fields = set(ac.get("mlat") or []) | set(ac.get("tisb") or [])
                yield {
                    "icao": ac.get("hex"),
                    "time": now / 1000 - age,
                    "lat": ac.get("lat"),
                    "lon": ac.get("lon"),
                    "height_ft": ac.get("alt_geom"),
                    "source": ac.get("type"),
                    "ground": ac.get("alt_baro") == "ground",
                    "break": False,
                    "derived": bool(fields & {"lat", "lon", "alt_geom"}),
                }


def trace_points(source, counts):
    """readsb trace: timestamp + point[0]; geometric height is point[10] or flag 8."""
    from .archive import stream_trace

    with Path(source).open("rb") as stream:
        with stream_trace(stream) as data:
            yield from trace_records(data, counts)


def trace_records(data, counts):
    """Decode one trace object without assuming its on-disk compression suffix."""
    if not isinstance(data, dict) or "trace" not in data or not hasattr(data["trace"], "__iter__"):
        raise ValueError("Expected a readsb trace object, not a map export or snapshot.")
    epoch = data.get("timestamp")
    if not number(epoch) or not 1e9 <= epoch <= 4e9:
        raise ValueError("Expected trace timestamp in Unix seconds.")
    for point in data["trace"]:
        counts["input_points"] += 1
        if not isinstance(point, list) or len(point) < 9 or not number(point[0]):
            counts["malformed_trace_point"] += 1
            continue
        flags = point[6]
        if type(flags) is not int or flags & 1:
            counts["stale_or_invalid_trace_flags"] += 1
            continue
        extra = point[8] if isinstance(point[8], dict) else {}
        geometric = point[10] if len(point) > 10 else None
        if geometric is None and flags & 8:
            geometric = point[3]
        # Never carry an earlier point's altitude/source into a later point.
        source_type = point[9] if len(point) > 9 else extra.get("type")
        yield {
            "icao": data.get("icao"),
            "time": epoch + point[0],
            "lat": point[1],
            "lon": point[2],
            "height_ft": geometric,
            "source": source_type,
            "ground": point[3] == "ground",
            "break": bool(flags & 2),
            "derived": False,
        }


def normalize(
    sources, output, source_format, start_utc, end_utc, bounds, max_gap_s=5, conflicts="error"
):
    """Export a geographic CSV and audit; discontinuities get distinct segment IDs."""
    start, end = parse_utc(start_utc), parse_utc(end_utc)
    if not 0 < end - start <= 3600:
        raise ValueError("Select a time window greater than zero and no longer than one hour.")
    if len(bounds) != 4 or not all(number(x) for x in bounds):
        raise ValueError("Bounds must be south west north east in decimal degrees.")
    south, west, north, east = bounds
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("Bounds must be ordered south west north east; no dateline wrapping.")
    if not number(max_gap_s) or not 0 < max_gap_s <= 30:
        raise ValueError("Maximum gap must be in (0, 30] seconds.")
    if source_format not in {"capture", "readsb-trace"}:
        raise ValueError("Choose capture or readsb-trace format.")
    if conflicts not in {"error", "quarantine"}:
        raise ValueError("Conflicts policy must be error or quarantine.")
    sources = [Path(p) for p in sources]
    if not sources or any(not p.is_file() for p in sources):
        raise ValueError("Supply existing capture JSONL or trace JSON/JSON.GZ files.")
    counts, grouped = Counter(), defaultdict(list)
    reader = capture_points if source_format == "capture" else trace_points
    for path in sources:
        for point in reader(path, counts):
            if not start <= point["time"] <= end:
                counts["outside_time"] += 1
                continue
            if not number(point["lat"]) or not number(point["lon"]):
                counts["missing_position"] += 1
                continue
            if not south <= point["lat"] <= north or not west <= point["lon"] <= east:
                counts["outside_bounds"] += 1
                continue
            if point["source"] != "adsb_icao" or point["derived"]:
                counts["unsupported_position_source"] += 1
                continue
            if point["ground"]:
                counts["ground"] += 1
                continue
            if not number(point["height_ft"]) or not -2000 <= point["height_ft"] <= 65000:
                counts["missing_or_invalid_geometric_height"] += 1
                continue
            if not isinstance(point["icao"], str) or not re.fullmatch(
                r"[0-9a-fA-F]{6}", point["icao"]
            ):
                counts["invalid_icao"] += 1
                continue
            grouped[point["icao"].lower()].append(point)
    segments = []
    quarantined = []
    for icao, points in sorted(grouped.items()):
        points.sort(key=lambda p: p["time"])
        collisions = [
            a["time"]
            for a, b in zip(points, points[1:], strict=False)
            if a["time"] == b["time"]
            and (a["lat"], a["lon"], a["height_ft"]) != (b["lat"], b["lon"], b["height_ft"])
        ]
        if collisions:
            if conflicts == "error":
                raise ValueError(
                    f"Conflicting positions at one timestamp for {icao}; review sources."
                )
            quarantined.append(
                {
                    "icao": icao,
                    "conflicting_times_utc": [utc(t) for t in sorted(set(collisions))],
                    "excluded_points": len(points),
                }
            )
            counts["quarantined_conflicting_aircraft"] += 1
            counts["quarantined_points"] += len(points)
            continue
        current, number_segment, last_position = [], 0, None

        def finish(aircraft_id=icao):
            nonlocal current, number_segment
            if len(current) >= 4 and current[-1]["time"] - current[0]["time"] >= 10:
                number_segment += 1
                segments.append((f"{aircraft_id}-s{number_segment:03d}", current))
            elif current:
                counts["short_segment_points"] += len(current)
            current = []

        for point in points:
            position = (point["lat"], point["lon"], point["height_ft"])
            if current and point["time"] == current[-1]["time"]:
                if position != last_position:
                    raise ValueError(
                        f"Conflicting positions at one timestamp for {icao}; review sources."
                    )
                counts["duplicate_fix"] += 1
                continue
            if current and (point["break"] or point["time"] - current[-1]["time"] > max_gap_s):
                finish()
            if current and position == last_position:
                counts["repeated_position"] += 1
                continue
            current.append(point)
            last_position = position
        finish()
    output = new_folder(output)
    geographic = output / "geographic.csv"
    with geographic.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["track_id", "timestamp_utc", "latitude_deg", "longitude_deg", "height_ellipsoid_m"]
        )
        for name, points in segments:
            for p in points:
                writer.writerow(
                    [name, utc(p["time"]), p["lat"], p["lon"], f"{p['height_ft'] * 0.3048:.4f}"]
                )
    summary = {
        "schema_version": 1,
        "format": source_format,
        "tool_version": __version__,
        "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "window_utc": [utc(start), utc(end)],
        "bounds_south_west_north_east": bounds,
        "max_gap_s": max_gap_s,
        "conflicts_policy": conflicts,
        "quarantined_aircraft": quarantined,
        "counts": dict(counts),
        "exported_points": sum(len(p) for _, p in segments),
        "segments": [
            {
                "track_id": n,
                "points": len(p),
                "start_utc": utc(p[0]["time"]),
                "end_utc": utc(p[-1]["time"]),
                "max_gap_s": max(b["time"] - a["time"] for a, b in zip(p, p[1:], strict=False)),
            }
            for n, p in segments
        ],
        "geographic_sha256": hashlib.sha256(geographic.read_bytes()).hexdigest(),
        "warnings": [
            "Trajectory preparation only; no audio association or location has been validated.",
            "Snapshot geometric altitude has no separate age field; contemporaneity is unverified.",
            "Quantized, noisy or simplified positions can corrupt derived velocity; inspect curves.",
            "Use source-specific data terms and attribution; exported provider data is not MIT.",
            "Quarantined aircraft are omitted alternatives, not evidence of aircraft absence.",
        ],
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
