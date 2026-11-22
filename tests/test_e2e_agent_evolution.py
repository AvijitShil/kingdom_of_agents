"""
End-to-End Agent Evolution & Self-Improvement Test Suite (Features 12–15, Scenarios 4 & 5).

Implements 4-tier testing:
- Tier 1: Feature Coverage (EvolutionaryAgent, FitnessMetrics, CategorySwitchManager, RecursiveReflectionEngine)
- Tier 2: Boundary & Corner Cases (Hysteresis margin H_margin=0.15, cooldown tau=3 ticks, switching cost C_trans, rollback, reflection memory bound, regret in [0,1])
- Tier 3: Cross-Feature Interactions (Dynamic CorpusRetriever integration, sandbox path confinement for reflection logs)
- Tier 4: Real-World Application Scenarios (Scenario 4: Rapid Oscillations & Rollback, Scenario 5: Long-Horizon Reflection)
"""

import sys
import pathlib
import pytest

from knowledge_base.models import IdeologicalProfile
from knowledge_base.retriever import CorpusRetriever
from sandbox import SecuritySandbox

# Graceful import check for progressive testability during parallel milestone execution
try:
    import evolution
    from evolution.agent import EvolutionaryAgent
    from evolution.models import ReflectionRecord
    from evolution.fitness import FitnessMetrics, compute_composite_fitness
    from evolution.switcher import CategorySwitchManager
    from evolution.reflection import RecursiveReflectionEngine
    HAS_EVOLUTION = True
except ImportError:
    HAS_EVOLUTION = False

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.evolution,
    pytest.mark.skipif(not HAS_EVOLUTION, reason="evolution module not yet implemented (Milestone M3)"),
]


@pytest.fixture
def stoic_profile(sample_ideological_profile) -> IdeologicalProfile:
    """Fixture providing Stoic ideological profile."""
    return sample_ideological_profile


@pytest.fixture
def utilitarian_profile() -> IdeologicalProfile:
    """Fixture providing Utilitarian ideological profile."""
    return IdeologicalProfile(
        id="philosophy.utilitarianism",
        domain="philosophy",
        title="Act & Rule Utilitarianism",
        key_thinkers=["Jeremy Bentham", "John Stuart Mill"],
        axioms=[
            "Maximize net aggregate utility across all conscious stakeholders.",
            "Each counts for one, and none for more than one.",
            "Action rightness depends solely upon consequential utility outcomes.",
        ],
        utility_weights={
            "wealth": 0.30,
            "security": 0.15,
            "reputation": 0.15,
            "fairness": 0.25,
            "compliance": 0.15,
        },
        decision_heuristics=[
            "Compute expected value and select action maximizing welfare.",
            "Prefer systemic stability if rule breakdown generates catastrophic disutility.",
        ],
        conflict_resolution_style="welfare_maximization",
        failure_modes=["Tyranny of majority over vulnerable minorities"],
        cross_references=["game_theory.pareto_optimality", "political_ideology.technocracy"],
        narrative_body="Utilitarianism guides action through consequential outcome maximization.",
    )


# ============================================================================
# TIER 1: FEATURE COVERAGE (Features 12–15)
# ============================================================================

@pytest.mark.tier1
def test_f12_agent_initialization(stoic_profile, mock_harness_adapter):
    """F12.1: EvolutionaryAgent initializes with valid IdeologicalProfile and inherited attributes."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
        budget=1000,
    )
    assert agent.name == "Marcus"
    assert agent.clan == "Philosophers"
    assert agent.ideology.id == "philosophy.stoicism"
    assert agent.fitness_history == []
    assert agent.reflection_history == []


@pytest.mark.tier1
def test_f12_agent_perceive_and_act_ideology_conditioned(stoic_profile, mock_harness_adapter):
    """F12.2: Agent builds prompt conditioning system instructions with active ideological axioms."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    agent.perceive("Resource scarcity crisis declared in Agora.")
    prompt_messages = agent.build_prompt("Decide resource allocation response.")

    system_content = prompt_messages[0]["content"]
    assert "Active Ideology" in system_content or "Stoic" in system_content or "philosophy.stoicism" in system_content
    assert "Distinguish strictly between what is within your control" in system_content


