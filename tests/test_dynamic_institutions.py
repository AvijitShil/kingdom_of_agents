"""
tests/test_dynamic_institutions.py
EON 2.0 â€” Tests for dynamic institutions, armies, kingdoms, and organic fission.
"""

import os
import pytest
from society.institutions import (
    Institution, ArmyInstitution, InstitutionRegistry, InstitutionType, InstitutionStatus,
)
from society.sovereignty import KingdomFormationEngine, SocioEconomicFissionTrigger


def test_institution_creation_and_registration():
    """Verify an institution can be created, registered, and retrieved."""
    registry = InstitutionRegistry()
    inst = registry.create_institution(
        name="Agora Grain Exchange",
        institution_type=InstitutionType.Business,
        owner="Hermes",
        treasury_account="Hermes",
        treasury_balance=250.0,
        founded_day=1,
    )
    assert inst.institution_id.startswith("inst_")
    assert inst.name == "Agora Grain Exchange"
    assert inst.status == InstitutionStatus.Active
    assert registry.get(inst.institution_id) is inst
    assert inst in registry.list_active()


def test_army_recruitment_pays_signing_bonus():
    """Recruitment of a soldier deducts 10 tokens from treasury."""
    registry = InstitutionRegistry()
    army = registry.create_army(
        name="Phalanx of Athena",
        owner="Athena",
        treasury_account="Athena",
        treasury_balance=50.0,
        founded_day=1,
    )
    assert army.treasury_balance == 50.0

    # Recruit soldier
    ok = army.recruit("Lysander")
    assert ok is True
    assert "Lysander" in army.soldiers
    assert army.treasury_balance == 40.0  # 50 - 10


def test_army_recruitment_fails_without_funds():
    """Recruitment fails when treasury cannot cover 10-token signing bonus."""
    registry = InstitutionRegistry()
    army = registry.create_army(
        name="Militia of Thebes",
        owner="Themis",
        treasury_account="Themis",
        treasury_balance=5.0,  # less than 10
        founded_day=1,
    )
    ok = army.recruit("Nikias")
    assert ok is False
    assert "Nikias" not in army.soldiers
    assert army.treasury_balance == 5.0


def test_army_wages_and_desertion():
    """Soldiers desert when the treasury cannot pay daily wages."""
    registry = InstitutionRegistry()
    army = registry.create_army(
        name="Spartan Vanguard",
        owner="Prometheus",
        treasury_account="Prometheus",
        treasury_balance=3.0,  # can pay only 1 soldier (3 tokens)
        founded_day=1,
    )
    # Manually populate soldiers
    army.soldiers = ["Soldier1", "Soldier2"]
    army.members = ["Soldier1", "Soldier2"]

    deserters = army.pay_wages()
    assert "Soldier2" in deserters
    assert "Soldier1" in army.soldiers
    assert "Soldier2" not in army.soldiers
    assert army.treasury_balance == 0.0


def test_army_conflict_resolution():
    """Simulate conflict between two armies and verify output structure."""
    registry = InstitutionRegistry()
    army1 = registry.create_army("Army of Athens", "Athena", "Athena", 100.0, 1, morale=0.9)
    army1.soldiers = ["A1", "A2", "A3", "A4", "A5"]

    army2 = registry.create_army("Army of Sparta", "Lysander", "Lysander", 100.0, 1, morale=0.8)
    army2.soldiers = ["S1", "S2"]

    result = army1.simulate_conflict(army2)
    assert "winner" in result
    assert "casualties" in result
    assert result["casualties"] >= 1
    assert "outcome" in result
    assert result["winner"] in [army1.name, army2.name]


def test_institution_dissolution():
    """Dissolving an institution sets its status to Dissolved and removes from active list."""
    registry = InstitutionRegistry()
    inst = registry.create_institution("Wager Hall", InstitutionType.WageringHall, "Midas", "Midas", 100.0, 1)
    assert inst in registry.list_active()

    ok = registry.dissolve(inst.institution_id)
    assert ok is True
    assert inst.status == InstitutionStatus.Dissolved
    assert inst not in registry.list_active()


def test_kingdom_formation_engine():
    """Autonomous kingdom declaration, membership changes, and succession."""
    engine = KingdomFormationEngine()
    kid = engine.declare_kingdom(
        name="Kingdom of Attica",
        ruler="Solon",
        founding_members=["Solon", "Athena", "Hermes"],
        treasury_account="Attica_Treasury",
        day=2,
    )
    assert kid.startswith(("kgm_", "kingdom_"))
    k = engine.get_kingdom(kid)
    assert k["name"] == "Kingdom of Attica"
    assert k["ruler"] == "Solon"
    assert len(k["members"]) == 3

    # Add & remove member
    assert engine.add_member(kid, "Dione") is True
    assert "Dione" in engine.get_kingdom(kid)["members"]
    assert engine.remove_member(kid, "Dione") is True
    assert "Dione" not in engine.get_kingdom(kid)["members"]

    # Succession
    assert engine.set_ruler(kid, "Athena") is True
    assert engine.get_kingdom(kid)["ruler"] == "Athena"


def test_fission_evaluation():
    """Full fission evaluation with multiple socio-economic triggers."""
    trigger = SocioEconomicFissionTrigger()

    # Stable clan
    equal_bals = {"A": 500, "B": 500, "C": 500}
    res_stable = trigger.evaluate_fission("clan_stable", equal_bals, dispute_count=1, petitioners=[])
    assert res_stable["should_fission"] is False
    assert len(res_stable["triggers"]) == 0

    # Unstable clan with Gini and dispute triggers
    unequal_bals = {"A": 10, "B": 20, "C": 5000}
    res_unstable = trigger.evaluate_fission("clan_unstable", unequal_bals, dispute_count=6, petitioners=["A"])
    assert res_unstable["should_fission"] is True
    assert "gini_inequality" in res_unstable["triggers"]
    assert "dispute_accumulation" in res_unstable["triggers"]
