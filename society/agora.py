"""
EON Society Agora (Town Square Group Chat Medium)
Provides persistent, multi-turn conversational infrastructure where agents converse,
debate, trade, dispute, and strategize with explicit @mentions and private Chains of Thought (CoT).
"""

import os
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class AgoraMessage:
    """Represents a single utterance in the Agora town square."""
    sender: str
    clan: str
    target: str  # e.g. "@all", "@ClanBeta", "@Trader-01"
    chain_of_thought: str  # Private internal reasoning
    public_message: str  # Spoken utterance in the town square
    intent: str  # PROPOSAL, COUNTER_OFFER, THREAT, PETITION, ACCORD, DISPUTE, DISPATCH
    codebook_reference: Optional[str] = None  # Specific philosophy/game-theory paper cited
    tick: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgoraChannel:
    """Manages the Town Square chat channel for a simulation day."""

    def __init__(self, day: int = 1):
        self.day = day
        self.messages: List[AgoraMessage] = []

    def post(self, msg: AgoraMessage) -> None:
        """Post a new message to the Agora channel."""
        self.messages.append(msg)

    def get_recent_messages(self, limit: int = 8) -> List[AgoraMessage]:
        """Return the most recent messages."""
        return self.messages[-limit:] if self.messages else []

    def get_context_for_agent(self, agent_name: str, clan: str, limit: int = 6) -> str:
        """Format recent dialogue for an agent prompt, highlighting relevant mentions."""
        recent = self.get_recent_messages(limit)
        if not recent:
            return "The Agora is currently quiet. No public utterances have been made yet today."

        lines = []
        for m in recent:
            mention_tag = ""
            if f"@{agent_name}" in m.target or f"@{clan}" in m.target:
                mention_tag = " [DIRECTED TO YOU / YOUR CLAN]"
            elif "@all" in m.target:
                mention_tag = " [BROADCAST TO ALL]"

            ref_tag = f" (Invoking: {m.codebook_reference})" if m.codebook_reference else ""
            lines.append(f"[{m.clan}] {m.sender} -> {m.target}{mention_tag}{ref_tag}:\n\"{m.public_message}\"")
        return "\n\n".join(lines)

    def export_markdown_transcript(self, filepath: str) -> None:
        """Export the complete town square conversation into a clean Markdown transcript."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        md_lines = [
            f"# Agora Group Chat Transcript: Day {self.day:02d} — {date_str}",
            "",
            "> Official public record of Town Square proceedings, diplomatic exchanges, and leaked deliberations.",
            "",
            "---",
            "",
        ]

        for idx, m in enumerate(self.messages, 1):
            ref_str = f" | *Survival Codebook Reference: `{m.codebook_reference}`*" if m.codebook_reference else ""
            md_lines.extend([
                f"### Exchange #{idx:02d}: {m.sender} ({m.clan}) -> {m.target}",
                f"- **Intent**: `{m.intent}`{ref_str}",
                f"- **Timestamp**: `{m.timestamp}`",
                "",
                "<details>",
                f"<summary>🧠 <em>Leaked Chain of Thought (Private Deliberation)</em></summary>",
                "",
                f"> {m.chain_of_thought.strip()}",
                "",
                "</details>",
                "",
                f"**Public Utterance**:",
                f"> \"{m.public_message.strip()}\"",
                "",
                "---",
                "",
            ])

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    def export_jsonl(self, filepath: str) -> None:
        """Export the conversation as machine-readable JSON Lines."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            for m in self.messages:
                f.write(json.dumps(m.to_dict()) + "\n")
