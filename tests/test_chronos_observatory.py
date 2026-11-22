"""
tests/test_chronos_observatory.py
EON 2.0 â€” Tests for Chronos Civilization Observatory, GazetteRenderer, and archives.
"""

import os
import json
import uuid
import pytest
from observer.chronos import Chronos, ChronosEvent, EventType, AgentRunningProfile
from observer.gazette import GazetteRenderer


def test_log_event_returns_valid_uuid(tmp_path):
    """log_event returns a valid UUID4 string."""
    chronos = Chronos(journal_root=str(tmp_path))
    eid = chronos.log_event(
        event_type=EventType.SPEECH,
        sim_day=1,
        sim_date="2026-11-22",
        agents=["Athena"],
        speech="Let us pool our grain.",
        intent="establish mutual aid",
        executed_action="spoke in Agora",
        outcome="Athena addressed the assembly",
    )
    # Must be valid UUID
    parsed = uuid.UUID(eid)
    assert str(parsed) == eid


def test_speech_intent_execution_outcome_distinct(tmp_path):
    """Chronos must log speech, intent, execution, and outcome distinctly."""
    chronos = Chronos(journal_root=str(tmp_path))
    eid = chronos.log_event(
        event_type=EventType.TRANSACTION,
        sim_day=1,
        sim_date="2026-11-22",
        agents=["Hermes", "Prometheus"],
        speech="I will sell 5 units of grain for 15 tokens.",
        intent="secure liquidity for water",
        executed_action="transferred 15 tokens Hermes->Prometheus",
        outcome="Grain delivery completed without dispute",
    )
    ev = chronos.get_days_events()[0]
    assert ev.speech == "I will sell 5 units of grain for 15 tokens."
    assert ev.intent == "secure liquidity for water"
    assert ev.executed_action == "transferred 15 tokens Hermes->Prometheus"
    assert ev.outcome == "Grain delivery completed without dispute"


def test_agent_log_file_created(tmp_path):
    """Logging an event creates an agent jsonl file in journal/agents/."""
    chronos = Chronos(journal_root=str(tmp_path))
    chronos.log_event(
        event_type=EventType.BIRTH,
        sim_day=2,
        sim_date="2026-11-23",
        agents=["Achilles", "Phaedra"],
        speech="Welcome our child.",
        intent="expand family lineage",
        executed_action="birth registered",
        outcome="Achilles was born to Phaedra",
    )
    agent_file = tmp_path / "agents" / "Achilles.jsonl"
    assert agent_file.exists()
    lines = agent_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["type"] == "BIRTH"
    assert data["outcome"] == "Achilles was born to Phaedra"


def test_flush_day_creates_transcript_file(tmp_path):
    """flush_day writes all day events to transcripts and clears in-memory day events."""
    chronos = Chronos(journal_root=str(tmp_path))
    chronos.log_event(
        event_type=EventType.CONFLICT,
        sim_day=3,
        sim_date="2026-11-24",
        agents=["Lysander", "Orion"],
        speech="This water cistern belongs to our clan!",
        intent="seize contested resource",
        executed_action="dispute raised in agora",
        outcome="Mediated by Solon; cistern divided equally",
    )
    assert len(chronos.get_days_events()) == 1
    chronos.flush_day(sim_day=3, sim_date="2026-11-24")
    assert len(chronos.get_days_events()) == 0

    transcript_file = tmp_path / "transcripts" / "2026-11-24_events.jsonl"
    assert transcript_file.exists()


def test_update_agent_profile_creates_json_file(tmp_path):
    """update_agent_profile writes {name}_profile.json in journal/agents/."""
    chronos = Chronos(journal_root=str(tmp_path))
    chronos.update_agent_profile(
        name="Solon",
        birth_day=1,
        survival_state="SECURE",
        clan="clan_solon",
        day=1,
    )
    profile_file = tmp_path / "agents" / "Solon_profile.json"
    assert profile_file.exists()
    data = json.loads(profile_file.read_text(encoding="utf-8"))
    assert data["name"] == "Solon"
    assert data["survival_state"] == "SECURE"


def test_load_agent_profiles_roundtrip(tmp_path):
    """load_agent_profiles reads all stored profiles into memory."""
    chronos1 = Chronos(journal_root=str(tmp_path))
    chronos1.update_agent_profile(name="Athena", birth_day=0, survival_state="SECURE", day=1)
    chronos1.update_agent_profile(name="Hermes", birth_day=0, survival_state="WARNING", day=1)

    chronos2 = Chronos(journal_root=str(tmp_path))
    chronos2.load_agent_profiles()
    assert "Athena" in chronos2.agent_profiles
    assert "Hermes" in chronos2.agent_profiles
    assert chronos2.agent_profiles["Hermes"].survival_state == "WARNING"


def test_gazette_renderer_generates_all_sections(tmp_path):
    """GazetteRenderer produces a comprehensive newspaper report with all sections."""
    chronos = Chronos(journal_root=str(tmp_path))
    renderer = GazetteRenderer(chronos)

    ledger_summary = {
        "total_circulation": 10000,
        "transaction_count": 14,
        "velocity": "1.17x",
    }
    survival_summary = {
        "alive": ["Athena", "Hermes", "Prometheus"],
        "critical": ["Hermes"],
        "deceased": [],
    }
    agora_highlights = ["Athena proposed a food cooperative.", "Hermes sought a 20-token emergency loan."]

    gazette = renderer.render_daily_gazette(
        sim_day=2,
        sim_date="2026-11-23",
        ledger_summary=ledger_summary,
        survival_summary=survival_summary,
        agora_highlights=agora_highlights,
    )

    assert "# THE EON CIVILIZATION GAZETTE" in gazette
    assert "DEMOGRAPHICS" in gazette
    assert "KINGDOMS & POLITICAL ORDER" in gazette
    assert "CLANS & FACTIONS" in gazette
    assert "ECONOMY & TOKEN LEDGER" in gazette
    assert "AGORA — PUBLIC DISCOURSE" in gazette
    assert "SURVIVAL ALERTS" in gazette
    assert "Hermes" in gazette


def test_gazette_saved_to_daily_archive(tmp_path):
    """save_gazette writes to journal/daily/YYYY-MM-DD.md."""
    chronos = Chronos(journal_root=str(tmp_path))
    renderer = GazetteRenderer(chronos)
    sample_text = "# THE EON CIVILIZATION GAZETTE\nDay 1 report"
    saved_path = renderer.save_gazette(sample_text, "2026-11-22")
    assert os.path.exists(saved_path)
    assert saved_path.endswith(os.path.join("daily", "2026-11-22.md"))
