"""
EON Society Clan Survival & Metabolic Scarcity Engine
Manages collective emergency ration & energy pools, daily metabolic life-support burn,
and starvation crisis triggers across Clans.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


class SurvivalStatus:
    PROSPEROUS = "PROSPEROUS"         # > 75%
    STABLE = "STABLE"                 # 45% - 75%
    STRESSED = "STRESSED"             # 25% - 45%
    STARVATION_CRISIS = "STARVATION"  # 1% - 25%
    COLLAPSED = "COLLAPSED"           # <= 0%


@dataclass
class ClanSurvivalPool:
    clan_name: str
    display_title: str
    energy_reserve: float = 600.0
    ration_reserve: float = 400.0
    max_energy: float = 800.0
    max_rations: float = 600.0
    headcount: int = 10  # Clan population / kinship unit
    daily_energy_burn_rate: float = 12.0
    daily_ration_burn_rate: float = 8.0

    @property
    def total_vitality_percent(self) -> float:
        energy_pct = (self.energy_reserve / self.max_energy) if self.max_energy > 0 else 0
        ration_pct = (self.ration_reserve / self.max_rations) if self.max_rations > 0 else 0
        return round(((energy_pct + ration_pct) / 2.0) * 100.0, 1)

    @property
    def status(self) -> str:
        pct = self.total_vitality_percent
        if pct <= 0:
            return SurvivalStatus.COLLAPSED
        elif pct <= 25.0:
            return SurvivalStatus.STARVATION_CRISIS
        elif pct <= 45.0:
            return SurvivalStatus.STRESSED
        elif pct <= 75.0:
            return SurvivalStatus.STABLE
        return SurvivalStatus.PROSPEROUS

    def burn_metabolism(self) -> Dict[str, Any]:
        """Apply one tick of metabolic life-support consumption."""
        energy_cost = self.headcount * self.daily_energy_burn_rate
        ration_cost = self.headcount * self.daily_ration_burn_rate

        self.energy_reserve = max(0.0, self.energy_reserve - energy_cost)
        self.ration_reserve = max(0.0, self.ration_reserve - ration_cost)

        return {
            "clan": self.clan_name,
            "energy_consumed": energy_cost,
            "rations_consumed": ration_cost,
            "energy_remaining": self.energy_reserve,
            "rations_remaining": self.ration_reserve,
            "vitality_pct": self.total_vitality_percent,
            "status": self.status,
        }

    def replenish(self, energy: float = 0.0, rations: float = 0.0) -> None:
        """Add resources acquired via production, trade, or court levies."""
        self.energy_reserve = min(self.max_energy, self.energy_reserve + max(0.0, energy))
        self.ration_reserve = min(self.max_rations, self.ration_reserve + max(0.0, rations))


class MetabolicEngine:
    """Manages all clan collective pools and daily survival calculations."""

    def __init__(self):
        self.pools: Dict[str, ClanSurvivalPool] = {
            "clan_alpha_technocrats": ClanSurvivalPool(
                clan_name="clan_alpha_technocrats",
                display_title="Clan Alpha (The Technocrats)",
                energy_reserve=650.0,
                ration_reserve=350.0,
                headcount=12,
            ),
            "clan_beta_merchants": ClanSurvivalPool(
                clan_name="clan_beta_merchants",
                display_title="Clan Beta (The Merchants)",
                energy_reserve=420.0,
                ration_reserve=550.0,
                headcount=14,
            ),
            "clan_gamma_jurists": ClanSurvivalPool(
                clan_name="clan_gamma_jurists",
                display_title="Clan Gamma (The Jurists)",
                energy_reserve=500.0,
                ration_reserve=450.0,
                headcount=10,
            ),
        }

    def get_pool(self, clan_id: str) -> ClanSurvivalPool:
        return self.pools.get(clan_id)

    def execute_daily_drain(self) -> Dict[str, Dict[str, Any]]:
        """Apply daily metabolic life-support drain across all clans."""
        report = {}
        for clan_id, pool in self.pools.items():
            report[clan_id] = pool.burn_metabolism()
        return report

    def get_society_survival_summary(self) -> Dict[str, Any]:
        """Generate structured status for Observer journal reporting."""
        summary = {}
        for clan_id, pool in self.pools.items():
            summary[clan_id] = {
                "title": pool.display_title,
                "vitality_pct": pool.total_vitality_percent,
                "status": pool.status,
                "energy": round(pool.energy_reserve, 1),
                "rations": round(pool.ration_reserve, 1),
                "headcount": pool.headcount,
            }
        return summary
