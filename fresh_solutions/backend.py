"""Batch-evaluation backend contract for Fresh Solutions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from .contracts import Evaluation, ProblemAdapter


@runtime_checkable
class BatchBackend(Protocol):
    """A batched exact evaluation backend.

    A CPU adapter is the default implementation. A GPU/device backend can implement the same
    protocol without leaking device details into the search loop.
    """

    def evaluate_batch(self, assignments: Sequence[Mapping[int, int]]) -> list[Evaluation]:
        """Return exact evaluations for a batch of assignments."""
        ...


class CpuBatchBackend:
    """Batch backend backed by an adapter's exact batch evaluator.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter.
    """

    def __init__(self, adapter: ProblemAdapter) -> None:
        self.adapter = adapter

    def evaluate_batch(self, assignments: Sequence[Mapping[int, int]]) -> list[Evaluation]:
        """Return exact evaluations for a batch.

        Parameters
        ----------
        assignments : sequence of mapping
            Complete assignments.

        Returns
        -------
        list of Evaluation
            Exact evaluations in input order.
        """
        return self.adapter.evaluate_batch(assignments)
