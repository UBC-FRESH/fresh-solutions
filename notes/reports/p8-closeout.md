# P8 close-out: competitive neighborhoods

Status: complete
Date: 2026-11-01
Issue: #19
Release: `v0.4.0`

## Recommendation

Approve the P8 PR and tag `v0.4.0`.

## Objectives and acceptance

- QAP robust tabu: **met**. Five-seed means: tai12a 0.000%, tai20a 0.403%, tai25a 0.786%,
  tai30a 0.792%.
- TSP 3-opt/LK evaluation: **met with limit**. Random 3-opt did not improve converged Or-opt and was
  not adopted.
- Exact replay: **met**.
- Progression report and public guide: **met**.

## Workflow compliance

- Parent issue #19; child issues #20/#21/#22/#23.
- Phase branch `feature/p8-competitive`; task commits use P8.x prefixes.
- No direct `main` commits for P8 work.
- P8.1/P8.2/P8.4 closed; P8.3 release issue closes at merge.

## Gate evidence

- 178 tests pass in a clean clone.
- Total coverage 96.03%, above the 95% gate.
- Ruff, strict mypy, Sphinx `-W`, workflow validator pass.
- Benchmark harness regenerates all toy records.

## CI evidence

- Clean clone: `notes/reports/p8-clean-checkout.log`.
- Remote CI status is checked on the phase PR before merge.

## Deviations

The random 3-opt result is negative and was retained rather than forced into the default path.

## Next phase

P10 in the papers project carries the competitive benchmark campaign, matched baseline, applied case,
and evidence closeout.

## Decision

Approve as written: merge P8, tag v0.4.0, close #19.
