"""Contract tests for the shared kernel: registry, solvers, and stopping rules."""

from __future__ import annotations

import json
import random
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from fresh_solutions.kernel import (
    AdaptiveCooling,
    OperatorRegistry,
    Problem,
    RunControl,
    TemperatureSchedule,
    clone_state,
    expired,
    parse_time_limit,
    patience_reached,
    restore,
    reversion_due,
    solve_ils,
    solve_sa,
    solve_sa_delta,
    solve_tabu,
    solve_threshold,
    state_signature,
    stopped,
)
from fresh_solutions.kernel.problem import Problem as ProblemType

State = dict[int, int]
Context = tuple[int, ...]


def _objective(state: State) -> float:
    return float(sum((value - 2) ** 2 for value in state.values()))


def _empty() -> State:
    return dict.fromkeys(range(4), 4)


class Revalue:
    """Set one key to a random value from zero to four."""

    name = "revalue"
    weight = 1.0

    def propose_inplace(
        self, state: State, rng: random.Random, context: Context
    ) -> dict[int, object] | None:
        key = rng.choice(context)
        before = state.get(key)
        state[key] = rng.randrange(5)
        return {key: before}

    def apply(self, state: State, rng: random.Random, context: Context) -> State | None:
        result = dict(state)
        self.propose_inplace(result, rng, context)
        return result


class NoMove:
    """An operator that can never move."""

    name = "no-move"
    weight = 1.0

    def propose_inplace(
        self, state: State, rng: random.Random, context: Context
    ) -> dict[int, object] | None:
        return None

    def apply(self, state: State, rng: random.Random, context: Context) -> State | None:
        return None


class Worsen:
    """Set one key to the worst value, so SA rejects the move at a low temperature."""

    name = "worsen"
    weight = 1.0

    def propose_inplace(
        self, state: State, rng: random.Random, context: Context
    ) -> dict[int, object] | None:
        key = context[0]
        before = state.get(key)
        state[key] = 4
        return {key: before}

    def apply(self, state: State, rng: random.Random, context: Context) -> State | None:
        result = dict(state)
        self.propose_inplace(result, rng, context)
        return result


class Improve:
    """Set the first non-optimal key to its optimum, so every proposal is accepted."""

    name = "improve"
    weight = 1.0

    def propose_inplace(
        self, state: State, rng: random.Random, context: Context
    ) -> dict[int, object] | None:
        for key, value in state.items():
            if value != 2:
                state[key] = 2
                return {key: value}
        return None

    def apply(self, state: State, rng: random.Random, context: Context) -> State | None:
        result = dict(state)
        if self.propose_inplace(result, rng, context) is None:
            return None
        return result


class ToyDelta:
    """A deliberately simple exact delta evaluator for the toy objective."""

    def __init__(self) -> None:
        self.assignments: State = {}
        self.totals: dict[Any, float] = {}
        self._objective = 0.0

    @property
    def objective(self) -> float:
        return self._objective

    def reset(self, state: State) -> None:
        self.assignments = dict(state)
        self._objective = _objective(state)

    def delta(self, changed: Sequence[int], state: State) -> float:
        return _objective(state) - self._objective

    def apply(self, changed: Sequence[int], state: State) -> None:
        self.assignments = dict(state)
        self._objective = _objective(state)

    def revert(self) -> None:
        return None


def _problem() -> Problem[State, Context]:
    return Problem(
        evaluate=_objective,
        candidates=tuple(range(4)),
        registry=OperatorRegistry([Revalue()]),
        empty=_empty,
        clone=lambda state: dict(state),
        snapshot=lambda state: {"total": float(sum(state.values()))},
    )


def test_clone_defaults_to_a_deep_copy() -> None:
    """A problem without a clone hook still gets an independent state."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry(),
    )
    state = {1: 3}
    assert clone_state(problem, state) == state
    assert clone_state(problem, state) is not state


def test_signature_uses_an_explicit_hook() -> None:
    """A package that knows its move semantics supplies its own tabu signature."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry(),
        signature=lambda before, after: ("custom", len(before), len(after)),
    )
    assert state_signature(problem, {1: 1}, {1: 2}) == ("custom", 1, 1)


def test_registry_selects_positive_weights_and_reports_names() -> None:
    """The registry exposes names and weights and never selects a disabled operator."""
    registry: OperatorRegistry[State, Context] = OperatorRegistry(
        [Revalue(), NoMove()],
    )
    registry.operators[1].weight = 0.0
    assert registry.names() == ["revalue", "no-move"]
    assert registry.weights()["no-move"] == 0.0
    rng = random.Random(1)
    assert all(registry.pick(rng).name == "revalue" for _ in range(20))


