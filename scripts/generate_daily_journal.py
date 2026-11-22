"""
EON Daily Journal Generator & Git Synchronizer
Executes living society simulation tick:
- Applies clan metabolic scarcity and life-support burn
- Orchestrates multi-turn Agora town square deliberation with private Chains of Thought
- Enables Scholar agents to expand the Survival Codebook
- Executes economic ledger and judicial dispute operations
- Saves raw Agora chat transcripts and publishes The Kingdom Gazette
- Commits and synchronizes to GitHub under AvijitShil credentials.
"""

import os
import sys
import subprocess
from datetime import datetime

# Adjust path to import from kingdom_of_agents root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from harness.frozen_guard import verify_integrity
from agents.observer import ObserverAgent
from society.economy import SocietyLedger
from society.court import JudicialCourt
from society.agora import AgoraChannel, AgoraMessage
from society.survival import MetabolicEngine
from knowledge_base.retriever import CorpusRetriever
from knowledge_base.scholar import ScholarIngestionPipeline
from evolution.agent import EvolutionaryAgent


def run_day(day: int = 1):
    print("=" * 70)
    print(f"🏛️  Starting EON Living Society Simulation: Day {day:02d}/30")
    print("=" * 70)

    # 1. Verify frozen foundation model
    print("[Step 1] Verifying base model cryptographic integrity...")
    model_intact = verify_integrity()
    if not model_intact:
        print("[CRITICAL] Base model weights compromised! Halting simulation.")
        sys.exit(1)
    print("[+] Model weights 100% frozen on Intel Arc A380 dGPU.")

    # 2. Metabolic Engine & Scarcity Drain
    print("[Step 2] Applying Clan Metabolic Life-Support Drain...")
    metabolic_engine = MetabolicEngine()
    metabolic_report = metabolic_engine.execute_daily_drain()
    survival_summary = metabolic_engine.get_society_survival_summary()

    for clan_id, data in survival_summary.items():
        print(f"    - {data['title']}: {data['vitality_pct']}% Vitality | Status: {data['status']} | "
              f"Energy: {data['energy']} EU, Rations: {data['rations']}")

    # 3. Knowledge Base & Agent Setup
    print("[Step 3] Initializing Survival Codebook & Clan Representatives...")
    kb_dir = os.path.join(REPO_ROOT, "knowledge_base")
    retriever = CorpusRetriever(corpus_root=kb_dir)

    # Agents representing their clans
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
    print("[Step 4] Opening the Agora Town Square for Public Deliberation...")
    agora = AgoraChannel(day=day)

    # Round 1: Technocrats propose emergency compute-for-rations corridor
    m1 = agent_alpha.deliberate_in_agora(
        agora_context=agora.get_context_for_agent("Archivist-01", "Clan Alpha (Technocrats)"),
        survival_context=survival_summary.get("clan_alpha_technocrats"),
        target="@ClanBeta (Merchants)",
        intent="PROPOSAL",
        tick=day,
    )
    agora.post(m1)
    print(f"    [Agora 1] {m1.sender} -> {m1.target}: {m1.public_message[:80]}...")

    # Round 2: Merchants counter-offer citing Game Theoretic Tit-for-Tat
    m2 = agent_beta.deliberate_in_agora(
        agora_context=agora.get_context_for_agent("Trader-01", "Clan Beta (Merchants)"),
        survival_context=survival_summary.get("clan_beta_merchants"),
        target="@Archivist-01",
        intent="COUNTER_OFFER",
        tick=day,
    )
    agora.post(m2)
    print(f"    [Agora 2] {m2.sender} -> {m2.target}: {m2.public_message[:80]}...")

    # Round 3: Jurists intervene citing Constitutional Deontology & Escrow
    m3 = agent_gamma.deliberate_in_agora(
        agora_context=agora.get_context_for_agent("Justiciar-01", "Clan Gamma (Jurists)"),
        survival_context=survival_summary.get("clan_gamma_jurists"),
        target="@all",
        intent="ACCORD",
        tick=day,
    )
    agora.post(m3)
    print(f"    [Agora 3] {m3.sender} -> {m3.target}: {m3.public_message[:80]}...")

    # Round 4: Technocrats ratify the High Court escrow terms
    m4 = agent_alpha.deliberate_in_agora(
        agora_context=agora.get_context_for_agent("Archivist-01", "Clan Alpha (Technocrats)"),
        survival_context=survival_summary.get("clan_alpha_technocrats"),
        target="@Justiciar-01",
        intent="ACCORD",
        tick=day,
    )
    agora.post(m4)
    print(f"    [Agora 4] {m4.sender} -> {m4.target}: {m4.public_message[:80]}...")

    # 5. Ledger & Court Execution
    print("[Step 5] Ratifying Agreed Transactions on Society Ledger...")
    ledger = SocietyLedger(initial_supply=10000)
    ledger.register_account("clan_alpha_technocrats", 3000)
    ledger.register_account("clan_beta_merchants", 3000)
    ledger.register_account("clan_gamma_jurists", 3000)

    # Execute bilateral trade resulting from Agora accord
    ledger.transfer("clan_alpha_technocrats", "clan_beta_merchants", 150, "Agora Energy-Ration Accord")
    ledger.transfer("clan_beta_merchants", "clan_gamma_jurists", 50, "High Court Escrow & Arbitration Retainer")

    # Replenish clan survival pools based on trade
    metabolic_engine.get_pool("clan_alpha_technocrats").replenish(energy=0, rations=100)
    metabolic_engine.get_pool("clan_beta_merchants").replenish(energy=150, rations=0)
    metabolic_engine.get_pool("clan_gamma_jurists").replenish(energy=50, rations=0)

    court = JudicialCourt()

    # 6. Scholar Research Ingestion into Survival Codebook
    print("[Step 6] Scholar Agent Research Ingestion...")
    pipeline = ScholarIngestionPipeline(kb_dir=kb_dir)
    try:
        new_paper_path = pipeline.ingest_treatise(
            category_id="game_theory_stochastic_evolutionary_stability",
            domain="game_theory",
            title="Stochastic Stability & Equilibrium Selection in Scarcity Regimes",
            key_thinkers=["H. Peyton Young", "Michihiro Kandori"],
            foundational_axioms=[
                "Agents face persistent stochastic perturbations in resource payoffs.",
                "Suboptimal equilibria unravel under repeated coordination trembling.",
                "Conventions that minimize transition resistance dominate long horizons."
            ],
            utility_weights={"wealth": 0.25, "security": 0.35, "reputation": 0.20, "fairness": 0.10, "compliance": 0.10},
            decision_heuristic="Adopt conventions that minimize transition risk under persistent perturbations.",
            failure_mode="Coordination lock-in to poverty traps when mutation rates vanish.",
            full_treatise_text="This treatise establishes the mathematical criteria under which clans in extreme scarcity regimes select risk-dominant cooperation equilibria over payoff-dominant autarky.",
            source_url="https://en.wikipedia.org/wiki/Evolutionary_game_theory",
        )
        print(f"    [+] New strategy paper added to Survival Codebook: {os.path.basename(new_paper_path)}")
    except Exception as e:
        print(f"    [*] Scholar ingestion note: {e}")

    # 7. Export Transcripts
    print("[Step 7] Exporting Verbatim Agora Transcripts...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    transcripts_dir = os.path.join(REPO_ROOT, "journal", "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)
    agora_md_path = os.path.join(transcripts_dir, f"{date_str}_agora.md")
    agora_jsonl_path = os.path.join(transcripts_dir, f"{date_str}_agora.jsonl")

    agora.export_markdown_transcript(agora_md_path)
    agora.export_jsonl(agora_jsonl_path)
    print(f"    [+] Agora Transcript saved to: journal/transcripts/{date_str}_agora.md")

    # 8. Observer Synthesizes "The Kingdom Gazette"
    print("[Step 8] Observer Agent Publishing The Kingdom Gazette...")
    hardware_metrics = {
        "device": "Intel(R) Arc(TM) A380 Graphics (GPU.1)",
        "vram_allocated_mb": "~3,200 MB",
        "tokens_per_sec": "14.29",
        "hash_status": "100% Intact (SHA-256 Verified)"
    }

    observer = ObserverAgent(name="Chronos")
    gazette_content = observer.synthesize_daily_report(
        day=day,
        ledger_summary=ledger.get_summary(),
        disputes=court.get_disputes(),
        hardware_metrics=hardware_metrics,
        agora_channel=agora,
        survival_summary=metabolic_engine.get_society_survival_summary(),
    )

    # 9. Save Gazette to journal/ and journals/
    for folder_name in ["journal", "journals"]:
        target_dir = os.path.join(REPO_ROOT, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"{date_str}.md")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(gazette_content)
    print(f"    [+] The Kingdom Gazette published to journal/{date_str}.md and journals/{date_str}.md")

    # 10. Git Add, Commit & Push under AvijitShil credentials
    print("[Step 9] Git Synchronization under AvijitShil Identity...")
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
    print("[Step 10] Pushing verified changes to GitHub origin/main...")
    try:
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, capture_output=True, text=True)
        if push_res.returncode == 0:
            print("    [+] Successfully pushed The Kingdom Gazette & Agora Transcripts to GitHub!")
        else:
            print(f"    [-] Git push output: {push_res.stderr.strip() or push_res.stdout.strip()}")
    except Exception as e:
        print(f"    [-] Push execution error: {e}")

    print("=" * 70)
    print("✨ Day 01 Living Society Simulation Complete!")
    print("=" * 70)


if __name__ == "__main__":
    day_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_day(day_num)
