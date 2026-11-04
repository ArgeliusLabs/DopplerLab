# First original-recording test: insufficient evidence

**Testing in progress. This exploratory test did not recover a validated recording
location.** The acquisition, terrain and scoring pipeline ran on real inputs. Its
acoustic ranking did not justify accepting a location. This negative result is part
of the project's evidence, not a successful geolocation demonstration.

## Recording and test design

An owner-supplied iPad recording from the Tucson area on 3 November 2026 contained
47 minutes 44 seconds of stereo audio in a 5.89 GB MOV. The Apple recording-date claim
had an explicit Arizona UTC offset; the generic container creation time was different.
The recording crossed midnight UTC. Both audio channels were reviewed using time/frequency
plots; no near-full-scale samples appeared in the 8 kHz review derivatives. That does
not establish absence of distortion or automatic gain/noise processing in the original.

GPS metadata was visible during intake, so this was **not blind validation**. The GPS
tag is not a surveyed reference. The original recording, exact coordinates, raw flight
data, private reports and audio excerpts are not included in the public release.
This page publishes aggregate outcomes and method limitations; it is not a fully
redistributable independent acoustic benchmark.

## Actual acquisition

The daily archive for the relevant date was not yet published. The new `download-window`
command instead used public replay chunks and detailed readsb traces. With a broad
Tucson box, the actual command produced:

| Measurement | Result |
| --- | ---: |
| Replay half-hour chunks | 3 |
| Distinct candidate aircraft | 42 |
| Retained dated trace files | 44 |
| Current full-trace fallbacks | 8 |
| HTTP requests, including unavailable historical files | 55 |
| Downloaded bytes | 58,933,188 |
| Elapsed time, including request pacing and normalization | 175.658 seconds |
| Geometry-ready segments | 47 |
| Exported positions | 1,885 |
| Missing resources after fallback | 0 |

The coarse replay positions selected aircraft IDs. Detailed traces supplied compatible
geometric heights. Stale points, unsupported position sources, missing geometric height
and undersized segments were rejected and counted. Maximum permitted track gap was
explicitly set to 30 seconds; the default remains five seconds. No missing altitude was
replaced with pressure altitude.

An initial wider-region import found two conflicting positions at one timestamp for
one aircraft and stopped. This motivated an explicit `--conflicts quarantine` option.
That wider import excluded the affected aircraft with an audit. The final smaller
download/normalization above had no conflicting aircraft within its retained bounds.

The Tucson [terrain bundle](TERRAIN.md) supplied USGS DEM heights converted from
NAD83/NAVD88 to WGS84 ellipsoid height. The assumed microphone height was 1.5 m above
bare ground. This does not model buildings, canyon reflections, obstruction or wind.

## Acoustic diagnostics

The strongest changing harmonic groups were not automatically labeled aircraft. Several
rose in pitch or changed rapidly. An initial exploratory comparison used three nearby
flight hypotheses selected from time/geometry at a regional reference point. Their best
single-event line-contrast scores were approximately 1.6–2.5 dB. These are optimized
contrast measurements, not confidence percentages or established detection thresholds.

A two-flight diagnostic then used the first six minutes of the recording:

- Two fixed windows: media +4–130 seconds and +220–360 seconds.
- 720 DEM-following observer nodes, approximately 1 km spacing in a regional box.
- 13 shared clock offsets from −60 to +60 seconds, in 10-second steps.
- 195 source frequencies per event from 30 to 1,000 Hz in 5 Hz steps.
- 2-second Hann windows, 0.5-second hop and a 1,800 Hz analysis ceiling.
- Still-air sound speed 343 m/s and the same two candidate tracks in every run.

The tracks were hypotheses, not independently confirmed identities for the sounds.
Event windows and settings were exploratory. This was a diagnostic local comparison,
not an exhaustive search of all Tucson flights or all possible recording times.

| Run | Highest joint contrast | Interpretation |
| --- | ---: | --- |
| Original, channel 0 | 2.346 dB | Weak; different leading location from channel 1 |
| Original, channel 1 | 2.491 dB | One event especially weak; does not corroborate channel 0 |
| Reverse each event's channel-0 spectral frames | 2.495 dB | Negative control scores at least as well as the original search |

Each run used the same 720 candidate nodes and search effort; 550 nodes had full temporal
support. Runtime was about 99–101 seconds per run on the test machine. Reversal retained
the same event windows and spectra while reversing their temporal evolution. It is a
diagnostic control, not a calibrated estimate of the real-world false-positive rate.

A follow-up at the metadata reference used 0.5 Hz pitch steps, 2.5-second clock steps,
both channels and sound speeds of 335, 343 and 351 m/s. Original-audio joint scores
remained approximately **2.026–2.155 dB**. These sound speeds are sensitivity assumptions,
not measured atmospheric conditions. Finer sampling did not provide a persuasive match.

## Decision and changes

**Insufficient evidence; no accepted location.** The control result, channel disagreement
and lack of convincing continuous overlays prevent accepting the ranked hypotheses.
The result does not prove that the technique can never work on this recording, nor
that no aircraft was audible. It establishes that this analysis did not validate one.

Practical changes from this test are included in v0.4.0:

1. `review-media` processes long original recordings into overlapping audio/spectrogram
   chunks, preserving offsets, hashes, channels and timestamp evidence.
2. `download-window` acquires a local time window without waiting for a multi-GB daily
   archive, handles UTC midnight and audits recent-trace fallbacks.
3. Explicit quarantine allows continuing around conflicting aircraft records while
   retaining the excluded alternatives in the audit.
4. Native archives include the investigation documentation and this test outcome.

The next useful field input is a recording with clearly sustained aircraft tones on
both sides of more than one flyover, a documented clock and independent held-out
ground truth. More tuning against this known site would remain exploratory. Use the
[recording workflow](REAL_RECORDING.md) and [blind field protocol](FIELD_PROTOCOL.md)
to contribute both successes and failures.