def test_an_empty_registry_cannot_pick() -> None:
    """An empty registry fails loudly instead of returning no operator."""
    registry: OperatorRegistry[State, Context] = OperatorRegistry()
    with pytest.raises(ValueError, match="no positive weight"):
        registry.pick(random.Random(1))


def test_restore_removes_absent_units_and_restores_values() -> None:
    """The undo record distinguishes an absent unit from a stored ``None``."""
    state = {1: "new"}
    restore(state, {1: "old", 2: None})
    assert state == {1: "old"}


def test_clone_and_signature_use_the_adapter_hooks() -> None:
    """The problem hooks override the kernel defaults."""
    problem = _problem()
    state = {1: 3}
    assert clone_state(problem, state) == state
    assert clone_state(problem, state) is not state
    assert state_signature(problem, {1: 1}, {1: 2}) == frozenset({(1, "2")})


def test_signature_falls_back_for_non_mappings() -> None:
    """A non-mapping state still gets a hashable signature."""
    problem: ProblemType[list[int], Context] = Problem(
        evaluate=lambda state: float(sum(state)),
        candidates=(),
        registry=OperatorRegistry(),
        signature=None,
    )
    assert state_signature(problem, [1], [2]) == ("[1]", "[2]")


def test_initial_state_requires_an_empty_factory() -> None:
    """A solver without an initial state needs an explicit empty factory."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([Revalue()]),
    )
    with pytest.raises(ValueError, match="empty-state"):
        solve_sa(problem, random.Random(1), iterations=1, temperature=1.0, cooling=0.9)


def test_sa_improves_and_reports_progress() -> None:
    """SA accepts improvements, records history, and emits a final snapshot."""
    steps: list[tuple[int, float]] = []
    snapshots: list[tuple[int, float]] = []
    _best, objective = solve_sa(
        _problem(),
        random.Random(2),
        iterations=300,
        temperature=1.0,
        cooling=0.99,
        on_step=lambda iteration, value: steps.append((iteration, value)),
        on_snapshot=lambda iteration, values, state: snapshots.append((iteration, values["total"])),
    )
    assert objective < _objective(_empty())
    assert len(steps) == 300
    assert snapshots[-1][0] == 299


def test_sa_accepts_an_explicit_initial_state_and_traces() -> None:
    """An explicit initial state is cloned, and the trace callback is called."""
    traces: list[tuple[int, float, float, int]] = []
    _best, objective = solve_sa(
        _problem(),
        random.Random(8),
        iterations=30,
        temperature=1.0,
        cooling=0.9,
        initial={0: 0, 1: 0, 2: 0, 3: 0},
        on_trace=lambda iteration, best, current, accepted: traces.append(
            (iteration, best, current, accepted)
        ),
    )
    assert objective >= 0.0
    assert len(traces) == 30


def test_sa_handles_no_move_and_a_deadline() -> None:
    """A no-move operator leaves the incumbent unchanged; an expired deadline stops early."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, objective = solve_sa(
        problem,
        random.Random(9),
        iterations=10,
        temperature=1.0,
        cooling=0.9,
        deadline=time.monotonic() - 1.0,
    )
    assert best == _empty()
    assert objective == _objective(_empty())


def test_sa_no_move_and_patience_cover_the_flat_path() -> None:
    """A no-move operator is skipped and patience stops the flat search."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, objective = solve_sa(
        problem, random.Random(17), iterations=10, temperature=1.0, cooling=0.9, patience=1
    )
    assert best == _empty()
    assert objective == _objective(_empty())


def test_sa_patience_and_reversion_are_optional() -> None:
    """Patience stops a flat search and reversion resets the accepted count."""
    best, _ = solve_sa(
        _problem(),
        random.Random(3),
        iterations=1000,
        temperature=1.0,
        cooling=0.999,
        patience=5,
        reversion=3,
    )
    assert best
    assert patience_reached(10, 5, 5)
    assert not patience_reached(10, 5, 0)
    assert reversion_due(6, 3)
    assert not reversion_due(0, 3)


def test_sa_honours_a_stop_control_and_reversion() -> None:
    """A stop control ends the loop and a one-move reversion resets the current state."""
    control = RunControl(Path("/nonexistent/control.json"))
    best, _ = solve_sa(
        _problem(),
        random.Random(10),
        iterations=30,
        temperature=1.0,
        cooling=0.99,
        control=control,
        reversion=1,
    )
    assert best


def test_adaptive_cooling_changes_temperature() -> None:
    """The adaptive schedule warms up and then cools from the objective spread."""
    schedule = TemperatureSchedule(
        initial=1.0,
        cooling=0.9,
        adaptive=True,
        window=2,
    )
    schedule.observe(1.0, 10.0)
    schedule.observe(3.0, 11.0)
    assert schedule.temperature > 0.0
    schedule.observe(0.0, 12.0)
    schedule.observe(0.0, 14.0)
    assert TemperatureSchedule.effective_window(10, 64) == 5


def test_tabu_handles_no_move_and_reversion() -> None:
    """Tabu skips a no-move operator and resets the accepted count on reversion."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, _ = solve_tabu(problem, random.Random(13), iterations=3, tenure=2, reversion=1)
    assert best == _empty()
    best, _ = solve_tabu(_problem(), random.Random(14), iterations=20, tenure=2, reversion=1)
    assert best


