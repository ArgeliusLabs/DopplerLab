# Community roadmap

Argelius Doppler Lab is an experimental, open-source investigation toolkit. We want useful
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
   The [first exploratory field test](FIELD_TEST_2026_11.md) ended with insufficient
   evidence and is published as a negative result. It is not blind accuracy validation.
2. **Model mismatch.** Evaluate source-pitch drift, wind, trajectory noise, height error
   and edited recordings. A concentrated score peak alone is not acceptance evidence.
3. **Data preparation.** Add small provider-specific importers with explicit source terms,
   units, coordinate references, time semantics and gap handling. Do not bundle restricted databases.
4. **Measurement workflow.** Improve ridge annotation and preserve the analyst's event
   choices in a reproducible record.
5. **Broader search.** Validate and extend the experimental candidate-selection stage described in the
   [investigation workflow](INVESTIGATION_WORKFLOW.md): regional track indexing,
   relative flyover timing, conservative screening and auditable local shortlists.
   Version 0.2.0 provides downloads, streaming indexes, coarse timing
   shortlists, resource accounting and a local handoff. Version 0.3.0 adds USGS terrain
   downloads, recorded height conversion and broad/local terrain candidates. Additional
   terrain providers, cross-day pairing, automatic audio measurement and field completeness
   still need work.
   Version 0.4.0 adds local time-window acquisition across UTC midnight, long-media
   review and auditable conflict quarantine. Continental cross-day pairing remains
   separate work.
   See [commands and limits](BROAD_SEARCH.md) and [data measurements](DATA_VOLUME.md).

These are open priorities, not promised features or deadlines. Keep the core toolkit easy
to install and run offline. New claims of accuracy must be supported by an independently
reviewable evaluation, not by tuning against known truth.

## Making corrections

Open a bug report with a minimal non-sensitive reproducer. State whether it affects
physical predictions, ranking, documentation or presentation. For scientific changes,
retain previous benchmark results and explain how conclusions change. Pull requests
should include appropriate checks and an update to the relevant documentation.

The project credits colsto's demonstration and links related implementations. Please
continue that practice when bringing in new research or code.
