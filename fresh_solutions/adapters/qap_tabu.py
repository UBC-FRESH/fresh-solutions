"""Robust tabu search for the quadratic assignment adapter."""

from __future__ import annotations

import random
import time
from collections.abc import Mapping
from dataclasses import dataclass, field

from .qap import QuadraticAssignment


@dataclass(frozen=True)
class QapTabuConfig:
    """Configuration for QAP robust tabu search.

    Parameters
    ----------
    iterations : int, optional
        Maximum tabu iterations. Defaults to 20,000.
    patience : int or None, optional
        Stop after this many iterations without a new best objective. ``None``
        disables the plateau rule and runs the full iteration budget.
    seed : int, optional
        Random seed for tabu tenures. Defaults to 1.
    min_tenure : int or None, optional
        Minimum tabu tenure. Defaults to ``n // 2``.
    max_tenure : int or None, optional
        Maximum tabu tenure. Defaults to ``n + n // 2``.
    max_seconds : float or None, optional
        Optional wall-clock stop.
    accelerated : bool, optional
        Use the O(n^2) Taillard delta-matrix update on symmetric zero-diagonal
        instances. Defaults to True. Set False to force the reference path.
    """

    iterations: int = 20000
    patience: int | None = None
    seed: int = 1
    min_tenure: int | None = None
    max_tenure: int | None = None
    max_seconds: float | None = None
    accelerated: bool = True

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if self.iterations < 1:
            raise ValueError("iterations must be positive")
        if self.patience is not None and self.patience < 1:
            raise ValueError("patience must be positive")
        if self.min_tenure is not None and self.min_tenure < 1:
            raise ValueError("min_tenure must be positive")
        if self.max_tenure is not None and self.max_tenure < 1:
            raise ValueError("max_tenure must be positive")
        if (
            self.min_tenure is not None
            and self.max_tenure is not None
            and self.min_tenure > self.max_tenure
        ):
            raise ValueError("min_tenure must not exceed max_tenure")
        if self.max_seconds is not None and self.max_seconds <= 0.0:
            raise ValueError("max_seconds must be positive")


