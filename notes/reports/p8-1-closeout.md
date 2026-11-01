# P8.1 close-out: QAP robust tabu

Status: complete
Date: 2026-11-01
Issue: #20

## Result

Added a QAP-specific robust tabu search with exact incremental swap deltas.

Five-seed results, 10,000 tabu iterations:

| Instance | Mean gap | Worst gap | Mean wall |
| --- | ---: | ---: | ---: |
| tai12a | 0.000% | 0.000% | 2.18 s |
| tai20a | 0.403% | 0.470% | 10.20 s |
| tai25a | 0.786% | 1.040% | 20.03 s |
| tai30a | 0.792% | 1.139% | 34.90 s |

This is a material improvement over the generic swap plateau of 5–9%.

## Verification

- Exact delta matches full QAP evaluation.
- Every result assignment replays exactly.
- 176 tests pass at 96% total coverage.
- Ruff, strict mypy, Sphinx `-W`, and workflow validator pass.

## Limits

- QAP-specific neighborhood, not a generic-engine improvement.
- 10,000 iterations is a fixed budget; no convergence claim yet.
- No release tag; P8 phase remains active.
