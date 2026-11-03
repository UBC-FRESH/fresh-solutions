"""The shared metaheuristic kernel: state, operators, solvers, and stopping rules.

The kernel is problem-agnostic. Adapters in WS4, FHOPS, and the public benchmark suite
supply the state representation, objective, move context, and operators.
"""

from .control import RunControl
from .cooling import AdaptiveCooling, TemperatureSchedule
from .operators import Operator, OperatorRegistry, Undo, restore, restore_state
from .problem import Problem, clone_state, state_signature
from .solvers import (
    DeltaEvaluator,
    SnapshotCallback,
    StepCallback,
    TraceCallback,
    solve_ils,
    solve_sa,
    solve_sa_delta,
    solve_tabu,
    solve_threshold,
)
from .stopping import (
    expired,
    parse_time_limit,
    patience_reached,
    reversion_due,
    stopped,
)

__all__ = [
    "AdaptiveCooling",
    "DeltaEvaluator",
    "Operator",
    "OperatorRegistry",
    "Problem",
    "RunControl",
    "SnapshotCallback",
    "StepCallback",
    "TemperatureSchedule",
    "TraceCallback",
    "Undo",
    "clone_state",
    "expired",
    "parse_time_limit",
    "patience_reached",
    "restore",
    "restore_state",
    "reversion_due",
    "solve_ils",
    "solve_sa",
    "solve_sa_delta",
    "solve_tabu",
    "solve_threshold",
    "state_signature",
    "stopped",
]
