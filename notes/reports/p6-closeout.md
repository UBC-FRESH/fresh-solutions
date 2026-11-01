# P6 close-out: TSP 2-opt and maintenance release

Status: complete
Date: 2026-11-01
Issue: #15
Release: v0.2.0

## Result

The TSP adapter now supports 2-opt segment reversal. Public `berlin52` evidence improved from
17,216 to 9,033 at population 32, generations 50, local iterations 3,000, seed 3.

## Verification

- 168 tests passed.
- Coverage 97.02%, above the 95% gate.
- Ruff and strict mypy pass.
- Sphinx `-W` pass.
- Workflow validator: 0 errors / 0 warnings.
- Clean-checkout log: `notes/reports/p6-clean-checkout.log`.

## Release

Tag `v0.2.0`; maintenance release metadata and release notes updated.

## Limits

- TSP 2-opt is much better but the public evidence is still a small, untuned pass.
- QAP/TSP results are not leadership claims.
- CPU-only backend remains.
