# Running a broad-area aircraft search

This guide describes **the experimental 0.2.0 release**. Testing is in progress.
The new workflow downloads a daily archive, builds a regional index, screens flight
pairs by relative sound-arrival timing, and exports candidates for local Doppler matching.
It does not automatically recognize aircraft in audio or establish a location from an
unreviewed recording. Original-recording field tests are still being prepared, and
real-world location accuracy remains unvalidated.

## Inputs you need

- An original, continuous recording, a supported date/UTC interval and a geographic region.
- Two separate flyovers, with an estimated interval between comparable acoustic landmarks
  and an honest uncertainty range. This screen uses delayed closest approach; the loudest
  sample is not necessarily that landmark. Use the spectrogram/ridge analysis to assess it.
- A declared receiver **WGS84 ellipsoid height**, with sensitivity runs if uncertain.
  The coarse screen uses one height across its region. It has no terrain model, so a
  flat-height country-wide run is an exploratory screen with known completeness limits.
- Enough local disk space for the archive, index and results. See [DATA_VOLUME.md](DATA_VOLUME.md).

The commands below are reproducible examples using a complete archived UTC day and a
**hypothetical 920-second interval**. They are a performance/exploration example, not a
claim that our own real recording has those events. Replace bounds, times, interval,
height and source assumptions with evidence from your investigation.

## 1. Download one UTC day

After installing from the current branch, run `doppler-lab` from your environment.
On Windows without activating the environment, replace it with
`.\.venv\Scripts\doppler-lab.exe`. A native candidate uses `.\doppler-lab.exe`.

```text
doppler-lab download-day --date 2026-11-02 --output work/archive-2026-11-02
```

The default download budget is 6 decimal GB. The command reads public GitHub release
metadata, validates the expected daily asset names, checks disk space and downloads all
parts of one production release. It records exact bytes, SHA-256, timings and provider
attribution in `download.json`. If the provider supplies an asset digest, it is checked.
HTTP errors and mismatched sizes/digests fail the operation; failed files remain marked
`.partial`. Choose a new output directory for a retry. Automated resume is not yet supported.

No account is required for this public archive route, subject to provider availability
and request limits. The date's archive must already have been published. Live API data
and historical releases are separate acquisition routes. Production/staging instances
are not geographical pieces that must all be downloaded.

## 2. Build a regional index

List **every part in suffix order**. For the verified example there are two:

```text
doppler-lab index-archive work/archive-2026-11-02/v2026.11.02-planes-readsb-prod-0.tar.aa work/archive-2026-11-02/v2026.11.02-planes-readsb-prod-0.tar.ab --region conus --start 2026-11-02T00:00:00Z --end 2026-11-03T00:00:00Z --output work/conus-index
```

Use `--region europe` for the European rectangle, or `--bounds SOUTH WEST NORTH EAST`
for your own region. The presets are broad geographic rectangles, not political borders:
CONUS = `24 -125 50 -66`; Europe = `34 -25 72 45`. They deliberately include surrounding
areas. Bounds may not cross the date line or extend beyond 75 degrees latitude.

The importer streams the split tar directly; it makes no joined-tar copy and does not
extract archive paths onto disk. It detects gzip by content, since real archives can
contain compressed files named `.json`. A streaming JSON parser reads individual points.
One index uses one instance/day; make separate indexes for adjacent UTC days and account
for cross-midnight event pairs separately. **Cross-index pairing is not implemented.**

The index retains geometric-height ADS-B ICAO positions inside the padded region/time
window. Pressure-only heights, ground positions, stale points and unsupported sources
are counted rather than silently converted. Tracks split at leg boundaries, conflicting
times and gaps beyond `--max-gap` (default 30 seconds for coarse screening). Segments
need at least four points spanning ten seconds. Dense local fitting has a stricter
default gap limit of five seconds; passing the coarse filter does not establish
sufficient sampling for a local Doppler fit.

Outputs: `index.sqlite` holds compressed numerical segments; `index.json` records source
hashes, filters, counts, time, size and index hash. A failed index cannot be used as a
completed input. Regional padding defaults to 30 km and must cover screening radius
plus grid spacing. The requested time window has an exclusive end; explicitly include
event context and sound-travel padding. The archive cannot supply the adjacent day if
you did not acquire it.

## 3. Screen flight pairs

```text
doppler-lab shortlist work/conus-index/index.sqlite --interval 920 --tolerance 10 --grid-km 10 --radius-km 10 --receiver-height 0 --max-evaluations 1000000000 --max-passages 30000000 --max-pairs 50000000 --output work/conus-screen
```

