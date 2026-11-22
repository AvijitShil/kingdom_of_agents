"""In-memory retrieval engine for the Ideological Knowledge Base subsystem."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .loader import CorpusLoader
from .models import IdeologicalProfile


class CorpusRetriever:
    """In-memory indexing and retrieval engine for ideological research corpus."""

    def __init__(self, corpus_root: Optional[Union[str, Path]] = None):
        if corpus_root is None:
            corpus_root = Path(__file__).parent.resolve()
        self.corpus_root = Path(corpus_root).resolve()
        self.catalog_path = self.corpus_root / "catalog.json"

        self.catalog: Dict[str, Any] = {}
        self._profiles: Dict[str, IdeologicalProfile] = {}
        self._domain_map: Dict[str, List[str]] = {}

        self._load_corpus()

    def _load_corpus(self) -> None:
        """Loads catalog.json and all referenced topic markdown files into memory."""
        if not self.catalog_path.is_file():
            raise FileNotFoundError(f"Catalog file not found at: {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            self.catalog = json.load(f)

        domains = self.catalog.get("domains", {})
        for domain_key, domain_info in domains.items():
            topics = domain_info.get("topics", [])
            self._domain_map[domain_key] = list(topics)
            domain_dir = self.corpus_root / domain_key
            for topic in topics:
                file_path = domain_dir / f"{topic}.md"
                if not file_path.is_file():
                    raise FileNotFoundError(
                        f"Expected topic file not found: {file_path} (catalog domain: {domain_key})"
                    )
                profile = CorpusLoader.parse_file(file_path)
                self._profiles[profile.id] = profile

    def get_ideology(self, category_id: str) -> IdeologicalProfile:
        """Retrieve an IdeologicalProfile by its unique category_id.
        
        Supports exact matches (e.g. 'philosophy.stoicism') and suffix matches
        (e.g. 'stoicism').
        """
        if category_id in self._profiles:
            return self._profiles[category_id]

        # Check for un-prefixed topic match
        for pid, profile in self._profiles.items():
            if pid.endswith(f".{category_id}"):
                return profile

        available = sorted(list(self._profiles.keys()))
        raise KeyError(
            f"Ideology '{category_id}' not found in corpus. "
            f"Available categories ({len(available)}): {available}"
        )

    def list_all_categories(self) -> List[str]:
        """Returns sorted list of all 29 category IDs."""
        return sorted(list(self._profiles.keys()))

    def list_domains(self) -> List[str]:
        """Returns list of domains defined in the catalog."""
        return list(self._domain_map.keys())

    def get_domain_topics(self, domain: str) -> List[str]:
        """Returns list of topic names for a specific domain."""
        if domain not in self._domain_map:
            raise KeyError(
                f"Domain '{domain}' not found. Available domains: {list(self._domain_map.keys())}"
            )
        return list(self._domain_map[domain])

    def search(
        self, query: str, domain: Optional[str] = None, top_k: int = 3
    ) -> List[IdeologicalProfile]:
        """Keyword/token overlap search across title, axioms, heuristics, thinkers, and narrative text.
        
        Args:
            query: Search query string.
            domain: Optional domain filter (e.g. 'philosophy').
            top_k: Maximum number of ranked results to return.
            
        Returns:
            List of top_k matching IdeologicalProfile objects ranked by relevance.
        """
        if top_k <= 0:
            return []

        if not query or not query.strip():
            return []

        clean_query = query.strip().lower()
        terms = [t for t in re.findall(r"\w+", clean_query) if len(t) > 1]
        if not terms:
            return []

        candidates = list(self._profiles.values())
        if domain:
            candidates = [
                p for p in candidates if p.domain.lower() == domain.lower()
            ]

        scored_profiles = []
        for profile in candidates:
            score = 0.0
            id_lower = profile.id.lower()
            title_lower = profile.title.lower()
            axioms_lower = " ".join(profile.axioms).lower()
            heuristics_lower = " ".join(profile.decision_heuristics).lower()
            thinkers_lower = " ".join(profile.key_thinkers).lower()
            narrative_lower = profile.narrative_body.lower()

            for term in terms:
                # Scored by importance of match location
                if term in id_lower:
                    score += 50.0
                if term in title_lower:
                    score += 40.0
                if term in thinkers_lower:
                    score += 25.0
                if term in axioms_lower:
                    score += 20.0
                if term in heuristics_lower:
                    score += 15.0

                occurrences = narrative_lower.count(term)
                if occurrences > 0:
                    score += min(occurrences * 2.0, 20.0)

            # Bonus for complete phrase match
            if clean_query in title_lower:
                score += 80.0
            if clean_query in axioms_lower:
                score += 50.0
            if clean_query in narrative_lower:
                score += 30.0

            if score > 0.0:
                scored_profiles.append((score, profile))

        scored_profiles.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored_profiles[:top_k]]
