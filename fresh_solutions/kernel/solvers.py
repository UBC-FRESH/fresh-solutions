"""Problem-agnostic metaheuristic solvers over an operator registry.

Every solver takes a :class:`~fresh_solutions.kernel.problem.Problem`, a random source, and
a budget. The state representation, the objective, and the move context belong to the
adapter. All solvers are seeded and reproducible, and each reports its objective trajectory
through optional callbacks.
"""

from __future__ import annotations

import copy
import math
import random
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol, TypeVar

from .control import RunControl
from .cooling import TemperatureSchedule
from .operators import OperatorRegistry, restore_state
from .problem import Problem, clone_state, state_signature
from .stopping import expired, patience_reached, reversion_due, stopped

State = TypeVar("State")
Context = TypeVar("Context")

StepCallback = Callable[[int, float], None]
TraceCallback = Callable[[int, float, float, int], None]
SnapshotCallback = Callable[[int, Mapping[Any, float], State], None]


class DeltaEvaluator(Protocol[State]):
    """A move-based objective evaluator with exact deltas.

    The evaluator owns the objective state for one schedule. A move is priced before it is
    applied; accepting it calls :meth:`apply`, and rejecting it calls :meth:`revert`.
    """

    @property
    def totals(self) -> Mapping[Any, float]:
        """Return the realized display values per cell."""
        ...

    @property
    def assignments(self) -> State:
        """Return the current state."""
        ...

    @property
    def objective(self) -> float:
        """Return the current exact objective."""
        ...

    def reset(self, state: State) -> None:
        """Set the evaluator to a complete state."""
        ...

    def delta(self, changed: Sequence[int], state: State) -> float:
        """Return the exact objective change for a proposed move."""
        ...

    def apply(self, changed: Sequence[int], state: State) -> None:
        """Commit a proposed move to the evaluator's state."""
        ...

    def revert(self) -> None:
        """Discard the most recent proposed move."""
        ...


def _initial_state(problem: Problem[State, Any], initial: State | None) -> State:
    """Return the starting state, cloning an explicit one or asking the problem for an empty one.

    Parameters
    ----------
    problem : Problem
        The problem adapter.
    initial : State or None
        An explicit starting state, or ``None`` for the problem's empty state.

    Returns
    -------
    State
        The starting state.

    Raises
    ------
    ValueError
        When ``initial`` is omitted and the problem has no ``empty`` factory.
    """
    if initial is not None:
        return clone_state(problem, initial)
    if problem.empty is None:
        raise ValueError("problem has no empty-state factory; pass an initial state")
    return problem.empty()


def _report(on_step: StepCallback | None, iteration: int, objective: float) -> None:
    """Report an iteration's incumbent objective when a callback is given."""
    if on_step is not None:
        on_step(iteration, objective)


def _trace(
    on_trace: TraceCallback | None,
    iteration: int,
    best: float,
    current: float,
    accepted: int,
) -> None:
    """Report the current solution alongside the incumbent when a callback is given."""
    if on_trace is not None:
        on_trace(iteration, best, current, accepted)


def _emit_snapshot(
    on_snapshot: SnapshotCallback[State] | None,
    problem: Problem[State, Any],
    iteration: int,
    iterations: int,
    best: State,
) -> None:
    """Emit a live snapshot every twentieth iteration and on the last one."""
    if on_snapshot is None or not (iteration % 20 == 0 or iteration == iterations - 1):
        return
    values: Mapping[Any, float] = problem.snapshot(best) if problem.snapshot is not None else {}
    on_snapshot(iteration, values, best)


