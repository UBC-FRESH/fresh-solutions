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

### P8.2 TSP 3-opt evaluation

- Added experimental randomized 3-opt and exact-replay tests.
- No improvement over converged Or-opt on berlin52/kroA100/ch150; not adopted.
- P8.2 complete with a recorded limit; P8.3 remains open.

### P8.4 heuristic progression

- Added `notes/reports/heuristic-progression.md` with stage budgets, measured gaps, and negative 3-opt result.
- Added public Sphinx guide `docs/heuristic-progression.rst`.
- No release tag; P8.3 remains open.

### P8.3/P8 close-out

- QAP robust tabu and Or-opt progression packaged.
- QAP five-seed means 0.000–0.792%; TSP 3-opt negative result retained.
- Release candidate v0.4.0; phase PR queued.

### P8 close-out

- P8.1 QAP tabu, P8.2 TSP 3-opt evaluation, P8.4 progression guide complete.
- Clean clone: 178 tests, 96.03% coverage, docs, workflow and benchmark harness pass.
- P8.3 release candidate v0.4.0 queued for approval.

### P9.1 certified QAP docs

- Added the certified QAP budget ladder and SciPy FAQ baseline to the public progression guide.
- Corrected the outdated 10k-fixed limit.
- No code change or release.

### P10.1 Lin–Kernighan core

- Added `fresh_solutions.adapters.tsp_lk`: candidate-list sequential edge exchange,
  deterministic double-bridge kicks, and exact tour construction.
- Added `tests/test_tsp_lk.py` for validity, determinism, replay, configuration, and small cases.
- Extended the public API exports and docs page.
- Dashboard green: 186 tests, 95.21% coverage, all gates pass.
- No release tag; TSPLIB campaign is next.

### P10.1 LK evidence and docs

- Five-seed iterated LK campaign from converged Or-opt tours.
- Three instances reach the known optimum; ch150 mean gap 0.383%; 20/20 exact replays.
- Public progression guide updated with Stage 4 and the extra-budget caveat.
- No release tag; close-out queues the phase PR.

### v0.5.0 release prep

- Version/citation bumped to 0.5.0.
- Release notes cover Lin–Kernighan, the five-seed campaign, and the kicks ablation.
- Release candidate from main `24dc60c`; tag/release approved by maintainer.
- Extended TSPLIB parsing to ATT, GEO, and explicit matrix formats for the broad benchmark panel.

### v0.5.1 TSPLIB GEO fix

- Fixed GEO latitude/longitude conversion in the TSPLIB parser.
- Added ATT/GEO/EXPLICIT parser tests.
- Broad-panel results must be rerun against v0.5.1; v0.5.0 GEO numbers are invalid.

### P10.1 convergence stopping

- Added `patience` to `TspLkConfig`: stop after N kicks without a new best tour.
- Added `patience` to `QapTabuConfig`: stop after N iterations without a new best assignment.
- Added plateau tests for both adapters.
- Removed the 30-second benchmark-cap interpretation; capacity runs now use the plateau rule.

### v0.6.0 convergence-stopping release

- Version/citation bumped to 0.6.0.
- Release notes cover patience stopping and cap-hit reporting.
- Tag/release approved by maintainer.

### P10.1 optional LKH backend

- Added `fresh_solutions.adapters.lkh` as an optional wrapper around a user-supplied LKH binary.
- LKH is not bundled; the research-use binary remains external.
- Added fake-backend tests for invocation, parsing, failure, and replay.

### v0.7.0 optional LKH release

- Version/citation bumped to 0.7.0.
- Release notes document the external backend and its license boundary.
- Large-tail LKH evidence is in the papers repository.

### P10.1 multi-start tabu support

- Added optional `initial` assignment to `run_qap_tabu`.
- Added validation and replay tests for explicit starts.
- Enables multi-start / population-generated QAP portfolios.
