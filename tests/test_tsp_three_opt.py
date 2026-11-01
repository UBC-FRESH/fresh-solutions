"""Tests for the experimental TSP 3-opt evaluation."""

from __future__ import annotations

import pytest
from fresh_solutions.adapters import TravellingSalesman
from fresh_solutions.adapters.tsp_three_opt import TspThreeOptConfig, run_tsp_three_opt


def test_three_opt_returns_an_exact_tour() -> None:
    """The experimental 3-opt result replays through the TSP adapter."""
    problem = TravellingSalesman([[0, 1, 3, 4], [1, 0, 2, 3], [3, 2, 0, 1], [4, 3, 1, 0]])
    result = run_tsp_three_opt(problem, TspThreeOptConfig(iterations=10, seed=2))
    assert problem.evaluate(result.assignment).objective == pytest.approx(result.objective)
    assert result.evaluations > 0
    assert result.to_dict()["objective"] == result.objective


def test_three_opt_config_and_time_stop() -> None:
    """Invalid settings fail and the wall-clock stop is reported."""
    with pytest.raises(ValueError, match="iterations"):
        TspThreeOptConfig(iterations=0)
    with pytest.raises(ValueError, match="max_seconds"):
        TspThreeOptConfig(max_seconds=0.0)
    problem = TravellingSalesman([[0, 1, 3, 4], [1, 0, 2, 3], [3, 2, 0, 1], [4, 3, 1, 0]])
    result = run_tsp_three_opt(problem, TspThreeOptConfig(iterations=100000, max_seconds=1e-9))
    assert result.stop_reason == "max_seconds"