def solve_sa(
    problem: Problem[State, Any],
    rng: random.Random,
    *,
    iterations: int,
    temperature: float,
    cooling: float,
    on_step: StepCallback | None = None,
    on_trace: TraceCallback | None = None,
    on_snapshot: SnapshotCallback[State] | None = None,
    initial: State | None = None,
    adaptive: bool = False,
    cooling_window: int = 64,
    control: RunControl | None = None,
    deadline: float | None = None,
    patience: int = 0,
    reversion: int = 0,
) -> tuple[State, float]:
    """Run simulated annealing.

    Parameters
    ----------
    problem : Problem
        The problem adapter.
    rng : random.Random
        The random source.
    iterations : int
        The iteration budget.
    temperature : float
        The initial temperature.
    cooling : float
        The geometric cooling factor.
    on_step : callable or None, optional
        Called with ``(iteration, best_objective)`` each iteration.
    on_trace : callable or None, optional
        Called with ``(iteration, best_objective, current_objective, accepted_moves)``.
    on_snapshot : callable or None, optional
        Called with ``(iteration, realized values, incumbent state)`` periodically.
    initial : State or None, optional
        A starting state. ``None`` uses the problem's empty state.
    adaptive : bool, optional
        Use the adaptive Aarts--Van Laarhoven schedule.
    cooling_window : int, optional
        The iterations per temperature in adaptive mode.
    control : RunControl or None, optional
        A polled control file.
    deadline : float or None, optional
        A :func:`time.monotonic` deadline, or ``None``.
    patience : int, optional
        Stop after this many iterations without improvement; ``0`` disables it.
    reversion : int, optional
        Revert to the incumbent every this many accepted moves; ``0`` disables it.

    Returns
    -------
    tuple of (State, float)
        The best state and its objective.
    """
    current = _initial_state(problem, initial)
    current_obj = problem.evaluate(current)
    best, best_obj = clone_state(problem, current), current_obj
    accepted = 0
    schedule = TemperatureSchedule(
        initial=temperature,
        cooling=cooling,
        adaptive=adaptive,
        window=TemperatureSchedule.effective_window(iterations, cooling_window),
    )
    last_improvement = 0
    for iteration in range(iterations):
        if patience_reached(iteration, last_improvement, patience):
            break
        if expired(deadline) or stopped(control, iteration):
            break
        increase = 0.0
        move = problem.registry.pick(rng).apply(current, rng, problem.candidates)
        if move is not None:
            move_obj = problem.evaluate(move)
            increase = move_obj - current_obj
            if move_obj <= current_obj or rng.random() < math.exp(
                (current_obj - move_obj) / max(schedule.temperature, 1e-9)
            ):
                current, current_obj = move, move_obj
                accepted += 1
                if move_obj < best_obj:
                    best, best_obj = clone_state(problem, move), move_obj
                    last_improvement = iteration
                if reversion_due(accepted, reversion):
                    current, current_obj = clone_state(problem, best), best_obj
                    accepted = 0
        schedule.observe(increase, current_obj)
        _report(on_step, iteration, best_obj)
        _trace(on_trace, iteration, best_obj, current_obj, accepted)
        _emit_snapshot(on_snapshot, problem, iteration, iterations, best)
    return best, best_obj


def solve_sa_delta(
    evaluator: DeltaEvaluator[State],
    rng: random.Random,
    *,
    iterations: int,
    temperature: float,
    cooling: float,
    candidates: Context,
    registry: OperatorRegistry[State, Context],
    initial: State | None = None,
    on_step: StepCallback | None = None,
    on_trace: TraceCallback | None = None,
    on_snapshot: SnapshotCallback[State] | None = None,
    adaptive: bool = False,
    cooling_window: int = 64,
    control: RunControl | None = None,
    deadline: float | None = None,
    patience: int = 0,
    reversion: int = 0,
) -> tuple[State, float]:
    """Run simulated annealing priced by exact per-move deltas.

    The acceptance rule is identical to :func:`solve_sa`, but the objective is updated by
    the move's exact delta instead of recomputing the whole state.

    Parameters
    ----------
    evaluator : DeltaEvaluator
        The move-based evaluator. It also holds the running state.
    rng : random.Random
        The random source.
    iterations : int
        The iteration budget.
    temperature : float
        The initial temperature.
    cooling : float
        The geometric cooling factor.
    candidates : object
        The adapter-owned move context.
    registry : OperatorRegistry
        The move operators.
    initial : State or None, optional
        A starting state. ``None`` requires the caller to have reset the evaluator first.
    on_step, on_trace, on_snapshot : callable or None, optional
        Progress callbacks, as in :func:`solve_sa`.
    adaptive : bool, optional
        Use the adaptive Aarts--Van Laarhoven schedule.
    cooling_window : int, optional
        The iterations per temperature in adaptive mode.
    control : RunControl or None, optional
        A polled control file.
    deadline : float or None, optional
        A :func:`time.monotonic` deadline, or ``None``.
    patience : int, optional
        Stop after this many iterations without improvement; ``0`` disables it.
    reversion : int, optional
        Revert to the incumbent every this many accepted moves; ``0`` disables it.

    Returns
    -------
    tuple of (State, float)
        The best state and its objective.

    Raises
    ------
    ValueError
        When ``initial`` is ``None``.
    """
    if initial is None:
        raise ValueError("solve_sa_delta needs an initial state")
    current = copy.deepcopy(initial)
    evaluator.reset(current)
    current_obj = evaluator.objective
    best, best_obj = copy.deepcopy(current), current_obj
    schedule = TemperatureSchedule(
        initial=temperature,
        cooling=cooling,
        adaptive=adaptive,
        window=TemperatureSchedule.effective_window(iterations, cooling_window),
    )
    last_improvement = 0
    accepted = 0
    for iteration in range(iterations):
        if patience_reached(iteration, last_improvement, patience):
            break
        if expired(deadline) or stopped(control, iteration):
            break
        increase = 0.0
        operator = registry.pick(rng)
        undo = operator.propose_inplace(current, rng, candidates)
        if undo is not None:
            changed = list(undo)
            move_obj = current_obj + evaluator.delta(changed, current)
            increase = move_obj - current_obj
            if move_obj <= current_obj or rng.random() < math.exp(
                (current_obj - move_obj) / max(schedule.temperature, 1e-9)
            ):
                evaluator.apply(changed, current)
                current_obj = move_obj
                accepted += 1
                if move_obj < best_obj:
                    best, best_obj = copy.deepcopy(current), move_obj
                    last_improvement = iteration
                if reversion_due(accepted, reversion):
                    current = copy.deepcopy(best)
                    evaluator.reset(current)
                    current_obj = best_obj
                    accepted = 0
            else:
                restore_state(current, undo)
                evaluator.revert()
        schedule.observe(increase, current_obj)
        _report(on_step, iteration, best_obj)
        _trace(on_trace, iteration, best_obj, current_obj, accepted)
        if on_snapshot is not None and (iteration % 20 == 0 or iteration == iterations - 1):
            on_snapshot(iteration, evaluator.totals, evaluator.assignments)
    return best, best_obj


