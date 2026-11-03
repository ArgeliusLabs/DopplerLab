"""Render the published aggregate timings and sampled RAM as a standalone figure."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.source.read_text(encoding="utf-8"))
    rows = {r["stage"]: r for r in data["measurements"]}
    keys = [
        "conus_index",
        "europe_index",
        "conus_screen",
        "europe_screen",
        "tucson_subset",
        "tucson_screen",
    ]
    labels = [
        "U.S. regional index",
        "European regional index",
        "U.S. timing screen",
        "European timing screen",
        "Tucson subset from U.S. index",
        "Tucson timing screen",
    ]
    colors = ["#75e3bc", "#75e3bc", "#b8a4ff", "#b8a4ff", "#ffd38b", "#ffd38b"]
    seconds = np.array([rows[k]["elapsed_s"] for k in keys])
    memory = np.array([rows[k]["sampled_peak_rss_bytes"] / 1e6 for k in keys])
    y = np.arange(len(keys))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, (time_axis, memory_axis) = plt.subplots(
        1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1.35, 1]}
    )
    fig.set_facecolor("#101b29")
    for axis in (time_axis, memory_axis):
        axis.set_facecolor("#101b29")
        axis.tick_params(colors="#e6edf4")
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.spines["bottom"].set_color("#536071")
        axis.xaxis.label.set_color("#e6edf4")
        axis.set_axisbelow(True)
        axis.grid(axis="x", color="#536071", alpha=0.25)
        axis.set_ylim(len(keys) - 0.4, -0.65)
    time_axis.barh(y, seconds / 60, color=colors, height=0.55)
    time_axis.set_yticks(y, labels)
    time_axis.set_xlabel("Elapsed time (minutes)")
    time_axis.set_xlim(0, max(seconds) / 60 * 1.3)
    for i, seconds_value in enumerate(seconds):
        label = f"{seconds_value / 60:.1f} min" if seconds_value >= 60 else f"{seconds_value:.1f} s"
        time_axis.text(
            seconds_value / 60 + max(seconds) / 60 * 0.025, i, label, va="center", color="#e6edf4"
        )
    memory_axis.barh(y, memory, color=colors, height=0.55)
    memory_axis.set_yticks(y, [""] * len(keys))
    memory_axis.set_xlabel("Sampled peak process RAM (decimal MB)")
    memory_axis.set_xlim(0, max(memory) * 1.3)
    for i, value in enumerate(memory):
        memory_axis.text(
            value + max(memory) * 0.025, i, f"{value:.0f} MB", va="center", color="#e6edf4"
        )
    fig.suptitle(
        "One archived day: measured pipeline stages",
        color="#ffffff",
        fontsize=21,
        x=0.04,
        ha="left",
        y=0.96,
    )
    fig.text(
        0.04,
        0.887,
        f"{data['archive_utc_date']} UTC  |  Shared global download: {data['download_bytes'] / 1e9:.2f} GB in {data['download_elapsed_s'] / 60:.2f} min",
        color="#b7c8d8",
        fontsize=12,
    )
    fig.text(
        0.04,
        0.085,
        "Single Windows development runs; other tasks ran concurrently. RAM sampled every 0.2 s.\n"
        "Timing screens use a hypothetical 920 s interval and flat receiver height. No audio-location validation.\n"
        "Tucson starts from the existing U.S. index. Download cost is shared; broad screening is not a precise location fix.",
        color="#b7c8d8",
        fontsize=10,
        linespacing=1.5,
    )
    fig.subplots_adjust(left=0.29, right=0.97, bottom=0.25, top=0.81, wspace=0.24)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
