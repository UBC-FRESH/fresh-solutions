"""Exact CPU search and resident-assignment primitives for Fresh Solutions."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from .contracts import Change, Evaluation, ProblemAdapter


@dataclass(frozen=True)
class SearchConfig:
    """Configuration for the exact CPU local search.

    Parameters
    ----------
    iterations : int, optional
        Number of proposals. Defaults to 1,000.
    seed : int, optional
        Random seed. Defaults to 1.
    temperature : float, optional
        Initial annealing temperature. Defaults to 1.0.
    cooling : float, optional
        Multiplicative cooling factor in ``(0, 1]``. Defaults to 0.999.
    """

    iterations: int = 1000
    seed: int = 1
    temperature: float = 1.0
    cooling: float = 0.999

    def __post_init__(self) -> None:
        """Validate search settings."""
        if self.iterations < 0:
            raise ValueError("iterations must not be negative")
        if self.temperature <= 0.0:
            raise ValueError("temperature must be positive")
        if not 0.0 < self.cooling <= 1.0:
            raise ValueError("cooling must be in (0, 1]")


@dataclass(frozen=True)
class SearchResult:
    """Best assignment found by one exact CPU search.

    Parameters
    ----------
    assignment : mapping of int to int
        Best variable-to-option assignment.
    objective : float
        Best exact objective.
    feasible : bool
        Best assignment's hard feasibility.
    evaluations : int
        Number of exact evaluations.
    accepted : int
        Number of accepted proposals.
    history : tuple of float
        Best-ever objective after each iteration.
    """

    assignment: Mapping[int, int]
    objective: float
    feasible: bool
    evaluations: int
    accepted: int
    history: tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready result.

        Returns
        -------
        dict of str to object
            Result with sorted assignment keys.
        """
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "feasible": self.feasible,
            "evaluations": self.evaluations,
            "accepted": self.accepted,
            "history": list(self.history),
        }


class ResidentState(Protocol):
    """Minimal resident-state protocol for exact apply/undo search."""

    def apply(self, change: Change) -> None:
        """Apply one change to the resident state."""
        ...

    def undo(self, change: Change) -> None:
        """Undo one change and restore the resident state."""
        ...

    def evaluate(self) -> Evaluation:
        """Return the exact evaluation of the resident state."""
        ...


class ResidentAssignment:
    """A resident assignment backed by an adapter's exact apply/undo operations.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter.
    assignment : mapping of int to int or None, optional
        Starting assignment. None uses the adapter's initial assignment.
    """

    def __init__(
        self,
        adapter: ProblemAdapter,
        assignment: Mapping[int, int] | None = None,
    ) -> None:
        self.adapter = adapter
        self._assignment = dict(adapter.initial_assignment() if assignment is None else assignment)

    @property
    def assignment(self) -> Mapping[int, int]:
        """Return the current assignment as a read-only mapping copy."""
        return dict(self._assignment)

    def apply(self, change: Change) -> None:
        """Apply one change through the adapter."""
        self._assignment = self.adapter.apply(self._assignment, change)

    def undo(self, change: Change) -> None:
        """Undo one change through the adapter."""
        self._assignment = self.adapter.undo(self._assignment, change)

    def evaluate(self) -> Evaluation:
        """Return the exact evaluation of the current assignment."""
        return self.adapter.evaluate(self._assignment)


def run_local_search(
    adapter: ProblemAdapter,
    config: SearchConfig,
    *,
    initial: Mapping[int, int] | None = None,
) -> SearchResult:
    """Run exact simulated-annealing local search over adapter proposals.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter supplying options, proposals, exact evaluation, and apply/undo.
    config : SearchConfig
        Search settings.
    initial : mapping of int to int or None, optional
        Starting assignment. None uses the adapter's initial assignment.

    Returns
    -------
    SearchResult
        Best assignment, exact objective, feasibility, counters, and history.
    """
    rng = random.Random(config.seed)
    state = ResidentAssignment(adapter, initial)
    current = state.evaluate()
    best = current
    best_assignment = state.assignment
    accepted = 0
    evaluations = 1
    history: list[float] = []
    temperature = config.temperature
    for _ in range(config.iterations):
        change = adapter.propose(state.assignment, rng)
        if change is None:
            history.append(best.objective)
            continue
        state.apply(change)
        candidate = state.evaluate()
        evaluations += 1
        delta = candidate.objective - current.objective
        if delta <= 0.0 or rng.random() < math.exp(-delta / max(temperature, 1e-12)):
            current = candidate
            accepted += 1
            if candidate.objective < best.objective:
                best = candidate
                best_assignment = state.assignment
        else:
            state.undo(change)
        history.append(best.objective)
        temperature *= config.cooling
    return SearchResult(
        assignment=best_assignment,
        objective=best.objective,
        feasible=best.feasible,
        evaluations=evaluations,
        accepted=accepted,
        history=tuple(history),
    )
