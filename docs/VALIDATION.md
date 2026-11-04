# Validation record — 3 November 2026

## Original v0.1.0 checks

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

The 0.2.0 release adds 13 tests covering binary-safe split archives, gzip detection
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
The [real-data benchmark](REAL_DATA_BENCHMARK.md) records completed U.S., European and
Tucson index/screening measurements, separately from the synthetic acoustic benchmark.
Two actual provider trajectories also passed local export and kinematic checks with an
explicitly reviewed 30-second maximum gap. That verifies the data handoff, not either
aircraft's association with a recording. See [BROAD_SEARCH.md](BROAD_SEARCH.md) for the implemented workflow
and explicit limits. The live two-second polling attempt on November 3 stopped at
HTTP 429 after ten snapshots, so it does not count as a completed capture or field test.

**Testing in progress:** the experimental release is available for community evaluation.
The first original iPad recording has now been analyzed; the exploratory outcome was
[insufficient acoustic evidence](FIELD_TEST_2026_11.md). Real-world accuracy remains unvalidated.
Native build checks exercise archive indexing, screening and handoff, followed by
fictional audio generation, spectrogram inspection, local matching and an embedded
HTML report from outside the source checkout. Packaging success does not establish
real-world location accuracy.

For development source commit `0b7e47a`, all four Python/OS test jobs and all four native
build/smoke jobs passed in [run 41739232065](https://github.com/ArgeliusLabs/DopplerLab/actions/runs/41739232065).
The local Windows development executable also passed that smoke workflow outside the
checkout. See [BINARIES.md](BINARIES.md) for target OS versions and artifact availability.

## Native onboarding checks in 0.2.1

The quick-start commands were run against the actual Windows 0.2.1 executable extracted
from its archive. The generated seed-7 case recovered A/B, (100, -200, 0) m and an
11.25-second clock offset. The noise-only practice still returned a ranked hypothesis
with weaker line contrast, and neither run accepted a location. The full lab's manual
one-event and 331 m/s manifest edits were also exercised through that executable.

The bundled README, quick start, practice and platform guide were checked for missing
local links. Source and student archives include the new guides. These checks validate
onboarding and packaging; they do not add field-accuracy evidence. Each published
patch still requires the full automated and native-platform CI checks.

## Terrain checks in 0.3.0

The expanded suite checks bilinear pixel-centre sampling, axis order, geoid-conversion
sign, microphone height and sensitivity offsets, observer frames, hash failures, nodata,
bounded downloads, complete offline bundles and terrain heights carried into screening
and local handoffs. The Windows executable passed these terrain operations through the
native smoke workflow and matched the source implementation on the actual Tucson DEM.

The Tucson acquisition retained two current USGS 3DEP tiles and the selected PROJ
operation's correction grids: 828,398,104 downloaded bytes in 137.089 seconds. Three
same-reference sample points differed from the independent USGS point service by
0.002, 1.813 and 1.606 metres; that service used finer source data. This is a consistency
check, not a survey accuracy estimate.

A 1-km grid over the existing Tucson flight index produced 1,707 terrain receivers and
54,200 coarse candidates for a hypothetical 920-second interval. A separate local grid
prepared 12,882 terrain-following observers. Neither used the owner's recording.
See the [terrain guide](TERRAIN.md) and
[recorded benchmark](../examples/terrain-benchmark.json) for sources, hashes and limitations.

## Original-recording workflow in 0.4.0

All 58 local automated tests pass. New checks cover timezone-aware recording metadata,
GPS-value exclusion, midnight date selection, replay decoding, overlapping historical/
current trace handling, rate-limit aborts and explicit whole-aircraft quarantine.

The live `download-window` command acquired the actual recording window in 175.658
seconds (58,933,188 bytes), producing 47 segments and 1,885 positions. The Windows
standalone executable processed the full 5.89 GB recording into 11 review chunks; every
derived WAV hash and original-media offset matched the Python implementation. Its
full native smoke workflow also passed. Review assets were checked (11 audio elements,
22 valid chart images, 34 resolved local references). Browser security blocked opening
the local HTML file, so browser playback/layout was not interactively verified.

The acoustic comparison was negative: channel disagreement, a reversed-event control
scoring at least as well as the original grid search, and weak finer-resolution
reference checks. See the [complete outcome and limitations](FIELD_TEST_2026_11.md).
Publication requires all Windows/Linux test jobs and all four native build/smoke jobs.

## Published v0.4.1 checkpoint

Release [v0.4.1](https://github.com/ArgeliusLabs/DopplerLab/releases/tag/v0.4.1) was
published from commit `35769d7252ad6277c30ed44434ab6b14b0b0e8f0`.
[Run 41764948654](https://github.com/ArgeliusLabs/DopplerLab/actions/runs/41764948654)
completed all nine jobs successfully: 58 tests on each Windows/Linux and Python
3.11/3.13 combination, native build/smoke checks on Windows, Linux, Intel Mac and
Apple Silicon, followed by publication.

This patch includes the benchmark chart and JSON evidence referenced by the native
guides, and checks bundled local Markdown links during native smoke tests. All ten
public release assets were present; the nine entries in the downloaded `SHA256SUMS.txt`
matched their GitHub asset digests. That comparison checks the published inventory;
users should still hash their own downloads.

These are software and packaging checks. The acoustic model and negative field outcome
are unchanged. Real-world location recovery, blind accuracy and false-localization
rates remain unproven; see the [field-validation issue](https://github.com/ArgeliusLabs/DopplerLab/issues/2).
