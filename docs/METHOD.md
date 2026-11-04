# Model and scoring

## Coordinates, clocks and assumptions

All numerical geometry uses one right-handed local ENU frame in metres: east, north,
up. Aircraft and receiver coordinates must use the same origin and compatible vertical
reference. A receiver is stationary. Aircraft are subsonic. Air is still, homogeneous
and represented by one sound speed `c`. Direct-path propagation is assumed.

Track timestamps are seconds relative to a documented epoch. Audio uses seconds from
its first sample. For every event in one continuous recording:

```text
track arrival time = audio-relative time + clock_offset_s
```

The offset may represent a UTC recording start relative to the track epoch, or a
fictional clock in the demonstration. An upload timestamp is not a recording timestamp.
Clock drift, edits and sample-rate changes are not modeled by a single offset.

## Retarded sound time

For emission time `te`, aircraft position `p(te)`, velocity `v(te)` and receiver `q`:

```text
r(te) = p(te) - q
R(te) = norm(r(te))
range_rate(te) = dot(r(te), v(te)) / R(te)   # positive when receding
ta(te) = te + R(te) / c
f_heard(ta(te)) = f_source / (1 + range_rate(te) / c)
```

Since `dta/dte = 1 + range_rate/c`, the map is monotone for the supported subsonic
motion. We evaluate the source trajectory on a dense emission-time grid, form its
arrival times and frequency ratios, and interpolate those ratios onto audio frame times.
This is a forward arrival-time map, not a constant horizontal shift.

`Track` uses coordinate-wise PCHIP on the supplied samples, with its analytic derivative
for velocity. Sampling the interpolant every 0.25 s reduces numerical cost during search.
Coordinates are not automatically smoothed: smoothing can erase real turns or introduce
false accelerations. PCHIP is not a physical aircraft dynamics model. Its implied
velocities must be inspected, and all sampled speeds >=0.9c are rejected. Sparse tracks,
timestamps out of order, duplicate times and excessive gaps are rejected.

No trajectory or frequency extrapolation is allowed. Every scored event must have
complete support for its fixed set of audio frames. Unsupported trials are counted.
The absence of a supported model is not evidence that a candidate location is impossible.

## Ideal straight-flight screening

For constant speed `v` and closest slant range `d`, let `tau = te - t_cpa` and
`u = ta - t_cpa`. Then:

```text
R = sqrt(v² tau² + d²)
tau = [c² u - sqrt(c² v² u² + (c²-v²)d²)] / (c²-v²)
```

The minus-root selects emission before reception. `fit-ridge` uses this expression
with robust nonlinear least squares and nine initial guesses. It reports speed,
slant range, source frequency, emission/arrival CPA, residual error, a Jacobian condition
number and proximity to search bounds. A successful optimizer does not establish that
the ideal model describes the aircraft. No covariance-derived confidence interval is
reported because the trace errors and model mismatch are not calibrated.

In a sufficiently long straight flyby, limiting approach/recede frequencies constrain
speed and source tone; many recordings do not reach those limits. A chosen harmonic
can be modeled as its own constant source tone. It must not be mistaken for an
independent flyover.

## Audio representation

The loader selects one channel explicitly to avoid phase cancellation from a stereo
average. It scales integer PCM, checks finite samples, and downsamples with an
anti-aliasing polyphase filter to 4 kHz. Spectrograms use a Hann window and SciPy
`ShortTimeFFT`. Only complete windows are retained.

The demonstration uses a 2 s window, 0.5 s hop and a 450 Hz plotting/scoring ceiling.
Frequency-bin spacing is 0.5 Hz; actual resolution also depends on the Hann main lobe
and a signal's motion during the window. Increasing FFT size by zero padding would
not create independent frequency information. Time and frequency precision trade off.
[SciPy ShortTimeFFT documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html).

For each frequency bin, subtract its median log power over time. This suppresses
persistent hum. It can also suppress a long-lived real tone, so retain the original
audio and inspect representation choices.

## A transparent matching score

For each modeled frequency at each selected frame:

1. Interpolate whitened log power at the predicted frequency and +/-0.5 Hz; average
   those three values to tolerate a narrow model mismatch.
2. Average log power 6 Hz above and below as local flanks.
3. Subtract flank from core and clip that frame's contrast to [-30, 30] dB.
4. Average equally across the same fixed frames for every candidate.

The average core avoids an avoidable noise bias from taking a local maximum. Searching
tones, clocks and positions still raises the maximum noise score. Nearby genuine tones
can contaminate the flanks; the fixed 6 Hz choice is a teaching default, not a universal
detector bandwidth. Window length, sample rate and scoring rules must stay fixed across
comparisons.

Each event searches its declared source-tone values and candidate tracks. Each independent
event must use a distinct track ID. Joint hypotheses share **one** clock offset. Joint
score is the arithmetic mean of per-event scores, so long events do not automatically
outvote short ones. A strong event can still conceal a weak event in the mean; the
report exposes each event score and flags a minimum below 3 dB as an **uncalibrated
heuristic**. That flag is not an acceptance rule.

The search retains the best clock, source tones and assignment at every receiver point.
Complete results are exported. The summary also selects spatial alternatives at least
300 m apart to reduce repetitive display of adjacent cells. That separation is for
presentation, not a statistical independence claim.

## Bounds and computational scope

The local solver supports one to four nonoverlapping flyovers, <=20,000 receiver points,
<=1,001 clock offsets, <=201 source-tone samples per event and <=256 flight assignments.
It caps the declared work at 20 million frequency-line trials. Receiver positions must
lie within 50 km of the local origin. These are engineering limits, not claims of
physical accuracy over that radius. Tracks imported from geographic data share the
same 50 km limit; custom local CSVs remain the preparer's responsibility.

Separate preparation commands index flight archives and [retrieve supported terrain](TERRAIN.md).
The local solver does not infer an absolute date, search all possible aircraft
automatically, model audibility or make a final location decision.
Use narrow, independently justified bounds. If the true source or
location is missing from them, a plausible-looking wrong winner can still emerge.

## Uncertainty and validation

Scores are neither likelihoods nor probabilities. No “95% location circle” is derived
from this surface. Repeat the **entire** search on suitable negative controls; rerunning
only the winning curve would omit the search's selection effect. Reversed audio and
three noise seeds are engineering checks, not a calibrated false-positive study.

For real recordings, perturb sound speed, timing, source-tone assumptions, event windows,
trajectory sampling and receiver heights. Check grid edges and several competing modes.
Use a held-out flyover or an independently recorded location to test the final hypothesis.
Report all failures, missing coverage and assumptions alongside any coordinate estimate.
