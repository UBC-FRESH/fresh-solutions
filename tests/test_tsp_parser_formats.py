"""Tests for the supported TSPLIB coordinate and explicit formats."""

from __future__ import annotations

from pathlib import Path

import pytest
from fresh_solutions.adapters import TravellingSalesman


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_att_and_ceil_coordinate_formats(tmp_path: Path) -> None:
    """ATT and CEIL_2D use the TSPLIB distance conventions."""
    att = _write(
        tmp_path,
        "att.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: ATT\nNODE_COORD_SECTION\n1 0 0\n2 10 0\nEOF\n",
    )
    ceil = _write(
        tmp_path,
        "ceil.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: CEIL_2D\nNODE_COORD_SECTION\n1 0 0\n2 1 1\nEOF\n",
    )
    assert TravellingSalesman.from_tsplib(att).distances[0][1] == 4.0
    assert TravellingSalesman.from_tsplib(ceil).distances[0][1] == 2.0


def test_geo_coordinate_format(tmp_path: Path) -> None:
    """GEO coordinates produce a symmetric positive distance matrix."""
    path = _write(
        tmp_path,
        "geo.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: GEO\nNODE_COORD_SECTION\n"
        "1 49.0 123.0\n2 49.1 123.1\nEOF\n",
    )
    problem = TravellingSalesman.from_tsplib(path)
    assert problem.distances[0][1] > 0.0
    assert problem.distances[0][1] == problem.distances[1][0]


def test_geo_known_distance_regression(tmp_path: Path) -> None:
    """GEO uses the integer degree as the base and the TSPLIB floor convention."""
    path = _write(
        tmp_path,
        "geo-known.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: GEO\nNODE_COORD_SECTION\n"
        "1 16.47 96.10\n2 16.47 94.44\nEOF\n",
    )
    problem = TravellingSalesman.from_tsplib(path)
    assert problem.distances[0][1] == 153.0


def test_explicit_matrix_formats(tmp_path: Path) -> None:
    """Explicit full, lower-diagonal, and upper-row matrices parse symmetrically."""
    full = _write(
        tmp_path,
        "full.tsp",
        "DIMENSION: 3\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: FULL_MATRIX\n"
        "EDGE_WEIGHT_SECTION\n0 1 2\n1 0 3\n2 3 0\nEOF\n",
    )
    lower = _write(
        tmp_path,
        "lower.tsp",
        "DIMENSION: 3\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: LOWER_DIAG_ROW\n"
        "EDGE_WEIGHT_SECTION\n0\n1 0\n2 3 0\nEOF\n",
    )
    upper = _write(
        tmp_path,
        "upper.tsp",
        "DIMENSION: 3\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: UPPER_ROW\n"
        "EDGE_WEIGHT_SECTION\n1 2\n3\nEOF\n",
    )
    upper_diag = _write(
        tmp_path,
        "upper-diag.tsp",
        "DIMENSION: 3\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: UPPER_DIAG_ROW\n"
        "EDGE_WEIGHT_SECTION\n0 1 2\n0 3\n0\nEOF\n",
    )
    lower_row = _write(
        tmp_path,
        "lower-row.tsp",
        "DIMENSION: 3\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: LOWER_ROW\n"
        "EDGE_WEIGHT_SECTION\n1\n2 3\nEOF\n",
    )
    expected = [[0.0, 1.0, 2.0], [1.0, 0.0, 3.0], [2.0, 3.0, 0.0]]
    for path in (full, lower, upper, upper_diag, lower_row):
        assert TravellingSalesman.from_tsplib(path).distances == tuple(
            tuple(row) for row in expected
        )


def test_explicit_error_paths(tmp_path: Path) -> None:
    """Malformed explicit matrices and unsupported formats are rejected."""
    missing_dimension = _write(
        tmp_path,
        "missing.tsp",
        "EDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_SECTION\n0\nEOF\n",
    )
    with pytest.raises(ValueError, match="DIMENSION"):
        TravellingSalesman.from_tsplib(missing_dimension)
    short = _write(
        tmp_path,
        "short.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: FULL_MATRIX\n"
        "EDGE_WEIGHT_SECTION\n0 1\nEOF\n",
    )
    with pytest.raises(ValueError, match="wrong number"):
        TravellingSalesman.from_tsplib(short)
    unsupported = _write(
        tmp_path,
        "unsupported.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: NOPE\n"
        "EDGE_WEIGHT_SECTION\n0 1 1 0\nEOF\n",
    )
    with pytest.raises(ValueError, match="unsupported"):
        TravellingSalesman.from_tsplib(unsupported)
    too_few = _write(
        tmp_path,
        "too-few.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: LOWER_DIAG_ROW\n"
        "EDGE_WEIGHT_SECTION\n0\nEOF\n",
    )
    with pytest.raises(ValueError, match="too few"):
        TravellingSalesman.from_tsplib(too_few)
    too_many = _write(
        tmp_path,
        "too-many.tsp",
        "DIMENSION: 2\nEDGE_WEIGHT_TYPE: EXPLICIT\nEDGE_WEIGHT_FORMAT: LOWER_DIAG_ROW\n"
        "EDGE_WEIGHT_SECTION\n0 1 0 9\nEOF\n",
    )
    with pytest.raises(ValueError, match="wrong number"):
        TravellingSalesman.from_tsplib(too_many)
