"""Tests for QAP robust tabu search."""

from __future__ import annotations

import pytest
from fresh_solutions.adapters import QuadraticAssignment
from fresh_solutions.adapters.qap_tabu import QapTabuConfig, _swap_delta, run_qap_tabu


def _problem() -> QuadraticAssignment:
    """Return a tiny asymmetric QAP."""
    return QuadraticAssignment([[0, 2, 3], [3, 0, 4], [5, 6, 0]], [[0, 5, 7], [7, 0, 2], [3, 4, 0]])


def test_swap_delta_matches_full_evaluation() -> None:
    """The incremental QAP delta matches the exact evaluator."""
    problem = _problem()
    assignment = [0, 1, 2]
    base = problem.evaluate(dict(enumerate(assignment))).objective
    for first in range(3):
        for second in range(first + 1, 3):
            moved = assignment[:]
            moved[first], moved[second] = moved[second], moved[first]
            exact = problem.evaluate(dict(enumerate(moved))).objective
            assert base + _swap_delta(problem, assignment, first, second) == pytest.approx(exact)


def test_qap_tabu_improves_and_replays_exactly() -> None:
    """Tabu search improves the tiny QAP and returns an exact assignment."""
    problem = _problem()
    result = run_qap_tabu(problem, QapTabuConfig(iterations=100, seed=2))
    assert result.objective <= problem.evaluate(problem.initial_assignment()).objective
    assert result.evaluations > 1
    assert result.stop_reason == "max_iterations"
    assert problem.evaluate(result.assignment).objective == pytest.approx(result.objective)
    assert result.to_dict()["objective"] == result.objective


def test_qap_tabu_config_validation_and_time_stop() -> None:
    """Invalid settings fail and a wall-clock budget stops the search."""
    with pytest.raises(ValueError, match="iterations"):
        QapTabuConfig(iterations=0)
    with pytest.raises(ValueError, match="min_tenure"):
        QapTabuConfig(min_tenure=0)
    with pytest.raises(ValueError, match="max_tenure"):
        QapTabuConfig(max_tenure=0)
    with pytest.raises(ValueError, match="min_tenure"):
        QapTabuConfig(min_tenure=5, max_tenure=2)
    with pytest.raises(ValueError, match="max_seconds"):
        QapTabuConfig(max_seconds=0.0)
    result = run_qap_tabu(_problem(), QapTabuConfig(iterations=100000, max_seconds=1e-9))
    assert result.stop_reason == "max_seconds"
