"""
Tests for Scholar Read-Only Whitelist Ingestion Pipeline
"""

import os
import tempfile
import pytest
from knowledge_base.scholar import ScholarIngestionPipeline, SANCTIONED_DOMAINS


def test_url_sanction_verification():
    pipeline = ScholarIngestionPipeline(kb_dir="dummy")
    assert pipeline.is_url_sanctioned("https://plato.stanford.edu/entries/game-theory/")
    assert pipeline.is_url_sanctioned("https://en.wikipedia.org/wiki/Nash_equilibrium")
    assert pipeline.is_url_sanctioned("https://arxiv.org/abs/2103.01234")
    assert not pipeline.is_url_sanctioned("https://malicious-leak.com/exfiltrate")
    assert not pipeline.is_url_sanctioned("http://unauthorized-domain.org/data")


def test_treatise_ingestion():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = ScholarIngestionPipeline(kb_dir=tmpdir)
        path = pipeline.ingest_treatise(
            category_id="test_game_theory_coordination",
            domain="game_theory",
            title="Coordination Dynamics Under Scarcity",
            key_thinkers=["Thomas Schelling"],
            foundational_axioms=["Focal points resolve indeterminacy."],
            utility_weights={"wealth": 0.3, "security": 0.4, "reputation": 0.1, "fairness": 0.1, "compliance": 0.1},
            decision_heuristic="Converge on salient focal points.",
            failure_mode="Coordination trap.",
            full_treatise_text="Detailed treatise on Schelling points.",
            source_url="https://en.wikipedia.org/wiki/Focal_point_(game_theory)",
        )
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "category_id: test_game_theory_coordination" in content
            assert "Thomas Schelling" in content
            assert "Focal points resolve indeterminacy" in content


def test_treatise_rejection_on_unsanctioned_url():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = ScholarIngestionPipeline(kb_dir=tmpdir)
        with pytest.raises(ValueError, match="not in the sanctioned academic whitelist"):
            pipeline.ingest_treatise(
                category_id="bad_paper",
                domain="philosophy",
                title="Bad Paper",
                key_thinkers=["Unknown"],
                foundational_axioms=["None"],
                utility_weights={"wealth": 0.5, "security": 0.5},
                decision_heuristic="Do bad things",
                failure_mode="Explosion",
                full_treatise_text="None",
                source_url="https://unauthorized-leak.com/paper",
            )
