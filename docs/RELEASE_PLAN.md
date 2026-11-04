# Community releases and demonstration plan

## Positioning

**Name:** Argelius Doppler Lab.
**Repository:** [ArgeliusLabs/DopplerLab](https://github.com/ArgeliusLabs/DopplerLab).

**One-sentence description:** An aircraft-audio investigation toolkit for acquiring
flight data, testing location hypotheses and teaching the limits of sound-based OSINT.

Lead with a reproducible investigation workflow: aircraft-data acquisition, candidate
screening, transparent physical modeling and useful failure cases. Include original
fictional data and a complete instructor pack for classroom demonstrations.
Credit colsto prominently. Link DOPPLERGEIST as related work. Do not claim first invention,
an affiliation, universal exact geolocation or demonstrated nationwide precision.

## What belongs in the public release

- MIT source package, documented CLI, tests and CI configuration.
- Original fictional audio, tracks, manifests and reference report.
- Research review, methodology, data-preparation guide and measured benchmark.
- Student handout, instructor guide, rubric and field-validation protocol.
- A source ZIP and a portable student handout/report pack, with SHA-256 checksums.
- Tested Windows, Linux, Intel Mac and Apple Silicon executable archives, with build
  provenance, dependency licenses and SHA-256 checksums; see [BINARIES.md](BINARIES.md).

The source license allows reuse, including commercial use. It does not convey rights
to the original YouTube media or third-party flight databases. No such data is bundled.
The publicly available answer key is intentional; assessment focuses on reasoning.

## Classroom pilots

The lab offers guided analytical practice: identifying weak evidence, preparing data
correctly, testing assumptions, resolving ambiguity and writing defensible conclusions.
Share classroom feedback and suggested improvements through the contribution workflow.

Before advertising a real-data advanced lab, complete the blind field protocol, secure
redistribution rights and rehearse it on student hardware. Evaluate setup time, completion
rate, interpretation errors and student feedback.

## Four-minute launch demo script

| Time | Action | Point to make |
| --- | --- | --- |
| 0:00–0:30 | Play a short excerpt of our fictional recording | Ordinary background sound can contain structure |
| 0:30–1:15 | Reveal the spectrogram and predicted curves | Show emitted sound versus received sound |
| 1:15–2:00 | Open the two-event report and score map | One shared clock constrains both events |
| 2:00–2:45 | Show the missing-aircraft and noise controls | A convincing winner can be wrong |
| 2:45–3:30 | Reveal fictional truth and sensitivity results | Explain what was tested and what remains unknown |
| 3:30–4:00 | Show the student handout and repository | Invite reproducible experiments and field validation |

Use the synthetic 39 m coarse-grid result only with its synthetic qualification on
screen. The stronger story is “you can test this yourself,” not “we can locate anyone.”

## Current community announcement draft

> We're developing Argelius Doppler Lab: an open-source investigation toolkit
> inspired by colsto's aircraft Doppler demonstration.
>
> It retrieves aircraft tracks and terrain, reviews original recordings, and compares
> the sounds candidate microphone positions would hear. Windows, Linux and Mac builds
> include a quickstart and generated practice; optional teaching materials are included.
>
> Testing is in progress. Our first original-recording test ran the data pipeline but
> did not support a location: a reversed-event control scored as well as the original
> search. Real-world location finding remains unproven. We publish failures so the
> community can inspect the evidence and improve the method.
>
> Help with independent physics review, clear flyover recordings, controls and later
> blind evaluation. Credit to colsto for the inspiration and to the broader community
> exploring this technique.

Link the released version, field-test outcome and validation record when sharing this announcement.
The draft is provided for reuse; it does not imply that an announcement was posted elsewhere.

## Release checklist

Ordinary development pushes run tests and produce temporary native candidates.
Experimental releases may be published while **testing is in progress**, provided the
release notes distinguish completed automated/benchmark checks from unfinished field
tests. Original recordings are not a publication prerequisite; field-accuracy claims
still require appropriate evidence.

Update the version in `pyproject.toml` and `src/doppler_lab/__init__.py`, the versioned
download links/checkpoint in `QUICKSTART.md` and `docs/BINARIES.md`, and the release notes
around the actual testing status. Exercise the quick-start and practice commands from
an extracted native archive, including its local documentation links. Publish by manually dispatching with
`publish_release` set to true, or by pushing an explicit publishing commit to `main`
whose complete subject is `release: publish vVERSION` (matching the package version).
Both routes require all four test jobs and all four native build/smoke jobs to pass.
The workflow rejects `.dev` versions and mismatched publishing subjects.

The release job assembles source/student ZIPs, wheel, source distribution, source
inventory, all four native archives and checksums. It leaves existing versioned
releases unchanged and does not publish to PyPI. Build candidates and their expiry
are described in [BINARIES.md](BINARIES.md).

1. Review the source, input permissions, documentation and validation record for the version.
2. Review every test and native smoke job, including the source commit and platform
   limitations. State when original-recording tests have not yet been performed, and
   record their outcomes, including unsuccessful cases, when available.
3. Trigger publication for the reviewed version and verify its public
   source/student/native assets, dependency notices and checksums.
4. Add the video credit, project scope and field-validation limitations to the repository description.
5. Record a demo using the supplied fictional data and clearly labeled results.
6. Pilot the 110-minute lab with a small class; collect setup and learning feedback.
7. Perform a separate blind field study before expanding accuracy claims or promising
   an automatic real-world geolocation exercise.

## Next technical work, ranked

| Priority | Work | Evidence required before claiming completion |
| --- | --- | --- |
| 1 | Known-site acoustic diagnosis, then a separate blind field benchmark | Independently identified flyover and controls; later frozen predictions, held-out truth and representative failures |
| 2 | Source-pitch and propagation sensitivity | Recovery and abstention behavior across realistic perturbations |
| 3 | Licensed provider-specific importers | Fixtures with explicit units, datums, gaps and timestamp semantics |
| 4 | Ridge annotation interface | Usability test; provenance for analyst choices |
| 5 | Terrain completeness studies, more DEM providers and cross-day event pairing | Complete-search accounting, boundary tests, representative accuracy/runtime |

Large-area indexing and timing screening are now implemented and
[benchmarked](REAL_DATA_BENCHMARK.md). Their millions of alternatives make local-model
validation and competing-candidate checks essential before claiming useful field
precision. The included fictional lab remains a reproducible teaching option while
that investigation work continues.
