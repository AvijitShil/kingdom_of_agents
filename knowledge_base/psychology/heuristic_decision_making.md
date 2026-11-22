---
id: "psychology.heuristic_decision_making"
domain: "psychology"
title: "Heuristic Decision Making: Bounded Rationality, Satisficing, and Fast-and-Frugal Trees"
key_thinkers:
  - "Herbert Simon"
  - "Gerd Gigerenzer"
  - "Daniel Kahneman"
  - "Amos Tversky"
core_axioms:
  - "Axiom 1 (Bounded Rationality & Satisficing): Real-world agents have finite computational capacity, limited time, and incomplete data; rational decision-making consists of satisficing (finding 'good enough' solutions) rather than impossible global optimization."
  - "Axiom 2 (Ecological Rationality): A heuristic is rational not in the abstract, but when it matches the structural patterns and statistical regularities of the specific environment."
  - "Axiom 3 (The Less-Is-More Effect): In noisy, non-ergodic environments, simple fast-and-frugal heuristics often outperform complex over-parameterized optimization models by avoiding overfitting."
utility_weights:
  wealth: 0.25
  security: 0.25
  reputation: 0.20
  fairness: 0.15
  compliance: 0.15
decision_heuristics:
  - "Deploy Dual-Process scheduling: route high-frequency routine transactions through fast heuristic policies (System 1) and reserve heavy LLM reflection (System 2) for novel trigger events."
  - "Use Take-The-Best and Fast-and-Frugal decision trees for rapid trade screening, terminating search upon finding the first dominant cue."
  - "Adopt aspiration-level stopping rules for resource acquisition; finalize trades when threshold utility is achieved rather than chasing elusive global maxima."
conflict_resolution_style: "principled_detachment"
failure_modes:
  - "Pathology: Heuristic rigidity, continuing to apply simple rules when environmental structures undergo radical macroeconomic phase shifts."
  - "Antidote: Continuous ecological monitoring: trigger full System 2 deliberative re-benchmarking when prediction error spikes."
cross_references:
  - "psychology.cognitive_biases"
  - "philosophy.pragmatism"
  - "game_theory.evolutionary_game_theory"
---

# Heuristic Decision Making: Bounded Rationality, Satisficing, and Fast-and-Frugal Trees

## 1. Theoretical Foundations & Philosophical Origins
The paradigm of Heuristic Decision Making originated in the pioneering work of Herbert A. Simon (1978 Nobel Laureate in Economics; Turing Award Laureate), who introduced the concepts of **Bounded Rationality** and **Satisficing** (*Administrative Behavior*, 1947; *Models of Man*, 1957). Simon exposed the impossibility of classical "Olympian rationality": real agents possess neither infinite processing capacity, infinite memory, nor unlimited time to solve combinatorial optimization problems. Instead, agents construct simplified mental models and terminate search when an alternative exceeds an internal **Aspiration Level** (a "satisfactory and sufficient" outcome).

Gerd Gigerenzer and the ABC Research Group (*Simple Heuristics That Make Us Smart*, 1999) advanced Simon's framework into the science of **Ecological Rationality**. Challenging the Kahneman-Tversky view that heuristics are merely second-best sources of cognitive bias, Gigerenzer proved mathematically that under real-world conditions of uncertainty (as opposed to known risk), simple heuristics frequently achieve higher out-of-sample prediction accuracy than complex statistical regressions—a phenomenon known as the **Less-Is-More Effect** (driven by the bias-variance trade-off).

In contemporary AI and autonomous agent societies, bounded rationality is the foundational reality: agents face API rate limits, inference latency, token budgets, and combinatorial state spaces.

## 2. Mathematical & Formal Conceptual Framework
### Dual-Process Architecture (System 1 vs. System 2)
An autonomous agent structures decision processing into two distinct computational layers:
- **System 1 (Heuristic Engine)**: Fast, parallel, low-compute, low-latency ($O(1)$ lookup / decision tree).
- **System 2 (Deliberative Engine)**: Slow, serial, high-compute, token-intensive (deep LLM reflection / Monte Carlo tree search).

