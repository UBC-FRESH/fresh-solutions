"""The problem boundary for the shared metaheuristic kernel.

A problem supplies an objective, an adapter-owned context, and an operator registry. The
state representation belongs to the adapter: a forest schedule, a machine timetable, or a
permutation all fit, as long as the operators can mutate it and report an undo record.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Hashable, Mapping
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from .operators import OperatorRegistry

State = TypeVar("State")
Context = TypeVar("Context")


@dataclass
class Problem(Generic[State, Context]):
    """The problem a kernel solver searches.

    Attributes
    ----------
    evaluate : callable
        The exact objective evaluator (lower is better).
    candidates : Context
        Adapter-owned move context, such as candidate moves or scenario lookups.
    registry : OperatorRegistry
        The neighbourhood operators.
    snapshot : callable or None, optional
        Return the realized display values for a state, for a live view. When omitted, a
        solver that would otherwise emit a snapshot sends an empty mapping.
    empty : callable or None, optional
        Return a fresh empty state. Required when a solver is called without an initial
        state.
    clone : callable or None, optional
        Return an independent copy of a state. When omitted the kernel uses
        :func:`copy.deepcopy`; adapters with a cheap copy should supply it.
    signature : callable or None, optional
        Return a hashable tabu signature for a move from ``before`` to ``after``. When
        omitted the kernel diffs mappings by key, using ``repr`` for values.
    """

    evaluate: Callable[[State], float]
    candidates: Context
    registry: OperatorRegistry[State, Context]
    snapshot: Callable[[State], Mapping[Any, float]] | None = None
    empty: Callable[[], State] | None = None
    clone: Callable[[State], State] | None = None
    signature: Callable[[State, State], Hashable] | None = None


def clone_state(problem: Problem[State, Context], state: State) -> State:
    """Return an independent copy of ``state``.

    Parameters
    ----------
    problem : Problem
        The problem, whose ``clone`` hook may override the default.
    state : State
        The state to copy.

    Returns
    -------
    State
        The copy.
    """
    if problem.clone is not None:
        return problem.clone(state)
    return copy.deepcopy(state)


def state_signature(
    problem: Problem[State, Context],
    before: State,
    after: State,
) -> Hashable:
    """Return a hashable signature for a move from ``before`` to ``after``.

    Parameters
    ----------
    problem : Problem
        The problem, whose ``signature`` hook may override the default.
    before : State
        The state before the move.
    after : State
        The state after the move.

    Returns
    -------
    Hashable
        The adapter's signature when supplied, otherwise a key/value diff for mappings.
    """
    if problem.signature is not None:
        return problem.signature(before, after)
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        keys = set(before) | set(after)
        return frozenset(
            (key, repr(after.get(key))) for key in keys if before.get(key) != after.get(key)
        )
    return (repr(before), repr(after))
