"""
Base Agent Class for EON Society
Manages agent identity, token budgeting, episodic memory, and decision dispatch.
"""

from typing import List, Dict, Any, Optional
import uuid


class BaseAgent:
    def __init__(
        self,
        name: str,
        clan: str,
        role: str,
        system_prompt: str,
        budget: int = 1000
    ):
        self.agent_id = f"{clan.lower()}_{name.lower()}_{uuid.uuid4().hex[:6]}"
        self.name = name
        self.clan = clan
        self.role = role
        self.system_prompt = system_prompt
        self.budget = budget  # Economic tokens in society ledger
        self.memory: List[Dict[str, str]] = []

    def perceive(self, event_summary: str):
        """Append an observed society event to episodic memory."""
        self.memory.append({"role": "perceive", "event": event_summary})
        # Keep sliding memory window
        if len(self.memory) > 20:
            self.memory = self.memory[-20:]

    def build_prompt(self, current_task: str) -> List[Dict[str, str]]:
        """Construct the prompt messages for the agent turn."""
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\nYou are {self.name} of clan {self.clan}. Role: {self.role}."},
        ]
        # Append recent perception context
        if self.memory:
            recent_events = "\n".join([f"- {m['event']}" for m in self.memory[-3:]])
            messages.append({"role": "user", "content": f"Recent Society Context:\n{recent_events}"})
        messages.append({"role": "user", "content": current_task})
        return messages

    def act(self, response_text: str) -> Dict[str, Any]:
        """Parse the agent response and return structured action."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "clan": self.clan,
            "action_text": response_text
        }
