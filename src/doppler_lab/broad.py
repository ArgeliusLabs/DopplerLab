"""Coarse geographic screening by delayed closest approach, with an auditable local handoff.

This is a shortlist generator, not an audio detector or a validated location solver.
It uses piecewise-linear WGS84 ECEF trajectories and a declared receiver height.
"""

import csv
import json
import math
import re
import sqlite3
import time
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from . import __version__
from .adsb import new_folder, number, trace_records, utc
from .archive import archive_traces
from .case import digest
from .importers import import_tracks, parse_utc
from .physics import geodetic_to_ecef, geodetic_to_enu

REGIONS = {"conus": [24, -125, 50, -66], "europe": [34, -25, 72, 45]}
FIELDS = [
    "candidate_id",
    "cell_id",
    "latitude_deg",
    "longitude_deg",
    "receiver_height_m",
    "segment_a",
    "segment_b",
    "icao_a",
    "icao_b",
    "arrival_a_utc",
    "arrival_b_utc",
    "interval_error_s",
    "allowed_error_s",
    "slant_a_m",
    "slant_b_m",
    "speed_a_m_s",
    "speed_b_m_s",
]
INDEX_SCHEMA = """
    CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE segments(id INTEGER PRIMARY KEY, icao TEXT NOT NULL, source_member TEXT NOT NULL,
      start REAL, end REAL, n INTEGER, max_gap REAL, points BLOB NOT NULL);
    CREATE INDEX segment_time ON segments(start,end);
"""


def bounds_check(bounds):
    if len(bounds) != 4 or not all(number(x) for x in bounds):
        raise ValueError("Bounds must be four finite values: south west north east.")
    s, w, n, e = bounds
    if not (-75 <= s < n <= 75 and -180 <= w < e <= 180):
        raise ValueError("Use ordered bounds within 75 degrees latitude; no dateline wrapping.")
    return bounds


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def open_index(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        metadata = json.loads(
            connection.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0]
        )
        if metadata.get("schema_version") != 1 or metadata.get("status") != "complete":
            raise ValueError("Index is incomplete or has an unsupported schema.")
        return connection, metadata
    except BaseException:
        connection.close()
        raise


def unpack(blob, count):
    if not 4 <= count <= 2_000_000:
        raise ValueError("Invalid indexed point count.")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(blob, count * 32 + 1)
    if len(raw) != count * 32 or not decoder.eof or decoder.unused_data:
        raise ValueError("Invalid indexed trajectory payload.")
    points = np.frombuffer(raw, dtype="<f8").reshape(-1, 4)
    if not np.isfinite(points).all() or np.any(np.diff(points[:, 0]) <= 0):
        raise ValueError("Invalid indexed trajectory samples.")
    return points


