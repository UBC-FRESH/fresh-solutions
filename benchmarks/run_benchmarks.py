#!/usr/bin/env python3
"""Run replayable Fresh Solutions benchmarks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fresh_solutions import GraphColouring, PopulationConfig, SearchConfig  # noqa: E402
from fresh_solutions.adapters import QuadraticAssignment, TravellingSalesman  # noqa: E402
from fresh_solutions.benchmark import run_benchmark, save_records  # noqa: E402

ROOT = Path(__file__).resolve().parent


def main() -> int:
    """Run the three benchmark families and write evidence."""
    population = PopulationConfig(population=6, generations=5, seed=3)
    local = SearchConfig(iterations=5, seed=3)
    records = [
        run_benchmark(
            GraphColouring(3, ((0, 1), (1, 2), (2, 0))),
            "triangle",
            population,
            local,
            {"family": "graph-colouring"},
        ),
        run_benchmark(
            QuadraticAssignment.from_qaplib(ROOT / "instances" / "tiny.dat"),
            "tiny-qap",
            population,
            local,
            {"family": "qap"},
        ),
        run_benchmark(
            TravellingSalesman.from_tsplib(ROOT / "instances" / "tiny.tsp"),
            "tiny-tsp",
            population,
            local,
            {"family": "tsp"},
        ),
    ]
    save_records(records, ROOT / "evidence.json")
    print(f"wrote {len(records)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
