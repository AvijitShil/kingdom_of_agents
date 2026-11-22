import pytest
from society.kinship import Household, KinshipRegistry, CitizenStatus


def test_household_initialization_and_living_standard():
    h = Household(
        agent_id="scholar-01",
        agent_name="Prometheus",
        clan_id="clan_alpha_technocrats",
        spouse_name="Pyrrha",
        num_children=2,
        water_cistern_reserve=80.0,
        grain_ration_reserve=60.0,
    )
    assert h.total_dependents == 4
    score = h.calculate_living_standard(clan_water_per_capita=15.0, clan_food_per_capita=10.0)
    assert score > 0.8
    assert h.status == CitizenStatus.CIVILIAN


def test_outlaw_defection_on_starvation():
    h = Household(
        agent_id="trader-01",
        agent_name="Mercator",
        clan_id="clan_beta_merchants",
        water_cistern_reserve=0.0,
        grain_ration_reserve=0.0,
    )
    # Drain 1
    h.consume_daily_rations()
    assert h.consecutive_starvation_ticks == 1
    assert h.status == CitizenStatus.DISCONTENT

    # Drain 2 -> Outlaw
    h.consume_daily_rations()
    assert h.consecutive_starvation_ticks == 2
    assert h.status == CitizenStatus.OUTLAW
    assert "Bandits" in h.bandit_camp

    # Outlaw raid
    h.raid_caravan("clan_alpha_technocrats", loot_water=50.0, loot_grain=40.0)
    assert h.water_cistern_reserve == 50.0
    assert h.grain_ration_reserve == 40.0


def test_kinship_registry_persistence(tmp_path):
    registry = KinshipRegistry()
    assert len(registry.households) >= 4
    
    save_file = str(tmp_path / "kinship_state.json")
    registry.save_state(save_file)

    new_registry = KinshipRegistry()
    new_registry.households.clear()
    assert len(new_registry.households) == 0

    loaded = new_registry.load_state(save_file)
    assert loaded is True
    assert len(new_registry.households) >= 4
    p = new_registry.get_household("scholar-01")
    assert p.agent_name == "Prometheus"
    assert p.spouse_name == "Pyrrha"
