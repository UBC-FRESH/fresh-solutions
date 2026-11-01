# P5 close-out: release and reproducibility

Status: complete
Date: 2026-11-01
Issue: #13
Release: `v0.1.0`

## Result

Fresh Solutions v0.1.0 is ready for public release.

Included:

- adapter/replay contracts
- exact CPU search and resident state
- backend-neutral batched population search
- exact hybrid handoff
- checkpoint replay
- graph-colouring, QAP, TSP adapters
- QAPLIB/TSPLIB parsers
- benchmark harness and evidence
- Apache-2.0 license, citation, and code of conduct

## Clean-checkout verification

- 167 tests passed.
- Coverage 97.24%, above the 95% gate.
- Sphinx `-W` passed.
- Workflow validator: 0 errors / 0 warnings.
- Benchmarks regenerated: triangle 0.0, tiny QAP 29.0, tiny TSP 4.0; all feasible.

Log: `notes/reports/p5-clean-checkout.log`

## Known gaps

- CPU-only exact backend; no production GPU kernel.
- Tiny parser fixtures, not full public benchmark campaigns.
- TSP uses swap moves, not 2-opt.
- No PyPI publication.

## Recommendation

Release v0.1.0 as the first public engine release.
