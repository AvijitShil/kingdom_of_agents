"""
EON Memory Guard & Rolling Context Manager
Enforces rolling context truncation (K=6 turns) and episodic memory summarization
to protect the Intel Arc A380 6GB dGPU (GPU.1) against RAM and VRAM exhaustion
during uncapped continuous simulation cycles.
"""

from typing import List, Dict, Any, Optional


class MemoryGuard:
    """Safeguards VRAM / RAM limits by maintaining a sliding-window KV memory footprint."""

    def __init__(self, max_rolling_turns: int = 6, max_token_budget: int = 4096):
        self.max_rolling_turns = max_rolling_turns
        self.max_token_budget = max_token_budget
        self.condensed_episodic_log: List[str] = []

    def truncate_history(self, dialogue_turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Truncate conversation history to at most `max_rolling_turns`.
        Earlier turns are archived into high-level episodic memory strings.
        """
        if len(dialogue_turns) <= self.max_rolling_turns:
            return dialogue_turns

        overflow_count = len(dialogue_turns) - self.max_rolling_turns
        overflow_turns = dialogue_turns[:overflow_count]
        active_window = dialogue_turns[overflow_count:]

        # Summarize evicted turns into episodic memory
        for turn in overflow_turns:
            speaker = turn.get("speaker", "Unknown")
            snippet = turn.get("content", "")[:120].strip()
            summary = f"[{speaker}]: {snippet}..."
            if summary not in self.condensed_episodic_log:
                self.condensed_episodic_log.append(summary)

        # Cap condensed episodic log to avoid indefinite growth
        if len(self.condensed_episodic_log) > 20:
            self.condensed_episodic_log = self.condensed_episodic_log[-20:]

        return active_window

    def get_condensed_context(self) -> str:
        """Returns condensed episodic memory string to inject into prompt headers."""
        if not self.condensed_episodic_log:
            return ""
        return "Recent Historical Context:\n" + "\n".join(f"- {entry}" for entry in self.condensed_episodic_log)
