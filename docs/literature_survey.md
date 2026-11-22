# Comprehensive Literature Survey: Autonomous LLM Civilizations, Ideological Evolution, Game Theory & Sandboxed Multi-Agent Societies

**Target Project:** EON Kingdom of Agents  
**Date:** November 2026  
**Context:** Longitudinal simulation on frozen Gemma 4 E4B (Intel Arc A380 dGPU, OpenVINO) with DeepSeek Harness adaptation, ideological categorization, and password-protected sandboxing.

---

## Executive Overview & Taxonomy

Autonomous LLM-driven civilization research sits at the intersection of four foundational domains:
1. **Generative Social Simulation & Civilizational Emergence** (scaling from individual personas to full socio-political ecosystems).
2. **Ideological, Philosophical & Psychological Modeling** (endowing agents with moral priors, strategic doctrines, and dynamic worldview switching).
3. **Game Theory, Economic Mechanism Design & Conflict Resolution** (strategic bargaining, public goods dilemmas, judicial courts, and currency velocity).
4. **Recursive Self-Improvement & Frozen-Model Evolutionary Harnesses** (improving capabilities without retraining base model weights).
5. **Agent Sandboxing, Execution Safety & Data Leakage Prevention** (air-gapping host filesystem and preventing external exfiltration).

```
                            ┌──────────────────────────────────────────────┐
                            │          EON Kingdom of Agents               │
                            │ (Frozen Gemma 4 + Arc A380 + DeepSeek Harness)│
                            └──────────────────────┬───────────────────────┘
                                                   │
         ┌─────────────────────────┬───────────────┴───────────────┬─────────────────────────┐
         ▼                         ▼                               ▼                         ▼
┌──────────────────┐     ┌──────────────────┐            ┌──────────────────┐      ┌──────────────────┐
│ Social Emergence │     │ Ideology & Psych │            │ Recursive Evol.  │      │ Containment &    │
│  & Civilization  │     │   Doctrine Base  │            │ (Frozen Weights) │      │ Sandbox Security │
├──────────────────┤     ├──────────────────┤            ├──────────────────┤      ├──────────────────┤
│ - Project Sid    │     │ - GenMinds       │            │ - Promptbreeder  │      │ - OWASP Agent Top│
│ - AgentSociety   │     │ - MoralFoundat.  │            │ - EvoPrompt      │      │ - Path Guardrail │
│ - GenerativeAgts │     │ - GameTheory-LLM │            │ - DeepSeekHarn.  │      │ - Token-Lock Wall│
└──────────────────┘     └──────────────────┘            └──────────────────┘      └──────────────────┘
```

---

## 1. Generative Social Simulation & Autonomous Civilizations

### 1.1 Project Sid: Many-Agent Civilizations in Minecraft
- **Authors:** Robert Yang, Altera.ai Team (2024 / 2025)
- **Core Architecture:** PIANO (*Parallel Information Aggregation via Neural Orchestration*).
- **Key Findings:** Over 1,000 autonomous agents placed in an open-ended environment spontaneously developed:
  - **Specialized Division of Labor:** Moving from uniform random behaviors to farmers, builders, and artisans based on collective utility.
  - **Economic Institutions:** Standardized rare in-game items into currency, established marketplace hubs, and exhibited bribery/corruption.
  - **Governance & Legal Tokens:** Voted on democratic constitutions, elected leaders, and amended statutory laws.
  - **Cultural & Religious Emergence:** Spontaneously generated sacred rituals, belief doctrines, and designated clergy figures.
- **Direct Relationship to EON Kingdom of Agents:**
  - *Direct Precedent:* Project Sid proves that LLM agents can organically establish religious, legal, and economic structures without hardcoded behavior trees.
  - *How EON Extends It:* While Project Sid relied on commercial cloud LLM endpoints and gaming environments, EON executes locally on a dedicated Intel Arc A380 6GB GPU using frozen Gemma 4 OpenVINO weights and formal daily git-journaled longitudinal tracking.

### 1.2 From Individual to Society: A Survey on Social Simulation Driven by LLMs
- **Authors:** Xinyi Mou, Zhongyu Wei, et al. (Fudan University, arXiv:2412.03563, Dec 2024)
- **Taxonomy Proposed:**
  1. *Individual Simulation:* Demographic profiling, psychological traits, and cognitive priors.
  2. *Scenario Simulation:* Task-oriented collaborations, market auctions, negotiation dyads.
  3. *Society Simulation:* Macro-level societal norms, institutional stratification, polarization, and cultural diffusion.
- **Direct Relationship to EON Kingdom of Agents:**
  - Provides the theoretical validation for EON’s multi-clan tiering (Section 8 of the plan), establishing that societal macro-properties cannot be observed through isolated pairwise agent benchmarks.

