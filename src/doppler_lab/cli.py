import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .audio import read_audio, spectrogram
from .case import load_case
from .importers import import_tracks
from .measure import fit_ridge
from .report import draw_spectrogram, write_report
from .search import search
from .synthetic import create_case


def parser():
    root = argparse.ArgumentParser(description="Argelius Doppler Lab: inspect, model, challenge.")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Generate an original fictional classroom case")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--noise-only", action="store_true")
    demo.add_argument(
        "--source-drift-hz",
        type=float,
        default=0,
        help="Change source tone by this many Hz per 60 emission seconds",
    )
    run = commands.add_parser("run", help="Rank a bounded set of local hypotheses")
    run.add_argument("case", type=Path)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--quiet", action="store_true")
    inspect = commands.add_parser("inspect", help="Save a spectrogram without locating anything")
    inspect.add_argument("audio", type=Path)
    inspect.add_argument("--output", type=Path, required=True)
    inspect.add_argument("--channel", type=int, default=0)
    inspect.add_argument("--window", type=float, default=2)
    inspect.add_argument("--hop", type=float, default=0.25)
    inspect.add_argument("--max-hz", type=float, default=600)
    extract = commands.add_parser("extract", help="Decode a local media excerpt with FFmpeg")
    extract.add_argument("media", type=Path)
    extract.add_argument("--output", type=Path, required=True)
    extract.add_argument("--start", type=float, default=0)
    extract.add_argument("--duration", type=float, default=120)
    fit = commands.add_parser("fit-ridge", help="Fit manually measured time_s,frequency_hz CSV")
    fit.add_argument("ridge", type=Path)
    fit.add_argument("--sound-speed", type=float, default=343)
    imp = commands.add_parser(
        "import-tracks", help="Convert normalized WGS84 track CSV to local ENU"
    )
    imp.add_argument("source", type=Path)
    imp.add_argument("--output", type=Path, required=True)
    imp.add_argument(
        "--origin", type=float, nargs=3, metavar=("LAT", "LON", "ELLIPSOID_M"), required=True
    )
    imp.add_argument("--time-origin", required=True, help="ISO timestamp with Z or UTC offset")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "demo":
            path = create_case(args.output, args.seed, args.noise_only, args.source_drift_hz)
            print(f"Created {path}\nFictional data. truth.json is for evaluation only.")
        elif args.command == "run":
            if args.output.exists() and any(args.output.iterdir()):
                raise ValueError("Choose an empty output directory to preserve previous results.")
            case = load_case(args.case)

            def progress(done, total):
                if not args.quiet:
                    print(f"Scored {done}/{total} locations", file=sys.stderr, flush=True)

            result, spec, ix = search(case, progress=progress)
            report = write_report(case, result, spec, ix, args.output)
            print(
                f"{result['status']}: {result['supported_candidate_count']} supported grid points."
            )
            print(f"Report: {report.resolve()}")
            if result["rows"]:
                top = result["rows"][0]
                print(
                    f"Leading ENU: ({top['east_m']:.0f}, {top['north_m']:.0f}, "
                    f"{top['up_m']:.0f}) m; clock +{top['clock_offset_s']:.2f} s; "
                    f"score {top['score_db']:.2f} dB. This is not a verified location."
                )
        elif args.command == "inspect":
            if args.output.exists():
                raise ValueError("Output already exists; choose a new filename.")
            fs, audio, metadata = read_audio(args.audio, args.channel)
            spec = spectrogram(audio, fs, args.window, args.hop, args.max_hz)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            draw_spectrogram(spec, args.output)
            print(json.dumps(metadata, indent=2))
            print(f"Saved {args.output}")
        elif args.command == "extract":
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                raise ValueError("Install FFmpeg and put ffmpeg on PATH, or supply a PCM WAV.")
            if not args.media.is_file() or args.output.exists():
                raise ValueError("Input must exist and output must be new.")
            if not 0 <= args.start < 1e7 or not 0 < args.duration <= 1800:
                raise ValueError("Use a nonnegative start and duration in (0, 1800] seconds.")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Local path only; argument array prevents shell interpretation. Preserve channels.
            subprocess.run(
                [
                    ffmpeg,
                    "-nostdin",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-n",
                    "-ss",
                    str(args.start),
                    "-i",
                    str(args.media.resolve()),
                    "-t",
                    str(args.duration),
                    "-map",
                    "0:a:0",
                    "-vn",
                    "-ar",
                    "8000",
                    "-c:a",
                    "pcm_s16le",
                    "-f",
                    "wav",
                    str(args.output.resolve()),
                ],
                check=True,
                timeout=300,
            )
            print(
                f"Saved {args.output}. Recording-relative zero is now media +{args.start} seconds."
            )
        elif args.command == "fit-ridge":
            if not 300 <= args.sound_speed <= 370:
                raise ValueError("Sound speed must be between 300 and 370 m/s.")
            print(json.dumps(fit_ridge(args.ridge, args.sound_speed), indent=2, allow_nan=False))
        elif args.command == "import-tracks":
            count = import_tracks(args.source, args.output, args.origin, args.time_origin)
            print(
                f"Converted {count} samples. Record this origin/time basis in your case manifest."
            )
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0
