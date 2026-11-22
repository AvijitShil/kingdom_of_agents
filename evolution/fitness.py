"""Fitness evaluation models and utilities for evolving agents."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class FitnessMetrics:
    """Multi-dimensional fitness metrics across societal performance pillars."""

    wealth: float = 0.0
    security: float = 0.0
    reputation: float = 0.0
    fairness: float = 0.0
    compliance: float = 0.0
    tick: int = 0
    composite_score: float = 0.0

    def compute_composite(self, weights: Dict[str, float]) -> float:
        """Compute normalized composite fitness score using active utility weights."""
        keys = ("wealth", "security", "reputation", "fairness", "compliance")
        total = sum(weights.get(k, 0.2) * getattr(self, k) for k in keys)
        self.composite_score = total
        return self.composite_score

    @property
    def token_wealth(self) -> float:
        return self.wealth

    @property
    def constitutional_fidelity(self) -> float:
        return self.security

    @property
    def reputation_score(self) -> float:
        return self.reputation

    @property
    def dispute_win_rate(self) -> float:
        return self.fairness

    @property
    def transaction_success_rate(self) -> float:
        return self.compliance


def compute_composite_fitness(metrics: FitnessMetrics, weights: Dict[str, float]) -> float:
    """Helper function to compute composite score from FitnessMetrics and weights dict."""
    return metrics.compute_composite(weights)


class FitnessEvaluator:
    """Provides contextual fitness evaluation from society, ledger, and judicial dispute data."""

    def __init__(self, ledger: Optional[Any] = None, court: Optional[Any] = None):
        self.ledger = ledger
        self.court = court

    def evaluate(
        self,
        agent_id: str,
        tick: int = 0,
        context: Optional[Dict[str, Any]] = None,
    ) -> FitnessMetrics:
        """Evaluate agent societal performance and return a FitnessMetrics record."""
        context = context or {}
        if "metrics" in context and isinstance(context["metrics"], FitnessMetrics):
            return context["metrics"]

        wealth = context.get("wealth", 0.5)
        if self.ledger is not None and hasattr(self.ledger, "get_balance"):
            try:
                bal = self.ledger.get_balance(agent_id)
                wealth = min(1.0, max(0.0, float(bal) / 2000.0))
            except Exception:
                pass

        security = context.get("security", 0.5)
        reputation = context.get("reputation", 0.5)
        fairness = context.get("fairness", 0.5)
        compliance = context.get("compliance", 0.5)

        return FitnessMetrics(
            wealth=wealth,
            security=security,
            reputation=reputation,
            fairness=fairness,
            compliance=compliance,
            tick=tick,
        )
