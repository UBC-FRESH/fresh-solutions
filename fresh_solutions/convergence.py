"""Convergence-controlled hybrid search for benchmark evidence."""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import ProblemAdapter
from .engine import SearchConfig, run_local_search
from .population import PopulationConfig, run_population_search


@dataclass(frozen=True)
class ConvergenceConfig:
    """Stopping rule for a benchmark run.

    Parameters
    ----------
    local_iterations_per_round : int, optional
        Local-search iterations per refinement round. Defaults to 2,000.
    patience_rounds : int, optional
        Stop after this many rounds without relative improvement. Defaults to 5.
    min_relative_improvement : float, optional
        Minimum relative improvement to reset patience. Defaults to 1e-4.
    max_rounds : int, optional
        Maximum refinement rounds. Defaults to 100.
    max_evaluations : int, optional
        Maximum exact evaluations including the population phase. Defaults to 1,000,000.
    """

    local_iterations_per_round: int = 2000
    patience_rounds: int = 5
    min_relative_improvement: float = 1e-4
    max_rounds: int = 100
    max_evaluations: int = 1_000_000

    def __post_init__(self) -> None:
        """Validate the stopping rule."""
        if self.local_iterations_per_round < 1:
            raise ValueError("local_iterations_per_round must be positive")
        if self.patience_rounds < 1:
            raise ValueError("patience_rounds must be positive")
        if self.min_relative_improvement < 0.0:
            raise ValueError("min_relative_improvement must not be negative")
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be positive")
        if self.max_evaluations < 1:
            raise ValueError("max_evaluations must be positive")


@dataclass(frozen=True)
class ConvergenceResult:
    """Best result and the convergence evidence."""

    assignment: dict[int, int]
    objective: float
    feasible: bool
    evaluations: int
    rounds: int
    converged: bool
    stop_reason: str
    history: tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready convergence result."""
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "feasible": self.feasible,
            "evaluations": self.evaluations,
            "rounds": self.rounds,
            "converged": self.converged,
            "stop_reason": self.stop_reason,
            "history": list(self.history),
        }


def run_to_convergence(
    adapter: ProblemAdapter,
    population_config: PopulationConfig,
    local_config: SearchConfig,
    convergence: ConvergenceConfig,
) -> ConvergenceResult:
    """Run population search, then local refinement until the stopping rule fires.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter.
    population_config : PopulationConfig
        Population settings.
    local_config : SearchConfig
        Local-search settings. Its ``iterations`` is overridden by the convergence
        round budget.
    convergence : ConvergenceConfig
        Stopping rule.

    Returns
    -------
    ConvergenceResult
        Best assignment and explicit stop evidence.
    """
    population = run_population_search(adapter, population_config)
    best = population.assignment
    evaluation = adapter.evaluate(best)
    evaluations = population.evaluations
    history = [evaluation.objective]
    patience = 0
    rounds = 0
    stop_reason = "max_evaluations"
    for round_index in range(convergence.max_rounds):
        if evaluations >= convergence.max_evaluations:
            stop_reason = "max_evaluations"
            break
        rounds += 1
        round_config = SearchConfig(
            iterations=convergence.local_iterations_per_round,
            seed=local_config.seed + round_index,
            temperature=local_config.temperature,
            cooling=local_config.cooling,
        )
        local = run_local_search(adapter, round_config, initial=best)
        evaluations += local.evaluations
        improved = (
            evaluation.objective - local.objective
        ) > convergence.min_relative_improvement * max(abs(evaluation.objective), 1.0)
        if local.feasible and (not evaluation.feasible or local.objective < evaluation.objective):
            evaluation = adapter.evaluate(local.assignment)
            best = local.assignment
            history.append(evaluation.objective)
        if improved:
            patience = 0
        else:
            patience += 1
        if patience >= convergence.patience_rounds:
            stop_reason = "patience"
            break
        if evaluations >= convergence.max_evaluations:
            stop_reason = "max_evaluations"
            break
    else:
        stop_reason = "max_rounds"
    return ConvergenceResult(
        assignment=dict(best),
        objective=evaluation.objective,
        feasible=evaluation.feasible,
        evaluations=evaluations,
        rounds=rounds,
        converged=stop_reason == "patience",
        stop_reason=stop_reason,
        history=tuple(history),
    )
