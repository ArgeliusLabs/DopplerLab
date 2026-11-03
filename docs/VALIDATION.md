# Validation record — 3 November 2026

## What was actually checked

The implementation was run locally on Windows with Python 3.13.11, NumPy 2.5.4,
SciPy 1.18.1 and Matplotlib 3.11.2. The automated suite passed **26 tests** at this
checkpoint. Ruff lint and formatting checks passed. The command-line entry point was
installed and exercised. The built wheel was installed and run from outside the source
directory; it recovered the same fictional pair and coarse location. `pip check` found
no broken requirements. The reference dependencies are recorded separately; the
initial local validation preceded the remote GitHub Actions run. Check the
[Actions history](https://github.com/ArgeliusLabs/DopplerLab/actions) for current platform results.

Tests cover an independent analytic retarded-time solution, Doppler sign and delayed
CPA, no time extrapolation, invalid timestamps/gaps/speeds, coordinate transformations,
mirror ambiguity, translation invariance, phase-inverted stereo, persistent hum,
out-of-band rejection, independent synthetic recovery, the shared-clock constraint,
noise controls, ridge fitting, input-path confinement, UTC requirements and malformed cases.

## Synthetic benchmark

The generator uses analytic curved paths and solves emission time by bisection to
construct the audio phase. The solver receives rounded trajectory samples every 2 s
and uses PCHIP interpolation with a 0.25 s modeling interval. These are separate
numerical paths, but both assume still, uniform air and direct propagation. This is
an engineering benchmark, not independent field validation.

The baseline includes two flyovers, two decoy tracks, broadband noise, persistent 60 Hz
hum and harmonics. The hidden observer is `(137, -213, 0)` m in a fictional local frame;
the first audio sample corresponds to track time 11.25 s. The solver never opens
`truth.json`.

Each complete coarse search evaluates 289 receiver points and nine common clock
offsets, with per-event source-tone and aircraft alternatives. There is no trajectory
or frequency-support loss in these benchmark cases. Each control reruns all of its
declared nuisance fits. No probabilities are derived from the scores.

| Condition | Best contrast (dB) | Position error (m) | Locations within 2 dB of peak | Observation |
| --- | ---: | ---: | ---: | --- |
| Baseline, two flyovers | 26.44 | 39.22 | 5 | Correct A/B pair and 11.25 s clock |
| Assumed sound speed 331 m/s | 23.23 | 231.81 | 12 | High score despite material model bias |
| Assumed sound speed 355 m/s | 23.54 | 129.38 | 11 | Estimate changes with propagation assumption |
| First flyover only | 27.38 | 39.22 | 18 | Same winning grid point, broader alternatives, clock 10.75 s |
| Reversed-time spectrogram | 1.60 | Not applicable | 289 | Physical curves no longer match well |
| Noise seed 100 | 1.77 | Not applicable | 289 | Still has a numerical winner |
| Noise seed 101 | 1.68 | Not applicable | 289 | Still has a numerical winner |
| Noise seed 102 | 1.63 | Not applicable | 289 | Still has a numerical winner |
| Correct first aircraft excluded | 19.01 | 767.68 | 3 | Wrong aircraft can yield an apparently concentrated result |
| Source pitch drifts 4 Hz per minute | 22.06 | 64.33 | 14 | Constant-tone model absorbs some drift into location/clock |

The near-peak counts are descriptive, not confidence-region sizes. They are especially
instructive when the true first aircraft is excluded: only three locations are near
the wrong maximum. A narrow peak does not imply a correct answer.

The coarse baseline search took about **1.68 s** on the local machine, excluding fixture
generation and report rendering. This is one timing, not a performance guarantee.
The retained benchmark JSON includes actual timings, effective parameters and input
hashes for every condition. Different machines and package versions may differ.

## Local refinement

The helper refined a 300 m × 300 m square around the coarse leader using 25 m spacing
and a narrower 0.25 s clock grid. It searched 169 locations and returned `(150, -200, 0)` m,
clock 11.50 s, score 26.86 dB: **18.38 m** horizontal error in the fictional example.
This did not read truth, but it refined only the leading mode. It does not establish
18 m field accuracy or exclude other modes outside the local refinement.

## Provided video

The provided WebM was inspected with FFprobe: 1,751.548 seconds, 3840×2160 AV1 video
and 48 kHz Opus audio. A 60-second excerpt starting at 1,530 seconds was decoded through
the toolkit and plotted. This verifies real-media ingestion and visualization only.
It does **not** validate a flight association or a microphone location from that excerpt.
The edited presentation's timing cannot be substituted for the original field recording.

The full transcript and sampled video frames informed the research review. No downloaded
video, subtitle text, video screenshots, source audio or derived source spectrogram is
included in the public release archive. Its images and demonstration audio are original.

## Report inspection

The generated spectrogram overlay and score map were opened and visually inspected.
The report embeds both figures and escapes case-supplied text. HTML structure and
embedded image integrity were checked programmatically. The managed browser blocked
the local file protocol, so a rendered-browser screenshot was **not** obtained. The
local HTML can be opened directly by a user in a permitted browser; no external assets
are needed.

## Reproduce

From an installed source checkout:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe scripts\benchmark.py --output work\reproduction
```

Use a new output directory. Compare the full benchmark, not only the successful baseline.
The published example JSON and report are under `examples/`; the generator remains the
authoritative recipe. The [field protocol](FIELD_PROTOCOL.md) describes the next required
validation stage. Real-world precision, false-localization rates, robustness to wind,
terrain uncertainty, codecs and unconstrained country-scale search remain unestablished.

## Development acquisition and screening checks

The 0.2.0.dev1 branch adds 13 tests covering binary-safe split archives, gzip detection
despite `.json` filenames, streamed trace decoding, source hashes, geometric-height
requirements, delayed closest approach, repeat flyovers, two-event candidate retention,
wrong-interval rejection, local track export, download integrity, altered candidate
files, truncated archives and resource-limit failure states. The full local suite now
has **39 tests**. Regional subsetting also verifies that parent evidence is
preserved and bounds cannot expand outside its indexed region. These checks use original fictional fixtures and mocked HTTP;
they are not real-recording accuracy measurements.
The per-event speed/slant filter is checked for retained true candidates, preserved
candidate IDs, successful export and rejection under incompatible speed bounds.

The complete November 2 public global archive was downloaded and hashed in 291.507 s.
Regional index and screening measurements are tracked separately from the synthetic
acoustic benchmark. See [BROAD_SEARCH.md](BROAD_SEARCH.md) for the implemented workflow
and explicit limits. The live two-second polling attempt on November 3 stopped at
HTTP 429 after ten snapshots, so it does not count as a completed capture or field test.

Two original recording cases are still required before the next public release.
Native build checks exercise archive indexing, screening and handoff, followed by
fictional audio generation, spectrogram inspection, local matching and an embedded
HTML report from outside the source checkout. Packaging success does not establish
real-world location accuracy.
