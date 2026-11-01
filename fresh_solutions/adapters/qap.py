"""Quadratic assignment adapter and QAPLIB parser."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..contracts import Change, Evaluation
from ._permutation import order_crossover, swap, validate_permutation


class QuadraticAssignment:
    """Quadratic assignment problem with permutation-preserving swaps.

    Parameters
    ----------
    flows : sequence of sequence of float
        Square flow matrix between facilities.
    distances : sequence of sequence of float
        Square distance matrix between locations.
    """

    name = "qap-v1"

    def __init__(
        self,
        flows: Sequence[Sequence[float]],
        distances: Sequence[Sequence[float]],
    ) -> None:
        size = len(flows)
        if (
            size < 2
            or len(distances) != size
            or any(len(row) != size for matrix in (flows, distances) for row in matrix)
        ):
            raise ValueError("flows and distances must be equally sized square matrices")
        self.flows = tuple(tuple(float(value) for value in row) for row in flows)
        self.distances = tuple(tuple(float(value) for value in row) for row in distances)

    @classmethod
    def from_qaplib(cls, path: str | Path) -> QuadraticAssignment:
        """Parse a Chen-Kost/Malik QAPLIB ``.dat`` instance.

        Parameters
        ----------
        path : str or Path
            QAPLIB instance path.

        Returns
        -------
        QuadraticAssignment
            Parsed instance.

        Raises
        ------
        ValueError
            When the file is not a complete QAPLIB instance.
        """
        tokens = Path(path).read_text(encoding="utf-8").split()
        if not tokens:
            raise ValueError("empty QAPLIB instance")
        try:
            size = int(tokens[0])
            values = [float(token) for token in tokens[1:]]
        except ValueError as error:
            raise ValueError("QAPLIB instance contains a non-numeric token") from error
        if len(values) != 2 * size * size:
            raise ValueError("QAPLIB instance has the wrong number of entries")
        flows = [values[row * size : (row + 1) * size] for row in range(size)]
        offset = size * size
        distances = [values[offset + row * size : offset + (row + 1) * size] for row in range(size)]
        return cls(flows, distances)

    @property
    def variable_count(self) -> int:
        """Return the number of locations."""
        return len(self.flows)

    def option_count(self, variable: int) -> int:
        """Return the number of facilities assignable to one location."""
        self._check_variable(variable)
        return len(self.flows)

    def option_at(self, variable: int, option: int) -> int:
        """Return one facility option."""
        self._check_variable(variable)
        if option < 0 or option >= len(self.flows):
            raise IndexError(option)
        return option

    def initial_assignment(self) -> dict[int, int]:
        """Return the identity permutation."""
        return {location: location for location in range(self.variable_count)}

    def random_assignment(self, rng: random.Random) -> dict[int, int]:
        """Return a random permutation."""
        options = list(range(self.variable_count))
        rng.shuffle(options)
        return dict(enumerate(options))

    def mutate(
        self,
        assignment: Mapping[int, int],
        rate: float,
        rng: random.Random,
    ) -> dict[int, int]:
        """Return a permutation-preserving swap mutation."""
        values = validate_permutation(assignment, self.variable_count)
        for variable in range(self.variable_count):
            if rng.random() < rate:
                other = rng.randrange(self.variable_count)
                values[variable], values[other] = values[other], values[variable]
        return values

    def crossover(
        self,
        left: Mapping[int, int],
        right: Mapping[int, int],
        rng: random.Random,
    ) -> dict[int, int]:
        """Return a permutation-preserving order crossover."""
        return order_crossover(left, right, rng)

    def evaluate(self, assignment: Mapping[int, int]) -> Evaluation:
        """Return the QAP flow-distance objective."""
        values = validate_permutation(assignment, self.variable_count)
        objective = sum(
            self.flows[first][second] * self.distances[values[first]][values[second]]
            for first in range(self.variable_count)
            for second in range(self.variable_count)
        )
        return Evaluation(objective=float(objective), feasible=True)

    def evaluate_batch(self, assignments: Sequence[Mapping[int, int]]) -> list[Evaluation]:
        """Return exact QAP evaluations."""
        return [self.evaluate(assignment) for assignment in assignments]

    def propose(self, assignment: Mapping[int, int], rng: random.Random) -> Change | None:
        """Propose a facility swap, or None for a one-location problem."""
        values = validate_permutation(assignment, self.variable_count)
        variable = rng.randrange(self.variable_count)
        other = rng.choice(
            [option for option in range(self.variable_count) if option != values[variable]]
        )
        return Change(variable=variable, before=values[variable], after=other)

    def apply(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Apply a facility swap."""
        return swap(assignment, change, before=True)

    def undo(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Undo a facility swap."""
        return swap(assignment, change, before=False)

    def _check_variable(self, variable: int) -> None:
        if variable < 0 or variable >= self.variable_count:
            raise IndexError(variable)
