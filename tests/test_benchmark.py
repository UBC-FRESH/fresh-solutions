"""Tests for replayable benchmark records."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from fresh_solutions import GraphColouring, PopulationConfig, SearchConfig
from fresh_solutions.benchmark import (
    BenchmarkRecord,
    run_benchmark,
    save_records,
)


def _record() -> BenchmarkRecord:
    graph = GraphColouring(3, ((0, 1), (1, 2), (2, 0)))
    return run_benchmark(
        graph,
        "triangle",
        PopulationConfig(population=4, generations=2, seed=2),
        SearchConfig(iterations=2, seed=2),
        {"family": "graph-colouring"},
    )


def test_benchmark_record_replays_exactly() -> None:
    """A recorded assignment replays through its adapter."""
    record = _record()
    graph = GraphColouring(3, ((0, 1), (1, 2), (2, 0)))
    evaluation = record.verify(graph)
    assert evaluation.objective == record.result.objective
    assert record.to_dict()["adapter"] == graph.name
    assert record.to_dict()["metadata"] == {"family": "graph-colouring"}


def test_benchmark_record_rejects_mismatch() -> None:
    """Wrong adapter names and objectives are rejected."""
    record = _record()
    with pytest.raises(ValueError, match="adapter"):
        replace(record, adapter="other").verify(GraphColouring(3, ((0, 1), (1, 2), (2, 0))))
    bad = BenchmarkRecord(
        instance=record.instance,
        adapter=record.adapter,
        population=record.population,
        local=record.local,
        result=record.result.__class__(
            assignment=record.result.assignment,
            objective=999.0,
            feasible=record.result.feasible,
            evaluations=record.result.evaluations,
            population_generations=record.result.population_generations,
            local_iterations=record.result.local_iterations,
        ),
    )
    with pytest.raises(ValueError, match="replay"):
        bad.verify(GraphColouring(3, ((0, 1), (1, 2), (2, 0))))


def test_save_and_load_records(tmp_path: Path) -> None:
    """Records save as a JSON list and load back."""
    path = save_records([_record()], tmp_path / "evidence.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload[0]["instance"] == "triangle"
    assert payload[0]["adapter"] == "graph-colouring-v1"
