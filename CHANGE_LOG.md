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
