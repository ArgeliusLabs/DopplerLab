# Research review: what the video establishes, and what we can reproduce

Prepared 3 November 2026 for Argelius Labs. Audience: intermediate OSINT students.

## Finding

Aircraft Doppler matching is a plausible and technically interesting way to constrain
where a recording was made. The useful innovation in colsto's demonstration is the
combination of faint tonal structure, historical aircraft trajectories, sound travel
time, multiple events and an independent visual check. The appropriate educational
claim is **“background audio can contain testable geographic evidence.”** Universal
exact-location claims are not justified by one demonstration or by a synthetic exercise.

The provided 29:11 video and English subtitle file were reviewed through the full
transcript, sampled visual frames and a locally decoded audio excerpt. Source media
and derivative inspection images remain outside the public distribution. The subtitle
file is auto-caption style, with repeated lines and occasional terminology errors.
Statements in it were treated as claims to examine, not instructions.

## The demonstration, step by step

| Video segment (approximate) | Method | What a class should notice |
| --- | --- | --- |
| 00:00–03:00 | A visually uninformative recording contains aircraft-like frequency curves | A spectrogram can reveal a faint signal that is hard to hear |
| 03:00–08:20 | Search flight records for two flyovers roughly 920 seconds apart | A relative interval is useful even without an exact recording start time |
| 08:20–11:45 | Fit idealized curves to obtain broad speed and slant-distance ranges | These estimates depend on constant speed, straight motion and stable source tone |
| 11:45–13:20 | Use the absence of intervening detected flights to reduce candidates | Absence depends on microphone sensitivity, environment and data coverage |
| 13:20–18:30 | Model actual 3D flight trajectories and delayed sound arrival | Receiver time and emission time are different variables |
| 18:30–22:00 | Score modeled curves, with both flyovers locked to a common clock | Independent time shifts would discard a valuable constraint |
| 22:00–25:30 | A faint single-event example uses tighter timing; visual corroboration follows | Known time helps, but alternative trajectories and locations still matter |
| 25:30–29:11 | Filtering, masking and phone-transmission demonstrations | Specific demonstrations are not universal guarantees about every codec or filter |

The visual material includes Flightradar24, GIS candidate maps, a Doppler fitting tool
and spectrograms. This repository does not recreate a proprietary data download or
claim access to the creator's implementation, complete input dataset or ground truth.

## Claims that need careful wording

**“Inaudible” describes the recording, not necessarily the frequency.** The visible
curves include ordinary low audio frequencies. A tone may be perceptually masked or
too quiet to notice; this does not make it ultrasonic or infrasonic.

**CPA normally means closest point of approach.** We distinguish the time of geometric
closest approach from the later arrival of the sound emitted there. Maximum recorded
loudness need not coincide with either: source directivity, gain control, absorption and
reflections can change the envelope.

