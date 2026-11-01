# Fresh Solutions

A general, reproducible hybrid metaheuristic solver for hard combinatorial optimisation.

Fresh Solutions extracts the search architecture developed in WS4:

- compiled/sparse problem state;
- exact incremental accounting;
- compact candidate and effect indexes;
- exact CPU local moves;
- batched GPU population search;
- weighted goal programming with inspectable aspirations;
- exact replay of every reported incumbent.

## Status

P4 (benchmark adapters and evidence) is complete: QAP, TSP, and graph-colouring adapters run through the same hybrid engine, with QAPLIB/TSPLIB parsers and replayable evidence. P5 remains planned.

## Relationship to the papers project

Fresh Solutions is the public solver artifact for the second paper in
[`UBC-FRESH/fresh-solutions-papers`](https://github.com/UBC-FRESH/fresh-solutions-papers).
That project contains the paper evidence and the submodule pinned to this repository.

## Intended architecture

```text
problem adapter
  -> decision variables / domains
  -> compact candidate representation
  -> exact + batched objective evaluation
  -> feasibility / repair rules
  -> move operators and optional graph/spatial structure
        |
        v
fresh-solutions engine
  -> resident state and delta accounting
  -> CPU exact local search
  -> GPU population search
  -> scheduling, checkpoints, seeds, telemetry, replay
```

## Non-goals

- It is not a universal MIP solver.
- It is not a proof of optimality.
- It does not hide infeasibility behind a scalar objective.
- It does not claim a benchmark win without an exact, replayable schedule.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest
sphinx-build -b html docs _build/html -W
python scripts/check_workflow.py
```
