"""Problem-agnostic neighbourhood operators and their weighted registry.

The kernel never imports a problem-specific package. An adapter supplies a state object,
a context object (candidate moves, lookup tables, or anything else its operators need),
and an operator set. An operator mutates the state in place and returns an undo record, or
returns ``None`` when it cannot move. The undo record is keyed by the adapter's decision
unit, so the adapter keeps ownership of the state representation.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Generic, Protocol, TypeVar

State = TypeVar("State")
Context = TypeVar("Context", contravariant=True)
Key = TypeVar("Key")
Value = TypeVar("Value")

Undo = Mapping[int, object]


class Operator(Protocol, Generic[State, Context]):
    """One neighbourhood move over an adapter-owned state.

    Attributes
    ----------
    name : str
        The operator name, as it appears in telemetry and run summaries.
    weight : float
        The relative probability of selecting the operator. A non-positive weight disables
        it in a weighted registry.
    """

    name: str
    weight: float

    def propose_inplace(self, state: State, rng: random.Random, context: Context) -> Undo | None:
        """Mutate ``state`` in place and return the previous values of the touched units.

        Parameters
        ----------
        state : State
            The adapter-owned state. The operator mutates it directly.
        rng : random.Random
            The random source.
        context : Context
            Adapter-owned move context.

        Returns
        -------
        Undo or None
            The previous value per touched decision unit (``None`` means the unit was
            absent), or ``None`` when the operator cannot move.
        """
        ...

    def apply(self, state: State, rng: random.Random, context: Context) -> State | None:
        """Return a modified copy of ``state``, or ``None`` when the operator cannot move.

        Parameters
        ----------
        state : State
            The state to copy and modify.
        rng : random.Random
            The random source.
        context : Context
            Adapter-owned move context.

        Returns
        -------
        State or None
            The modified copy, or ``None``.
        """
        ...


def restore_state(state: object, undo: Mapping[int, object]) -> None:
    """Restore a state that is known at runtime to be a mutable mapping.

    Parameters
    ----------
    state : object
        The mutated state. It must implement the mutable-mapping protocol.
    undo : Mapping
        The previous value per touched unit.

    Raises
    ------
    TypeError
        When ``state`` is not a mutable mapping.
    """
    if not isinstance(state, MutableMapping):
        raise TypeError("the state must be a mutable mapping")
    restore(state, undo)


def restore(state: MutableMapping[Key, Value], undo: Mapping[Key, Value | None]) -> None:
    """Undo an in-place move, restoring each touched unit's previous value.

    Parameters
    ----------
    state : MutableMapping
        The mutated state.
    undo : Mapping
        The previous value per touched unit. ``None`` means the unit was absent.
    """
    for key, previous in undo.items():
        if previous is None:
            state.pop(key, None)
        else:
            state[key] = previous


class OperatorRegistry(Generic[State, Context]):
    """A weighted set of operators.

    Parameters
    ----------
    operators : sequence of Operator, optional
        The operators to choose between. When omitted the registry is empty and
        :meth:`pick` raises.
    """

    def __init__(self, operators: Sequence[Operator[State, Context]] | None = None) -> None:
        self._operators: list[Operator[State, Context]] = list(operators or ())

    @property
    def operators(self) -> list[Operator[State, Context]]:
        """Return the registered operators in selection order.

        Returns
        -------
        list of Operator
            A copy of the operator list.
        """
        return list(self._operators)

    def names(self) -> list[str]:
        """Return the operator names in registration order.

        Returns
        -------
        list of str
            The names.
        """
        return [operator.name for operator in self._operators]

    def weights(self) -> dict[str, float]:
        """Return the operator weights by name.

        Returns
        -------
        dict of str to float
            The selection weight per operator name.
        """
        return {operator.name: operator.weight for operator in self._operators}

    def pick(self, rng: random.Random) -> Operator[State, Context]:
        """Return a weighted-random operator.

        Parameters
        ----------
        rng : random.Random
            The random source.

        Returns
        -------
        Operator
            The chosen operator.

        Raises
        ------
        ValueError
            When the registry is empty or every weight is non-positive.
        """
        total = sum(operator.weight for operator in self._operators if operator.weight > 0.0)
        if total <= 0.0:
            raise ValueError("operator registry has no positive weight")
        threshold = rng.random() * total
        for operator in self._operators:
            if operator.weight <= 0.0:
                continue
            threshold -= operator.weight
            if threshold <= 0.0:
                return operator
        return next(operator for operator in reversed(self._operators) if operator.weight > 0.0)
