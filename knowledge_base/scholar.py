"""
EON Scholar Read-Only Whitelist Ingestion Pipeline
Allows Scholar agents to research survival, game theory, and philosophical treatises from
sanctioned academic domains and safely format them into the Survival Codebook (knowledge_base/).
Enforces strict read-only outbound rules with zero data leakage.
"""

import os
import re
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional
from datetime import datetime

SANCTIONED_DOMAINS = [
    "plato.stanford.edu",
    "en.wikipedia.org",
    "arxiv.org",
]


class ScholarIngestionPipeline:
    """Manages secure retrieval of academic strategy and survival treatises."""

    def __init__(self, kb_dir: str):
        self.kb_dir = os.path.abspath(kb_dir)
        os.makedirs(self.kb_dir, exist_ok=True)

    def is_url_sanctioned(self, url: str) -> bool:
        """Verify that the target URL belongs strictly to a sanctioned academic domain."""
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            return any(netloc == domain or netloc.endswith(f".{domain}") for domain in SANCTIONED_DOMAINS)
        except Exception:
            return False

    def format_codebook_entry(
        self,
        category_id: str,
        domain: str,
        title: str,
        key_thinkers: List[str],
        foundational_axioms: List[str],
        utility_weights: Dict[str, float],
        decision_heuristic: str,
        failure_mode: str,
        full_treatise_text: str,
    ) -> str:
        """Format paper content into the standard EON Knowledge Base Markdown specification."""
        thinkers_yaml = "[" + ", ".join([f'"{t}"' for t in key_thinkers]) + "]"
        axioms_yaml = "\n".join([f'  - "{a}"' for a in foundational_axioms])
        weights_yaml = ", ".join([f"{k}: {v}" for k, v in utility_weights.items()])

        return f"""---
category_id: {category_id}
domain: {domain}
title: "{title}"
key_thinkers: {thinkers_yaml}
foundational_axioms:
{axioms_yaml}
utility_weights: {{{weights_yaml}}}
decision_heuristic: "{decision_heuristic}"
failure_mode: "{failure_mode}"
date_ingested: "{datetime.now().strftime('%Y-%m-%d')}"
---

# {title}

## Abstract & Survival Heuristic
{decision_heuristic}

## Strategic Foundations & Axioms
{full_treatise_text}

## Systemic Failure Modes & Risks
{failure_mode}
"""

    def ingest_treatise(
        self,
        category_id: str,
        domain: str,
        title: str,
        key_thinkers: List[str],
        foundational_axioms: List[str],
        utility_weights: Dict[str, float],
        decision_heuristic: str,
        failure_mode: str,
        full_treatise_text: str,
        source_url: Optional[str] = None,
    ) -> str:
        """Save a new survival paper into knowledge_base/."""
        if source_url and not self.is_url_sanctioned(source_url):
            raise ValueError(f"Ingestion rejected: Source URL '{source_url}' is not in the sanctioned academic whitelist.")

        filename = f"{category_id}.md"
        filepath = os.path.join(self.kb_dir, filename)

        content = self.format_codebook_entry(
            category_id=category_id,
            domain=domain,
            title=title,
            key_thinkers=key_thinkers,
            foundational_axioms=foundational_axioms,
            utility_weights=utility_weights,
            decision_heuristic=decision_heuristic,
            failure_mode=failure_mode,
            full_treatise_text=full_treatise_text,
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
