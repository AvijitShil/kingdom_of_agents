"""
society/simulation_engine.py
EON 2.0 Autonomous Civilizational Simulation Engine.
Executes multi-interval daily cycles with Chronos Observatory logging every 6 hours:
  - Interval 1: 00:00 - 06:00 (Dawn Edition) — Metabolic Upkeep, Morning Market Opening
  - Interval 2: 06:00 - 12:00 (Midday Edition) — Agora Forum, Credit, Trade & Banking
  - Interval 3: 12:00 - 18:00 (Dusk Edition) — Kingdom Assemblies, Armies & Alliances
  - Interval 4: 18:00 - 24:00 (Midnight Edition) — Cultural Lineages, Reproduction & Night Plots
Saves reports to `daily gazette/` and `daily_gazette/` organized by date.
"""

from __future__ import annotations

import os
import sys
import json
import random
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from society.economy import SocietyLedger
from society.survival import SurvivalEngine, SurvivalState, DAILY_UPKEEP
from society.kinship import GreekNamingRegistry, ReproductionController, ParentalEducation
from society.sovereignty import KingdomFormationEngine, SocioEconomicFissionTrigger
from society.institutions import (
    InstitutionRegistry, InstitutionType, ArmyInstitution, default_registry as inst_registry
)
from evolution.cultural_traits import (
    CulturalTraitRegistry, TransmissionType, default_registry as trait_registry
)
from observer.chronos import Chronos, EventType
from observer.gazette import GazetteRenderer
from harness.memory_guard import MemoryGuard


GREEK_FOUNDING_CITIZENS = [
    "Athena", "Hermes", "Prometheus", "Themis", "Orion", "Dione",
    "Solon", "Thalia", "Lysander", "Phaedra", "Nikias", "Calliope"
]

INTERVAL_METADATA = [
    {
        "code": "06_00_dawn",
        "name": "Dawn Edition (00:00 - 06:00)",
        "theme": "Metabolic Upkeep, Cistern Inspections & Dawn Trade Opening",
        "time_str": "06:00 AM",
    },
    {
        "code": "12_00_midday",
        "name": "Midday Edition (06:00 - 12:00)",
        "theme": "Agora Commercial Fair, Credit Auctions & Banking Operations",
        "time_str": "12:00 PM",
    },
    {
        "code": "18_00_dusk",
        "name": "Dusk Edition (12:00 - 18:00)",
        "theme": "Kingdom Assemblies, Defense Treaties & Military Recruitment",
        "time_str": "06:00 PM",
    },
    {
        "code": "24_00_midnight",
        "name": "Midnight Edition (18:00 - 24:00)",
        "theme": "Cultural Traditions, Intergenerational Education & Night Conspiracies",
        "time_str": "12:00 AM",
    },
]


