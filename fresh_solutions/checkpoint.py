"""Serializable search checkpoints and exact replay for Fresh Solutions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from .contracts import Evaluation, ProblemAdapter


@dataclass(frozen=True)
class SearchCheckpoint:
    """A replayable search state.

    Parameters
    ----------
    assignment : mapping of int to int
        Variable-to-option assignment.
    seed : int
        Search seed.
    generation : int
        Population generation or local iteration.
    objective : float
        Claimed objective at the checkpoint.
    metadata : mapping of str to object, optional
        Adapter, instance, and provenance metadata.
    """

    assignment: Mapping[int, int]
    seed: int
    generation: int
    objective: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready checkpoint.

        Returns
        -------
        dict of str to object
            Checkpoint with sorted assignment keys.
        """
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "seed": self.seed,
            "generation": self.generation,
            "objective": self.objective,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SearchCheckpoint:
        """Build a checkpoint from a JSON-like mapping.

        Parameters
        ----------
        payload : mapping
            Checkpoint fields.

        Returns
        -------
        SearchCheckpoint
            Parsed checkpoint.
        """
        assignment = {
            int(variable): int(option) for variable, option in dict(payload["assignment"]).items()
        }
        return cls(
            assignment=assignment,
            seed=int(payload["seed"]),
            generation=int(payload["generation"]),
            objective=float(payload["objective"]),
            metadata=dict(payload.get("metadata", {})),
        )

    def save(self, path: str | Path) -> Path:
        """Write the checkpoint as JSON.

        Parameters
        ----------
        path : str or Path
            Destination.

        Returns
        -------
        Path
            Written path.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return destination

    @classmethod
    def load(cls, path: str | Path) -> SearchCheckpoint:
        """Load a checkpoint from JSON.

        Parameters
        ----------
        path : str or Path
            Source.

        Returns
        -------
        SearchCheckpoint
            Parsed checkpoint.
        """
        payload = cast(dict[str, Any], json.loads(Path(path).read_text(encoding="utf-8")))
        return cls.from_dict(payload)

    def verify(self, adapter: ProblemAdapter) -> Evaluation:
        """Replay the checkpoint and verify its objective.

        Parameters
        ----------
        adapter : ProblemAdapter
            Adapter for the same instance.

        Returns
        -------
        Evaluation
            Exact evaluation.

        Raises
        ------
        ValueError
            When the objective does not match.
        """
        evaluation = adapter.evaluate(self.assignment)
        if abs(evaluation.objective - self.objective) > 1e-9:
            raise ValueError("checkpoint objective does not replay exactly")
        return evaluation
