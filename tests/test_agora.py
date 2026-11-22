"""
Tests for Agora Town Square Group Chat Medium
"""

import os
import tempfile
import pytest
from society.agora import AgoraChannel, AgoraMessage


def test_agora_message_creation():
    msg = AgoraMessage(
        sender="Archivist-01",
        clan="Clan Alpha (Technocrats)",
        target="@ClanBeta",
        chain_of_thought="We need rations urgently.",
        public_message="We propose trading compute for grain.",
        intent="PROPOSAL",
        codebook_reference="Utilitarianism",
        tick=1,
    )
    assert msg.sender == "Archivist-01"
    assert msg.target == "@ClanBeta"
    assert "We need rations" in msg.chain_of_thought
    assert "trading compute" in msg.public_message
    d = msg.to_dict()
    assert d["intent"] == "PROPOSAL"


def test_agora_channel_post_and_context():
    channel = AgoraChannel(day=1)
    m1 = AgoraMessage(
        sender="Archivist-01",
        clan="Clan Alpha",
        target="@ClanBeta",
        chain_of_thought="Secret plan A",
        public_message="Offer to beta",
        intent="PROPOSAL",
    )
    m2 = AgoraMessage(
        sender="Trader-01",
        clan="Clan Beta",
        target="@Archivist-01",
        chain_of_thought="Counter plan B",
        public_message="Countering alpha offer",
        intent="COUNTER_OFFER",
    )
    channel.post(m1)
    channel.post(m2)

    assert len(channel.messages) == 2
    context = channel.get_context_for_agent("Archivist-01", "Clan Alpha")
    assert "DIRECTED TO YOU" in context
    assert "Countering alpha offer" in context


def test_agora_channel_exports():
    channel = AgoraChannel(day=1)
    channel.post(AgoraMessage(
        sender="Justiciar-01",
        clan="Clan Gamma",
        target="@all",
        chain_of_thought="Maintain constitutional order",
        public_message="Order in the Agora!",
        intent="ACCORD",
    ))

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, "test_agora.md")
        jsonl_path = os.path.join(tmpdir, "test_agora.jsonl")

        channel.export_markdown_transcript(md_path)
        channel.export_jsonl(jsonl_path)

        assert os.path.exists(md_path)
        assert os.path.exists(jsonl_path)

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Order in the Agora!" in content
            assert "Maintain constitutional order" in content