def solve_tabu(
    problem: Problem[State, Any],
    rng: random.Random,
    *,
    iterations: int,
    tenure: int,
    samples: int = 8,
    on_step: StepCallback | None = None,
    on_trace: TraceCallback | None = None,
    on_snapshot: SnapshotCallback[State] | None = None,
    initial: State | None = None,
    control: RunControl | None = None,
    deadline: float | None = None,
    patience: int = 0,
    reversion: int = 0,
) -> tuple[State, float]:
    """Run tabu search: pick the best non-tabu move each iteration.

    Parameters
    ----------
    problem : Problem
        The problem adapter.
    rng : random.Random
        The random source.
    iterations : int
        The iteration budget.
    tenure : int
        The tabu list length.
    samples : int, optional
        The number of candidate moves sampled per iteration. Defaults to 8.
    on_step, on_trace, on_snapshot : callable or None, optional
        Progress callbacks, as in :func:`solve_sa`.
    initial : State or None, optional
        A starting state. ``None`` uses the problem's empty state.
    control : RunControl or None, optional
        A polled control file.
    deadline : float or None, optional
        A :func:`time.monotonic` deadline, or ``None``.
    patience : int, optional
        Stop after this many iterations without improvement; ``0`` disables it.
    reversion : int, optional
        Revert to the incumbent every this many accepted moves; ``0`` disables it.

    Returns
    -------
    tuple of (State, float)
        The best state and its objective.
    """
    current = _initial_state(problem, initial)
    current_obj = problem.evaluate(current)
    best, best_obj = clone_state(problem, current), current_obj
    accepted = 0
    tabu: deque[Any] = deque(maxlen=tenure)
    last_improvement = 0
    for iteration in range(iterations):
        if patience_reached(iteration, last_improvement, patience):
            break
        if expired(deadline) or stopped(control, iteration):
            break
        chosen: State | None = None
        chosen_obj = math.inf
        for _ in range(samples):
            move = problem.registry.pick(rng).apply(current, rng, problem.candidates)
            if move is None:
                continue
            signature = state_signature(problem, current, move)
            move_obj = problem.evaluate(move)
            if signature in tabu and move_obj >= best_obj:
                continue
            if move_obj < chosen_obj:
                chosen, chosen_obj = move, move_obj
        if chosen is not None:
            tabu.append(state_signature(problem, current, chosen))
            current, current_obj = chosen, chosen_obj
            accepted += 1
            if current_obj < best_obj:
                best, best_obj = clone_state(problem, current), current_obj
                last_improvement = iteration
            if reversion_due(accepted, reversion):
                current, current_obj = clone_state(problem, best), best_obj
                accepted = 0
        _report(on_step, iteration, best_obj)
        _trace(on_trace, iteration, best_obj, current_obj, accepted)
        _emit_snapshot(on_snapshot, problem, iteration, iterations, best)
    return best, best_obj


