# Benchmark harness

The harness runs the same hybrid engine on three non-forestry families:

- graph colouring (toy triangle);
- quadratic assignment (QAPLIB-format parser);
- travelling salesman (TSPLIB EUC_2D parser).

Run:

```bash
python benchmarks/run_benchmarks.py
```

Output: `benchmarks/evidence.json`

Each record carries the adapter, instance, population/local settings, assignment, objective, feasibility,
evaluations, and history. `BenchmarkRecord.verify` replays the assignment through the adapter.