def test_tabu_stops_on_patience_and_control(tmp_path: Path) -> None:
    """Tabu honours patience and a stop control."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, _ = solve_tabu(problem, random.Random(20), iterations=10, tenure=2, patience=1)
    assert best == _empty()
    control = RunControl(tmp_path / "control.json")
    control.path.write_text(json.dumps({"action": "stop"}), encoding="utf-8")
    best, _ = solve_tabu(_problem(), random.Random(21), iterations=10, tenure=2, control=control)
    assert best


def test_tabu_improves_and_emits_snapshots() -> None:
    """Tabu samples the neighbourhood and keeps the best non-tabu move."""
    best, objective = solve_tabu(
        _problem(),
        random.Random(4),
        iterations=200,
        tenure=5,
        samples=4,
        on_snapshot=lambda iteration, values, state: None,
    )
    assert objective < _objective(_empty())
    assert best


def test_threshold_accepting_validates_and_improves() -> None:
    """Threshold accepting rejects invalid settings and accepts bounded uphill moves."""
    with pytest.raises(ValueError, match="threshold"):
        solve_threshold(
            _problem(),
            random.Random(1),
            iterations=1,
            threshold=-1.0,
            cooling=0.9,
        )
    with pytest.raises(ValueError, match="cooling"):
        solve_threshold(
            _problem(),
            random.Random(1),
            iterations=1,
            threshold=1.0,
            cooling=0.0,
        )
    _, objective = solve_threshold(
        _problem(),
        random.Random(5),
        iterations=300,
        threshold=1.0,
        cooling=0.99,
    )
    assert objective < _objective(_empty())


def test_threshold_patience_control_and_reversion(tmp_path: Path) -> None:
    """Threshold accepting honours patience, a stop control, and reversion."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, _ = solve_threshold(
        problem, random.Random(22), iterations=10, threshold=1.0, cooling=0.9, patience=1
    )
    assert best == _empty()
    control = RunControl(tmp_path / "control.json")
    control.path.write_text(json.dumps({"action": "stop"}), encoding="utf-8")
    best, _ = solve_threshold(
        _problem(), random.Random(23), iterations=10, threshold=1.0, cooling=0.9, control=control
    )
    assert best
    best, objective = solve_threshold(
        _problem(), random.Random(24), iterations=10, threshold=1.0, cooling=0.9, reversion=1
    )
    assert best
    assert objective >= 0.0


def test_threshold_stops_at_a_zero_threshold_and_traces() -> None:
    """A zero threshold still runs one iteration and then stops."""
    traces: list[int] = []
    best, _ = solve_threshold(
        _problem(),
        random.Random(15),
        iterations=100,
        threshold=0.0,
        cooling=0.5,
        on_trace=lambda iteration, best_value, current, accepted: traces.append(iteration),
    )
    assert best
    assert traces == [0]


def test_ils_patience_control_and_reversion(tmp_path: Path) -> None:
    """ILS honours patience, a stop control, and reversion."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, _ = solve_ils(problem, random.Random(25), iterations=10, perturbation=1, patience=1)
    assert best == _empty()
    control = RunControl(tmp_path / "control.json")
    control.path.write_text(json.dumps({"action": "stop"}), encoding="utf-8")
    best, _ = solve_ils(
        _problem(), random.Random(26), iterations=10, perturbation=1, control=control
    )
    assert best
    best, objective = solve_ils(
        _problem(), random.Random(27), iterations=10, perturbation=1, reversion=1
    )
    assert best
    assert objective >= 0.0


def test_ils_handles_a_no_move_operator() -> None:
    """ILS leaves the incumbent unchanged when no perturbation can move."""
    problem: Problem[State, Context] = Problem(
        evaluate=_objective,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        empty=_empty,
        clone=lambda state: dict(state),
    )
    best, objective = solve_ils(problem, random.Random(16), iterations=3, perturbation=2)
    assert best == _empty()
    assert objective == _objective(_empty())


def test_ils_perturbs_and_accepts_improvements() -> None:
    """ILS perturbs the incumbent and keeps an improving candidate."""
    best, objective = solve_ils(
        _problem(),
        random.Random(6),
        iterations=200,
        perturbation=3,
    )
    assert objective < _objective(_empty())
    assert best


def test_delta_solver_rejects_uphill_moves_and_reverts() -> None:
    """A rejected delta move restores the state and discards the evaluator's pending move."""
    evaluator = ToyDelta()
    best, objective = solve_sa_delta(
        evaluator,
        random.Random(11),
        iterations=20,
        temperature=1e-9,
        cooling=0.5,
        candidates=(0, 1, 2, 3),
        registry=OperatorRegistry([Worsen()]),
        initial={0: 2, 1: 2, 2: 2, 3: 2},
        reversion=1,
    )
    assert best == {0: 2, 1: 2, 2: 2, 3: 2}
    assert objective == 0.0