def solve_threshold(
    problem: Problem[State, Any],
    rng: random.Random,
    *,
    iterations: int,
    threshold: float,
    cooling: float,
    on_step: StepCallback | None = None,
    on_trace: TraceCallback | None = None,
    on_snapshot: SnapshotCallback[State] | None = None,
    initial: State | None = None,
    control: RunControl | None = None,
    deadline: float | None = None,
    patience: int = 0,
    reversion: int = 0,
) -> tuple[State, float]:
    """Run threshold accepting: accept a move within the current threshold.

    Parameters
    ----------
    problem : Problem
        The problem adapter.
    rng : random.Random
        The random source.
    iterations : int
        The iteration budget.
    threshold : float
        The initial threshold, in objective units.
    cooling : float
        The factor applied to the threshold each iteration, in ``(0, 1]``.
    on_step, on_trace, on_snapshot : callable or None, optional
        Progress callbacks, as in :func:`solve_sa`.
    initial : State or None, optional
        A starting state. ``None`` uses the problem's empty state.
    control : RunControl or None, optional
        A polled control file.
    deadline : float or None, optional
        A :func:`time.monotonic` deadline, or ``None``.
    patience : int, optional
        Stop after this many iterations without improvement; ``0`` disables it.
    reversion : int, optional
        Revert to the incumbent every this many accepted moves; ``0`` disables it.

    Returns
    -------
    tuple of (State, float)
        The best state and its objective.

    Raises
    ------
    ValueError
        When ``threshold`` is negative or ``cooling`` is outside ``(0, 1]``.
    """
    if threshold < 0.0:
        raise ValueError("threshold must be zero or positive")
    if not 0.0 < cooling <= 1.0:
        raise ValueError("cooling must be in (0, 1]")
    current = _initial_state(problem, initial)
    current_obj = problem.evaluate(current)
    best, best_obj = clone_state(problem, current), current_obj
    accepted = 0
    last_improvement = 0
    current_threshold = threshold
    for iteration in range(iterations):
        if patience_reached(iteration, last_improvement, patience):
            break
        if expired(deadline) or stopped(control, iteration):
            break
        move = problem.registry.pick(rng).apply(current, rng, problem.candidates)
        if move is not None:
            move_obj = problem.evaluate(move)
            if move_obj <= current_obj or (move_obj - current_obj) <= current_threshold:
                current, current_obj = move, move_obj
                accepted += 1
                if move_obj < best_obj:
                    best, best_obj = clone_state(problem, move), move_obj
                    last_improvement = iteration
                if reversion_due(accepted, reversion):
                    current, current_obj = clone_state(problem, best), best_obj
                    accepted = 0
        current_threshold *= cooling
        _report(on_step, iteration, best_obj)
        _trace(on_trace, iteration, best_obj, current_obj, accepted)
        _emit_snapshot(on_snapshot, problem, iteration, iterations, best)
        if current_threshold <= 1e-12:
            break
    return best, best_obj


def solve_ils(
    problem: Problem[State, Any],
    rng: random.Random,
    *,
    iterations: int,
    perturbation: int,
    on_step: StepCallback | None = None,
    on_trace: TraceCallback | None = None,
    on_snapshot: SnapshotCallback[State] | None = None,
    initial: State | None = None,
    control: RunControl | None = None,
    deadline: float | None = None,
    patience: int = 0,
    reversion: int = 0,
) -> tuple[State, float]:
    """Run iterated local search: perturb, then accept an improvement.

    Parameters
    ----------
    problem : Problem
        The problem adapter.
    rng : random.Random
        The random source.
    iterations : int
        The iteration budget.
    perturbation : int
        The number of random moves applied to perturb the incumbent.
    on_step, on_trace, on_snapshot : callable or None, optional
        Progress callbacks, as in :func:`solve_sa`.
    initial : State or None, optional
        A starting state. ``None`` uses the problem's empty state.
    control : RunControl or None, optional
        A polled control file.
    deadline : float or None, optional
        A :func:`time.monotonic` deadline, or ``None``.
    patience : int, optional
        Stop after this many iterations without improvement; ``0`` disables it.
    reversion : int, optional
        Revert to the incumbent every this many accepted moves; ``0`` disables it.

    Returns
    -------
    tuple of (State, float)
        The best state and its objective.
    """
    current = _initial_state(problem, initial)
    current_obj = problem.evaluate(current)
    best, best_obj = clone_state(problem, current), current_obj
    last_improvement = 0
    accepted = 0
    for iteration in range(iterations):
        if patience_reached(iteration, last_improvement, patience):
            break
        if expired(deadline) or stopped(control, iteration):
            break
        candidate = clone_state(problem, current)
        for _ in range(perturbation):
            move = problem.registry.pick(rng).apply(candidate, rng, problem.candidates)
            if move is not None:
                candidate = move
        candidate_obj = problem.evaluate(candidate)
        if candidate_obj < current_obj:
            current, current_obj = candidate, candidate_obj
            accepted += 1
            if candidate_obj < best_obj:
                best, best_obj = clone_state(problem, candidate), candidate_obj
                last_improvement = iteration
            if reversion_due(accepted, reversion):
                current, current_obj = clone_state(problem, best), best_obj
                accepted = 0
        _report(on_step, iteration, best_obj)
        _trace(on_trace, iteration, best_obj, current_obj, accepted)
        _emit_snapshot(on_snapshot, problem, iteration, iterations, best)
    return best, best_obj