def build_index(
    parts, output, bounds, start_utc, end_utc, padding_km=30, max_gap_s=30, progress=None
):
    """Stream a global archive to compressed regional segments in SQLite."""
    s, w, n, e = bounds_check(bounds)
    start, end = parse_utc(start_utc), parse_utc(end_utc)
    if not 0 < end - start <= 7 * 86400:
        raise ValueError("Index interval must be positive and at most seven days.")
    if not 0 <= padding_km <= 100 or not 0 < max_gap_s <= 30:
        raise ValueError("Use 0–100 km padding and a maximum gap in (0, 30] seconds.")
    lat_pad = padding_km / 110
    lon_pad = padding_km / (110 * math.cos(math.radians(max(abs(s), abs(n)) + lat_pad)))
    output = new_folder(output)
    db = sqlite3.connect(output / "index.sqlite")
    db.executescript(INDEX_SCHEMA)
    counts = Counter()
    manifest = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "indexing",
        "bounds": bounds,
        "padding_km": padding_km,
        "start_utc": utc(start),
        "end_utc": utc(end),
        "max_gap_s": max_gap_s,
        "created_utc": utc(),
        "source_license": "https://opendatacommons.org/licenses/odbl/1-0/",
    }
    started = time.monotonic()
    identities = set()
    try:
        for name, data in archive_traces(parts, counts):
            counts["trace_files"] += 1
            icao = str(data.get("icao", "")).lower()
            if not re.fullmatch("[0-9a-f]{6}", icao):
                counts["invalid_icao"] += 1
                continue
            # One source archive per index avoids quietly blending replicas or duplicate days.
            if icao in identities:
                raise ValueError(
                    f"Duplicate full trace for {icao}; index one instance/day at a time."
                )
            identities.add(icao)
            current = []

            def finish(aircraft=icao, member=name):
                nonlocal current
                if len(current) >= 4 and current[-1][0] - current[0][0] >= 10:
                    points = np.asarray(current, dtype="<f8")
                    db.execute(
                        "INSERT INTO segments(icao,source_member,start,end,n,max_gap,points) VALUES(?,?,?,?,?,?,?)",
                        (
                            aircraft,
                            member,
                            points[0, 0],
                            points[-1, 0],
                            len(points),
                            float(np.diff(points[:, 0]).max()),
                            zlib.compress(points.tobytes(), 1),
                        ),
                    )
                    counts["segments"] += 1
                    counts["retained_points"] += len(points)
                else:
                    counts["short_segment_points"] += len(current)
                current = []

            for point in trace_records(data, counts):
                reason = None
                if not start <= point["time"] < end:
                    reason = "outside_time"
                elif not number(point["lat"]) or not number(point["lon"]):
                    reason = "missing_position"
                elif not (
                    s - lat_pad <= point["lat"] <= n + lat_pad
                    and w - lon_pad <= point["lon"] <= e + lon_pad
                ):
                    reason = "outside_padded_region"
                elif point["source"] != "adsb_icao" or point["derived"]:
                    reason = "unsupported_position_source"
                elif point["ground"]:
                    reason = "ground"
                elif not number(point["height_ft"]) or not -2000 <= point["height_ft"] <= 65000:
                    reason = "missing_or_invalid_geometric_height"
                if reason:
                    counts[reason] += 1
                    finish()
                    continue
                row = [point["time"], point["lat"], point["lon"], point["height_ft"] * 0.3048]
                if current and row[0] <= current[-1][0]:
                    if row == current[-1]:
                        counts["duplicate_points"] += 1
                        continue
                    counts["nonincreasing_or_conflicting_time"] += 1
                    finish()
                if current and (point["break"] or row[0] - current[-1][0] > max_gap_s):
                    finish()
                current.append(row)
            finish()
            if counts["trace_files"] % 100 == 0:
                db.commit()
                if progress:
                    progress(dict(counts))
        if not counts["segments"]:
            raise ValueError("No usable geometric ADS-B segments; inspect rejection counts.")
        manifest["status"] = "complete"
    except BaseException as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        raise
    finally:
        manifest["elapsed_s"] = round(time.monotonic() - started, 3)
        manifest["counts"] = dict(counts)
        db.execute("INSERT OR REPLACE INTO metadata VALUES('manifest',?)", (json.dumps(manifest),))
        db.commit()
        db.close()
        manifest["index_bytes"] = (output / "index.sqlite").stat().st_size
        manifest["index_sha256"] = digest(output / "index.sqlite")
        write_json(output / "index.json", manifest)
    return manifest


def receiver_grid(bounds, step_m, height_m):
    s, w, n, e = bounds_check(bounds)
    if not 1000 <= step_m <= 20000 or not -500 <= height_m <= 6000:
        raise ValueError("Coarse grid step must be 1–20 km and ellipsoid height -500–6000 m.")
    latitudes = np.unique(np.append(np.arange(s, n, step_m / 111320), n))
    coords = []
    count = 0
    for lat in latitudes:
        lons = np.unique(
            np.append(np.arange(w, e, step_m / (111320 * math.cos(math.radians(lat)))), e)
        )
        count += len(lons)
        if count > 2_000_000:
            raise ValueError(
                "More than two million receiver nodes; increase --grid-km or tile region."
            )
        coords.append(np.column_stack((np.full(len(lons), lat), lons)))
    geographic = np.concatenate(coords)
    xyz = geodetic_to_ecef(geographic[:, 0], geographic[:, 1], height_m)
    return geographic, xyz


