"""Problem-adapter and replay contracts for Fresh Solutions.

The engine and the problem are separated by this module. A problem adapter supplies discrete
variables, their options, exact and batched evaluation, a feasibility rule, and move/undo
operations. The engine never imports a problem-specific package.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Evaluation:
    """One exact or batched objective result.

    Parameters
    ----------
    objective : float
        Scalar objective; lower is better.
    feasible : bool
        Whether the assignment satisfies the problem's hard rules.
    details : mapping of str to float, optional
        Optional diagnostic values, such as a violation count.
    """

    objective: float
    feasible: bool
    details: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Change:
    """One reversible assignment change.

    Parameters
    ----------
    variable : int
        Variable position.
    before : int
        Previous option index.
    after : int
        Proposed option index.
    """

    variable: int
    before: int
    after: int


@dataclass(frozen=True)
class EvidenceRecord:
    """A replayable record for one incumbent.

    Parameters
    ----------
    instance : str
        Stable instance identifier.
    adapter : str
        Adapter name and version.
    assignment : mapping of int to int
        Variable-to-option assignment.
    objective : float
        Claimed objective.
    feasible : bool
        Claimed feasibility.
    seed : int
        Random seed used to produce the assignment.
    metadata : mapping of str to object, optional
        Provenance such as hardware, software, and configuration.
    """

    instance: str
    adapter: str
    assignment: Mapping[int, int]
    objective: float
    feasible: bool
    seed: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready record.

        Returns
        -------
        dict of str to object
            The record with sorted assignment keys.
        """
        return {
            "instance": self.instance,
            "adapter": self.adapter,
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "feasible": self.feasible,
            "seed": self.seed,
            "metadata": dict(self.metadata),
        }

    def verify(self, adapter: ProblemAdapter) -> Evaluation:
        """Replay the assignment through an adapter and return its exact evaluation.

        Parameters
        ----------
        adapter : ProblemAdapter
            Adapter for the same instance.

        Returns
        -------
        Evaluation
            The exact evaluation of the recorded assignment.

        Raises
        ------
        ValueError
            When the adapter name or variable set does not match the record.
        """
        if adapter.name != self.adapter:
            raise ValueError(f"adapter mismatch: {self.adapter!r} != {adapter.name!r}")
        if set(self.assignment) != set(range(adapter.variable_count)):
            raise ValueError("record assignment does not cover every variable")
        return adapter.evaluate(self.assignment)


@runtime_checkable
class ProblemAdapter(Protocol):
    """Protocol implemented by every Fresh Solutions problem."""

    name: str

    @property
    def variable_count(self) -> int:
        """Return the number of discrete variables."""
        ...

    def option_count(self, variable: int) -> int:
        """Return the number of options for one variable."""
        ...

    def option_at(self, variable: int, option: int) -> object:
        """Return the value of one option."""
        ...

    def initial_assignment(self) -> dict[int, int]:
        """Return a complete starting assignment."""
        ...

    def random_assignment(self, rng: random.Random) -> dict[int, int]:
        """Return a random valid assignment."""
        ...

    def mutate(
        self,
        assignment: Mapping[int, int],
        rate: float,
        rng: random.Random,
    ) -> dict[int, int]:
        """Return a valid mutated assignment."""
        ...

    def crossover(
        self,
        left: Mapping[int, int],
        right: Mapping[int, int],
        rng: random.Random,
    ) -> dict[int, int]:
        """Return a valid child assignment."""
        ...

    def evaluate(self, assignment: Mapping[int, int]) -> Evaluation:
        """Return the exact objective and feasibility of one assignment."""
        ...

    def evaluate_batch(self, assignments: Sequence[Mapping[int, int]]) -> list[Evaluation]:
        """Return exact evaluations for a batch of assignments."""
        ...

    def propose(self, assignment: Mapping[int, int], rng: random.Random) -> Change | None:
        """Propose one reversible move, or None when the assignment cannot move."""
        ...

    def apply(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Return a new assignment with one change applied."""
        ...

    def undo(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Return a new assignment with one change reversed."""
        ...
