"""Robust tabu search for the quadratic assignment adapter."""

from __future__ import annotations

import random
import time
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
    """

    iterations: int = 20000
    patience: int | None = None
    seed: int = 1
    min_tenure: int | None = None
    max_tenure: int | None = None
    max_seconds: float | None = None

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


def run_qap_tabu(problem: QuadraticAssignment, config: QapTabuConfig) -> QapTabuResult:
    """Run robust tabu search over QAP facility swaps.

    Parameters
    ----------
    problem : QuadraticAssignment
        QAP instance.
    config : QapTabuConfig
        Search settings.

    Returns
    -------
    QapTabuResult
        Best assignment and stop evidence.
    """
    rng = random.Random(config.seed)
    size = problem.variable_count
    assignment = list(problem.initial_assignment().values())
    evaluation = problem.evaluate(dict(enumerate(assignment)))
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
