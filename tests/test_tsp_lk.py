"""Tests for the Lin-Kernighan TSP neighborhoods."""

from __future__ import annotations

import pytest
from fresh_solutions.adapters import TravellingSalesman
from fresh_solutions.adapters.tsp_lk import (
    TspLkConfig,
    _double_bridge,
    _tour_edges,
    run_tsp_lk,
)


def _line_problem() -> TravellingSalesman:
    """Return a deliberately awkward six-city line tour."""
    points = ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (10.0, 0.0), (11.0, 0.0))
    distances = [[abs(first[0] - second[0]) for second in points] for first in points]
    return TravellingSalesman(distances)


def _bad_initial() -> dict[int, int]:
    """Return a non-optimal permutation for the line fixture."""
    return {0: 0, 1: 3, 2: 5, 3: 1, 4: 4, 5: 2}


def test_lk_improves_and_replays_exactly() -> None:
    """LK returns a valid tour whose recorded objective is exact."""
    problem = _line_problem()
    result = run_tsp_lk(problem, TspLkConfig(kicks=3, seed=2), _bad_initial())
    assert result.objective < result.initial_objective
    assert result.improvements >= 1
    assert result.kicks == 3
    assert problem.evaluate(result.assignment).objective == pytest.approx(result.objective)
    assert sorted(result.assignment.values()) == list(range(problem.variable_count))
    assert result.to_dict()["objective"] == result.objective


def test_lk_does_not_mutate_the_initial_tour() -> None:
    """The caller's mapping is not changed in place."""
    problem = _line_problem()
    initial = _bad_initial()
    before = initial.copy()
    run_tsp_lk(problem, TspLkConfig(kicks=1, seed=1), initial)
    assert initial == before


def test_lk_is_deterministic_for_a_seed() -> None:
    """Identical configurations and seeds produce identical tours."""
    problem = _line_problem()
    config = TspLkConfig(kicks=5, seed=11)
    first = run_tsp_lk(problem, config, _bad_initial())
    second = run_tsp_lk(problem, config, _bad_initial())
    assert first.assignment == second.assignment
    assert first.objective == second.objective


def test_lk_without_kicks_stops_after_the_initial_search() -> None:
    """Zero kicks reports the completed initial search."""
    problem = _line_problem()
    result = run_tsp_lk(problem, TspLkConfig(kicks=0, seed=1), _bad_initial())
    assert result.kicks == 0
    assert result.accepted_kicks == 0
    assert result.stop_reason == "max_kicks"
    assert len(result.history) >= 2


def test_lk_wall_clock_stop() -> None:
    """A tiny wall-clock budget stops the search and is reported."""
    problem = _line_problem()
    result = run_tsp_lk(
        problem,
        TspLkConfig(kicks=100, max_seconds=1e-9),
        _bad_initial(),
    )
    assert result.stop_reason == "max_seconds"


def test_lk_configuration_validation() -> None:
    """Invalid configuration values fail before search starts."""
    with pytest.raises(ValueError, match="candidate_count"):
        TspLkConfig(candidate_count=0)
    with pytest.raises(ValueError, match="max_depth"):
        TspLkConfig(max_depth=0)
    with pytest.raises(ValueError, match="kicks"):
        TspLkConfig(kicks=-1)
    with pytest.raises(ValueError, match="max_passes"):
        TspLkConfig(max_passes=0)
    with pytest.raises(ValueError, match="max_seconds"):
        TspLkConfig(max_seconds=0.0)


def test_double_bridge_preserves_the_permutation() -> None:
    """A double-bridge perturbation keeps every city exactly once."""
    import random

    tour = list(range(12))
    kicked = _double_bridge(tour, random.Random(3))
    assert sorted(kicked) == tour
    assert _tour_edges(kicked) == _tour_edges(tour) or kicked != tour


def test_lk_handles_small_instances() -> None:
    """A three-city instance returns a valid tour without exchange branches."""
    problem = TravellingSalesman([[0.0, 1.0, 2.0], [1.0, 0.0, 3.0], [2.0, 3.0, 0.0]])
    result = run_tsp_lk(problem, TspLkConfig(kicks=2, seed=1))
    assert sorted(result.assignment.values()) == [0, 1, 2]
    assert problem.evaluate(result.assignment).objective == pytest.approx(result.objective)
