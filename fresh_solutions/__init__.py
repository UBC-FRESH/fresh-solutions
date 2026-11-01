"""Fresh Solutions: a hybrid metaheuristic engine for hard combinatorial optimisation."""

from .backend import BatchBackend, CpuBatchBackend
from .checkpoint import SearchCheckpoint
from .contracts import Change, Evaluation, EvidenceRecord, ProblemAdapter
from .convergence import ConvergenceConfig, ConvergenceResult, run_to_convergence
from .engine import ResidentAssignment, ResidentState, SearchConfig, SearchResult, run_local_search
from .population import (
    HybridResult,
    PopulationConfig,
    PopulationResult,
    run_hybrid_search,
    run_population_search,
)
from .toy import GraphColouring

__all__ = [
    "BatchBackend",
    "Change",
    "ConvergenceConfig",
    "ConvergenceResult",
    "CpuBatchBackend",
    "Evaluation",
    "EvidenceRecord",
    "GraphColouring",
    "HybridResult",
    "PopulationConfig",
    "PopulationResult",
    "ProblemAdapter",
    "ResidentAssignment",
    "ResidentState",
    "SearchCheckpoint",
    "SearchConfig",
    "SearchResult",
    "run_hybrid_search",
    "run_local_search",
    "run_population_search",
    "run_to_convergence",
]
