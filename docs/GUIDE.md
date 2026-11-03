# From background noise to a defensible hypothesis

A passing aircraft changes pitch as the geometry between it and a microphone changes.
Historical flight positions let us ask a reverse question: **what frequency curve would
each candidate microphone position have heard?** Comparing those predictions with a
recording can narrow a location hypothesis.

This guide accompanies Argelius Doppler Lab, an original educational implementation
inspired by [colsto's demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI). It is
designed to make the method inspectable. Start with fictional data, then use controlled
recordings to learn which assumptions survive outside the lab.

## A complete first experiment

Follow the [installation commands](../README.md#start-in-five-minutes). Generate and run
the default case. Open `report.html`. Nothing is uploaded, and the report contains its
own plots; it does not load map tiles, fonts or analytics from external services.

The first plot shows time along the horizontal axis and frequency vertically. Brighter
regions contain stronger energy relative to that frequency's typical level. Mint curves
show the top hypothesis. The second plot shows the same hypothesis evaluated over a
declared local grid. The table keeps spatial alternatives visible.

Look for the entire curve shape, especially changes near closest approach. A local
overlap over a few frames is weak evidence. Check the two event scores separately: a
good fit for event one does not excuse a poor fit for event two. Read the configuration
and hashes at the bottom before comparing reports from different runs.

## Why timing matters

Suppose a sound takes nine seconds to reach the microphone. The aircraft can move
hundreds of metres during those nine seconds. The frequency at the microphone reflects
the aircraft when it emitted the sound, not where it is now. Our predictor explicitly
maps emission time to arrival time for each receiver position.

One continuous recording has one start time. If two flyovers appear in it, both must
be explained with that same clock. Fitting a separate time shift for every flyover
throws away the relative timing evidence that makes the joint search more useful.

## A result you can challenge

Run the supplied variants and negative cases in [the lab handout](STUDENT_LAB.md).
Each condition should answer a concrete question:

| Experiment | Question |
| --- | --- |
| Use only the first event | How much do the alternatives and clock change without the second constraint? |
| Change sound speed | Is the location stable under a plausible modeling change? |
| Remove matching flyover tones | Does a score still appear when there is nothing to find? |
| Reverse time and rerun all fits | Does the procedure prefer any strong structure regardless of physical shape? |
| Change source pitch over time | Does the constant-tone assumption cause a biased location? |
| Remove the true track | Can a wrong candidate still look persuasive? |

Do not compare raw scores from incompatible scoring settings as if they were calibrated
units of evidence. Do not turn adjacent high-scoring cells into independent votes.
Do not use the control examples here to promise a false-positive rate in real cases.

## Finer search, carefully

A finer grid can reduce sampling error after a broad local search. The helper uses
the current leader without reading hidden truth:

```powershell
.\.venv\Scripts\python.exe scripts\refine_case.py work\class-case\case.json work\class-result\results.json --output work\class-case\case-fine.json
.\.venv\Scripts\doppler-lab.exe run work\class-case\case-fine.json --output work\fine-result
```

This refines one local mode. It does not prove that mode is globally correct. Compare
several spatial alternatives and preserve the broader result. Flat-grid refinement
is supported by the helper; terrain-aware observer sets need explicit preparation.

## Moving to recordings you own

Use [DATA.md](DATA.md) to preserve media, establish a UTC clock, normalize flight tracks,
reconcile heights and declare bounded receiver candidates. The current tool expects
you to supply event windows and candidate aircraft segments. It does not infer a
country, date or complete flight inventory from arbitrary audio.

A good first field test has a stationary microphone, multiple independent flyovers,
known time, a documented observer position, stable recording settings and compatible
trajectory data. Have someone else hold the true position while you analyze. Include
recordings without useful aircraft tones. Record failures as carefully as successes.

## What to publish

Publish input permissions, provenance, hashes, preprocessing, search bounds, event
selection rules, data gaps, per-event overlays, alternative candidates, controls and
evaluation methodology. Clearly separate source-informed replays from blind tests.
If raw data cannot be redistributed, provide permitted derived material and exact
acquisition instructions, while stating what another analyst cannot reproduce.

A defensible conclusion might read:

> Within the declared local grid and candidate aircraft set, the leading hypothesis
> explains both selected frequency curves under one clock offset. The result is
> sensitive to the assumed propagation model and has not been independently verified.

That statement is more useful than an unjustified “exact location found.”
