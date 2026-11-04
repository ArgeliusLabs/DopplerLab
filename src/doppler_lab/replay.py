"""Small-window acquisition using adsb.lol's public tar1090 replay resources.

Heatmap positions select aircraft IDs only. Their heights are not used for geometry.
Detailed traces still pass through the strict geometric-height normalizer.
"""

import gzip
import io
import json
import math
import time
import urllib.error
from datetime import UTC, datetime

import numpy as np

from . import __version__
from .adsb import LICENSE_URL, new_folder, normalize, number, utc
from .archive import open_url
from .case import digest
from .importers import parse_utc

MAGIC = 0x0E7F7C9D


def decode_body(raw, maximum):
    if raw[:2] == b"\x1f\x8b":
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Decoded replay resource exceeds its byte budget.")
    return raw


def replay_candidates(raw, start, end, bounds, chunk_start):
    """Read little-endian tar1090 16-byte records; ignore prefix indexes and metadata."""
    body = decode_body(raw, 200_000_000)
    if not body or len(body) % 16:
        raise ValueError("Invalid replay record alignment.")
    points = np.frombuffer(body, dtype="<i4").reshape(-1, 4)
    unsigned = points.view("<u4")
    headers = np.flatnonzero(points[:, 0] == MAGIC)
    if not len(headers):
        raise ValueError("Replay has no recognized time-slice headers.")
    south, west, north, east = bounds
    identities = set()
    stamps = []
    count = 0
    excluded = 0
    for n, h in enumerate(headers):
        stamp = int(unsigned[h, 1]) * 4294967.296 + int(unsigned[h, 2]) / 1000
        interval = int(unsigned[h, 3] & 65535) / 1000
        if not chunk_start <= stamp < chunk_start + 1800 or not 0 < interval <= 60:
            raise ValueError("Unexpected replay timestamp or sampling interval.")
        if stamps and stamp <= stamps[-1]:
            raise ValueError("Replay timestamps are not strictly increasing.")
        stamps.append(stamp)
        if not start <= stamp <= end:
            continue
        stop = headers[n + 1] if n + 1 < len(headers) else len(points)
        rows = points[h + 1 : stop]
        selected = rows[
            (rows[:, 1] >= south * 1e6)
            & (rows[:, 1] <= north * 1e6)
            & (rows[:, 2] >= west * 1e6)
            & (rows[:, 2] <= east * 1e6)
        ]
        for row in selected:
            if int(row[0]) & 0x1000000:
                excluded += 1
                continue
            identities.add(f"{int(row[0]) & 0xFFFFFF:06x}")
            count += 1
    return identities, {
        "slices": len(headers),
        "first_slice_utc": utc(stamps[0]),
        "last_slice_utc": utc(stamps[-1]),
        "regional_icao_points": count,
        "excluded_non_icao_points": excluded,
        "max_slice_gap_s": float(max(np.diff(stamps), default=0)),
        "decoded_bytes": len(body),
    }


class WindowFetcher:
    def __init__(self, output, info, max_bytes, progress=None):
        self.output, self.info, self.max_bytes = output, info, max_bytes
        self.received = 0
        self.last_request = None
        self.progress = progress

    def fetch(self, url, name, limit):
        # Public map requests are deliberately paced; no auth/rate-limit bypass or retry.
        if self.last_request is not None:
            time.sleep(max(0, 2 - (time.monotonic() - self.last_request)))
        record = {"url": url, "file": name, "requested_utc": utc()}
        self.info["requests"].append(record)
        try:
            allowance = min(limit, self.max_bytes - self.received)
            if allowance <= 0:
                raise ValueError("Window download byte budget exhausted.")
            with open_url(url) as response:
                raw = response.read(allowance + 1)
            self.received += len(raw)
            if len(raw) > allowance:
                raise ValueError("Replay resource exceeded the download byte budget.")
            path = self.output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            record.update(status="downloaded", bytes=len(raw), sha256=digest(path))
            return raw
        except urllib.error.HTTPError as error:
            record.update(status="http_error", http_status=error.code)
            if error.code == 404:
                return None
            raise ValueError(
                f"Provider returned HTTP {error.code}; stopped without retrying."
            ) from error
        finally:
            self.last_request = time.monotonic()
            self.info["downloaded_bytes"] = self.received
            if self.progress:
                self.progress(
                    {"requests": len(self.info["requests"]), "downloaded_bytes": self.received}
                )


