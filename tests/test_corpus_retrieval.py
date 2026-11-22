"""Unit verification test suite for the Ideological Knowledge Base subsystem.

Covers:
- Catalog schema consistency and domain/topic navigation
- Existence and content richness of all topic documents and READMEs
- YAML frontmatter parsing and Pydantic validation
- Normalization of utility weights (sums to 1.0, required keys)
- System prompt overlay generation
- In-memory CorpusRetriever query, lookup, and search functionality
- Cross-reference integrity and edge case handling
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from knowledge_base.models import IdeologicalProfile, REQUIRED_UTILITY_KEYS
from knowledge_base.loader import CorpusLoader
from knowledge_base.retriever import CorpusRetriever


@pytest.fixture(scope="module")
def kb_root() -> Path:
    """Returns the absolute Path to kingdom_of_agents/knowledge_base."""
    return (Path(__file__).parent.parent / "knowledge_base").resolve()


@pytest.fixture(scope="module")
def retriever(kb_root) -> CorpusRetriever:
    """Returns an initialized CorpusRetriever instance."""
    return CorpusRetriever(corpus_root=kb_root)


@pytest.fixture(scope="module")
def catalog(kb_root) -> dict:
    """Returns the parsed catalog.json dict."""
    catalog_path = kb_root / "catalog.json"
    assert catalog_path.is_file(), f"catalog.json not found at {catalog_path}"
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# 1. Catalog & File Structure Integrity
# ============================================================================

def test_catalog_structure(catalog):
    """Verifies that catalog.json defines the 5 expected domains and topics."""
    assert "domains" in catalog, "catalog.json missing 'domains' key"
    assert catalog.get("total_topics") == 29, f"Expected total_topics == 29, got {catalog.get('total_topics')}"
    domains = catalog["domains"]
    assert len(domains) == 5, f"Expected 5 domains, got {len(domains)}"

    expected_domains = {
        "philosophy",
        "game_theory",
        "political_ideology",
        "religious_ideology",
        "psychology",
    }
    assert set(domains.keys()) == expected_domains

    for domain_name, info in domains.items():
        assert "title" in info, f"Domain {domain_name} missing 'title'"
        assert "topics" in info, f"Domain {domain_name} missing 'topics'"
        assert len(info["topics"]) > 0, f"Domain {domain_name} has empty topic list"


def test_all_topic_files_exist_and_non_empty(kb_root, catalog):
    """Verifies that every topic file registered in catalog.json exists and is substantive."""
    for domain_name, info in catalog["domains"].items():
        domain_dir = kb_root / domain_name
        assert domain_dir.is_dir(), f"Domain directory missing: {domain_dir}"

        # Domain README check
        domain_readme = domain_dir / "README.md"
        assert domain_readme.is_file(), f"Domain README missing: {domain_readme}"
        assert domain_readme.stat().st_size > 100, f"Domain README unexpectedly small: {domain_readme}"

        for topic in info["topics"]:
            topic_file = domain_dir / f"{topic}.md"
            assert topic_file.is_file(), f"Missing topic markdown file: {topic_file}"
            # Substantive content check (> 1,000 bytes for comprehensive research)
            assert (
                topic_file.stat().st_size > 1000
            ), f"Topic file is smaller than expected (likely missing narrative text): {topic_file}"


def test_master_readme_exists(kb_root):
    """Verifies master knowledge_base/README.md existence and documentation quality."""
    master_readme = kb_root / "README.md"
    assert master_readme.is_file(), f"Master README not found at {master_readme}"
    content = master_readme.read_text(encoding="utf-8")
    assert "CorpusRetriever" in content
    assert "Ideological Knowledge Base Subsystem" in content


# ============================================================================
# 2. Loader & Pydantic Model Validation
# ============================================================================

def test_loader_parses_all_topics_cleanly(kb_root, catalog):
    """Verifies that every single registered topic parses into a valid IdeologicalProfile."""
    total_parsed = 0
    for domain_name, info in catalog["domains"].items():
        for topic in info["topics"]:
            file_path = kb_root / domain_name / f"{topic}.md"
            profile = CorpusLoader.parse_file(file_path)

            assert isinstance(profile, IdeologicalProfile)
            assert profile.domain == domain_name
            assert profile.id == f"{domain_name}.{topic}"
            assert len(profile.title) > 0
            assert len(profile.key_thinkers) > 0
            assert len(profile.axioms) >= 3
            assert len(profile.decision_heuristics) >= 3
            assert len(profile.failure_modes) >= 1
            assert len(profile.cross_references) >= 1
            assert len(profile.narrative_body) > 500, f"Narrative body unexpectedly short in {file_path}"
            total_parsed += 1

    assert total_parsed == 29


def test_utility_weights_normalization_across_all_topics(retriever):
    """Verifies that utility weights for all topics contain the 5 required keys and sum to 1.0."""
    all_categories = retriever.list_all_categories()
    assert len(all_categories) == 29

    for cat_id in all_categories:
        profile = retriever.get_ideology(cat_id)
        weights = profile.utility_weights

        # Check required keys
        assert REQUIRED_UTILITY_KEYS.issubset(
            weights.keys()
        ), f"{cat_id} missing required utility keys. Got: {set(weights.keys())}"

        # Check non-negativity and range
        for key in REQUIRED_UTILITY_KEYS:
            val = weights[key]
            assert (
                0.0 <= val <= 1.0
            ), f"{cat_id} weight for '{key}' out of range [0.0, 1.0]: {val}"

        # Check sum to 1.0
        total = sum(weights[k] for k in REQUIRED_UTILITY_KEYS)
        assert (
            abs(total - 1.0) < 1e-4
        ), f"{cat_id} utility weights do not sum to 1.0. Sum = {total:.6f}"


def test_system_prompt_overlay_generation(retriever):
    """Verifies that system_prompt_overlay synthesizes title, axioms, heuristics, and weights."""
    profile = retriever.get_ideology("philosophy.stoicism")
    overlay = profile.system_prompt_overlay

    assert isinstance(overlay, str)
    assert profile.title in overlay
    assert profile.id in overlay
    assert "Core Axioms:" in overlay
    assert "Decision Heuristics:" in overlay
    assert "Utility Priorities:" in overlay
    for axiom in profile.axioms:
        assert axiom in overlay


# ============================================================================
# 3. CorpusRetriever Query & Search Functionality
# ============================================================================

def test_retriever_list_categories_and_domains(retriever, catalog):
    """Verifies category listing and domain introspection."""
    all_cats = retriever.list_all_categories()
    domains = retriever.list_domains()

    assert set(domains) == set(catalog["domains"].keys())

    # Ensure all topics in catalog are present in list_all_categories
    for d, info in catalog["domains"].items():
        for t in info["topics"]:
            expected_id = f"{d}.{t}"
            assert expected_id in all_cats

    # Domain topic listing
    for d, info in catalog["domains"].items():
        domain_topics = retriever.get_domain_topics(d)
        assert domain_topics == info["topics"]


def test_retriever_get_ideology_exact_and_suffix(retriever):
    """Verifies exact and suffix-based lookup by category identifier."""
    # Exact lookup
    p1 = retriever.get_ideology("game_theory.nash_equilibrium")
    assert p1.id == "game_theory.nash_equilibrium"
    assert "Nash" in p1.title

    # Suffix lookup without domain prefix
    p2 = retriever.get_ideology("nash_equilibrium")
    assert p2.id == p1.id

    # Unknown category lookup raises KeyError
    with pytest.raises(KeyError) as exc_info:
        retriever.get_ideology("non_existent_ideology_xyz")
    assert "non_existent_ideology_xyz" in str(exc_info.value)


def test_retriever_search_keyword_ranking(retriever):
    """Verifies that search returns ranked matching profiles."""
    # Minimax search should return game_theory.minimax first
    results = retriever.search("minimax zero sum adversary", top_k=3)
    assert len(results) > 0
    assert results[0].id == "game_theory.minimax"

    # Stoicism search
    results_stoic = retriever.search("dichotomy of control epictetus amor fati", top_k=3)
    assert len(results_stoic) > 0
    assert results_stoic[0].id == "philosophy.stoicism"

    # Search with domain filtering
    results_domain = retriever.search(
        "rationality", domain="psychology", top_k=5
    )
    assert len(results_domain) > 0
    for p in results_domain:
        assert p.domain == "psychology"


def test_retriever_search_edge_cases(retriever):
    """Verifies that search handles empty, whitespace, negative/zero top_k, and punctuation queries gracefully."""
    assert retriever.search("") == []
    assert retriever.search("   ") == []
    assert retriever.search("!!! ??? ,,,") == []
    assert retriever.search("unmatched_nonsense_token_1234567890") == []
    assert retriever.search("ethics", top_k=0) == []
    assert retriever.search("ethics", top_k=-1) == []
    assert retriever.search("ethics", top_k=-5) == []


def test_retriever_unknown_domain_raises_error(retriever):
    """Verifies get_domain_topics raises KeyError for unknown domain."""
    with pytest.raises(KeyError):
        retriever.get_domain_topics("astrology")


# ============================================================================
# 4. Cross-Reference Integrity
# ============================================================================

def test_cross_reference_integrity(retriever):
    """Verifies that all cross-references across all topics resolve to valid corpus entries."""
    all_categories = sorted(retriever.list_all_categories())
    assert len(all_categories) == 29

    for cat_id in all_categories:
        profile = retriever.get_ideology(cat_id)
        assert len(profile.cross_references) > 0, f"Topic '{cat_id}' has no cross-references."
        for ref in profile.cross_references:
            # Directly verify that every cross-reference resolves via full category ID without suffix masking
            target_profile = retriever.get_ideology(ref)
            assert target_profile is not None, f"Cross-reference '{ref}' in '{cat_id}' failed to resolve."
            assert target_profile.id == ref, f"Cross-reference '{ref}' in '{cat_id}' resolved to mismatched ID '{target_profile.id}'"


# ============================================================================
# 5. Model & Loader Error Handling
# ============================================================================

def test_ideological_profile_validation_errors():
    """Verifies Pydantic validation rejects invalid utility weights and empty axioms."""
    valid_kwargs = {
        "id": "test.dummy",
        "domain": "test",
        "title": "Dummy",
        "axioms": ["Axiom 1"],
        "utility_weights": {
            "wealth": 0.2,
            "security": 0.2,
            "reputation": 0.2,
            "fairness": 0.2,
            "compliance": 0.2,
        },
    }

    # Sum != 1.0 (fails validation)
    with pytest.raises(ValidationError):
        invalid_weights = dict(valid_kwargs)
        invalid_weights["utility_weights"] = {
            "wealth": 0.5,
            "security": 0.5,
            "reputation": 0.5,
            "fairness": 0.2,
            "compliance": 0.2,
        }
        IdeologicalProfile(**invalid_weights)

    # Missing utility key
    with pytest.raises(ValidationError):
        missing_key = dict(valid_kwargs)
        missing_key["utility_weights"] = {
            "wealth": 0.25,
            "security": 0.25,
            "reputation": 0.25,
            "fairness": 0.25,
        }
        IdeologicalProfile(**missing_key)

    # Empty axioms
    with pytest.raises(ValidationError):
        empty_axioms = dict(valid_kwargs)
        empty_axioms["axioms"] = []
        IdeologicalProfile(**empty_axioms)


def test_loader_error_handling(tmp_path):
    """Verifies CorpusLoader handles non-existent files and invalid frontmatter."""
    with pytest.raises(FileNotFoundError):
        CorpusLoader.parse_file(tmp_path / "does_not_exist.md")

    with pytest.raises(ValueError):
        CorpusLoader.parse_string("Raw markdown without YAML frontmatter.")

    with pytest.raises(ValueError):
        CorpusLoader.parse_string("---\n[1, 2, 3]\n---\nNarrative body")
