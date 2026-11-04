# From a broad region to a location hypothesis

You do not need to know the recording's exact location before collecting flight data.
Start with the geographic and time bounds that the evidence supports. A country and
a recording date can be enough to begin candidate selection; they do not guarantee a
unique answer. A city and precise recording time make the first controlled test easier.

**Implementation status, 3 November 2026:** The experimental 0.2.0 release implements
archive download, regional indexing, coarse interval screening, per-event speed/slant
filters and a handoff to detailed local matching. See the
[runnable broad-search guide](BROAD_SEARCH.md) for commands and limits. **Testing is in
progress:** automated checks and archive benchmarks are complete; original-recording
field tests are being prepared. This document identifies the stages that still require
analyst preparation or future development. The classroom lab demonstrates the local
stage with fictional data.

## What the video actually knew

At approximately 00:24–00:33, the creator specifies **September 8 and the continental
United States**. At approximately 02:50–03:00, two aircraft events are separated by
about **920 seconds (15 minutes 20 seconds)**. This interval constrains pairs of flights
even when the recording's exact start time is unknown. At approximately 03:01–03:15,
he describes collecting historical tracks over several hours. These are observations
from [colsto's demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI), not timings
measured for our downloader or proof that our implementation reproduces the full search.

The sound does not contain a coordinate or an aircraft identifier. The investigator
compares an acoustic pattern against independently recorded aircraft trajectories.
The result depends on the relevant flight being present in the database and on the
sound and trajectory being modeled well enough.

## The investigation sequence

```text
Original recording + supported region/date/time uncertainty
                         |
                         v
Acquire historical aircraft positions for that time span
                         |
                         v
Filter/index tracks by region, time and data quality
                         |
                         v
Find candidate areas and flight pairs compatible with the audio
                         |
                         v
Prepare small local cases and score full Doppler curves together
                         |
                         v
Compare alternatives, run controls, seek independent corroboration
```

### 1. Record what is known and what is uncertain

Preserve the original media and its hash. Record the basis for the date, possible time
zones, edits, playback speed and uncertainty in sample-zero time. Upload time is not
automatically recording time. Measure flyover windows and relative intervals in the
original uninterrupted audio; use uncertainty ranges instead of treating hand-selected
points as exact. Two harmonics of one flyover are still one event.

If only the date is known, search the whole supported date interval. If the date is
unknown, additional days must be acquired and searched. If the location is uncertain
across time zones, account for the corresponding UTC span. Date boundaries must not
silently discard a possible match.

### 2. Acquire positions, not just a flight schedule

Aircraft transmit radio messages that ground receivers collect and data services
aggregate. For geometric matching, obtain time-stamped trajectories: latitude,
longitude, compatible aircraft height, position times and identity/source metadata.
A flight number, airport schedule or image of a tracking map is insufficient.

| Situation | Acquisition route | Important distinction |
| --- | --- | --- |
| Recording a new local test now | Capture time-stamped positions from a permitted live API or your own receiver while recording audio | A current snapshot is not a historical track; repeated collection builds the track |
| Existing recording with a known time | Obtain historical traces covering the event and surrounding flight segments | A live endpoint cannot recover an earlier flyover |
| Known day and broad region | Download a daily archive, or use a licensed historical query that supports the required region/time | A provider's regional query and a global archive have different costs and limits |

One open historical route is the [adsb.lol archive](https://www.adsb.lol/docs/open-data/historical).
Its daily releases contain the network's recorded worldwide coverage. The
[download guide](DATA_VOLUME.md) links real releases and explains how to select their
parts. With this route, U.S. and European investigations can start from the same global
input; geographic filtering happens locally. Other providers may offer server-side
regional filtering. Verify the particular product's access, sampling and license.

For a live Tucson experiment, a city-centered query is a convenient way to collect
test inputs. It is not a requirement that an unknown-location investigation start with
Tucson. Known recording truth is held out from the analyst during a blind test.
Respect live API request limits; a fast polling loop is not an unrestricted data feed.

### 3. Build a regional and temporal candidate index

This stage was not implemented in v0.1.0 and is now available experimentally in
0.2.0. The indexer parses the archive incrementally, preserves source hashes and splits aircraft histories into
continuous segments. Keep points around region and time boundaries so filtering does
not cut away the approach, departure or sound-delay context. Include flights crossing
the region, not only flights departing from or arriving at its airports.

Store a compact index of segment time intervals and geographic bounds. Use it to find
nearby trajectories at candidate ground areas before expensive acoustic scoring. Avoid
putting an entire continent into one local ENU coordinate frame or blindly comparing
every possible flight pair against every ground point.

Track missing data, irregular sampling, source quality and altitude reference explicitly.
An airframe identifier can cover multiple flights. Keep unknown aircraft types when a
type filter is uncertain; a guessed exclusion can remove the correct answer. Retain a
record of every filter and the number of surviving segments.

### 4. Use the audio to narrow candidate areas

For the video's two-event example, ask: **where could two recorded flight paths have
produced these flyovers about 920 seconds apart?** The interval refers to sound arriving
at a candidate microphone, not simply to two database timestamps or airport departures.

For each plausible receiver area, a preliminary model can calculate closest-approach
events and their sound travel delays. Compare the resulting arrival-time intervals
against the measured interval and its uncertainty. Preliminary pitch fits can add broad
speed and slant-distance constraints, subject to the assumptions of steady source pitch
and suitable flight motion. Closest approach is a useful screening landmark, not a
guarantee about the time of maximum recorded loudness.

This produces candidate **flight combinations and ground areas**, which may be far
apart geographically. The video's 10 km screening radius is an assumption in that
demonstration, not a universal sound-propagation limit. Silent intervals alone should
not eliminate a candidate without evidence about audibility and recording conditions.

This candidate-selection stage is where the search can shrink from a continent to a
set of local cases. One weak event with an unknown clock may leave many possibilities.
More independently timed events can help; no fixed event count guarantees a solution.

### 5. Run detailed local matching

Prepare each shortlisted area's
tracks, receiver heights and time bounds following [DATA.md](DATA.md). Use compatible
WGS84 ellipsoid heights for aircraft and receiver, split large trajectory gaps and
convert each local case to its declared ENU frame.
For supported US regions, [download terrain and prepare observers](TERRAIN.md) using
the same local origin as the aircraft tracks. Use the DEM during broad screening too.

The model predicts changing frequency and sound arrival time along the actual 3D
trajectories. All events share one recording-clock offset. A wrong flight cannot be
rescued by independently sliding each event in time. See [METHOD.md](METHOD.md).

Refine around surviving areas only after comparing the broader alternatives. Keep
scores, input hashes, search bounds and unsuccessful cases. A local maximum is only
the best point among the supplied candidates; it does not establish that an excluded
location elsewhere was worse. The current report's score is not a calibrated probability
and should not be treated as one when comparing separately configured searches.

### 6. Evaluate the result

Inspect whether all independent events agree. Run wrong-clock, missing-flight and
noise controls using comparable search effort. Test plausible sound-speed, height and
source-pitch changes. Seek separate evidence before making a location claim. Report
ambiguous and unsupported cases as such. The [field protocol](FIELD_PROTOCOL.md)
describes how to evaluate against hidden recording truth; real-world accuracy remains
unvalidated in the published release.

## What is automatic in the experimental v0.3.0 release?

| Stage | v0.3.0 status |
| --- | --- |
| WAV inspection, FFmpeg extraction, manually traced ridge fitting | Implemented |
| Live capture or historical archive download | Implemented for adsb.lol; access limits and coverage apply |
| Continental track index and relative-interval candidate selection | Implemented with explicit budgets and coarse-model limits |
| Per-event speed/slant filtering and local track handoff | Implemented; audio constraints and final case require analyst review |
| USGS terrain download, correction grids and broad/local receiver heights | Implemented for bounded contiguous-US regions; [commands and limits](TERRAIN.md) |
| Other terrain/flight providers and unsupported height references | Analyst preparation |
| Geographic CSV to local coordinates | Implemented; explicit time and height requirements |
| Detailed scoring of supplied local candidates | Implemented |
| Report, input hashes and fictional controls | Implemented |
| Validated real-world accuracy or automatic acceptance | Not established |

The [real-data benchmark](REAL_DATA_BENCHMARK.md) reports bytes read, rejected records,
shortlist size, wall time, sampled memory and storage for the broad stage. Whether the
true held-out recording area survives still needs field evaluation. Download speed is
not a substitute for location accuracy.

For runnable commands and resource limits, use [BROAD_SEARCH.md](BROAD_SEARCH.md).
