# Reproducible fictional example

- `classroom/`: generated noisy WAV, candidate tracks, manifest and evaluation truth.
- `report/`: prebuilt baseline report, plots, candidate CSV and full JSON results.
- `benchmark.json`: measured controls and sensitivity results, with configurations and hashes.

All aircraft, coordinates and audio in this directory are fictional and original.
They are distributed under the project's MIT license. No origin on Earth is assigned.

Regenerate from the source checkout with:

```powershell
.\.venv\Scripts\python.exe scripts\benchmark.py --output work\fresh-benchmark
```

The benchmark reads the hidden truth only for evaluation, after handing the case to
the solver. Search code does not consume `truth.json`. Keep it closed until the lab's
evaluation step. See `docs/VALIDATION.md` for the measured reference and its limitations.
