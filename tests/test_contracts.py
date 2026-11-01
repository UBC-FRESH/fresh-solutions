"""Tests for the Fresh Solutions adapter and replay contracts."""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import replace

import pytest
from fresh_solutions import Change, Evaluation, EvidenceRecord, GraphColouring, ProblemAdapter


def _triangle() -> GraphColouring:
    """Return a three-node triangle with three colours."""
    return GraphColouring(3, ((0, 1), (1, 2), (2, 0)))


def test_graph_colouring_options_and_initial_assignment() -> None:
    """The adapter exposes every variable and option and starts with one complete assignment."""
    graph = _triangle()
    assert graph.variable_count == 3
    assert graph.option_count(0) == 3
    assert graph.option_at(1, 2) == 2
    assert graph.initial_assignment() == {0: 0, 1: 0, 2: 0}
    assert isinstance(graph, ProblemAdapter)


def test_graph_colouring_evaluates_conflicts_and_batches() -> None:
    """The exact and batched paths agree on a conflict objective."""
    graph = _triangle()
    conflicting = graph.evaluate({0: 0, 1: 0, 2: 1})
    feasible = graph.evaluate({0: 0, 1: 1, 2: 2})
    assert conflicting == Evaluation(1.0, False, {"conflicts": 1.0})
    assert feasible == Evaluation(0.0, True, {"conflicts": 0.0})
    assert graph.evaluate_batch([{0: 0, 1: 0, 2: 1}, {0: 0, 1: 1, 2: 2}]) == [
        conflicting,
        feasible,
    ]


def test_graph_colouring_move_round_trip() -> None:
    """A proposed move changes one option and undo restores the original assignment."""
    graph = _triangle()
    assignment = graph.initial_assignment()
    change = graph.propose(assignment, random.Random(4))
    assert change is not None
    moved = graph.apply(assignment, change)
    assert moved[change.variable] == change.after
    assert graph.undo(moved, change) == assignment


def test_one_colour_graph_has_no_move() -> None:
    """A problem with one option per variable has no reversible change."""
    assert GraphColouring(1, (), (7,)).propose({0: 0}, random.Random(1)) is None


def test_bad_assignments_and_changes_are_rejected() -> None:
    """Invalid inputs fail loudly instead of producing a silent objective."""
    graph = _triangle()
    with pytest.raises(ValueError, match="cover every node"):
        graph.evaluate({0: 0})
    with pytest.raises(ValueError, match="invalid option"):
        graph.evaluate({0: 0, 1: 0, 2: 99})
    change = Change(0, 0, 1)
    with pytest.raises(ValueError, match="before"):
        graph.apply({0: 1, 1: 0, 2: 0}, change)
    with pytest.raises(ValueError, match="after"):
        graph.undo({0: 0, 1: 0, 2: 0}, change)
    with pytest.raises(IndexError):
        graph.option_count(3)
    with pytest.raises(IndexError):
        graph.option_at(0, 8)
    with pytest.raises(ValueError, match="positive"):
        GraphColouring(0, ())
    with pytest.raises(ValueError, match="colour"):
        GraphColouring(1, (), ())
    with pytest.raises(ValueError, match="unknown node"):
        GraphColouring(2, ((0, 2),))


def test_evidence_record_replays_exactly() -> None:
    """A recorded assignment can be replayed and checked against its claimed objective."""
    graph = _triangle()
    assignment: Mapping[int, int] = {0: 0, 1: 1, 2: 2}
    record = EvidenceRecord(
        instance="triangle",
        adapter=graph.name,
        assignment=assignment,
        objective=0.0,
        feasible=True,
        seed=7,
        metadata={"hardware": "test"},
    )
    assert record.verify(graph).feasible
    assert record.to_dict()["assignment"] == {"0": 0, "1": 1, "2": 2}
    with pytest.raises(ValueError, match="adapter mismatch"):
        replace(record, adapter="other").verify(graph)
    bad = EvidenceRecord("triangle", graph.name, {0: 0}, 0.0, False, 7)
    with pytest.raises(ValueError, match="cover every variable"):
        bad.verify(graph)
