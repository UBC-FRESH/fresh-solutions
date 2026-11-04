"""Budget, patience, reversion, and control-file stopping rules."""

from __future__ import annotations

import time

from .control import RunControl


def parse_time_limit(text: str) -> float | None:
    """Parse an ``HH:MM:SS`` limit into seconds.

    Parameters
    ----------
    text : str
        The limit, or an empty string for no limit.

    Returns
    -------
    float or None
        The limit in seconds, or ``None``.

    Raises
    ------
    ValueError
        When the text is not ``HH:MM:SS``, or states zero or less.
    """
    if not text.strip():
        return None
    parts = text.strip().split(":")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"a time limit is HH:MM:SS, and {text!r} is not")
    hours, minutes, seconds = (int(part) for part in parts)
    if minutes > 59 or seconds > 59:
        raise ValueError(f"a time limit is HH:MM:SS, and {text!r} has no such minutes or seconds")
    total = float(hours * 3600 + minutes * 60 + seconds)
    if total <= 0.0:
        raise ValueError(f"a time limit of {text!r} would stop a run before it started")
    return total


def expired(deadline: float | None) -> bool:
    """Return whether a ``time.monotonic`` deadline has passed.

    Parameters
    ----------
    deadline : float or None
        The deadline, or ``None`` for no limit.

    Returns
    -------
    bool
        Whether the deadline has passed.
    """
    return deadline is not None and time.monotonic() >= deadline


def patience_reached(iteration: int, last_improvement: int, patience: int) -> bool:
    """Return whether a patience stop applies.

    Parameters
    ----------
    iteration : int
        The current iteration.
    last_improvement : int
        The iteration of the last incumbent improvement.
    patience : int
        The allowed number of iterations without improvement; ``0`` disables the rule.

    Returns
    -------
    bool
        Whether the search should stop.
    """
    return patience > 0 and iteration - last_improvement >= patience


def reversion_due(accepted: int, reversion: int) -> bool:
    """Return whether the current state should revert to the incumbent.

    Parameters
    ----------
    accepted : int
        The accepted moves since the last reversion.
    reversion : int
        The reversion interval; ``0`` disables it.

    Returns
    -------
    bool
        Whether a reversion is due.
    """
    return reversion > 0 and accepted > 0 and accepted % reversion == 0


def stopped(control: RunControl | None, iteration: int) -> bool:
    """Return whether the control file asks the search to stop, waiting while paused.

    The file is polled every sixty-fourth iteration, which is often enough for a person to
    see and cheap enough not to dominate a move; a missing or invalid file means "run".

    Parameters
    ----------
    control : RunControl or None
        The run's control file, or ``None``.
    iteration : int
        The current iteration index.

    Returns
    -------
    bool
        True when the search should stop.
    """
    if control is None or iteration % 64:
        return False
    action = control.action()
    while action == "pause":
        time.sleep(0.2)
        action = control.action()
    return action == "stop"
