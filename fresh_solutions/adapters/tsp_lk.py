"""Lin-Kernighan and iterated Lin-Kernighan for the TSP adapter.

The implementation uses candidate neighbour lists and a sequential edge-exchange
search.  A local optimum is perturbed with deterministic double-bridge moves and
the LK search is reapplied.  It is a Lin-Kernighan implementation, not the
randomised triple-sampling experiment in :mod:`fresh_solutions.adapters.tsp_three_opt`.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .tsp import TravellingSalesman

Edge = tuple[int, int]


@dataclass(frozen=True)
class TspLkConfig:
    """Configuration for iterated Lin-Kernighan search.

    Parameters
    ----------
    candidate_count : int, optional
        Number of nearest neighbours considered at each exchange step. Defaults to 16.
    max_depth : int, optional
        Maximum sequential exchange depth before the search must close the tour. Defaults to 4.
    kicks : int, optional
        Maximum number of double-bridge perturbations. Defaults to 20.
    patience : int or None, optional
        Stop after this many kicks without a new best tour. ``None`` disables
        the plateau rule and runs the full ``kicks`` budget.
    seed : int, optional
        Random seed for the perturbations. Defaults to 1.
    max_passes : int, optional
        Maximum LK improvement passes per search. Defaults to 100.
    max_seconds : float or None, optional
        Optional wall-clock limit for the whole search.
    """

    candidate_count: int = 16
    max_depth: int = 4
    kicks: int = 20
    patience: int | None = None
    seed: int = 1
    max_passes: int = 100
    max_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if self.candidate_count < 1:
            raise ValueError("candidate_count must be positive")
        if self.max_depth < 1:
            raise ValueError("max_depth must be positive")
        if self.kicks < 0:
            raise ValueError("kicks must not be negative")
        if self.patience is not None and self.patience < 1:
            raise ValueError("patience must be positive")
        if self.max_passes < 1:
            raise ValueError("max_passes must be positive")
        if self.max_seconds is not None and self.max_seconds <= 0.0:
            raise ValueError("max_seconds must be positive")


@dataclass(frozen=True)
class TspLkResult:
    """Best tour and search evidence from iterated Lin-Kernighan."""

    assignment: dict[int, int]
    objective: float
    initial_objective: float
    kicks: int
    accepted_kicks: int
    lk_passes: int
    exchange_tests: int
    improvements: int
    stop_reason: str
    search_seconds: float
    history: tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready result."""
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "initial_objective": self.initial_objective,
            "kicks": self.kicks,
            "accepted_kicks": self.accepted_kicks,
            "lk_passes": self.lk_passes,
            "exchange_tests": self.exchange_tests,
            "improvements": self.improvements,
            "stop_reason": self.stop_reason,
            "search_seconds": self.search_seconds,
            "history": list(self.history),
        }


def _edge(first: int, second: int) -> Edge:
    """Return a normalised undirected edge."""
    return (first, second) if first < second else (second, first)


def _tour_edges(tour: list[int]) -> set[Edge]:
    """Return the undirected edges of a cyclic tour."""
    return {_edge(tour[index], tour[(index + 1) % len(tour)]) for index in range(len(tour))}


def _adjacency(edges: set[Edge], size: int) -> list[list[int]]:
    """Build a deterministic adjacency list."""
    adjacency: list[list[int]] = [[] for _ in range(size)]
    for first, second in sorted(edges):
        adjacency[first].append(second)
        adjacency[second].append(first)
    for neighbours in adjacency:
        neighbours.sort()
    return adjacency


def _tour_from_edges(edges: set[Edge], size: int) -> list[int] | None:
    """Return a tour from a 2-regular connected edge set, or None if invalid."""
    if len(edges) != size:
        return None
    adjacency = _adjacency(edges, size)
    if any(len(neighbours) != 2 for neighbours in adjacency):
        return None
    tour: list[int] = []
    previous = -1
    current = 0
    for _ in range(size):
        tour.append(current)
        first, second = adjacency[current]
        following = second if first == previous else first
        previous, current = current, following
    if current != 0 or len(set(tour)) != size:
        return None
    return tour


