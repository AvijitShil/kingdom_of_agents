"""
Tests for Scholar Ingestion Pipeline (Whitelist Security & Ingestion)
"""

import os
import tempfile
import pytest
from knowledge_base.scholar import ScholarIngestionPipeline, SANCTIONED_DOMAINS


def test_scholar_whitelist_validation():
    pipeline = ScholarIngestionPipeline(kb_dir="/tmp/test_kb")
    assert pipeline.is_url_sanctioned("https://plato.stanford.edu/entries/game-theory/")
    assert pipeline.is_url_sanctioned("https://en.wikipedia.org/wiki/Nash_equilibrium")
    assert pipeline.is_url_sanctioned("https://arxiv.org/abs/2103.00000")
    assert not pipeline.is_url_sanctioned("https://evil-hacker.com/exfiltrate")
    assert not pipeline.is_url_sanctioned("http://localhost:8080/data")


def test_scholar_ingestion_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = ScholarIngestionPipeline(kb_dir=tmpdir)
        filepath = pipeline.ingest_treatise(
            category_id="test_survival_treatise",
            domain="game_theory",
            title="Evolutionary Stability Under Resource Depletion",
            key_thinkers=["John Maynard Smith"],
            foundational_axioms=["Axiom 1: Replicator dynamics favor energy-conserving strategies."],
            utility_weights={"wealth": 0.2, "security": 0.4, "reputation": 0.2, "fairness": 0.1, "compliance": 0.1},
            decision_heuristic="Minimize energy expenditure during non-cooperative rounds.",
            failure_mode="Systemic depletion if all agents defect.",
            full_treatise_text="Detailed survival analysis demonstrating energy equilibrium.",
            source_url="https://en.wikipedia.org/wiki/Evolutionary_game_theory",
        )
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Evolutionary Stability Under Resource Depletion" in content
            assert "John Maynard Smith" in content
            assert "Replicator dynamics" in content
