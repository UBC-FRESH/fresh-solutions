# Heuristic progression: from generic moves to literature-grade design

Status: P8.4 evidence report
Date: 2026-11-01
Scope: Fresh Solutions v0.1.0 through v0.4.0
Related evidence:
`fresh-solutions-papers/paper2/evidence/converged-summary.json`,
`fresh-solutions-papers/paper2/evidence/qap-tabu-summary.json`,
`fresh-solutions-papers/paper2/evidence/qap-tabu-converged-summary.json`,
`fresh-solutions-papers/paper2/evidence/qap-scipy-faq-summary.json`

## Purpose

This report records the design progression, not a single leaderboard result. The point is to show how
Fresh Solutions lets a user add known-good metaheuristic principles through an adapter without
re-architecting the solver, and to state honestly what each layer did and did not prove.

Every stage below names its budget. The stages are not all equal-budget controlled comparisons.

## Stage 0 — generic moves, short budget

Baseline: permutation-preserving swaps for QAP, 2-opt for TSP, 10,000 local iterations, five seeds.

| Instance | Mean gap | Notes |
| --- | ---: | --- |
| tai12a | 8.897% | QAP swap plateau |
| tai20a | 7.185% | QAP swap plateau |
| tai25a | 5.249% | QAP swap plateau |
| tai30a | 5.679% | QAP swap plateau |
| berlin52 | 10.196% | TSP 2-opt |
| kroA100 | 21.490% | TSP 2-opt |
| kroB100 | 17.108% | TSP 2-opt |
| ch150 | 56.259% | badly under-converged |

Principle applied: valid permutation moves and exact evaluation. This proves the adapter and replay
contracts, not competitive quality.

## Stage 1 — convergence discipline + Or-opt

Changes:

- patience stopping rule (`ConvergenceConfig`);
- Or-opt segment relocation for TSP;
- ten-thousand-iteration rounds until the plateau rule.

Observed:

| Instance | Mean gap | Change from Stage 0 |
| --- | ---: | --- |
| tai12a–tai30a | 5.249–8.897% | unchanged; QAP still swap-limited |
| berlin52 | 6.433% | 10.196% → 6.433% |
| kroA100 | 7.323% | 21.490% → 7.323% |
| kroB100 | 3.696% | 17.108% → 3.696% |
| ch150 | 8.229% | 56.259% → 8.229% |

Principle: **do not compare an unconverged run to a converged one**. The huge TSP improvement is partly
the Or-opt neighborhood and partly the elimination of a premature 10k cutoff. The report must say that.

## Stage 2 — QAP robust tabu and budget certification

Changes:

- exact O(n) swap-delta evaluation;
- robust tabu memory and aspiration;
- ten-thousand-iteration QAP-specific neighborhood.

Observed, five seeds:

| Instance | Mean gap | Worst gap |
| --- | ---: | ---: |
| tai12a | 0.000% | 0.000% |
| tai20a | 0.403% | 0.470% |
| tai25a | 0.786% | 1.040% |
| tai30a | 0.792% | 1.139% |

Principle: **a domain-specific neighborhood plus tabu memory is qualitatively better than more random
swaps**. This is the strongest result in the progression. It is QAP-adapter-specific, not a generic
engine replacement.

### Certified budget update

The 10k table is the first effective tabu stage, not a converged final budget. The papers campaign uses
a doubling check: a budget is certified when the next doubling improves the five-seed mean by no more
than 0.10 percentage points, or every seed reaches the known optimum.

| Instance | Certified budget | Mean gap | Worst gap | Next doubling |
| --- | ---: | ---: | ---: | ---: |
| tai12a | 10,000 | 0.000% | 0.000% | optimum on all seeds |
| tai20a | 10,000 | 0.403% | 0.470% | 20k: 0.370% |
| tai25a | 20,000 | 0.685% | 0.850% | 40k: 0.592% |
| tai30a | 40,000 | 0.407% | 0.678% | 80k: 0.348% |

The 20k/40k/80k records are retained in the papers evidence. The larger values are not substituted into
the headline table. This is a budget-stability rule, not a convergence proof.

### Independent baseline

SciPy `quadratic_assignment` (`faq`, `maxiter=10000`, SciPy 1.18.1), five seeds, is an independent
implementation. It is much faster and much worse than the certified tabu table:

| Instance | SciPy mean gap | Tabu mean gap |
| --- | ---: | ---: |
| tai12a | 9.026% | 0.000% |
| tai20a | 4.642% | 0.403% |
| tai25a | 4.474% | 0.685% |
| tai30a | 2.289% | 0.407% |

This is a time-quality comparison, not an equal-budget comparison. SciPy returned the same assignment
on all five seeds for each instance.

## Stage 3 — randomized 3-opt, negative result

Starting from the converged Or-opt incumbent, a randomized 3-opt evaluation produced no improvement:

| Instance | Or-opt | 3-opt |
| --- | ---: | ---: |
| berlin52 | 7,815 | 7,815 |
| kroA100 | 21,282 | 21,282 |
| ch150 | 6,952 | 6,952 |

Principle: **not every literature-inspired move improves a converged incumbent**. Random triple
sampling is not Lin–Kernighan. The negative result is retained; the implementation is not adopted as
the default.

## What the framework actually provides

1. **A stable adapter boundary.** A user supplies variables, options, exact/batched evaluation,
   feasibility, mutation/crossover, and reversible moves.
2. **Exact resident state and replay.** Every incumbent is serializable and replayable.
3. **A place to add known-good neighborhoods.** QAP tabu and TSP Or-opt are separate adapter modules;
   they do not rewrite the engine.
4. **A convergence/evidence loop.** The user gets stopping rules, seed records, budgets, and replay
   without inventing a benchmark harness.
5. **Negative-result safety.** A bad neighborhood can be evaluated and rejected without contaminating
   the core package or the paper.

## How a user applies the progression

1. Implement the adapter.
2. Add the strongest simple valid move.
3. Add exact delta/evaluation and replay tests.
4. Run a convergence pilot; do not tune against an arbitrary short cutoff.
5. Add a literature-grade neighborhood for the domain.
6. Compare against a baseline at a stated budget; say whether it is equal-budget or time-quality.
7. Keep the negative result if the new move does not help.

## Limits

- Not a claim of state-of-the-art QAP/TSP performance.
- Not a global-optimality proof.
- QAP tabu is specialized; TSP still lacks Lin–Kernighan/3-opt adoption.
- The QAP certified budget uses a single-doubling rule; it is not an asymptotic convergence proof.
- The TSP figures mix Stage 0/1 changes and must not be presented as a clean single-variable ablation.
- TSP remains Or-opt-only; randomized 3-opt was negative and Lin–Kernighan is not implemented.

## Publication use

This progression can support a **framework/methods paper**:

> Fresh Solutions lets users apply known-good metaheuristic principles through adapters, with exact
> replay, convergence discipline, and a measured progression from generic moves to domain-specific
> neighborhoods.

It cannot support a leadership paper until the TSP neighbourhood and independent-baseline gaps are closed.
