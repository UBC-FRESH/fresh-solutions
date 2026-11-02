"""Optional Numba acceleration for the QAP delta-matrix tabu path."""

from __future__ import annotations

import random
import time

import numpy as np
from numba import njit

from .qap import QuadraticAssignment
from .qap_tabu import QapTabuConfig, QapTabuResult


@njit(cache=True)
def _initialize(
    flows: np.ndarray,
    distances: np.ndarray,
    assignment: np.ndarray,
) -> np.ndarray:
    size = assignment.shape[0]
    gains = np.zeros((size, size), dtype=np.float64)
    for first in range(size):
        for second in range(first + 1, size):
            before_first = assignment[first]
            before_second = assignment[second]
            delta = 0.0
            for other in range(size):
                if other in (first, second):
                    continue
                other_city = assignment[other]
                delta += flows[first, other] * (
                    distances[before_second, other_city] - distances[before_first, other_city]
                )
                delta += flows[other, first] * (
                    distances[other_city, before_second] - distances[other_city, before_first]
                )
                delta += flows[second, other] * (
                    distances[before_first, other_city] - distances[before_second, other_city]
                )
                delta += flows[other, second] * (
                    distances[other_city, before_first] - distances[other_city, before_second]
                )
            delta += flows[first, first] * (
                distances[before_second, before_second] - distances[before_first, before_first]
            )
            delta += flows[second, second] * (
                distances[before_first, before_first] - distances[before_second, before_second]
            )
            delta += flows[first, second] * (
                distances[before_second, before_first] - distances[before_first, before_second]
            )
            delta += flows[second, first] * (
                distances[before_first, before_second] - distances[before_second, before_first]
            )
            gains[first, second] = -delta
            gains[second, first] = -delta
    return gains


@njit(cache=True)
def _best_move(
    gains: np.ndarray,
    tabu_until: np.ndarray,
    current: float,
    best_objective: float,
    iteration: int,
) -> tuple[float, int, int]:
    size = gains.shape[0]
    best_gain = -1.0e300
    best_first = -1
    best_second = -1
    for first in range(size):
        for second in range(first + 1, size):
            gain = gains[first, second]
            candidate = current - gain
            if tabu_until[first, second] > iteration and candidate >= best_objective:
                continue
            if gain > best_gain:
                best_gain = gain
                best_first = first
                best_second = second
    return best_gain, best_first, best_second


@njit(cache=True)
def _update(
    flows: np.ndarray,
    distances: np.ndarray,
    assignment: np.ndarray,
    gains: np.ndarray,
    first: int,
    second: int,
) -> None:
    size = assignment.shape[0]
    old_first = assignment[first]
    old_second = assignment[second]
    assignment[first] = old_second
    assignment[second] = old_first
    old_gains = gains.copy()
    for left in range(size):
        for right in range(left + 1, size):
            if left in (first, second) or right in (first, second):
                before_left = assignment[left]
                before_right = assignment[right]
                delta = 0.0
                for other in range(size):
                    if other in (left, right):
                        continue
                    other_city = assignment[other]
                    delta += flows[left, other] * (
                        distances[before_right, other_city] - distances[before_left, other_city]
                    )
                    delta += flows[other, left] * (
                        distances[other_city, before_right] - distances[other_city, before_left]
                    )
                    delta += flows[right, other] * (
                        distances[before_left, other_city] - distances[before_right, other_city]
                    )
                    delta += flows[other, right] * (
                        distances[other_city, before_left] - distances[other_city, before_right]
                    )
                delta += flows[left, left] * (
                    distances[before_right, before_right] - distances[before_left, before_left]
                )
                delta += flows[right, right] * (
                    distances[before_left, before_left] - distances[before_right, before_right]
                )
                delta += flows[left, right] * (
                    distances[before_right, before_left] - distances[before_left, before_right]
                )
                delta += flows[right, left] * (
                    distances[before_left, before_right] - distances[before_right, before_left]
                )
                gain = -delta
            else:
                factor = (
                    flows[first, left]
                    - flows[first, right]
                    + flows[second, right]
                    - flows[second, left]
                )
                delta = (
                    distances[assignment[second], assignment[left]]
                    - distances[assignment[second], assignment[right]]
                    + distances[assignment[first], assignment[right]]
                    - distances[assignment[first], assignment[left]]
                )
                gain = old_gains[left, right] - 2.0 * factor * delta
            gains[left, right] = gain
            gains[right, left] = gain


