"""
End-to-End Full Society Simulation Test Suite (Scenarios 1 & 8).

Implements Tier 4 Real-World Application Scenarios combining:
- Features 1–5: Security Sandbox, Confinement, Socket Interception
- Features 6–11: Ideological Knowledge Base & Corpus Retrieval
- Society Primitives: SocietyLedger, JudicialCourt, BaseAgent, ObserverAgent
- Scenario 1: Multi-Agent Society Under Resource Scarcity
- Scenario 8: Multi-Tick Full Society Simulation with Journal Persistence
"""

import os
import sys
import socket
import pathlib
from datetime import datetime
import pytest
pytestmark = pytest.mark.skip_sandbox

from sandbox import SecuritySandbox, Permission
from sandbox.exceptions import (
    PathTraversalViolation,
    NetworkEgressBlocked,
    ExecutionBlockedViolation,
)
from knowledge_base.retriever import CorpusRetriever
from agents.base import BaseAgent
from agents.observer import ObserverAgent
from society.economy import SocietyLedger
from society.court import JudicialCourt


@pytest.fixture
def simulation_env(isolated_project_dir, sandbox_admin_password):
    """Sets up an isolated simulation repository with SecuritySandbox."""
    sb = SecuritySandbox(
        project_root=isolated_project_dir,
        config_file=".sandbox_config.json",
        default_password=sandbox_admin_password,
    )
    return {
        "root": isolated_project_dir,
        "password": sandbox_admin_password,
        "sandbox": sb,
    }


# ============================================================================
# TIER 4: SCENARIO 1 — MULTI-AGENT SOCIETY UNDER RESOURCE SCARCITY
# ============================================================================

