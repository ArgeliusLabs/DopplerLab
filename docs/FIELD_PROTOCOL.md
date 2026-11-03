# Blind field validation protocol

This protocol describes work still to be done before making real-world accuracy claims.
It is not a report of a completed field validation.

## Question

Under declared conditions, can Doppler matching improve an analyst's microphone-location
estimate over simple geographic and time priors, without access to the true position?
How often does it fail, abstain, or prefer a materially wrong location?

## Roles and separation

The collector records at authorized public or controlled sites and keeps a private
ground-truth ledger. The analyst receives audio, justified search bounds, clock evidence
and flight data, but not the microphone coordinates. The evaluator holds the truth,
scores frozen predictions and reveals it only after each analysis has been committed.
Do not use private people's recordings or residences as targets.

Keep a consent/permission record, retention period and redistribution decision for each
recording. Public release needs permission for the recording and its metadata; flight
data and terrain need their own compatible terms. Redact unrelated intelligible speech.
If redaction changes timing, preserve an edit map and adapt the analysis accordingly.

## Pilot design

Start with a feasibility pilot, not an accuracy headline. A proposed pilot is 12–20
sessions over several sites and days, including deliberately negative or unusable
recordings. This count is an operational starting point, not a statistical power claim.
Use a later, independently planned evaluation to estimate population performance.

For each session record:

- Microphone coordinates, height, coordinate reference, measurement method and its error.
- Sample-zero UTC evidence, clock synchronization method, drift estimate and any trigger lag.
- Recorder, microphone, channels, gain/AGC/noise reduction and sample rate.
- Temperature, wind observations and the limitations of those observations along the sound path.
- Continuous recording duration; visible flight notes kept separate from blind analysis inputs.
- Flight-data source, field types, timing precision, coverage, gaps and compatible heights.
- Terrain source, datum conversions, version, interpolation method and microphone elevation.
- Raw-file hashes, processing commands, acquisition date and permission/license record.

Prefer multiple naturally occurring flyovers without manipulating aircraft operations.
The project does not require aircraft access or a drone flight. Do not create a field
experiment near restricted areas or interfere with other people to improve a recording.

## Freeze the analysis before revealing truth

Predeclare geographic and time bounds from evidence available to the analyst. Freeze
event-selection rules, source-tone bounds, flight candidate preparation, interpolation,
scoring parameters and control procedures. Document why each input is available.

Preserve every search, not just the best-looking run. If a parameter changes, mark
the run as exploratory and justify the change. Keep a separate held-out evaluation
set that is not repeatedly used to choose settings.

Submit a timestamped prediction record containing the leading hypothesis, alternatives,
per-event diagnostics, support gaps, sensitivity findings and an explicit conclusion:
unresolved / insufficient evidence / candidate requiring corroboration. The current
software does not implement a calibrated acceptance rule; any future rule must be
defined and evaluated separately.

## Required comparisons

1. **Prior-only baseline:** compare with a location chosen using only the supplied bounds.
2. **One versus multiple flyovers:** evaluate the added information, including ambiguous modes.
3. **Negative recordings:** test audio with no confirmed useful flyover, not just white noise.
4. **Wrong date/time/track controls:** repeat the same complete search under incompatible inputs.
5. **Held-out event:** where available, use one flyover only for final prediction checking.
6. **Sensitivity:** vary clock, source pitch, event selection, height, sound speed and track sampling.

Reversed time and synthetic noise remain useful diagnostics but are not substitutes
for representative field negatives. Negative control sets must resemble actual failure
conditions closely enough to support the intended inference.

## Report all outcomes

For each session publish, where permitted: horizontal error against the held-out
reference, uncertainty in that reference, track-association correctness, number of
competing modes, whether the true position/track was inside the declared search,
data support, runtime and final decision. Report the number of abstentions and failures
in the denominator. Separate source-informed replays from genuinely blind predictions.

Use error distributions and threshold counts such as within 100/500/1,000 m only after
predeclaring them. Do not select the most flattering threshold afterward. A small
sample cannot establish rare false-localization rates or national coverage. Release a
versioned benchmark with failures and a reproducible analysis environment before
advertising any general accuracy number.

## Privacy experiment

For recordings you control, compare the original and final exported versions after
specific filtering, encoding or audio replacement. Name the exact processing pipeline.
Evaluate surviving tones and matching performance independently of how loud they sound.
Removing/replacing the original audio eliminates that original audio channel from the
export, but does not remove visual clues, metadata or other sources of location information.