@dataclass(frozen=True)
class QapTabuResult:
    """Best assignment and counters from QAP tabu search."""

    assignment: dict[int, int]
    objective: float
    evaluations: int
    iterations: int
    stop_reason: str
    history: tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready result."""
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "evaluations": self.evaluations,
            "iterations": self.iterations,
            "stop_reason": self.stop_reason,
            "history": list(self.history),
        }


def _swap_delta(
    problem: QuadraticAssignment,
    permutation: list[int],
    first: int,
    second: int,
) -> float:
    """Return the QAP objective delta for swapping two positions."""
    flows = problem.flows
    distances = problem.distances
    size = len(permutation)
    before_first = permutation[first]
    before_second = permutation[second]
    delta = 0.0
    for other in range(size):
        if other in (first, second):
            continue
        other_city = permutation[other]
        delta += flows[first][other] * (
            distances[before_second][other_city] - distances[before_first][other_city]
        )
        delta += flows[other][first] * (
            distances[other_city][before_second] - distances[other_city][before_first]
        )
        delta += flows[second][other] * (
            distances[before_first][other_city] - distances[before_second][other_city]
        )
        delta += flows[other][second] * (
            distances[other_city][before_first] - distances[other_city][before_second]
        )
    delta += flows[first][first] * (
        distances[before_second][before_second] - distances[before_first][before_first]
    )
    delta += flows[second][second] * (
        distances[before_first][before_first] - distances[before_second][before_second]
    )
    delta += flows[first][second] * (
        distances[before_second][before_first] - distances[before_first][before_second]
    )
    delta += flows[second][first] * (
        distances[before_first][before_second] - distances[before_second][before_first]
    )
    return delta


def _is_symmetric_zero_diagonal(problem: QuadraticAssignment) -> bool:
    """Return whether the Taillard delta update applies."""
    size = problem.variable_count
    for first in range(size):
        if problem.flows[first][first] != 0.0 or problem.distances[first][first] != 0.0:
            return False
        for second in range(first + 1, size):
            if (
                problem.flows[first][second] != problem.flows[second][first]
                or problem.distances[first][second] != problem.distances[second][first]
            ):
                return False
    return True


def _delta_matrix(problem: QuadraticAssignment, assignment: list[int]) -> list[list[float]]:
    """Build the matrix of old-minus-new swap gains."""
    size = len(assignment)
    gains = [[0.0 for _ in range(size)] for _ in range(size)]
    for first in range(size):
        for second in range(first + 1, size):
            gain = -_swap_delta(problem, assignment, first, second)
            gains[first][second] = gain
            gains[second][first] = gain
    return gains


def _update_delta_matrix(
    problem: QuadraticAssignment,
    assignment: list[int],
    gains: list[list[float]],
    first: int,
    second: int,
) -> None:
    """Apply the Taillard O(n^2) delta update after swapping two positions."""
    flows = problem.flows
    distances = problem.distances
    size = len(assignment)
    old_first = assignment[first]
    old_second = assignment[second]
    assignment[first], assignment[second] = old_second, old_first
    old_gains = [row[:] for row in gains]
    for left in range(size):
        for right in range(left + 1, size):
            if left in (first, second) or right in (first, second):
                gain = -_swap_delta(problem, assignment, left, right)
            else:
                factor = (
                    flows[first][left]
                    - flows[first][right]
                    + flows[second][right]
                    - flows[second][left]
                )
                delta = (
                    distances[assignment[second]][assignment[left]]
                    - distances[assignment[second]][assignment[right]]
                    + distances[assignment[first]][assignment[right]]
                    - distances[assignment[first]][assignment[left]]
                )
                gain = old_gains[left][right] - 2.0 * factor * delta
            gains[left][right] = gain
            gains[right][left] = gain


def _run_accelerated(
    problem: QuadraticAssignment,
    config: QapTabuConfig,
    assignment: list[int],
) -> QapTabuResult:
    """Run robust tabu with Taillard's delta-matrix update."""
    rng = random.Random(config.seed)
    size = len(assignment)
    current = problem.evaluate(dict(enumerate(assignment))).objective
    best_objective = current
    best = assignment[:]
    tabu_until = [[0 for _ in range(size)] for _ in range(size)]
    gains = _delta_matrix(problem, assignment)
    evaluations = 1
    history = [current]
    stop_reason = "max_iterations"
    started = time.monotonic()
    iterations = 0
    last_improvement = 0
    for iteration in range(1, config.iterations + 1):
        if config.max_seconds is not None and time.monotonic() - started >= config.max_seconds:
            stop_reason = "max_seconds"
            break
        iterations = iteration
        best_gain = float("-inf")
        best_move: tuple[int, int] | None = None
        for first in range(size):
            for second in range(first + 1, size):
                gain = gains[first][second]
                candidate = current - gain
                if tabu_until[first][second] > iteration and candidate >= best_objective:
                    continue
                if gain > best_gain:
                    best_gain = gain
                    best_move = (first, second)
                evaluations += 1
        if best_move is None:
            break
        first, second = best_move
        _update_delta_matrix(problem, assignment, gains, first, second)
        current -= best_gain
        tabu_until[first][second] = iteration + rng.randint(
            config.min_tenure if config.min_tenure is not None else max(1, size // 2),
            config.max_tenure if config.max_tenure is not None else size + size // 2,
        )
        if current < best_objective:
            best_objective = current
            best = assignment[:]
            history.append(best_objective)
            last_improvement = iteration
        if config.patience is not None and iteration - last_improvement >= config.patience:
            stop_reason = "patience"
            break
    return QapTabuResult(
        assignment=dict(enumerate(best)),
        objective=best_objective,
        evaluations=evaluations,
        iterations=iterations,
        stop_reason=stop_reason,
        history=tuple(history),
    )


def run_qap_tabu(
    problem: QuadraticAssignment,
    config: QapTabuConfig,
    initial: Mapping[int, int] | None = None,
) -> QapTabuResult:
    """Run robust tabu search over QAP facility swaps.

    Parameters
    ----------
    problem : QuadraticAssignment
        QAP instance.
    config : QapTabuConfig
        Search settings.
    initial : mapping of int to int or None, optional
        Starting assignment. Defaults to the adapter's identity assignment.

    Returns
    -------
    QapTabuResult
        Best assignment and stop evidence.
    """
    size = problem.variable_count
    starting = initial if initial is not None else problem.initial_assignment()
    evaluation = problem.evaluate(starting)
    assignment = [starting[index] for index in range(size)]
    if config.accelerated:
        try:
            from .qap_tabu_numba import run_accelerated_general, run_accelerated_numba
        except ImportError:
            if _is_symmetric_zero_diagonal(problem):
                return _run_accelerated(problem, config, assignment)
        else:
            if _is_symmetric_zero_diagonal(problem):
                return run_accelerated_numba(problem, config, assignment)
            return run_accelerated_general(problem, config, assignment)
    rng = random.Random(config.seed)
    current = evaluation.objective
    best_objective = current
    best = assignment[:]
    tabu_until = [[0 for _ in range(size)] for _ in range(size)]
    evaluations = 1
    history = [current]
    stop_reason = "max_iterations"
    started = time.monotonic()
    iterations = 0
    last_improvement = 0
    for iteration in range(1, config.iterations + 1):
        if config.max_seconds is not None and time.monotonic() - started >= config.max_seconds:
            stop_reason = "max_seconds"
            break
        iterations = iteration
        best_delta = float("inf")
        best_move: tuple[int, int] | None = None
        for first in range(size):
            for second in range(first + 1, size):
                delta = _swap_delta(problem, assignment, first, second)
                candidate = current + delta
                if tabu_until[first][second] > iteration and candidate >= best_objective:
                    continue
                if delta < best_delta:
                    best_delta = delta
                    best_move = (first, second)
                evaluations += 1
        if best_move is None:
            break
        first, second = best_move
        assignment[first], assignment[second] = assignment[second], assignment[first]
        current += best_delta
        tabu_until[first][second] = iteration + rng.randint(
            config.min_tenure if config.min_tenure is not None else max(1, size // 2),
            config.max_tenure if config.max_tenure is not None else size + size // 2,
        )
        if current < best_objective:
            best_objective = current
            best = assignment[:]
            history.append(best_objective)
            last_improvement = iteration
        if config.patience is not None and iteration - last_improvement >= config.patience:
            stop_reason = "patience"
            break
    return QapTabuResult(
        assignment=dict(enumerate(best)),
        objective=best_objective,
        evaluations=evaluations,
        iterations=iterations,
        stop_reason=stop_reason,
        history=tuple(history),
    )
