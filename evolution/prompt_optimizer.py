"""Prompt optimizer synthesizing base identity, ideological overlays, and reflection lessons."""

from typing import Optional, List
from knowledge_base.models import IdeologicalProfile
from .models import ReflectionRecord


class PromptOptimizer:
    """Synthesizes agent identity, ideological axioms, heuristics, and reflection lessons into prompts."""

    @staticmethod
    def synthesize_system_prompt(
        agent_name: str,
        clan: str,
        role: str,
        base_system_prompt: str = "",
        ideology: Optional[IdeologicalProfile] = None,
        reflection_history: Optional[List[ReflectionRecord]] = None,
        max_reflections: int = 3,
    ) -> str:
        """Compose comprehensive system instructions conditioned on identity, active doctrine, and reflections."""
        sections: List[str] = []

        # 1. Base instructions and Identity
        if base_system_prompt.strip():
            sections.append(base_system_prompt.strip())
        sections.append(f"You are {agent_name} of clan {clan}. Role: {role}.")

        # 2. Active Ideological Overlay (Axioms, Heuristics, Weights)
        if ideology is not None:
            sections.append(ideology.system_prompt_overlay)

        # 3. Adaptive Reflection Lessons
        if reflection_history:
            recent = [] if max_reflections <= 0 else reflection_history[-max_reflections:]
            reflections_text = "\n".join(
                f"- [Tick {r.tick}] (Regret: {r.regret:.2f}) {r.prompt_mutation_suggestion}"
                for r in recent
                if r.prompt_mutation_suggestion
            )
            if reflections_text:
                sections.append(f"### Adaptive Reflection Insights:\n{reflections_text}")

        return "\n\n".join(sections)
