# P8.2 close-out: TSP 3-opt evaluation

Status: complete with limit
Date: 2026-11-01
Issue: #21

## Result

Randomized 3-opt was evaluated from the converged Or-opt incumbent on three TSPLIB instances.

| Instance | Or-opt converged | 3-opt result |
| --- | ---: | ---: |
| berlin52 | 7,815 | 7,815 |
| kroA100 | 21,282 | 21,282 |
| ch150 | 6,952 | 6,952 |

The randomized 3-opt campaign did not improve the Or-opt incumbent. The 3-opt implementation is
retained as an experimental evaluation module, not as the adopted TSP search path.

## Acceptance

- Material improvement over the 3.7–8.2% Or-opt range: **not met**.
- Exact replay: **met**.
- Negative result recorded: **met**.

## Decision

Do not adopt randomized 3-opt. The next TSP attempt should be a proper Lin–Kernighan/Or-3-opt
implementation or a stronger population/restart policy, not more random triple sampling.