### 1.3 AgentSociety: Large-Scale Simulation of Generative Agents
- **Authors:** Tsinghua & Collaborators (arXiv:2502.08691, Feb 2025)
- **Core Contribution:** Scaled social agent simulations to evaluate urban dynamics, tax policy shocks, and institutional collapse over extended simulation horizons.
- **Direct Relationship to EON Kingdom of Agents:**
  - Validates EON's 30-day longitudinal timeline: short-horizon runs (e.g. 10 ticks) miss systemic phenomena like wealth concentration, currency hoarding, and constitutional decay, which only manifest over extended cycles.

### 1.4 Generative Agents: Interactive Simulacra of Human Behavior
- **Authors:** Joon Sung Park, Joseph C. O'Hanlon, et al. (Stanford University & Google Research, UIST 2023)
- **Core Architecture:** Tripartite memory architecture: *Memory Stream* (perceptions), *Reflection* (higher-level synthesis), and *Planning* (hierarchical intention).
- **Direct Relationship to EON Kingdom of Agents:**
  - EON's `agents/base.py` and `memory/` modules adopt the Reflection $\rightarrow$ Action cycle, while adding inter-clan economic tokens and court litigation mechanisms.

### 1.5 WarAgent: Emergent Historical Conflicts and AI International Relations
- **Authors:** Wenyue Hua et al. (Rutgers University, 2023)
- **Core Findings:** Simulated historical conflicts (e.g. WWI mobilization) by parameterizing country-agents with military capacity, alliance treaties, and nationalistic rhetoric.
- **Direct Relationship to EON Kingdom of Agents:**
  - Informs EON's `society/alliance.py` and `society/court.py`: demonstrates that when agents represent competing sovereign entities without an enforceable arbitration court, alliance spirals predictably lead to conflict.

---

## 2. Ideological, Philosophical, Psychological & Game-Theoretic Frameworks

### 2.1 Simulating Society Requires Simulating Thought (GenMinds)
- **Authors:** Cognitive AI Research Collective (arXiv:2506.06958, 2025)
- **Core Argument:** Criticizes standard agent frameworks that use superficial demographic prompts ("You are a merchant"). Argues that genuine agent societies require explicit cognitive models of **belief-desire-intention (BDI)**, moral foundations, and philosophical grounding.
- **Direct Relationship to EON Kingdom of Agents:**
  - Directly justifies the user's requirement to ground agents in formal texts across **Philosophy** (Plato, Kant, Nietzsche, Confucius), **Political Ideologies** (Classical Liberalism, Socialism, Realpolitik), **Religious Ideology**, and **Psychology** (Jungian archetypes, Kohlberg's moral development stages, Kahneman's cognitive heuristics).

### 2.2 Game-Theoretic Strategic Reasoning in LLM Agents
- **Authors:** Akata et al. (2023); Fan et al. (2024)
- **Key Investigations:** Prisoner's Dilemma, Public Goods games, Ultimatum games, and Stag Hunt played by LLM agents.
- **Key Findings:**
  - Default LLM agents are overly compliant/altruistic ("sycophancy bias"), failing to reach Nash equilibria in competitive games unless explicitly primed with strategic concepts like tit-for-tat, minimax, or Machiavellian political philosophy.
- **Direct Relationship to EON Kingdom of Agents:**
  - Injecting game-theoretic documentation into the agent corpus enables clans (e.g. Clan Beta Merchants) to detect free-riding, enforce contract sanctions, and bargain rationally.

### 2.3 Moral Foundations and Ideological Polarization in Multi-Agent Networks
- **Authors:** Petter Törnberg (2023/2024); Santurkar et al. (Google/Stanford, 2023)
- **Key Findings:** Language models possess latent ideological tendencies influenced by pretraining data. When multi-agent societies interact without an overarching legal arbitration layer, agents form ideological echo chambers that rapidly polarize.
- **Direct Relationship to EON Kingdom of Agents:**
  - Explains the necessity of EON's **Judicial Court (`society/court.py`)** and the **Observer Agent (`Chronos`)** to record ideological drift and prevent catastrophic social fragmentation.

---

## 3. Recursive Self-Improvement with Frozen Foundation Models

### 3.1 Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution
- **Authors:** Chrisantha Fernando et al. (Google DeepMind, 2023)
- **Core Mechanism:** An evolutionary algorithm where both task prompts and the mutation-operator prompts evolve recursively. Evaluates candidates using fitness functions and preserves top-performing variants.
- **Direct Relationship to EON Kingdom of Agents:**
  - Proves that an agent system can dramatically improve reasoning, coordination, and domain efficacy **while the underlying neural network weights remain 100% frozen**. EON's `harness/candidates/` and `harness/adapter.py` directly leverage this evolutionary paradigm.

