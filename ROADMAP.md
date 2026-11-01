# Fresh Solutions Roadmap

This roadmap is the plan of record and issue tracker map for Fresh Solutions. Keep it in step with the
GitHub issues, `CHANGE_LOG.md`, and `notes/`. `scripts/check_workflow.py` parses the phase headers,
status lines, and checkboxes below, so keep their format.

Every phase starts as `planned` with `Parent issue: TBD`. Activate a phase only after its parent issue
exists and the maintainer approves it.

## Issue Tracker Map

| Phase | Parent issue | Branch | Status |
| --- | --- | --- | --- |
| P0 Bootstrap | #1 | `feature/p0-bootstrap` | complete |
| P1 Problem-adapter contract | #2 | `feature/p1-adapter-contract` | complete |
| P2 Engine extraction | #7 | `feature/p2-engine-extraction` | complete |
| P3 CPU/GPU search scheduling | #9 | `feature/p3-search-scheduling` | complete |
| P4 Benchmark adapters and evidence | #11 | `feature/p4-benchmarks` | complete |
| P5 Release and reproducibility | #13 | `feature/p5-release` | complete |
| P6 Maintain and expand | #15 | `feature/p6-tsp-2opt` | complete |
| P7 Convergence protocol | #17 | `feature/p7-convergence` | complete |
| P8 Competitive neighborhoods | #19 | `feature/p8-competitive` | active |

## Lifecycle Map

| Stage | Phases | Exit criteria |
| --- | --- | --- |
| Design | P0, P1 | The adapter contract and scope are recorded |
| Build | P2, P3 | Engine and scheduling work leaves the dashboard green |
| Evidence | P4 | Every benchmark has a public instance/config/seed/schedule |
| Release | P5 | Tag, docs, and clean-checkout reproduction |
| Maintain | P6 | Review cadence and benchmark expansion |

## Conventions

- A phase is `P<n>`. A task is `P<n>.<m>`. A subtask is a checklist item in the task issue.
- Status values are `planned`, `active`, `pr-open`, `complete`, and `deferred`.
- A phase becomes `complete` only after its pull request merges to `main` and its parent issue closes.
- A benchmark claim without a replayable schedule and provenance is not a result.

## Phase 0: Bootstrap

Parent issue: #1
Branch: `feature/p0-bootstrap`
Status: complete

Goal: establish the public package identity, license, documentation, and reviewable first pull request.

- [x] P0.1 Adapt `AGENTS.md`, `README.md`, and the license to Fresh Solutions
- [x] P0.2 Confirm the validator and docs build pass

Acceptance criteria:

- The repository states the solver scope and the non-goals.
- `python scripts/check_workflow.py` reports zero errors.
- `sphinx-build -b html docs _build/html -W` passes.

## Phase 1: Problem-adapter contract

Parent issue: #2
Branch: `feature/p1-adapter-contract`
Status: complete

Goal: define the boundary between a problem and the engine before extracting code.

- [x] P1.1 Write the adapter protocol: variables, domains, candidates, objective, feasibility, moves
- [x] P1.2 Define the evidence/replay contract
- [x] P1.3 Build a WS4-free toy adapter and contract tests

Acceptance criteria:

- A toy problem can be expressed without importing WS4.
- The adapter contract names exact and batched evaluation explicitly.

## Phase 2: Engine extraction

Parent issue: #7
Branch: `feature/p2-engine-extraction`
Status: complete

Goal: extract the reusable engine from WS4 without coupling it to forestry accounts or datasets.

- [x] P2.1 Extract resident state and incremental accounting interfaces
- [x] P2.2 Extract candidate/option indexing
- [x] P2.3 Extract exact CPU local search
- [x] P2.4 Add the first non-forestry adapter

Acceptance criteria:

- At least one non-forestry problem runs end to end.
- The engine has no WS4 import in its core package.

## Phase 3: CPU/GPU search scheduling

Parent issue: #9
Branch: `feature/p3-search-scheduling`
Status: complete

Goal: support the hybrid CPU/GPU execution pattern generically.

- [x] P3.1 Define resident GPU effect/state representation
- [x] P3.2 Implement batched population evaluation
- [x] P3.3 Implement exact local refinement handoff
- [x] P3.4 Add checkpointing, seed reset, and replay

Acceptance criteria:

- The same adapter can run CPU-only and hybrid paths.
- Every elite schedule can be exactly replayed.

## Phase 4: Benchmark adapters and evidence

Parent issue: #11
Branch: `feature/p4-benchmarks`
Status: complete

Goal: prove that the architecture transfers beyond forestry.

- [x] P4.1 Add quadratic assignment and graph-colouring adapters
- [x] P4.2 Add job-shop or vehicle-routing adapter
- [x] P4.3 Add a public-library benchmark harness
- [x] P4.4 Record comparison evidence with provenance

Acceptance criteria:

- At least three non-forestry benchmark families are replayable.
- Results report time-to-quality, not only final objective.

## Phase 5: Release and reproducibility

Parent issue: #13
Branch: `feature/p5-release`
Status: complete

Goal: publish a usable package and reproducible benchmark artifact.

- [x] P5.1 Write the release notes and known-gaps list
- [x] P5.2 Tag, publish, and verify from a clean checkout
- [x] P5.3 Publish the benchmark archive

Acceptance criteria:

- A clean checkout reproduces the documented examples and benchmark evidence.

## Phase 6: Maintain and expand

Parent issue: #15
Branch: `feature/p6-tsp-2opt`
Status: complete

Goal: keep the package useful and the benchmark claims current.

- [x] P6.1 Implement TSP 2-opt
- [x] P6.2 Refresh public benchmark evidence
- [x] P6.3 Release v0.2.0 and review cadence

Acceptance criteria:

- The benchmark suite is current and reproducible.

## Phase 7: Convergence-grade benchmark protocol

Parent issue: #17
Branch: `feature/p7-convergence`
Status: complete

Goal: replace arbitrary budgets with a convergence rule and stronger TSP moves.

- [x] P7.1 Define convergence record/stop rule
- [x] P7.2 Implement TSP Or-opt
- [x] P7.3 Run convergence pilot
- [x] P7.4 Freeze the benchmark protocol

## Phase 8: Competitive neighborhoods

Parent issue: #19
Branch: `feature/p8-competitive`
Status: active

Goal: add competitive QAP/TSP neighborhoods and produce converged benchmark evidence.

- [ ] #20 P8.1 QAP robust tabu
- [ ] P8.2 TSP 3-opt/LK evaluation
- [ ] P8.3 Competitive benchmark release
