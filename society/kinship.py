"""
EON Kinship, Domestic Lineage, and Outlawry Engine
EON 2.0: Adds Greek naming pool, reproduction controller, and parental education.
Models domestic households, named agents, spouses, dependent children, water/grain
reserves, living standard metrics, and outlaw bandit defection.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
import json
import os
import random


# ──────────────────────────────────────────────────────────────────────────────
# Legacy household / kinship API (kept for test_kinship.py backward compatibility)
# ──────────────────────────────────────────────────────────────────────────────

class CitizenStatus:
    CIVILIAN = "CIVILIAN"
    DISCONTENT = "DISCONTENT"
    STRIKING = "STRIKING"
    OUTLAW = "OUTLAW"


@dataclass
class Household:
    agent_id: str
    agent_name: str
    clan_id: str
    spouse_name: Optional[str] = None
    num_children: int = 0
    water_cistern_reserve: float = 50.0  # Clean drinking water liters
    grain_ration_reserve: float = 40.0   # Food rations kg
    living_standard_score: float = 1.0   # Scale 0.0 - 1.0
    status: str = CitizenStatus.CIVILIAN
    consecutive_starvation_ticks: int = 0
    bandit_camp: Optional[str] = None

    @property
    def total_dependents(self) -> int:
        count = 1  # the agent themself
        if self.spouse_name:
            count += 1
        count += self.num_children
        return count

    def calculate_living_standard(self, clan_water_per_capita: float, clan_food_per_capita: float) -> float:
        """
        L_i = beta1 * Water_Security + beta2 * Food_Abundance + beta3 * Child_Health
        """
        water_ratio = min(1.0, (self.water_cistern_reserve + clan_water_per_capita) / (self.total_dependents * 15.0))
        food_ratio = min(1.0, (self.grain_ration_reserve + clan_food_per_capita) / (self.total_dependents * 10.0))

        child_health = 1.0
        if self.num_children > 0 and (water_ratio < 0.4 or food_ratio < 0.4):
            child_health = max(0.1, (water_ratio + food_ratio) / 2.0)

        score = (0.45 * water_ratio) + (0.35 * food_ratio) + (0.20 * child_health)
        self.living_standard_score = round(max(0.0, min(1.0, score)), 3)
        return self.living_standard_score

    def consume_daily_rations(self) -> Dict[str, Any]:
        """Daily domestic consumption for agent, spouse, and children."""
        water_need = self.total_dependents * 3.0
        grain_need = self.total_dependents * 2.0

        water_consumed = min(self.water_cistern_reserve, water_need)
        grain_consumed = min(self.grain_ration_reserve, grain_need)

        self.water_cistern_reserve = max(0.0, self.water_cistern_reserve - water_consumed)
        self.grain_ration_reserve = max(0.0, self.grain_ration_reserve - grain_consumed)

        is_starving = (water_consumed < water_need * 0.5) or (grain_consumed < grain_need * 0.5)
        if is_starving:
            self.consecutive_starvation_ticks += 1
        else:
            self.consecutive_starvation_ticks = max(0, self.consecutive_starvation_ticks - 1)

        # Update political status
        if self.status != CitizenStatus.OUTLAW:
            if self.consecutive_starvation_ticks >= 2 or self.living_standard_score < 0.25:
                self.status = CitizenStatus.OUTLAW
                self.bandit_camp = f"Bandits_of_{self.clan_id}"
            elif self.consecutive_starvation_ticks == 1 or self.living_standard_score < 0.5:
                self.status = CitizenStatus.DISCONTENT
            else:
                self.status = CitizenStatus.CIVILIAN

        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "water_reserve": self.water_cistern_reserve,
            "grain_reserve": self.grain_ration_reserve,
            "living_standard": self.living_standard_score,
            "status": self.status,
            "starving": is_starving,
            "starvation_ticks": self.consecutive_starvation_ticks,
        }

    def raid_caravan(self, target_clan: str, loot_water: float, loot_grain: float) -> None:
        """Outlaw bandit survival raid to feed starving dependents."""
        if self.status == CitizenStatus.OUTLAW:
            self.water_cistern_reserve += loot_water
            self.grain_ration_reserve += loot_grain


class KinshipRegistry:
    """Manages all agent households, domestic relations, and outlaw tracking."""

    def __init__(self):
        self.households: Dict[str, Household] = {}
        self._initialize_canonical_households()

    def _initialize_canonical_households(self):
        """Populate initial canonical families for core agents."""
        initial = [
            Household(
                agent_id="scholar-01",
                agent_name="Prometheus",
                clan_id="clan_alpha_technocrats",
                spouse_name="Pyrrha",
                num_children=2,
                water_cistern_reserve=80.0,
                grain_ration_reserve=60.0,
            ),
            Household(
                agent_id="trader-01",
                agent_name="Mercator",
                clan_id="clan_beta_merchants",
                spouse_name="Aurelia",
                num_children=3,
                water_cistern_reserve=60.0,
                grain_ration_reserve=120.0,
            ),
            Household(
                agent_id="justiciar-01",
                agent_name="Solon",
                clan_id="clan_gamma_jurists",
                spouse_name="Themis",
                num_children=1,
                water_cistern_reserve=70.0,
                grain_ration_reserve=70.0,
            ),
            Household(
                agent_id="archivist-01",
                agent_name="Callimachus",
                clan_id="clan_gamma_jurists",
                spouse_name="Kalliope",
                num_children=0,
                water_cistern_reserve=55.0,
                grain_ration_reserve=50.0,
            ),
        ]
        for h in initial:
            self.households[h.agent_id] = h

    def get_household(self, agent_id: str) -> Optional[Household]:
        return self.households.get(agent_id)

    def register_household(self, household: Household) -> None:
        self.households[household.agent_id] = household

    def get_outlaws(self) -> List[Household]:
        return [h for h in self.households.values() if h.status == CitizenStatus.OUTLAW]

    def execute_daily_kinship_cycle(
        self,
        clan_water_per_capita: Dict[str, float],
        clan_food_per_capita: Dict[str, float],
    ) -> Dict[str, Any]:
        """Update living standards and consume domestic food/water for all households."""
        results = {}
        for aid, h in self.households.items():
            w_cap = clan_water_per_capita.get(h.clan_id, 10.0)
            f_cap = clan_food_per_capita.get(h.clan_id, 10.0)
            h.calculate_living_standard(w_cap, f_cap)
            res = h.consume_daily_rations()
            results[aid] = res
        return results

    def save_state(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {aid: {
            "agent_id": h.agent_id,
            "agent_name": h.agent_name,
            "clan_id": h.clan_id,
            "spouse_name": h.spouse_name,
            "num_children": h.num_children,
            "water_cistern_reserve": h.water_cistern_reserve,
            "grain_ration_reserve": h.grain_ration_reserve,
            "living_standard_score": h.living_standard_score,
            "status": h.status,
            "consecutive_starvation_ticks": h.consecutive_starvation_ticks,
            "bandit_camp": h.bandit_camp,
        } for aid, h in self.households.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.households = {}
        for aid, d in data.items():
            self.households[aid] = Household(**d)
        return True


# ──────────────────────────────────────────────────────────────────────────────
# EON 2.0: Greek naming, reproduction, and parental education
# ──────────────────────────────────────────────────────────────────────────────

GREEK_NAME_POOL = [
    # Female
    "Alkmene", "Andromeda", "Antigone", "Ariadne", "Cassandra", "Clio", "Danae",
    "Electra", "Eurydice", "Hecate", "Helen", "Hera", "Io", "Iris", "Medea",
    "Nausikaa", "Niobe", "Pasiphae", "Penelope", "Persephone", "Phaedra",
    "Semele", "Thetis", "Zoe",
    # Male
    "Achilles", "Adonis", "Ajax", "Aristotle", "Bellerophon", "Deucalion",
    "Diomedes", "Euclid", "Hector", "Hippocrates", "Icarus", "Jason", "Leander",
    "Leonidas", "Midas", "Narcissus", "Odysseus", "Oedipus", "Patroclus",
    "Pericles", "Perseus", "Plato", "Poseidon", "Pyrrhus", "Socrates",
    "Tantalus", "Theseus", "Xenophon", "Zephyr", "Zenobia",
]

# Roman numeral suffixes for pool exhaustion fallback
_ROMAN = ["", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
          "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]


class GreekNamingRegistry:
    """Generates unique Greek names for newborn agents."""

    def __init__(self):
        self.used_names: Set[str] = set()

    def generate_child_name(self, parent1: str, parent2: str) -> str:
        """
        Return a unique name from GREEK_NAME_POOL not already used.
        If pool is exhausted, generates 'Name_II', 'Name_III' variants.
        """
        # Try pool names first (shuffle for variety)
        pool = [n for n in GREEK_NAME_POOL if n not in self.used_names]
        if pool:
            # Prefer names unrelated to parents for variety
            name = random.choice(pool)
            self.used_names.add(name)
            return name

        # Pool exhausted — generate suffixed variants
        for base in GREEK_NAME_POOL:
            for suffix in _ROMAN[2:]:  # II, III, ...
                candidate = f"{base}_{suffix}"
                if candidate not in self.used_names:
                    self.used_names.add(candidate)
                    return candidate

        # Absolute fallback (practically unreachable)
        import uuid
        fallback = f"Agent_{uuid.uuid4().hex[:6]}"
        self.used_names.add(fallback)
        return fallback


class ReproductionController:
    """Controls daily birth rates and reproduction eligibility."""

    MAX_DAILY_BIRTHS = 10
    MIN_REPRODUCTION_BALANCE = 28  # 2x daily upkeep

    def __init__(self):
        self.global_daily_births: int = 0
        self._births_this_day: List[dict] = []

    def can_reproduce(self, parent1_balance: int, parent2_balance: int) -> bool:
        """
        Returns True iff:
        - Neither parent's balance is below MIN_REPRODUCTION_BALANCE
        - Daily birth cap not yet reached
        """
        if self.global_daily_births >= self.MAX_DAILY_BIRTHS:
            return False
        return (
            parent1_balance >= self.MIN_REPRODUCTION_BALANCE
            and parent2_balance >= self.MIN_REPRODUCTION_BALANCE
        )

    def register_birth(
        self,
        child_name: str,
        parent1: str,
        parent2: str,
        day: int,
    ) -> dict:
        """
        Register a new birth event.
        Returns birth record dict.
        """
        self.global_daily_births += 1
        record = {
            "child": child_name,
            "parent1": parent1,
            "parent2": parent2,
            "day": day,
            "birth_number_today": self.global_daily_births,
        }
        self._births_this_day.append(record)
        return record

    def reset_daily_counter(self) -> None:
        """Call at the start of each new simulated day."""
        self.global_daily_births = 0
        self._births_this_day = []


# Mutation tokens — simple string transforms representing cultural drift
_MUTATION_PREFIXES = ["Neo-", "Proto-", "Meta-", "Anti-", "Hyper-"]
_MUTATION_SUFFIXES = ["-ism", "-craft", "-lore", "-way", "-art"]


class ParentalEducation:
    """Models knowledge transfer from parent to child with possible trait mutation."""

    def transfer_knowledge(
        self,
        parent: str,
        child: str,
        parent_cultural_traits: list,
        day: int,
    ) -> dict:
        """
        Transfer cultural traits from parent to child.
        Each trait has a 10% chance of mutating (string modification).

        Returns:
            {
                "child": name,
                "inherited_traits": list,
                "day": day,
            }
        """
        inherited_traits = []
        for trait in parent_cultural_traits:
            if random.random() < 0.10:
                # Mutate the trait
                mutation_type = random.choice(["prefix", "suffix", "replace"])
                if mutation_type == "prefix":
                    mutated = random.choice(_MUTATION_PREFIXES) + str(trait)
                elif mutation_type == "suffix":
                    mutated = str(trait) + random.choice(_MUTATION_SUFFIXES)
                else:
                    # Replace entire trait with a random adjacent concept
                    mutated = f"{trait}[evolved]"
                inherited_traits.append(mutated)
            else:
                inherited_traits.append(trait)

        return {
            "child": child,
            "inherited_traits": inherited_traits,
            "day": day,
        }
