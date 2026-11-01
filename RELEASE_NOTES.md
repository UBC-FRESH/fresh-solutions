# Fresh Solutions v0.1.0

Date: 2026-11-01

First public solver release.

## Included

- Exact problem-adapter and evidence/replay contracts.
- WS4-free exact CPU local search and resident assignment state.
- Backend-neutral batched population search.
- Exact population-to-local hybrid handoff.
- Checkpoint save/load/replay.
- Graph-colouring, QAP, and TSP adapters.
- QAPLIB and TSPLIB parsers.
- Replayable benchmark harness and evidence.

## Verification

- Clean checkout tests and docs.
- Benchmark evidence replays through the adapters.
- No WS4 dependency in the core package.

## Known gaps

- `CpuBatchBackend` is exact but CPU-only; no production torch kernel.
- Benchmark instances are tiny parser fixtures, not full public benchmark campaigns.
- TSP uses swap moves, not 2-opt.
- No PyPI publication in this release.
