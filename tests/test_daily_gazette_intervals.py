"""
tests/test_daily_gazette_intervals.py
EON 2.0 â€” Tests for 6-hour interval simulation cycles, Chronos logging,
and daily gazette archive generation by date.
"""

import os
import pytest
from society.simulation_engine import CivilizationalSimulator, INTERVAL_METADATA


def test_four_intervals_configured():
    """Verify exactly 4 six-hour intervals configured for each simulated day."""
    assert len(INTERVAL_METADATA) == 4
    codes = [m["code"] for m in INTERVAL_METADATA]
    assert codes == ["06_00_dawn", "12_00_midday", "18_00_dusk", "24_00_midnight"]


def test_civilizational_simulator_run_interval(tmp_path):
    """Running an interval produces a valid bulletin with themed events."""
    sim = CivilizationalSimulator(repo_root=str(tmp_path))
    # Run interval 0 (Dawn)
    res_dawn = sim.run_interval(sim_day=1, sim_date="2026-11-22", interval_idx=0)
    assert res_dawn["interval_idx"] == 0
    assert "Dawn Edition" in res_dawn["bulletin_text"]
    assert "Metabolic cycle complete" in res_dawn["bulletin_text"]


def test_civilizational_simulator_run_full_day_cycle(tmp_path):
    """Running full day creates 4 interval dispatches and consolidated gazette in daily gazette/."""
    sim = CivilizationalSimulator(repo_root=str(tmp_path))
    day = 7
    sim_date = "2026-11-28"

    result = sim.run_full_day_cycle(sim_day=day, sim_date=sim_date)
    assert len(result["intervals"]) == 4

    # Verify daily gazette directory structure
    daily_gazette_dir = tmp_path / "daily gazette" / sim_date
    assert daily_gazette_dir.exists()

    expected_files = [
        "06_00_dawn.md",
        "12_00_midday.md",
        "18_00_dusk.md",
        "24_00_midnight.md",
        "gazette_full.md",
    ]
    for fname in expected_files:
        fpath = daily_gazette_dir / fname
        assert fpath.exists(), f"Missing {fname} in {daily_gazette_dir}"
        assert fpath.stat().st_size > 0

    # Verify consolidated root gazette
    consolidated = tmp_path / "daily gazette" / f"{sim_date}.md"
    assert consolidated.exists()
    assert "THE EON CIVILIZATION GAZETTE" in consolidated.read_text(encoding="utf-8")


def test_mirrored_daily_gazette_structure(tmp_path):
    """Ensure daily_gazette (no space) mirror is also populated identically."""
    sim = CivilizationalSimulator(repo_root=str(tmp_path))
    day = 8
    sim_date = "2026-11-29"

    sim.run_full_day_cycle(sim_day=day, sim_date=sim_date)

    mirrored_dir = tmp_path / "daily_gazette" / sim_date
    assert mirrored_dir.exists()
    assert (mirrored_dir / "06_00_dawn.md").exists()
    assert (mirrored_dir / "12_00_midday.md").exists()
    assert (mirrored_dir / "18_00_dusk.md").exists()
    assert (mirrored_dir / "24_00_midnight.md").exists()
    assert (tmp_path / "daily_gazette" / f"{sim_date}.md").exists()