def subset_index(index_path, output, bounds):
    """Reuse a completed regional index for a smaller region, keeping boundary context."""
    s, w, n, e = bounds_check(bounds)
    source, parent = open_index(index_path)
    ps, pw, pn, pe = parent["bounds"]
    if not (ps <= s < n <= pn and pw <= w < e <= pe):
        source.close()
        raise ValueError("Subset bounds must stay inside the indexed receiver region.")
    output = new_folder(output)
    destination = sqlite3.connect(output / "index.sqlite")
    destination.executescript(INDEX_SCHEMA)
    pad_lat = parent["padding_km"] / 110
    pad_lon = parent["padding_km"] / (110 * math.cos(math.radians(max(abs(s), abs(n)) + pad_lat)))
    metadata = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "indexing",
        "bounds": bounds,
        "padding_km": parent["padding_km"],
        "max_gap_s": parent["max_gap_s"],
        "start_utc": parent["start_utc"],
        "end_utc": parent["end_utc"],
        "created_utc": utc(),
        "source_index_sha256": digest(index_path),
        "source_index_metadata": parent,
    }
    started, counts = time.monotonic(), Counter()
    try:
        for row in source.execute(
            "SELECT id,icao,source_member,start,end,n,max_gap,points FROM segments ORDER BY id"
        ):
            counts["input_segments"] += 1
            points = unpack(row[7], row[5])
            intersects = (
                points[:, 1].max() >= s - pad_lat
                and points[:, 1].min() <= n + pad_lat
                and points[:, 2].max() >= w - pad_lon
                and points[:, 2].min() <= e + pad_lon
            )
            if intersects:
                destination.execute("INSERT INTO segments VALUES(?,?,?,?,?,?,?,?)", row)
                counts["segments"] += 1
                counts["retained_points"] += len(points)
        if not counts["segments"]:
            raise ValueError("No trajectories intersect this padded region.")
        metadata["status"] = "complete"
    except BaseException as error:
        metadata["status"] = "failed"
        metadata["error"] = str(error)
        raise
    finally:
        metadata["elapsed_s"] = round(time.monotonic() - started, 3)
        metadata["counts"] = dict(counts)
        destination.execute(
            "INSERT OR REPLACE INTO metadata VALUES('manifest',?)", (json.dumps(metadata),)
        )
        destination.commit()
        destination.close()
        source.close()
        metadata["index_bytes"] = (output / "index.sqlite").stat().st_size
        metadata["index_sha256"] = digest(output / "index.sqlite")
        write_json(output / "index.json", metadata)
    return metadata


