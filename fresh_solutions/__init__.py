"""Fresh Solutions: a hybrid metaheuristic engine for hard combinatorial optimisation."""

from .contracts import Change, Evaluation, EvidenceRecord, ProblemAdapter
from .engine import ResidentAssignment, ResidentState, SearchConfig, SearchResult, run_local_search
from .toy import GraphColouring

__all__ = [
    "Change",
    "Evaluation",
    "EvidenceRecord",
    "GraphColouring",
    "ProblemAdapter",
    "ResidentAssignment",
    "ResidentState",
    "SearchConfig",
    "SearchResult",
    "run_local_search",
]
