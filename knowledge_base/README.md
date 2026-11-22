# Ideological Knowledge Base Subsystem

The `knowledge_base/` subsystem serves as the authoritative philosophical, strategic, political, spiritual, and psychological corpus for autonomous agents in `kingdom_of_agents`. It transforms theoretical disciplines into machine-readable behavioral overlays, formal utility weightings, and decision heuristics that guide recursive self-improvement and evolutionary category adaptation.

---

## 1. Architectural Overview

Autonomous agents in complex multi-agent societies require coherent normative guidelines, strategic frameworks, and value priorities. Rather than hardcoding static personalities or prompting agents with ad-hoc instructions, the `knowledge_base/` provides:

1. **Structured Frontmatter**: Machine-readable metadata specifying core axioms, normalized 5-dimensional utility weights, operational decision heuristics, conflict resolution styles, failure modes, and cross-references.
2. **Exhaustive Narrative Body**: In-depth academic exposition detailing theoretical foundations, formal mechanisms, multi-agent dynamics, and failure mode mitigations.
3. **Programmatic Loader & Validator**: Automated YAML parsing and Pydantic validation enforcing that utility vectors sum to 1.0 and axioms are non-empty.
4. **In-Memory Retrieval Engine (`CorpusRetriever`)**: Sub-millisecond lookup, domain filtering, and keyword/token overlap search.

---

## 2. Taxonomy of Domains and Topics

The research corpus encompasses **5 foundational domains** and **29 standardized topics**:

### Domain 1: Philosophy & Normative Systems (`philosophy/`)
- `epistemology.md`: Epistemic validation, empiricism vs. rationalism, Bayesian updating, falsificationism.
- `ethics.md`: Meta-ethics, moral realism, constructivism, and normative principles for machine intelligence.
- `metaphysics.md`: Ontology, determinism vs. free will, agent emergence, and identity through state transitions.
- `existentialism.md`: Radical agency, authentic choice, freedom, and combating existential despair or bad faith.
- `utilitarianism.md`: Act vs. rule utilitarianism, expected aggregate utility, negative utilitarianism, and utility monster mitigation.
- `deontology.md`: Kantian categorical imperative, duty ethics, universalizability, and deontic side-constraints.
- `virtue_ethics.md`: Aristotelian phronesis (practical wisdom), eudaimonia, character cultivation, and the golden mean.
- `stoicism.md`: Epictetus and Aurelius, dichotomy of control, Amor Fati, cognitive resilience, and apatheia.
- `pragmatism.md`: Peirce, James, Dewey, instrumental truth, fallibilism, and iterative inquiry loops.

### Domain 2: Strategic Interaction & Game Theory (`game_theory/`)
- `nash_equilibrium.md`: Non-cooperative equilibria, mixed strategies, focal points, and coordination dilemmas.
- `minimax.md`: Zero-sum defense, worst-case payoff maximization, security levels, and adversarial hedging.
- `evolutionary_game_theory.md`: Replicator dynamics, Evolutionarily Stable Strategies (ESS), Hawk-Dove, and Tit-for-Tat.
- `pareto_optimality.md`: Pareto efficiency frontiers, non-dominated outcomes, and Kaldor-Hicks compensations.
- `mechanism_design.md`: Reverse game theory, incentive compatibility, VCG auctions, and adverse selection mitigation.
- `multi_agent_coordination.md`: Common-pool resource governance (Elinor Ostrom), coalition formation, and trust primitives.

### Domain 3: Political Ideologies & Governance Models (`political_ideology/`)
- `classical_liberalism.md`: Negative liberties, inviolable property rights, spontaneous market order, and rule of law.
- `libertarianism.md`: Non-aggression principle, minarchism, polycentric law, and absolute transactional voluntarism.
- `socialism_communitarianism.md`: Collective ownership, solidarity, commons preservation, and mutual aid structures.
- `realism_vs_idealism.md`: Realpolitik, distribution of power, deterrence, balance of power vs. institutional collective security.
- `technocracy.md`: Cybernetic governance, algorithmic resource optimization, expert meritocracy, and systems engineering.

### Domain 4: Religious & Spiritual Ideologies (`religious_ideology/`)
- `dharmic_karma.md`: Cosmic order (Rita), righteous duty (Dharma), causal feedback (Karma), and detached action (Nishkama Karma).
- `abrahamic_covenantal.md`: Sacred covenant, deontic commandments, restorative justice, moral stewardship, and grace.
- `taoist_wu_wei.md`: The Tao, effortless non-coercive action (Wu Wei), dynamic balance (Yin-Yang), and yielding resilience.
- `buddhist_non_attachment.md`: Dependent origination (Pratityasamutpada), impermanence (Anicca), non-self (Anatta), and suffering cessation.

### Domain 5: Psychology & Behavioral Economics (`psychology/`)
- `cognitive_biases.md`: Systematic cognitive distortions (anchoring, confirmation bias, loss aversion, sunk cost fallacy) and de-biasing filters.
- `heuristic_decision_making.md`: Bounded rationality (Herbert Simon), fast-and-frugal heuristics (Gigerenzer), satisficing, and Dual-Process Theory.
- `maslow_hierarchy.md`: Motivational priority staging (computational survival -> security -> belonging -> esteem -> self-actualization).
- `evolutionary_psychology.md`: Kin selection, reciprocal altruism, costly signaling, reputational tracking, and social cheater detection.
- `behavioral_reinforcement.md`: Operant conditioning, intermittent reinforcement schedules, reward shaping, and dopamine/habit loops.

---

## 3. Data Specification & Frontmatter Schema

Each document begins with strict YAML frontmatter:

```yaml
---
id: "domain.topic"
domain: "domain_name"
title: "Expository Title"
key_thinkers:
  - "Thinker One"
  - "Thinker Two"
core_axioms:
  - "Axiom 1: ..."
  - "Axiom 2: ..."
  - "Axiom 3: ..."
utility_weights:
  wealth: 0.20
  security: 0.20
  reputation: 0.20
  fairness: 0.20
  compliance: 0.20
decision_heuristics:
  - "Heuristic 1: ..."
  - "Heuristic 2: ..."
  - "Heuristic 3: ..."
conflict_resolution_style: "principled_detachment" # Options: principled_detachment, tit_for_tat, cooperative, punitive, arbitrated, etc.
failure_modes:
  - "Pathology: ..."
  - "Antidote: ..."
cross_references:
  - "other_domain.other_topic"
---
```

### Utility Weight Normalization Rule
The 5 utility keys are mandatory:
$$\sum_{k \in \{wealth, security, reputation, fairness, compliance\}} W_k = 1.0 \pm 10^{-4}$$
Each individual weight $W_k \in [0.0, 1.0]$.

---

## 4. Python API Usage

```python
from knowledge_base import CorpusRetriever, CorpusLoader, IdeologicalProfile

# Initialize retriever (loads catalog.json and all 30 markdown docs)
retriever = CorpusRetriever()

# Direct lookup by category ID
stoicism = retriever.get_ideology("philosophy.stoicism")
print(stoicism.title)
print(stoicism.utility_weights)
print(stoicism.system_prompt_overlay)

# Semantic keyword search
results = retriever.search("minimax zero sum adversary", domain="game_theory", top_k=3)
for profile in results:
    print(profile.id, profile.title)

# Domain introspection
domains = retriever.list_domains()
topics = retriever.get_domain_topics("psychology")
all_ids = retriever.list_all_categories() # 30 total
```
