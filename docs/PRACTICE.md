# Guided practice: two flyovers and a misleading winner

**Time:** about 15–20 minutes after setup, plus executable startup time.
**You need:** a native Doppler Lab build, a browser and somewhere to write short notes.
The exercise generates original fictional audio and tracks; it uses no real location.
It works offline after downloading. Real-recording testing remains in progress.

**Question:** can the tool explain two frequency curves with one location and one
recording clock—and can a search return a winner when the useful signal is absent?

## 1. Get the baseline ready — 2 minutes

Complete [Quick start](../QUICKSTART.md) through opening
`practice/report/report.html`. If you already did it, reuse those files; do not rerun
the creation commands into the same directories. Keep your terminal in the folder
containing the executable, and leave `practice/case/truth.json` closed.

The generated recording lasts 200 seconds. Open `practice/case/recording.wav` in an
audio player if useful. These are modeled tones, hum and noise, not a real jet recording.
Small speakers may make the low tones hard to hear; the spectrogram is the main evidence.

Before examining the score map, write one sentence for each:

1. How should pitch change as a sound source approaches and then recedes?
2. Why might two separate flyovers help more than one?
3. Would you expect random noise to have a highest-scoring candidate?

## 2. Read the signal before the location — 3 minutes

In the report, find **01 / Read the signal**. Time runs left to right; frequency runs
bottom to top. Bright structure is observed energy. Mint lines are the leading model's
predicted curves, so an overlay is a hypothesis, not another measurement.

Look at the two event windows: roughly **15–75 seconds** and **115–175 seconds**.
Follow each curve across its window rather than judging one bright crossing point.
The display reduces steady tones by subtracting the median power at each frequency.

Record whether each predicted curve follows a sustained observed shape. The two events
have different source tones but share one recording-clock offset.

## 3. Compare hypotheses — 3 minutes

Read **02 / Compare locations** and **03 / Keep competing explanations**.
The orange star marks the leading grid point. The axes are fictional east/north metres,
not latitude and longitude. Adjacent colored points are not independent confirmations.

Write down:

| Item | Where to find it |
| --- | --- |
| Leading east/north/up point | First row in “Keep competing explanations” |
| Common clock offset | The same row's “Clock offset” column |
| Track IDs and each event's score | Its “Event scores (dB)” column |
| One competing location | Another row in that table |
| One input hash | Expand “Configuration & input provenance” |

Read the **Accepted location: no** notice. The score measures contrast along predicted
frequency curves. It is not a probability, and the score map is not a confidence region.

## 4. Remove the flyover signal and search again — 4 minutes

Use a new case and result directory. `--noise-only` leaves noise and steady hum but
omits the generated flyover tones. The supplied tracks still let the solver try its
whole search; this is a deliberately negative control.

Windows PowerShell:

```powershell
.\doppler-lab.exe demo --seed 7 --noise-only --output practice/noise-case
.\doppler-lab.exe run practice/noise-case/case.json --output practice/noise-report
Start-Process "practice/noise-report/report.html"
```

macOS/Linux:

```bash
./doppler-lab demo --seed 7 --noise-only --output practice/noise-case
./doppler-lab run practice/noise-case/case.json --output practice/noise-report
```

Open `practice/noise-report/report.html` in your browser (`open` on macOS or `xdg-open`
on a Linux desktop, as in Quick start). Keep the baseline report open beside it.
If you previously used these folders, choose a new prefix such as `practice-02` for
this command block; retain the original baseline for comparison.

Compare the two reports:

- Does noise still produce a highest-scoring point and an orange star?
- Do its overlays follow two convincing, sustained flyover curves?
- How do both event scores and the leading line contrast compare with the baseline?
- Does either report claim an accepted location?

**Checkpoint:** noise still has a winner. Ranking is an operation on the candidates
you supplied; it does not establish that any of them explains a real aircraft signal.
This engineered comparison does not define a universal score threshold for field work.

## 5. Commit an answer, then reveal truth — 3 minutes

Before opening the answer, write a three-sentence assessment:

1. What the baseline appears to support within this declared search.
2. What the noise comparison shows about trusting a winner.
3. What additional evidence a real recording would need.

Now open `practice/case/truth.json` in a text editor. Compare its `observer_enu_m`,
`clock_offset_s` and `track_ids` with your baseline result. `truth.json` is for evaluation;
the solver does not read it. Do not use the noise case's truth file as evidence of a
recoverable microphone location: its flyover signals were deliberately omitted.

<details>
<summary>Self-check for the default seed-7 case — open after writing your assessment</summary>

The fictional truth is **(137, −213, 0) metres**, with tracks **A/B** and clock offset
**11.25 seconds**. The tested coarse search puts **(100, −200, 0) metres** first, using
tracks A/B and the same clock offset. Its horizontal error is:

```text
sqrt((100 - 137)^2 + (-200 - -213)^2) ≈ 39.22 metres
```

The truth lies between grid nodes. This result is for one deliberately generated case;
it does not establish 39-metre accuracy on real recordings. Small floating-point score
differences across environments are not the point of the exercise.

The noise-only search still returns ranked candidates, with much weaker support in
this fixture. Its leading location need not be the baseline location. Both reports
remain **hypothesis only**, with no accepted location.

A suitable conclusion is: “Within the supplied fictional tracks and local grid, one
shared-clock hypothesis explains both generated flyovers. The noise control still
produces a winner, so ranking alone is insufficient. A real investigation would require
supported clocks, heights and trajectories, competing explanations and independent
validation.”

</details>

## Keep or share the result

Keep both case folders, result folders and your assessment together. Each report HTML
embeds its plots and can be shared on its own; reproducing a run also needs the case
inputs and settings. These generated fixtures are original and redistributable under
the project's MIT license. They contain no real recording location.

Next: the [full classroom lab](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/STUDENT_LAB.md)
adds one-event and sound-speed controls. For an investigation, start with the
[real-data workflow](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/INVESTIGATION_WORKFLOW.md).
