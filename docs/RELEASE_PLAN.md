# Community releases and demonstration plan

## Positioning

**Name:** Argelius Doppler Lab.
**Repository:** [ArgeliusLabs/DopplerLab](https://github.com/ArgeliusLabs/DopplerLab).

**One-sentence description:** An offline aircraft Doppler matching toolkit and practical
OSINT lab for testing what background sound can reveal—and what it cannot prove.

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

## Draft release announcement

> We're releasing Argelius Doppler Lab: an open-source toolkit and classroom exercise
> inspired by colsto's aircraft Doppler demonstration.
>
> It generates fictional aircraft recordings, predicts the sounds candidate microphone
> positions would hear, and makes the results inspectable. The lab includes working
> code, original data, negative controls, an instructor guide and a rubric.
>
> One of our favorite lessons: remove the correct aircraft from the search and a wrong
> location can still score well. Learning to challenge the result is part of the method.
>
> This release is validated on synthetic cases. Blind field validation is the next step,
> and the protocol is included. Credit to colsto for the inspiration and to the broader
> community exploring this technique.

Link the released version and its validation record when sharing this announcement.
The draft is provided for reuse; it does not imply that an announcement was posted elsewhere.

## Release checklist

On this repository's `main` branch, GitHub Actions publishes a prerelease for a new
package version only after all four test jobs pass. It builds the source and student
ZIPs, wheel, source distribution, source inventory and checksums on the release
runner. Existing versioned releases are left unchanged; bump the package version
and update the release notes for the next published version. The workflow does not
publish to PyPI.

1. Review the source, input permissions, documentation and validation record for the version.
2. Run the provided GitHub Actions matrix and resolve platform failures before claiming
   support beyond the locally tested Windows environment.
3. Attach the source/student archives and checksums to a versioned experimental release.
4. Add the video credit, project scope and field-validation limitations to the repository description.
5. Record a demo using the supplied fictional data and clearly labeled results.
6. Pilot the 110-minute lab with a small class; collect setup and learning feedback.
7. Perform a separate blind field study before expanding accuracy claims or promising
   an automatic real-world geolocation exercise.

## Next technical work, ranked

| Priority | Work | Evidence required before claiming completion |
| --- | --- | --- |
| 1 | Blind field benchmark with appropriate clocks and heights | Frozen predictions, held-out truth, representative failures |
| 2 | Source-pitch and propagation sensitivity | Recovery and abstention behavior across realistic perturbations |
| 3 | Licensed provider-specific importers | Fixtures with explicit units, datums, gaps and timestamp semantics |
| 4 | Ridge annotation interface | Usability test; provenance for analyst choices |
| 5 | Larger-area indexing and terrain support | Complete-search accounting, budgets, representative accuracy/runtime |

Adding a broad search before validating the local model would multiply attractive
false candidates. The local educational release is useful on its own.
