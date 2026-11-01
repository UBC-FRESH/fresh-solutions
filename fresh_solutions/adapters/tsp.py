"""Symmetric TSP adapter and TSPLIB parser."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..contracts import Change, Evaluation
from ._permutation import order_crossover, reverse_segment, validate_permutation


def _nint(value: float) -> float:
    """Return the TSPLIB nearest-integer convention."""
    return float(int(value + 0.5))


def _coordinate_distance(
    edge_type: str,
    first: tuple[float, float],
    second: tuple[float, float],
) -> float:
    """Return one TSPLIB coordinate distance."""
    dx = first[0] - second[0]
    dy = first[1] - second[1]
    if edge_type == "EUC_2D":
        return _nint(math.hypot(dx, dy))
    if edge_type == "CEIL_2D":
        return float(math.ceil(math.hypot(dx, dy)))
    if edge_type == "ATT":
        candidate = _nint(math.sqrt((dx * dx + dy * dy) / 10.0))
        return candidate + 1.0 if candidate < math.sqrt((dx * dx + dy * dy) / 10.0) else candidate
    if edge_type == "GEO":
        pi = 3.141592
        radius = 6378.388
        latitude_first = pi * (first[0] + 5.0 * (first[0] - int(first[0])) / 3.0) / 180.0
        latitude_second = pi * (second[0] + 5.0 * (second[0] - int(second[0])) / 3.0) / 180.0
        longitude_first = pi * (first[1] + 5.0 * (first[1] - int(first[1])) / 3.0) / 180.0
        longitude_second = pi * (second[1] + 5.0 * (second[1] - int(second[1])) / 3.0) / 180.0
        q1 = math.cos(longitude_first - longitude_second)
        q2 = math.cos(latitude_first - latitude_second)
        q3 = math.cos(latitude_first + latitude_second)
        return float(int(radius * math.acos(0.5 * ((1.0 + q1) * q2 - (1.0 - q1) * q3)) + 1.0))
    raise ValueError(f"unsupported coordinate edge type: {edge_type}")


def _explicit_distances(
    values: list[float],
    dimension: int,
    edge_format: str,
) -> list[list[float]]:
    """Build a symmetric matrix from an explicit TSPLIB section."""
    matrix = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    if edge_format == "FULL_MATRIX":
        if len(values) != dimension * dimension:
            raise ValueError("explicit matrix has the wrong number of values")
        for first in range(dimension):
            for second in range(dimension):
                matrix[first][second] = values[first * dimension + second]
        return matrix
    index = 0
    formats = {
        "LOWER_DIAG_ROW": lambda first, second: second <= first,
        "UPPER_DIAG_ROW": lambda first, second: second >= first,
        "LOWER_ROW": lambda first, second: second < first,
        "UPPER_ROW": lambda first, second: second > first,
    }
    predicate = formats.get(edge_format)
    if predicate is None:
        raise ValueError(f"unsupported explicit edge-weight format: {edge_format}")
    for first in range(dimension):
        for second in range(dimension):
            if predicate(first, second):
                if index >= len(values):
                    raise ValueError("explicit matrix has too few values")
                matrix[first][second] = values[index]
                matrix[second][first] = values[index]
                index += 1
    if index != len(values):
        raise ValueError("explicit matrix has the wrong number of values")
    return matrix


class TravellingSalesman:
    """Symmetric TSP with position-to-city permutation and swap moves.

    Parameters
    ----------
    distances : sequence of sequence of float
        Square symmetric distance matrix.
    """

    name = "tsp-v1"

    def __init__(self, distances: Sequence[Sequence[float]]) -> None:
        size = len(distances)
        if size < 2 or any(len(row) != size for row in distances):
            raise ValueError("distances must be a square matrix with at least two cities")
        self.distances = tuple(tuple(float(value) for value in row) for row in distances)

    @classmethod
    def from_tsplib(cls, path: str | Path) -> TravellingSalesman:
        """Parse a TSPLIB TSP instance.

        Supports coordinate instances with ``EUC_2D``, ``CEIL_2D``, ``ATT``, and
        ``GEO`` edge weights, plus explicit symmetric matrices in the common
        TSPLIB formats.

        Parameters
        ----------
        path : str or Path
            TSPLIB instance path.

        Returns
        -------
        TravellingSalesman
            Parsed instance.

        Raises
        ------
        ValueError
            When the file is missing required data or uses an unsupported format.
        """
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        dimension: int | None = None
        edge_type = "EUC_2D"
        edge_format = ""
        coordinates: dict[int, tuple[float, float]] = {}
        explicit: list[float] = []
        section = ""
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            upper = stripped.upper()
            if upper.startswith("DIMENSION"):
                dimension = int(stripped.split(":")[-1])
            elif upper.startswith("EDGE_WEIGHT_TYPE"):
                edge_type = stripped.split(":")[-1].strip().upper()
            elif upper.startswith("EDGE_WEIGHT_FORMAT"):
                edge_format = stripped.split(":")[-1].strip().upper()
            elif upper in {"NODE_COORD_SECTION", "EDGE_WEIGHT_SECTION"}:
                section = upper
            elif upper == "EOF":
                break
            elif upper in {
                "DISPLAY_DATA_SECTION",
                "DEPOT_SECTION",
                "DEMAND_SECTION",
                "FIXED_EDGES_SECTION",
            }:
                section = ""
            elif section == "NODE_COORD_SECTION":
                parts = stripped.split()
                if len(parts) >= 3:
                    coordinates[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif section == "EDGE_WEIGHT_SECTION":
                explicit.extend(float(value) for value in stripped.split())
        if dimension is None:
            raise ValueError("TSPLIB instance is missing DIMENSION")
        if edge_type in {"EUC_2D", "CEIL_2D", "ATT", "GEO"}:
            if len(coordinates) != dimension:
                raise ValueError("TSPLIB instance is missing coordinates")
            ordered = [coordinates[index] for index in range(1, dimension + 1)]
            distances = [
                [_coordinate_distance(edge_type, first, second) for second in ordered]
                for first in ordered
            ]
        elif edge_type == "EXPLICIT":
            distances = _explicit_distances(explicit, dimension, edge_format)
        else:
            raise ValueError(f"unsupported TSPLIB edge type: {edge_type}")
        return cls(distances)

    @property
    def variable_count(self) -> int:
        """Return the number of tour positions."""
        return len(self.distances)

    def option_count(self, variable: int) -> int:
        """Return the number of cities available at one position."""
        self._check_variable(variable)
        return len(self.distances)

    def option_at(self, variable: int, option: int) -> int:
        """Return one city option."""
        self._check_variable(variable)
        if option < 0 or option >= len(self.distances):
            raise IndexError(option)
        return option

    def initial_assignment(self) -> dict[int, int]:
        """Return the identity tour."""
        return {position: position for position in range(self.variable_count)}

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
                start, end = (variable, other) if variable <= other else (other, variable)
                segment = [values[position] for position in range(start, end + 1)]
                for offset, city in enumerate(reversed(segment)):
                    values[start + offset] = city
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
        """Return the closed-tour distance."""
        values = validate_permutation(assignment, self.variable_count)
        objective = sum(
            self.distances[values[position]][values[(position + 1) % self.variable_count]]
            for position in range(self.variable_count)
        )
        return Evaluation(objective=float(objective), feasible=True)

    def evaluate_batch(self, assignments: Sequence[Mapping[int, int]]) -> list[Evaluation]:
        """Return exact TSP evaluations."""
        return [self.evaluate(assignment) for assignment in assignments]

    def propose(self, assignment: Mapping[int, int], rng: random.Random) -> Change | None:
        """Propose a city swap, or None for a one-city problem."""
        values = validate_permutation(assignment, self.variable_count)
        if rng.random() < 0.5:
            variable = rng.randrange(self.variable_count)
            other = rng.choice(
                [option for option in range(self.variable_count) if option != values[variable]]
            )
            return Change(variable=variable, before=values[variable], after=other, kind="2opt")
        size = rng.randint(1, min(3, self.variable_count - 1))
        start = rng.randrange(self.variable_count - size + 1)
        segment = {values[position] for position in range(start, start + size)}
        destination = rng.choice(
            [city for city in range(self.variable_count) if city not in segment]
        )
        return Change(
            variable=start,
            before=values[start],
            after=destination,
            kind="oropt",
            size=size,
        )

    def apply(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Apply a 2-opt reversal or Or-opt segment relocation."""
        if change.kind == "oropt":
            return self._move_segment(assignment, change, undo=False)
        return reverse_segment(assignment, change, before=True)

    def undo(self, assignment: Mapping[int, int], change: Change) -> dict[int, int]:
        """Undo a 2-opt reversal or Or-opt segment relocation."""
        if change.kind == "oropt":
            return self._move_segment(assignment, change, undo=True)
        return reverse_segment(assignment, change, before=False)

    def _move_segment(
        self,
        assignment: Mapping[int, int],
        change: Change,
        *,
        undo: bool,
    ) -> dict[int, int]:
        """Move or restore an Or-opt segment."""
        values = validate_permutation(assignment, self.variable_count)
        sequence = [values[position] for position in range(self.variable_count)]
        if not undo:
            if sequence[change.variable] != change.before:
                raise ValueError("change does not match the assignment")
            start = change.variable
            segment = sequence[start : start + change.size]
            remaining = sequence[:start] + sequence[start + change.size :]
            try:
                destination = remaining.index(change.after)
            except ValueError as error:
                raise ValueError("Or-opt destination is not present") from error
            return dict(
                enumerate(remaining[: destination + 1] + segment + remaining[destination + 1 :])
            )
        try:
            current_start = sequence.index(change.before)
        except ValueError as error:
            raise ValueError("Or-opt segment is not present") from error
        segment = sequence[current_start : current_start + change.size]
        remaining = sequence[:current_start] + sequence[current_start + change.size :]
        return dict(
            enumerate(remaining[: change.variable] + segment + remaining[change.variable :])
        )

    def _check_variable(self, variable: int) -> None:
        if variable < 0 or variable >= self.variable_count:
            raise IndexError(variable)