def passages(points, tree, receivers, radius_m, min_speed, max_speed, sound_speed, budget):
    """Retain each bracketed local distance minimum, including repeated passes in a loop."""
    times = points[:, 0]
    xyz = geodetic_to_ecef(points[:, 1], points[:, 2], points[:, 3])
    delta = np.diff(xyz, axis=0)
    durations = np.diff(times)
    lengths = np.linalg.norm(delta, axis=1)
    speed = lengths / durations
    valid = (speed >= min_speed) & (speed <= max_speed)
    budget["speed_filtered_edges"] += int(np.count_nonzero(~valid))
    edges = np.flatnonzero(valid)
    grouped = defaultdict(list)
    segment_evaluations = 0
    for begin in range(0, len(edges), 4096):
        batch = edges[begin : begin + 4096]
        centers = (xyz[batch] + xyz[batch + 1]) / 2
        radii = radius_m + lengths[batch] / 2
        count = int(tree.query_ball_point(centers, radii, return_length=True, workers=1).sum())
        segment_evaluations += count
        budget["edge_receiver_evaluations"] += count
        if budget["edge_receiver_evaluations"] > budget["max_evaluations"]:
            raise ValueError(
                "Screening evaluation budget exceeded; output is incomplete. Tile the region."
            )
        if segment_evaluations > 5_000_000:
            raise ValueError(
                "One trajectory exceeds five million edge/receiver pairs; use a coarser grid or smaller region."
            )
        neighbors = tree.query_ball_point(centers, radii, workers=1)
        for edge, cells in zip(batch, neighbors, strict=True):
            for cell in cells:
                grouped[cell].append(edge)
    for cell, indexes in grouped.items():
        ix = np.asarray(indexes)
        vector = delta[ix]
        fraction = np.clip(
            np.sum((receivers[cell] - xyz[ix]) * vector, axis=1) / lengths[ix] ** 2, 0, 1
        )
        distances = np.linalg.norm(xyz[ix] + vector * fraction[:, None] - receivers[cell], axis=1)
        # Exact ECEF distances to vertices bracket valid local minima even at shared endpoints.
        prior = np.maximum(ix - 1, 0)
        to_receiver = xyz[ix] - receivers[cell]
        before = np.sum(to_receiver * delta[prior], axis=1)
        after = np.sum(to_receiver * vector, axis=1)
        interior = (fraction > 1e-8) & (fraction < 1 - 1e-8)
        vertex = (fraction <= 1e-8) & (ix > 0) & valid[prior] & (before < 0) & (after >= 0)
        minima = (distances <= radius_m) & (interior | vertex)
        pending = None
        for k in np.flatnonzero(minima):
            edge, f = ix[k], fraction[k]
            emission = times[edge] + f * durations[edge]
            distance = distances[k]
            event = (cell, emission + distance / sound_speed, distance, speed[edge])
            # Quantization and the straight chords can create neighboring minima for one pass.
            # Merge within 10 s; this is screening resolution, not independent acoustic events.
            if pending is not None and event[1] - pending[1] < 10:
                budget["merged_nearby_minima"] += 1
                if event[2] < pending[2]:
                    pending = event
            else:
                if pending is not None:
                    yield pending
                pending = event
        if pending is not None:
            yield pending


