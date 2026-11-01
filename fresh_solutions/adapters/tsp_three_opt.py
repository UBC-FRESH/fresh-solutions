"""Random 3-opt local search for the TSP adapter."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .tsp import TravellingSalesman


@dataclass(frozen=True)
class TspThreeOptConfig:
    """Configuration for random 3-opt local search.

    Parameters
    ----------
    iterations : int, optional
        Number of sampled triple-cut moves. Defaults to 20,000.
    seed : int, optional
        Random seed. Defaults to 1.
    max_seconds : float or None, optional
        Optional wall-clock stop.
    """

    iterations: int = 20000
    seed: int = 1
    max_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if self.iterations < 1:
            raise ValueError("iterations must be positive")
        if self.max_seconds is not None and self.max_seconds <= 0.0:
            raise ValueError("max_seconds must be positive")


@dataclass(frozen=True)
class TspThreeOptResult:
    """Best assignment from random 3-opt."""

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


def _variants(tour: list[int], first: int, second: int, third: int) -> list[list[int]]:
    """Return the seven nontrivial 3-opt reconnections for three cuts."""
    head = tour[: first + 1]
    middle_a = tour[first + 1 : second + 1]
    middle_b = tour[second + 1 : third + 1]
    tail = tour[third + 1 :]
    return [
        head + list(reversed(middle_a)) + middle_b + tail,
        head + middle_a + list(reversed(middle_b)) + tail,
        head + list(reversed(middle_a)) + list(reversed(middle_b)) + tail,
        head + list(reversed(middle_b)) + middle_a + tail,
        head + list(reversed(middle_b)) + list(reversed(middle_a)) + tail,
        head + middle_b + middle_a + tail,
        head + middle_b + list(reversed(middle_a)) + tail,
    ]


def run_tsp_three_opt(
    problem: TravellingSalesman,
    config: TspThreeOptConfig,
    initial: dict[int, int] | None = None,
) -> TspThreeOptResult:
    """Run randomized 3-opt local search on a TSP instance.

    Parameters
    ----------
    problem : TravellingSalesman
        TSP adapter.
    config : TspThreeOptConfig
        Search settings.
    initial : mapping of int to int or None, optional
        Starting tour. Defaults to the adapter's identity tour.

    Returns
    -------
    TspThreeOptResult
        Best tour and stop evidence.
    """
    rng = random.Random(config.seed)
    tour = list((initial or problem.initial_assignment()).values())
    current = problem.evaluate(dict(enumerate(tour)))
    best = tour[:]
    best_objective = current.objective
    evaluations = 1
    history = [best_objective]
    started = time.monotonic()
    stop_reason = "max_iterations"
    iterations = 0
    size = problem.variable_count
    for iteration in range(1, config.iterations + 1):
        if config.max_seconds is not None and time.monotonic() - started >= config.max_seconds:
            stop_reason = "max_seconds"
            break
        iterations = iteration
        first, second, third = sorted(rng.sample(range(size - 1), 3))
        candidates = _variants(tour, first, second, third)
        for candidate in candidates:
            evaluation = problem.evaluate(dict(enumerate(candidate)))
            evaluations += 1
            if evaluation.objective < best_objective:
                best_objective = evaluation.objective
                best = candidate
        if best_objective < current.objective:
            tour = best[:]
            current = problem.evaluate(dict(enumerate(tour)))
            evaluations += 1
            history.append(best_objective)
    return TspThreeOptResult(
        assignment=dict(enumerate(best)),
        objective=best_objective,
        evaluations=evaluations,
        iterations=iterations,
        stop_reason=stop_reason,
        history=tuple(history),
    )
