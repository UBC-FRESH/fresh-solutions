"""Shared permutation helpers for public-library adapters."""

from __future__ import annotations

import random
from collections.abc import Mapping

from ..contracts import Change


def validate_permutation(assignment: Mapping[int, int], size: int) -> dict[int, int]:
    """Validate that an assignment is a complete permutation.

    Parameters
    ----------
    assignment : mapping of int to int
        Variable-to-option assignment.
    size : int
        Number of variables/options.

    Returns
    -------
    dict of int to int
        Normalized assignment.

    Raises
    ------
    ValueError
        When the assignment is incomplete, out of range, or not a permutation.
    """
    if set(assignment) != set(range(size)):
        raise ValueError("assignment must cover every variable")
    values = {int(variable): int(option) for variable, option in assignment.items()}
    if set(values.values()) != set(range(size)):
        raise ValueError("assignment must be a permutation")
    return values


def swap(assignment: Mapping[int, int], change: Change, *, before: bool) -> dict[int, int]:
    """Apply or undo a swap encoded by one variable's before/after options.

    Parameters
    ----------
    assignment : mapping of int to int
        Current permutation.
    change : Change
        Proposed swap.
    before : bool
        True to apply, False to undo.

    Returns
    -------
    dict of int to int
        New permutation.

    Raises
    ------
    ValueError
        When the change does not match the current assignment.
    """
    values = dict(assignment)
    expected = change.before if before else change.after
    actual = values[change.variable]
    if actual != expected:
        raise ValueError("change does not match the assignment")
    other_option = change.after if before else change.before
    other_variable = next(
        (variable for variable, option in values.items() if option == other_option), None
    )
    if other_variable is None:
        raise ValueError("swap target is not present")
    values[change.variable], values[other_variable] = (
        values[other_variable],
        values[change.variable],
    )
    return values


def order_crossover(
    left: Mapping[int, int],
    right: Mapping[int, int],
    rng: random.Random,
) -> dict[int, int]:
    """Return a permutation-preserving order crossover.

    Parameters
    ----------
    left : mapping of int to int
        First parent permutation.
    right : mapping of int to int
        Second parent permutation.
    rng : random.Random
        Random source.

    Returns
    -------
    dict of int to int
        Child permutation.
    """
    size = len(left)
    values_left = validate_permutation(left, size)
    values_right = validate_permutation(right, size)
    cut = rng.randrange(size)
    head = [values_left[index] for index in range(cut)]
    used = set(head)
    tail = [values_right[index] for index in range(size) if values_right[index] not in used]
    return dict(enumerate(head + tail))


def reverse_segment(
    assignment: Mapping[int, int], change: Change, *, before: bool
) -> dict[int, int]:
    """Apply or undo a 2-opt segment reversal encoded by two endpoint cities.

    Parameters
    ----------
    assignment : mapping of int to int
        Current permutation.
    change : Change
        Endpoint change. ``variable`` is the segment start and ``after`` is the other
        endpoint city when applying.
    before : bool
        True to apply, False to undo.

    Returns
    -------
    dict of int to int
        New permutation.
    """
    values = dict(assignment)
    expected = change.before if before else change.after
    if values[change.variable] != expected:
        raise ValueError("change does not match the assignment")
    other_city = change.after if before else change.before
    end = next((position for position, city in values.items() if city == other_city), None)
    if end is None:
        raise ValueError("2-opt endpoint is not present")
    start = change.variable
    low, high = (start, end) if start <= end else (end, start)
    segment = [values[position] for position in range(low, high + 1)]
    for offset, city in enumerate(reversed(segment)):
        values[low + offset] = city
    return values
