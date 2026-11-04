"""The runner boundary shared by portfolio and tuning layers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class Runner(Protocol):
    """The part of a solver a portfolio or tuner needs."""

    def run(self, out_dir: Path) -> dict[str, Any]:
        """Run one member and write its outputs.

        Parameters
        ----------
        out_dir : Path
            The member's run directory.

        Returns
        -------
        dict of str to object
            The run summary.
        """
        ...
