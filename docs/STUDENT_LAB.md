# Lab: Can background sound place a microphone?

**Audience:** intermediate OSINT students. **Time:** 110 minutes after installation.
**Case:** fictional audio and aircraft tracks. **Deliverable:** a one-page evidence assessment.

By the end, you should be able to identify a plausible flyover in a spectrogram,
explain sound-travel delay, run a bounded multi-event match, challenge the result with
controls, and write a conclusion that distinguishes a hypothesis from a verified location.

## Before class

Follow [Quick start](../QUICKSTART.md) to extract and check the native executable.
The core lab needs that executable, a browser and a text editor; it does not require
Python, a flight-data account or a GIS license. Use new directories for class.
An instructor-provided report also supports the interpretation and assessment portions.
Installation is not graded. For a shorter introduction, use [guided practice](PRACTICE.md).

Commands below are for Windows PowerShell, from the executable's folder. On macOS/Linux
replace `.\doppler-lab.exe` with `./doppler-lab`, use forward slashes in paths, and
replace `Start-Process` with `open` (macOS) or `xdg-open` (Linux desktop).
Source installations can substitute their installed `doppler-lab` command.

## 1. Make a prediction — 10 minutes

A stationary microphone recorded two aircraft-like flyovers. Four candidate track
segments are supplied. The microphone is somewhere inside a 1.6 km × 1.6 km local area.
The first sample's offset relative to the track clock is uncertain.

Write down your prediction before running the search:

1. What should happen to pitch as an aircraft approaches and then recedes?
2. If the aircraft is 3 km away, about how long does sound take to reach you?
3. Why might two flyovers be more useful than two harmonics of one flyover?
4. What evidence would make you reject even a visually attractive match?

## 2. Inspect the evidence — 15 minutes

```powershell
.\doppler-lab.exe demo --output work\class-case
.\doppler-lab.exe inspect work\class-case\recording.wav --max-hz 450 --output work\class-inspection.png
Start-Process work\class-inspection.png
```

Keep `truth.json` closed. Open `case.json` in a text editor and locate the event windows,
track IDs, source-tone ranges, spatial grid and shared clock range.

Annotate a copy of the spectrogram or describe it in your notes. Identify the two main
curves and their harmonics. Explain why a persistent horizontal 60 Hz tone, if present
in the raw audio, would not be a useful flyover curve. The displayed representation
subtracts the median power at each frequency, so it suppresses that steady hum.

**Checkpoint:** spectral structure is an observation; “this is aircraft A” is a hypothesis.

## 3. Fit the joint hypothesis — 20 minutes

```powershell
.\doppler-lab.exe run work\class-case\case.json --output work\class-result
Start-Process work\class-result\report.html
```

Record the leading east/north/up point, common clock offset, flight pair, both event
scores and the mean score. These are local coordinates in metres, not latitude/longitude.
Inspect the overlay: does each predicted curve follow the observed shape across its
whole event window? Look at the competing locations, not just the orange star.

Explain why the label says `hypothesis only` and why the tool always sets
`accepted_location` to false. Describe one way a missing correct aircraft could still
produce a winning score for the wrong candidate.

## 4. Challenge the explanation — 25 minutes

Using your file manager or text editor, make two copies of `case.json` **inside the
same `work/class-case` folder** so their relative audio/track paths still work. Keep the
original unchanged. Save plain UTF-8 JSON with these exact names:

1. `case-one-event.json`: in the `events` array, keep only the `Flyover 1` object.
   Remove the `Flyover 2` object and the comma between them; leave valid JSON.
   Set `title` to `One flyover control` to label that report clearly.
2. `case-cold.json`: keep both events and change only `sound_speed_m_s` from `343` to `331`.

Watch for editors that append an extra `.txt` extension. The source checkout's optional
Python helper `scripts/make_variants.py` can create these same copies, but manual editing
works with the native executable alone.

```powershell
.\doppler-lab.exe run work\class-case\case-one-event.json --output work\one-event-result
.\doppler-lab.exe run work\class-case\case-cold.json --output work\cold-result
```

The first variant uses only flyover 1. The second changes sound speed from 343 to
331 m/s. Everything else remains the same. Compare the clock estimate, competing
locations, score surface and per-event fit. A higher numerical score from one event
does not establish that it is better geographic evidence than the two-event result.

Now generate a recording with no flyover tones and run the same search:

```powershell
.\doppler-lab.exe demo --noise-only --output work\noise-case
.\doppler-lab.exe run work\noise-case\case.json --output work\noise-result
```

The noise case still has a highest-scoring candidate. Explain why that is expected.
Does the result contain two convincing curved signals? Why would scoring only the
original winner against noise be an unfair control for a search over many candidates?

**Checkpoint:** do not convert a score or score gap into a percentage confidence.

## 5. Evaluate after committing your answer — 15 minutes

Before opening the answer, write your best current interpretation and two limitations.
Then open `work/class-case/truth.json` and calculate horizontal error:

```text
error = sqrt((estimated_east - true_east)^2 + (estimated_north - true_north)^2)
```

Compare the baseline and cold-air estimates with truth. The truth is deliberately
between grid nodes. Explain why neither a 100 m grid nor a small error in this one
fictional case establishes 100 m accuracy on an unknown real recording.

## 6. Submit an evidence assessment — 25 minutes

Use this structure, keeping the final assessment to one page:

| Item | Your finding |
| --- | --- |
| Evidence | Input files, recording duration and an input SHA-256 from the report |
| Search scope | Spatial bounds, clock range, aircraft candidates and two event windows |
| Leading hypothesis | Local point, aircraft pair, common clock and both event scores |
| Alternatives | At least one materially different explanation or location |
| Controls | What happened with one event, changed sound speed and noise |
| Evaluation | Error after truth was revealed; what that error does and does not establish |
| Conclusion | Supported, unsupported or unresolved claims; one next validation step |

A strong submission may conclude that an attractive hypothesis remains unverified.
The assignment rewards disciplined interpretation, not the most precise-looking number.

## Optional extensions

The first two extensions use Python and the source checkout. The remaining commands
are available in the native executable.

- Run `scripts/benchmark.py --output work/full-benchmark` for the full suite and retain
  its machine-readable table. It repeats the search on reversed time and three noise seeds.
- Use `scripts/refine_case.py` to make a finer local grid around the current leader;
  explain why refining only the winning mode could miss another mode.
- Generate a case with `--source-drift-hz 4`, then test the constant-tone assumption.
- Trace a curve manually and use `fit-ridge`; inspect the fit's residuals and bounds.
- Design a consent-based blind field experiment using [FIELD_PROTOCOL.md](FIELD_PROTOCOL.md).
