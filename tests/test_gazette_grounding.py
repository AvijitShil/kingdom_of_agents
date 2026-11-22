"""
Tests for Observer Agent Gazette Synthesis & Grounding
"""

import pytest
from agents.observer import ObserverAgent
from society.agora import AgoraChannel, AgoraMessage
from society.survival import MetabolicEngine


def test_gazette_synthesis_grounding():
    channel = AgoraChannel(day=1)
    channel.post(AgoraMessage(
        sender="Archivist-01",
        clan="Clan Alpha (Technocrats)",
        target="@ClanBeta (Merchants)",
        chain_of_thought="Our energy reserves are critically balanced against food.",
        public_message="We propose a bilateral compute-for-grain exchange treaty.",
        intent="PROPOSAL",
        codebook_reference="Utilitarianism",
    ))
    channel.post(AgoraMessage(
        sender="Trader-01",
        clan="Clan Beta (Merchants)",
        target="@Archivist-01",
        chain_of_thought="Tit-for-Tat dictates we demand escrow.",
        public_message="We accept provided the High Court guarantees delivery.",
        intent="ACCORD",
        codebook_reference="Game Theory Tit-for-Tat",
    ))

    metabolic_engine = MetabolicEngine()
    survival_summary = metabolic_engine.get_society_survival_summary()

    observer = ObserverAgent(name="Chronos")
    gazette = observer.synthesize_daily_report(
        day=1,
        agora_channel=channel,
        survival_summary=survival_summary,
        ledger_summary={"transaction_count": 2, "total_circulation": 9000, "velocity": "0.67x"},
    )

    # Assert newspaper layout
    assert "# 📰 The Kingdom Gazette: Day 01" in gazette
    assert "## 🔥 FRONT PAGE:" in gazette
    assert "## 📊 Clan Survival & Vitality Ledger" in gazette
    assert "Clan Alpha (The Technocrats)" in gazette

    # Assert zero-hallucination grounding in the Agora transcript
    assert "Behind Closed Minds: Leaked Chains of Thought" in gazette
    assert "Our energy reserves are critically balanced against food" in gazette
    assert "Tit-for-Tat dictates we demand escrow" in gazette
    assert "We propose a bilateral compute-for-grain exchange treaty" in gazette
    assert "We accept provided the High Court guarantees delivery" in gazette
