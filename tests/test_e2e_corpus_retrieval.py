"""
End-to-End Corpus Retrieval & Knowledge Base Test Suite (Features 6–11, Scenario 3).

Implements 4-tier testing:
- Tier 1: Feature Coverage (5 domains, all topics, catalog.json, READMEs, retriever API)
- Tier 2: Boundary & Corner Cases (YAML frontmatter schema, utility weight invariant, non-empty axioms, query edge cases)
- Tier 3: Cross-Feature Interactions (caching performance, loading via sandbox)
- Tier 4: Real-World Application Scenarios (Scenario 3: Full Corpus Ingestion and Cross-Domain Querying)
"""

import json
import time
import pathlib
import pytest

from knowledge_base.models import IdeologicalProfile, REQUIRED_UTILITY_KEYS
from knowledge_base.loader import CorpusLoader
from knowledge_base.retriever import CorpusRetriever
from sandbox import SecuritySandbox, Permission


@pytest.fixture(scope="module")
def corpus_root() -> pathlib.Path:
    """Returns the resolved Path to the knowledge_base directory."""
    return (pathlib.Path(__file__).parent.parent / "knowledge_base").resolve()


@pytest.fixture(scope="module")
def retriever(corpus_root) -> CorpusRetriever:
    """Fixture providing a cached CorpusRetriever instance."""
    return CorpusRetriever(corpus_root=corpus_root)


