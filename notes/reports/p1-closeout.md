# P1 close-out: problem-adapter contract

Status: complete
Date: 2026-11-01
Issue: #2

## Result

Fresh Solutions now has an executable problem-adapter contract and a WS4-free toy adapter.

Implemented:

- `fresh_solutions/contracts.py`
  - `Evaluation`
  - `Change`
  - `EvidenceRecord`
  - runtime-checkable `ProblemAdapter`
- `fresh_solutions/toy.py`
  - graph-colouring adapter
  - exact and batched evaluation
  - reversible move/apply/undo
- `tests/test_contracts.py`
  - options and initial assignment
  - conflict objective
  - batch/exact agreement
  - apply/undo round trip
  - replay and mismatch failures
- `docs/api/contracts.rst`
- `pyproject.toml` package metadata and coverage scope

## Verification

- `pytest`: 144 passed, 100% branch coverage.
- `ruff`: pass.
- `mypy --strict`: pass.
- Sphinx HTML with `-W`: pass.
- Workflow validator: 0 errors.

## Acceptance criteria

- A toy problem runs end to end without importing WS4. **Met.**
- The adapter contract names exact and batched evaluation. **Met.**
- The replay contract records instance, adapter, assignment, objective, feasibility, seed, and metadata. **Met.**

## Limits

This phase defines contracts and a toy. It does not extract the WS4 engine or implement the hybrid
CPU/GPU scheduler. Those remain P2/P3.

## Recommendation

Close P1. Activate P2 engine extraction only after the maintainer approves the P2 parent issue.
