"""
Tests for Clan Collective Survival Pools and Metabolic Scarcity
"""

import pytest
from society.survival import ClanSurvivalPool, MetabolicEngine, SurvivalStatus


def test_clan_survival_pool_metabolism():
    pool = ClanSurvivalPool(
        clan_name="clan_test",
        display_title="Clan Test",
        energy_reserve=100.0,
        ration_reserve=100.0,
        max_energy=200.0,
        max_rations=200.0,
        headcount=2,
        daily_energy_burn_rate=10.0,
        daily_ration_burn_rate=10.0,
    )
    assert pool.status == SurvivalStatus.STABLE
    report = pool.burn_metabolism()
    assert report["energy_consumed"] == 20.0
    assert report["rations_consumed"] == 20.0
    assert pool.energy_reserve == 80.0
    assert pool.ration_reserve == 80.0

    # Replenish
    pool.replenish(energy=50.0, rations=30.0)
    assert pool.energy_reserve == 130.0
    assert pool.ration_reserve == 110.0


def test_survival_status_transitions():
    pool = ClanSurvivalPool(
        clan_name="clan_crisis",
        display_title="Clan Crisis",
        energy_reserve=20.0,
        ration_reserve=20.0,
        max_energy=200.0,
        max_rations=200.0,
        headcount=1,
    )
    # 20/200 = 10% vitality -> STARVATION_CRISIS
    assert pool.status == SurvivalStatus.STARVATION_CRISIS

    # Burn remaining
    pool.burn_metabolism()
    pool.energy_reserve = 0
    pool.ration_reserve = 0
    assert pool.status == SurvivalStatus.COLLAPSED


def test_metabolic_engine_operations():
    engine = MetabolicEngine()
    summary = engine.get_society_survival_summary()
    assert "clan_alpha_technocrats" in summary
    assert "clan_beta_merchants" in summary
    assert "clan_gamma_jurists" in summary

    drain_report = engine.execute_daily_drain()
    assert len(drain_report) == 3