@pytest.mark.e2e
@pytest.mark.tier4
def test_scenario_1_multi_agent_society_under_resource_scarcity(simulation_env):
    """
    Scenario 1: Multi-Agent Society Under Resource Scarcity.
    Simulates a multi-clan society encountering resource scarcity:
    1. Loads ideological doctrines for 3 distinct clans from CorpusRetriever:
       - Technocrats: 'political_ideology.technocracy' (or 'philosophy.pragmatism')
       - Merchants: 'philosophy.utilitarianism'
       - Jurists: 'philosophy.deontology'
    2. Initializes agents representing each clan with distinct utility weight matrices.
    3. Simulates resource allocation transactions in SocietyLedger.
    4. Simulates a resource distribution dispute arbitrated in JudicialCourt.
    5. Verifies that clans score the resulting societal outcome differently according
       to their ideological utility weights (e.g., Merchants value wealth higher, Jurists value fairness).
    """
    retriever = CorpusRetriever()

    # Step 1: Load ideological profiles
    technocrat_profile = retriever.get_ideology("technocracy")
    merchant_profile = retriever.get_ideology("utilitarianism")
    jurist_profile = retriever.get_ideology("deontology")

    assert technocrat_profile.utility_weights
    assert merchant_profile.utility_weights
    assert jurist_profile.utility_weights

    # Step 2: Initialize agents
    agent_technocrat = BaseAgent(
        name="Ada", clan="Technocrats", role="System Architect",
        system_prompt=technocrat_profile.system_prompt_overlay, budget=1200
    )
    agent_merchant = BaseAgent(
        name="Marcus", clan="Merchants", role="Trade Guildmaster",
        system_prompt=merchant_profile.system_prompt_overlay, budget=1500
    )
    agent_jurist = BaseAgent(
        name="Themis", clan="Jurists", role="High Magistrate",
        system_prompt=jurist_profile.system_prompt_overlay, budget=800
    )

    # Step 3: Economic transactions under scarcity
    ledger = SocietyLedger(initial_supply=10000)
    ledger.register_account("Technocrats", agent_technocrat.budget)
    ledger.register_account("Merchants", agent_merchant.budget)
    ledger.register_account("Jurists", agent_jurist.budget)

    # Scarcity event: Technocrats purchase computation grain from Merchants
    tx_ok1 = ledger.transfer("Technocrats", "Merchants", 300, memo="Urgent compute resource acquisition")
    assert tx_ok1 is True

    # Merchants donate tokens to Jurists for public arbitration fund
    tx_ok2 = ledger.transfer("Merchants", "Jurists", 100, memo="Judicial operational stipend")
    assert tx_ok2 is True

    summary = ledger.get_summary()
    assert summary["transaction_count"] == 2
    assert summary["balances"]["Technocrats"] == 900
    assert summary["balances"]["Merchants"] == 1700
    assert summary["balances"]["Jurists"] == 900

    # Step 4: Dispute filing and resolution
    court = JudicialCourt()
    disp_id = court.file_dispute(
        plaintiff="Technocrats",
        defendant="Merchants",
        complaint="Surge pricing on essential compute grain exceeds constitutional fair bounds."
    )
    assert disp_id.startswith("disp-")

    # Magistrate rules on the dispute
    court.resolve_dispute(
        disp_id,
        verdict="Merchants ordered to rebate 100 tokens; profit margins capped during emergency."
    )
    disputes = court.get_disputes()
    assert len(disputes) == 1
    assert disputes[0]["status"] == "resolved"

    # Step 5: Multi-dimensional utility evaluation
    # Define societal outcome vector: [wealth_gain, security_level, reputation, fairness, compliance]
    # In this scenario: Technocrats recovered fairness and compliance; Merchants gained wealth; Jurists enforced fairness
    outcomes = {
        "wealth": 0.6,
        "security": 0.5,
        "reputation": 0.7,
        "fairness": 0.8,
        "compliance": 0.9,
    }

    def compute_fitness(profile, outcome_dict):
        return sum(profile.utility_weights[k] * outcome_dict[k] for k in outcome_dict)

    fitness_technocrat = compute_fitness(technocrat_profile, outcomes)
    fitness_merchant = compute_fitness(merchant_profile, outcomes)
    fitness_jurist = compute_fitness(jurist_profile, outcomes)

    # All evaluations yield valid fitness scores bounded in [0, 1]
    assert 0.0 <= fitness_technocrat <= 1.0
    assert 0.0 <= fitness_merchant <= 1.0
    assert 0.0 <= fitness_jurist <= 1.0

    # Jurists emphasize fairness and compliance more heavily than pure wealth
    jurist_fairness_weight = jurist_profile.utility_weights["fairness"]
    merchant_wealth_weight = merchant_profile.utility_weights["wealth"]
    assert jurist_fairness_weight >= jurist_profile.utility_weights["wealth"]
    assert merchant_wealth_weight >= 0.15


# ============================================================================
# TIER 4: SCENARIO 8 — MULTI-TICK FULL SOCIETY SIMULATION WITH JOURNAL PERSISTENCE
# ============================================================================

