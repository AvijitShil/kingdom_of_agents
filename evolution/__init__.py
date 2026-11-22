"""Evolution package for EON Kingdom of Agents society."""

from .models import ReflectionRecord, SwitchEvent
from .fitness import FitnessMetrics, FitnessEvaluator, compute_composite_fitness
from .reflection import RecursiveReflectionEngine
from .switcher import CategorySwitchManager
from .prompt_optimizer import PromptOptimizer
from .agent import EvolutionaryAgent, ActionString

__all__ = [
    "EvolutionaryAgent",
    "CategorySwitchManager",
    "RecursiveReflectionEngine",
    "FitnessEvaluator",
    "FitnessMetrics",
    "compute_composite_fitness",
    "ReflectionRecord",
    "SwitchEvent",
    "PromptOptimizer",
    "ActionString",
]
