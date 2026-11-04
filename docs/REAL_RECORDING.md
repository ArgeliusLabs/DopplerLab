# Work an original recording

This is the investigation workflow for a video or audio file you are authorized to
analyze. The generated practice remains useful for learning the mechanics. A real
recording may end with **insufficient evidence**; do not turn its highest score into
a location claim. Read the [first field-test outcome](FIELD_TEST_2026_11.md).

## 1. Review the recording and its clock

Use the v0.4.0 native executable. Install [FFmpeg and ffprobe](https://ffmpeg.org/download.html)
separately for media review. They are not bundled. From PowerShell:

```powershell
.\doppler-lab.exe review-media "C:\recordings\owned-video.mov" --output work\review-01
Start-Process "work\review-01\review.html"
```

If the executables are not on PATH, add their actual paths:

```powershell
.\doppler-lab.exe review-media "C:\recordings\owned-video.mov" --ffmpeg "C:\tools\ffmpeg\bin\ffmpeg.exe" --ffprobe "C:\tools\ffmpeg\bin\ffprobe.exe" --output work\review-02
```

On macOS/Linux use `./doppler-lab`, forward slashes and your own recording path.
Always choose a new output directory. Default review budget is 120 minutes; the maximum
is 240. Processing uses five-minute chunks with 20-second overlaps, preserving stereo
channels. The output contains:

- `review.html`: a local audio player and spectrograms for each chunk/channel.
- `media.json`: original SHA-256, duration, timestamp claims, extraction offsets,
  derived WAV hashes, channel levels and clock assumptions.
- `chunk-*.wav` and channel PNGs: derived review material. Keep these files together.

The page's spectrogram axis uses **original-media seconds**. Add the displayed chunk
offset to the audio player's time. Overlapping chunks are the same underlying evidence,
not independent events. The original is not modified.

For Apple recordings, the tool suggests the explicit-offset
`com.apple.quicktime.creationdate` as a recording-time claim. It records generic
container `creation_time` separately: that may be an export time. File modification
time is not used. Without a supported recording-date claim, sample-zero time stays
unknown. Use `--start-utc 2026-11-03T23:19:48Z` only with supporting evidence;
`--clock-uncertainty 60` is a declared allowance, not a measured clock error.
Inspect edits, trigger lag and clock drift separately.

GPS/location values are excluded from the intake manifest; their presence is flagged.
The original and derived audio can still identify people or places. Keep the review
private unless redistribution is authorized. If the analyst has seen embedded GPS,
label the analysis exploratory/source-informed instead of calling it blind validation.

## 2. Select acoustic events

Review both channels. Look for sustained, traceable pitch curves across an approach
and departure, with consistent harmonics. Rising engine pitch, short chirps, speech,
wind, stationary hum and passing vehicles can be misleading. Loudness alone is not
an aircraft identifier or a reliable closest-approach timestamp.

Use a lower frequency ceiling for a closer look:

```powershell
.\doppler-lab.exe inspect work\review-01\chunk-000.wav --channel 0 --max-hz 400 --output work\detail-channel-0.png
```

`inspect` uses seconds from that WAV's zero; retain the chunk offset from `media.json`.
Record proposed event windows, rejected alternatives and reasons. Do not choose events
solely because a flight was present. Two harmonics of one flyover count as one event.
If the recording lacks usable tones, retain that negative result.

## 3. Download the relevant historical flight window

For a supported **local area and known time**, `download-window` can retrieve the public
replay chunks, identify regional aircraft and download their detailed traces. This can
work before a daily archive is published. The following is the Tucson field-test window,
not a template timestamp to reuse for a different recording:

```powershell
.\doppler-lab.exe download-window --start 2026-11-03T23:19:48Z --end 2026-11-04T00:07:32Z --bounds 32.10 -111.15 32.55 -110.55 --max-gap 30 --conflicts quarantine --output work\flights-01
```

Bounds are **south west north east**. Use the area justified by the investigation and
include room for audible approaches. The recording crosses midnight UTC even though
it is one afternoon in Arizona. The command handles both dates. Default padding adds
180 seconds at each end; increase the margin for clock uncertainty and propagation
delay when needed. Start/end **plus both margins must fit within one hour**. Split
longer recordings into overlapping windows and review cross-window duplicates explicitly.

Default maximum gap is five seconds. This example explicitly allows 30 seconds because
the field traces are simplified. That improves support but may degrade interpolated
velocity and predicted pitch. It does not make sparse data accurate.

The output includes `download.json`, raw replay/traces, dated/time-filtered traces and
`tracks/geographic.csv` with `tracks/summary.json`. The latter records rejected records,
gaps and the accepted **geometric** altitude field. Heatmap altitude is never used for
acoustic geometry. Files that lack compatible heights cannot become valid trajectories.

`--conflicts quarantine` explicitly excludes an entire aircraft if it has conflicting
positions at a timestamp and audits that exclusion. Default `error` stops for review.
An excluded aircraft remains a missing alternative, not evidence that it was absent.

This adapter uses the resources behind [adsb.lol replay](https://adsb.lol/) and the
[upstream viewer implementation](https://github.com/adsblol/tar1090/blob/master/html/script.js).
It is experimental: URL formats and retention may change. Recent traces may use the
viewer's current full-trace fallback, which is checked for the requested date/time.
Daily archives remain the preferred route for broad/historical work.

Replay sampling and receiver coverage can omit aircraft. A successful request does not
prove complete coverage. Missing chunks/traces produce a partial manifest and a nonzero
exit status. HTTP 401/403/429 stops without retrying. Requests are paced; do not run a
fleet of parallel downloads to defeat limits. Default caps are 1 GB and 150 aircraft;
`--max-gb` and `--max-aircraft` make those budgets explicit.

For a country/continent or an unknown recording hour, use [daily archives and regional
screening](BROAD_SEARCH.md). Window acquisition requires a local prior; that is an
optimization for this test, not a requirement of the broader technique. Data from
adsb.lol retains its [ODbL terms](https://www.adsb.lol/docs/open-data/historical),
separate from this project's MIT code.

## 4. Prepare terrain and local hypotheses

Follow [TERRAIN.md](TERRAIN.md) to download/reuse a USGS terrain bundle and run
`prepare-observers`. Import `tracks/geographic.csv` with `import-tracks`, using exactly
the same local origin recorded in `observers.json`. Set the track epoch explicitly.
Never substitute pressure altitude for geometric height or raw NAVD88 height for WGS84
ellipsoid height.

Use [DATA.md](DATA.md) to assemble `case.json`: selected WAV, nonoverlapping event
windows, candidate track segments, frequency ranges, one shared clock range and the
terrain observer CSV. If the WAV was extracted at media +120 seconds, reflect that
offset in the track epoch/clock. Overlapping review chunks are for inspection;
do not concatenate them as if they were continuous new evidence.

## 5. Test the hypothesis and retain failure

Run the local search, compare both channels, inspect curve overlays, examine spatial
alternatives and run controls with comparable search effort. Test sound speed, pitch
resolution, clock range and height assumptions. Keep the full configuration and every
result. A control scoring as well as the original is a reason to reject the claimed
association, not to hide the control.

The [field protocol](FIELD_PROTOCOL.md) describes independent evaluation. A known-site
diagnostic can reveal implementation problems, but it cannot establish blind location
accuracy. The software continues to emit `accepted_location: false`.
