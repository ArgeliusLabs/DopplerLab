# Instructor guide

**Session:** Background Sound as Geographic Evidence. **Audience:** intermediate OSINT.
**Duration:** 110 minutes, with a 90-minute compressed option or 120-minute extension.

## Teaching outcome

Students should leave with a reproducible method and a better standard of evidence.
They should understand why the sound's emission time differs from its reception time,
why multiple flyovers need one shared clock, and why a ranked candidate can be wrong.
They do not need calculus or prior DSP experience to complete the core lab.

The hook is strong: play the fictional recording briefly, reveal its spectrogram, and
ask students how much information can hide in “background.” Attribute the inspiration
to colsto and link the original video. Use our original figures and fictional audio in
public slides. Obtain permission before redistributing third-party video or field audio.

## Preparation checklist

One week before: install the toolkit on the classroom OS image, run tests and the
benchmark, and retain the exact dependency versions. Pre-download the Python packages
for the classroom OS if network access is unreliable. A wheelhouse is platform-specific;
do not distribute a Windows-only cache as if it also installs on macOS/Linux.

One day before: generate `work/class-case`, run its report, and prepare the no-flyover
case. Give students the source release and student handout. Keep a static report ready
for learners whose installation fails. The supplied student handout pack supports the
interpretation exercise without Python. Have headphones available, but grade the
spectrogram analysis rather than hearing acuity.

Do not make students buy a flight-data plan, surrender an API key or reveal a personal
recording location. Real-data acquisition is a separate optional exercise.

## Run of show

| Minute | Activity | Instructor move |
| --- | --- | --- |
| 0–10 | Prediction and acoustic delay | Draw a plane, microphone and expanding wavefront; estimate 3,000/343 seconds |
| 10–25 | Inspect the fictional recording | Separate visible structure from aircraft identity; identify harmonics |
| 25–45 | Joint search and report | Ask why the second curve cannot have its own clock adjustment |
| 45–70 | One-event, sound-speed and noise controls | Show that noise always has a winner; avoid confidence percentages |
| 70–85 | Reveal truth and compute error | Discuss grid quantization versus model bias |
| 85–110 | Write and discuss evidence assessment | Compare warranted conclusions, not just coordinate estimates |

For 90 minutes, provide installation and the initial inspection in advance, then reduce
discussion/writing by 10 minutes. For 120 minutes, add a source-pitch drift experiment
and a short critique of the video's silence filter.

## Talk track for the difficult concepts

**Sound travel time:** “At the instant a sound reaches the microphone, the aircraft has
already moved. We need the position and velocity where the sound started.”

**Source tone:** “The engine is not a laboratory oscillator. A changing source pitch
can look like motion. Our basic model holds the tone constant so we can test that
assumption openly.”

**Shared clock:** “Both events were captured by one continuous recording. If the first
sample starts at a particular time, that fixes the clock for every later event.”

**A winner versus evidence:** “If I search a noisy image for the best line, I will find
a best line. I still need to ask whether that line tells me anything.”

**Accuracy:** “Synthetic success verifies parts of the implementation. It does not
measure errors from weather, source RPM, incomplete ADS-B or an unknown microphone.”

## Answers and expected observations

The standard fixture hides the observer at east **137 m**, north **−213 m**, up **0 m**.
The recording starts at track-relative **11.25 s**. The true track IDs are **A** and **B**;
their selected source tones are **131 Hz** and **173 Hz**. Decoys are deliberately included.

The measured reference run's baseline top grid point was **(100, −200, 0) m**, giving
**39.22 m** horizontal error. The clock was **11.25 s** and the pair **A/B**. The supplied
benchmark records exact values and environment. Minor numerical variation is acceptable;
do not grade a floating-point score to the second decimal place.

The 331 m/s run moved to **(0, −400) m**, about **231.81 m** from truth, despite a high
score. The 355 m/s run moved to **(200, −100) m**, about **129.38 m** from truth. These
are measured results for this fictional case, not predicted errors for outdoor conditions.

The one-event run can still place the correct grid point first. Its lesson is reduced
constraint and changed nuisance parameters, not a requirement to produce a wrong winner.
Compare the surface and common-clock estimate. In the reference run the one-event
clock was **10.75 s**, versus the correct two-event **11.25 s**.

The reversed-time and three white-noise controls had much lower scores than the signal
case. They still returned ranked hypotheses and `accepted_location: false`. Do not
teach a universal threshold from these few controls. They are engineered examples.

Other answers:

- 3 km / 343 m/s ≈ **8.75 seconds**. An aircraft at 100 m/s moves roughly 875 m during
  that interval; a constant delay still cannot repair every part of a changing curve.
- A 100 m square grid's largest nearest-node distance is **70.71 m**, when the true
  point lies within a complete cell. A 200 m grid gives **141.42 m**. Neither bounds
  localization error from a wrong model or missing candidate.
- Two harmonics share an underlying source and geometry; they are not two independent flyovers.
- Non-detection can reflect poor recording conditions or missing flight data. It does
  not establish that no aircraft passed.
- The video narration is edited and mixed. Its clock is not the field recorder's clock.

## Assessment rubric — 100 points

| Criterion | Points | Full-credit evidence |
| --- | --- | --- |
| Provenance and scope | 15 | Identifies input/hash, bounds, windows and shared clock |
| Signal interpretation | 15 | Correct curve/harmonic explanation; observation distinguished from attribution |
| Model reasoning | 20 | Correct emission/reception distinction; explains common clock and source-tone assumption |
| Controls and alternatives | 25 | Compares all three required challenges; preserves a meaningful alternative |
| Evaluation | 10 | Correct error calculation without generalizing synthetic accuracy |
| Conclusion | 15 | Clear warranted claim, two material limitations, sensible independent next check |

Deduct for unsupported certainty, not for a cautious conclusion. Give partial credit
for a correct conceptual explanation if software setup prevented a run. The exact
winning coordinate alone earns very little without an evidence assessment.

## Troubleshooting during class

| Symptom | Action |
| --- | --- |
| `python` opens Microsoft Store | Install a supported Python interpreter before class; use the provided report today |
| PowerShell blocks activation | Use the explicit `.venv\Scripts\...exe` paths; activation is unnecessary |
| “Output directory is not empty” | Choose a new output name; preserve previous experiments |
| No NumPy/SciPy | Install with the same virtual environment's Python, not a different global interpreter |
| `ffmpeg` missing | Use the generated WAV; the core lab does not need FFmpeg |
| Very different results | Compare version, manifest hash, seed, modifications and selected audio channel |
| No supported candidates | Check track coverage, event windows, frequency band and clock basis |
| HTML will not open inside a managed viewer | Open the file in a permitted browser, or use the included PNG/JSON files |

## Instructor boundaries

The public answer key is intentional: this is a reasoning lab, not a secret-coordinate
competition. For a graded blind assessment use separately collected field data with
truth held by an independent evaluator. Do not claim independent field accuracy until
that evaluation has actually been performed.