def run_accelerated_numba(
    problem: QuadraticAssignment,
    config: QapTabuConfig,
    assignment: list[int],
) -> QapTabuResult:
    """Run the delta-matrix tabu search with Numba loops."""
    flows = np.asarray(problem.flows, dtype=np.float64)
    distances = np.asarray(problem.distances, dtype=np.float64)
    permutation = np.asarray(assignment, dtype=np.int64)
    gains = _initialize(flows, distances, permutation)
    tabu_until = np.zeros((len(assignment), len(assignment)), dtype=np.int64)
    rng = random.Random(config.seed)
    size = len(assignment)
    current = problem.evaluate(dict(enumerate(assignment))).objective
    best_objective = current
    best = assignment[:]
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
        best_gain, first, second = _best_move(
            gains,
            tabu_until,
            current,
            best_objective,
            iteration,
        )
        if first < 0:
            break
        _update(flows, distances, permutation, gains, first, second)
        current -= best_gain
        evaluations += size * (size - 1) // 2
        tabu_until[first, second] = iteration + rng.randint(
            config.min_tenure if config.min_tenure is not None else max(1, size // 2),
            config.max_tenure if config.max_tenure is not None else size + size // 2,
        )
        if current < best_objective:
            best_objective = current
            best = [int(value) for value in permutation]
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


@njit(cache=True)
def _best_move_general(
    flows: np.ndarray,
    distances: np.ndarray,
    assignment: np.ndarray,
    tabu_until: np.ndarray,
    current: float,
    best_objective: float,
    iteration: int,
) -> tuple[float, int, int]:
    size = assignment.shape[0]
    best_delta = 1.0e300
    best_first = -1
    best_second = -1
    for first in range(size):
        for second in range(first + 1, size):
            before_first = assignment[first]
            before_second = assignment[second]
            delta = 0.0
            for other in range(size):
                if other in (first, second):
                    continue
                other_city = assignment[other]
                delta += flows[first, other] * (
                    distances[before_second, other_city] - distances[before_first, other_city]
                )
                delta += flows[other, first] * (
                    distances[other_city, before_second] - distances[other_city, before_first]
                )
                delta += flows[second, other] * (
                    distances[before_first, other_city] - distances[before_second, other_city]
                )
                delta += flows[other, second] * (
                    distances[other_city, before_first] - distances[other_city, before_second]
                )
            delta += flows[first, first] * (
                distances[before_second, before_second] - distances[before_first, before_first]
            )
            delta += flows[second, second] * (
                distances[before_first, before_first] - distances[before_second, before_second]
            )
            delta += flows[first, second] * (
                distances[before_second, before_first] - distances[before_first, before_second]
            )
            delta += flows[second, first] * (
                distances[before_first, before_second] - distances[before_second, before_first]
            )
            candidate = current + delta
            if tabu_until[first, second] > iteration and candidate >= best_objective:
                continue
            if delta < best_delta:
                best_delta = delta
                best_first = first
                best_second = second
    return best_delta, best_first, best_second


def run_accelerated_general(
    problem: QuadraticAssignment,
    config: QapTabuConfig,
    assignment: list[int],
) -> QapTabuResult:
    """Run the general tabu scan with Numba loops."""
    flows = np.asarray(problem.flows, dtype=np.float64)
    distances = np.asarray(problem.distances, dtype=np.float64)
    permutation = np.asarray(assignment, dtype=np.int64)
    tabu_until = np.zeros((len(assignment), len(assignment)), dtype=np.int64)
    rng = random.Random(config.seed)
    size = len(assignment)
    current = problem.evaluate(dict(enumerate(assignment))).objective
    best_objective = current
    best = assignment[:]
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
        delta, first, second = _best_move_general(
            flows,
            distances,
            permutation,
            tabu_until,
            current,
            best_objective,
            iteration,
        )
        if first < 0:
            break
        permutation[first], permutation[second] = permutation[second], permutation[first]
        current += delta
        evaluations += size * (size - 1) // 2
        tabu_until[first, second] = iteration + rng.randint(
            config.min_tenure if config.min_tenure is not None else max(1, size // 2),
            config.max_tenure if config.max_tenure is not None else size + size // 2,
        )
        if current < best_objective:
            best_objective = current
            best = [int(value) for value in permutation]
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
