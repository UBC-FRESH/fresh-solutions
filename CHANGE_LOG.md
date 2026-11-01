# Change Log

Newest entries last. Each milestone gets a dated entry that matches the roadmap status and the GitHub issue comments.

## 2026-11-01

- Created Fresh Solutions from the UBC-FRESH dev workflow seed. The agent contract, roadmap, docs skeleton, and validator came from the seed. Every phase is planned, and no parent issues exist yet.

### P0 Bootstrap

- Created the public repository from the UBC-FRESH seed and adapted the README to a generic solver.
- Added the Apache-2.0 license.
- Tests, docs, and the workflow validator pass. P0 issue #1 closed; P1 issue #2 activated.

### P1 Problem-adapter contract

- P1 started. The adapter boundary is described in `notes/design/architecture.md`.
- Next: freeze the protocol and add a WS4-free toy adapter.

### P1 close-out

- Added the executable adapter/replay contract and a WS4-free graph-colouring toy adapter.
- 144 tests pass with 100% branch coverage; ruff, strict mypy, Sphinx `-W`, and the workflow validator pass.
- P1 is complete; P2 engine extraction remains planned.

- P1 roadmap corrected to match the completed toy-adapter task.

### P2 close-out

- Added the exact CPU search engine and resident-assignment primitive.
- Ran graph colouring end to end with no WS4 dependency.
- 150 tests, 100% branch coverage, ruff, strict mypy, Sphinx -W, and workflow validator pass.
- P2 is complete; P3 CPU/GPU scheduling remains planned.

### P3 close-out

- Added backend-neutral batched population search, exact hybrid handoff, and checkpoint replay.
- Graph colouring runs through CPU, population, and hybrid paths.
- 157 tests, 100% branch coverage, ruff, strict mypy, Sphinx -W, and workflow validator pass.
- P3 is complete; P4 benchmark adapters remain planned.

### P4 close-out

- Added QAP and TSP public-library adapters with QAPLIB/TSPLIB parsers.
- Added a replayable benchmark-record harness and evidence for graph colouring, QAP, and TSP.
- 167 tests pass at 97% coverage; lint, types, docs, and workflow validator pass.
- P4 is complete; P5 release remains planned.

### P5 close-out

- Added release notes, citation, code of conduct, and clean-checkout verification.
- Clean clone: 167 tests, 97.24% coverage, Sphinx -W, workflow validator 0 errors/warnings, all benchmark records replayed.
- P5 complete; v0.1.0 release.

### P6 close-out

- Added TSP 2-opt segment reversal and refreshed benchmark evidence.
- Public berlin52 improved from 17,216 to 9,033 under the stronger settings.
- Clean checkout: 168 tests, 97.02% coverage, docs and workflow validator green.
- Released v0.2.0 maintenance update.

### P7 close-out

- Added convergence protocol and TSP Or-opt.
- Convergence pilot: tai12a local optimum 7.397%; kroA100 optimum; ch150 6.495% at patience stop.
- 173 tests, docs, workflow validator green; v0.3.0 release.

### P8.1 QAP robust tabu

- Added exact-delta robust tabu for QAP and tests.
- Five-seed 10k results: tai12a 0.000%, tai20a 0.403%, tai25a 0.786%, tai30a 0.792% mean gap.
- P8 remains active; no release tag.
