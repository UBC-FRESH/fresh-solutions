"""Fresh Solutions: a hybrid metaheuristic engine for hard combinatorial optimisation."""

from .contracts import Change, Evaluation, EvidenceRecord, ProblemAdapter
from .toy import GraphColouring

__all__ = ["Change", "Evaluation", "EvidenceRecord", "GraphColouring", "ProblemAdapter"]
