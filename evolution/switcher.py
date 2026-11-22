"""Category switch manager governing ideological transitions, hysteresis, and probation."""

from datetime import datetime, timezone
from typing import Optional, List, Any
from knowledge_base.models import IdeologicalProfile
from knowledge_base.retriever import CorpusRetriever
from .models import SwitchEvent


class CategorySwitchManager:
    """Manages ideological category switches with switching costs, hysteresis, cooldown, and probation."""

    def __init__(
        self,
        agent: Optional[Any] = None,
        switching_cost: float = 50.0,
        hysteresis_margin: float = 0.15,
        cooldown_ticks: int = 3,
        probation_window: int = 2,
        retriever: Optional[CorpusRetriever] = None,
    ):
        self.agent = agent
        self.switching_cost = float(switching_cost)
        self.hysteresis_margin = float(hysteresis_margin)
        self.cooldown_ticks = int(cooldown_ticks)
        self.probation_window = int(probation_window)
        self.retriever = retriever

        self.last_switch_tick: int = -999
        self.switch_history: List[SwitchEvent] = []
        self.previous_ideology: Optional[IdeologicalProfile] = None
        self.pre_switch_fitness: float = 0.0
        self.probation_ticks_remaining: int = 0

    def evaluate_switch(
        self,
        candidate_ideology: IdeologicalProfile,
        candidate_expected_fitness: float,
        current_tick: Optional[int] = None,
    ) -> bool:
        """Evaluate whether a switch to candidate_ideology is justified under cooldown and hysteresis."""
        # 1. Cooldown enforcement
        if current_tick is not None and (current_tick - self.last_switch_tick) < self.cooldown_ticks:
            return False

        # 2. Hysteresis barrier enforcement
        f_curr = 0.5
        if self.agent is not None and getattr(self.agent, "fitness_history", None):
            latest = self.agent.fitness_history[-1]
            if getattr(latest, "composite_score", 0.0) != 0.0:
                f_curr = latest.composite_score
            elif getattr(self.agent, "ideology", None) and hasattr(self.agent.ideology, "utility_weights"):
                f_curr = latest.compute_composite(self.agent.ideology.utility_weights)
            else:
                f_curr = (
                    getattr(latest, "wealth", 0.0)
                    + getattr(latest, "security", 0.0)
                    + getattr(latest, "reputation", 0.0)
                    + getattr(latest, "fairness", 0.0)
                    + getattr(latest, "compliance", 0.0)
                ) / 5.0

        if candidate_expected_fitness <= f_curr + self.hysteresis_margin:
            return False

        return True

    def execute_switch(
        self,
        candidate_ideology: IdeologicalProfile,
        current_tick: int = 0,
        reason: str = "performance_optimization",
    ) -> SwitchEvent:
        """Execute category switch, deduct switching cost, initialize probation, and log SwitchEvent."""
        if self.agent is not None:
            # Deduct switching cost from agent budget
            cost = int(self.switching_cost) if isinstance(self.agent.budget, int) else self.switching_cost
            self.agent.budget = max(0, self.agent.budget - cost)

            self.previous_ideology = getattr(self.agent, "ideology", None)

            if getattr(self.agent, "fitness_history", None):
                latest = self.agent.fitness_history[-1]
                if getattr(latest, "composite_score", 0.0) != 0.0:
                    self.pre_switch_fitness = latest.composite_score
                elif self.previous_ideology and hasattr(self.previous_ideology, "utility_weights"):
                    self.pre_switch_fitness = latest.compute_composite(self.previous_ideology.utility_weights)
                else:
                    self.pre_switch_fitness = (
                        getattr(latest, "wealth", 0.0)
                        + getattr(latest, "security", 0.0)
                        + getattr(latest, "reputation", 0.0)
                        + getattr(latest, "fairness", 0.0)
                        + getattr(latest, "compliance", 0.0)
                    ) / 5.0
            else:
                self.pre_switch_fitness = 0.5

            self.agent.ideology = candidate_ideology
            self.agent.is_on_probation = True
            self.agent.last_switch_tick = current_tick

        self.probation_ticks_remaining = self.probation_window
        self.last_switch_tick = current_tick

        event = SwitchEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tick=current_tick,
            from_ideology=self.previous_ideology.id if self.previous_ideology else "none",
            to_ideology=candidate_ideology.id,
            trigger_reason=reason,
            transition_cost=self.switching_cost,
            pre_switch_fitness=self.pre_switch_fitness,
            probation_ticks_remaining=self.probation_window,
            post_switch_fitness=None,
            status="PROBATION",
        )
        self.switch_history.append(event)
        return event

    def check_probation(self, current_tick: int) -> bool:
        """Evaluate active probation period. Return True if state transitioned (rollback or confirmed)."""
        if self.agent is None or not getattr(self.agent, "is_on_probation", False):
            return False

        if not getattr(self.agent, "fitness_history", None):
            current_composite = self.pre_switch_fitness
        else:
            latest = self.agent.fitness_history[-1]
            if getattr(self.agent, "ideology", None) and hasattr(self.agent.ideology, "utility_weights"):
                current_composite = latest.compute_composite(self.agent.ideology.utility_weights)
            elif getattr(latest, "composite_score", 0.0) != 0.0:
                current_composite = latest.composite_score
            else:
                current_composite = (
                    getattr(latest, "wealth", 0.0)
                    + getattr(latest, "security", 0.0)
                    + getattr(latest, "reputation", 0.0)
                    + getattr(latest, "fairness", 0.0)
                    + getattr(latest, "compliance", 0.0)
                ) / 5.0

        if self.switch_history:
            self.switch_history[-1].post_switch_fitness = current_composite

        # Performance degradation check
        is_degraded = (current_composite < self.pre_switch_fitness - 1e-4) or (
            current_composite < 0.4 and self.pre_switch_fitness >= 0.4
        )

        if is_degraded:
            # Rollback to previous doctrine
            self.agent.ideology = self.previous_ideology
            self.agent.is_on_probation = False
            if self.switch_history:
                self.switch_history[-1].status = "ROLLED_BACK"
            return True
        else:
            # Sustained performance decrements probation window
            self.probation_ticks_remaining -= 1
            if self.switch_history:
                self.switch_history[-1].probation_ticks_remaining = max(0, self.probation_ticks_remaining)
            if self.probation_ticks_remaining <= 0:
                # Promotion to permanent ideology
                self.agent.is_on_probation = False
                if self.switch_history:
                    self.switch_history[-1].status = "CONFIRMED"
                return True
            return False
