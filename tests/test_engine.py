"""Tests for the exact CPU engine and resident assignment state."""

from __future__ import annotations

import random
import subprocess
import sys
from pathlib import Path

import pytest
from fresh_solutions import GraphColouring, ResidentAssignment, SearchConfig, run_local_search


def _graph() -> GraphColouring:
    """Return a triangle with three colours."""
    return GraphColouring(3, ((0, 1), (1, 2), (2, 0)))


def test_search_finds_a_feasible_colouring() -> None:
    """The exact CPU search solves the toy graph end to end."""
    result = run_local_search(_graph(), SearchConfig(iterations=500, seed=4))
    assert result.feasible
    assert result.objective == 0.0
    assert result.evaluations == 501
    assert len(result.history) == 500
    assert set(result.assignment) == {0, 1, 2}
    assert result.to_dict()["feasible"] is True


def test_search_is_deterministic_for_a_seed() -> None:
    """The same seed reproduces the same search path and incumbent."""
    config = SearchConfig(iterations=50, seed=17)
    first = run_local_search(_graph(), config)
    second = run_local_search(_graph(), config)
    assert first.assignment == second.assignment
    assert first.history == second.history
    assert first.accepted == second.accepted


def test_search_config_rejects_invalid_values() -> None:
    """Invalid search settings fail before a run starts."""
    with pytest.raises(ValueError, match="iterations"):
        SearchConfig(iterations=-1)
    with pytest.raises(ValueError, match="temperature"):
        SearchConfig(temperature=0.0)
    with pytest.raises(ValueError, match="cooling"):
        SearchConfig(cooling=0.0)
    with pytest.raises(ValueError, match="cooling"):
        SearchConfig(cooling=1.1)


def test_resident_assignment_applies_and_undoes_exactly() -> None:
    """The resident state uses adapter apply/undo and restores the exact assignment."""
    graph = _graph()
    state = ResidentAssignment(graph)
    original = state.assignment
    change = graph.propose(original, random.Random(3))
    assert change is not None
    state.apply(change)
    assert state.assignment != original
    state.undo(change)
    assert state.assignment == original
    assert state.evaluate().objective >= 0.0


def test_search_handles_an_adapter_with_no_moves() -> None:
    """A one-option problem records iterations without accepting a move."""
    result = run_local_search(GraphColouring(1, (), (7,)), SearchConfig(iterations=2, seed=1))
    assert result.accepted == 0
    assert result.history == (0.0, 0.0)


def test_engine_package_has_no_ws4_dependency() -> None:
    """Importing the engine does not import or textually reference WS4."""
    root = Path(__file__).resolve().parents[1] / "fresh_solutions"
    for path in root.glob("*.py"):
        assert "ws4" not in path.read_text(encoding="utf-8").lower()
    result = subprocess.run(
        [sys.executable, "-c", "import fresh_solutions.engine"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "ws4" not in result.stderr.lower()
