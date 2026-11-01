# P8.3 close-out: competitive neighborhood release

Status: complete
Date: 2026-11-01
Issue: #22
Release: `v0.4.0`

## Recommendation

Approve the P8 phase merge and tag `v0.4.0`.

## Objectives and acceptance

- Competitive QAP neighborhood: **met** (robust tabu, five-seed means 0.000–0.792%).
- TSP 3-opt/LK evaluation: **met with limit** (random 3-opt did not improve Or-opt; not adopted).
- Exact replay: **met**.
- No tag without approval: **met** (this report requests it).

## Workflow compliance

- Parent issue #19 and child issues #20/#21/#22/#23.
- Phase branch `feature/p8-competitive`.
- Task commits start with P8.x.
- Dashboard green on branch.
- No direct `main` commits for P8 work.
- Prior P8.1/P8.2 tasks closed with evidence.

## Gate evidence

- 178 tests pass.
- Coverage above the 95% gate.
- Ruff, strict mypy, Sphinx `-W`, workflow validator pass.
- QAP delta tests and exact-replay tests pass.

## CI evidence

Local gates were run on the evidence head; remote CI is checked after the PR opens. A failed remote run
is a stop condition and will be reported before merge.

## Deviations

None for P8.3 beyond the negative 3-opt result, which is disclosed and not adopted.

## Next phase

P8.4 progression report is complete. P8 can close. Competitive benchmark campaign remains P10.
