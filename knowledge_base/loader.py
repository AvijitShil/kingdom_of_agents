"""Corpus loader for parsing Markdown research documents with YAML frontmatter."""

import re
from pathlib import Path
from typing import Union, Dict, Any, List
import yaml

from .models import IdeologicalProfile


class CorpusLoader:
    """Parses markdown research documents with YAML frontmatter into IdeologicalProfile models."""

    # Matches YAML frontmatter enclosed by '---' at the start of the document
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", re.DOTALL
    )

    @classmethod
    def parse_string(cls, content: str) -> IdeologicalProfile:
        """Parses a markdown string containing YAML frontmatter and narrative text."""
        stripped = content.strip()
        match = cls.FRONTMATTER_PATTERN.match(stripped)
        if not match:
            raise ValueError(
                "Document does not contain valid YAML frontmatter delimited by '---'."
            )

        frontmatter_raw, narrative_body = match.groups()
        data: Dict[str, Any] = yaml.safe_load(frontmatter_raw)
        if not isinstance(data, dict):
            raise ValueError("Frontmatter failed to parse into a dictionary.")

        # Normalize frontmatter keys
        if "core_axioms" in data and "axioms" not in data:
            data["axioms"] = data["core_axioms"]
        if "category_id" in data and "id" not in data:
            data["id"] = data["category_id"]

        data["narrative_body"] = narrative_body.strip()
        return IdeologicalProfile(**data)

    @classmethod
    def parse_file(cls, file_path: Union[str, Path]) -> IdeologicalProfile:
        """Reads a file from disk and parses it into an IdeologicalProfile."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Corpus topic file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return cls.parse_string(content)

    @classmethod
    def load_directory(cls, dir_path: Union[str, Path]) -> List[IdeologicalProfile]:
        """Loads and parses all markdown files in a directory (excluding README.md)."""
        path = Path(dir_path).resolve()
        if not path.is_dir():
            raise NotADirectoryError(f"Directory not found: {path}")

        profiles: List[IdeologicalProfile] = []
        for file in sorted(path.glob("*.md")):
            if file.name.lower() == "readme.md":
                continue
            profiles.append(cls.parse_file(file))
        return profiles
