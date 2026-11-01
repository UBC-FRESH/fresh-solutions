# P3 close-out: CPU/GPU search scheduling

Status: complete
Date: 2026-11-01
Issue: #9

## Result

Fresh Solutions now has a backend-neutral batched population search and exact hybrid handoff.

Implemented:

- `fresh_solutions/backend.py`
  - `BatchBackend` protocol
  - `CpuBatchBackend`
- `fresh_solutions/population.py`
  - `PopulationConfig`
  - `PopulationResult`
  - `HybridResult`
  - `run_population_search`
  - `run_hybrid_search`
- `fresh_solutions/checkpoint.py`
  - `SearchCheckpoint` save/load/replay
- `fresh_solutions/engine.py`
  - `run_local_search(..., initial=...)`
- API docs for all new modules.

## Verification

- 157 tests passed.
- 100% branch coverage.
- Ruff and strict mypy pass.
- Sphinx `-W` pass.
- Workflow validator: 0 errors.
- Graph colouring runs through CPU-only, population-only, and hybrid paths.

## Acceptance criteria

- The same adapter can run CPU-only and hybrid paths. **Met.**
- Every tested elite replays exactly through the adapter. **Met.**
- Checkpoint replay validates objective equality. **Met.**

## Limits

`CpuBatchBackend` is exact but CPU-only. No production torch kernel or device-resident effect table is
implemented in Fresh Solutions yet. The backend protocol is the integration point.

## Recommendation

Close P3. P4 benchmark adapters and evidence remain planned.
