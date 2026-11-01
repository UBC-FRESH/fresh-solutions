# P7 close-out: convergence protocol and stronger neighborhoods

Status: complete
Date: 2026-11-01
Issue: #17
Release: v0.3.0

## Result

Fresh Solutions now has a convergence-controlled benchmark protocol and TSP Or-opt.

- `ConvergenceConfig` / `ConvergenceResult` / `run_to_convergence`.
- TSP Or-opt segment moves alongside 2-opt.
- Convergence pilot:
  - tai12a: local optimum, 7.397% gap;
  - kroA100: optimum 21,282;
  - ch150: 6.495% gap, patience stop at 191,651 evaluations.

## Verification

- 173 tests passed.
- Coverage above the 95% gate.
- Sphinx `-W` pass.
- Workflow validator: 0 errors / 0 warnings.

## Limits

The stopping rule is not a global-optimality proof. QAP tai12a is still trapped at a local optimum.
The full multi-seed convergence campaign still needs to be released as final Paper 2 evidence.
