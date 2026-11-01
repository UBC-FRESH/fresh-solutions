"""Tests for batched population search, hybrid handoff, and checkpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fresh_solutions import (
    BatchBackend,
    CpuBatchBackend,
    GraphColouring,
    PopulationConfig,
    SearchCheckpoint,
    SearchConfig,
    run_hybrid_search,
    run_population_search,
)


def _graph() -> GraphColouring:
    """Return a triangle with three colours."""
    return GraphColouring(3, ((0, 1), (1, 2), (2, 0)))


def test_population_config_rejects_invalid_values() -> None:
    """Invalid population settings fail before a run starts."""
    with pytest.raises(ValueError, match="population"):
        PopulationConfig(population=1)
    with pytest.raises(ValueError, match="generations"):
        PopulationConfig(generations=-1)
    with pytest.raises(ValueError, match="mutation"):
        PopulationConfig(mutation_rate=1.1)
    with pytest.raises(ValueError, match="elite"):
        PopulationConfig(elite_fraction=1.0)
    with pytest.raises(ValueError, match="tournament"):
        PopulationConfig(tournament_size=0)
    with pytest.raises(ValueError, match="random"):
        PopulationConfig(random_fraction=-0.1)


def test_cpu_backend_matches_adapter_batch() -> None:
    """The CPU backend is a thin exact batch adapter."""
    graph = _graph()
    assignments = [graph.initial_assignment(), {0: 0, 1: 1, 2: 2}]
    backend = CpuBatchBackend(graph)
    assert isinstance(backend, BatchBackend)
    assert backend.evaluate_batch(assignments) == graph.evaluate_batch(assignments)


def test_population_search_finds_a_feasible_colouring() -> None:
    """Population search solves the toy graph and reports its history."""
    result = run_population_search(
        _graph(),
        PopulationConfig(population=8, generations=30, seed=5),
    )
    assert result.feasible
    assert result.objective == 0.0
    assert result.generations == 30
    assert len(result.history) == 31
    assert result.evaluations == 8 * 31
    assert "generations" in result.to_dict()


def test_population_search_zero_generations_evaluates_once() -> None:
    """Zero generations is a single exact initial-population evaluation."""
    result = run_population_search(
        _graph(),
        PopulationConfig(population=4, generations=0, seed=1),
    )
    assert result.evaluations == 4
    assert len(result.history) == 1


def test_hybrid_search_runs_population_then_local() -> None:
    """Hybrid search reports both phases and an exact final assignment."""
    result = run_hybrid_search(
        _graph(),
        PopulationConfig(population=6, generations=5, seed=2),
        SearchConfig(iterations=20, seed=2),
    )
    assert result.population_generations == 5
    assert result.local_iterations == 20
    assert result.evaluations > 0
    assert result.feasible
    assert "population_generations" in result.to_dict()


def test_checkpoint_round_trip_and_replay(tmp_path: Path) -> None:
    """A checkpoint saves, loads, and replays exactly."""
    graph = _graph()
    assignment = {0: 0, 1: 1, 2: 2}
    checkpoint = SearchCheckpoint(
        assignment=assignment,
        seed=7,
        generation=3,
        objective=0.0,
        metadata={"adapter": graph.name},
    )
    path = checkpoint.save(tmp_path / "checkpoint.json")
    loaded = SearchCheckpoint.load(path)
    assert loaded == checkpoint
    assert loaded.verify(graph).feasible
    assert loaded.to_dict()["assignment"] == {"0": 0, "1": 1, "2": 2}


def test_checkpoint_rejects_a_nonmatching_objective() -> None:
    """A checkpoint whose objective does not replay is rejected."""
    checkpoint = SearchCheckpoint({0: 0, 1: 0, 2: 0}, 1, 0, 0.0)
    with pytest.raises(ValueError, match="replay"):
        checkpoint.verify(_graph())