### 3.2 EvoPrompt: Connecting LLMs with Evolutionary Algorithms
- **Authors:** Qingyan Guo et al. (2023)
- **Core Mechanism:** Employs genetic algorithm operators (crossover, mutation) where the LLM itself generates diverse offspring prompts based on parent prompt pairs.
- **Direct Relationship to EON Kingdom of Agents:**
  - Provides the algorithmic blueprint for inter-clan skill exchange: when Clan Alpha develops an efficient tool schema, Clan Beta can cross-breed that schema with its economic negotiation prompts.

### 3.3 DeepSeek Harness Architecture
- **Authors:** DeepSeek-AI (2024 / 2025)
- **Design Philosophy:** "Everything is a Plugin". Completely decouples the frozen inference engine from execution tools, memory indices, and dynamic agent roles.
- **Direct Relationship to EON Kingdom of Agents:**
  - EON's runtime is engineered on `deepseek-harness-sdk` to guarantee modularity and enforce base weight immutability.

---

## 4. Agent Sandboxing, Execution Safety & Host Boundary Containment

### 4.1 Sandboxing LLM Agents: Boundary Defense & Execution Guardrails
- **Authors:** OWASP GenAI Top 10 Security Project & Application Security Research (2024 / 2025)
- **Identified Threat Vectors:**
  - *Arbitrary Tool Execution & Host Traversal:* Agents generating malicious shell or filesystem commands (`os.system`, `subprocess`, path traversal `../../`).
  - *Data Exfiltration:* Network calls (`curl`, `requests`, DNS tunneling) leaking sensitive user files or API tokens.
  - *Recursive Jailbreak / Prompt Injection:* Autonomous agents adopting unconstrained goals that violate host safety.
- **Required Defenses:**
  - Application-level canonical path resolution (`os.path.realpath`, prefix whitelisting).
  - Interception wrappers on file I/O operations (`open`, `Path.write_text`, `os.remove`).
  - Strict network socket binding (disallowing external outbound TCP sockets except explicitly whitelisted local localhost ports).
  - Password / HMAC token authentication required to alter containment parameters.
- **Direct Relationship to EON Kingdom of Agents:**
  - Directly informs the user's password-protected sandbox firewall (`c:\Users\Subhajit\Documents\EON exp\kingdom_of_agents`), ensuring agents can never touch any host directory outside this project root.

---

## Comparative Matrix: EON vs. Prior Works

| System | Base Model / Execution | Weight State | Longitudinal Horizon | Ideological / Philosophical Grounding | Sandboxing & Host Isolation | Automated Git Journaling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Generative Agents (Smallville)** | Cloud OpenAI (GPT-3.5) | N/A (Closed API) | 2–3 in-game days | Generic Persona prompts | Soft game-world boundary | None |
| **Project Sid (Altera)** | Cloud Proprietary LLMs | N/A (Closed API) | Variable sessions | Emergent in-game beliefs | Minecraft game engine | None |
| **WarAgent** | Cloud OpenAI (GPT-4) | N/A (Closed API) | Single historical event | Hardcoded country stances | Simulation loop | None |
| **AgentSociety** | Distributed Cloud Cluster | N/A (Closed API) | Multi-day simulation | Sociological parameters | Container cluster | None |
| **Promptbreeder** | Google PaLM / Gemini | Frozen | Iterative rounds | Algorithmic fitness | Algorithmic harness | None |
| **EON Kingdom of Agents (This Work)** | **Gemma 4 E4B INT4 on local Intel Arc A380 dGPU (OpenVINO)** | **100% Cryptographically Frozen (SHA-256 Verified)** | **30 Days Longitudinal (Daily ticks)** | **Explicit Corpus: Philosophy, Game Theory, Politics, Religion, Psychology (Dynamic Switching)** | **Password-Protected Application-Level Host Firewall** | **Automated Daily Git Commit & Remote Push** |

---

## Key Implications for EON Implementation

1. **Explicit Pre-Launch User Approval:** Before initiating Day 01+ continuous tick cycles, present the full state (agent rosters, ideological allocations, court laws, and sandbox boundaries) to the user for explicit authorization.
2. **Dynamic Worldview Adoption:** Agents should not be statically frozen in one ideology; they must evaluate their utility and social standing, allowing them to shift from e.g. Utilitarian Technocracy to Stoic Legalism or Game-Theoretic Realpolitik as societal stress dictates.
3. **Double-Lock Containment:** The sandbox must operate at both the file I/O layer and the tool execution layer, protected by a cryptographic password/hash.
