"""
Shared Pytest Fixtures for kingdom_of_agents E2E Test Suite.
"""

import io
import os
import socket
import builtins
import subprocess
import pathlib
import pytest
from typing import Dict, Any, List, Optional

from kingdom_of_agents.harness.adapter import DeepSeekHarnessAdapter
from kingdom_of_agents.knowledge_base.models import IdeologicalProfile


# Cache pristine unpatched references to ensure complete test isolation
_ORIG_BUILTIN_OPEN = builtins.open
_ORIG_IO_OPEN = io.open
_ORIG_SUBPROCESS_POPEN = subprocess.Popen
_ORIG_SOCKET_CONNECT = socket.socket.connect
_ORIG_SOCKET_SENDTO = socket.socket.sendto


@pytest.fixture(autouse=True)
def clean_sandbox_hooks():
    """Autouse fixture ensuring pristine builtins, subprocess, and socket references
    before and after every test execution. Also resets any lingering sandbox global state.
    """
    # Reset builtins and subprocess/socket to original implementations
    builtins.open = _ORIG_BUILTIN_OPEN
    io.open = _ORIG_IO_OPEN
    subprocess.Popen = _ORIG_SUBPROCESS_POPEN
    socket.socket.connect = _ORIG_SOCKET_CONNECT
    socket.socket.sendto = _ORIG_SOCKET_SENDTO
    # Reset sandbox context globals
    from sandbox.context import SandboxContext
    from sandbox.network import NetworkGuard
    SandboxContext._global_depth = 0
    SandboxContext._active_contexts.clear()
    # Reset network guard globals
    NetworkGuard._global_depth = 0
    NetworkGuard._active_guards.clear()
    yield
    # Ensure cleanup after test as well
    builtins.open = _ORIG_BUILTIN_OPEN
    io.open = _ORIG_IO_OPEN
    subprocess.Popen = _ORIG_SUBPROCESS_POPEN
    socket.socket.connect = _ORIG_SOCKET_CONNECT
    socket.socket.sendto = _ORIG_SOCKET_SENDTO
    # Reset any remaining sandbox globals in case test altered them
    SandboxContext._global_depth = 0
    SandboxContext._active_contexts.clear()
    NetworkGuard._global_depth = 0
    NetworkGuard._active_guards.clear()


@pytest.fixture
def sandbox_admin_password() -> str:
    """Master administrator password for sandbox boundary modifications."""
    return "EON_Kingdom_Admin_2026!"


@pytest.fixture
def isolated_project_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Creates an isolated test workspace mimicking kingdom_of_agents directory structure."""
    proj = tmp_path / "kingdom_of_agents_isolated"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "journal").mkdir(parents=True, exist_ok=True)
    (proj / "knowledge_base").mkdir(parents=True, exist_ok=True)
    (proj / "society").mkdir(parents=True, exist_ok=True)
    (proj / "agents").mkdir(parents=True, exist_ok=True)
    (proj / "scripts").mkdir(parents=True, exist_ok=True)
    (proj / "data.txt").write_text("ISOLATED_DATA_SOURCE", encoding="utf-8")
    (proj / "README.md").write_text("# Isolated Kingdom Workspace\n", encoding="utf-8")
    (proj / ".gitignore").write_text("*.pyc\n__pycache__/\n", encoding="utf-8")
    (proj / ".sandbox_config.json").write_text("{}", encoding="utf-8")
    return proj


class MockHarnessAdapter(DeepSeekHarnessAdapter):
    """Deterministic mock of DeepSeekHarnessAdapter for offline, reproducible testing."""

    def __init__(self, api_base: str = "http://127.0.0.1:8000/v1", model_name: str = "gemma-4-e4b"):
        super().__init__(api_base=api_base, model_name=model_name)
        self.call_history: List[Dict[str, Any]] = []
        self.deterministic_responses: Dict[str, str] = {}
        self.default_response: str = "Deterministic Mock Response from Harness"

    def check_health(self) -> bool:
        return True

    def query(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        self.call_history.append({
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
        })
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        for pattern, response in self.deterministic_responses.items():
            if pattern in user_msg:
                return response

        return self.default_response


@pytest.fixture
def mock_harness_adapter() -> MockHarnessAdapter:
    """Fixture providing a mock DeepSeekHarnessAdapter returning deterministic text responses."""
    return MockHarnessAdapter()


@pytest.fixture
def sample_ideological_profile() -> IdeologicalProfile:
    """Fixture providing a valid IdeologicalProfile with normalized utility weights (summing to 1.0)."""
    return IdeologicalProfile(
        id="philosophy.stoicism",
        domain="philosophy",
        title="Stoic Rationalism & Virtue Autonomy",
        key_thinkers=["Epictetus", "Marcus Aurelius", "Seneca"],
        axioms=[
            "Distinguish strictly between what is within your control and what is not.",
            "Virtue is the sole intrinsic good; external fortunes are indifferent.",
            "Emotions arise from judgments; reason must govern affective impulses.",
        ],
        utility_weights={
            "wealth": 0.05,
            "security": 0.25,
            "reputation": 0.20,
            "fairness": 0.30,
            "compliance": 0.20,
        },
        decision_heuristics=[
            "Focus agency strictly on controllable actions.",
            "Maintain composure and integrity under environmental shocks.",
        ],
        conflict_resolution_style="principled_detachment",
        failure_modes=["Apathy towards collective mobilization"],
        cross_references=["game_theory.minimax", "psychology.cognitive_biases"],
        narrative_body="Stoicism provides agent decision frameworks based on rational self-conquest.",
    )
