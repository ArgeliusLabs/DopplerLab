# Community roadmap

Argelius Doppler Lab is an experimental, open-source teaching toolkit. We want useful
contributions from analysts, educators, acoustics researchers and developers. A careful
failure report can be more valuable than another attractive screenshot.

## Start here

| Area | Useful first contribution | Evidence to include |
| --- | --- | --- |
| Installation and teaching | Try the quickstart on a fresh machine or teach the lab | OS/Python versions, confusing steps, timing, suggested wording |
| Negative cases | Produce a fictional case where the model is wrong or ambiguous | Generator/seed, unchanged search settings, complete results |
| Physics review | Check signs, units, interpolation or propagation assumptions | Independent derivation or analytic test, including the failing case |
| Reporting and accessibility | Improve labels, table readability, keyboard access or printable output | Before/after example and an explanation of the user benefit |

Use [Issues](https://github.com/ArgeliusLabs/DopplerLab/issues) for changes, questions,
ideas, classroom experiences and experiments. The experiment template helps capture
enough detail for others to reproduce a result.

## Research priorities

1. **Blind field validation.** Collect authorized recordings with documented sample-zero
   time and microphone position. Hold truth out of analysis and publish failures as well
   as successes. Begin with the [field protocol](FIELD_PROTOCOL.md).
2. **Model mismatch.** Evaluate source-pitch drift, wind, trajectory noise, height error
   and edited recordings. A concentrated score peak alone is not acceptance evidence.
3. **Data preparation.** Add small provider-specific importers with explicit source terms,
   units, coordinate references, time semantics and gap handling. Do not bundle restricted databases.
4. **Measurement workflow.** Improve ridge annotation and preserve the analyst's event
   choices in a reproducible record.
5. **Broader search.** Consider larger geographic indexes only alongside complete-search
   accounting, resource limits, terrain support and validation of the local model.

These are open priorities, not promised features or deadlines. Keep the core lab easy
to install and run offline. New claims of accuracy must be supported by an independently
reviewable evaluation, not by tuning against known truth.

## Making corrections

Open a bug report with a minimal non-sensitive reproducer. State whether it affects
physical predictions, ranking, documentation or presentation. For scientific changes,
retain previous benchmark results and explain how conclusions change. Pull requests
should include appropriate checks and an update to the relevant documentation.

The project credits colsto's demonstration and links related implementations. Please
continue that practice when bringing in new research or code.