@pytest.fixture(scope="module")
def catalog_data(corpus_root) -> dict:
    """Fixture returning the parsed catalog.json."""
    catalog_file = corpus_root / "catalog.json"
    with open(catalog_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# TIER 1: FEATURE COVERAGE (Features 6–11)
# ============================================================================

# --- Feature 6: Philosophy Corpus (9 topics) ---

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f6_philosophy_topics_exist(corpus_root):
    """F6: Verifies existence of all 7 philosophy topic files."""
    philosophy_dir = corpus_root / "philosophy"
    expected_topics = [
        "epistemology", "metaphysics", "existentialism",
        "utilitarianism", "deontology", "stoicism", "pragmatism"
    ]
    for topic in expected_topics:
        file_path = philosophy_dir / f"{topic}.md"
        assert file_path.is_file(), f"Missing philosophy topic file: {file_path}"
        assert file_path.stat().st_size > 500, f"Philosophy topic file unexpectedly small: {file_path}"


# --- Feature 7: Game Theory Corpus (6 topics) ---

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f7_game_theory_topics_exist(corpus_root):
    """F7: Verifies existence of all 6 game theory topic files."""
    gt_dir = corpus_root / "game_theory"
    expected_topics = [
        "nash_equilibrium", "minimax", "evolutionary_game_theory",
        "pareto_optimality", "mechanism_design", "multi_agent_coordination"
    ]
    for topic in expected_topics:
        file_path = gt_dir / f"{topic}.md"
        assert file_path.is_file(), f"Missing game theory topic file: {file_path}"
        assert file_path.stat().st_size > 500, f"Game theory topic file unexpectedly small: {file_path}"


# --- Feature 8: Political Ideology Corpus (5 topics) ---

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f8_political_ideology_topics_exist(corpus_root):
    """F8: Verifies existence of all 5 political ideology topic files."""
    pol_dir = corpus_root / "political_ideology"
    expected_topics = [
        "classical_liberalism", "libertarianism", "socialism_communitarianism",
        "realism_vs_idealism", "technocracy"
    ]
    for topic in expected_topics:
        file_path = pol_dir / f"{topic}.md"
        assert file_path.is_file(), f"Missing political ideology topic file: {file_path}"
        assert file_path.stat().st_size > 500, f"Political ideology topic file unexpectedly small: {file_path}"


# --- Feature 9: Religious Ideology Corpus (4 topics) ---

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f9_religious_ideology_topics_exist(corpus_root):
    """F9: Verifies existence of all 4 religious ideology topic files."""
    rel_dir = corpus_root / "religious_ideology"
    expected_topics = [
        "dharmic_karma", "abrahamic_covenantal", "taoist_wu_wei", "buddhist_non_attachment"
    ]
    for topic in expected_topics:
        file_path = rel_dir / f"{topic}.md"
        assert file_path.is_file(), f"Missing religious ideology topic file: {file_path}"
        assert file_path.stat().st_size > 500, f"Religious ideology topic file unexpectedly small: {file_path}"


# --- Feature 10: Psychology Corpus (5 topics) ---

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f10_psychology_topics_exist(corpus_root):
    """F10: Verifies existence of all 5 psychology topic files."""
    psych_dir = corpus_root / "psychology"
    expected_topics = [
        "cognitive_biases", "heuristic_decision_making", "maslow_hierarchy",
        "evolutionary_psychology", "behavioral_reinforcement"
    ]
    for topic in expected_topics:
        file_path = psych_dir / f"{topic}.md"
        assert file_path.is_file(), f"Missing psychology topic file: {file_path}"
        assert file_path.stat().st_size > 500, f"Psychology topic file unexpectedly small: {file_path}"


# --- Feature 11: Catalog & Retriever API ---

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f11_catalog_json_schema(catalog_data):
    """F11.1: Validates catalog.json structure, domain count, and topic mappings."""
    assert "version" in catalog_data
    assert catalog_data.get("total_domains") == 5
    domains = catalog_data.get("domains", {})
    assert len(domains) == 5
    for domain_name in ["philosophy", "game_theory", "political_ideology", "religious_ideology", "psychology"]:
        assert domain_name in domains
        d_info = domains[domain_name]
        assert "title" in d_info
        assert "description" in d_info
        assert len(d_info.get("topics", [])) > 0


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f11_domain_readmes_exist(corpus_root):
    """F11.2: Verifies master README.md and all 5 domain README.md documentation files exist."""
    master_readme = corpus_root / "README.md"
    assert master_readme.is_file() and master_readme.stat().st_size > 200

    for domain in ["philosophy", "game_theory", "political_ideology", "religious_ideology", "psychology"]:
        domain_readme = corpus_root / domain / "README.md"
        assert domain_readme.is_file(), f"Missing domain README: {domain_readme}"
        assert domain_readme.stat().st_size > 100


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f11_retriever_list_all_categories(retriever, catalog_data):
    """F11.3: CorpusRetriever.list_all_categories returns all indexed categories."""
    categories = retriever.list_all_categories()
    expected_count = sum(len(d["topics"]) for d in catalog_data["domains"].values())
    assert len(categories) == expected_count
    assert len(categories) >= 27


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f11_retriever_get_ideology_across_domains(retriever):
    """F11.4: CorpusRetriever.get_ideology returns valid IdeologicalProfile for topics across all 5 domains."""
    sample_categories = [
        "philosophy.stoicism",
        "game_theory.nash_equilibrium",
        "political_ideology.technocracy",
        "religious_ideology.taoist_wu_wei",
        "psychology.cognitive_biases",
    ]
    for cat_id in sample_categories:
        profile = retriever.get_ideology(cat_id)
        assert isinstance(profile, IdeologicalProfile)
        assert profile.id == cat_id
        assert len(profile.axioms) > 0
        assert len(profile.decision_heuristics) > 0


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f11_retriever_search_keyword(retriever):
    """F11.5: CorpusRetriever.search returns relevant ranked profiles for keywords."""
    results = retriever.search("equilibrium", top_k=3)
    assert len(results) > 0
    match_ids = [p.id for p in results]
    assert any("nash_equilibrium" in pid or "game_theory" in pid for pid in match_ids)


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier1
def test_f11_retriever_domain_navigation(retriever):
    """F11.6: CorpusRetriever domain and topic navigation helpers return expected lists."""
    domains = retriever.list_domains()
    assert len(domains) == 5
    topics = retriever.get_domain_topics("philosophy")
    assert "stoicism" in topics
    assert "epistemology" in topics


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES (Schema Invariants & Query Edge Cases)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_utility_weights_invariant_across_all_topics(retriever):
    """Tier 2: Validates utility weights invariant across all topics:
    1. Exactly 5 dimensions: wealth, security, reputation, fairness, compliance
    2. Non-negativity: w_i >= 0.0
    3. Sum equals 1.000 ± 0.001
    """
    for cat_id in retriever.list_all_categories():
        profile = retriever.get_ideology(cat_id)
        weights = profile.utility_weights

        # 5 required keys
        assert set(weights.keys()) == REQUIRED_UTILITY_KEYS, f"{cat_id} missing utility keys"

        # Non-negativity and upper bound
        for k, v in weights.items():
            assert 0.0 <= v <= 1.0, f"{cat_id} weight for {k} out of bounds: {v}"

        # Normalization
        total = sum(weights.values())
        assert abs(total - 1.0) <= 0.001, f"{cat_id} utility weights do not sum to 1.0: {total}"


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_frontmatter_required_fields_across_all_topics(retriever):
    """Tier 2: Validates that every topic document has complete, non-empty metadata fields."""
    for cat_id in retriever.list_all_categories():
        profile = retriever.get_ideology(cat_id)
        assert profile.id, f"{cat_id} has empty id"
        assert profile.domain, f"{cat_id} has empty domain"
        assert profile.title, f"{cat_id} has empty title"
        assert len(profile.key_thinkers) > 0, f"{cat_id} has empty key_thinkers"
        assert len(profile.axioms) > 0, f"{cat_id} has empty axioms"
        assert len(profile.decision_heuristics) > 0, f"{cat_id} has empty decision_heuristics"
        assert profile.conflict_resolution_style, f"{cat_id} has empty conflict_resolution_style"
        assert len(profile.failure_modes) > 0, f"{cat_id} has empty failure_modes"
        assert len(profile.narrative_body) > 100, f"{cat_id} narrative body unexpectedly short"


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_system_prompt_overlay_synthesis(retriever):
    """Tier 2: Validates system prompt overlay synthesis for agent conditioning."""
    profile = retriever.get_ideology("philosophy.stoicism")
    overlay = profile.system_prompt_overlay

    assert "### Active Ideology: Stoic" in overlay or "philosophy.stoicism" in overlay
    assert "Core Axioms:" in overlay
    assert "Decision Heuristics:" in overlay
    assert "Utility Priorities:" in overlay
    assert "fairness:" in overlay


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_missing_category_handling(retriever):
    """Tier 2: Querying for non-existent category raises KeyError with available list."""
    with pytest.raises(KeyError) as exc_info:
        retriever.get_ideology("unknown_domain.fictional_doctrine")
    assert "not found in corpus" in str(exc_info.value)


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_empty_or_whitespace_search_query(retriever):
    """Tier 2: Empty or whitespace query returns empty result list."""
    assert retriever.search("") == []
    assert retriever.search("   ") == []
    assert retriever.search("\t\n") == []


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_search_domain_filtering(retriever):
    """Tier 2: Search with domain filter strictly confines results to requested domain."""
    # "cooperation" appears in multiple domains
    results = retriever.search("cooperation", domain="game_theory", top_k=5)
    for p in results:
        assert p.domain == "game_theory", f"Expected game_theory, got {p.domain}"


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_case_insensitive_suffix_lookup(retriever):
    """Tier 2: Suffix-based category lookup without domain prefix resolves properly."""
    profile_full = retriever.get_ideology("philosophy.stoicism")
    profile_suffix = retriever.get_ideology("stoicism")
    assert profile_full.id == profile_suffix.id


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier2
def test_boundary_loader_invalid_frontmatter():
    """Tier 2: Documents without valid frontmatter delimiters raise ValueError."""
    with pytest.raises(ValueError):
        CorpusLoader.parse_string("No frontmatter markdown text here.")

    with pytest.raises(ValueError):
        CorpusLoader.parse_string("---\nnot_a_dictionary\n---\nBody")


# ============================================================================
# TIER 3: CROSS-FEATURE INTERACTIONS (Caching & Sandbox Confinement)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier3
def test_cross_corpus_retrieval_performance_caching(retriever):
    """F11 + Performance: In-memory retrieval provides sub-millisecond query latency."""
    cat_id = "philosophy.stoicism"
    # Warmup
    _ = retriever.get_ideology(cat_id)

    # Benchmark 100 fetches
    start = time.perf_counter()
    for _ in range(100):
        _ = retriever.get_ideology(cat_id)
    duration = time.perf_counter() - start

    avg_latency_ms = (duration / 100) * 1000
    assert avg_latency_ms < 1.0, f"Average in-memory retrieval latency too slow: {avg_latency_ms:.3f}ms"


@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier3
def test_cross_corpus_loading_via_sandbox(isolated_project_dir, corpus_root):
    """F1 + F11: CorpusLoader reads research documents through sandboxed path validation."""
    sb = SecuritySandbox(project_root=isolated_project_dir)
    # Copy a topic into the sandboxed repository
    topic_src = corpus_root / "philosophy" / "stoicism.md"
    sandbox_topic = isolated_project_dir / "knowledge_base" / "stoicism.md"
    sandbox_topic.write_text(topic_src.read_text(encoding="utf-8"), encoding="utf-8")

    # Validate sandboxed access
    validated_path = sb.validator.validate_access(sandbox_topic, Permission.READ)
    profile = CorpusLoader.parse_file(validated_path)
    assert profile.id == "philosophy.stoicism"
    assert profile.domain == "philosophy"


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (Scenario 3)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.corpus
@pytest.mark.tier4
def test_scenario_3_full_corpus_ingestion_and_cross_domain_querying(retriever):
    """
    Scenario 3: Full Corpus Ingestion and Cross-Domain Querying.
    Simulates complete knowledge base ingestion for an autonomous agent:
    1. Ingests all indexed topics across all 5 domains.
    2. Validates that all cross-references across all topics point to existing category IDs.
    3. Performs multi-perspective querying: Given a complex societal scenario (e.g. "scarce resource allocation"),
       queries across philosophy, game theory, and political ideology to retrieve actionable doctrines.
    """
    all_categories = set(retriever.list_all_categories())
    assert len(all_categories) >= 27

    # 1. Cross-reference integrity check
    for cat_id in all_categories:
        profile = retriever.get_ideology(cat_id)
        for ref in profile.cross_references:
            topic_name = ref.split(".")[-1]
            # Verify reference exists in corpus either by full ID or topic name
            ref_found = (ref in all_categories) or any(c.endswith(f".{topic_name}") for c in all_categories)
            assert ref_found, f"Dangling cross-reference in {cat_id}: '{ref}' not found in corpus!"

    # 2. Multi-perspective societal problem query
    # Query 1: Efficiency & Payoff distribution
    payoff_profiles = retriever.search("payoff equilibrium allocation", top_k=3)
    assert len(payoff_profiles) > 0
    domains_represented = {p.domain for p in payoff_profiles}
    assert "game_theory" in domains_represented or "political_ideology" in domains_represented

    # Query 2: Moral duty & Justice
    moral_profiles = retriever.search("duty justice ethics", top_k=3)
    assert len(moral_profiles) > 0
    moral_domains = {p.domain for p in moral_profiles}
    assert "philosophy" in moral_domains or "religious_ideology" in moral_domains

    # Query 3: Decision under uncertainty & Cognitive limitations
    decision_profiles = retriever.search("heuristics uncertainty bounded", top_k=3)
    assert len(decision_profiles) > 0
    decision_domains = {p.domain for p in decision_profiles}
    assert "psychology" in decision_domains or "game_theory" in decision_domains