def shortlist(
    index_path,
    output,
    interval_s,
    tolerance_s=10,
    grid_km=5,
    radius_km=10,
    receiver_height_m=0,
    sound_speed=343,
    min_speed=25,
    max_speed=300,
    max_evaluations=500_000_000,
    max_passages=5_000_000,
    max_pairs=500_000,
    progress=None,
):
    """Coarse two-event timing filter; preserve alternatives, limits and assumptions."""
    values = [
        interval_s,
        tolerance_s,
        grid_km,
        radius_km,
        receiver_height_m,
        sound_speed,
        min_speed,
        max_speed,
    ]
    if not all(number(v) for v in values):
        raise ValueError("Search parameters must be finite.")
    if not 10 <= interval_s <= 86400 or not 0 <= tolerance_s <= 600:
        raise ValueError("Use a 10–86400 s interval and 0–600 s measurement tolerance.")
    if (
        not 1 <= radius_km <= 50
        or not 300 <= sound_speed <= 370
        or not 10 <= min_speed < max_speed < 0.9 * sound_speed
    ):
        raise ValueError("Invalid radius, sound speed or subsonic speed range.")
    if any(type(v) is not int or v <= 0 for v in [max_evaluations, max_passages, max_pairs]):
        raise ValueError("Resource budgets must be positive integers.")
    source, metadata = open_index(index_path)
    if metadata["padding_km"] < radius_km + grid_km:
        source.close()
        raise ValueError(
            "Index padding must cover radius plus grid spacing; rebuild with more padding."
        )
    output = new_folder(output)
    manifest = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "screening",
        "accepted_location": False,
        "index_sha256": digest(index_path),
        "index_metadata": metadata,
        "interval_s": interval_s,
        "tolerance_s": tolerance_s,
        "grid_km": grid_km,
        "radius_km": radius_km,
        "receiver_height_m": receiver_height_m,
        "sound_speed_m_s": sound_speed,
        "speed_bounds_m_s": [min_speed, max_speed],
        "max_pairs": max_pairs,
        "max_passages": max_passages,
        "created_utc": utc(),
        "warnings": [
            "Candidate timing screen only; no audio has been matched.",
            "One flat ellipsoid receiver height is assumed; terrain and height uncertainty are not modeled.",
            "Grid timing allowance assumes locally straight, steady flight; completeness is not guaranteed for curved or noisy paths.",
            "Radius, speed, missing-height and coverage filters can exclude the true flight.",
            "Two distinct aircraft are required; repeated passes of one airframe are excluded.",
        ],
    }
    started = time.monotonic()
    budget = Counter(edge_receiver_evaluations=0, max_evaluations=max_evaluations)
    db = sqlite3.connect(output / "passages.sqlite")
    db.executescript("""
      CREATE TABLE passages(id INTEGER PRIMARY KEY, cell INTEGER, segment INTEGER, icao TEXT,
                            arrival REAL, slant REAL, speed REAL);
      CREATE INDEX passage_time ON passages(cell,arrival);
    """)
    try:
        geo, xyz = receiver_grid(metadata["bounds"], grid_km * 1000, receiver_height_m)
        tree = cKDTree(xyz)
        # Allow a half-cell diagonal for corridor selection and conservative timing screening.
        cell_radius = grid_km * 1000 / math.sqrt(2) * 1.02
        manifest["cell_cover_radius_m"] = cell_radius
        manifest["receiver_nodes"] = len(geo)
        for segment, icao, count, blob in source.execute(
            "SELECT id,icao,n,points FROM segments ORDER BY id"
        ):
            points = unpack(blob, count)
            rows = []
            for cell, arrival, distance, speed in passages(
                points,
                tree,
                xyz,
                radius_km * 1000 + cell_radius,
                min_speed,
                max_speed,
                sound_speed,
                budget,
            ):
                budget["passages"] += 1
                if budget["passages"] > max_passages:
                    raise ValueError(
                        "Passage budget exceeded; output is incomplete. Tile the region."
                    )
                rows.append((cell, segment, icao, arrival, distance, speed))
            db.executemany(
                "INSERT INTO passages(cell,segment,icao,arrival,slant,speed) VALUES(?,?,?,?,?,?)",
                rows,
            )
            budget["segments_processed"] += 1
            if segment % 100 == 0:
                db.commit()
                if progress:
                    progress(dict(budget))
        db.commit()
        manifest["passage_generation_s"] = round(time.monotonic() - started, 3)
        maximum_tolerance = (
            tolerance_s + 2 * cell_radius / min_speed + 2 * cell_radius / sound_speed
        )
        query = """SELECT a.cell,a.segment,b.segment,a.icao,b.icao,a.arrival,b.arrival,
                    a.slant,b.slant,a.speed,b.speed
          FROM passages a JOIN passages b ON b.cell=a.cell
          AND b.arrival BETWEEN a.arrival+? - ? AND a.arrival+? + ?
          WHERE b.arrival>a.arrival AND a.icao<>b.icao ORDER BY a.id,b.arrival,b.id"""
        with (output / "candidates.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for cell, a, b, ia, ib, ta, tb, ra, rb, va, vb in db.execute(
                query, (interval_s, maximum_tolerance, interval_s, maximum_tolerance)
            ):
                error = tb - ta - interval_s
                allowed = (
                    tolerance_s
                    + cell_radius / va
                    + cell_radius / vb
                    + 2 * cell_radius / sound_speed
                )
                if abs(error) > allowed:
                    continue
                if budget["candidates"] >= max_pairs:
                    raise ValueError(
                        "Candidate budget exceeded; CSV is partial. Tile region or tighten supported bounds."
                    )
                budget["candidates"] += 1
                writer.writerow(
                    dict(
                        zip(
                            FIELDS,
                            [
                                budget["candidates"],
                                cell,
                                *geo[cell],
                                receiver_height_m,
                                a,
                                b,
                                ia,
                                ib,
                                utc(ta),
                                utc(tb),
                                error,
                                allowed,
                                ra,
                                rb,
                                va,
                                vb,
                            ],
                            strict=True,
                        )
                    )
                )
        manifest["status"] = "complete"
    except BaseException as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        raise
    finally:
        source.close()
        db.commit()
        db.close()
        manifest["elapsed_s"] = round(time.monotonic() - started, 3)
        manifest["counts"] = dict(budget)
        manifest["output_bytes"] = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        if (output / "candidates.csv").exists():
            manifest["candidates_sha256"] = digest(output / "candidates.csv")
        write_json(output / "screening.json", manifest)
    return manifest