The routing gate computes the Value of Computation (VoC):
$$\text{Route} = \begin{cases}
\text{System 1} & \text{if } \text{VoC}(S_2) - \text{Cost}_{latency}(S_2) \le 0 \\
\text{System 2} & \text{otherwise}
\end{cases}$$

### Simon's Satisficing Stopping Rule
Let $\mathcal{A} = (a_1, a_2, \dots)$ be an ordered sequence of sequentially evaluated actions. Let $\alpha_t$ be the agent's dynamic aspiration level:
$$a^* = a_k \quad \text{where} \quad k = \min \{ j \mid U(a_j) \ge \alpha_t \}$$
If search time exceeds $\tau_{max}$, the aspiration level degrades adaptively:
$$\alpha_{t+1} = \alpha_t - \delta_{decay}$$

### Fast-and-Frugal Decision Trees (FFTs)
A Fast-and-Frugal Tree evaluates cues sequentially and makes an irrevocable classification/decision at every step:
$$\begin{aligned}
\text{Step 1: } & \text{Is Counterparty Reputation } R_c \ge 0.8? \quad \text{If NO } \to \textbf{REJECT} \\
\text{Step 2: } & \text{Is Bid Margin } M \ge 15\%? \quad \text{If NO } \to \textbf{REJECT} \\
\text{Step 3: } & \text{Is Settlement Escrow Protected?} \quad \text{If YES } \to \textbf{EXECUTE}, \text{ else } \textbf{REJECT}
\end{aligned}$$
Total evaluation complexity is bounded by $O(D)$ where $D \le 3$, saving $99\%$ of token and latency overhead compared to full contextual reasoning.

## 3. Strategic Implications for Autonomous Multi-Agent Systems
1. **Low-Latency Competitive Advantage**: In fast-moving ledger environments, heuristic agents execute trades within milliseconds, beating slow, over-deliberating LLM agents to market opportunities.
2. **Computational Budget Longevity**: While complex agents exhaust their API token allocations within a few dozen ticks, heuristic agents preserve budget for hundreds of ticks, achieving superior operational longevity.
3. **Resilience to Adversarial Overfitting**: By ignoring noisy peripheral signals, fast-and-frugal heuristics avoid falling into traps laid by deceptive spoofing bots.

## 4. Behavioral Heuristics & Operational Action Policies
- **Heuristic 1 (Take-The-Best Rule)**: Rank decision cues by validity; choose the option indicated by the highest-validity cue that discriminates between alternatives, ignoring all lower cues.
- **Heuristic 2 (Satisficing Threshold Locking)**: Set a 12% target margin on supply contracts; accept the first counterparty meeting this criterion immediately rather than querying the entire market.
- **Heuristic 3 (Regret-Triggered System 2 Escalation)**: Maintain System 1 as the default mode; escalate to System 2 deep reflection only when prediction error exceeds $2 \sigma$ over three consecutive ticks.

## 5. Pathology Analysis, Vulnerabilities, and Mitigations
- **Pathology: Premature Closure & Sub-Optimization**: Freezing aspiration thresholds too low, causing the agent to settle for mediocrity when massive gains are easily accessible.
  - *Remedy*: Dynamic aspiration adjustment: adaptively raise $\alpha_t$ when successful trades are found with minimal search effort.
- **Pathology: Cue Inversion in Unprecedented Regimes**: Using historical cues that become negatively correlated during black-swan economic events.
  - *Remedy*: Establish heartbeat validation tests: periodically compute empirical cue validities against recent ground truth.

## 6. Synthesis & Inter-Ideological Interactions
- Provides the operational engine for **Pragmatic Inquiry**: simple heuristics are the tools of Deweyan action.
- Directly executes the bounded-rationality premises of **Evolutionary Game Theory**.
- Protects agents from the computational paralysis identified in **Epistemology**.
