"""Portable HTML, machine-readable JSON/CSV, and original diagnostic figures."""

import base64
import csv
import html
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

from . import __version__
from .search import rank_distinct


def new_output(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Output directory is not empty; choose a new path: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def draw_spectrogram(spec, path, title="Frequency over time", curves=None):
    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(12, 4.8), layout="constrained")
        mesh = ax.pcolormesh(
            spec.times,
            spec.frequencies,
            spec.whitened,
            shading="auto",
            cmap="magma",
            vmin=-5,
            vmax=25,
            rasterized=True,
        )
        for label, times, frequencies, color in curves or []:
            ax.plot(times, frequencies, color=color, lw=1.6, label=label)
        if curves:
            ax.legend(loc="upper right", fontsize=9)
        ax.set(xlabel="Recording time (seconds)", ylabel="Frequency (Hz)", title=title)
        fig.colorbar(mesh, ax=ax, label="dB above each frequency's temporal median")
        fig.savefig(path, dpi=150)
        plt.close(fig)


def write_report(case, result, spec, indices, output):
    output = new_output(output)
    result = dict(result)
    result.update(
        {
            "tool": "Argelius Doppler Lab",
            "version": __version__,
            "generated_utc": datetime.now(UTC).isoformat(),
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "platform": platform.platform(),
            },
            "input_sha256": case.hashes,
            "configuration": case.config,
        }
    )
    rows = result["rows"]
    result["spatial_alternatives_300m"] = rank_distinct(rows)
    (output / "results.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (output / "candidates.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "rank",
                "east_m",
                "north_m",
                "up_m",
                "clock_offset_s",
                "score_db",
                "track_ids",
                "source_hz",
                "event_scores_db",
            ]
        )
        for rank, row in enumerate(rows, 1):
            writer.writerow(
                [
                    rank,
                    *(row[k] for k in ("east_m", "north_m", "up_m", "clock_offset_s", "score_db")),
                    ";".join(e["track_id"] for e in row["events"]),
                    ";".join(str(e["source_hz"]) for e in row["events"]),
                    ";".join(str(e["contrast_db"]) for e in row["events"]),
                ]
            )
    curves = []
    if rows:
        top = rows[0]
        observer = [top["east_m"], top["north_m"], top["up_m"]]
        for event, ix in zip(top["events"], indices, strict=True):
            ratio = (
                case.tracks[event["track_id"]]
                .sample()
                .predict(observer, spec.times[ix] + top["clock_offset_s"], case.c)
            )
            curves.append(
                (
                    f"{event['name']}: {event['track_id']}",
                    spec.times[ix],
                    ratio * event["source_hz"],
                    "#73fbd3",
                )
            )
    draw_spectrogram(
        spec, output / "spectrogram.png", "Measured audio + leading predictions", curves
    )
    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(8, 6), layout="constrained")
        ax.scatter(
            case.observers[:, 0],
            case.observers[:, 1],
            color="#d1d5db",
            s=18,
            label="Declared candidates",
        )
        if rows:
            dots = ax.scatter(
                [r["east_m"] for r in rows],
                [r["north_m"] for r in rows],
                c=[r["score_db"] for r in rows],
                cmap="viridis",
                s=32,
            )
            fig.colorbar(dots, ax=ax, label="Mean line contrast (dB), not confidence")
            ax.scatter(
                rows[0]["east_m"],
                rows[0]["north_m"],
                marker="*",
                s=240,
                facecolor="#fb923c",
                edgecolor="#172554",
                label="Leading grid point",
            )
        ax.set(
            xlabel="East of local origin (m)",
            ylabel="North of local origin (m)",
            title="Candidate score surface • local coordinates only",
        )
        ax.set_aspect("equal")
        ax.legend(fontsize=9)
        fig.savefig(output / "score-map.png", dpi=150)
        plt.close(fig)

    def embed(name):
        return "data:image/png;base64," + base64.b64encode((output / name).read_bytes()).decode()

    escape = html.escape
    title = escape(str(case.config.get("title", "Doppler case")))
    table_rows = []
    for rank, row in enumerate(result["spatial_alternatives_300m"], 1):
        event_text = " / ".join(
            f"{escape(e['track_id'])}: {e['contrast_db']:.2f}" for e in row["events"]
        )
        table_rows.append(
            f"<tr><td>{rank}</td><td>{row['east_m']:.0f}, "
            f"{row['north_m']:.0f}, {row['up_m']:.0f}</td>"
            f"<td>{row['clock_offset_s']:.2f} s</td>"
            f"<td>{row['score_db']:.2f}</td><td>{event_text}</td></tr>"
        )
    warnings = "".join(f"<li>{escape(w)}</li>" for w in result["warnings"])
    best_score = f"{rows[0]['score_db']:.2f} dB" if rows else "No support"
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta name="color-scheme" content="light"><title>{title} | Argelius Doppler Lab</title>
<style>
:root{{--ink:#142539;--muted:#536477;--paper:#f2f5f7;--teal:#146b68;--orange:#ef7e46}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1160px;margin:auto;padding:32px 24px}}
header{{background:var(--ink);color:white;border-bottom:5px solid var(--orange);padding:44px 24px}}
header>div{{max-width:1112px;margin:auto}}.eyebrow{{font-size:12px;letter-spacing:.18em;text-transform:uppercase}}
h1{{font-size:clamp(30px,5vw,52px);line-height:1.12;max-width:850px;margin:18px 0}}
header p{{max-width:780px;color:#ccdae5}}h2{{font-size:24px;line-height:1.3;margin-top:0}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:26px}}
.card,section,details{{background:white;border:1px solid #dbe2e8;border-radius:12px;padding:24px;margin-bottom:22px}}
.card{{margin:0;padding:20px}}.number{{font-size:26px;font-weight:750}}.label{{font-size:13px;color:var(--muted)}}
.notice{{border-left:5px solid var(--orange)}}.pill{{display:inline-block;background:#fff1df;color:#85410e;
padding:4px 10px;border-radius:6px;font-weight:700;font-size:13px}}img{{display:block;width:100%;height:auto}}
.map{{max-width:850px;margin:auto}}p.caption{{font-size:14px;color:var(--muted)}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid #e1e7ed}}
th{{background:#edf3f6}}.scroll{{overflow:auto}}summary{{cursor:pointer;font-weight:700}}
pre{{overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;background:#f3f6f8;padding:18px}}
footer{{font-size:13px;color:var(--muted);padding:12px 0 32px}}a{{color:var(--teal)}}
@media(max-width:700px){{.grid{{grid-template-columns:repeat(2,1fr)}}main{{padding:20px 12px}}section{{padding:18px}}}}
@media print{{header{{color:#142539;background:white}}header p{{color:#536477}}details{{break-inside:avoid}}}}
</style></head><body><header><div><div class="eyebrow">Argelius Labs / Signal &amp; Evidence / 01</div>
<h1>{title}</h1><p>Aircraft Doppler matching with a shared recording clock.
Inspect the signal, compare alternatives, and decide what the evidence supports.</p></div></header>
<main><div class="grid"><div class="card"><div class="label">Declared locations</div>
<div class="number">{result["candidate_count"]:,}</div></div>
<div class="card"><div class="label">Clock trials / location</div>
<div class="number">{result["clock_trials_per_candidate"]}</div></div>
<div class="card"><div class="label">Leading line contrast</div><div class="number">{best_score}</div></div>
<div class="card"><div class="label">Independent flyovers</div><div class="number">{len(case.events)}</div></div></div>
<section class="notice"><span class="pill">{escape(result["status"].replace("_", " ").upper())}</span>
<h2 style="margin-top:16px">A ranked hypothesis needs corroboration.</h2>
<p>Accepted location: <strong>no</strong>. A high score means that predicted frequency curves follow
bright structure in this spectrogram. It does not establish that the aircraft or location is correct.</p>
<ul>{warnings}</ul></section>
<section><h2>01 / Read the signal</h2><img src="{embed("spectrogram.png")}"
alt="Measured spectrogram with leading predicted Doppler curves overlaid in mint green">
<p class="caption">Time is relative to the first audio sample. Each event has its own source tone;
all events share one clock offset. Persistent tones are reduced by temporal median subtraction.</p></section>
<section><h2>02 / Compare locations</h2><img class="map" src="{embed("score-map.png")}"
alt="Local candidate score map with the highest scoring location marked by a star">
<p class="caption">This is a score surface, not an uncertainty region. Unsupported grid points are gray.
Grid spacing, track error, terrain, clock error and the acoustic model limit interpretation.</p></section>
<section><h2>03 / Keep competing explanations</h2><div class="scroll"><table><thead><tr>
<th>Rank</th><th>East, north, up (m)</th><th>Clock offset</th><th>Score (dB)</th><th>Event scores (dB)</th>
</tr></thead><tbody>{"".join(table_rows)}</tbody></table></div>
<p class="caption">Greedy spatial alternatives separated by at least 300 m. The full grid is in
candidates.csv; these alternatives are descriptive and are not independent statistical trials.</p></section>
<section><h2>04 / Test the explanation</h2><ol><li>Inspect each event separately.</li>
<li>Repeat the complete search on reversed-time and noise controls.</li>
<li>Change sound speed, clock bounds, event window and source frequency bounds.</li>
<li>Validate against a held-out flyover or independently established recorder position.</li></ol>
<p>Do not turn the score gap into a percentage confidence. Report unresolved alternatives.</p></section>
<details><summary>Configuration &amp; input provenance</summary>
<pre>{escape(json.dumps(case.config, indent=2))}</pre>
<pre>{escape(json.dumps(case.hashes, indent=2))}</pre></details>
<footer>Argelius Doppler Lab {__version__} · Offline report · {result["elapsed_s"]:.2f} seconds of search.
Inspired by <a href="https://www.youtube.com/watch?v=UytYrhYLOKI">colsto's aircraft Doppler demonstration</a>.
Original teaching implementation; no affiliation or endorsement implied.</footer></main></body></html>"""
    (output / "report.html").write_text(page, encoding="utf-8")
    return output / "report.html"