def export_candidate(index_path, screening_dir, candidate_id, output, window_s=180):
    """Prepare geographically limited tracks and a reviewable handoff; no invented audio inputs."""
    screening_dir = Path(screening_dir)
    info = json.loads((screening_dir / "screening.json").read_text(encoding="utf-8"))
    if info["status"] != "complete" or digest(index_path) != info["index_sha256"]:
        raise ValueError("Use a completed shortlist and its unchanged source index.")
    if digest(screening_dir / "candidates.csv") != info["candidates_sha256"]:
        raise ValueError("Candidate CSV hash mismatch.")
    if not 30 <= window_s <= 600:
        raise ValueError("Use 30–600 seconds around each candidate's arrival time.")
    with (screening_dir / "candidates.csv").open(newline="", encoding="utf-8") as stream:
        candidate = next(
            (r for r in csv.DictReader(stream) if int(r["candidate_id"]) == candidate_id), None
        )
    if candidate is None:
        raise ValueError("Candidate ID was not found.")
    db, _ = open_index(index_path)
    origin = [float(candidate[k]) for k in ["latitude_deg", "longitude_deg", "receiver_height_m"]]
    epoch = parse_utc(candidate["arrival_a_utc"]) - window_s - 120
    selected = []
    try:
        for label in ["a", "b"]:
            row = db.execute(
                "SELECT icao,n,points FROM segments WHERE id=?",
                (int(candidate[f"segment_{label}"]),),
            ).fetchone()
            if row is None:
                raise ValueError("Candidate references an unknown segment.")
            points = unpack(row[2], row[1])
            arrival = parse_utc(candidate[f"arrival_{label}_utc"])
            points = points[
                (points[:, 0] >= arrival - window_s - 120) & (points[:, 0] <= arrival + window_s)
            ]
            # Keep one continuous neighborhood of this CPA inside the local solver's frame.
            if len(points):
                positions = geodetic_to_enu(points[:, 1], points[:, 2], points[:, 3], origin)
                inside = np.linalg.norm(positions, axis=1) <= 45000
                emission = arrival - float(candidate[f"slant_{label}_m"]) / info["sound_speed_m_s"]
                center = int(np.argmin(np.abs(points[:, 0] - emission)))
                if not inside[center]:
                    raise ValueError(
                        "No local trajectory support around candidate closest approach."
                    )
                first, last = center, center
                while first > 0 and inside[first - 1]:
                    first -= 1
                while last + 1 < len(points) and inside[last + 1]:
                    last += 1
                points = points[first : last + 1]
            if len(points) < 4:
                raise ValueError("Too few retained samples for local fitting.")
            selected.append((f"{row[0]}-s{candidate[f'segment_{label}']}", points))
    finally:
        db.close()
    output = new_folder(output)
    geographic = output / "geographic.csv"
    with geographic.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["track_id", "timestamp_utc", "latitude_deg", "longitude_deg", "height_ellipsoid_m"]
        )
        for name, points in selected:
            for t, lat, lon, height in points:
                writer.writerow([name, utc(t), lat, lon, height])
    import_tracks(geographic, output / "tracks.csv", origin, utc(epoch))
    result = {
        "schema_version": 1,
        "status": "requires_audio_and_terrain_review",
        "accepted_location": False,
        "candidate": candidate,
        "origin_wgs84": origin,
        "track_epoch_utc": utc(epoch),
        "track_ids": [name for name, _ in selected],
        "max_track_gap_s": max(float(np.diff(p[:, 0]).max()) for _, p in selected),
        "input_index_sha256": info["index_sha256"],
        "tracks_sha256": digest(output / "tracks.csv"),
        "next_steps": [
            "Verify receiver ellipsoid height/terrain and repeat screening if necessary.",
            "Inspect trajectory gaps and derived velocity before choosing max_track_gap_s.",
            "Add the original audio and measured event windows/source-tone ranges.",
            "Set the shared clock around first candidate arrival minus the first audio landmark.",
            "Use case.json from the demo as the schema; run independent controls and other candidates.",
        ],
    }
    write_json(output / "handoff.json", result)
    return result
