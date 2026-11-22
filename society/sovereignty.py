"""
EON Sovereignty & Dynastic Fission Engine
Monitors clan populations and triggers organic fission based on socio-economic
conditions: Gini inequality, dispute frequency, and member petitions.
Breakaway factions establish independent kingdoms with sovereign charters,
territorial borders, and dynamic foreign policy (treaties vs. resource wars).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import os
import uuid

# ---------------------------------------------------------------------------
# Organic fission thresholds (replace legacy headcount threshold)
# ---------------------------------------------------------------------------
FISSION_GINI_THRESHOLD = 0.45
FISSION_DISPUTE_COUNT = 5
FISSION_PETITION_FRACTION = 0.30

# Legacy headcount threshold kept only for backward-compat with FissionEngine
_FISSION_HEADCOUNT_THRESHOLD = 20


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SovereignKingdom:
    kingdom_id: str
    kingdom_name: str
    parent_clan: str
    population: int
    charter_preamble: str
    allied_factions: List[str] = field(default_factory=list)
    hostile_factions: List[str] = field(default_factory=list)
    treasury_balance: float = 100.0
    water_reserve: float = 200.0


# ---------------------------------------------------------------------------
# Socio-economic fission trigger
# ---------------------------------------------------------------------------

class SocioEconomicFissionTrigger:
    """
    Evaluates organic socio-economic conditions that may precipitate clan fission:
    - Gini wealth inequality above threshold
    - Accumulated dispute count above threshold
    - A sufficient fraction of members formally petitioning for split
    """

    def check_gini_trigger(self, clan_name: str, member_balances: dict) -> bool:
        """Return True if Gini coefficient of member_balances > FISSION_GINI_THRESHOLD."""
        values = sorted(member_balances.values())
        n = len(values)
        if n == 0:
            return False
        total = sum(values)
        if total == 0:
            return False
        # Standard formula: G = (2 * sum((i+1) * x_i)) / (n * total) - (n+1)/n
        gini_sum = sum((i + 1) * v for i, v in enumerate(values))
        gini = (2 * gini_sum) / (n * total) - (n + 1) / n
        return gini > FISSION_GINI_THRESHOLD

    def check_dispute_trigger(self, clan_name: str, dispute_count: int) -> bool:
        """Return True if dispute_count >= FISSION_DISPUTE_COUNT."""
        return dispute_count >= FISSION_DISPUTE_COUNT

    def check_petition_trigger(self, petitioners: list, total_members: int) -> bool:
        """Return True if fraction of petitioners >= FISSION_PETITION_FRACTION."""
        if total_members == 0:
            return False
        return (len(petitioners) / total_members) >= FISSION_PETITION_FRACTION

    def evaluate_fission(
        self,
        clan_name: str,
        member_balances: dict,
        dispute_count: int,
        petitioners: list,
    ) -> dict:
        """
        Evaluate all triggers and return a summary dict:
            {"should_fission": bool, "triggers": [str], "reason": str}
        """
        total_members = len(member_balances)
        triggers: List[str] = []

        if self.check_gini_trigger(clan_name, member_balances):
            triggers.append("gini_inequality")

        if self.check_dispute_trigger(clan_name, dispute_count):
            triggers.append("dispute_accumulation")

        if self.check_petition_trigger(petitioners, total_members):
            triggers.append("member_petition")

        should_fission = len(triggers) > 0
        if should_fission:
            reason = (
                f"Clan {clan_name!r} meets fission conditions: "
                + ", ".join(triggers)
            )
        else:
            reason = f"Clan {clan_name!r} is stable; no fission triggers met."

        return {
            "should_fission": should_fission,
            "triggers": triggers,
            "reason": reason,
        }


# ---------------------------------------------------------------------------
# Kingdom formation engine
# ---------------------------------------------------------------------------

class KingdomFormationEngine:
    """
    Manages the lifecycle of multi-clan kingdoms: formation, membership,
    rulership succession, and persistent state.
    """

    def __init__(self):
        self.kingdoms: Dict[str, dict] = {}

    def declare_kingdom(
        self,
        name: str,
        ruler: str,
        founding_members: list,
        treasury_account: str,
        day: int,
    ) -> str:
        """Declare a new kingdom.  Returns the generated kingdom_id."""
        kingdom_id = f"kgm_{uuid.uuid4().hex[:8]}"
        self.kingdoms[kingdom_id] = {
            "kingdom_id": kingdom_id,
            "name": name,
            "ruler": ruler,
            "members": list(founding_members),
            "treasury_account": treasury_account,
            "founded_day": day,
        }
        return kingdom_id

    def add_member(self, kingdom_id: str, agent: str) -> bool:
        if kingdom_id not in self.kingdoms:
            return False
        if agent not in self.kingdoms[kingdom_id]["members"]:
            self.kingdoms[kingdom_id]["members"].append(agent)
        return True

    def remove_member(self, kingdom_id: str, agent: str) -> bool:
        if kingdom_id not in self.kingdoms:
            return False
        try:
            self.kingdoms[kingdom_id]["members"].remove(agent)
            return True
        except ValueError:
            return False

    def set_ruler(self, kingdom_id: str, new_ruler: str) -> bool:
        if kingdom_id not in self.kingdoms:
            return False
        self.kingdoms[kingdom_id]["ruler"] = new_ruler
        return True

    def get_kingdom(self, kingdom_id: str) -> dict:
        return self.kingdoms.get(kingdom_id, {})

    def list_kingdoms(self) -> list:
        return list(self.kingdoms.values())

    def save_state(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.kingdoms, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            self.kingdoms = json.load(f)
        return True


# ---------------------------------------------------------------------------
# Legacy FissionEngine — API preserved for test_sovereignty.py
# ---------------------------------------------------------------------------

class FissionEngine:
    """
    Evaluates clan headcount and executes institutional fission into sovereign kingdoms.

    The class-level FISSION_HEADCOUNT_THRESHOLD attribute is kept for backward
    compatibility; organic socio-economic triggers are exposed via
    SocioEconomicFissionTrigger.
    """

    FISSION_HEADCOUNT_THRESHOLD = _FISSION_HEADCOUNT_THRESHOLD

    def __init__(self):
        self.sovereign_kingdoms: Dict[str, SovereignKingdom] = {}
        self.fission_history: List[Dict[str, Any]] = []

    def check_and_execute_fission(
        self, clan_id: str, current_headcount: int
    ) -> Optional[SovereignKingdom]:
        """
        If headcount >= 20, split the clan, creating a new sovereign kingdom.
        Returns the new SovereignKingdom if fission occurred, else None.
        """
        if current_headcount >= self.FISSION_HEADCOUNT_THRESHOLD:
            breakaway_size = current_headcount // 2
            kid = f"kingdom_{clan_id}_{len(self.sovereign_kingdoms) + 1}"
            kname = (
                f"Free Sovereign Realm of "
                f"{clan_id.replace('clan_', '').replace('_', ' ').title()}"
            )

            charter = (
                f"We, the {breakaway_size} free citizens formerly of {clan_id}, "
                f"hereby declare our sovereign independence. Under extreme survival imperatives, "
                f"we establish this autonomous realm to secure our drinking water, harvest rights, "
                f"and domestic lineages."
            )

            new_kingdom = SovereignKingdom(
                kingdom_id=kid,
                kingdom_name=kname,
                parent_clan=clan_id,
                population=breakaway_size,
                charter_preamble=charter,
                hostile_factions=[clan_id],
            )

            self.sovereign_kingdoms[kid] = new_kingdom
            self.fission_history.append(
                {
                    "tick_event": "DYNASTIC_FISSION",
                    "parent_clan": clan_id,
                    "kingdom_id": kid,
                    "kingdom_name": kname,
                    "breakaway_population": breakaway_size,
                    "charter": charter,
                }
            )
            return new_kingdom
        return None

    def get_kingdoms(self) -> List[SovereignKingdom]:
        return list(self.sovereign_kingdoms.values())

    def save_state(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {
            "sovereign_kingdoms": {
                kid: {
                    "kingdom_id": k.kingdom_id,
                    "kingdom_name": k.kingdom_name,
                    "parent_clan": k.parent_clan,
                    "population": k.population,
                    "charter_preamble": k.charter_preamble,
                    "allied_factions": k.allied_factions,
                    "hostile_factions": k.hostile_factions,
                    "treasury_balance": k.treasury_balance,
                    "water_reserve": k.water_reserve,
                }
                for kid, k in self.sovereign_kingdoms.items()
            },
            "fission_history": self.fission_history,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.sovereign_kingdoms = {}
        for kid, kd in data.get("sovereign_kingdoms", {}).items():
            self.sovereign_kingdoms[kid] = SovereignKingdom(**kd)
        self.fission_history = data.get("fission_history", [])
        return True
