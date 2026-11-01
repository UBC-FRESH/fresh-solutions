# Fresh Solutions v0.5.0

Date: 2026-11-01

Lin–Kernighan TSP release.

## Changes

- Added candidate-list Lin–Kernighan sequential edge exchange.
- Added deterministic double-bridge kicks for iterated Lin–Kernighan.
- Five-seed TSPLIB campaign from converged Or-opt tours:
  - berlin52, kroA100, kroB100: 0.000% mean gap;
  - ch150: 0.383% mean gap, 0.475% worst.
- Kicks ablation:
  - LK-only means 0.780–2.580%;
  - ILK-5 means 0.000–0.558%;
  - ILK-20 means 0.000–0.383%.
- All 20 LK tours and all 60 ablation tours replay exactly.
- Added public API docs and tests for the LK path.
- Extended the TSPLIB parser to `EUC_2D`, `CEIL_2D`, `ATT`, `GEO`, and explicit symmetric matrix formats.
- Version/citation updated to v0.5.0.

## Known gaps

- The LK comparison is quality-at-additional-cost, not equal-budget.
- No independent TSP solver baseline and no TSPLIB-wide campaign.
- No state-of-the-art claim.
- No PyPI publication in this release.

# Fresh Solutions v0.4.0

Date: 2026-11-01

Competitive QAP neighborhood release.

## Changes

- Added QAP robust tabu with exact O(n) swap deltas.
- Five-seed QAP means: tai12a 0.000%, tai20a 0.403%, tai25a 0.786%, tai30a 0.792%.
- Retained TSP Or-opt and the convergence protocol.
- Randomized 3-opt evaluated and rejected; retained as an experimental module.
- Added the heuristic progression report and public framework guide.
- Version/citation updated to v0.4.0.

## Known gaps

- QAP tabu is a specialized adapter module, not a generic move.
- TSP 3-opt/LK is not adopted.
- No full public benchmark campaign.
- No tag/release without explicit approval.

# Fresh Solutions v0.3.0

Date: 2026-11-01

Convergence and neighborhood release.

## Changes

- Added `ConvergenceConfig`, `ConvergenceResult`, and `run_to_convergence`.
- Added TSP Or-opt segment moves alongside 2-opt.
- Added TSP Or-opt contract tests.
- Convergence pilot: tai12a local optimum 7.397%; kroA100 reaches optimum 21,282; ch150 reaches 6.495% gap with a patience stop at 191,651 evaluations.
- Version/citation updated to v0.3.0.

## Known gaps

- Convergence is a stopping-rule claim, not a global-optimality proof.
- QAP tai12a remains at a local optimum.
- QAP/TSP campaign is not yet released as final evidence.

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
