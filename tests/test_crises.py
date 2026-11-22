import pytest
from society.crises import CrisisManager, CRISIS_CURRICULUM


def test_crises_curriculum_coverage():
    # Day 1 through 10 have explicit curriculum entries
    for day in range(1, 11):
        crisis = CrisisManager.get_crisis_for_day(day)
        assert crisis.day_number == day
        assert len(crisis.title) > 0
        assert len(crisis.recommended_kb_topics) > 0
        assert crisis.water_impact_pct <= 0.0
        assert crisis.ration_impact_pct <= 0.0


def test_crisis_day_4_summer_drought():
    crisis = CrisisManager.get_crisis_for_day(4)
    assert "Drought" in crisis.title
    assert crisis.water_impact_pct == -0.50
    assert "nash_equilibrium" in crisis.recommended_kb_topics


def test_procedural_crises_beyond_day_10():
    crisis_15 = CrisisManager.get_crisis_for_day(15)
    assert crisis_15.day_number == 15
    assert "Resurgent" in crisis_15.title
    assert crisis_15.water_impact_pct < 0 or crisis_15.ration_impact_pct < 0
