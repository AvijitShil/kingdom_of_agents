"""
EON Society Clan Survival & Metabolic Scarcity Engine
EON 2.0: Human-token economy survival model.
Manages collective emergency ration & energy pools (backward-compatible),
AND individual agent survival profiles with token-based daily upkeep.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import os


# ──────────────────────────────────────────────────────────────────────────────
# Legacy clan-pool API (kept for test_survival_pool.py backward compatibility)
# ──────────────────────────────────────────────────────────────────────────────

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

    def save_state(self, filepath: str) -> None:
        """Persist current clan survival pool reserves to JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {}
        for clan_id, pool in self.pools.items():
            data[clan_id] = {
                "clan_name": pool.clan_name,
                "display_title": pool.display_title,
                "energy_reserve": pool.energy_reserve,
                "ration_reserve": pool.ration_reserve,
                "max_energy": pool.max_energy,
                "max_rations": pool.max_rations,
                "headcount": pool.headcount,
                "daily_energy_burn_rate": pool.daily_energy_burn_rate,
                "daily_ration_burn_rate": pool.daily_ration_burn_rate,
            }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        """Load clan survival pool reserves from JSON."""
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for clan_id, pool_data in data.items():
            if clan_id in self.pools:
                self.pools[clan_id].energy_reserve = pool_data.get("energy_reserve", self.pools[clan_id].energy_reserve)
                self.pools[clan_id].ration_reserve = pool_data.get("ration_reserve", self.pools[clan_id].ration_reserve)
                self.pools[clan_id].headcount = pool_data.get("headcount", self.pools[clan_id].headcount)
            else:
                self.pools[clan_id] = ClanSurvivalPool(**pool_data)
        return True


# ──────────────────────────────────────────────────────────────────────────────
# EON 2.0: Individual agent survival with token economy
# ──────────────────────────────────────────────────────────────────────────────

# Survival costs per simulated day (tokens)
FOOD_COST = 5
WATER_COST = 4
SHELTER_COST = 3
HEALTHCARE_COST = 2
DAILY_UPKEEP = 14  # total

# Minimum survival (food + water); below this → CRITICAL
SURVIVAL_MINIMUM = FOOD_COST + WATER_COST  # 9


class SurvivalState(str, Enum):
    SECURE = "SECURE"      # balance > 3x upkeep  (> 42)
    WARNING = "WARNING"    # balance 1x-3x upkeep  (14-42)
    DEPRIVED = "DEPRIVED"  # balance 0.5x-1x upkeep (7-13)
    CRITICAL = "CRITICAL"  # balance < 0.5x upkeep  (< 7)
    DECEASED = "DECEASED"  # 3 consecutive CRITICAL days