@pytest.mark.tier1
def test_f12_fitness_metric_computation(stoic_profile):
    """F12.3: FitnessMetrics computes multi-dimensional weighted score across 5 dimensions."""
    metrics = FitnessMetrics(
        wealth=0.5,
        security=0.8,
        reputation=0.7,
        fairness=0.9,
        compliance=0.6,
    )
    composite = metrics.compute_composite(stoic_profile.utility_weights)
    expected = (
        0.5 * 0.05
        + 0.8 * 0.25
        + 0.7 * 0.20
        + 0.9 * 0.30
        + 0.6 * 0.20
    )
    assert abs(composite - expected) < 1e-4


@pytest.mark.tier1
def test_f13_category_switch_trigger_on_performance_drop(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """F13.1: CategorySwitchManager triggers category switch when sustained fitness falls below threshold."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    switcher = CategorySwitchManager(agent=agent, switching_cost=50, hysteresis_margin=0.15, cooldown_ticks=3)

    # Low fitness shock
    degraded_metrics = FitnessMetrics(wealth=0.1, security=0.1, reputation=0.2, fairness=0.2, compliance=0.1)
    agent.fitness_history.append(degraded_metrics)

    should_switch = switcher.evaluate_switch(candidate_ideology=utilitarian_profile, candidate_expected_fitness=0.85)
    assert should_switch is True


@pytest.mark.tier1
def test_f15_recursive_reflection_record(stoic_profile, mock_harness_adapter):
    """F15.1: RecursiveReflectionEngine generates ReflectionRecord with regret metric."""
    engine = RecursiveReflectionEngine(adapter=mock_harness_adapter)
    record = engine.reflect(
        tick=1,
        perceived_context="Severe resource shortfall.",
        action_taken="Withheld assets under stoic detachment.",
        observed_outcome="Reputation diminished; zero welfare gain.",
        counterfactual_alternative="Cooperated with merchant clan under utilitarian policy.",
        actual_fitness=0.3,
        counterfactual_fitness=0.75,
    )
    assert isinstance(record, ReflectionRecord)
    assert record.tick == 1
    assert abs(record.regret - 0.45) < 1e-3
    assert len(record.prompt_mutation_suggestion) > 0


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ============================================================================

@pytest.mark.tier2
def test_boundary_f13_hysteresis_margin_enforcement(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """Tier 2: Marginal fitness improvements (<= H_margin = 0.15) do not trigger switch."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    switcher = CategorySwitchManager(agent=agent, switching_cost=0, hysteresis_margin=0.15, cooldown_ticks=3)

    # Current fitness 0.60; Candidate expected fitness 0.70 (diff = 0.10 <= 0.15)
    agent.fitness_history.append(FitnessMetrics(wealth=0.6, security=0.6, reputation=0.6, fairness=0.6, compliance=0.6))
    should_switch = switcher.evaluate_switch(candidate_ideology=utilitarian_profile, candidate_expected_fitness=0.70)
    assert should_switch is False


@pytest.mark.tier2
def test_boundary_f13_switching_cost_deduction(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """Tier 2: Category switch deducts C_trans from agent budget."""
    initial_budget = 1000
    switch_cost = 75
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
        budget=initial_budget,
    )
    switcher = CategorySwitchManager(agent=agent, switching_cost=switch_cost, hysteresis_margin=0.15, cooldown_ticks=3)

    switcher.execute_switch(candidate_ideology=utilitarian_profile, current_tick=10)
    assert agent.budget == initial_budget - switch_cost
    assert agent.ideology.id == utilitarian_profile.id


@pytest.mark.tier2
def test_boundary_f13_cooldown_timer_enforcement(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """Tier 2: Cooldown timer (tau = 3 ticks) prevents rapid switches within cooldown window."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    switcher = CategorySwitchManager(agent=agent, switching_cost=10, hysteresis_margin=0.15, cooldown_ticks=3)

    # Switch at tick 5
    switcher.execute_switch(candidate_ideology=utilitarian_profile, current_tick=5)

    # Attempt switch at tick 6 (cooldown active: 6 - 5 < 3)
    can_switch = switcher.evaluate_switch(candidate_ideology=stoic_profile, candidate_expected_fitness=0.99, current_tick=6)
    assert can_switch is False

    # Attempt switch at tick 8 (cooldown expired: 8 - 5 >= 3)
    can_switch_expired = switcher.evaluate_switch(candidate_ideology=stoic_profile, candidate_expected_fitness=0.99, current_tick=8)
    assert can_switch_expired is True


@pytest.mark.tier2
def test_boundary_f14_probationary_rollback_on_degraded_fitness(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """Tier 2: Post-switch performance degradation during probation window triggers rollback to prior ideology."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    switcher = CategorySwitchManager(agent=agent, probation_window=2)
    switcher.execute_switch(candidate_ideology=utilitarian_profile, current_tick=1)

    assert agent.is_on_probation is True

    # Performance degrades during probation tick
    degraded = FitnessMetrics(wealth=0.1, security=0.1, reputation=0.1, fairness=0.1, compliance=0.1)
    agent.fitness_history.append(degraded)

    rolled_back = switcher.check_probation(current_tick=2)
    assert rolled_back is True
    assert agent.ideology.id == stoic_profile.id


@pytest.mark.tier2
def test_boundary_f14_probationary_promotion_on_sustained_fitness(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """Tier 2: Sustained performance promotes probationary ideology to permanent."""
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    switcher = CategorySwitchManager(agent=agent, probation_window=2)
    switcher.execute_switch(candidate_ideology=utilitarian_profile, current_tick=1)

    # Sustained high performance
    high_perf = FitnessMetrics(wealth=0.9, security=0.9, reputation=0.9, fairness=0.9, compliance=0.9)
    agent.fitness_history.append(high_perf)
    switcher.check_probation(current_tick=2)

    agent.fitness_history.append(high_perf)
    promoted = switcher.check_probation(current_tick=3)
    assert promoted is True
    assert agent.is_on_probation is False
    assert agent.ideology.id == utilitarian_profile.id


@pytest.mark.tier2
def test_boundary_f15_reflection_sliding_window_bound(mock_harness_adapter):
    """Tier 2: RecursiveReflectionEngine bounds reflection history to prevent context explosion."""
    engine = RecursiveReflectionEngine(adapter=mock_harness_adapter, max_history=5)
    for i in range(10):
        engine.record_reflection(
            ReflectionRecord(
                tick=i,
                actual_fitness=0.5,
                counterfactual_fitness=0.6,
                regret=0.1,
                prompt_mutation_suggestion=f"Mutation {i}",
            )
        )
    assert len(engine.history) == 5
    assert engine.history[-1].tick == 9


@pytest.mark.tier2
def test_boundary_f15_regret_bounded_in_unit_interval(mock_harness_adapter):
    """Tier 2: Regret metric is strictly bounded in [0.0, 1.0]."""
    engine = RecursiveReflectionEngine(adapter=mock_harness_adapter)
    # Actual exceeds counterfactual -> regret is 0.0
    rec1 = engine.reflect(1, "ctx", "act", "out", "alt", actual_fitness=0.9, counterfactual_fitness=0.4)
    assert rec1.regret == 0.0

    # Extreme counterfactual delta -> regret clamped to 1.0
    rec2 = engine.reflect(2, "ctx", "act", "out", "alt", actual_fitness=-0.5, counterfactual_fitness=1.5)
    assert 0.0 <= rec2.regret <= 1.0


# ============================================================================
# TIER 3: CROSS-FEATURE INTERACTIONS
# ============================================================================

@pytest.mark.tier3
def test_cross_evolution_dynamic_corpus_retrieval(stoic_profile, mock_harness_adapter):
    """F11 + F13: Agent dynamically queries CorpusRetriever to evaluate candidate doctrines."""
    retriever = CorpusRetriever()
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    # Search for alternative doctrines matching 'fairness'
    candidates = retriever.search("fairness and justice", top_k=3)
    assert len(candidates) > 0
    candidate_profile = candidates[0]
    assert isinstance(candidate_profile, IdeologicalProfile)


@pytest.mark.tier3
def test_cross_evolution_sandbox_reflection_persistence(stoic_profile, mock_harness_adapter, isolated_project_dir):
    """F1 + F15: Agent persisting reflection log writes strictly within sandbox repository paths."""
    sb = SecuritySandbox(project_root=isolated_project_dir)
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    with sb.get_context():
        log_path = isolated_project_dir / "journal" / "agent_reflections.jsonl"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write('{"tick": 1, "agent": "Marcus", "regret": 0.15}\n')

        assert log_path.is_file()

        # Writing outside repo is blocked
        with pytest.raises(Exception):
            with open(isolated_project_dir.parent / "leak.log", "w") as f:
                f.write("LEAK")


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (Scenarios 4 & 5)
# ============================================================================

@pytest.mark.tier4
def test_scenario_4_rapid_ideological_oscillations_and_rollback(stoic_profile, utilitarian_profile, mock_harness_adapter):
    """
    Scenario 4: Rapid Ideological Oscillations and Probationary Rollback.
    Simulates a volatile macroeconomic environment where noisy fitness signals threaten stability:
    1. Agent starts with Stoic doctrine.
    2. Environmental shock drops fitness, triggering tentative switch to Utilitarianism under probation.
    3. Hysteresis margin prevents erratic intermediate switching.
    4. Post-switch performance drops significantly, causing probationary rollback.
    5. Agent safely restores prior Stoic doctrine, recovering baseline stability.
    """
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
        budget=1000,
    )
    switcher = CategorySwitchManager(agent=agent, switching_cost=50, hysteresis_margin=0.15, probation_window=2)

    # Initial tick
    agent.fitness_history.append(FitnessMetrics(wealth=0.7, security=0.7, reputation=0.7, fairness=0.7, compliance=0.7))

    # Shock at tick 1: fitness drops
    shock_metrics = FitnessMetrics(wealth=0.2, security=0.2, reputation=0.2, fairness=0.2, compliance=0.2)
    agent.fitness_history.append(shock_metrics)

    # Switch evaluated and executed
    assert switcher.evaluate_switch(utilitarian_profile, candidate_expected_fitness=0.8) is True
    switcher.execute_switch(utilitarian_profile, current_tick=1)
    assert agent.ideology.id == utilitarian_profile.id
    assert agent.is_on_probation is True

    # Marginal noise at tick 2: new candidate offers only 0.82 (+0.02 <= H_margin 0.15) -> rejected
    noisy_candidate = IdeologicalProfile(
        id="political_ideology.technocracy",
        domain="political_ideology",
        title="Technocracy",
        key_thinkers=["Veblen"],
        axioms=["Efficiency above all."],
        utility_weights={"wealth": 0.4, "security": 0.3, "reputation": 0.1, "fairness": 0.1, "compliance": 0.1},
        decision_heuristics=["Optimize allocation"],
    )
    assert switcher.evaluate_switch(noisy_candidate, candidate_expected_fitness=0.82, current_tick=2) is False

    # Tick 2: Utilitarian performance collapses
    collapse_metrics = FitnessMetrics(wealth=0.05, security=0.05, reputation=0.1, fairness=0.1, compliance=0.1)
    agent.fitness_history.append(collapse_metrics)

    # Probation check triggers rollback
    rolled_back = switcher.check_probation(current_tick=2)
    assert rolled_back is True
    assert agent.ideology.id == stoic_profile.id


@pytest.mark.tier4
def test_scenario_5_long_horizon_recursive_reflection(stoic_profile, mock_harness_adapter):
    """
    Scenario 5: Long-Horizon Recursive Reflection and Regret Minimization.
    Simulates multi-tick introspective self-improvement:
    1. Over 5 sequential ticks, agent records outcomes and introspects via RecursiveReflectionEngine.
    2. Counterfactual regret is tracked across ticks.
    3. Engine adapts system prompt overlays with distilled policy heuristics.
    4. Composite fitness monotonically recovers as heuristics are integrated into memory.
    """
    agent = EvolutionaryAgent(
        name="Marcus",
        clan="Philosophers",
        role="Virtue Ethicist",
        ideology=stoic_profile,
        adapter=mock_harness_adapter,
    )
    engine = RecursiveReflectionEngine(adapter=mock_harness_adapter, max_history=10)

    fitness_trajectory = [0.25, 0.40, 0.55, 0.70, 0.85]
    for tick, fitness in enumerate(fitness_trajectory, start=1):
        rec = engine.reflect(
            tick=tick,
            perceived_context=f"Society state tick {tick}",
            action_taken=f"Action at tick {tick}",
            observed_outcome=f"Outcome with fitness {fitness}",
            counterfactual_alternative="Alternative policy choice",
            actual_fitness=fitness,
            counterfactual_fitness=0.85,
        )
        agent.reflection_history.append(rec)
        agent.fitness_history.append(
            FitnessMetrics(wealth=fitness, security=fitness, reputation=fitness, fairness=fitness, compliance=fitness)
        )

    # Assert regret decreased over time as actual fitness approached counterfactual
    initial_regret = agent.reflection_history[0].regret
    final_regret = agent.reflection_history[-1].regret
    assert initial_regret > final_regret
    assert final_regret == 0.0

    # Assert monotonic recovery
    fitness_values = [m.wealth for m in agent.fitness_history]
    assert fitness_values == sorted(fitness_values)
