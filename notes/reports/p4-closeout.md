# P4 close-out: benchmark adapters and evidence

Status: complete
Date: 2026-11-01
Issue: #11

## Result

Fresh Solutions now runs three non-forestry benchmark families through the same hybrid engine.

Implemented:

- `fresh_solutions/adapters/qap.py` — QAP adapter and QAPLIB parser.
- `fresh_solutions/adapters/tsp.py` — symmetric TSP adapter and TSPLIB EUC_2D parser.
- `fresh_solutions/adapters/_permutation.py` — permutation swaps and order crossover.
- `fresh_solutions/benchmark.py` — replayable benchmark records.
- `benchmarks/run_benchmarks.py` — harness for graph colouring, QAP, and TSP.
- `benchmarks/evidence.json` — generated evidence.
- API docs and parser/adaptor tests.

## Verification

- 167 tests passed.
- 97% total coverage, above the 95% gate.
- Ruff and strict mypy pass.
- Sphinx `-W` pass.
- Workflow validator: 0 errors.
- QAP, TSP, and graph colouring all replay through `BenchmarkRecord.verify`.

## Evidence

`benchmarks/evidence.json` contains three records:

- triangle graph colouring: objective 0.0, feasible;
- tiny QAP: objective 29.0, feasible;
- tiny TSP: tour objective, feasible.

These are toy/public-format transfer records, not claims about public benchmark leadership.

## Limits

- Instances are tiny parser fixtures, not full QAPLIB/TSPLIB benchmark campaigns.
- The TSP adapter uses swaps, not 2-opt; this is a contract/transfer test.
- No production GPU backend; `CpuBatchBackend` is the current exact backend.

## Recommendation

Close P4. P5 release and reproducibility remains planned.