Here `--receiver-height 0` is an explicit exploratory assumption, not a statement about
actual U.S. terrain. Repeat with supported heights or smaller terrain-compatible regions
before interpreting exclusions. Likewise, a 10 km radius is a configurable assumption;
it is not a universal aircraft audibility limit.

This is the full-region benchmark configuration with explicitly increased work budgets.
It can generate millions of alternatives and substantial disk output. For a quick first
experiment, use the smaller-region `subset-index` example below. The default budgets
are intentionally smaller and may stop a continental run as incomplete; increasing a
budget does not make the resulting candidates more credible.

The screen builds a geographic receiver grid and an ECEF spatial tree. For each recorded
trajectory edge, it checks nearby receiver nodes, calculates piecewise-linear closest
approach and adds `slant_distance / sound_speed`. It retains bracketed local minima,
including separate repeat passes, while merging minima within ten seconds to reduce
duplicates caused by quantization and straight-chord approximation. It requires two
different aircraft IDs for the pair.

The pair join uses a SQLite index on receiver/time, avoiding an unrestricted Cartesian
product of all aircraft. It compares the resulting arrival-time interval with the audio
interval. At a coarse grid node, the test also allows a half-cell-diagonal displacement:

```text
allowed interval error = measurement tolerance
                      + cell radius / first aircraft speed
                      + cell radius / second aircraft speed
                      + 2 * cell radius / sound speed
```

This allowance assumes locally straight, steady flight. It does **not** prove that a
match exists somewhere inside the cell, or guarantee preservation of all matches on
curved/noisy paths. Coarser grids are faster but can retain many more false candidates.
The reported error and allowance are visible for every candidate.

`--min-speed` and `--max-speed` default to 25 and 300 m/s. Bounds must remain below
0.9 times the selected sound speed. Only tighten them when supported by your audio and
aircraft evidence; the software does not infer propeller/jet class automatically.

Outputs:

| File | Purpose |
| --- | --- |
| `candidates.csv` | Every retained receiver/flight-pair combination, timing error, allowance, slant ranges and speeds |
| `passages.sqlite` | Intermediate closest-approach records for inspection |
| `screening.json` | Completion status, index hash, assumptions, timing, work counters and output hashes |

Large candidate CSVs can exceed spreadsheet row limits. Use `filter-candidates` to
stream supported audio constraints through them, and refine justified smaller areas
before inspecting individual candidates. Do not assume a spreadsheet loaded every row.
After trajectory progress messages end, pairing, CSV writing and hashing can still take
several minutes. Wait for a zero exit status and `status: complete` in `screening.json`;
a growing CSV alone is not a completed search.

Candidate IDs are stable row references within that run. Their order is **not a
confidence ranking**. No audio has been scored at this stage, and every result carries
`accepted_location: false`. Adjacent cells and repeated matches are not independent
confirmations. Preserve alternatives and compare detailed fits using consistent settings.

When `fit-ridge` supplies a defensible ideal-model estimate, use its `cpa_arrival_s`
field for each landmark. If you traced separate clips, first add each clip's offset
in the original recording. Subtract the resulting arrival times to get `--interval`;
do not substitute `cpa_emission_s`, which omits the source-to-microphone travel delay.

To refine a smaller receiver area without downloading or reparsing the global archive:

```text
doppler-lab subset-index work/conus-index/index.sqlite --bounds 32.1 -111.2 32.5 -110.6 --output work/tucson-index
doppler-lab shortlist work/tucson-index/index.sqlite --interval 920 --grid-km 1 --receiver-height 0 --output work/tucson-screen
```

These remain hypothetical interval/height examples. The subset must lie inside its
parent region. It preserves intersecting trajectory segments and padding, and records
the parent index's hash. Use the actual shortlist to choose areas; a convenient test
city is not evidence that an unknown recording was made there.

### Apply the two audio measurements

`fit-ridge` reports conditional speed and slant-distance estimates. Inspect its residuals,
conditioning and bound warnings, then choose generous ranges and test their sensitivity.
They are not exact values or statistical confidence intervals. The two aircraft can have
different speeds and distances, so apply separate ranges to the completed shortlist:

```text
doppler-lab filter-candidates work/tucson-screen --speed-a 70 110 --speed-b 90 140 --slant-a 1000 4000 --slant-b 2000 6000 --output work/tucson-filtered
```

These numbers are hypothetical examples; replace them with supported bounds from your
recording. Speed units are metres/second and slant units are metres. The filter streams
the existing CSV rather than recalculating all flight/receiver geometry. Slant bounds
allow the original half-cell diagonal, so coarse grids retain broad alternatives.
Re-run a smaller region at finer spacing when justified.

