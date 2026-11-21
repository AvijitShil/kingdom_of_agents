"""
DeepSeek Harness Base Adapter for EON Society Simulation
Interfaces agents, plugins, and mutation candidates with the local Gemma 4 OpenVINO engine.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional

DEFAULT_API_BASE = "http://127.0.0.1:8000/v1"


class DeepSeekHarnessAdapter:
    """
    Adapter adhering to the DeepSeek Harness modular architecture.
    Connects society agents to the local frozen Gemma 4 OpenVINO server.
    """

    def __init__(self, api_base: str = DEFAULT_API_BASE, model_name: str = "gemma-4-e4b"):
        self.api_base = api_base
        self.model_name = model_name
        self.active_plugins = {}
        self.mutation_history = []

    def check_health(self) -> bool:
        try:
            resp = requests.get(f"{self.api_base.replace('/v1', '')}/health", timeout=3)
            return resp.status_code == 200 and resp.json().get("loaded", False)
        except Exception:
            return False

    def query(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Query the frozen Gemma 4 model with optional tool schemas in the harness prompt."""
        formatted_messages = list(messages)

        # If tools are provided, inject tool schema into the system prompt (DeepSeek harness pattern)
        if tools:
            tool_desc = json.dumps(tools, indent=2)
            tool_prompt = (
                f"\nYou have access to the following executable tools:\n```json\n{tool_desc}\n```\n"
                "To invoke a tool, output a JSON block: ```json\n{\"tool\": \"name\", \"args\": {...}}\n```"
            )
            if formatted_messages and formatted_messages[0]["role"] == "system":
                formatted_messages[0]["content"] += tool_prompt
            else:
                formatted_messages.insert(0, {"role": "system", "content": tool_prompt})

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        resp = requests.post(
            f"{self.api_base}/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Harness query failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def register_plugin(self, name: str, plugin_callable: Any):
        self.active_plugins[name] = plugin_callable

    def record_mutation(self, mutation_id: str, diff_description: str, performance_delta: float):
        self.mutation_history.append({
            "id": mutation_id,
            "diff": diff_description,
            "delta": performance_delta
        })
