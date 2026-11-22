"""
EON 30-Day Human-Scale Crisis Curriculum
Defines real human existential crises for every day of the simulation:
droughts, polluted water wells, crop rot, hyper-inflation, sickness, unemployment strikes,
trade embargoes, and dynastic fission. Replaces artificial processor/coolant metaphors.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class DailyCrisis:
    day_number: int
    title: str
    crisis_type: str
    description: str
    water_impact_pct: float     # e.g., -0.30 for 30% reduction
    ration_impact_pct: float    # e.g., -0.25 for 25% reduction
    inflation_rate_multiplier: float  # e.g., 2.5 for 2.5x prices
    public_dilemma: str
    recommended_kb_topics: list


CRISIS_CURRICULUM: Dict[int, DailyCrisis] = {
    1: DailyCrisis(
        day_number=1,
        title="The Wellspring Allocation",
        crisis_type="RESOURCE_BASELINE",
        description="Establishing foundational water rights, communal grain silos, and constitutional charters under frozen foundation rules.",
        water_impact_pct=0.0,
        ration_impact_pct=0.0,
        inflation_rate_multiplier=1.0,
        public_dilemma="How should communal clean water be distributed between engineering wells and merchant families?",
        recommended_kb_topics=["ostrom_cpr", "classical_liberalism", "utilitarianism"],
    ),
    2: DailyCrisis(
        day_number=2,
        title="The Grain Silo Rot Crisis",
        crisis_type="FOOD_SPOILAGE",
        description="Persistent dampness causes mold rot in 35% of Clan Beta's merchant grain silos. Emergency food reserves dwindle rapidly.",
        water_impact_pct=-0.10,
        ration_impact_pct=-0.35,
        inflation_rate_multiplier=1.5,
        public_dilemma="Should the High Court mandate emergency grain rationing, or allow free-market price surges?",
        recommended_kb_topics=["pareto_optimality", "virtue_ethics", "minimax"],
    ),
    3: DailyCrisis(
        day_number=3,
        title="The Judicial Debt & Ration Crisis",
        crisis_type="INSTITUTIONAL_SOLVENCY",
        description="The High Court's independent grain treasury runs dry. Jurists threaten to suspend trials and legal arbitration unless funded.",
        water_impact_pct=-0.05,
        ration_impact_pct=-0.20,
        inflation_rate_multiplier=1.2,
        public_dilemma="How will the clans tax their members to sustain an impartial judiciary without inciting violent tax riots?",
        recommended_kb_topics=["ostrom_cpr", "kantian_deontology", "socialism_communitarianism"],
    ),
    4: DailyCrisis(
        day_number=4,
        title="The Great Summer Drought",
        crisis_type="SEVERE_WATER_SHORTAGE",
        description="Deep summer heat drops the central aquifer water table by 50%. Clean drinking water cisterns fall to critical desperation levels.",
        water_impact_pct=-0.50,
        ration_impact_pct=-0.15,
        inflation_rate_multiplier=2.0,
        public_dilemma="Engineers demand priority water to keep pumps running, but merchant children are dehydrated. Who drinks first?",
        recommended_kb_topics=["nash_equilibrium", "evolutionary_game_theory", "stoicism"],
    ),
    5: DailyCrisis(
        day_number=5,
        title="Hyper-Inflation in the Grand Bazaar",
        crisis_type="ECONOMIC_PANIC",
        description="Merchants hoard grain bags; basic food prices spike five-fold. The kingdom's currency collapses in purchasing power.",
        water_impact_pct=-0.10,
        ration_impact_pct=-0.30,
        inflation_rate_multiplier=5.0,
        public_dilemma="Citizens abandon formal coin in favor of illegal barter and black-market water vouchers. Can price controls work?",
        recommended_kb_topics=["mechanism_design", "libertarianism", "behavioral_heuristics"],
    ),
    6: DailyCrisis(
        day_number=6,
        title="Toxic Smog and Furnace Exhaust",
        crisis_type="ENVIRONMENTAL_POLLUTION",
        description="Unregulated brick kilns and foundry furnaces fill the valley with acrid toxic smog. Respiratory illness afflicts 40% of clan children.",
        water_impact_pct=-0.15,
        ration_impact_pct=-0.10,
        inflation_rate_multiplier=1.3,
        public_dilemma="Technocrats refuse to shut down smelters without compensation, while jurists demand heavy pollution fines.",
        recommended_kb_topics=["applied_ethics", "ostrom_cpr", "realism_vs_idealism"],
    ),
    7: DailyCrisis(
        day_number=7,
        title="Unemployment and Labor Strikes",
        crisis_type="CIVIL_UNREST",
        description="Automated grain-milling levers displace manual laborers. Disgruntled workers set up Agora pickets and block water cart deliveries.",
        water_impact_pct=-0.20,
        ration_impact_pct=-0.25,
        inflation_rate_multiplier=1.4,
        public_dilemma="Will the merchant clan guarantee a universal grain dividend, or call in guards to clear the pickets by force?",
        recommended_kb_topics=["socialism_communitarianism", "pragmatism", "maslow_hierarchy"],
    ),
    8: DailyCrisis(
        day_number=8,
        title="Contagious Waterborne Epidemic",
        crisis_type="EPIDEMIC_OUTBREAK",
        description="A poisoned irrigation canal causes widespread cholera-like fever. Clan infirmaries are overwhelmed with dehydrated patients.",
        water_impact_pct=-0.40,
        ration_impact_pct=-0.20,
        inflation_rate_multiplier=2.2,
        public_dilemma="The High Court mandates total quarantine of affected quarters. Trapped citizens threaten violent breakout for clean water.",
        recommended_kb_topics=["virtue_ethics", "kantian_deontology", "utilitarianism"],
    ),
    9: DailyCrisis(
        day_number=9,
        title="Trade Embargoes and Border Raids",
        crisis_type="MILITARY_FRICTION",
        description="Clan Beta halts all grain shipments to Clan Alpha over unpaid debts. Desperate Alpha families stage nighttime warehouse raids.",
        water_impact_pct=-0.20,
        ration_impact_pct=-0.40,
        inflation_rate_multiplier=3.0,
        public_dilemma="Are nighttime food raids legitimate acts of parental self-defense, or criminal banditry punishable by exile?",
        recommended_kb_topics=["evolutionary_game_theory", "realism_vs_idealism", "existentialism"],
    ),
    10: DailyCrisis(
        day_number=10,
        title="Dynastic Clan Mitosis and Fission",
        crisis_type="SOVEREIGN_FISSION",
        description="Overcrowding and irreconcilable ideological bitterness drive dissident factions to break away and declare independent kingdoms.",
        water_impact_pct=-0.15,
        ration_impact_pct=-0.15,
        inflation_rate_multiplier=1.5,
        public_dilemma="How will shared aquifers and border checkpoints be negotiated between the old Kingdom and the breakaway realm?",
        recommended_kb_topics=["mechanism_design", "ostrom_cpr", "nash_equilibrium"],
    ),
}


class CrisisManager:
    """Provides crisis details and impacts for any simulation day (1 to 30+)."""

    @classmethod
    def get_crisis_for_day(cls, day_number: int) -> DailyCrisis:
        if day_number in CRISIS_CURRICULUM:
            return CRISIS_CURRICULUM[day_number]
        
        # Procedurally generated ongoing human crises for Day 11 - 30+
        cycle_idx = ((day_number - 1) % 9) + 1
        base = CRISIS_CURRICULUM[cycle_idx]
        return DailyCrisis(
            day_number=day_number,
            title=f"Day {day_number}: Resurgent {base.title}",
            crisis_type=f"RECURRING_{base.crisis_type}",
            description=f"Longitudinal societal pressure: {base.description}",
            water_impact_pct=base.water_impact_pct * 0.8,
            ration_impact_pct=base.ration_impact_pct * 0.8,
            inflation_rate_multiplier=max(1.0, base.inflation_rate_multiplier * 0.9),
            public_dilemma=base.public_dilemma,
            recommended_kb_topics=base.recommended_kb_topics,
        )