The filtered folder has its own `screening.json`, parent hashes, filter settings,
input/output counts and `candidates.csv`. Original candidate IDs are preserved. Pass
that folder to `export-candidate` and choose an ID present in its CSV. Filtering cannot
restore tracks excluded by earlier source, time, radius, speed or height assumptions.

## 4. Hand a candidate to the local workflow

```text
doppler-lab export-candidate work/conus-index/index.sqlite work/conus-screen --candidate 1 --output work/candidate-1
```

The handoff verifies the index and candidate hashes, then writes `geographic.csv`,
`tracks.csv` in local ENU coordinates and `handoff.json` with origin, epoch, track IDs,
observed maximum gap and review steps. Export retains a continuous neighborhood around
each candidate's closest approach inside 45 km of the local origin. This keeps the
handoff inside the local solver's 50 km limit. Inspect whether the remaining trajectory
still covers the audio windows; missing context must not be filled by extrapolation.

The handoff deliberately requires the actual audio windows, tone ranges and receiver
terrain before building `case.json`; it does not invent them. Use the generated demo's
manifest as the schema and follow [DATA.md](DATA.md). If the first audio CPA landmark is
at recording time `a`, the candidate suggests the shared clock offset:

```text
offset = candidate first arrival UTC - track epoch UTC - a
```

Search a supported range around that offset and both events together. Run the local
matcher with `doppler-lab run CASE --output RESULT`, inspect each event and repeat for
competing areas. This bridge prepares real tracks; it does not automate the analyst's
audio interpretation or turn a coarse result into an accepted location.

## Work budgets and failure handling

Defaults cap the grid at two million nodes, edge/receiver evaluations at 500 million,
passages at five million and output candidates at 500,000. The latter three have explicit
CLI options. A limit hit produces a **failed/incomplete** manifest and a nonzero exit;
partial results must not be described as a completed search. Use smaller declared areas,
supported filters or explicitly larger budgets, and retain the original failed run.
Tiling must preserve spatial padding and event pairs at time boundaries.
One trajectory is additionally limited to five million edge/receiver pairs, counted
before allocating the neighbor lists. Use a coarser grid or smaller region if that
per-trajectory memory safeguard is reached.

Compressed trace members are limited to 64 MiB and decoded streaming content to 1 GiB
per aircraft/day. The readsb identity/time header must precede the trace array within
the first 64 KiB. Format/size errors stop the index and name the offending trace. These
are resource/schema limits, not claims that an omitted aircraft could not matter.

## Benchmark your hardware

See the [completed real-data benchmark](REAL_DATA_BENCHMARK.md) before choosing a
country-scale workload. It reports the full day's measured download, regional indexing,
candidate counts, storage and elapsed time, including a much smaller Tucson refinement.

Install the optional benchmark extra and wrap any command:

```text
python -m pip install -e ".[benchmark]"
python scripts/measure_command.py --output work/measurement.json -- doppler-lab shortlist work/conus-index/index.sqlite --interval 920 --receiver-height 0 --output work/measured-screen
```

The wrapper saves a log, command, machine details, exit status, wall time and process-tree
RSS sampled every 0.2 seconds. Sampling can miss brief peaks. Report acquisition,
indexing, screening and local fitting separately. A completed archive benchmark with
a hypothetical interval is **not real-recording geolocation validation**.

## Recording a local validation case

Choose a quiet, low-wind period and a stationary recording position. Record continuously
for 20–30 minutes, preserving the original and exact start-time evidence. Two distinct
flyovers in one unedited recording help constrain a shared clock. Do not discard quiet
intervals or stitch clips together without documenting every timing change.

For the first two feasibility cases, make two separate original recordings when useful
flyovers occur; both can have a known time and a small, predeclared region. A later
unknown-clock broad-area demonstration should use multiple events with preserved relative
timing, preferably in one continuous recording. Do not treat sparse historical tracks
near a recording site as a reliable schedule or a prediction of audibility. Quiet
daylight conditions are a practical starting point, but a useful pass is not guaranteed.

For a contemporaneous small-region capture:

```text
doppler-lab capture-adsb --latitude 32.22 --longitude -110.97 --radius-nm 20 --duration 1200 --interval 10 --output work/tucson-live
```

This city-center example records trajectories, not microphone audio. The interval is
not a promise that anonymous API access permits that rate. On 3 November, an initial
two-second polling attempt was stopped after HTTP 429; it yielded only ten snapshots
and is not a usable 20-minute capture. The command stops on 401/403/429 without retrying.
Use access agreed with the provider, your own receiver, or published historical traces.
Review sample density before local fitting; waiting for an archive can be simpler.

Keep the recording position and precise time as held-out truth for a blind test. Follow
[FIELD_PROTOCOL.md](FIELD_PROTOCOL.md), including wrong-time and missing-flight controls.
