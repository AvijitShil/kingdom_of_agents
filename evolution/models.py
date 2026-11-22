"""Data models for Agent Category Selection and Evolution Framework."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


@dataclass
class ReflectionRecord:
    """Record of agent introspection, regret calculation, and prompt adaptation."""

    tick: int
    actual_fitness: float
    counterfactual_fitness: float
    regret: float
    prompt_mutation_suggestion: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ideology_id: str = ""
    perceived_context: str = ""
    action_taken: str = ""
    observed_outcome: str = ""
    counterfactual_alternative: str = ""
    diagnosis: str = ""
    proposed_adaptation_level: str = "NONE"
    adaptation_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def observed_fitness(self) -> float:
        """Alias for actual fitness achieved."""
        return self.actual_fitness

    @property
    def expected_fitness(self) -> float:
        """Alias for counterfactual expected fitness."""
        return self.counterfactual_fitness

    @property
    def prediction_error(self) -> float:
        """Alias for regret / counterfactual delta."""
        return self.regret


@dataclass
class SwitchEvent:
    """Log record of an ideological transition event."""

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tick: int = 0
    from_ideology: str = ""
    to_ideology: str = ""
    trigger_reason: str = ""
    transition_cost: float = 0.0
    pre_switch_fitness: float = 0.0
    probation_ticks_remaining: int = 2
    post_switch_fitness: Optional[float] = None
    status: str = "PROBATION"  # "PROBATION", "CONFIRMED", "ROLLED_BACK"
