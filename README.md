# Argelius Doppler Lab

![Argelius Doppler Lab: aircraft sounds, testable hypotheses](assets/banner.svg)

**Turn aircraft sounds into testable location hypotheses. Learn when the evidence is insufficient.**

An open-source aircraft-audio investigation toolkit, with a 110-minute OSINT teaching lab, inspired by
[colsto's aircraft Doppler demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI).
Original implementation by Argelius Labs. No affiliation with colsto is implied.

The package generates fictional flight tracks and noisy audio, predicts the sound each
candidate microphone position would receive, and ranks the matches under one shared
recording clock. Every run produces an inspectable HTML report, spectrogram overlays,
a score map, complete candidate CSV and a JSON record with input hashes.

**Status: experimental investigation software.** Synthetic validation is not evidence of
real-world location accuracy. The solver reports hypotheses, never an accepted location.
The development branch adds daily archive acquisition and regional candidate screening;
it does not automatically identify aircraft from audio. The published v0.1.0 release
contains the local matcher. Real-recording validation for the next release is pending.

**How do you start with only a country or continent?** Read the
[investigation workflow](docs/INVESTIGATION_WORKFLOW.md) for aircraft-data acquisition,
relative timing, broad candidate selection and local refinement. The
[download and storage guide](docs/DATA_VOLUME.md) gives verified archive sizes and
transfer estimates. The [real-data benchmark](docs/REAL_DATA_BENCHMARK.md) records actual
U.S., European and Tucson indexing/search measurements. These guides distinguish the
full technique from the features
available in the published release and the development branch.

**Development workflow:** [run a broad-area search](docs/BROAD_SEARCH.md) or read about
[native Windows, Linux and macOS candidates](docs/BINARIES.md). Builds on `main` do not
automatically publish a release.

## Build it with us

This is an early community project. Corrections, reproducible failures, classroom
feedback and careful field validation are welcome. Start with the
[community roadmap](docs/ROADMAP.md) and [contribution guide](CONTRIBUTING.md).
Use [Issues](https://github.com/ArgeliusLabs/DopplerLab/issues) for bugs, proposals,
questions and shared experiments. Include unsuccessful experiments too.

[Download the experimental release](https://github.com/ArgeliusLabs/DopplerLab/releases)
for the complete source ZIP, portable student pack, Python wheel and checksums.

## Start in five minutes

Requires Python 3.11 or later. Internet access is needed to install packages; the demo
runs offline afterward. FFmpeg is optional, needed only to decode non-WAV media.
Download a release or clone the repository:

```bash
git clone https://github.com/ArgeliusLabs/DopplerLab.git
cd DopplerLab
```

Then run from the repository directory:

Windows PowerShell (no activation or execution-policy change needed):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\doppler-lab.exe demo --output work\case
.\.venv\Scripts\doppler-lab.exe run work\case\case.json --output work\result
Start-Process work\result\report.html
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/doppler-lab demo --output work/case
.venv/bin/doppler-lab run work/case/case.json --output work/result
# Open work/result/report.html in your browser.
```

The generated case uses fictional local east/north/up coordinates, not a real person's
location. Keep `truth.json` closed until the evaluation step. Output directories must
be empty so previous experiments remain intact.

![Original synthetic spectrogram with predicted aircraft curves](assets/demo-spectrogram.png)

*Original fictional data. The mint lines are the leading model's predictions; this
demonstration does not establish real-world geolocation accuracy.*

For a no-install preview, open [the included report](examples/report/report.html).
GitHub displays HTML as source; download the student pack and open its report locally.
The [portable student pack guide](docs/STUDENT_PACK.md) describes the interpretation-only option.

## What is included

| Capability | Scope |
| --- | --- |
| Audio inspection | PCM WAV, explicit channel selection, anti-aliased resampling, spectrogram PNG |
| Media extraction | Local video/audio through FFmpeg, with explicit clip start and duration |
| Ideal flyby measurement | Fit a manually traced frequency ridge; report conditional speed/slant estimates |
| Physics | 3D trajectories, variable radial velocity, retarded sound arrival, one common clock |
| Matching | Small declared receiver grids, supplied candidate aircraft, per-event tone sweeps |
| Geographic import | WGS84 ellipsoid heights and explicit UTC to one local ENU frame |
| Daily archives (development) | Verified downloads; stream compressed traces into a regional SQLite index |
| Broad screening (development) | Spatially indexed, delayed-closest-approach pairs with a shared relative interval and explicit work budgets |
| Audio constraints (development) | Filter existing candidates by separate speed/slant bounds for each flyover, with source hashes and retained alternatives |
| Local handoff (development) | Export candidate tracks, coordinate origin and time basis for analyst-reviewed local matching |
| Evidence | Source hashes, full configuration, per-event scores, spatial alternatives, unsupported trials |
| Classroom | Student handout, instructor guide, answer key, rubric, extensions and a blind field protocol |

Start with [the investigation workflow](docs/INVESTIGATION_WORKFLOW.md),
[the public guide](docs/GUIDE.md), or [the research review](docs/RESEARCH.md).
For teaching, use [the student lab](docs/STUDENT_LAB.md).
For supplied recordings, read [data preparation](docs/DATA.md) before building a case.
See [validation](docs/VALIDATION.md) for measured results and their limits.

## The technique

For a stationary microphone and still, uniform air:

```text
arrival time = emission time + source-to-microphone distance / sound speed
heard frequency = source frequency / (1 + receding radial speed / sound speed)
```

Predict the **arrival-time** curve from each trajectory, compare it with spectral
energy in the recording, and use the same clock offset for all independent flyovers.
The second event cannot slide freely to make a bad location fit.
The [method document](docs/METHOD.md) gives equations, assumptions and implementation details.

## Before interpreting a match

Run controls, inspect each event, preserve competing locations, and validate with
independent evidence. A score is not a probability. Source pitch drift, wind, reflections,
bad heights, missing tracks, clock error and incomplete search bounds can all mislead.
Not seeing a tone is not proof that no aircraft passed.

Use recordings you own or have permission to study. Do not use the toolkit to expose private
people's locations. The supplied exercise is fictional and fully redistributable.

## Development

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe scripts\benchmark.py --output work\benchmark
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Code, original documentation and generated
fictional fixtures are MIT licensed. Third-party audio, video, flight databases and
terrain retain their own licenses; they are not bundled or relicensed by this project.

Related work: [DOPPLERGEIST](https://github.com/1337isnot1337/DOPPLERGEIST) is a separate,
broader experimental implementation. This repository emphasizes inspectable investigation
experiments, auditable candidate preparation and a reproducible classroom lab. No source
code from that project was copied.