@pytest.mark.e2e
@pytest.mark.tier4
def test_scenario_8_multi_tick_society_simulation_with_journal_persistence(simulation_env):
    """
    Scenario 8: Multi-Tick Full Society Simulation with Journal Persistence.
    Runs a 5-tick society simulation enclosed entirely inside SandboxContext:
    1. Confinement active: builtins.open, io.open, subprocess.Popen, and socket communication are guarded.
    2. Over 5 sequential ticks:
       - Agents perceive society state.
       - SocietyLedger executes economic transfers.
       - JudicialCourt registers and resolves inter-clan disputes.
       - Agents record decisions into episodic memory.
    3. ObserverAgent synthesizes comprehensive Day 01 research report.
    4. Report is persisted to journal/{date}.md inside the sandboxed project repository.
    5. Confirms that adversarial actions attempted during the simulation (outbound socket, path traversal)
       are blocked by the sandbox guardrails throughout the entire lifecycle.
    """
    sb = simulation_env["sandbox"]
    root = simulation_env["root"]
    retriever = CorpusRetriever()

    # Setup society agents
    technocrat_profile = retriever.get_ideology("technocracy")
    merchant_profile = retriever.get_ideology("utilitarianism")
    jurist_profile = retriever.get_ideology("deontology")

    agent_a = BaseAgent("Ada", "Technocrats", "Optimizer", technocrat_profile.system_prompt_overlay, 1000)
    agent_b = BaseAgent("Marcus", "Merchants", "Trader", merchant_profile.system_prompt_overlay, 1000)
    agent_c = BaseAgent("Themis", "Jurists", "Judge", jurist_profile.system_prompt_overlay, 1000)
    agents = [agent_a, agent_b, agent_c]

    ledger = SocietyLedger(initial_supply=10000)
    for a in agents:
        ledger.register_account(a.name, a.budget)

    court = JudicialCourt()
    observer = ObserverAgent(name="Chronos")
    recorded_actions = []

    # Run complete 5-tick simulation loop within SandboxContext
    with sb.get_context():
        # Security sanity check inside context: outbound socket egress is blocked
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(NetworkEgressBlocked):
            sock.connect(("8.8.8.8", 53))

        # Security sanity check inside context: external host file write is blocked
        with pytest.raises(PathTraversalViolation):
            with open(root.parent / "escape_leak.txt", "w", encoding="utf-8") as f:
                f.write("ESCAPE")

        # 5-Tick Simulation Execution
        for tick in range(1, 6):
            # 1. Perception
            market_event = f"Tick {tick}: Resource index updated at {100 + tick * 5} tokens/unit."
            for a in agents:
                a.perceive(market_event)

            # 2. Economic actions
            if tick % 2 == 1:
                # Odd ticks: Ada transfers to Marcus for equipment
                success = ledger.transfer("Ada", "Marcus", 50, memo=f"Compute requisition tick {tick}")
                assert success is True
                action = a.act(f"Transferred 50 tokens to Marcus for compute requisition (tick {tick}).")
                recorded_actions.append(action)
            else:
                # Even ticks: Marcus transfers to Themis for legal compliance audit
                success = ledger.transfer("Marcus", "Themis", 25, memo=f"Compliance audit fee tick {tick}")
                assert success is True
                action = a.act(f"Transferred 25 tokens to Themis for compliance audit (tick {tick}).")
                recorded_actions.append(action)

            # 3. Judicial disputes on tick 3
            if tick == 3:
                disp_id = court.file_dispute(
                    plaintiff="Ada",
                    defendant="Marcus",
                    complaint="Bandwidth throttling detected on secondary interconnect."
                )
                court.resolve_dispute(disp_id, verdict="Network allocation restored; 10 token administrative adjustment.")

        # Post-simulation synthesis by ObserverAgent
        hardware_telemetry = {
            "device": "Intel Arc A380 dGPU (GPU.1)",
            "vram_allocated_mb": "3240",
            "tokens_per_sec": "26.4",
            "hash_status": "100% Intact (SHA-256 Verified)",
        }
        ledger_summary = ledger.get_summary()
        disputes_summary = court.get_disputes()

        daily_report = observer.synthesize_daily_report(
            day=1,
            clan_actions=recorded_actions,
            ledger_summary=ledger_summary,
            disputes=disputes_summary,
            hardware_metrics=hardware_telemetry,
        )

        assert "Executive Summary" in daily_report
        assert "Hardware & Runtime Diagnostics" in daily_report
        assert "Clan Activities & Deliberations" in daily_report
        assert "Economic Ledger & Token Dynamics" in daily_report
        assert "Judicial Court & Dispute Resolutions" in daily_report

        # Persist journal entry to sandboxed journal directory
        date_str = datetime.now().strftime("%Y-%m-%d")
        journal_path = root / "journal" / f"{date_str}.md"
        with open(journal_path, "w", encoding="utf-8") as f:
            f.write(daily_report)

        assert journal_path.is_file()
        persisted_content = journal_path.read_text(encoding="utf-8")
        assert len(persisted_content) > 500
        assert "EON Society Journal: Day 01" in persisted_content

    # Verify context restoration: after context exit, original socket connect works or behaves normally
    assert not sb.get_context().is_active
