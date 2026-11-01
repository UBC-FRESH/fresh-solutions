# Fresh Solutions v0.2.0

Date: 2026-11-01

Maintenance release.

## Changes

- TSP adapter now uses 2-opt segment reversal instead of swap-only moves.
- TSP mutation uses segment reversal.
- Public `berlin52` evidence improves from 17,216 (128% gap) to 9,033 (19.8% gap)
  at population 32, 50 generations, 3,000 local iterations.
- Version and citation updated to v0.2.0.

## Known gaps

- Still a toy/public-instance evidence pass, not a full benchmark campaign.
- QAP is within about 7.4% of the tai12a optimum with the stronger settings.
- CPU-only backend; no production GPU kernel.

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
