"""
Tests for Observer Agent Gazette Grounding (Investigative Newspaper)
"""

import pytest
from society.agora import AgoraChannel, AgoraMessage
from agents.observer import ObserverAgent


def test_gazette_synthesis_grounding():
    channel = AgoraChannel(day=1)
    channel.post(AgoraMessage(
        sender="Archivist-01",
        clan="Clan Alpha (Technocrats)",
        target="@ClanBeta",
        chain_of_thought="Our energy reserves are critically low, must secure food.",
        public_message="We propose 150 energy units for 100 food units.",
        intent="PROPOSAL",
        codebook_reference="Utilitarianism",
    ))
    channel.post(AgoraMessage(
        sender="Trader-01",
        clan="Clan Beta (Merchants)",
        target="@Archivist-01",
        chain_of_thought="Technocrats are desperate, demand higher escrow.",
        public_message="We counter: 120 energy tokens at fixed parity.",
        intent="COUNTER_OFFER",
        codebook_reference="Tit-for-Tat",
    ))

    observer = ObserverAgent(name="Chronos")
    survival_summary = {
        "clan_alpha_technocrats": {
            "title": "Clan Alpha (The Technocrats)",
            "headcount": 12,
            "energy": 650.0,
            "rations": 350.0,
            "vitality_pct": 82.5,
            "status": "PROSPEROUS",
        }
    }

    report = observer.synthesize_daily_report(
        day=1,
        agora_channel=channel,
        survival_summary=survival_summary,
        ledger_summary={"transaction_count": 2, "total_circulation": 9000, "velocity": "0.67x"},
    )

    # Verify no hallucination: must contain exact verbatim quotes and CoT
    assert "# 📰 The Kingdom Gazette: Day 01" in report
    assert "We propose 150 energy units for 100 food units." in report
    assert "Our energy reserves are critically low, must secure food." in report
    assert "Clan Alpha (The Technocrats)" in report
    assert "82.5%" in report
    assert "Behind Closed Minds: Leaked Chains of Thought" in report
