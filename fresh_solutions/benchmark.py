"""Replayable benchmark records for Fresh Solutions adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contracts import Evaluation, ProblemAdapter
from .engine import SearchConfig
from .population import HybridResult, PopulationConfig, run_hybrid_search


@dataclass(frozen=True)
class BenchmarkRecord:
    """A replayable non-forestry benchmark result.

    Parameters
    ----------
    instance : str
        Instance identifier.
    adapter : str
        Adapter name.
    population : PopulationConfig
        Population settings.
    local : SearchConfig
        Local-refinement settings.
    result : HybridResult
        Search result.
    metadata : mapping of str to object, optional
        Provenance metadata.
    """

    instance: str
    adapter: str
    population: PopulationConfig
    local: SearchConfig
    result: HybridResult
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready benchmark record."""
        return {
            "instance": self.instance,
            "adapter": self.adapter,
            "population": self.population.__dict__,
            "local": self.local.__dict__,
            "result": self.result.to_dict(),
            "metadata": dict(self.metadata),
        }

    def verify(self, adapter: ProblemAdapter) -> Evaluation:
        """Replay the recorded assignment and verify its objective.

        Parameters
        ----------
        adapter : ProblemAdapter
            Adapter for the same instance.

        Returns
        -------
        Evaluation
            Exact replay evaluation.

        Raises
        ------
        ValueError
            When the adapter name or objective does not match.
        """
        if adapter.name != self.adapter:
            raise ValueError("adapter name does not match the record")
        evaluation = adapter.evaluate(self.result.assignment)
        if abs(evaluation.objective - self.result.objective) > 1e-9:
            raise ValueError("record objective does not replay exactly")
        return evaluation


def run_benchmark(
    adapter: ProblemAdapter,
    instance: str,
    population: PopulationConfig,
    local: SearchConfig,
    metadata: Mapping[str, Any] | None = None,
) -> BenchmarkRecord:
    """Run and capture one hybrid benchmark.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter.
    instance : str
        Instance identifier.
    population : PopulationConfig
        Population settings.
    local : SearchConfig
        Local-refinement settings.
    metadata : mapping or None, optional
        Provenance metadata.

    Returns
    -------
    BenchmarkRecord
        Replayable benchmark record.
    """
    result = run_hybrid_search(adapter, population, local)
    return BenchmarkRecord(
        instance=instance,
        adapter=adapter.name,
        population=population,
        local=local,
        result=result,
        metadata={} if metadata is None else dict(metadata),
    )


def save_records(records: list[BenchmarkRecord], path: str | Path) -> Path:
    """Write benchmark records to JSON.

    Parameters
    ----------
    records : list of BenchmarkRecord
        Records to write.
    path : str or Path
        Destination.

    Returns
    -------
    Path
        Written path.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps([record.to_dict() for record in records], indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
