"""
EON Kinship, Domestic Lineage, and Outlawry Engine
Models domestic households (H_i), named agents (e.g., Prometheus), spouses,
dependent children, water cistern reserves, grain rations, living standard metrics,
and outlaw bandit defection when clans fail to provide basic sustenance.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import os


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
        # Domestic reserves + clan per-capita provisioning
        water_ratio = min(1.0, (self.water_cistern_reserve + clan_water_per_capita) / (self.total_dependents * 15.0))
        food_ratio = min(1.0, (self.grain_ration_reserve + clan_food_per_capita) / (self.total_dependents * 10.0))
        
        # Child penalty if children are hungry
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

    def execute_daily_kinship_cycle(self, clan_water_per_capita: Dict[str, float], clan_food_per_capita: Dict[str, float]) -> Dict[str, Any]:
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