def _nearest_neighbours(problem: TravellingSalesman, count: int) -> list[list[int]]:
    """Return deterministic nearest-neighbour candidate lists."""
    distances = problem.distances
    size = problem.variable_count
    candidates: list[list[int]] = []
    for city in range(size):
        order = sorted(
            (other for other in range(size) if other != city),
            key=lambda other: (distances[city][other], other),
        )
        candidates.append(order[:count])
    return candidates


def _tour_objective(problem: TravellingSalesman, tour: list[int]) -> float:
    """Return the exact closed-tour objective."""
    distances = problem.distances
    size = len(tour)
    return float(sum(distances[tour[index]][tour[(index + 1) % size]] for index in range(size)))


def _lk_pass(
    problem: TravellingSalesman,
    tour: list[int],
    candidates: list[list[int]],
    max_depth: int,
    max_passes: int,
    deadline: float | None,
) -> tuple[list[int], int, int, int, bool]:
    """Apply first-improvement LK passes until no exchange is found."""
    size = len(tour)
    edges = _tour_edges(tour)
    adjacency = _adjacency(edges, size)
    current = _tour_objective(problem, tour)
    passes = 0
    tests = 0
    improvements = 0
    timed_out = False
    distances = problem.distances

    while passes < max_passes:
        passes += 1
        if deadline is not None and time.monotonic() >= deadline:
            timed_out = True
            break
        found: list[int] | None = None
        for first in range(size):
            if deadline is not None and time.monotonic() >= deadline:
                timed_out = True
                break
            for second in adjacency[first]:
                removed: set[Edge] = {_edge(first, second)}
                used: set[int] = {first, second}
                first_gain = distances[first][second]
                for third in candidates[second]:
                    if third in used:
                        continue
                    added_edge = _edge(second, third)
                    if added_edge in edges:
                        continue
                    gain = first_gain - distances[second][third]
                    if gain <= 1e-9:
                        continue
                    added: set[Edge] = {added_edge}
                    stack = [
                        (third, used | {third}, removed, added, gain, 1),
                    ]
                    while stack and found is None:
                        (
                            odd,
                            path_used,
                            current_removed,
                            current_added,
                            current_gain,
                            depth,
                        ) = stack.pop()
                        for even in adjacency[odd]:
                            if even in path_used or even == first:
                                continue
                            removed_edge = _edge(odd, even)
                            if removed_edge in current_removed or removed_edge in current_added:
                                continue
                            next_removed = current_removed | {removed_edge}
                            next_gain = current_gain + distances[odd][even]
                            closing = _edge(even, first)
                            if closing not in edges:
                                tests += 1
                                if next_gain - distances[even][first] > 1e-9:
                                    complete_edges = (
                                        (edges - next_removed) | current_added | {closing}
                                    )
                                    complete = _tour_from_edges(complete_edges, size)
                                    if complete is not None:
                                        objective = _tour_objective(problem, complete)
                                        if objective < current - 1e-9:
                                            found = complete
                                            break
                            if depth >= max_depth:
                                continue
                            next_used = path_used | {even}
                            for next_odd in candidates[even]:
                                if next_odd in next_used or next_odd == first:
                                    continue
                                next_added_edge = _edge(even, next_odd)
                                if (
                                    next_added_edge in edges
                                    or next_added_edge in next_removed
                                    or next_added_edge in current_added
                                ):
                                    continue
                                extended_gain = next_gain - distances[even][next_odd]
                                if extended_gain <= 1e-9:
                                    continue
                                stack.append(
                                    (
                                        next_odd,
                                        next_used | {next_odd},
                                        next_removed,
                                        current_added | {next_added_edge},
                                        extended_gain,
                                        depth + 1,
                                    )
                                )
                        if found is not None:
                            break
                    if found is not None:
                        break
                if found is not None:
                    break
            if found is not None or timed_out:
                break
        if timed_out:
            break
        if found is None:
            break
        tour = found
        current = _tour_objective(problem, tour)
        improvements += 1
        edges = _tour_edges(tour)
        adjacency = _adjacency(edges, size)

    return tour, passes, tests, improvements, timed_out


