# P9.1 close-out: certified QAP budget docs

Status: complete
Date: 2026-11-01
Issue: #26

## Recommendation

Approve the docs-only P9.1 change. No release tag is required.

## Changes

- `notes/reports/heuristic-progression.md` now distinguishes the first 10k tabu stage from the certified
  budget table.
- `docs/heuristic-progression.rst` carries the certified table and the independent SciPy FAQ baseline.
- Outdated "10k fixed" language is removed.
- TSP remains explicitly Or-opt-only.

## Gates

- Sphinx `-W`: pass.
- pytest: pass.
- `scripts/check_workflow.py`: pass.
- No code, version, tag, or release change.

## Limits

- The certification rule checks one doubling; it is not an asymptotic convergence proof.
- SciPy FAQ is not budget-matched.
