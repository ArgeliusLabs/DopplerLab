"""Auditable daily downloads and bounded streaming of split readsb tar archives."""

import gzip
import hashlib
import io
import json
import re
import shutil
import ssl
import tarfile
import time
import urllib.request
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import certifi
import ijson

from . import __version__
from .adsb import LICENSE_URL, new_folder, utc

MAX_RECORD = 64 * 1024 * 1024


def open_url(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": f"ArgeliusDopplerLab/{__version__}"}
    )
    return urllib.request.urlopen(
        request, timeout=60, context=ssl.create_default_context(cafile=certifi.where())
    )


def download_day(day, output, instance="prod-0", max_gb=6, progress=None):
    """Download one observed global UTC day; fail closed on errors or a byte budget breach."""
    day = date.fromisoformat(day)
    if instance not in {"prod-0", "prod-1", "staging-0"}:
        raise ValueError("Choose a documented production or staging instance.")
    if not 0 < max_gb <= 100:
        raise ValueError("Download budget must be in (0, 100] decimal GB.")
    tag = f"v{day:%Y.%m.%d}-planes-readsb-{instance}"
    repository = f"adsblol/globe_history_{day.year}"
    metadata_url = f"https://api.github.com/repos/{repository}/releases/tags/{tag}"
    with open_url(metadata_url) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Release metadata exceeds 2 MB.")
    release = json.loads(raw)
    assets = sorted(
        [
            a
            for a in release["assets"]
            if re.fullmatch(re.escape(tag) + r"\.tar(?:\.[a-z]{2})?", a["name"])
        ],
        key=lambda a: a["name"],
    )
    if not assets:
        raise ValueError("No daily archive parts found; inspect provider availability.")
    validate_parts([Path(a["name"]) for a in assets])
    size = sum(a["size"] for a in assets)
    if size <= 0 or size > max_gb * 1e9:
        raise ValueError(f"Archive is {size / 1e9:.3f} GB, outside the {max_gb:g} GB budget.")
    for asset in assets:
        expected = f"https://github.com/{repository}/releases/download/{tag}/{asset['name']}"
        if asset["browser_download_url"] != expected or asset["size"] <= 0:
            raise ValueError("Unexpected archive asset URL or size.")
    output = new_folder(output)
    if shutil.disk_usage(output).free < size + 1_000_000_000:
        raise ValueError("Insufficient free disk space for archive plus 1 GB headroom.")
    manifest = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "downloading",
        "provider": "adsb.lol",
        "license": LICENSE_URL,
        "release_url": release["html_url"],
        "metadata_url": metadata_url,
        "metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "utc_day": day.isoformat(),
        "expected_bytes": size,
        "started_utc": utc(),
        "parts": [],
    }
    (output / "release-metadata.json").write_bytes(raw)
    started = time.monotonic()
    total = 0
    try:
        for asset in assets:
            path = output / (asset["name"] + ".partial")
            digest = hashlib.sha256()
            count = 0
            with open_url(asset["browser_download_url"]) as response, path.open("xb") as stream:
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    if count > asset["size"]:
                        raise ValueError("Asset exceeded advertised byte count.")
                    stream.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
                    if progress:
                        progress(total, size)
            if count != asset["size"]:
                raise ValueError("Incomplete download; byte count differs from release metadata.")
            sha = digest.hexdigest()
            if asset.get("digest") and asset["digest"] != f"sha256:{sha}":
                raise ValueError("Asset digest differs from GitHub's published digest.")
            path.rename(output / asset["name"])
            manifest["parts"].append({"name": asset["name"], "bytes": count, "sha256": sha})
        manifest["status"] = "complete"
    except BaseException as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        raise
    finally:
        manifest["elapsed_s"] = round(time.monotonic() - started, 3)
        manifest["received_bytes"] = total
        manifest["ended_utc"] = utc()
        (output / "download.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    return manifest


def validate_parts(paths):
    """No missing, duplicated, mixed-release or out-of-order split parts."""
    if not paths:
        raise ValueError("Supply a tar archive or all its ordered split parts.")
    if len(paths) == 1 and paths[0].name.endswith(".tar"):
        return
    bases = {str(p).rsplit(".", 1)[0] for p in paths}
    suffixes = [p.suffix[1:] for p in paths]
    expected = [chr(97 + i // 26) + chr(97 + i % 26) for i in range(len(paths))]
    if len(bases) != 1 or suffixes != expected or not all(".tar." in p.name for p in paths):
        raise ValueError("Supply all parts of one tar in .aa, .ab, ... order without gaps.")


class PartReader(io.RawIOBase):
    """Join binary parts on read, hashing every input without making an extra tar."""

    def __init__(self, paths):
        self.paths = [Path(p) for p in paths]
        validate_parts(self.paths)
        self.index = 0
        self.stream = None
        self.hashes = []
        self.digest = None
        self.count = 0

    def readable(self):
        return True

    def read(self, size=-1):
        if size < 0:
            raise ValueError("Unbounded archive reads are not supported.")
        chunks = []
        while size and self.index < len(self.paths):
            if self.stream is None:
                self.stream = self.paths[self.index].open("rb")
                self.digest = hashlib.sha256()
                self.count = 0
            chunk = self.stream.read(size)
            if chunk:
                chunks.append(chunk)
                self.digest.update(chunk)
                self.count += len(chunk)
                size -= len(chunk)
            else:
                self.stream.close()
                self.stream = None
                self.hashes.append(
                    {
                        "name": str(self.paths[self.index]),
                        "bytes": self.count,
                        "sha256": self.digest.hexdigest(),
                    }
                )
                self.index += 1
        return b"".join(chunks)

    def close(self):
        if self.stream:
            self.stream.close()
        super().close()


def read_trace(stream):
    """Archive .json members may be gzip encoded despite their suffix."""
    buffered = io.BufferedReader(stream)
    try:
        if buffered.peek(2)[:2] == b"\x1f\x8b":
            with gzip.GzipFile(fileobj=buffered) as decoded:
                raw = decoded.read(MAX_RECORD + 1)
        else:
            raw = buffered.read(MAX_RECORD + 1)
        if len(raw) > MAX_RECORD:
            raise ValueError("A trace exceeds the 64 MiB decoded record limit.")
        return json.loads(raw)
    finally:
        buffered.close()


class LimitedReader:
    def __init__(self, stream, maximum=1024 * 1024 * 1024):
        self.stream, self.maximum, self.count = stream, maximum, 0

    def read(self, size):
        body = self.stream.read(min(size, self.maximum - self.count + 1))
        self.count += len(body)
        if self.count > self.maximum:
            raise ValueError("Decoded trace exceeds the 1 GiB streaming limit.")
        return body


@contextmanager
def stream_trace(stream):
    """Parse header and individual points without materializing a day's huge JSON list."""
    with io.BufferedReader(stream) as raw:
        decoded_stream = gzip.GzipFile(fileobj=raw) if raw.peek(2)[:2] == b"\x1f\x8b" else raw
        with io.BufferedReader(decoded_stream, buffer_size=65536) as decoded:
            metadata = {}
            for prefix, event, value in ijson.parse(
                io.BytesIO(decoded.peek(65536)), use_float=True
            ):
                if prefix in {"icao", "timestamp"} and event in {"string", "number"}:
                    metadata[prefix] = value
                if prefix == "trace" and event == "start_array":
                    break
            if not {"icao", "timestamp"}.issubset(metadata):
                raise ValueError(
                    "Expected readsb identity/time header before trace array within 64 KiB."
                )
            metadata["trace"] = ijson.items(LimitedReader(decoded), "trace.item", use_float=True)
            yield metadata


def archive_traces(paths, audit):
    """Read regular trace members only; never extract paths, links or executable files."""
    with PartReader(paths) as joined:
        with tarfile.open(fileobj=joined, mode="r|") as archive:
            for member in archive:
                audit["archive_members"] += 1
                if not member.isfile() or "/traces/" not in "/" + member.name:
                    continue
                if not re.fullmatch(
                    r"trace_full_[0-9a-fA-F]{6}\.json(?:\.gz)?", Path(member.name).name
                ):
                    continue
                if member.size > MAX_RECORD:
                    raise ValueError("A compressed trace member exceeds 64 MiB.")
                try:
                    with stream_trace(archive.extractfile(member)) as data:
                        yield member.name, data
                except (ValueError, ijson.JSONError) as error:
                    raise ValueError(f"Invalid trace {member.name}: {error}") from error
        # Tar can stop before the last padding block; hash all original bytes.
        while joined.read(1024 * 1024):
            pass
        audit["input_parts"] = joined.hashes
