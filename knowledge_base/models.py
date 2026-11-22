"""Data models for the Ideological Knowledge Base subsystem."""

import math
from typing import Dict, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

REQUIRED_UTILITY_KEYS = {"wealth", "security", "reputation", "fairness", "compliance"}


class IdeologicalProfile(BaseModel):
    """Authoritative representation of an ideological or strategic doctrine."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., alias="category_id")
    domain: str
    title: str
    key_thinkers: List[str] = Field(default_factory=list)
    axioms: List[str] = Field(default_factory=list, alias="core_axioms")
    utility_weights: Dict[str, float]
    decision_heuristics: List[str] = Field(default_factory=list)
    conflict_resolution_style: str = "principled_detachment"
    failure_modes: List[str] = Field(default_factory=list)
    cross_references: List[str] = Field(default_factory=list)
    narrative_body: str = ""

    @property
    def category_id(self) -> str:
        """Alias for category identifier."""
        return self.id

    @property
    def core_axioms(self) -> List[str]:
        """Alias for foundational axioms."""
        return self.axioms

    @field_validator("axioms", mode="before")
    @classmethod
    def validate_axioms_non_empty(cls, v: Any) -> List[str]:
        """Enforces that core axioms list is non-empty."""
        if not v or not isinstance(v, list) or len(v) == 0:
            raise ValueError("Axioms list must be non-empty.")
        return [str(x) for x in v]

    @field_validator("utility_weights")
    @classmethod
    def validate_utility_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validates that utility weights contain required keys and sum to 1.0."""
        missing = REQUIRED_UTILITY_KEYS - set(v.keys())
        if missing:
            raise ValueError(f"utility_weights missing required keys: {sorted(missing)}")
        for k in REQUIRED_UTILITY_KEYS:
            val = v[k]
            if val is None or math.isnan(val) or math.isinf(val):
                raise ValueError(f"utility_weight for '{k}' must not be NaN or Inf, got {val}")
        total = sum(v[k] for k in REQUIRED_UTILITY_KEYS)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(
                f"utility_weights must sum to 1.0 (with 1e-4 tolerance); current sum: {total:.6f}"
            )
        for k in REQUIRED_UTILITY_KEYS:
            if v[k] < -1e-6 or v[k] > 1.0 + 1e-6:
                raise ValueError(
                    f"utility_weight for '{k}' must be bounded in [0.0, 1.0], got {v[k]}"
                )
        return v

    @property
    def system_prompt_overlay(self) -> str:
        """Synthesizes axioms, heuristics, and conflict resolution style into an actionable system prompt."""
        axioms_str = "\n".join(f"- {a}" for a in self.axioms)
        heuristics_str = "\n".join(f"- {h}" for h in self.decision_heuristics)
        weights_str = ", ".join(
            f"{k}: {self.utility_weights[k]:.2f}"
            for k in sorted(self.utility_weights.keys())
        )
        overlay = (
            f"### Active Ideology: {self.title} [{self.id}]\n"
            f"Domain: {self.domain} | Conflict Resolution Style: {self.conflict_resolution_style}\n"
            f"Utility Priorities: {weights_str}\n\n"
            f"Core Axioms:\n{axioms_str}\n\n"
            f"Decision Heuristics:\n{heuristics_str}"
        )
        return overlay
