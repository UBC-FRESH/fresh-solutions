"""Tests for QAP robust tabu search."""

from __future__ import annotations

import pytest
from fresh_solutions.adapters import QuadraticAssignment
from fresh_solutions.adapters.qap_tabu import (
    QapTabuConfig,
    _delta_matrix,
    _run_accelerated,
    _update_delta_matrix,
    _swap_delta,
    run_qap_tabu,
)


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
    with pytest.raises(ValueError, match="patience"):
        QapTabuConfig(patience=0)
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
    with pytest.raises(ValueError, match="permutation"):
        run_qap_tabu(_problem(), QapTabuConfig(iterations=10), {0: 0, 1: 0, 2: 2})


def test_qap_tabu_starts_from_an_optional_assignment() -> None:
    """An explicit start is honored and still replays exactly."""
    problem = _problem()
    initial = {0: 2, 1: 0, 2: 1}
    result = run_qap_tabu(problem, QapTabuConfig(iterations=10, seed=1), initial)
    assert problem.evaluate(initial).objective >= 0.0
    assert problem.evaluate(result.assignment).objective == pytest.approx(result.objective)
    assert result.to_dict()["assignment"] == {
        str(key): value for key, value in sorted(result.assignment.items())
    }


def test_qap_tabu_accelerated_matches_reference() -> None:
    """The delta-matrix path agrees with the reference scan on a symmetric fixture."""
    problem = QuadraticAssignment(
        [[0, 1, 2], [1, 0, 3], [2, 3, 0]], [[0, 2, 4], [2, 0, 1], [4, 1, 0]]
    )
    reference = run_qap_tabu(
        problem,
        QapTabuConfig(iterations=50, seed=4, accelerated=False),
    )
    accelerated = run_qap_tabu(
        problem,
        QapTabuConfig(iterations=50, seed=4, accelerated=True),
    )
    assert accelerated.objective == pytest.approx(reference.objective)
    assert accelerated.assignment == reference.assignment


def test_qap_tabu_pure_delta_matrix_path() -> None:
    """The pure delta-matrix path agrees with the reference and can time out."""
    problem = QuadraticAssignment(
        [[0, 1, 2], [1, 0, 3], [2, 3, 0]], [[0, 2, 4], [2, 0, 1], [4, 1, 0]]
    )
    reference = run_qap_tabu(problem, QapTabuConfig(iterations=50, seed=4, accelerated=False))
    accelerated = _run_accelerated(problem, QapTabuConfig(iterations=50, seed=4), [0, 1, 2])
    assert accelerated.objective == pytest.approx(reference.objective)
    timed = _run_accelerated(problem, QapTabuConfig(iterations=50, max_seconds=1e-9), [0, 1, 2])
    assert timed.stop_reason == "max_seconds"


def test_qap_tabu_delta_matrix_update() -> None:
    """The delta matrix remains consistent after a swap with unrelated pairs."""
    problem = QuadraticAssignment(
        [[0, 1, 2, 4], [1, 0, 3, 1], [2, 3, 0, 2], [4, 1, 2, 0]],
        [[0, 2, 4, 1], [2, 0, 1, 3], [4, 1, 0, 2], [1, 3, 2, 0]],
    )
    assignment = [0, 1, 2, 3]
    gains = _delta_matrix(problem, assignment)
    _update_delta_matrix(problem, assignment, gains, 0, 1)
    expected = _delta_matrix(problem, assignment)
    assert assignment == [1, 0, 2, 3]
    assert gains == expected


def test_qap_tabu_patience_stops_the_plateau() -> None:
    """The QAP plateau rule stops after a declared number of stale iterations."""
    problem = _problem()
    result = run_qap_tabu(problem, QapTabuConfig(iterations=100000, patience=1, seed=2))
    assert result.stop_reason == "patience"
    assert result.iterations == 1