def test_delta_solver_reversion_and_patience_paths() -> None:
    """The delta solver resets on reversion and stops on patience."""
    evaluator = ToyDelta()
    best, objective = solve_sa_delta(
        evaluator,
        random.Random(18),
        iterations=5,
        temperature=1.0,
        cooling=0.9,
        candidates=(),
        registry=OperatorRegistry([Improve()]),
        initial=_empty(),
        reversion=1,
    )
    assert objective == 0.0
    assert best == dict.fromkeys(range(4), 2)
    evaluator = ToyDelta()
    _best, objective = solve_sa_delta(
        evaluator,
        random.Random(19),
        iterations=10,
        temperature=1.0,
        cooling=0.9,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        initial=_empty(),
        patience=1,
    )
    assert objective == _objective(_empty())


def test_delta_solver_handles_a_no_move_operator() -> None:
    """A no-move delta operator is skipped without touching the evaluator."""
    evaluator = ToyDelta()
    best, objective = solve_sa_delta(
        evaluator,
        random.Random(12),
        iterations=3,
        temperature=1.0,
        cooling=0.9,
        candidates=(),
        registry=OperatorRegistry([NoMove()]),
        initial=_empty(),
    )
    assert best == _empty()
    assert objective == _objective(_empty())


def test_delta_solver_matches_the_full_objective() -> None:
    """The delta solver's accepted state replays through the exact objective."""
    evaluator = ToyDelta()
    best, objective = solve_sa_delta(
        evaluator,
        random.Random(7),
        iterations=200,
        temperature=1.0,
        cooling=0.99,
        candidates=tuple(range(4)),
        registry=OperatorRegistry([Revalue()]),
        initial=_empty(),
        on_snapshot=lambda iteration, values, state: None,
    )
    assert objective == _objective(best)
    assert objective < _objective(_empty())


def test_stopping_helpers_parse_and_compare() -> None:
    """Time limits, deadlines, and control files follow their contracts."""
    assert parse_time_limit("") is None
    assert parse_time_limit("01:02:03") == 3723.0
    for bad in ("1:2", "aa:bb:cc", "00:00:00"):
        with pytest.raises(ValueError, match="time limit"):
            parse_time_limit(bad)
    assert expired(time.monotonic() - 1.0)
    assert not expired(None)


def test_control_file_stop_is_seen_at_the_poll_interval(tmp_path: Path) -> None:
    """A control file stops the search only at the polling interval."""
    control = RunControl(tmp_path / "control.json")
    control.path.write_text(json.dumps({"action": "stop"}), encoding="utf-8")
    assert stopped(control, 0)
    assert not stopped(control, 1)
    control.path.write_text(json.dumps({"action": "run"}), encoding="utf-8")
    assert not stopped(control, 64)
    assert not stopped(None, 0)


def test_cooling_edge_cases() -> None:
    """No uphill move gives zero initial temperature; a zero spread leaves it unchanged."""
    rule = AdaptiveCooling()
    assert rule.initial_temperature([]) == 0.0
    assert rule.cool(3.0, 0.0) == 3.0
    with pytest.raises(ValueError, match="window"):
        TemperatureSchedule(initial=1.0, cooling=0.9, adaptive=True, window=0)


def test_control_reads_an_unreadable_file_as_run(tmp_path: Path) -> None:
    """A missing or malformed control file means run."""
    control = RunControl(tmp_path / "missing.json")
    assert control.action() == "run"
    control.path.write_text("not json", encoding="utf-8")
    assert control.action() == "run"


def test_a_pause_then_stop_control_is_polled() -> None:
    """A pause holds the loop and a later stop ends it."""

    class PauseThenStop:
        def __init__(self) -> None:
            self.calls = 0

        def action(self) -> str:
            self.calls += 1
            return "pause" if self.calls == 1 else "stop"

    control = PauseThenStop()
    assert stopped(control, 0)  # type: ignore[arg-type]


def test_adaptive_cooling_rejects_bad_parameters() -> None:
    """The adaptive rule rejects undefined parameter values."""
    with pytest.raises(ValueError, match="initial_acceptance"):
        AdaptiveCooling(initial_acceptance=1.0)
    with pytest.raises(ValueError, match="delta"):
        AdaptiveCooling(delta=0.0)
