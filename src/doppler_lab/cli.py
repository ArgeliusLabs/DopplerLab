import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from pyproj.exceptions import ProjError
from rasterio.errors import RasterioError

from . import __version__
from .adsb import capture, normalize
from .archive import download_day
from .audio import read_audio, spectrogram
from .broad import (
    REGIONS,
    build_index,
    export_candidate,
    filter_candidates,
    shortlist,
    subset_index,
)
from .case import load_case
from .importers import import_tracks
from .measure import fit_ridge
from .media import review_media
from .replay import download_window
from .report import draw_spectrogram, write_report
from .search import search
from .synthetic import create_case
from .terrain import Terrain, download_terrain, prepare_observers


def parser():
    root = argparse.ArgumentParser(
        description="Argelius Doppler Lab: aircraft-audio investigation toolkit."
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Generate an original fictional practice case")
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
    review = commands.add_parser(
        "review-media", help="Review a long local recording in timed audio/spectrogram chunks"
    )
    review.add_argument("media", type=Path)
    review.add_argument("--output", type=Path, required=True)
    review.add_argument("--chunk-seconds", type=float, default=300)
    review.add_argument("--overlap-seconds", type=float, default=20)
    review.add_argument("--max-minutes", type=float, default=120)
    review.add_argument("--start-utc", help="Override sample-zero time, with Z or UTC offset")
    review.add_argument("--clock-uncertainty", type=float, default=60)
    review.add_argument("--ffmpeg", default="ffmpeg")
    review.add_argument("--ffprobe", default="ffprobe")
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
    collect = commands.add_parser(
        "capture-adsb", help="Save current adsb.lol aircraft positions for a local experiment"
    )
    collect.add_argument("--latitude", type=float, required=True)
    collect.add_argument("--longitude", type=float, required=True)
    collect.add_argument("--radius-nm", type=int, default=20)
    collect.add_argument("--duration", type=float, default=600, help="Seconds, up to 1800")
    collect.add_argument(
        "--interval",
        type=float,
        default=10,
        help="Seconds between requests; respect provider limits",
    )
    collect.add_argument("--output", type=Path, required=True)
    norm = commands.add_parser(
        "normalize-adsb", help="Prepare geographic tracks from captures or historical readsb traces"
    )
    norm.add_argument("sources", type=Path, nargs="+")
    norm.add_argument("--format", choices=["capture", "readsb-trace"], required=True)
    norm.add_argument("--start", required=True, help="Start timestamp with Z or UTC offset")
    norm.add_argument("--end", required=True, help="End timestamp with Z or UTC offset")
    norm.add_argument(
        "--bounds", type=float, nargs=4, metavar=("SOUTH", "WEST", "NORTH", "EAST"), required=True
    )
    norm.add_argument("--max-gap", type=float, default=5)
    norm.add_argument(
        "--conflicts",
        choices=["error", "quarantine"],
        default="error",
        help="Fail on conflicting fixes, or explicitly exclude and audit the whole aircraft",
    )
    norm.add_argument("--output", type=Path, required=True)
    download = commands.add_parser(
        "download-day", help="Download one adsb.lol global UTC-day archive"
    )
    download.add_argument(
        "--date", required=True, help="UTC date YYYY-MM-DD, after archive publication"
    )
    download.add_argument("--instance", choices=["prod-0", "prod-1", "staging-0"], default="prod-0")
    download.add_argument("--max-gb", type=float, default=6, help="Maximum download in decimal GB")
    download.add_argument("--output", type=Path, required=True)
    window = commands.add_parser(
        "download-window",
        help="Acquire a local historical hour through public replay and detailed traces",
    )
    window.add_argument("--start", required=True)
    window.add_argument("--end", required=True)
    window.add_argument(
        "--bounds", type=float, nargs=4, required=True, metavar=("SOUTH", "WEST", "NORTH", "EAST")
    )
    window.add_argument("--padding", type=float, default=180)
    window.add_argument("--max-gb", type=float, default=1)
    window.add_argument("--max-aircraft", type=int, default=150)
    window.add_argument("--max-gap", type=float, default=5)
    window.add_argument("--conflicts", choices=["error", "quarantine"], default="error")
    window.add_argument("--output", type=Path, required=True)
    terrain = commands.add_parser(
        "download-terrain", help="Download USGS 3DEP DEMs and required height-correction grids"
    )
    terrain.add_argument(
        "--bounds", type=float, nargs=4, required=True, metavar=("SOUTH", "WEST", "NORTH", "EAST")
    )
    terrain.add_argument("--max-gb", type=float, default=2)
    terrain.add_argument("--output", type=Path, required=True)
    terrain_point = commands.add_parser("terrain-point", help="Check an offline terrain height")
    terrain_point.add_argument("terrain", type=Path)
    terrain_point.add_argument("--latitude", type=float, required=True)
    terrain_point.add_argument("--longitude", type=float, required=True)
    observers = commands.add_parser(
        "prepare-observers", help="Make terrain-following local receiver candidates"
    )
    observers.add_argument("terrain", type=Path)
    observers.add_argument(
        "--bounds", type=float, nargs=4, required=True, metavar=("SOUTH", "WEST", "NORTH", "EAST")
    )
    observers.add_argument("--spacing-m", type=float, default=100)
    observers.add_argument("--origin", type=float, nargs=3, metavar=("LAT", "LON", "ELLIPSOID_M"))
    observers.add_argument("--output", type=Path, required=True)
    for command in (terrain_point, observers):
        command.add_argument(
            "--microphone-height",
            type=float,
            default=1.5,
            help="Metres above bare ground (default 1.5)",
        )
        command.add_argument(
            "--height-offset",
            type=float,
            default=0,
            help="Metres added for a documented height-sensitivity run",
        )
    index = commands.add_parser(
        "index-archive", help="Stream split archive parts into a regional SQLite index"
    )
    index.add_argument("parts", type=Path, nargs="+")
    area = index.add_mutually_exclusive_group(required=True)
    area.add_argument("--region", choices=list(REGIONS))
    area.add_argument("--bounds", type=float, nargs=4, metavar=("SOUTH", "WEST", "NORTH", "EAST"))
    index.add_argument("--start", required=True)
    index.add_argument("--end", required=True, help="Exclusive end timestamp with Z or UTC offset")
    index.add_argument("--padding-km", type=float, default=30)
    index.add_argument("--max-gap", type=float, default=30)
    index.add_argument("--output", type=Path, required=True)
    subset = commands.add_parser(
        "subset-index", help="Reuse a completed index for a smaller receiver region"
    )
    subset.add_argument("index", type=Path)
    subset.add_argument(
        "--bounds", type=float, nargs=4, required=True, metavar=("SOUTH", "WEST", "NORTH", "EAST")
    )
    subset.add_argument("--output", type=Path, required=True)
    screen = commands.add_parser(
        "shortlist", help="Screen regional flight pairs by relative sound-arrival timing"
    )
    screen.add_argument("index", type=Path)
    receiver = screen.add_mutually_exclusive_group(required=True)
    receiver.add_argument("--terrain", type=Path, help="Offline download-terrain bundle")
    screen.add_argument(
        "--interval",
        type=float,
        required=True,
        help="Seconds between two measured CPA audio landmarks",
    )
    screen.add_argument(
        "--tolerance", type=float, default=10, help="Landmark interval uncertainty, in seconds"
    )
    screen.add_argument("--grid-km", type=float, default=5)
    screen.add_argument("--radius-km", type=float, default=10)
    receiver.add_argument(
        "--receiver-height",
        type=float,
        help="Assumed WGS84 ellipsoid height, metres",
    )
    screen.add_argument(
        "--microphone-height",
        type=float,
        default=1.5,
        help="Metres above DEM ground (default 1.5; requires --terrain)",
    )
    screen.add_argument(
        "--height-offset", type=float, default=0, help="Terrain height-sensitivity offset, metres"
    )
    screen.add_argument("--sound-speed", type=float, default=343)
    screen.add_argument("--min-speed", type=float, default=25)
    screen.add_argument("--max-speed", type=float, default=300)
    screen.add_argument("--max-evaluations", type=int, default=500_000_000)
    screen.add_argument("--max-passages", type=int, default=5_000_000)
    screen.add_argument("--max-pairs", type=int, default=500_000)
    screen.add_argument("--output", type=Path, required=True)
    export = commands.add_parser(
        "export-candidate", help="Prepare a shortlisted pair for local matching and review"
    )
    export.add_argument("index", type=Path)
    export.add_argument("screening", type=Path)
    export.add_argument("--candidate", type=int, required=True)
    export.add_argument("--window", type=float, default=180)
    export.add_argument("--output", type=Path, required=True)
    narrow = commands.add_parser(
        "filter-candidates",
        help="Apply measured per-event speed and slant bounds to an existing shortlist",
    )
    narrow.add_argument("screening", type=Path)
    for option in ["speed-a", "speed-b", "slant-a", "slant-b"]:
        narrow.add_argument(
            "--" + option,
            type=float,
            nargs=2,
            required=True,
            metavar=("MIN", "MAX"),
            help="Metres/second for speed; metres for slant distance",
        )
    narrow.add_argument("--output", type=Path, required=True)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    last_update = [0.0]

    def status(value):
        if time.monotonic() - last_update[0] >= 10:
            print(json.dumps(value), file=sys.stderr, flush=True)
            last_update[0] = time.monotonic()

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
        elif args.command == "review-media":
            result = review_media(
                args.media,
                args.output,
                args.chunk_seconds,
                args.overlap_seconds,
                args.max_minutes,
                args.start_utc,
                args.clock_uncertainty,
                args.ffmpeg,
                args.ffprobe,
                progress=lambda value: print(json.dumps(value), file=sys.stderr, flush=True),
            )
            print(
                json.dumps(
                    {
                        "status": result["status"],
                        "chunks": len(result["chunks"]),
                        "review": str((args.output / "review.html").resolve()),
                        "timing": result["timing"],
                    },
                    indent=2,
                )
            )
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
        elif args.command == "capture-adsb":
            print(
                f"Capturing current aircraft positions to {args.output}; no audio is recorded.",
                flush=True,
            )
            result = capture(
                args.output,
                args.latitude,
                args.longitude,
                args.radius_nm,
                args.duration,
                args.interval,
            )
            print(json.dumps(result, indent=2))
            if result["status"] != "complete":
                return 130
        elif args.command == "normalize-adsb":
            result = normalize(
                args.sources,
                args.output,
                args.format,
                args.start,
                args.end,
                args.bounds,
                args.max_gap,
                conflicts=args.conflicts,
            )
            print(json.dumps(result, indent=2))
            if not result["segments"]:
                print(
                    "No usable segments. Review summary.json; no geometry-ready tracks were produced.",
                    file=sys.stderr,
                )
                return 2
        elif args.command == "download-window":
            result = download_window(
                args.start,
                args.end,
                args.bounds,
                args.output,
                args.padding,
                args.max_gb,
                args.max_aircraft,
                args.max_gap,
                args.conflicts,
                progress=status,
            )
            print(
                json.dumps(
                    {
                        "status": result["status"],
                        "aircraft_count": result.get("aircraft_count", 0),
                        "downloaded_bytes": result.get("downloaded_bytes", 0),
                        "missing_resources": result.get("missing_resources", []),
                        "output": str(args.output.resolve()),
                    },
                    indent=2,
                )
            )
            if result["status"] != "complete":
                return 2
        elif args.command == "download-day":
            result = download_day(
                args.date,
                args.output,
                args.instance,
                args.max_gb,
                lambda done, total: status({"downloaded_bytes": done, "total_bytes": total}),
            )
            print(json.dumps(result, indent=2))
        elif args.command == "index-archive":
            result = build_index(
                args.parts,
                args.output,
                REGIONS[args.region] if args.region else args.bounds,
                args.start,
                args.end,
                args.padding_km,
                args.max_gap,
                status,
            )
            print(json.dumps(result, indent=2))
        elif args.command == "download-terrain":
            print(
                json.dumps(
                    download_terrain(args.bounds, args.output, args.max_gb, status), indent=2
                )
            )
        elif args.command == "terrain-point":
            terrain = Terrain(args.terrain)
            height = terrain.sample(
                [args.latitude], [args.longitude], args.microphone_height, args.height_offset
            )[0]
            print(
                json.dumps(
                    {
                        "latitude_deg": args.latitude,
                        "longitude_deg": args.longitude,
                        "receiver_height_ellipsoid_m": float(height),
                        "terrain": terrain.provenance(args.microphone_height, args.height_offset),
                    },
                    indent=2,
                )
            )
        elif args.command == "prepare-observers":
            print(
                json.dumps(
                    prepare_observers(
                        args.terrain,
                        args.output,
                        args.bounds,
                        args.spacing_m,
                        args.origin,
                        args.microphone_height,
                        args.height_offset,
                    ),
                    indent=2,
                )
            )
        elif args.command == "shortlist":
            result = shortlist(
                args.index,
                args.output,
                args.interval,
                args.tolerance,
                args.grid_km,
                args.radius_km,
                args.receiver_height,
                args.sound_speed,
                args.min_speed,
                args.max_speed,
                args.max_evaluations,
                args.max_passages,
                args.max_pairs,
                status,
                terrain_path=args.terrain,
                microphone_height_m=args.microphone_height,
                height_offset_m=args.height_offset,
            )
            print(json.dumps(result, indent=2))
        elif args.command == "subset-index":
            print(json.dumps(subset_index(args.index, args.output, args.bounds), indent=2))
        elif args.command == "export-candidate":
            print(
                json.dumps(
                    export_candidate(
                        args.index, args.screening, args.candidate, args.output, args.window
                    ),
                    indent=2,
                )
            )
        elif args.command == "filter-candidates":
            print(
                json.dumps(
                    filter_candidates(
                        args.screening,
                        args.output,
                        args.speed_a,
                        args.speed_b,
                        args.slant_a,
                        args.slant_b,
                    ),
                    indent=2,
                )
            )
    except (
        ValueError,
        KeyError,
        OSError,
        ProjError,
        RasterioError,
        subprocess.SubprocessError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0
