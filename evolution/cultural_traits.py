"""
evolution/cultural_traits.py
EON 2.0 Cultural Trait Registry and Evolutionary Dynamics.
Supports 6 transmission mechanisms (vertical, horizontal, oblique, prestige, success, conformist),
variation, selection, retention, transformation, and extinction.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TransmissionType(str, Enum):
    VERTICAL = "vertical"           # parent -> child
    HORIZONTAL = "horizontal"       # peer -> peer
    OBLIQUE = "oblique"             # elder -> youth (not parent)
    PRESTIGE = "prestige"           # copy high-status agents
    SUCCESS = "success"             # copy successful/wealthy agents
    CONFORMIST = "conformist"       # copy majority behavior


class TraitStatus(str, Enum):
    EMERGING = "emerging"
    ESTABLISHED = "established"
    DECLINING = "declining"
    EXTINCT = "extinct"


@dataclass
class CulturalTrait:
    trait_id: str
    name: str
    category: str           # e.g. "economic", "social", "religious", "political"
    creator_agent: str
    origin_day: int
    description: str
    transmission_type: TransmissionType
    adoption_history: List[dict] = field(default_factory=list)
    # Each entry: {"agent": name, "day": day, "source_agent": str}
    status: TraitStatus = TraitStatus.EMERGING
    economic_effects: dict = field(default_factory=dict)
    # e.g. {"income_modifier": 0.1, "cost_modifier": -0.05}
    social_effects: dict = field(default_factory=dict)
    # e.g. {"cooperation_boost": 0.2, "conflict_risk": -0.1}
    parent_trait_id: Optional[str] = None  # lineage tracking
    transformed_traits: List[str] = field(default_factory=list)

    def record_adoption(self, agent: str, day: int, source_agent: str = "") -> None:
        self.adoption_history.append({
            "agent": agent,
            "day": day,
            "source_agent": source_agent,
            "timestamp": int(time.time()),
        })
        # If trait reaches critical mass, mark established
        if self.adopter_count() >= 5 and self.status == TraitStatus.EMERGING:
            self.status = TraitStatus.ESTABLISHED

    def record_transformation(self, new_trait: "CulturalTrait") -> None:
        new_trait.parent_trait_id = self.trait_id
        if new_trait.trait_id not in self.transformed_traits:
            self.transformed_traits.append(new_trait.trait_id)

    def mark_extinct(self, day: int) -> None:
        self.status = TraitStatus.EXTINCT

    def adopter_count(self) -> int:
        """Return count of unique agents who have adopted this trait."""
        unique_agents = {entry["agent"] for entry in self.adoption_history}
        return len(unique_agents)


class CulturalTraitRegistry:
    """Global registry of cultural traits in the civilization."""

    def __init__(self):
        self._traits: Dict[str, CulturalTrait] = {}

    def register_new_trait(
        self,
        name: str,
        category: str,
        creator: str,
        day: int,
        description: str,
        transmission_type: TransmissionType,
        economic_effects: dict = None,
        social_effects: dict = None,
        parent_trait_id: str = None,
    ) -> CulturalTrait:
        trait_id = f"trait_{uuid.uuid4().hex[:8]}"
        trait = CulturalTrait(
            trait_id=trait_id,
            name=name,
            category=category,
            creator_agent=creator,
            origin_day=day,
            description=description,
            transmission_type=transmission_type,
            economic_effects=economic_effects or {},
            social_effects=social_effects or {},
            parent_trait_id=parent_trait_id,
        )
        # Record initial adoption by creator
        trait.record_adoption(agent=creator, day=day, source_agent="")
        self._traits[trait_id] = trait
        return trait

    def record_adoption(
        self,
        trait_id: str,
        agent: str,
        day: int,
        source_agent: str = "",
    ) -> bool:
        trait = self._traits.get(trait_id)
        if not trait or trait.status == TraitStatus.EXTINCT:
            return False
        trait.record_adoption(agent, day, source_agent)
        return True

    def record_transformation(
        self,
        original_trait_id: str,
        new_trait: CulturalTrait,
    ) -> None:
        original = self._traits.get(original_trait_id)
        if original:
            original.record_transformation(new_trait)
        self._traits[new_trait.trait_id] = new_trait

    def record_extinction(self, trait_id: str, day: int) -> None:
        trait = self._traits.get(trait_id)
        if trait:
            trait.mark_extinct(day)

    def get_active_traits(self) -> List[CulturalTrait]:
        return [t for t in self._traits.values() if t.status != TraitStatus.EXTINCT]

    def get_traits_by_agent(self, agent: str) -> List[CulturalTrait]:
        results = []
        for trait in self._traits.values():
            if any(e["agent"] == agent for e in trait.adoption_history):
                results.append(trait)
        return results

    def get_trait(self, trait_id: str) -> Optional[CulturalTrait]:
        return self._traits.get(trait_id)

    def save_state(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {}
        for tid, t in self._traits.items():
            data[tid] = {
                "trait_id": t.trait_id,
                "name": t.name,
                "category": t.category,
                "creator_agent": t.creator_agent,
                "origin_day": t.origin_day,
                "description": t.description,
                "transmission_type": t.transmission_type.value,
                "adoption_history": t.adoption_history,
                "status": t.status.value,
                "economic_effects": t.economic_effects,
                "social_effects": t.social_effects,
                "parent_trait_id": t.parent_trait_id,
                "transformed_traits": t.transformed_traits,
            }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._traits = {}
        for tid, d in data.items():
            trait = CulturalTrait(
                trait_id=d["trait_id"],
                name=d["name"],
                category=d["category"],
                creator_agent=d["creator_agent"],
                origin_day=d["origin_day"],
                description=d["description"],
                transmission_type=TransmissionType(d["transmission_type"]),
                adoption_history=d["adoption_history"],
                status=TraitStatus(d["status"]),
                economic_effects=d.get("economic_effects", {}),
                social_effects=d.get("social_effects", {}),
                parent_trait_id=d.get("parent_trait_id"),
                transformed_traits=d.get("transformed_traits", []),
            )
            self._traits[tid] = trait
        return True


default_registry = CulturalTraitRegistry()