class CivilizationalSimulator:
    """Orchestrates autonomous agents and logs 6-hour interval gazette editions."""

    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.journal_root = os.path.join(repo_root, "journal")
        self.chronos = Chronos(journal_root=self.journal_root)
        self.gazette_renderer = GazetteRenderer(self.chronos)

        # Core registries
        self.ledger = SocietyLedger()
        self.survival = SurvivalEngine()
        self.naming = GreekNamingRegistry()
        self.reproduction = ReproductionController()
        self.education = ParentalEducation()
        self.kingdom_engine = KingdomFormationEngine()
        self.fission_trigger = SocioEconomicFissionTrigger()
        self.institution_registry = inst_registry
        self.trait_registry = trait_registry

        # State file paths
        self.society_dir = os.path.join(repo_root, "society")
        self.ledger_file = os.path.join(self.society_dir, "ledger_state.json")
        self.survival_file = os.path.join(self.society_dir, "individual_survival_state.json")
        self.sovereignty_file = os.path.join(self.society_dir, "sovereignty_state.json")
        self.institutions_file = os.path.join(self.society_dir, "institutions_state.json")
        self.traits_file = os.path.join(self.journal_root, "economy", "cultural_traits.json")

        self._load_or_bootstrap_state()

    def _load_or_bootstrap_state(self):
        """Load persistent states or bootstrap founding civilization if clean."""
        if os.path.isfile(self.ledger_file):
            self.ledger.load_state(self.ledger_file)
            # Ensure Greek founding agents are present; if legacy state loaded, bootstrap
            if any(name not in self.ledger.balances for name in GREEK_FOUNDING_CITIZENS):
                self.ledger.register_founding_civilization()
        else:
            self.ledger.register_founding_civilization()

        if os.path.isfile(self.survival_file):
            self.survival.load_state(self.survival_file)
        else:
            for name in GREEK_FOUNDING_CITIZENS:
                self.survival.register_agent(name)

        if os.path.isfile(self.sovereignty_file):
            self.kingdom_engine.load_state(self.sovereignty_file)

        if os.path.isfile(self.institutions_file):
            self.institution_registry.load_state(self.institutions_file)

        if os.path.isfile(self.traits_file):
            self.trait_registry.load_state(self.traits_file)

        # Ensure all founding agents are registered in survival
        for name in GREEK_FOUNDING_CITIZENS:
            if name not in self.survival.profiles:
                self.survival.register_agent(name)

    def save_state(self):
        """Persist all simulation states."""
        self.ledger.save_state(self.ledger_file)
        self.survival.save_state(self.survival_file)
        self.kingdom_engine.save_state(self.sovereignty_file)
        self.institution_registry.save_state(self.institutions_file)
        self.trait_registry.save_state(self.traits_file)

    def get_living_agents(self) -> List[str]:
        return [
            name for name, p in self.survival.profiles.items()
            if p.state != SurvivalState.DECEASED
        ]

    def run_interval(
        self,
        sim_day: int,
        sim_date: str,
        interval_idx: int,
    ) -> Dict[str, Any]:
        """Execute one 6-hour interval of civilizational life."""
        meta = INTERVAL_METADATA[interval_idx]
        interval_code = meta["code"]
        interval_name = meta["name"]
        time_str = meta["time_str"]

        living = self.get_living_agents()
        interval_events = []
        agora_speeches = []

        # ------------------------------------------------------------------
        # Interval 1 (Dawn): Upkeep, Cisterns, and Emergency Relief
        # ------------------------------------------------------------------
        if interval_idx == 0:
            self.reproduction.reset_daily_counter()
            upkeep_res = self.survival.run_daily_upkeep(self.ledger, day=sim_day)

            for agent in living:
                p = self.survival.profiles[agent]
                bal = self.ledger.balances.get(agent, 0)
                if p.state == SurvivalState.CRITICAL:
                    speech = f"My water cistern is dry and I hold only {bal} tokens! I need an emergency grant."
                    intent = "secure immediate survival liquidity"
                    action = "petitioned Agora for drought relief"
                    outcome = "Emergency petition placed on public docket"
                    self.chronos.log_event(
                        EventType.SURVIVAL_STATE_CHANGE, sim_day, sim_date,
                        [agent], speech, intent, action, outcome,
                        {"time": time_str, "balance": bal}
                    )
                    agora_speeches.append(f"**{agent}** ({time_str}): \"{speech}\"")
                elif p.state == SurvivalState.WARNING:
                    speech = f"Rations are thinning ({bal} tokens remaining). I will offer my labor at the dawn market."
                    agora_speeches.append(f"**{agent}** ({time_str}): \"{speech}\"")

            interval_events.append(
                f"Metabolic cycle complete: {len(upkeep_res.get('alive', []))} surviving, "
                f"{len(upkeep_res.get('critical', []))} in critical need, "
                f"{len(upkeep_res.get('deceased', []))} perished."
            )

        # ------------------------------------------------------------------
        # Interval 2 (Midday): Commercial Fair, Banking, Trade, Loans
        # ------------------------------------------------------------------
        elif interval_idx == 1:
            # Pairwise autonomous trade
            random.shuffle(living)
            for i in range(0, len(living) - 1, 2):
                buyer, seller = living[i], living[i+1]
                buyer_bal = self.ledger.balances.get(buyer, 0)
                if buyer_bal >= 20:
                    trade_amt = random.randint(5, 18)
                    ok = self.ledger.transfer(
                        buyer, seller, trade_amt,
                        memo=f"Midday Fair: {buyer} purchased grain/water rights from {seller}"
                    )
                    if ok:
                        speech = f"I purchase your surplus grain ration for {trade_amt} tokens."
                        intent = "replenish domestic pantry"
                        action = f"transferred {trade_amt} tokens {buyer} -> {seller}"
                        outcome = f"Trade finalized in Agora. {buyer} has {self.ledger.balances[buyer]}t, {seller} has {self.ledger.balances[seller]}t."
                        self.chronos.log_event(
                            EventType.TRANSACTION, sim_day, sim_date,
                            [buyer, seller], speech, intent, action, outcome,
                            {"time": time_str, "amount": trade_amt}
                        )
                        agora_speeches.append(f"**{buyer}** ({time_str}): \"{speech}\" (paid {trade_amt}t to {seller})")
                        interval_events.append(outcome)

            # Solon or Athena acts as lender if peer in need
            for agent in living:
                if self.ledger.balances.get(agent, 0) < 15:
                    for wealthy in ["Solon", "Athena", "Hermes"]:
                        if wealthy in living and self.ledger.balances.get(wealthy, 0) > 100:
                            loan_id = self.ledger.issue_loan(
                                wealthy, agent, amount=25, interest_rate=0.05,
                                memo=f"Emergency survival credit from {wealthy}"
                            )
                            if loan_id:
                                speech = f"I extend 25 tokens of credit to {agent} at 5% interest to prevent insolvency."
                                intent = "protect societal cohesion while earning yield"
                                action = f"issued loan {loan_id[:8]} to {agent}"
                                outcome = f"{agent} received 25 tokens emergency credit from {wealthy}"
                                self.chronos.log_event(
                                    EventType.TRANSACTION, sim_day, sim_date,
                                    [wealthy, agent], speech, intent, action, outcome,
                                    {"time": time_str, "loan_id": loan_id}
                                )
                                agora_speeches.append(f"**{wealthy}** ({time_str}): \"{speech}\"")
                                interval_events.append(outcome)
                            break

        # ------------------------------------------------------------------
        # Interval 3 (Dusk): Sovereignty, Armies, Treaties & Disputes
        # ------------------------------------------------------------------
        elif interval_idx == 2:
            # Check for kingdom formation or army recruitment
            active_kingdoms = self.kingdom_engine.list_kingdoms()
            if not active_kingdoms and sim_day >= 3:
                # Solon or Lysander declares kingdom
                ruler = "Lysander" if "Lysander" in living else living[0]
                founders = [ruler, "Orion", "Dione"]
                kid = self.kingdom_engine.declare_kingdom(
                    name="Peloponnesian League",
                    ruler=ruler,
                    founding_members=[f for f in founders if f in living],
                    treasury_account=ruler,
                    day=sim_day,
                )
                speech = f"By virtue of our shared water security, we declare the Peloponnesian League under sovereign charter!"
                intent = "consolidate defensive power against nomad raids"
                action = f"declared sovereign kingdom {kid}"
                outcome = f"Kingdom of {ruler}'s realm chartered with {len(founders)} citizens."
                self.chronos.log_event(
                    EventType.KINGDOM_FORMATION, sim_day, sim_date,
                    founders, speech, intent, action, outcome,
                    {"time": time_str, "kingdom_id": kid}
                )
                agora_speeches.append(f"**{ruler}** ({time_str}): \"{speech}\"")
                interval_events.append(outcome)

            # Army recruitment
            armies = self.institution_registry.list_by_type(InstitutionType.Army) if hasattr(self.institution_registry, "list_by_type") else []
            if not armies and "Lysander" in living and self.ledger.balances.get("Lysander", 0) >= 30:
                army = self.institution_registry.create_army(
                    name="Hoplite Phalanx",
                    owner="Lysander",
                    treasury_account="Lysander",
                    treasury_balance=float(self.ledger.balances["Lysander"] // 2),
                    founded_day=sim_day,
                )
                for candidate in ["Orion", "Nikias"]:
                    if candidate in living:
                        army.recruit(candidate)
                speech = "The Hoplite Phalanx stands to defend the granaries from bandit plunder."
                intent = "deter outlaw incursions"
                action = "commissioned standing army and recruited hoplites"
                outcome = f"Hoplite Phalanx founded with soldiers: {', '.join(army.soldiers)}"
                self.chronos.log_event(
                    EventType.INSTITUTION_CREATION, sim_day, sim_date,
                    ["Lysander"] + army.soldiers, speech, intent, action, outcome,
                    {"time": time_str, "institution_id": army.institution_id}
                )
                agora_speeches.append(f"**Lysander** ({time_str}): \"{speech}\"")
                interval_events.append(outcome)

        # ------------------------------------------------------------------
        # Interval 4 (Midnight): Lineage, Reproduction, Cultural Traits
        # ------------------------------------------------------------------
        elif interval_idx == 3:
            # Check reproduction eligibility
            couples = [("Prometheus", "Dione"), ("Hermes", "Phaedra"), ("Solon", "Calliope")]
            for p1, p2 in couples:
                if p1 in living and p2 in living:
                    b1 = self.ledger.balances.get(p1, 0)
                    b2 = self.ledger.balances.get(p2, 0)
                    if self.reproduction.can_reproduce(b1, b2):
                        child_name = self.naming.generate_child_name(p1, p2)
                        self.reproduction.register_birth(child_name, p1, p2, sim_day)
                        self.survival.register_agent(child_name)
                        # Gift tokens from parents
                        gift = 30
                        self.ledger.balances[child_name] = gift * 2
                        self.ledger.balances[p1] -= gift
                        self.ledger.balances[p2] -= gift

                        # Parental education
                        traits_res = self.education.transfer_knowledge(
                            parent=p1, child=child_name,
                            parent_cultural_traits=["Ostrom_Common_Pool", "Pragmatic_Barter"],
                            day=sim_day
                        )
                        speech = f"We welcome our child {child_name} into the lineage of {p1} and {p2}!"
                        intent = "perpetuate lineage and transmit survival wisdom"
                        action = f"birth of {child_name} registered; inherited traits: {', '.join(traits_res['inherited_traits'])}"
                        outcome = f"{child_name} born with 60 tokens starter endowment."
                        self.chronos.log_event(
                            EventType.BIRTH, sim_day, sim_date,
                            [p1, p2, child_name], speech, intent, action, outcome,
                            {"time": time_str, "child": child_name}
                        )
                        self.chronos.log_generation(
                            child=child_name, parent1=p1, parent2=p2,
                            inherited_traits=traits_res["inherited_traits"],
                            day=sim_day, sim_date=sim_date
                        )
                        agora_speeches.append(f"**{p1} & {p2}** ({time_str}): \"{speech}\"")
                        interval_events.append(outcome)
                        break  # 1 birth per midnight tick

            # Cultural trait emergence
            if sim_day % 2 == 0 and len(self.trait_registry.get_active_traits()) < 10:
                innovator = random.choice(living)
                new_trait = self.trait_registry.register_new_trait(
                    name=f"Cistern Desilting Guild (Day {sim_day})",
                    category="social_institution",
                    creator=innovator,
                    day=sim_day,
                    description="Cooperative labor sharing for cleaning civic water channels.",
                    transmission_type=TransmissionType.SUCCESS,
                    economic_effects={"upkeep_reduction": 0.10},
                )
                speech = f"I introduce the {new_trait.name}. Collective maintenance reduces our daily water burn."
                intent = "lower metabolic expenses through organized cooperation"
                action = f"registered new cultural trait {new_trait.trait_id}"
                outcome = f"New cultural tradition established by {innovator}."
                self.chronos.log_event(
                    EventType.CULTURAL_TRAIT_EMERGENCE, sim_day, sim_date,
                    [innovator], speech, intent, action, outcome,
                    {"time": time_str, "trait_id": new_trait.trait_id}
                )
                agora_speeches.append(f"**{innovator}** ({time_str}): \"{speech}\"")
                interval_events.append(outcome)

        # Update running profiles for active participants
        for agent in living:
            self.chronos.update_agent_profile(
                name=agent,
                birth_day=1,
                day=sim_day,
                survival_state=self.survival.profiles[agent].state.value,
            )

        # Render interval bulletin
        bulletin_text = self._render_interval_bulletin(
            sim_day=sim_day,
            sim_date=sim_date,
            meta=meta,
            events=interval_events,
            speeches=agora_speeches,
            living_count=len(self.get_living_agents()),
        )

        return {
            "interval_idx": interval_idx,
            "interval_meta": meta,
            "bulletin_text": bulletin_text,
            "events": interval_events,
            "speeches": agora_speeches,
        }

    def _render_interval_bulletin(
        self,
        sim_day: int,
        sim_date: str,
        meta: dict,
        events: List[str],
        speeches: List[str],
        living_count: int,
    ) -> str:
        """Format an individual 6-hour interval bulletin."""
        lines = [
            f"# THE EON CIVILIZATION GAZETTE — 6-HOUR DISPATCH",
            f"### {meta['name']} | Time: {meta['time_str']} | Date: {sim_date} (Day {sim_day})",
            f"*Observatory Dispatch Filed by Chronos*",
            "",
            f"**Cycle Focus**: {meta['theme']}",
            f"**Active Living Population**: {living_count} citizens",
            f"**Conserved Supply Invariant**: {sum(self.ledger.balances.values())} tokens (Gini: {self.ledger.get_wealth_gini():.3f})",
            "",
            "---",
            "",
            "## ⚡ CHRONICLED EVENTS IN THIS 6-HOUR WINDOW",
        ]
        if events:
            for ev in events:
                lines.append(f"- {ev}")
        else:
            lines.append("- Routine civil tranquility observed across markets and quarters.")

        lines += [
            "",
            "## 🏛️ VOICES OF THE AGORA & CITIZEN DELIBERATIONS",
        ]
        if speeches:
            for sp in speeches:
                lines.append(f"- {sp}")
        else:
            lines.append("- The Agora square remained peaceful during this cycle.")

        lines += [
            "",
            "---",
            f"*Next Observatory Dispatch in 6 hours.*",
        ]
        return "\n".join(lines)

    def run_full_day_cycle(self, sim_day: int, sim_date: str) -> Dict[str, Any]:
        """
        Execute all four 6-hour intervals for the day, save interval dispatches,
        render the consolidated Daily Gazette, and save to `daily gazette/` and `daily_gazette/`.
        """
        interval_results = []
        all_day_speeches = []

        print(f"\n{'='*70}")
        print(f"🏛️  Executing EON 2.0 Full 4-Interval Day Cycle: Day {sim_day:02d} ({sim_date})")
        print(f"{'='*70}")

        # Run 4 intervals (every 6 hours)
        for idx in range(4):
            meta = INTERVAL_METADATA[idx]
            print(f"  [Interval {idx+1}/4] Running {meta['name']} ({meta['time_str']})...")
            res = self.run_interval(sim_day, sim_date, idx)
            interval_results.append(res)
            all_day_speeches.extend(res["speeches"])

        # Create target directories
        dir_names = ["daily gazette", "daily_gazette"]
        for dname in dir_names:
            date_dir = os.path.join(self.repo_root, dname, sim_date)
            os.makedirs(date_dir, exist_ok=True)

            # Write each interval bulletin
            for res in interval_results:
                code = res["interval_meta"]["code"]
                file_path = os.path.join(date_dir, f"{code}.md")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(res["bulletin_text"])

        # Render consolidated Daily Gazette
        living = self.get_living_agents()
        deceased = [name for name, p in self.survival.profiles.items() if p.state == SurvivalState.DECEASED]
        critical = [name for name, p in self.survival.profiles.items() if p.state == SurvivalState.CRITICAL]

        survival_summary = {
            "alive": living,
            "critical": critical,
            "deceased": deceased,
        }

        consolidated_gazette = self.gazette_renderer.render_daily_gazette(
            sim_day=sim_day,
            sim_date=sim_date,
            ledger_summary=self.ledger.get_summary(),
            survival_summary=survival_summary,
            agora_highlights=all_day_speeches[:12],
        )

        # Write consolidated daily gazette to both folders
        for dname in dir_names:
            # 1. Inside date subfolder as gazette_full.md
            full_path = os.path.join(self.repo_root, dname, sim_date, "gazette_full.md")
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(consolidated_gazette)

            # 2. At date root as YYYY-MM-DD.md
            date_root_path = os.path.join(self.repo_root, dname, f"{sim_date}.md")
            with open(date_root_path, "w", encoding="utf-8") as f:
                f.write(consolidated_gazette)

        # Also write to journal/daily/ and journal/ for backward compatibility
        daily_archive = os.path.join(self.journal_root, "daily", f"{sim_date}.md")
        with open(daily_archive, "w", encoding="utf-8") as f:
            f.write(consolidated_gazette)

        journal_compat = os.path.join(self.journal_root, f"{sim_date}.md")
        with open(journal_compat, "w", encoding="utf-8") as f:
            f.write(consolidated_gazette)

        # Flush Chronos daily transcripts
        self.chronos.flush_day(sim_day, sim_date)

        # Save all simulation states
        self.save_state()

        print(f"  [+] Saved 4 interval bulletins to daily gazette/{sim_date}/")
        print(f"  [+] Saved consolidated Daily Gazette to daily gazette/{sim_date}.md")
        print(f"  [+] Mirrored to daily_gazette/ and journal/daily/")

        return {
            "day": sim_day,
            "date": sim_date,
            "intervals": interval_results,
            "consolidated_gazette": consolidated_gazette,
        }
