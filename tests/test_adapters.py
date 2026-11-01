"""Tests for the QAP and TSP benchmark adapters and parsers."""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from fresh_solutions import (
    Change,
    GraphColouring,
    PopulationConfig,
    SearchConfig,
    run_hybrid_search,
)
from fresh_solutions.adapters import QuadraticAssignment, TravellingSalesman


def test_qap_objective_swap_and_batch() -> None:
    """QAP evaluation is exact, swaps preserve the permutation, and batches agree."""
    problem = QuadraticAssignment([[0, 2], [3, 0]], [[0, 5], [7, 0]])
    identity = problem.initial_assignment()
    assert problem.evaluate(identity).objective == 31.0
    change = problem.propose(identity, random.Random(1))
    assert change is not None
    moved = problem.apply(identity, change)
    assert problem.undo(moved, change) == identity
    assert problem.evaluate_batch([identity])[0] == problem.evaluate(identity)


def test_qap_parser_and_errors(tmp_path: Path) -> None:
    """QAPLIB parsing handles a complete instance and rejects malformed data."""
    path = tmp_path / "qap.dat"
    path.write_text("2\n0 2\n3 0\n0 5\n7 0\n", encoding="utf-8")
    problem = QuadraticAssignment.from_qaplib(path)
    assert problem.variable_count == 2
    bad = tmp_path / "bad.dat"
    bad.write_text("2\n1 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="wrong number"):
        QuadraticAssignment.from_qaplib(bad)
    bad2 = tmp_path / "bad2.dat"
    bad2.write_text("x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-numeric"):
        QuadraticAssignment.from_qaplib(bad2)


def test_tsp_objective_swap_and_batch() -> None:
    """TSP tour distance is exact and swaps preserve the permutation."""
    problem = TravellingSalesman([[0, 1, 3], [1, 0, 2], [3, 2, 0]])
    identity = problem.initial_assignment()
    assert problem.evaluate(identity).objective == 6.0
    change = problem.propose(identity, random.Random(2))
    assert change is not None
    moved = problem.apply(identity, change)
    assert problem.undo(moved, change) == identity
    assert problem.evaluate_batch([identity])[0].objective == 6.0


def test_tsp_two_opt_reverses_a_segment() -> None:
    """A TSP change reverses a tour segment and undo restores it."""
    problem = TravellingSalesman([[0, 1, 3, 4], [1, 0, 2, 3], [3, 2, 0, 1], [4, 3, 1, 0]])
    identity = problem.initial_assignment()
    change = Change(variable=0, before=0, after=2)
    moved = problem.apply(identity, change)
    assert moved == {0: 2, 1: 1, 2: 0, 3: 3}
    assert problem.undo(moved, change) == identity


def test_tsp_parser_and_errors(tmp_path: Path) -> None:
    """TSPLIB parsing reads EUC_2D coordinates and rejects malformed files."""
    path = tmp_path / "tsp.tsp"
    path.write_text(
        "NAME: square\nTYPE: TSP\nDIMENSION: 4\nEDGE_WEIGHT_TYPE: EUC_2D\n"
        "NODE_COORD_SECTION\n1 0 0\n2 1 0\n3 1 1\n4 0 1\nEOF\n",
        encoding="utf-8",
    )
    problem = TravellingSalesman.from_tsplib(path)
    assert problem.variable_count == 4
    assert problem.evaluate(problem.initial_assignment()).objective == 4.0
    bad = tmp_path / "bad.tsp"
    bad.write_text("DIMENSION: 2\nNODE_COORD_SECTION\n1 0 0\nEOF\n", encoding="utf-8")
    with pytest.raises(ValueError, match="coordinates"):
        TravellingSalesman.from_tsplib(bad)
    bad.write_text("EDGE_WEIGHT_TYPE: MAN_2D\nNODE_COORD_SECTION\nEOF\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        TravellingSalesman.from_tsplib(bad)


@pytest.mark.parametrize(
    "adapter",
    [
        QuadraticAssignment([[0, 2], [3, 0]], [[0, 5], [7, 0]]),
        TravellingSalesman([[0, 1, 3], [1, 0, 2], [3, 2, 0]]),
        GraphColouring(3, ((0, 1), (1, 2), (2, 0))),
    ],
)
def test_hybrid_search_runs_all_benchmark_families(adapter: object) -> None:
    """The same engine runs QAP, TSP, and graph colouring adapters."""
    result = run_hybrid_search(
        adapter,  # type: ignore[arg-type]
        PopulationConfig(population=4, generations=2, seed=3),
        SearchConfig(iterations=3, seed=3),
    )
    assert result.evaluations > 0
    assert set(result.assignment) == set(range(adapter.variable_count))  # type: ignore[attr-defined]
