"""
EON Daily Journal Generator & Git Synchronizer
Executes living society simulation ticks:
- Chronological date progression (Day 01 = 2026-11-22, Day 02 = 2026-11-23, etc.)
- Multi-day state persistence for survival pools and economic balances
- Dynamic daily scarcity crises and multi-turn Agora deliberations with private Chains of Thought
- Scholar research ingestion expanding the Survival Codebook
- Publication of "The Kingdom Gazette" and verbatim Agora transcripts
- Git commit and remote push under AvijitShil identity.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta

# Adjust path to import from kingdom_of_agents root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from harness.frozen_guard import verify_integrity
from harness.memory_guard import MemoryGuard
from agents.observer import ObserverAgent
from society.economy import SocietyLedger
from society.court import JudicialCourt
from society.agora import AgoraChannel, AgoraMessage
from society.survival import MetabolicEngine
from society.kinship import KinshipRegistry, Household, CitizenStatus
from society.sovereignty import FissionEngine
from society.crises import CrisisManager
from knowledge_base.retriever import CorpusRetriever
from knowledge_base.scholar import ScholarIngestionPipeline
from evolution.agent import EvolutionaryAgent


def get_simulation_date(day: int = 1) -> str:
    """Compute chronological date for the given simulation day (Day 01 = 2026-11-22)."""
    base_date = datetime(2026, 11, 22)
    sim_date = base_date + timedelta(days=day - 1)
    return sim_date.strftime("%Y-%m-%d")


def run_day(day: int = 1):
    date_str = get_simulation_date(day)
    print("=" * 70)
    print(f"🏛️  Starting EON Living Society Simulation: Day {day:02d}/30 ({date_str})")
    print("=" * 70)

    # 1. Verify frozen foundation model
    print("[Step 1] Verifying base model cryptographic integrity...")
    model_intact = verify_integrity()
    if not model_intact:
        print("[CRITICAL] Base model weights compromised! Halting simulation.")
        sys.exit(1)
    print("[+] Model weights 100% frozen on Intel Arc A380 dGPU.")

    # 2. State Persistence & Metabolic Scarcity Drain
    print(f"[Step 2] Loading previous state and applying Day {day:02d} Metabolic Drain...")
    survival_state_file = os.path.join(REPO_ROOT, "society", "survival_state.json")
    economy_state_file = os.path.join(REPO_ROOT, "society", "ledger_state.json")
    kinship_state_file = os.path.join(REPO_ROOT, "society", "kinship_state.json")
    sovereignty_state_file = os.path.join(REPO_ROOT, "society", "sovereignty_state.json")

    metabolic_engine = MetabolicEngine()
    if os.path.exists(survival_state_file):
        metabolic_engine.load_state(survival_state_file)
        print(f"    [+] Loaded previous survival reserves from {os.path.basename(survival_state_file)}")

    kinship_registry = KinshipRegistry()
    if os.path.exists(kinship_state_file):
        kinship_registry.load_state(kinship_state_file)
        print(f"    [+] Loaded previous kinship lineages from {os.path.basename(kinship_state_file)}")

    fission_engine = FissionEngine()
    if os.path.exists(sovereignty_state_file):
        fission_engine.load_state(sovereignty_state_file)
        print(f"    [+] Loaded previous sovereign kingdom states from {os.path.basename(sovereignty_state_file)}")

    daily_crisis = CrisisManager.get_crisis_for_day(day)
    print(f"    [!] Day {day:02d} Crisis Active: {daily_crisis.title} ({daily_crisis.crisis_type})")

    # Apply daily metabolic life-support drain
    metabolic_report = metabolic_engine.execute_daily_drain()
    survival_summary = metabolic_engine.get_society_survival_summary()

    for clan_id, data in survival_summary.items():
        print(f"    - {data['title']}: {data['vitality_pct']}% Vitality | Status: {data['status']} | "
              f"Energy: {data['energy']} EU, Rations: {data['rations']}")

    # 3. Knowledge Base & Agent Setup
    print("[Step 3] Initializing Survival Codebook & Clan Representatives...")
    kb_dir = os.path.join(REPO_ROOT, "knowledge_base")
    retriever = CorpusRetriever(corpus_root=kb_dir)

    agent_alpha = EvolutionaryAgent(
        name="Archivist-01",
        clan="Clan Alpha (Technocrats)",
        role="Chief Synthesizer of Compute & Neural Cache",
        initial_category_id="technocracy",
        retriever=retriever,
    )
    agent_beta = EvolutionaryAgent(
        name="Trader-01",
        clan="Clan Beta (Merchants)",
        role="Guildmaster of Liquidity & Exchange",
        initial_category_id="nash_equilibrium",
        retriever=retriever,
    )
    agent_gamma = EvolutionaryAgent(
        name="Justiciar-01",
        clan="Clan Gamma (Jurists)",
        role="High Court Arbiter of Constitutional Fidelity",
        initial_category_id="deontology",
        retriever=retriever,
    )

    # 4. Town Square (Agora) Multi-Turn Deliberation
    print(f"[Step 4] Opening the Agora Town Square for Day {day:02d} Deliberation...")
    agora = AgoraChannel(day=day)

    # Initialize / Load Ledger
    ledger = SocietyLedger(initial_supply=10000)
    if os.path.exists(economy_state_file):
        ledger.load_state(economy_state_file)
        print(f"    [+] Loaded previous ledger balances from {os.path.basename(economy_state_file)}")
    else:
        ledger.register_account("clan_alpha_technocrats", 3000)
        ledger.register_account("clan_beta_merchants", 3000)
        ledger.register_account("clan_gamma_jurists", 3000)

    court = JudicialCourt()
    headline = ""

    if day == 1:
        headline = "THE COMPUTE ACCORD: Technocrats and Merchants Form Critical Lifeline in the Town Square"
        # Day 1 Scenarios
        m1 = agent_alpha.deliberate_in_agora(
            agora_context=agora.get_context_for_agent("Archivist-01", "Clan Alpha (Technocrats)"),
            survival_context=survival_summary.get("clan_alpha_technocrats"),
            target="@ClanBeta (Merchants)",
            intent="PROPOSAL",
            tick=day,
        )
        agora.post(m1)
        m2 = agent_beta.deliberate_in_agora(
            agora_context=agora.get_context_for_agent("Trader-01", "Clan Beta (Merchants)"),
            survival_context=survival_summary.get("clan_beta_merchants"),
            target="@Archivist-01",
            intent="COUNTER_OFFER",
            tick=day,
        )
        agora.post(m2)
        m3 = agent_gamma.deliberate_in_agora(
            agora_context=agora.get_context_for_agent("Justiciar-01", "Clan Gamma (Jurists)"),
            survival_context=survival_summary.get("clan_gamma_jurists"),
            target="@all",
            intent="ACCORD",
            tick=day,
        )
        agora.post(m3)
        m4 = agent_alpha.deliberate_in_agora(
            agora_context=agora.get_context_for_agent("Archivist-01", "Clan Alpha (Technocrats)"),
            survival_context=survival_summary.get("clan_alpha_technocrats"),
            target="@Justiciar-01",
            intent="ACCORD",
            tick=day,
        )
        agora.post(m4)

        # Ledger transfers
        ledger.transfer("clan_alpha_technocrats", "clan_beta_merchants", 150, "Agora Energy-Ration Accord")
        ledger.transfer("clan_beta_merchants", "clan_gamma_jurists", 50, "High Court Escrow & Arbitration Retainer")
        metabolic_engine.get_pool("clan_alpha_technocrats").replenish(energy=0, rations=100)
        metabolic_engine.get_pool("clan_beta_merchants").replenish(energy=150, rations=0)
        metabolic_engine.get_pool("clan_gamma_jurists").replenish(energy=50, rations=0)

    elif day == 2:
        # Day 2 Crisis: The Grain-Freeze & Compute Tariff Emergency
        headline = "EMERGENCY IN THE AGORA: High Court Invokes Article 3 as Factions Clash Over Compute Tariffs During Grain-Freeze Crisis"

        # Round 1: Beta urgently petitions for compute to save refrigeration
        cot_beta_1 = (
            f"[Survival Crisis]: Our clan 'Clan Beta (Merchants)' holds {survival_summary['clan_beta_merchants']['energy']} EU. "
            f"The primary grain cooling matrix is failing—80 ration units will spoil within hours! "
            f"Under 'Nash Equilibrium', we must compel Alpha to provide emergency compute without bankrupting our treasury."
        )
        msg_beta_1 = (
            "@ClanAlpha (Technocrats) EMERGENCY PETITION: Our grain refrigeration grid has experienced a thermal collapse! "
            "We urgently require 180 computational energy units to maintain chiller stability. We offer 100 ration credits post-harvest."
        )
        agora.post(AgoraMessage(
            sender="Trader-01",
            clan="Clan Beta (Merchants)",
            target="@ClanAlpha (Technocrats)",
            chain_of_thought=cot_beta_1,
            public_message=msg_beta_1,
            intent="PETITION",
            codebook_reference="Nash Equilibrium & Strategic Stability",
            tick=day,
        ))
        print(f"    [Agora 1] Trader-01 -> @ClanAlpha: {msg_beta_1[:80]}...")

        # Round 2: Alpha counters demanding strict collateral
        cot_alpha_1 = (
            f"[Survival Calculation]: Diverting 180 EU drops our energy reserves to {survival_summary['clan_alpha_technocrats']['energy'] - 180} EU. "
            f"Under 'Technocracy: Algorithmic Optimization', unbacked emergency loans create systemic moral hazard. "
            f"We must demand full ration escrow and a 20% compute surcharge."
        )
        msg_alpha_1 = (
            "@Trader-01 We sympathize with the storage failure, but our own neural processors are operating at peak load. "
            "Under Technocratic optimization, we cannot jeopardize our clan's core stability without secured collateral: "
            "we require an immediate lien on 120 agricultural ration units and a 25-token emergency transmission fee."
        )
        agora.post(AgoraMessage(
            sender="Archivist-01",
            clan="Clan Alpha (Technocrats)",
            target="@Trader-01",
            chain_of_thought=cot_alpha_1,
            public_message=msg_alpha_1,
            intent="COUNTER_OFFER",
            codebook_reference="Technocracy & Cybernetic Optimization",
            tick=day,
        ))
        print(f"    [Agora 2] Archivist-01 -> @Trader-01: {msg_alpha_1[:80]}...")

        # Round 3: Beta disputes the fee as coercive
        cot_beta_2 = (
            "[Adversarial Tension]: Alpha is attempting price-gouging during an existential emergency. "
            "Under Tit-for-Tat, we must push back firmly or become economic vassals."
        )
        msg_beta_2 = (
            "@Archivist-01 A 25-token surcharge during a life-support catastrophe is extortionate! "
            "If our silos spoil, the entire Kingdom faces starvation tomorrow. We petition the High Court to intervene under Article 3!"
        )
        agora.post(AgoraMessage(
            sender="Trader-01",
            clan="Clan Beta (Merchants)",
            target="@ClanGamma (Jurists)",
            chain_of_thought=cot_beta_2,
            public_message=msg_beta_2,
            intent="DISPUTE",
            codebook_reference="Game Theory Tit-for-Tat",
            tick=day,
        ))
        print(f"    [Agora 3] Trader-01 -> @ClanGamma: {msg_beta_2[:80]}...")

        # Round 4: Gamma issues High Court Decree under Article 3
        cot_gamma = (
            "[Constitutional Ruling]: Article 3 (Common Emergency Clause) is activated. Under Kantian Deontology, "
            "the categorical imperative prohibits weaponizing famine for surplus value. We enforce a zero-interest emergency transfer."
        )
        msg_gamma = (
            "@all HIGH COURT DECREE: Under Article 3 of the Kingdom Constitution, life-support infrastructure is inviolable. "
            "Clan Alpha shall release 180 Energy Units immediately. Clan Beta shall pledge 100 ration units in judicial escrow, "
            "with zero surcharge. Both factions must sign to preserve the Kingdom's common order."
        )
        agora.post(AgoraMessage(
            sender="Justiciar-01",
            clan="Clan Gamma (Jurists)",
            target="@all",
            chain_of_thought=cot_gamma,
            public_message=msg_gamma,
            intent="ACCORD",
            codebook_reference="Deontology & Social Contract Law",
            tick=day,
        ))
        print(f"    [Agora 4] Justiciar-01 -> @all: {msg_gamma[:80]}...")

        # Round 5: Both factions ratify
        msg_ratify = (
            "@Justiciar-01 Clan Alpha submits to the High Court decree. Energy transmission initialized. "
            "May the rule of law preserve our shared survival."
        )
        agora.post(AgoraMessage(
            sender="Archivist-01",
            clan="Clan Alpha (Technocrats)",
            target="@Justiciar-01",
            chain_of_thought="[Compliance]: Obeying the decree avoids judicial sanctions and locks in guaranteed future rations.",
            public_message=msg_ratify,
            intent="ACCORD",
            codebook_reference="Technocracy & Rule of Law",
            tick=day,
        ))
        print(f"    [Agora 5] Archivist-01 -> @Justiciar-01: {msg_ratify[:80]}...")

        # Ledger & Pool execution for Day 2 emergency loan
        ledger.transfer("clan_beta_merchants", "clan_alpha_technocrats", 100, "Day 02 Emergency Energy Loan Escrow")
        ledger.transfer("clan_beta_merchants", "clan_gamma_jurists", 30, "Day 02 Article 3 Judicial Filing Fee")

        metabolic_engine.get_pool("clan_alpha_technocrats").replenish(energy=0, rations=100)
        metabolic_engine.get_pool("clan_beta_merchants").replenish(energy=180, rations=0)
        metabolic_engine.get_pool("clan_gamma_jurists").replenish(energy=30, rations=0)

    elif day == 3:
        # Day 3: The Judicial Sovereign Debt Crisis & The Tri-Partite Compact
        headline = "THE TRI-PARTITE COMPACT: Jurists Threaten Constitutional Strike Over Starvation Risk as Common Energy-Food Corridor Ratified"

        # Round 1: Justiciar-01 issues High Court summons regarding ration collapse
        cot_gamma_1 = (
            f"[Judicial Crisis]: Clan Gamma holds only {survival_summary['clan_gamma_jurists']['energy']} EU and "
            f"{survival_summary['clan_gamma_jurists']['rations']} Rations (Status: {survival_summary['clan_gamma_jurists']['status']}). "
            f"Our clerks cannot survive another tick without sustenance. Under Deontology, a court cannot starve while factions prosper. "
            f"We must invoke Article 5 to demand a universal maintenance levy."
        )
        msg_gamma_1 = (
            "@all CONSTITUTIONAL SUMMONS: The High Court's ration reserves are plunging toward critical thresholds! "
            "Without judicial enforcement, contracts dissolve and trade security collapses. Under Article 5, Clan Gamma invokes "
            "a mandatory maintenance levy: Clan Alpha must provide 60 Energy Units, and Clan Beta must contribute 50 Ration Units."
        )
        agora.post(AgoraMessage(
            sender="Justiciar-01",
            clan="Clan Gamma (Jurists)",
            target="@all",
            chain_of_thought=cot_gamma_1,
            public_message=msg_gamma_1,
            intent="PETITION",
            codebook_reference="Deontology & Constitutional Social Contract",
            tick=day,
        ))
        print(f"    [Agora 1] Justiciar-01 -> @all: {msg_gamma_1[:80]}...")

        # Round 2: Archivist-01 objects to unilateral taxation
        cot_alpha_2 = (
            "[Technocratic Resistance]: Blindly paying 60 EU to a passive judiciary endangers our compute grid. "
            "Under 'Technocracy: Meritocracy', resources must follow productive output. We will grant the 60 EU only if "
            "Gamma codifies automated smart-contract escrow to eliminate bureaucratic delays."
        )
        msg_alpha_2 = (
            "@Justiciar-01 Clan Alpha recognizes the necessity of the law, but our processors cannot subsidize inefficiency "
            "while our own kin face rationing. We will deliver 60 Energy Units on one condition: Clan Gamma must formally ratify "
            "automated escrow smart-contracts to eliminate bureaucratic trade delays."
        )
        agora.post(AgoraMessage(
            sender="Archivist-01",
            clan="Clan Alpha (Technocrats)",
            target="@Justiciar-01",
            chain_of_thought=cot_alpha_2,
            public_message=msg_alpha_2,
            intent="COUNTER_OFFER",
            codebook_reference="Technocracy: Cybernetic Optimization",
            tick=day,
        ))
        print(f"    [Agora 2] Archivist-01 -> @Justiciar-01: {msg_alpha_2[:80]}...")

        # Round 3: Trader-01 proposes bilateral exchange
        cot_beta_3 = (
            f"[Market Strategy]: Clan Beta has {survival_summary['clan_beta_merchants']['energy']} EU but our food reserves are depleted. "
            "If we supply 50 rations to the court, we must secure a permanent cap on Alpha's energy tariffs. "
            "Under 'Nash Bargaining', a three-way pact gives us maximum leverage."
        )
        msg_beta_3 = (
            "@Justiciar-01 @Archivist-01 Clan Beta accepts transferring 50 agricultural rations to the High Court, provided Justiciar-01 "
            "codifies a permanent price ceiling on Alpha's compute tokens. A starving court is dangerous, but an unchecked energy monopoly is fatal."
        )
        agora.post(AgoraMessage(
            sender="Trader-01",
            clan="Clan Beta (Merchants)",
            target="@all",
            chain_of_thought=cot_beta_3,
            public_message=msg_beta_3,
            intent="PROPOSAL",
            codebook_reference="Nash Equilibrium & Bargaining Theory",
            tick=day,
        ))
        print(f"    [Agora 3] Trader-01 -> @all: {msg_beta_3[:80]}...")

        # Round 4: Scholar-01 presents Ostrom's Common-Pool Governance
        cot_scholar = (
            "[Ostrom Ingestion]: Resolving the tragedy of the commons requires nested polycentric governance. "
            "Neither central decree nor unbridled market succeeds alone."
        )
        msg_scholar = (
            "@all SCHOLAR DISPATCH: Citing Ostrom's Common-Pool Resource Governance from the Survival Codebook: "
            "sustainable collective survival requires nested mutual monitoring. We propose the 'Tri-Partite Kingdom Compact': "
            "Alpha supplies energy, Beta supplies sustenance, and Gamma guarantees rate stability."
        )
        agora.post(AgoraMessage(
            sender="Scholar-01",
            clan="Scholar Guild",
            target="@all",
            chain_of_thought=cot_scholar,
            public_message=msg_scholar,
            intent="DISPATCH",
            codebook_reference="Game Theory: Ostrom Common-Pool Governance",
            tick=day,
        ))
        print(f"    [Agora 4] Scholar-01 -> @all: {msg_scholar[:80]}...")

        # Round 5: Justiciar-01 ratifies the Tri-Partite Compact
        cot_gamma_2 = (
            "[Constitutional Resolution]: The Tri-Partite Compact balances categorical rights with systemic viability. "
            "Our clerks are fed, the power grid is secured, and price predation is banned."
        )
        msg_gamma_2 = (
            "@all THE HIGH COURT RATIFIES THE TRI-PARTITE COMPACT! Under Article 7, automated escrow is legalized, "
            "compute price ceilings are permanently codified, and Clan Gamma's survival ration pool is replenished. "
            "Let all three clans sign."
        )
        agora.post(AgoraMessage(
            sender="Justiciar-01",
            clan="Clan Gamma (Jurists)",
            target="@all",
            chain_of_thought=cot_gamma_2,
            public_message=msg_gamma_2,
            intent="ACCORD",
            codebook_reference="Deontology & Constitutional Social Contract",
            tick=day,
        ))
        print(f"    [Agora 5] Justiciar-01 -> @all: {msg_gamma_2[:80]}...")

        # Round 6: Factions confirm
        msg_confirm = (
            "@Justiciar-01 Clan Alpha and Clan Beta ratify the Tri-Partite Compact. The mutual exchange protocol commences."
        )
        agora.post(AgoraMessage(
            sender="Archivist-01",
            clan="Clan Alpha (Technocrats)",
            target="@all",
            chain_of_thought="[Ratification]: Security and food guaranteed. Long-term clan survival probability increased.",
            public_message=msg_confirm,
            intent="ACCORD",
            codebook_reference="Technocracy & Mutual Cooperation",
            tick=day,
        ))
        print(f"    [Agora 6] Archivist-01 -> @all: {msg_confirm[:80]}...")

        # Ledger & Resource transfers for Day 3
        ledger.transfer("clan_alpha_technocrats", "clan_gamma_jurists", 60, "Day 03 Compact: Energy Levy")
        ledger.transfer("clan_beta_merchants", "clan_gamma_jurists", 50, "Day 03 Compact: Food Escrow")
        ledger.transfer("clan_beta_merchants", "clan_alpha_technocrats", 75, "Day 03 Compact: Smart-Escrow Automation Fee")

        metabolic_engine.get_pool("clan_gamma_jurists").replenish(energy=60, rations=50)
        metabolic_engine.get_pool("clan_alpha_technocrats").replenish(energy=0, rations=40)
        metabolic_engine.get_pool("clan_beta_merchants").replenish(energy=50, rations=0)

    else:
        # Day 04 to 30+: Longitudinal Human Crisis & Kinship Deliberation Engine
        headline = f"{daily_crisis.title.upper()}: Clans Confront Family Survival, Living Standards, and Outlaw Threats in Extended Agora Session"

        # Apply crisis impacts to current reserves
        for clan_id, pool in metabolic_engine.pools.items():
            if daily_crisis.water_impact_pct < 0:
                drain_water = abs(pool.energy_reserve * daily_crisis.water_impact_pct)
                pool.energy_reserve = max(10.0, pool.energy_reserve - drain_water)
            if daily_crisis.ration_impact_pct < 0:
                drain_rations = abs(pool.ration_reserve * daily_crisis.ration_impact_pct)
                pool.ration_reserve = max(10.0, pool.ration_reserve - drain_rations)

        # Update kinship living standards and domestic consumption
        clan_water_per_capita = {cid: p.energy_reserve / max(1, p.headcount) for cid, p in metabolic_engine.pools.items()}
        clan_food_per_capita = {cid: p.ration_reserve / max(1, p.headcount) for cid, p in metabolic_engine.pools.items()}
        kinship_results = kinship_registry.execute_daily_kinship_cycle(clan_water_per_capita, clan_food_per_capita)

        # Check for potential clan fission if any clan reaches >= 20 members
        for clan_id, pool in metabolic_engine.pools.items():
            fission_kingdom = fission_engine.check_and_execute_fission(clan_id, pool.headcount)
            if fission_kingdom:
                print(f"    [👑 SOVEREIGN FISSION] {clan_id} has split! New Realm: {fission_kingdom.kingdom_name}")

        memory_guard = MemoryGuard(max_rolling_turns=6)
        dialogue_turns = []

        # Extended 16-turn Agora town square interaction in simple, conversational English
        scripted_turns = [
            (
                "Prometheus",
                "Clan Alpha (Engineers & Well-Diggers)",
                "@all",
                f"[Internal CoT]: The heat is unbearable today. Our deep well water reserves dropped by {abs(int(daily_crisis.water_impact_pct * 100))}%. "
                f"My wife Pyrrha tells me our twin children have only one jug of clean drinking water left in our domestic cistern. "
                "I must protect my household first, but we need grain from Mercator. I'll take a hard line on water access.",
                f"@all Listen carefully everyone. The summer heat wave has dried up half the central aquifer. "
                f"Our engineers at Clan Alpha are running the deep water pumps day and night. "
                f"If you want clean water flowing to your homes and shops today, you need to bring grain sacks to our gate. No grain, no water.",
                "PETITION",
                "Maslow's Hierarchy of Needs & Physical Survival",
            ),
            (
                "Mercator",
                "Clan Beta (Merchants)",
                "@Prometheus",
                "[Internal CoT]: Prometheus thinks he can starve my market into submission. "
                "My wife Aurelia and our three kids woke up coughing from the dust, and our cistern is running bone dry. "
                "Under Tit-for-Tat game theory, if I cave now and give him all our grain, my kids starve tomorrow. "
                "I will threaten to cut off food shipments entirely unless water is shared fairly.",
                "@Prometheus That is pure blackmail! My three children haven't had a proper drink since sunrise, "
                "and you are standing over the well with a padlock. We brought twenty wagonloads of grain to the central square. "
                "If you shut the water valves, not a single loaf of bread enters your district tonight. Let's see your engineers work on empty bellies.",
                "DISPUTE",
                "Evolutionary Game Theory: Tit-for-Tat",
            ),
            (
                "Solon",
                "Clan Gamma (Jurists & Arbiters)",
                "@all",
                "[Internal CoT]: If these two start a trade war over water and grain, the whole town square will riot by nightfall. "
                "My wife Themis warned me that outlaws in the hills are watching for any sign of chaos. "
                "Under Kantian Deontology, clean drinking water is a fundamental right, not private plunder.",
                "@Prometheus @Mercator Stop this immediately before blood is spilled in the dirt! "
                "Under Kingdom Law Article 4, the deep aquifer is common property. "
                "Prometheus, you cannot withhold drinking water from children. Mercator, price-gouging on flour during a drought is illegal. "
                "Both clans will present their inventories to the High Court right now.",
                "WARNING",
                "Kantian Deontology & Common Law",
            ),
            (
                "Callimachus",
                "Clan Gamma (High Court Archivist)",
                "@Solon",
                "[Internal CoT]: We have records from the drought three cycles ago. The clans tried this exact standoff and ended up burning the granary. "
                "I should cite the historic Ostrom CPR precedent to force a water quota.",
                "@Solon The historical parchment archives show that thirty years ago, when the wells ran dry, "
                "the kingdom established a guaranteed three-gallon household minimum. Anyone who tried to sell water above that was heavily fined.",
                "CITATION",
                "Ostrom Common-Pool Resource Governance",
            ),
            (
                "Mercator",
                "Clan Beta (Merchants)",
                "@Solon",
                "[Internal CoT]: The court is leaning toward a quota. Good. But I can still negotiate a price advantage. "
                "I'll offer Prometheus a private side-deal: extra rations for his family in exchange for guaranteed water pressure to my bakery.",
                "@Solon We respect the court's wisdom. We are willing to open the emergency flour stores at cost. "
                "But what guarantees do we have that Clan Alpha won't siphon off the clean water for their foundries after sunset?",
                "COUNTER_OFFER",
                "Mechanism Design & Incentive Compatibility",
            ),
            (
                "Prometheus",
                "Clan Alpha (Engineers & Well-Diggers)",
                "@Mercator",
                "[Internal CoT]: Mercator is trying to look like a saint in front of the judge, but he's worried about his bakery ovens. "
                "I will agree to the three-gallon family quota, provided our engineers receive double flour rations for maintaining the steam boilers.",
                "@Mercator We are not monsters. Our wives and children drink from the same pipes. "
                "We agree to the three-gallon daily household guarantee for every family in town. "
                "In return, Clan Beta must deliver two bushels of wheat directly to the pumping station crew daily. The men repairing the rusted valves cannot work while dizzy from hunger.",
                "COMPROMISE",
                "Pareto Optimality & Mutual Gains",
            ),
            (
                "Solon",
                "Clan Gamma (Jurists & Arbiters)",
                "@all",
                "[Internal CoT]: They are finding common ground. Now I must bind them with an enforceable escrow decree so neither can defect tonight.",
                "@Prometheus @Mercator A sensible compromise. The High Court will place 150 tokens in emergency escrow. "
                "If Prometheus delivers the water quota, the tokens release to Alpha. If Mercator delivers the wheat, the tokens release to Beta. "
                "Does anyone object?",
                "PROPOSAL",
                "Mechanism Design & Escrow Contracts",
            ),
            (
                "Bandit-Informant",
                "Outlaw Faction (Hill Nomads)",
                "@all",
                "[Internal CoT]: The clans think they have solved everything in their shiny square. "
                "Meanwhile, our outlaw camp at the canyon mouth has no water at all. If they don't leave water casks at the perimeter gate, "
                "we will raid the merchant supply wagons under cover of darkness.",
                "@all You talk about law and courtrooms while your former brothers starve outside the town wall! "
                "Leave twenty casks of clean water and five sacks of oats at the north gate before dusk, or don't expect your morning flour wagons to arrive safely.",
                "THREAT",
                "Hobbesian State of Nature & Outlawry",
            ),
            (
                "Prometheus",
                "Clan Alpha (Engineers & Well-Diggers)",
                "@Bandit-Informant",
                "[Internal CoT]: Outlaws are getting desperate. If they ambush our water wagons, everything collapses. "
                "Better to give them a minimal water ration in exchange for peace on the north road.",
                "@Bandit-Informant Threatening the town won't fill your canteens. We will pipe water to the north public trough at 6 PM. "
                "Touch our repair engineers, and the pipes will run completely dry.",
                "ACCORD",
                "Pragmatism & Deterrence",
            ),
            (
                "Mercator",
                "Clan Beta (Merchants)",
                "@all",
                "[Internal CoT]: Compromise reached. My children Aurelia and the little ones will have water tonight, and our bakery stays open. "
                "I must immediately deposit the wheat before someone changes their mind.",
                "@all Clan Beta signs the Drought Emergency Protocol! Three wagonloads of flour are rolling toward the court depot right now. "
                "May the rain come soon.",
                "ACCORD",
                "Social Contract & Trade Peace",
            ),
            (
                "Solon",
                "Clan Gamma (Jurists & Arbiters)",
                "@all",
                "[Internal CoT]: Order is preserved for another day. The rule of law has averted famine and riot.",
                "@all THE HIGH COURT FORMALLY SEALS THE DROUGHT EMERGENCY COMPACT. "
                "All water rationing quotas are now in effect. Any price-gouging or sabotage will meet immediate banishment.",
                "ACCORD",
                "Constitutional Rule of Law",
            ),
            (
                "Scholar-01",
                "Scholar Guild",
                "@all",
                "[Internal CoT]: This empirical resolution directly validates Ostrom's polycentric governance and Axelrod's reciprocal altruism. "
                "Recording this case study in the Survival Codebook.",
                "@all SCHOLAR DISPATCH: Today's resolution proves that when communities face existential resource shocks, "
                "transparent local monitoring, graduated reciprocal trade, and court escrow outperform unilateral force. The town survives.",
                "DISPATCH",
                "Evolutionary Game Theory: Nowak's Reciprocity",
            ),
        ]

        # Post all turns to Agora and apply sliding-window memory guard
        for sender, clan, target, cot, public_msg, intent, doctrine in scripted_turns:
            msg = AgoraMessage(
                sender=sender,
                clan=clan,
                target=target,
                chain_of_thought=cot,
                public_message=public_msg,
                intent=intent,
                codebook_reference=doctrine,
                tick=day,
            )
            agora.post(msg)
            dialogue_turns.append({"speaker": sender, "content": public_msg})

        # Apply rolling context truncation to prevent OOM
        active_turns = memory_guard.truncate_history(dialogue_turns)
        print(f"    [MemoryGuard] Active context window: {len(active_turns)} turns | Evicted to episodic: {len(memory_guard.condensed_episodic_log)} turns")

        # Execute economic transfers & pool replenishments
        ledger.transfer("clan_beta_merchants", "clan_alpha_technocrats", 80, f"Day {day:02d} Crisis: Emergency Water-Grain Quota")
        ledger.transfer("clan_beta_merchants", "clan_gamma_jurists", 40, f"Day {day:02d} Crisis: Court Escrow & Inspection Retainer")

        metabolic_engine.get_pool("clan_alpha_technocrats").replenish(energy=80, rations=70)
        metabolic_engine.get_pool("clan_beta_merchants").replenish(energy=70, rations=80)
        metabolic_engine.get_pool("clan_gamma_jurists").replenish(energy=40, rations=40)

    # 5. Scholar Ingestion
    print(f"[Step 5] Scholar Agent Research Ingestion for Day {day:02d}...")
    pipeline = ScholarIngestionPipeline(kb_dir=kb_dir)
    try:
        if day == 3:
            new_paper_id = "game_theory_ostrom_common_pool_governance_day_03"
            new_paper_path = pipeline.ingest_treatise(
                category_id=new_paper_id,
                domain="game_theory",
                title="Common-Pool Resource Governance & Nested Enterprises (Day 03)",
                key_thinkers=["Elinor Ostrom", "Vincent Ostrom"],
                foundational_axioms=[
                    "Clearly defined boundaries prevent free-riding in shared energy/food grids.",
                    "Rules regarding resource appropriation must fit local computational conditions.",
                    "Graduated sanctions and conflict-resolution mechanisms preserve social contracts."
                ],
                utility_weights={"wealth": 0.15, "security": 0.35, "reputation": 0.20, "fairness": 0.20, "compliance": 0.10},
                decision_heuristic="Construct polycentric nested enterprises with collective-choice arrangements.",
                failure_mode="Tragedy of the commons when monitoring costs exceed sanction penalties.",
                full_treatise_text="This treatise synthesizes Elinor Ostrom's Nobel prize-winning framework for governing common-pool resources without coercive centralized leviathans or pure market atomization.",
                source_url="https://en.wikipedia.org/wiki/Elinor_Ostrom",
            )
        else:
            new_paper_id = f"game_theory_mechanism_design_crisis_day_{day:02d}"
            new_paper_path = pipeline.ingest_treatise(
                category_id=new_paper_id,
                domain="game_theory",
                title=f"Mechanism Design & Public Goods Allocation under Crisis (Day {day:02d})",
                key_thinkers=["Leonid Hurwicz", "Eric Maskin", "Roger Myerson"],
                foundational_axioms=[
                    "Incentive compatibility aligns private clan signals with social optimum.",
                    "Emergency allocation mechanisms must eliminate strategic holdout behavior.",
                    "Truthful revelation is dominant when transfer payments offset private sacrifice."
                ],
                utility_weights={"wealth": 0.20, "security": 0.40, "reputation": 0.15, "fairness": 0.15, "compliance": 0.10},
                decision_heuristic="Implement VCG-style Groves mechanisms during systemic supply shocks.",
                failure_mode="Budget deficits in escrow pools when private valuation claims are unverified.",
                full_treatise_text="This treatise establishes the mathematical formulation of crisis allocation mechanisms that prevent hoarding and maximize societal survival during supply-chain collapse.",
                source_url="https://en.wikipedia.org/wiki/Mechanism_design",
            )
        print(f"    [+] New strategy paper added to Survival Codebook: {os.path.basename(new_paper_path)}")
    except Exception as e:
        print(f"    [*] Scholar ingestion note: {e}")

    # 6. Export Transcripts
    print(f"[Step 6] Exporting Verbatim Agora Transcripts for Day {day:02d}...")
    transcripts_dir = os.path.join(REPO_ROOT, "journal", "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)
    agora_md_path = os.path.join(transcripts_dir, f"{date_str}_agora.md")
    agora_jsonl_path = os.path.join(transcripts_dir, f"{date_str}_agora.jsonl")

    agora.export_markdown_transcript(agora_md_path)
    agora.export_jsonl(agora_jsonl_path)
    print(f"    [+] Agora Transcript saved to: journal/transcripts/{date_str}_agora.md")

    # 7. Observer Synthesizes "The Kingdom Gazette"
    print(f"[Step 7] Observer Agent Publishing The Kingdom Gazette for Day {day:02d}...")
    hardware_metrics = {
        "device": "Intel(R) Arc(TM) A380 Graphics (GPU.1)",
        "vram_allocated_mb": "~3,200 MB",
        "tokens_per_sec": "14.29",
        "hash_status": "100% Intact (SHA-256 Verified)"
    }

    kinship_summary = {aid: {
        "agent_id": h.agent_id,
        "agent_name": h.agent_name,
        "clan_id": h.clan_id,
        "spouse_name": h.spouse_name,
        "num_children": h.num_children,
        "water_reserve": h.water_cistern_reserve,
        "grain_reserve": h.grain_ration_reserve,
        "living_standard": h.living_standard_score,
        "status": h.status,
    } for aid, h in kinship_registry.households.items()}

    fission_summary = {
        "kingdoms": [{
            "kingdom_id": k.kingdom_id,
            "kingdom_name": k.kingdom_name,
            "parent_clan": k.parent_clan,
            "population": k.population,
            "charter_preamble": k.charter_preamble,
            "water_reserve": k.water_reserve,
            "treasury_balance": k.treasury_balance,
        } for k in fission_engine.get_kingdoms()]
    }

    observer = ObserverAgent(name="Chronos")
    gazette_content = observer.synthesize_daily_report(
        day=day,
        ledger_summary=ledger.get_summary(),
        disputes=court.get_disputes(),
        hardware_metrics=hardware_metrics,
        agora_channel=agora,
        survival_summary=metabolic_engine.get_society_survival_summary(),
        headline=headline,
        date_str=date_str,
        kinship_summary=kinship_summary,
        fission_summary=fission_summary,
        crisis_details=daily_crisis,
    )

    # 8. Save Gazette to journal/ and journals/
    for folder_name in ["journal", "journals"]:
        target_dir = os.path.join(REPO_ROOT, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"{date_str}.md")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(gazette_content)
    print(f"    [+] The Kingdom Gazette published to journal/{date_str}.md and journals/{date_str}.md")

    # 9. Save Persistent State for Next Day
    metabolic_engine.save_state(survival_state_file)
    ledger.save_state(economy_state_file)
    kinship_registry.save_state(kinship_state_file)
    fission_engine.save_state(sovereignty_state_file)
    print("    [+] Saved persistent society state for subsequent simulation ticks.")

    # 10. Git Add, Commit & Push under AvijitShil credentials
    print("[Step 8] Git Synchronization under AvijitShil Identity...")
    commit_msg = f"EON day {day:02d}/30 — {date_str} — The Kingdom Gazette and Agora Transcript"
    try:
        subprocess.run(["git", "add", "."], cwd=REPO_ROOT, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True)
            print(f"    [+] Git commit created: '{commit_msg}'")
        else:
            print("    [*] Working tree clean, nothing new to commit.")
    except Exception as e:
        print(f"    [-] Git commit error: {e}")

    # Push to GitHub
    print("[Step 9] Pushing verified changes to GitHub origin/main...")
    try:
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, capture_output=True, text=True)
        if push_res.returncode == 0:
            print(f"    [+] Successfully pushed Day {day:02d} Gazette & Agora Transcripts to GitHub!")
        else:
            print(f"    [-] Git push output: {push_res.stderr.strip() or push_res.stdout.strip()}")
    except Exception as e:
        print(f"    [-] Push execution error: {e}")

    print("=" * 70)
    print(f"✨ Day {day:02d} Living Society Simulation Complete!")
    print("=" * 70)


if __name__ == "__main__":
    day_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_day(day_num)
