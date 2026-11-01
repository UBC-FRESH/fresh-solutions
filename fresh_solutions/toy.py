"""A small graph-colouring adapter used to exercise the Fresh Solutions contract."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

from .contracts import Change, Evaluation

Colour = int


class GraphColouring:
    """A graph-colouring problem with a conflict-count objective.

    Parameters
    ----------
    node_count : int
        Number of graph nodes; each node is one variable.
    edges : sequence of tuple of int
        Undirected edges between node positions.
    colours : sequence of int, optional
        Allowed colour values. Defaults to three colours.
    """

    name = "graph-colouring-v1"

    def __init__(
        self,
        node_count: int,
        edges: Sequence[tuple[int, int]],
        colours: Sequence[int] = (0, 1, 2),
    ) -> None:
        if node_count < 1:
            raise ValueError("node_count must be positive")
        if not colours:
            raise ValueError("at least one colour is required")
        if any(node < 0 or node >= node_count for edge in edges for node in edge):
            raise ValueError("an edge refers to an unknown node")
        self.node_count = int(node_count)
        self.edges = tuple((int(left), int(right)) for left, right in edges)
        self.colours = tuple(int(colour) for colour in colours)

    @property
    def variable_count(self) -> int:
        """Return the number of nodes."""
        return self.node_count

    def option_count(self, variable: int) -> int:
        """Return the number of colours available to one node."""
        self._check_variable(variable)
        return len(self.colours)

    def option_at(self, variable: int, option: int) -> Colour:
        """Return one colour by option index."""
        self._check_variable(variable)
        if option < 0 or option >= len(self.colours):
            raise IndexError(option)
        return self.colours[option]

    def initial_assignment(self) -> dict[int, int]:
        """Return every node assigned to the first colour."""
        return dict.fromkeys(range(self.node_count), 0)

    def random_assignment(self, rng: random.Random) -> dict[int, int]:
        """Return a random colour assignment."""
        return {node: rng.randrange(len(self.colours)) for node in range(self.node_count)}

    def mutate(
        self,
        assignment: Mapping[int, int],
        rate: float,
        rng: random.Random,
    ) -> dict[int, int]:
        """Return a mutation that may change any node colour."""
        values = self._assignment(assignment)
        for node in range(self.node_count):
            if rng.random() < rate:
                values[node] = rng.randrange(len(self.colours))
        return values

    def crossover(
        self,
        left: Mapping[int, int],
        right: Mapping[int, int],
        rng: random.Random,
    ) -> dict[int, int]:
        """Return a uniform crossover of two colourings."""
        left_values = self._assignment(left)
        right_values = self._assignment(right)
        return {
            node: left_values[node] if rng.random() < 0.5 else right_values[node]
            for node in range(self.node_count)
        }

    def evaluate(self, assignment: Mapping[int, int]) -> Evaluation:
        """Return the number of monochromatic edges as the objective."""
        values = self._assignment(assignment)
        conflicts = sum(1 for left, right in self.edges if values[left] == values[right])
        return Evaluation(
            objective=float(conflicts),
            feasible=conflicts == 0,
            details={"conflicts": float(conflicts)},
        )

    def evaluate_batch(self, assignments: Sequence[Mapping[int, int]]) -> list[Evaluation]:
        """Return exact evaluations for a batch."""
        return [self.evaluate(assignment) for assignment in assignments]

    def propose(self, assignment: Mapping[int, int], rng: random.Random) -> Change | None:
        """Propose a colour change for one node, or None for a one-colour problem."""
        if len(self.colours) < 2:
            return None
        values = self._assignment(assignment)
        variable = rng.randrange(self.node_count)
        before = values[variable]
        choices = [option for option in range(len(self.colours)) if option != before]
        after = rng.choice(choices)
        return Change(variable=variable, before=before, after=after)

    def apply(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Return a copy with the proposed option applied."""
        values = self._assignment(assignment)
        if values[change.variable] != change.before:
            raise ValueError("change.before does not match the assignment")
        values[change.variable] = change.after
        return values

    def undo(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Return a copy with the change reversed."""
        values = self._assignment(assignment)
        if values[change.variable] != change.after:
            raise ValueError("change.after does not match the assignment")
        values[change.variable] = change.before
        return values

    def _assignment(self, assignment: Mapping[int, int]) -> dict[int, int]:
        if set(assignment) != set(range(self.node_count)):
            raise ValueError("assignment must cover every node")
        values = {int(variable): int(option) for variable, option in assignment.items()}
        for variable, option in values.items():
            if option < 0 or option >= len(self.colours):
                raise ValueError(f"node {variable} has an invalid option {option}")
        return values

    def _check_variable(self, variable: int) -> None:
        if variable < 0 or variable >= self.node_count:
            raise IndexError(variable)