def _double_bridge(tour: list[int], rng: random.Random) -> list[int]:
    """Return a deterministic double-bridge perturbation of a tour."""
    size = len(tour)
    if size < 4:
        return tour[:]
    first, second, third, fourth = sorted(rng.sample(range(size), 4))
    return (
        tour[:first] + tour[third:fourth] + tour[second:third] + tour[first:second] + tour[fourth:]
    )


def run_tsp_lk(
    problem: TravellingSalesman,
    config: TspLkConfig,
    initial: dict[int, int] | None = None,
) -> TspLkResult:
    """Run iterated Lin-Kernighan on a symmetric TSP instance.

    Parameters
    ----------
    problem : TravellingSalesman
        TSP adapter.
    config : TspLkConfig
        Search settings.
    initial : mapping of int to int or None, optional
        Starting tour. Defaults to the adapter's identity tour.

    Returns
    -------
    TspLkResult
        Best tour, objective, and search evidence.
    """
    starting = initial if initial is not None else problem.initial_assignment()
    initial_evaluation = problem.evaluate(starting)
    tour = [starting[index] for index in range(problem.variable_count)]
    initial_objective = initial_evaluation.objective
    started = time.monotonic()
    deadline = started + config.max_seconds if config.max_seconds is not None else None
    candidates = _nearest_neighbours(
        problem,
        min(config.candidate_count, problem.variable_count - 1),
    )
    history = [initial_objective]
    total_passes = 0
    total_tests = 0
    total_improvements = 0
    accepted_kicks = 0
    stop_reason = "max_kicks"
    rng = random.Random(config.seed)

    tour, passes, tests, improvements, timed_out = _lk_pass(
        problem,
        tour,
        candidates,
        config.max_depth,
        config.max_passes,
        deadline,
    )
    total_passes += passes
    total_tests += tests
    total_improvements += improvements
    if timed_out:
        stop_reason = "max_seconds"
    current = _tour_objective(problem, tour)
    best = tour[:]
    best_objective = current
    history.append(current)

    kicks = 0
    stale_kicks = 0
    while kicks < config.kicks and stop_reason != "max_seconds":
        if deadline is not None and time.monotonic() >= deadline:
            stop_reason = "max_seconds"
            break
        kicks += 1
        kicked = _double_bridge(tour, rng)
        kicked, passes, tests, improvements, timed_out = _lk_pass(
            problem,
            kicked,
            candidates,
            config.max_depth,
            config.max_passes,
            deadline,
        )
        total_passes += passes
        total_tests += tests
        total_improvements += improvements
        if timed_out:
            stop_reason = "max_seconds"
        kicked_objective = _tour_objective(problem, kicked)
        if kicked_objective < current - 1e-9:
            tour = kicked
            current = kicked_objective
            accepted_kicks += 1
            if current < best_objective - 1e-9:
                best = tour[:]
                best_objective = current
                history.append(best_objective)
                stale_kicks = 0
            else:
                stale_kicks += 1
        else:
            stale_kicks += 1
        if config.patience is not None and stale_kicks >= config.patience:
            stop_reason = "patience"
            break

    return TspLkResult(
        assignment=dict(enumerate(best)),
        objective=best_objective,
        initial_objective=initial_objective,
        kicks=kicks,
        accepted_kicks=accepted_kicks,
        lk_passes=total_passes,
        exchange_tests=total_tests,
        improvements=total_improvements,
        stop_reason=stop_reason,
        search_seconds=time.monotonic() - started,
        history=tuple(history),
    )
