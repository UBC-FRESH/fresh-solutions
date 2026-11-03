"""Contract tests for the shared kernel telemetry logger."""

from __future__ import annotations

import json
from pathlib import Path

from fresh_solutions.kernel import RunLogger, read_records


def test_run_logger_writes_header_steps_and_targets(tmp_path: Path) -> None:
    """The header and each record type round-trip through the JSONL file."""
    path = tmp_path / "telemetry.jsonl"
    with RunLogger(path, "run-1", {"seed": 7}) as logger:
        logger.step(0, 10.0)
        logger.trace(1, 9.0, 11.0, 2)
        logger.targets(2, {(1, "volume"): 3.0, (0, "cost"): 4.0}, island="a")
        logger.schedule(3, {1: (("CC", 0),)}, island="a")
        logger.flush()
    records = read_records(path)
    assert records[0] == {"type": "run", "run_id": "run-1", "config": {"seed": 7}}
    assert records[1] == {"type": "step", "iteration": 0, "objective": 10.0}
    assert records[2] == {
        "type": "step",
        "iteration": 1,
        "objective": 9.0,
        "current": 11.0,
        "accepted": 2,
    }
    assert records[3]["values"] == [
        {"year": 0, "account": "cost", "value": 4.0},
        {"year": 1, "account": "volume", "value": 3.0},
    ]
    assert records[3]["island"] == "a"
    assert records[4]["changed"] == [[1, [["CC", 0]]]]
    assert records[4]["island"] == "a"


def test_schedule_records_only_changes_and_removals(tmp_path: Path) -> None:
    """A steady schedule writes nothing, a change writes the block, and a removal is empty."""
    path = tmp_path / "telemetry.jsonl"
    logger = RunLogger(path, "run", {}, auto_flush=False)
    logger.schedule(0, {1: (("CC", 0),), 2: (("CC", 1),)})
    logger.schedule(1, {1: (("CC", 0),), 2: (("CC", 1),)})
    logger.schedule(2, {1: (("CC", 5),)})
    logger.close()
    records = read_records(path)
    assert [record["iteration"] for record in records[1:]] == [0, 2]
    assert records[2]["changed"] == [[1, [["CC", 5]]], [2, []]]


def test_a_header_only_logger_can_flush_later(tmp_path: Path) -> None:
    """Disabling auto-flush leaves the file readable only after an explicit flush or close."""
    path = tmp_path / "telemetry.jsonl"
    logger = RunLogger(path, "run", {}, auto_flush=False)
    logger.step(0, 1.0)
    logger.flush()
    assert len(read_records(path)) == 2
    logger.close()


def test_read_records_ignores_blank_lines(tmp_path: Path) -> None:
    """A trailing blank line does not break the reader."""
    path = tmp_path / "telemetry.jsonl"
    path.write_text(json.dumps({"type": "run"}) + "\n\n", encoding="utf-8")
    assert read_records(path) == [{"type": "run"}]