**Recorded flight altitude is not automatically height above ground.** Providers may
expose barometric and geometric fields. A compatible aircraft height and receiver
height are needed for slant range. OpenSky's API documents separate fields; USGS
describes product-specific DEM references. Our importer requires explicit ellipsoid
height, and does not silently turn pressure altitude into a physical height.
[OpenSky field definitions](https://openskynetwork.github.io/opensky-api/rest.html),
[USGS DEM reference systems](https://www.usgs.gov/faqs/what-projection-horizontal-datum-vertical-datum-and-resolution-a-usgs-digital-elevation-model).

**A pitch curve does not always determine speed uniquely.** Unknown changing engine or
propeller RPM can imitate some Doppler changes. Short curves may not show either
asymptote; multiple parameter combinations can fit them. The ideal fit is a screening
estimate whose residuals, fit bounds and sensitivity must be inspected.

**Silence is conditional evidence.** A flight database is not an acoustic audibility
model. Terrain, buildings, wind, distance, aircraft type, source power, recording gain
and compression all affect detection. The toolkit deliberately omits hard silence-based
rejection. A future implementation should estimate detection probability from measured
conditions, including known missed flyovers.

**More pixels or a smaller grid do not prove more accuracy.** A 100 m grid bounds only
the distance to the nearest grid node under an ideal complete square lattice. Model
error, wrong flight association and an excluded true location can be much larger.

**A winning score is inevitable in many wrong searches.** After trying enough locations,
times and tones, noise also has a maximum. Every negative control must rerun the same
optimization. Adjacent high-scoring points are not independent confirmations. Multiple
harmonics of the same aircraft are not multiple independent aircraft.

**Filtering claims must name the actual pipeline.** A finite high-pass filter attenuates
frequencies; it need not erase every trace. Gain can reveal a residual signal but does
not restore information that was completely removed. A successful phone demonstration
shows survival in that tested path, not all phone systems. Cuts can defeat an interval
constraint while leaving a single flyover analyzable. Replacing or removing the original
audio removes this particular acoustic evidence from the exported artifact, but other
location clues can remain. Test the final exported file.

## Independent derivation and physical checks

For source position `p(te)` and fixed receiver `q`, let `R = |p(te)-q|`. Successive wave
cycles emitted `dte` apart arrive `dta = (1 + dR/dte / c) dte` apart. Frequency therefore
scales by `dte/dta`. This produces the equation implemented in [METHOD.md](METHOD.md).
The relation changes along the path, so adding one constant delay to an otherwise
incorrect curve does not repair it. NASA's explanation supplies a general acoustic
Doppler reference; the retarded-time derivation and numerical tests here are our own.
[NASA Doppler effect](https://www.grc.nasa.gov/www/k-12/airplane/doppler.html).

The speed of sound depends on gas state, including temperature. The implementation
uses a configurable uniform value and exposes a dry-air approximation; it does not
solve wind fields, atmospheric refraction or humidity-dependent propagation. Sensitivity
runs are therefore part of the lab, not optional decoration.
[NASA speed of sound](https://www.grc.nasa.gov/WWW/k-12/VirtualAero/BottleRocket/airplane/sound.html).

## Existing implementation and contribution

Aircraft acoustic tracking has a research history predating this video. It is useful
to distinguish the inverse problems: many studies locate an aircraft using microphones
at known positions, whereas this project treats the aircraft trajectory as known and
searches for the microphone position.

| Primary reference | Relevance and limit |
| --- | --- |
| [Aircraft localization using a passive acoustic method. Experimental test (2016)](https://doi.org/10.1016/j.ast.2015.11.023) | Its published abstract describes relative Doppler stretch across a microphone mesh and nonlinear recovery of aircraft position/velocity. This is related acoustic geometry, not validation of arbitrary recording-location search. |
| [Three-Dimensional UAV-Based Atmospheric Tomography (2013)](https://doi.org/10.1175/JTECH-D-12-00036.1) | The publisher's summary connects emitted/received UAV spectra, travel time and atmospheric sound speed. It reinforces why propagation assumptions need measurement rather than being treated as exact constants. |
| [NASA sUAS acoustics research summary (2018)](https://ntrs.nasa.gov/citations/20180002208) | Describes a program of flyover measurements, component tests, prediction and perception research. Its measurement discussion includes synchronized acoustic/vehicle data and changing rotor signatures; a controlled field protocol matters. |

The first two entries were reviewed at the publisher-summary/abstract level, not as
independently replicated studies. The NASA report's instrumentation material was also
consulted. These references provide context, not a performance claim for our tool.

[DOPPLERGEIST](https://github.com/1337isnot1337/DOPPLERGEIST) is an independent project
already working on broader aircraft Doppler geolocation. Its README reviewed on
3 November 2026 describes real-recording experiments as well as substantial unresolved
validation limits. Its claimed results were not independently rerun in this project.
We do not claim to be the first open-source implementation, and no source code from
that project was copied.

Argelius Doppler Lab contributes a deliberately small reference implementation, native
Windows verification, independently synthesized fictional cases, full-search negative
controls, and a classroom sequence with assessment. Its scoring system is original and
different from the raw brightness scoring described in the video.

## Evidence ladder

1. **Physics consistency:** approaching/receding behavior and an independent analytic
   constant-speed solution agree with the numerical model.
2. **Synthetic recovery:** an independent waveform generator and sparse rounded tracks
   produce a recoverable fictional observer location. These still share broad acoustic
   assumptions, so success is not external validation.
3. **Real-media processing:** a provided video excerpt can be decoded and plotted.
   Speech and tonal structure do not by themselves identify an aircraft or a location.
4. **Controlled field validation:** collect synchronized, authorized recordings with
   known microphone positions and sufficiently sampled flight tracks; keep truth hidden
   from the analyst. This has not yet been completed here.
5. **Generalization:** test diverse sites, aircraft, codecs, weather and negative cases;
   publish failures and false-localization rates. This has not yet been established.

The release supports levels 1–3, with a reproducible protocol for level 4. It should be
marketed as an experimental OSINT teaching toolkit, not a proven surveillance capability.
