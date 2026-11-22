import pytest
from harness.memory_guard import MemoryGuard


def test_memory_guard_truncation():
    guard = MemoryGuard(max_rolling_turns=6)
    turns = [
        {"speaker": f"Agent_{i}", "content": f"Turn {i} message regarding water and grain resources."}
        for i in range(10)
    ]
    active = guard.truncate_history(turns)
    assert len(active) == 6
    assert active[0]["speaker"] == "Agent_4"
    assert active[-1]["speaker"] == "Agent_9"

    # Verify condensed episodic context contains evicted turns
    condensed = guard.get_condensed_context()
    assert "Recent Historical Context:" in condensed
    assert "Agent_0" in condensed
    assert "Agent_3" in condensed


def test_memory_guard_no_overflow():
    guard = MemoryGuard(max_rolling_turns=6)
    turns = [
        {"speaker": f"Agent_{i}", "content": f"Turn {i} content"}
        for i in range(4)
    ]
    active = guard.truncate_history(turns)
    assert len(active) == 4
    assert guard.get_condensed_context() == ""
