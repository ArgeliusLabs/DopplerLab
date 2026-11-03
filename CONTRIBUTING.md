# Contributing

Small, inspectable contributions are welcome. Reproduce a failing case and explain
what changes in the evidence or behavior before proposing a new heuristic.

## Find a starting point

See the [roadmap](docs/ROADMAP.md), open a focused issue, or choose a task labeled
`good first issue` or `help wanted`. Documentation corrections and classroom feedback
are useful contributions. For a larger change, describe the design in an issue before
investing heavily in implementation.

Fork the repository, create a branch, and open a pull request against `main`. Explain
the problem, the resulting behavior and how you verified it. Keep unrelated changes
separate. Follow the [community guidelines](CODE_OF_CONDUCT.md).

## Verify your change

Install `.[dev]`, then run `python -m pytest`, `ruff check .`, and `ruff format --check .`
inside your virtual environment. For changes to physics or scoring, also run
`python scripts/benchmark.py --output work/new-benchmark` and compare every condition.
Document changes in parameters or expected outputs. Do not tune a matcher against a
hidden coordinate and then call the result blind validation.

Useful contributions include independent analytic tests, licensed field datasets with
documented clocks and microphone locations, negative cases, uncertainty studies,
provider importers with explicit units and datums, and accessibility improvements.

Do not commit API credentials, personal recordings without permission, raw commercial
flight databases, or the third-party video/transcript that inspired the lab. Keep
local experiments in ignored `work/` or `local-review/` directories. If reporting a bug,
use a fictional reproducer when possible and include tool/dependency versions, manifest
and error output with sensitive paths or data removed.

Contributions are submitted under the repository's MIT license. Credit external
research and retain notices for any third-party code you introduce. The current source
was written independently; the original video and DOPPLERGEIST are related work, not
code dependencies.
