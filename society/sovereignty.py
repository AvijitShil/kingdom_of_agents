"""
EON Sovereignty & Dynastic Fission Engine
Monitors clan populations and triggers mitotic fission when headcount reaches >= 20.
Breakaway factions establish independent kingdoms with sovereign charters,
territorial borders, and dynamic foreign policy (treaties vs. resource wars).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import os


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


class FissionEngine:
    """Evaluates clan headcount and executes institutional fission into sovereign kingdoms."""

    FISSION_HEADCOUNT_THRESHOLD = 20

    def __init__(self):
        self.sovereign_kingdoms: Dict[str, SovereignKingdom] = {}
        self.fission_history: List[Dict[str, Any]] = []

    def check_and_execute_fission(self, clan_id: str, current_headcount: int) -> Optional[SovereignKingdom]:
        """
        If headcount >= 20, split the clan, creating a new sovereign kingdom.
        Returns the new SovereignKingdom if fission occurred, else None.
        """
        if current_headcount >= self.FISSION_HEADCOUNT_THRESHOLD:
            breakaway_size = current_headcount // 2
            kid = f"kingdom_{clan_id}_{len(self.sovereign_kingdoms) + 1}"
            kname = f"Free Sovereign Realm of {clan_id.replace('clan_', '').replace('_', ' ').title()}"
            
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
                hostile_factions=[clan_id],  # Initial competitive friction with parent clan
            )
            
            self.sovereign_kingdoms[kid] = new_kingdom
            self.fission_history.append({
                "tick_event": "DYNASTIC_FISSION",
                "parent_clan": clan_id,
                "kingdom_id": kid,
                "kingdom_name": kname,
                "breakaway_population": breakaway_size,
                "charter": charter,
            })
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
