# Shared-kernel retrofit — closeout

Status: **complete**
Date: 2026-11-04
Scope: `fresh-solutions`, `ws4`, `fhops`, `fresh-solutions-papers`

## Outcome

`fresh-solutions` is the released search kernel for the FRESH ecosystem. WS4 and FHOPS consume
it; the papers project is pinned to the released version.

The retrofit deliberately keeps domain logic in the consuming packages:

- `fresh-solutions` owns the generic `Problem[State, Context]`, operator protocol and weighted
  registry, SA / delta-SA / Tabu / ILS / threshold, cooling, control, stopping rules, telemetry,
  and the `Runner` protocol.
- WS4 owns its compiled dataset, `Optimizer`, goal-programming objective, incremental accounting,
  constraints, patch/spatial/route/carbon models, MIP layer, seeding, and reporting.
- FHOPS owns its machine-by-slot `Schedule`, repair/sanitizer, sequencing, landing/mobilisation
  rules, objective weights, MIP hybrid, telemetry, and tuning.

## Release

- PyPI: `fresh-solutions 0.9.3` — <https://pypi.org/project/fresh-solutions/0.9.3/>
- GitHub release: <https://github.com/UBC-FRESH/fresh-solutions/releases/tag/v0.9.3>
- Tag `v0.9.3` at `3aa241e`.
- Trusted-publisher workflow `.github/workflows/publish.yml` publishes on `v*` tags through the
  `pypi` environment.
- Clean venv install from PyPI verified; wheel and sdist pass `twine check`.

## Merged changes

| Repository | Change | Merge commit |
| --- | --- | --- |
| `fresh-solutions` | PR #43, shared search kernel and 0.9.3 release | `907f8e1` |
| `ws4` | PR #797, consume the shared kernel | `e2b240a` |
| `ws4` | PR #808, close the scripts coverage gate | `de28612` |
| `fhops` | PR #394, shared-kernel adapter | `63ebfbd` |
| `fhops` | PR #404, reversible block-separable scoring | `300d5e3` |
| `fhops` | PR #406, objective-weight parity | `a008df3` |
| `fhops` | PR #409, base parity ladder | `33b0111` |
| `fhops` | PR #410, scaling parity ladder | `44fc677` |
| `fhops` | PR #413, like-for-like kernel ILS | `bdeb3fb` |
| `fhops` | PR #414, multi-seed ILS ladder | `9724d33` |
| `fhops` | PR #417, Jaffray case-study ladder | `7e81568` |
| `fresh-solutions-papers` | PR #77, pin v0.9.3 and replay evidence | `04e533c` |

## Evidence

### WS4

- Full suite: 1,589 tests at the coverage fix.
- Strict mypy, ruff, format, Sphinx `-W`, and workflow validator pass.
- Script coverage gate: **90.14%** (was 89.69% on `22471cb`).
- Main's SDMD guard, LNS `max_destroy`, and delta-SA best-move journal preserved; the journal was
  ported into the kernel.

### Papers

- Submodule pinned from `v0.8.0` to `v0.9.3`.
- Evidence replayed under `v0.9.3`: **40 QAP + 20 TSP incumbents, 60/60 exact**; 1,085 broad
  records and 7 summary rows validated.
- Provenance records both the campaign commit (`7d3c831`, v0.8.0) and replay commit
  (`3aa241e`, v0.9.3).

### FHOPS

Block-separable incremental scoring:

- Tiny7, 200 iterations: full 0.157 s, incremental 0.108 s, identical objective `-2673.433`.
- med42, 100 iterations: full 0.515 s, incremental 0.355 s, identical `20543.16`.

Jaffray case studies (`UBC-FRESH/jaffray-masc-fhops-model` at `d726ace2`,
`data/input/scenarios/{ka,ni,pg}_{6,18,40}`; manuscript
`UBC-FRESH/fhops-cjfr-rolling-horizon` at `4c800450`):

- 6-block, 50 iterations: kernel SA/Tabu/ILS-like agree on `ka_6` and `pg_6`; `ni_6` kernel is
  1,316–2,654 better.
- 18-block, 20 iterations: mostly equal; `ni_18` SA +1,316, Tabu −1,316, ILS-like +95.868.
- 40-block, 50 iterations, SA/Tabu only: `ka_40` kernel −1,316; `ni_40` SA −47,376 and Tabu
  +4,263; `pg_40` kernel SA/Tabu +111k to +154k.
- The 40-block results are high-variance at these budgets and need multi-seed, longer runs before
  any retirement decision.

Raw FHOPS records live in `notes/reference/kernel-parity-*.json` in the FHOPS repository.

## Decisions

1. **Keep the existing FHOPS SA/Tabu/ILS loops.** The kernel paths are competitive and often
   faster, but not uniformly better and not trajectory-identical.
2. **Keep the kernel ILS and ILS-like as supported experimental paths**, not defaults.
3. **Defer true in-place move/undo.** Block-separable scoring was the dominant win; the remaining
   candidate copy is operator-level. Revisit only if a profile shows allocation is material.
4. **No further kernel plumbing** unless a consuming package has a concrete need.

## Open items

None required for the retrofit.

Optional future work:

- multi-seed, longer-budget Jaffray 40-block comparison (SA/Tabu only);
- true in-place FHOPS move/undo if profiling justifies it;
- unify FHOPS telemetry/tuning with the kernel `Runner` contract;
- retire duplicate FHOPS solver loops only after a uniform multi-scenario win.

## Verification commands

```bash
# fresh-solutions
cd fresh-solutions && python scripts/dashboard.py

# WS4
cd ws4 && python -m pytest -q

# FHOPS
cd fhops && pytest
```

PyPI: `python -m pip install fresh-solutions==0.9.3`

## Correction

The Jaffray scenarios are not missing. They are in
`UBC-FRESH/jaffray-masc-fhops-model`. The earlier statement that they were unavailable was wrong;
the closeout and ladder use the actual case-study bundles.
