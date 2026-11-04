"""Bounded local-media intake with explicit timing evidence and channel review."""

import html
import json
import math
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import __version__
from .adsb import new_folder, number, utc
from .audio import read_audio, spectrogram
from .case import digest
from .report import draw_spectrogram


def aware_time(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Recording start needs an explicit UTC offset or Z.")
    return stamp.astimezone(UTC)


def timing_evidence(probe, start_utc=None):
    """Only allowlisted timestamp fields escape ffprobe; GPS values are never copied."""
    tags = probe.get("format", {}).get("tags", {})
    claims = []
    for key in ("com.apple.quicktime.creationdate", "creation_time"):
        value = tags.get(key)
        if not isinstance(value, str):
            continue
        claim = {"field": key, "value": value[:100]}
        try:
            claim["utc"] = aware_time(value).isoformat()
        except (ValueError, OverflowError):
            claim["warning"] = "Unparseable timestamp or missing timezone; not used."
        claims.append(claim)
    apple = next((c for c in claims if c["field"].endswith("creationdate") and "utc" in c), None)
    selected = aware_time(start_utc) if start_utc else aware_time(apple["utc"]) if apple else None
    return {
        "timestamp_claims": claims,
        "suggested_sample_zero_utc": selected.isoformat() if selected else None,
        "basis": "analyst override"
        if start_utc
        else "Apple recording-date claim"
        if apple
        else None,
        "location_metadata_present": any(
            "location" in k.lower() or "gps" in k.lower() for k in tags
        ),
        "warning": "Metadata is evidence, not clock verification. Export/container creation time "
        "and file modification time may differ from recording start. Edits can invalidate alignment.",
    }


def utc_days(start, duration_s, uncertainty_s=60, padding_s=180):
    first = aware_time(start) - timedelta(seconds=uncertainty_s + padding_s)
    last = aware_time(start) + timedelta(seconds=duration_s + uncertainty_s + padding_s)
    return [
        (first.date() + timedelta(days=i)).isoformat()
        for i in range((last.date() - first.date()).days + 1)
    ]


def review_media(
    source,
    output,
    chunk_s=300,
    overlap_s=20,
    max_minutes=120,
    start_utc=None,
    uncertainty_s=60,
    ffmpeg="ffmpeg",
    ffprobe="ffprobe",
    progress=None,
):
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError("Supply an existing local media file.")
    for value, low, high, label in [
        (chunk_s, 30, 600, "chunk duration"),
        (overlap_s, 0, 60, "overlap"),
        (max_minutes, 1, 240, "minute budget"),
        (uncertainty_s, 0, 86400, "clock uncertainty"),
    ]:
        if not number(value) or not low <= value <= high:
            raise ValueError(f"Invalid {label}; use {low} to {high}.")
    if overlap_s >= chunk_s / 2:
        raise ValueError("Overlap must be less than half the chunk duration.")
    executables = [shutil.which(str(x)) for x in (ffmpeg, ffprobe)]
    if not all(executables):
        raise ValueError(
            "Install FFmpeg and ffprobe on PATH, or pass --ffmpeg and --ffprobe paths."
        )
    probe = json.loads(
        subprocess.run(
            [
                executables[1],
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    )
    audio = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not audio or audio.get("channels") not in (1, 2):
        raise ValueError("Review currently supports a mono or stereo audio stream.")
    stream_start = float(audio.get("start_time", 0))
    format_start = float(probe.get("format", {}).get("start_time", 0))
    if (
        not all(math.isfinite(t) for t in (stream_start, format_start))
        or abs(stream_start - format_start) > 0.05
    ):
        raise ValueError(
            "Audio/media start times differ by over 50 ms; prepare and document an aligned WAV first."
        )
    duration = float(audio.get("duration", probe.get("format", {}).get("duration", 0)))
    if not math.isfinite(duration) or not 2 <= duration <= max_minutes * 60:
        raise ValueError("Audio duration is missing, too short, or exceeds --max-minutes.")
    timing = timing_evidence(probe, start_utc)
    output = new_folder(output)
    info = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "preparing",
        "source_name": source.name,
        "source_bytes": source.stat().st_size,
        "duration_s": duration,
        "audio_stream_index": audio["index"],
        "audio_stream_start_s": stream_start,
        "media_start_s": format_start,
        "source_sample_rate_hz": audio.get("sample_rate"),
        "channels": audio["channels"],
        "timing": timing,
        "clock_uncertainty_s": uncertainty_s,
        "uncertainty_note": "Analyst-declared search allowance, not measured clock accuracy.",
        "chunk_s": chunk_s,
        "overlap_s": overlap_s,
        "chunks": [],
        "created_utc": utc(),
        "privacy": "Contains derived recording audio. Keep private unless redistribution is authorized. "
        "Location tags are excluded; speech and other identifying content may remain.",
    }
    if timing["suggested_sample_zero_utc"]:
        info["flight_archive_utc_days"] = utc_days(
            timing["suggested_sample_zero_utc"], duration, uncertainty_s
        )
    try:
        if progress:
            progress({"stage": "hashing original"})
        info["source_sha256"] = digest(source)
        info["ffmpeg_version"] = subprocess.run(
            [executables[0], "-version"], check=True, capture_output=True, text=True, timeout=15
        ).stdout.splitlines()[0]
        offset = 0.0
        while offset < duration:
            length = min(chunk_s, duration - offset)
            if 0 < duration - offset - length < 2:
                length = duration - offset
            # Avoid a tiny final remainder: the preceding chunk already contains the overlap.
            if length <= overlap_s and info["chunks"]:
                break
            stem = f"chunk-{len(info['chunks']):03d}"
            wav = output / f"{stem}.wav"
            command = [
                executables[0],
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-ss",
                str(offset),
                "-i",
                str(source),
                "-t",
                str(length),
                "-map",
                f"0:{audio['index']}",
                "-map_metadata",
                "-1",
                "-vn",
                "-ar",
                "8000",
                "-c:a",
                "pcm_s16le",
                "-f",
                "wav",
                str(wav.resolve()),
            ]
            subprocess.run(command, check=True, timeout=300, capture_output=True)
            entry = {
                "file": wav.name,
                "media_start_s": offset,
                "requested_duration_s": length,
                "sha256": digest(wav),
                "channels": [],
            }
            for channel in range(audio["channels"]):
                fs, samples, metadata = read_audio(wav, channel)
                spec = spectrogram(samples, fs, 2, 0.5, 1800)
                spec.times += offset
                figure = output / f"{stem}-channel-{channel}.png"
                draw_spectrogram(spec, figure, f"Channel {channel} — original-media seconds")
                entry["channels"].append({**metadata, "spectrogram": figure.name})
            info["chunks"].append(entry)
            if progress:
                progress(
                    {"stage": "review", "through_media_s": offset + length, "duration_s": duration}
                )
            offset += chunk_s - overlap_s
        info["status"] = "complete"
        write_review(output, info)
    except BaseException as error:
        info["status"], info["error"] = "failed", str(error)
        raise
    finally:
        (output / "media.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


def write_review(output, info):
    cards = []
    for chunk in info["chunks"]:
        offset = chunk["media_start_s"]
        charts = "".join(
            f"<figure><figcaption>Channel {c['channel']}</figcaption>"
            f'<img loading="lazy" src="{c["spectrogram"]}" alt="Channel spectrogram"></figure>'
            for c in chunk["channels"]
        )
        cards.append(
            f"<section><h2>Original media +{offset:g} seconds</h2>"
            f"<p>Player time + {offset:g} = original-media time. Overlap is intentional.</p>"
            f'<audio controls preload="none" src="{chunk["file"]}"></audio>{charts}</section>'
        )
    document = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Recording review</title>'
        "<style>body{font:17px system-ui;max-width:1250px;margin:2rem auto;padding:1rem;"
        "background:#101820;color:#e9eff3}img{width:100%}section{border-top:1px solid #678;"
        "padding-top:1rem}audio{width:100%}a{color:#75d8e8}</style><h1>Recording review</h1>"
        f"<p>{html.escape(info['source_name'])}</p><p>{html.escape(info['privacy'])}</p>"
        "<p>Review both channels. A bright line is not automatically an aircraft. Select events "
        "with sustained curves and preserve rejected alternatives. This page makes no location claim.</p>"
        '<p>Timing evidence, offsets, hashes and quality measurements: <a href="media.json">media.json</a>.</p>'
        + "".join(cards)
        + "</html>"
    )
    (output / "review.html").write_text(document, encoding="utf-8")
