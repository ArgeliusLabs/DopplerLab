"""Measure a CLI subprocess; sampling is approximate and is reported as such."""

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.output.exists():
        raise ValueError("Supply a command and a new report filename.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "command": command,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": psutil.cpu_count(),
        "system_ram_bytes": psutil.virtual_memory().total,
        "started_utc": datetime.now(UTC).isoformat(),
        "sample_interval_s": 0.2,
    }
    root = Path(__file__).resolve().parents[1]
    report["source_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    report["source_sha256"] = {
        str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root / "src").glob("**/*.py"))
    }
    started, peak = time.monotonic(), 0
    with args.output.with_suffix(".log").open("x", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        observed = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                processes = [observed, *observed.children(recursive=True)]
                peak = max(peak, sum(p.memory_info().rss for p in processes if p.is_running()))
            except psutil.Error:
                pass
            time.sleep(0.2)
        report["exit_code"] = process.returncode
    report["elapsed_s"] = round(time.monotonic() - started, 3)
    report["sampled_peak_rss_bytes"] = peak
    report["note"] = (
        "Peak process-tree RSS sampled every 0.2 s; transient peaks can be missed. Not a hardware requirement."
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