@dataclass
class AgentSurvivalProfile:
    name: str
    state: SurvivalState = SurvivalState.SECURE
    consecutive_critical_days: int = 0
    last_upkeep_day: int = -1

    def evaluate_state(self, balance: int) -> SurvivalState:
        """Compute the survival state from a token balance (does NOT modify self.state)."""
        if self.state == SurvivalState.DECEASED:
            return SurvivalState.DECEASED
        if balance > 3 * DAILY_UPKEEP:
            return SurvivalState.SECURE
        elif balance >= DAILY_UPKEEP:
            return SurvivalState.WARNING
        elif balance >= DAILY_UPKEEP // 2:
            return SurvivalState.DEPRIVED
        else:
            return SurvivalState.CRITICAL

    def pay_daily_upkeep(self, ledger, day: int) -> dict:
        """
        Attempt to pay daily survival costs in priority order:
        Food > Water > Shelter > Healthcare.

        Returns:
            {
                "success": bool,
                "state": SurvivalState,
                "costs_paid": {category: amount},
                "shortfall": int,
            }
        """
        if self.state == SurvivalState.DECEASED:
            return {
                "success": False,
                "state": SurvivalState.DECEASED,
                "costs_paid": {},
                "shortfall": DAILY_UPKEEP,
            }

        balance = ledger.balances.get(self.name, 0)
        costs_paid: Dict[str, int] = {}
        shortfall = 0

        cost_items = [
            ("food", FOOD_COST),
            ("water", WATER_COST),
            ("shelter", SHELTER_COST),
            ("healthcare", HEALTHCARE_COST),
        ]

        for category, cost in cost_items:
            if balance >= cost:
                ok = ledger.transfer(self.name, "survival_pool", cost,
                                     memo=f"[UPKEEP:{category}] day={day}")
                if ok:
                    costs_paid[category] = cost
                    balance -= cost
                else:
                    shortfall += cost
            else:
                shortfall += cost

        # Determine survival minimum (food + water)
        paid_minimum = costs_paid.get("food", 0) + costs_paid.get("water", 0)
        cannot_survive = paid_minimum < SURVIVAL_MINIMUM

        if cannot_survive:
            self.consecutive_critical_days += 1
            if self.consecutive_critical_days >= 3:
                self.state = SurvivalState.DECEASED
            else:
                self.state = SurvivalState.CRITICAL
        else:
            self.consecutive_critical_days = 0
            self.state = self.evaluate_state(ledger.balances.get(self.name, 0))

        self.last_upkeep_day = day
        success = shortfall == 0

        return {
            "success": success,
            "state": self.state,
            "costs_paid": costs_paid,
            "shortfall": shortfall,
        }


class SurvivalEngine:
    """Orchestrates individual agent survival profiles against the token ledger."""

    def __init__(self):
        self.profiles: Dict[str, AgentSurvivalProfile] = {}

    def register_agent(self, name: str) -> AgentSurvivalProfile:
        if name not in self.profiles:
            self.profiles[name] = AgentSurvivalProfile(name=name)
        return self.profiles[name]

    def run_daily_upkeep(self, ledger, day: int) -> dict:
        """
        Run daily upkeep for all registered agents.

        Returns:
            {
                "alive": [names],
                "critical": [names],
                "deceased": [names],
                "events": [str],
            }
        """
        # Ensure survival_pool account exists
        if "survival_pool" not in ledger.balances:
            ledger.balances["survival_pool"] = 0

        alive: List[str] = []
        critical: List[str] = []
        deceased: List[str] = []
        events: List[str] = []

        for name, profile in self.profiles.items():
            if profile.state == SurvivalState.DECEASED:
                deceased.append(name)
                continue

            result = profile.pay_daily_upkeep(ledger, day)
            state = result["state"]

            if state == SurvivalState.DECEASED:
                deceased.append(name)
                events.append(
                    f"DECEASED: {name} died after 3 consecutive CRITICAL days on day {day}"
                )
            elif state == SurvivalState.CRITICAL:
                alive.append(name)
                critical.append(name)
                events.append(
                    f"CRITICAL: {name} cannot meet survival minimum "
                    f"(day {day}, consecutive={profile.consecutive_critical_days})"
                )
            else:
                alive.append(name)

        return {
            "alive": alive,
            "critical": critical,
            "deceased": deceased,
            "events": events,
        }

    def get_agent_state(self, name: str) -> SurvivalState:
        profile = self.profiles.get(name)
        if profile is None:
            raise KeyError(f"Agent '{name}' not registered in SurvivalEngine")
        return profile.state

    def save_state(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {}
        for name, p in self.profiles.items():
            data[name] = {
                "name": p.name,
                "state": p.state.value,
                "consecutive_critical_days": p.consecutive_critical_days,
                "last_upkeep_day": p.last_upkeep_day,
            }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.profiles = {}
        for name, d in data.items():
            if not isinstance(d, dict) or "name" not in d or "state" not in d:
                continue
            p = AgentSurvivalProfile(
                name=d["name"],
                state=SurvivalState(d["state"]),
                consecutive_critical_days=d.get("consecutive_critical_days", 0),
                last_upkeep_day=d.get("last_upkeep_day", -1),
            )
            self.profiles[name] = p
        return True
