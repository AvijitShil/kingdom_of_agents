"""
tests/test_reproduction_inheritance.py
EON 2.0 — Tests for survival states, Greek naming, reproduction, and parental education.
"""

import pytest
from society.economy import SocietyLedger
from society.survival import (
    SurvivalState, SurvivalEngine, AgentSurvivalProfile,
    DAILY_UPKEEP, FOOD_COST, WATER_COST, SHELTER_COST, HEALTHCARE_COST,
)
from society.kinship import (
    GreekNamingRegistry, ReproductionController, ParentalEducation,
    GREEK_NAME_POOL,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_ledger(agent: str, balance: int) -> SocietyLedger:
    """Create a minimal ledger with one agent and a survival_pool sink."""
    ledger = SocietyLedger()
    ledger.balances[agent] = balance
    ledger.balances["survival_pool"] = 0
    return ledger


# ──────────────────────────────────────────────────────────────────────────────
# Test 1 — Daily birth cap ≤ 10
# ──────────────────────────────────────────────────────────────────────────────

def test_daily_birth_cap():
    """After MAX_DAILY_BIRTHS births, can_reproduce returns False."""
    ctrl = ReproductionController()
    naming = GreekNamingRegistry()
    high_balance = ReproductionController.MIN_REPRODUCTION_BALANCE + 100

    # Register exactly MAX births
    for _ in range(ReproductionController.MAX_DAILY_BIRTHS):
        assert ctrl.can_reproduce(high_balance, high_balance)
        name = naming.generate_child_name("ParentA", "ParentB")
        ctrl.register_birth(name, "ParentA", "ParentB", day=1)

    assert ctrl.global_daily_births == ReproductionController.MAX_DAILY_BIRTHS
    # Cap reached — reproduction blocked
    assert not ctrl.can_reproduce(high_balance, high_balance)

    # After reset, can reproduce again
    ctrl.reset_daily_counter()
    assert ctrl.global_daily_births == 0
    assert ctrl.can_reproduce(high_balance, high_balance)


# ──────────────────────────────────────────────────────────────────────────────
# Test 2 — Greek name uniqueness
# ──────────────────────────────────────────────────────────────────────────────

def test_greek_name_uniqueness():
    """Every generated name must be unique across many calls."""
    registry = GreekNamingRegistry()
    generated = set()

    # Generate more names than the pool to exercise fallback variants
    num_names = len(GREEK_NAME_POOL) + 10
    for _ in range(num_names):
        name = registry.generate_child_name("Alpha", "Beta")
        assert name not in generated, f"Duplicate name generated: {name}"
        generated.add(name)

    assert len(generated) == num_names


# ──────────────────────────────────────────────────────────────────────────────
# Test 3 — Cannot reproduce if balance < 28
# ──────────────────────────────────────────────────────────────────────────────

def test_cannot_reproduce_below_min_balance():
    """can_reproduce is False when either parent is below MIN_REPRODUCTION_BALANCE."""
    ctrl = ReproductionController()
    min_bal = ReproductionController.MIN_REPRODUCTION_BALANCE  # 28
    high = min_bal + 10
    low = min_bal - 1

    assert not ctrl.can_reproduce(low, high), "parent1 below min should block"
    assert not ctrl.can_reproduce(high, low), "parent2 below min should block"
    assert not ctrl.can_reproduce(low, low), "both below min should block"
    assert ctrl.can_reproduce(high, high), "both at/above min should allow"
    assert ctrl.can_reproduce(min_bal, min_bal), "exactly at min should allow"


# ──────────────────────────────────────────────────────────────────────────────
# Test 4 — Parental education transfer
# ──────────────────────────────────────────────────────────────────────────────

def test_parental_education_transfer():
    """transfer_knowledge returns dict with child, inherited_traits, day."""
    edu = ParentalEducation()
    traits = ["agriculture", "philosophy", "trade", "metallurgy"]
    result = edu.transfer_knowledge("Prometheus", "Achilles", traits, day=5)

    assert result["child"] == "Achilles"
    assert result["day"] == 5
    assert isinstance(result["inherited_traits"], list)
    # Same number of traits (mutations modify, not drop)
    assert len(result["inherited_traits"]) == len(traits)


# ──────────────────────────────────────────────────────────────────────────────
# Test 5 — Trait mutation CAN happen (10% chance per trait)
# ──────────────────────────────────────────────────────────────────────────────

def test_trait_mutation_can_happen():
    """
    Over many calls with many traits, at least one mutation must occur.
    (Statistical: probability of zero mutations across 500 trait-transfers ≈ 0.9^500 ≈ 1e-23)
    """
    edu = ParentalEducation()
    traits = ["agriculture"] * 10  # 10 traits each call

    found_mutation = False
    for _ in range(50):  # 500 total trait-transfer attempts
        result = edu.transfer_knowledge("Prometheus", "Achilles", traits, day=1)
        for orig, inherited in zip(traits, result["inherited_traits"]):
            if orig != inherited:
                found_mutation = True
                break
        if found_mutation:
            break

    assert found_mutation, "Expected at least one trait mutation in 500 attempts"


# ──────────────────────────────────────────────────────────────────────────────
# Test 6 — Survival state transitions (SECURE→WARNING→DEPRIVED→CRITICAL→DECEASED)
# ──────────────────────────────────────────────────────────────────────────────

def test_survival_state_transitions():
    """AgentSurvivalProfile.evaluate_state maps balance ranges correctly."""
    profile = AgentSurvivalProfile(name="TestAgent")

    # SECURE: balance > 3 * 14 = 42
    assert profile.evaluate_state(43) == SurvivalState.SECURE
    assert profile.evaluate_state(100) == SurvivalState.SECURE

    # WARNING: 14 <= balance <= 42
    assert profile.evaluate_state(42) == SurvivalState.WARNING
    assert profile.evaluate_state(14) == SurvivalState.WARNING

    # DEPRIVED: 7 <= balance < 14
    assert profile.evaluate_state(13) == SurvivalState.DEPRIVED
    assert profile.evaluate_state(7) == SurvivalState.DEPRIVED

    # CRITICAL: balance < 7
    assert profile.evaluate_state(6) == SurvivalState.CRITICAL
    assert profile.evaluate_state(0) == SurvivalState.CRITICAL

    # Once DECEASED, always DECEASED
    profile.state = SurvivalState.DECEASED
    assert profile.evaluate_state(10000) == SurvivalState.DECEASED


# ──────────────────────────────────────────────────────────────────────────────
# Test 7 — Daily upkeep deducts correct token amounts
# ──────────────────────────────────────────────────────────────────────────────

def test_daily_upkeep_deducts_correct_amounts():
    """
    An agent with ample balance should pay food+water+shelter+healthcare = 14.
    """
    agent = "TestAgent"
    starting_balance = 100
    ledger = _make_ledger(agent, starting_balance)

    profile = AgentSurvivalProfile(name=agent)
    result = profile.pay_daily_upkeep(ledger, day=1)

    assert result["success"] is True
    assert result["shortfall"] == 0
    assert result["costs_paid"]["food"] == FOOD_COST        # 5
    assert result["costs_paid"]["water"] == WATER_COST      # 4
    assert result["costs_paid"]["shelter"] == SHELTER_COST  # 3
    assert result["costs_paid"]["healthcare"] == HEALTHCARE_COST  # 2

    total_paid = sum(result["costs_paid"].values())
    assert total_paid == DAILY_UPKEEP  # 14
    assert ledger.balances[agent] == starting_balance - DAILY_UPKEEP


# ──────────────────────────────────────────────────────────────────────────────
# Test 8 — Deceased agent stays DECEASED
# ──────────────────────────────────────────────────────────────────────────────

def test_deceased_agent_stays_deceased():
    """
    After an agent reaches DECEASED state, further upkeep calls leave it DECEASED
    and no tokens are transferred.
    """
    agent = "GhostAgent"
    ledger = _make_ledger(agent, 1000)

    profile = AgentSurvivalProfile(name=agent)
    # Force DECEASED directly
    profile.state = SurvivalState.DECEASED

    before_balance = ledger.balances[agent]
    result = profile.pay_daily_upkeep(ledger, day=10)

    assert result["state"] == SurvivalState.DECEASED
    assert result["success"] is False
    assert result["costs_paid"] == {}
    # Balance must be untouched
    assert ledger.balances[agent] == before_balance

    # Also via SurvivalEngine.run_daily_upkeep
    engine = SurvivalEngine()
    engine.profiles[agent] = profile
    report = engine.run_daily_upkeep(ledger, day=11)

    assert agent in report["deceased"]
    assert agent not in report["alive"]
    assert ledger.balances[agent] == before_balance
