"""Tests for the optional external LKH backend."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fresh_solutions.adapters import TravellingSalesman
from fresh_solutions.adapters.lkh import LkhConfig, run_lkh


def _problem() -> TravellingSalesman:
    """Return a small symmetric TSP fixture."""
    return TravellingSalesman([[0, 1, 3, 4], [1, 0, 2, 3], [3, 2, 0, 1], [4, 3, 1, 0]])


def _fake_lkh(tmp_path: Path, body: str) -> Path:
    """Create an executable fake LKH script."""
    path = tmp_path / "fake-lkh"
    path.write_text(
        f"#!{sys.executable}\nimport pathlib, sys\n"
        "parameters = pathlib.Path(sys.argv[1]).read_text().splitlines()\n"
        "parts = [line.split(' = ', 1) for line in parameters if ' = ' in line]\n"
        "values = {part[0]: part[1] for part in parts}\n"
        "problem = pathlib.Path(values['PROBLEM_FILE'])\n"
        "tour = pathlib.Path(values['TOUR_FILE'])\n"
        f"{body}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_lkh_config_validation() -> None:
    """Invalid backend settings fail before subprocess execution."""
    with pytest.raises(ValueError, match="binary"):
        LkhConfig(binary="")
    with pytest.raises(ValueError, match="runs"):
        LkhConfig(runs=0)
    with pytest.raises(ValueError, match="seed"):
        LkhConfig(seed=-1)
    with pytest.raises(ValueError, match="timeout_seconds"):
        LkhConfig(timeout_seconds=0.0)


def test_run_lkh_with_fake_backend(tmp_path: Path) -> None:
    """The wrapper writes TSPLIB, invokes LKH, parses the tour, and replays it."""
    fake = _fake_lkh(
        tmp_path,
        "tour.write_text('NAME: fake\\nTYPE: TOUR\\nTOUR_SECTION\\n1\\n2\\n3\\n4\\n-1\\nEOF\\n')",
    )
    result = run_lkh(_problem(), LkhConfig(binary=str(fake), runs=2, seed=3))
    assert result.assignment == {0: 0, 1: 1, 2: 2, 3: 3}
    assert result.objective == 8.0
    assert result.runs == 2
    assert result.seed == 3
    assert result.to_dict()["backend"] == "lkh"


def test_run_lkh_rejects_missing_binary() -> None:
    """A missing binary is reported as an execution failure."""
    with pytest.raises(RuntimeError, match="execution failed"):
        run_lkh(_problem(), LkhConfig(binary="/definitely/not/a/lkh"))


def test_run_lkh_rejects_failed_process(tmp_path: Path) -> None:
    """A non-zero LKH exit is reported."""
    fake = _fake_lkh(tmp_path, "sys.exit(2)")
    with pytest.raises(RuntimeError, match="exited with 2"):
        run_lkh(_problem(), LkhConfig(binary=str(fake)))


def test_run_lkh_rejects_invalid_tour(tmp_path: Path) -> None:
    """A malformed tour file is rejected."""
    fake = _fake_lkh(
        tmp_path,
        "tour.write_text('TOUR_SECTION\\n1\\n2\\n-1\\nEOF\\n')",
    )
    with pytest.raises(RuntimeError, match="invalid tour"):
        run_lkh(_problem(), LkhConfig(binary=str(fake)))
