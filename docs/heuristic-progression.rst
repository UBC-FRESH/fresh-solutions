Heuristic design progression
============================

Fresh Solutions is a framework for applying metaheuristic principles, not a claim that one generic
move set is competitive on every problem. The design record below shows how a user can add known-good
neighbourhoods through an adapter, while keeping exact replay.

The stages have different budgets and are not all controlled single-variable ablations. Report the
budget with every result.

Stage 0: generic valid moves
----------------------------

QAP uses permutation swaps; TSP uses 2-opt. A short 10,000-iteration budget produces:

* QAP mean gaps around 5–9% on QAPLIB ``tai12a``–``tai30a``;
* TSP gaps that are badly under-converged, especially on ``ch150``.

This establishes the adapter and replay contracts, not competitive quality.

Stage 1: convergence discipline and Or-opt
------------------------------------------

Applying a patience stopping rule and adding Or-opt segment relocation changes the TSP picture
materially: mean gaps fall to roughly 3.7–8.2% on the four TSPLIB instances. The QAP result does not
improve because the swap neighbourhood is still the limitation.

The TSP change combines two effects — a stronger move and removal of a premature cutoff — so it is not
a clean ablation.

Stage 2: QAP robust tabu
------------------------

An exact O(n) swap-delta, tabu memory, and aspiration produce five-seed QAP mean gaps of:

.. list-table::
   :header-rows: 1

   * - Instance
     - Mean gap
     - Worst gap
   * - ``tai12a``
     - 0.000%
     - 0.000%
   * - ``tai20a``
     - 0.403%
     - 0.470%
   * - ``tai25a``
     - 0.786%
     - 1.040%
   * - ``tai30a``
     - 0.792%
     - 1.139%

The tabu module is adapter-specific. It is not a replacement for the generic engine.

Stage 3: randomized 3-opt, negative result
------------------------------------------

Starting from the converged Or-opt incumbent, randomized 3-opt produced no improvement on
``berlin52``, ``kroA100``, or ``ch150``. The implementation is retained as an experimental evaluation
module, not adopted as the default.

How to use the framework
------------------------

1. Implement the adapter contract.
2. Add the strongest simple valid move.
3. Add exact evaluation/delta and replay tests.
4. Apply a convergence stopping rule; do not compare against a premature cutoff.
5. Add a literature-grade neighbourhood for the problem domain.
6. Compare against an independent baseline at equal budget.
7. Keep negative results and report the budget.

The framework supplies the adapter boundary, exact resident state, batch/population search, hybrid
handoff, checkpoint replay, convergence records, and benchmark evidence. It does not supply a
domain-specific neighbourhood; that is the adapter author's contribution.