def download_window(
    start_utc,
    end_utc,
    bounds,
    output,
    padding_s=180,
    max_gb=1,
    max_aircraft=150,
    max_gap_s=5,
    conflicts="error",
    progress=None,
):
    start, end = parse_utc(start_utc), parse_utc(end_utc)
    if not number(padding_s) or not 0 <= padding_s <= 600:
        raise ValueError("Padding must be 0 to 600 seconds.")
    if not 0 < end - start or end - start + 2 * padding_s > 3600:
        raise ValueError("The recording window plus both padding margins must fit within one hour.")
    if len(bounds) != 4 or not all(number(x) for x in bounds):
        raise ValueError("Supply finite south west north east bounds.")
    south, west, north, east = bounds
    if not -90 <= south < north <= 90 or not -180 <= west < east <= 180:
        raise ValueError("Invalid geographic bounds; dateline wrapping is unsupported.")
    if north - south > 2 or east - west > 2:
        raise ValueError("Window acquisition supports a local box at most 2 degrees per side.")
    if (
        not number(max_gb)
        or not 0 < max_gb <= 5
        or type(max_aircraft) is not int
        or not 1 <= max_aircraft <= 500
    ):
        raise ValueError("Use a byte budget in (0, 5] GB and an aircraft cap from 1 to 500.")
    if not number(max_gap_s) or not 0 < max_gap_s <= 30 or conflicts not in {"error", "quarantine"}:
        raise ValueError("Use a maximum gap in (0, 30] seconds and an explicit conflict policy.")
    start -= padding_s
    end += padding_s
    output = new_folder(output)
    info = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "downloading",
        "provider": "adsb.lol public replay and readsb traces",
        "license_url": LICENSE_URL,
        "recording_window_utc": [utc(parse_utc(start_utc)), utc(parse_utc(end_utc))],
        "padded_window_utc": [utc(start), utc(end)],
        "padding_s": padding_s,
        "bounds": bounds,
        "max_gap_s": max_gap_s,
        "conflicts_policy": conflicts,
        "started_utc": utc(),
        "requests": [],
        "chunks": [],
        "traces": [],
        "warnings": [
            "Experimental map-resource adapter; URLs/formats/retention may change.",
            "Replay sampling and receiver coverage can omit aircraft. This is not an exhaustive flight census.",
            "Heatmap heights are never used for acoustic geometry; detailed geometric heights are required.",
            "Expand the geographic box for audible approaches; clipping is a completeness limitation.",
            "Provider data is ODbL, separate from this project's MIT code.",
        ],
    }
    begun = time.monotonic()
    fetcher = WindowFetcher(output, info, int(max_gb * 1e9), progress)
    candidates = set()
    selected_paths = []
    missing = []
    current_cache = {}
    try:
        first = math.floor(start / 1800) * 1800
        for stamp in range(first, math.floor(end / 1800) * 1800 + 1, 1800):
            date = datetime.fromtimestamp(stamp, UTC)
            day = date.strftime("%Y/%m/%d")
            index = date.hour * 2 + date.minute // 30
            name = f"replay/{date:%Y-%m-%d}-{index:02d}.bin.ttf"
            raw = fetcher.fetch(
                f"https://adsb.lol/globe_history/{day}/heatmap/{index:02d}.bin.ttf",
                name,
                100_000_000,
            )
            if raw is None:
                missing.append(name)
                continue
            ids, details = replay_candidates(raw, start, end, bounds, stamp)
            info["chunks"].append({"file": name, **details})
            candidates.update((day, ident) for ident in ids)
        info["aircraft_count"] = len({ident for _, ident in candidates})
        if info["aircraft_count"] > max_aircraft:
            raise ValueError("Aircraft cap exceeded; narrow the time/area or raise --max-aircraft.")
        for day, ident in sorted(candidates):
            dated_name = day.replace("/", "-") + "-" + ident
            url = (
                f"https://adsb.lol/globe_history/{day}/traces/{ident[-2:]}/trace_full_{ident}.json"
            )
            raw = fetcher.fetch(url, f"raw-traces/{dated_name}.json", 25_000_000)
            source = "historical"
            day_start = datetime.strptime(day, "%Y/%m/%d").replace(tzinfo=UTC).timestamp()
            # tar1090 uses the current full trace for recent dates before history is written.
            if raw is None and 0 <= time.time() - day_start < 172800:
                source = "current_full_trace_fallback"
                if ident not in current_cache:
                    current_cache[ident] = fetcher.fetch(
                        f"https://adsb.lol/data/traces/{ident[-2:]}/trace_full_{ident}.json",
                        f"raw-traces/current-{ident}.json",
                        25_000_000,
                    )
                raw = current_cache[ident]
            if raw is None:
                missing.append(dated_name)
                continue
            data = json.loads(decode_body(raw, 64 * 1024 * 1024))
            if (
                not isinstance(data, dict)
                or data.get("icao") != ident
                or not isinstance(data.get("trace"), list)
                or not number(data.get("timestamp"))
            ):
                raise ValueError(f"Unexpected detailed trace for {ident}.")
            # Use each date exactly once; current full traces can overlap historical files.
            rows = [
                r
                for r in data["trace"]
                if isinstance(r, list)
                and r
                and number(r[0])
                and day_start <= data["timestamp"] + r[0] < day_start + 86400
                and start <= data["timestamp"] + r[0] <= end
            ]
            if not rows:
                missing.append(dated_name + ": no time support")
                continue
            data["trace"] = rows
            path = output / "selected-traces" / f"{dated_name}.json"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            selected_paths.append(path)
            info["traces"].append(
                {
                    "file": str(path.relative_to(output)).replace("\\", "/"),
                    "source": source,
                    "points_before_normalization": len(rows),
                    "sha256": digest(path),
                }
            )
        info["missing_resources"] = missing
        if selected_paths:
            info["normalization"] = normalize(
                selected_paths,
                output / "tracks",
                "readsb-trace",
                utc(start),
                utc(end),
                bounds,
                max_gap_s,
                conflicts,
            )
        info["status"] = "partial" if missing else "complete"
        if not selected_paths:
            info["status"] = "no_traces"
        elif not info["normalization"]["exported_points"]:
            info["status"] = "no_usable_tracks"
    except BaseException as error:
        info["status"], info["error"] = "failed", str(error)
        raise
    finally:
        info["missing_resources"] = missing
        info["elapsed_s"] = round(time.monotonic() - begun, 3)
        info["ended_utc"] = utc()
        (output / "download.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info
