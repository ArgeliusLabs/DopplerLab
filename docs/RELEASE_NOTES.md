# v0.4.0 — original-recording workflow and first field result

**Experimental — testing in progress.** This release comes from working an actual
47-minute iPad recording through public aircraft data, Tucson terrain and acoustic
controls. The acquisition and analysis pipeline ran; **the recording did not support
an accepted location**. Read the [field-test report](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.4.0/docs/FIELD_TEST_2026_11.md).
Real-world location accuracy remains unvalidated.

## What changed

- `review-media`: review long local videos in overlapping audio/spectrogram chunks,
  preserve channel separation, offsets and hashes, and distinguish recording-date claims
  from container/export time. GPS values are excluded from its intake manifest.
- `download-window`: fetch a bounded local historical hour through public adsb.lol
  replay and detailed traces, including UTC midnight and recent full-trace fallback.
  Heatmap altitude is never used for acoustic geometry. Gaps, missing data, source
  rejections and resource budgets remain explicit.
- `normalize-adsb --conflicts quarantine`: optionally exclude and audit an entire
  aircraft with conflicting timestamped positions; default behavior still stops.
- Native archives now include the investigation documentation and first field outcome.

## Start here

- [Native quick start](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.4.0/QUICKSTART.md)
- [Original-recording walkthrough](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.4.0/docs/REAL_RECORDING.md)
- [Terrain guide](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.4.0/docs/TERRAIN.md)
- [Field result and limits](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.4.0/docs/FIELD_TEST_2026_11.md)

FFmpeg/ffprobe are separate requirements for media review. The native executable
bundles Python, scientific libraries and terrain dependencies. Generated practice
and existing WAV analysis still work offline without FFmpeg.

## Evidence

The real window acquisition downloaded **58,933,188 bytes in 175.658 seconds**, retaining
42 candidate aircraft, 44 dated trace files, 47 geometry-ready segments and 1,885
positions. Eight traces used the recent full-trace fallback. Coverage is not guaranteed.

A terrain-following 720-node diagnostic gave different winners on the two audio
channels. Reversing each event's time/frequency frames scored at least as well as the
original grid search. Finer pitch/clock sampling and sound-speed sensitivity at the
metadata reference did not produce persuasive evidence. The correct outcome is
**insufficient evidence**, not a coordinate. GPS was visible at intake, so this was
exploratory and not blind validation. Raw recording, precise coordinates and private
reports are excluded from the release.

Automated tests cover midnight boundaries, overlapping trace fallback, timestamp/GPS
handling, rate-limit aborts and conflict quarantine. Publication requires the
Windows/Linux test matrix and all four native smoke checks.

## Downloads

- [Windows x86-64 ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.0/doppler-lab-0.4.0-windows-x86_64.zip)
- [Linux x86-64](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.0/doppler-lab-0.4.0-linux-x86_64.tar.gz)
- [Intel Mac](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.0/doppler-lab-0.4.0-macos-x86_64.tar.gz)
- [Apple Silicon](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.4.0/doppler-lab-0.4.0-macos-arm64.tar.gz)

Source ZIP, student pack, wheel, source distribution, inventory and SHA-256 checksums
are included. See [platform requirements](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.4.0/docs/BINARIES.md).

The replay adapter uses public map resources whose format and retention can change;
use daily archives for broader historical searches. Rate-limit/authentication errors
stop without retry. Aircraft data retains its ODbL terms, separate from MIT code.

Original implementation by Argelius Labs, inspired by
[colsto's demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI). No affiliation
or endorsement is implied. Share reproducible successes and failures through
[Issues](https://github.com/ArgeliusLabs/DopplerLab/issues).
