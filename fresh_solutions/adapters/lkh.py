"""Optional external LKH backend for the TSP adapter.

LKH is Keld Helsgaun's Lin-Kernighan-Helsgaun solver. It is not bundled with
Fresh Solutions: it is research-use software and must be installed separately.
This module invokes a user-supplied ``LKH`` binary and parses its tour output.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .tsp import TravellingSalesman


@dataclass(frozen=True)
class LkhConfig:
    """Configuration for the optional external LKH backend.

    Parameters
    ----------
    binary : str, optional
        LKH executable name or path. Defaults to the ``LKH_BINARY`` environment
        variable, or ``LKH``.
    runs : int, optional
        Number of LKH runs. Defaults to 1.
    seed : int, optional
        LKH random seed. Defaults to 1.
    timeout_seconds : float or None, optional
        Optional subprocess timeout.
    """

    binary: str = "LKH"
    runs: int = 1
    seed: int = 1
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if not self.binary:
            raise ValueError("binary must not be empty")
        if self.runs < 1:
            raise ValueError("runs must be positive")
        if self.seed < 0:
            raise ValueError("seed must not be negative")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class LkhResult:
    """Best tour returned by the external LKH backend."""

    assignment: dict[int, int]
    objective: float
    runs: int
    seed: int
    wall_seconds: float
    backend: str = "lkh"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready result."""
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "runs": self.runs,
            "seed": self.seed,
            "wall_seconds": self.wall_seconds,
            "backend": self.backend,
        }


def _write_tsplib(problem: TravellingSalesman, path: Path) -> None:
    """Write a symmetric explicit TSPLIB instance for LKH."""
    size = problem.variable_count
    lines = [
        "NAME: fresh-solutions-lkh",
        "TYPE: TSP",
        f"DIMENSION: {size}",
        "EDGE_WEIGHT_TYPE: EXPLICIT",
        "EDGE_WEIGHT_FORMAT: FULL_MATRIX",
        "EDGE_WEIGHT_SECTION",
    ]
    for row in problem.distances:
        lines.append(" ".join(f"{value:.12g}" for value in row))
    lines.extend(["EOF", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_parameter_file(
    problem_path: Path,
    tour_path: Path,
    parameter_path: Path,
    config: LkhConfig,
) -> None:
    """Write the LKH parameter file."""
    parameter_path.write_text(
        "\n".join(
            [
                f"PROBLEM_FILE = {problem_path}",
                f"TOUR_FILE = {tour_path}",
                f"RUNS = {config.runs}",
                f"SEED = {config.seed}",
                "TRACE_LEVEL = 0",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_tour(path: Path, size: int) -> dict[int, int]:
    """Parse an LKH tour file and convert it to zero-based positions."""
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("TOUR_SECTION") + 1
    except ValueError as error:
        raise RuntimeError("LKH tour file has no TOUR_SECTION") from error
    values: list[int] = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("-1") or stripped == "EOF":
            break
        values.extend(int(value) for value in stripped.split())
    if len(values) != size or sorted(values) != list(range(1, size + 1)):
        raise RuntimeError("LKH returned an invalid tour")
    return {position: city - 1 for position, city in enumerate(values)}


def run_lkh(
    problem: TravellingSalesman,
    config: LkhConfig | None = None,
) -> LkhResult:
    """Run a user-supplied LKH binary on a TSP instance.

    Parameters
    ----------
    problem : TravellingSalesman
        TSP adapter.
    config : LkhConfig or None, optional
        Backend settings. Defaults to ``LKH_BINARY`` or ``LKH``.

    Returns
    -------
    LkhResult
        Best tour and exact re-evaluation.

    Raises
    ------
    RuntimeError
        When LKH is unavailable, fails, or returns an invalid tour.
    """
    settings = config or LkhConfig(binary=os.environ.get("LKH_BINARY", "LKH"))
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="fresh-lkh-") as directory:
        root = Path(directory)
        problem_path = root / "problem.tsp"
        tour_path = root / "problem.tour"
        parameter_path = root / "problem.par"
        _write_tsplib(problem, problem_path)
        _write_parameter_file(problem_path, tour_path, parameter_path, settings)
        try:
            completed = subprocess.run(
                [settings.binary, str(parameter_path)],
                capture_output=True,
                text=True,
                timeout=settings.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"LKH execution failed: {error}") from error
        if completed.returncode != 0:
            raise RuntimeError(
                f"LKH exited with {completed.returncode}: {completed.stderr.strip()}"
            )
        assignment = _read_tour(tour_path, problem.variable_count)
    objective = problem.evaluate(assignment).objective
    return LkhResult(
        assignment=assignment,
        objective=objective,
        runs=settings.runs,
        seed=settings.seed,
        wall_seconds=time.monotonic() - started,
    )
