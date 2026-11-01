"""Backend-neutral batched population search and exact hybrid handoff."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .backend import BatchBackend, CpuBatchBackend
from .contracts import Evaluation, ProblemAdapter
from .engine import SearchConfig, run_local_search


@dataclass(frozen=True)
class PopulationConfig:
    """Configuration for a batched population search.

    Parameters
    ----------
    population : int, optional
        Number of genomes. Defaults to 32.
    generations : int, optional
        Number of bred generations. Defaults to 50.
    seed : int, optional
        Random seed. Defaults to 1.
    mutation_rate : float, optional
        Per-variable mutation probability. Defaults to 0.05.
    elite_fraction : float, optional
        Fraction copied unchanged into the next generation. Defaults to 0.1.
    tournament_size : int, optional
        Tournament contenders. Defaults to 3.
    random_fraction : float, optional
        Fraction of the initial population that is uniformly random. Defaults to 0.2.
    """

    population: int = 32
    generations: int = 50
    seed: int = 1
    mutation_rate: float = 0.05
    elite_fraction: float = 0.1
    tournament_size: int = 3
    random_fraction: float = 0.2

    def __post_init__(self) -> None:
        """Validate population settings."""
        if self.population < 2:
            raise ValueError("population must be at least two")
        if self.generations < 0:
            raise ValueError("generations must not be negative")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be in [0, 1]")
        if not 0.0 <= self.elite_fraction < 1.0:
            raise ValueError("elite_fraction must be in [0, 1)")
        if self.tournament_size < 1:
            raise ValueError("tournament_size must be positive")
        if not 0.0 <= self.random_fraction <= 1.0:
            raise ValueError("random_fraction must be in [0, 1]")


@dataclass(frozen=True)
class PopulationResult:
    """Best result from a batched population search."""

    assignment: Mapping[int, int]
    objective: float
    feasible: bool
    evaluations: int
    generations: int
    history: tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready result."""
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "feasible": self.feasible,
            "evaluations": self.evaluations,
            "generations": self.generations,
            "history": list(self.history),
        }


@dataclass(frozen=True)
class HybridResult:
    """Best result from population search plus exact local refinement."""

    assignment: Mapping[int, int]
    objective: float
    feasible: bool
    evaluations: int
    population_generations: int
    local_iterations: int
    history: tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready result."""
        return {
            "assignment": {str(key): value for key, value in sorted(self.assignment.items())},
            "objective": self.objective,
            "feasible": self.feasible,
            "evaluations": self.evaluations,
            "population_generations": self.population_generations,
            "local_iterations": self.local_iterations,
            "history": list(self.history),
        }


def _score(evaluation: Evaluation) -> tuple[bool, float]:
    return (not evaluation.feasible, evaluation.objective)


def _random_assignment(adapter: ProblemAdapter, rng: random.Random) -> dict[int, int]:
    return adapter.random_assignment(rng)


def _tournament(
    population: Sequence[Mapping[int, int]],
    scores: Sequence[Evaluation],
    size: int,
    rng: random.Random,
) -> Mapping[int, int]:
    contenders = [rng.randrange(len(population)) for _ in range(size)]
    winner = min(contenders, key=lambda index: _score(scores[index]))
    return population[winner]


def run_population_search(
    adapter: ProblemAdapter,
    config: PopulationConfig,
    backend: BatchBackend | None = None,
) -> PopulationResult:
    """Run a batched population search using exact batch evaluations.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter.
    config : PopulationConfig
        Search settings.
    backend : BatchBackend or None, optional
        Batch backend. Defaults to the adapter's exact CPU batch path.

    Returns
    -------
    PopulationResult
        Best assignment, exact objective, counters, and history.
    """
    rng = random.Random(config.seed)
    evaluator = backend if backend is not None else CpuBatchBackend(adapter)
    seed_assignment = adapter.initial_assignment()
    random_count = min(round(config.population * config.random_fraction), config.population - 1)
    mutant_count = config.population - 1 - random_count
    population: list[dict[int, int]] = [dict(seed_assignment)]
    population.extend(
        adapter.mutate(seed_assignment, config.mutation_rate, rng) for _ in range(mutant_count)
    )
    population.extend(_random_assignment(adapter, rng) for _ in range(random_count))
    scores = evaluator.evaluate_batch(population)
    evaluations = len(population)
    best_index = min(range(len(population)), key=lambda index: _score(scores[index]))
    best = scores[best_index]
    best_assignment = dict(population[best_index])
    history = [best.objective]
    for _ in range(config.generations):
        order = sorted(range(len(population)), key=lambda index: _score(scores[index]))
        elite_count = min(
            len(population),
            max(1, round(len(population) * config.elite_fraction)),
        )
        children = [dict(population[index]) for index in order[:elite_count]]
        while len(children) < config.population:
            left = _tournament(population, scores, config.tournament_size, rng)
            right = _tournament(population, scores, config.tournament_size, rng)
            child = adapter.crossover(left, right, rng)
            children.append(adapter.mutate(child, config.mutation_rate, rng))
        population = children
        scores = evaluator.evaluate_batch(population)
        evaluations += len(population)
        generation_best = min(range(len(population)), key=lambda index: _score(scores[index]))
        if _score(scores[generation_best]) < _score(best):
            best = scores[generation_best]
            best_assignment = dict(population[generation_best])
        history.append(best.objective)
    return PopulationResult(
        assignment=best_assignment,
        objective=best.objective,
        feasible=best.feasible,
        evaluations=evaluations,
        generations=config.generations,
        history=tuple(history),
    )


def run_hybrid_search(
    adapter: ProblemAdapter,
    population_config: PopulationConfig,
    local_config: SearchConfig,
    backend: BatchBackend | None = None,
) -> HybridResult:
    """Run population search, then exact local refinement from its elite.

    Parameters
    ----------
    adapter : ProblemAdapter
        Problem adapter.
    population_config : PopulationConfig
        Population settings.
    local_config : SearchConfig
        Local-refinement settings.
    backend : BatchBackend or None, optional
        Batch backend for the population phase.

    Returns
    -------
    HybridResult
        Best of the population and refined elites.
    """
    population = run_population_search(adapter, population_config, backend)
    local = run_local_search(adapter, local_config, initial=population.assignment)
    return HybridResult(
        assignment=local.assignment,
        objective=local.objective,
        feasible=local.feasible,
        evaluations=population.evaluations + local.evaluations,
        population_generations=population.generations,
        local_iterations=local_config.iterations,
        history=population.history + local.history,
    )
