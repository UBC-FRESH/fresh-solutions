# Fresh Solutions architecture

Status: planning
Date: 2026-11-01

## Purpose

Fresh Solutions is the generic solver extracted from the WS4 search architecture. It must remain useful
without forestry-specific concepts such as blocks, treatments, or forest accounts.

## Layers

```text
problem adapter
  variables + domains
  candidate/option representation
  exact evaluator
  batched evaluator
  feasibility/repair
  move operators
        |
engine
  resident state / delta accounting
  CPU local search
  GPU population search
  scheduling and hybrid handoff
  checkpoint, seed, telemetry, replay
```

## Adapter protocol

A problem adapter must expose:

- `variables`: the discrete decision objects and their option domains;
- `candidate_count` and `option_at` for compact indexing;
- `evaluate(schedule)` for exact objective/feasibility;
- `evaluate_batch(states)` for the batched path, or a documented fallback;
- `moves`/`neighbourhoods` and `undo`;
- `state_init` and `state_apply` for resident accounting;
- `replay` metadata and provenance.

The engine must not assume:

- linear or additive accounts;
- spatial adjacency;
- a fixed objective shape;
- that the batched evaluator is available.

## Hybrid handoff

The core pattern is:

1. exact CPU state is authoritative;
2. a batched GPU/population search proposes elites;
3. the CPU exact path verifies and refines selected elites;
4. the refined schedule returns to the population as a seed/immigrant;
5. every reported incumbent is replayed exactly.

This is the transferable claim of the papers programme.

## Contract tests

- A toy adapter runs CPU-only and hybrid.
- Batch and exact paths agree on the same state.
- Undo restores exact state.
- A benchmark record replays from its config and seed.
- No core module imports a problem-specific package.

## Open questions

- How much of the effect/state representation belongs in the engine versus the adapter?
- What is the minimum batched-evaluator contract?
- Can resident state be optional without losing the architecture's value?
- How are cache invalidation and provenance represented generically?

## P1 implementation status

The P1 contract is implemented in `fresh_solutions/contracts.py`:

- `Evaluation` carries objective, feasibility, and diagnostics.
- `Change` is a reversible variable/option move.
- `EvidenceRecord` serializes and replays an incumbent.
- `ProblemAdapter` is the runtime-checkable protocol.

`fresh_solutions/toy.py` implements a graph-colouring adapter with options, exact and batched
evaluation, proposal, apply, and undo. The contract tests replay an evidence record and prove that
batch and exact paths agree.
