# P10.1 close-out: Lin–Kernighan neighborhood

Status: complete; phase PR queued
Date: 2026-11-01
Issue: #29
Parent: #28
Solver branch: `feature/p10-tsp-lk`
Solver commit: `0b87746`
Papers evidence commit: `2856dae`

## Recommendation

Approve the P10 phase merge. Do not create a tag yet; the close-out recommends `v0.5.0` only after
review.

## Implementation

- `fresh_solutions/adapters/tsp_lk.py`
- Candidate-list sequential edge exchange.
- Exact tour reconstruction from alternating edge sets.
- Deterministic double-bridge kicks.
- Public exports and API docs page.
- `tests/test_tsp_lk.py`.

No randomized 3-opt sampling is presented as LK.

## Evidence

Papers campaign at solver commit `0b87746`, five seeds from converged Or-opt:

| Instance | Or-opt mean gap | LK mean gap | LK worst gap |
| --- | ---: | ---: | ---: |
| berlin52 | 6.433% | 0.000% | 0.000% |
| kroA100 | 7.323% | 0.000% | 0.000% |
| kroB100 | 3.696% | 0.000% | 0.000% |
| ch150 | 8.229% | 0.383% | 0.475% |

- 20/20 exact replays.
- Three instances reach the known optimum on every seed.
- `ch150` best seed 0.230%, worst 0.475%.

## Gate evidence

- Fresh Solutions dashboard: **GREEN**.
- 186 tests pass; 95.21% coverage (95% gate).
- Ruff, format, strict mypy, Sphinx `-W`, and workflow validator pass.
- Papers: 154 tests pass; 99.53% coverage; 20/20 LK replays.

## Limits

- The comparison is quality-at-additional-cost, not equal-budget.
- No independent TSP solver baseline.
- Four TSPLIB instances only; no TSPLIB-wide campaign.
- No state-of-the-art claim.
- No tag or release in this phase.

## Next

1. CI and maintainer review of the P10 PR.
2. Decide whether to tag `v0.5.0`.
3. Keep Paper 2 internal until the remaining evidence gates pass.
