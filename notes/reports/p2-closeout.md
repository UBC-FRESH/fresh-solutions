# P2 close-out: engine extraction

Status: complete
Date: 2026-11-01
Issue: #7

## Result

Fresh Solutions now has a WS4-free exact CPU engine and a resident-assignment state.

Implemented:

- `fresh_solutions/engine.py`
  - `SearchConfig`
  - `SearchResult`
  - `ResidentState` protocol
  - `ResidentAssignment`
  - `run_local_search`
- Graph-colouring end-to-end run through the engine.
- Deterministic seed tests, apply/undo tests, no-move adapter test, and a no-WS4 dependency test.
- API docs for the engine.

## Verification

- 150 tests passed.
- 100% branch coverage.
- Ruff and strict mypy pass.
- Sphinx `-W` pass.
- Workflow validator: 0 errors.
- Engine package contains no WS4 import or textual dependency.

## Acceptance criteria

- At least one non-forestry problem runs end to end. **Met** (triangle graph colouring).
- The engine has no WS4 import in its core package. **Met.**

## Limits

This is an exact CPU engine. GPU scheduling, population evaluation, checkpointing, and external benchmark
adapters are P3/P4.

## Recommendation

Close P2. P3 CPU/GPU search scheduling remains planned.
