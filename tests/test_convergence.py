"""Tests for the convergence-controlled benchmark protocol."""

from __future__ import annotations

import pytest
from fresh_solutions import (
    ConvergenceConfig,
    GraphColouring,
    PopulationConfig,
    SearchConfig,
    run_to_convergence,
)


def _graph() -> GraphColouring:
    """Return a triangle with three colours."""
    return GraphColouring(3, ((0, 1), (1, 2), (2, 0)))


def test_convergence_config_rejects_invalid_values() -> None:
    """Invalid stopping rules fail before a run starts."""
    with pytest.raises(ValueError, match="local_iterations"):
        ConvergenceConfig(local_iterations_per_round=0)
    with pytest.raises(ValueError, match="patience"):
        ConvergenceConfig(patience_rounds=0)
    with pytest.raises(ValueError, match="improvement"):
        ConvergenceConfig(min_relative_improvement=-1.0)
    with pytest.raises(ValueError, match="max_rounds"):
        ConvergenceConfig(max_rounds=0)
    with pytest.raises(ValueError, match="max_evaluations"):
        ConvergenceConfig(max_evaluations=0)


def test_convergence_result_records_patience_stop() -> None:
    """A converged toy run reports a patience stop and history."""
    result = run_to_convergence(
        _graph(),
        PopulationConfig(population=4, generations=2, seed=1),
        SearchConfig(iterations=10, seed=1),
        ConvergenceConfig(local_iterations_per_round=10, patience_rounds=1, max_rounds=10),
    )
    assert result.converged
    assert result.stop_reason == "patience"
    assert result.rounds >= 1
    assert result.feasible
    assert result.to_dict()["stop_reason"] == "patience"


def test_convergence_stops_on_evaluation_budget() -> None:
    """An evaluation budget stops the run without claiming convergence."""
    result = run_to_convergence(
        _graph(),
        PopulationConfig(population=4, generations=2, seed=1),
        SearchConfig(iterations=10, seed=1),
        ConvergenceConfig(local_iterations_per_round=10, max_evaluations=1),
    )
    assert not result.converged
    assert result.stop_reason == "max_evaluations"


def test_convergence_stops_on_round_budget() -> None:
    """A round budget is reported as a non-convergence stop."""
    result = run_to_convergence(
        _graph(),
        PopulationConfig(population=4, generations=0, seed=1),
        SearchConfig(iterations=10, seed=1),
        ConvergenceConfig(
            local_iterations_per_round=1,
            patience_rounds=100,
            max_rounds=1,
            max_evaluations=10**9,
        ),
    )
    assert result.stop_reason == "max_rounds"
    assert not result.converged
