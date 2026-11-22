# E2E Test Infra: kingdom_of_agents

## Test Philosophy
- **Opaque-box & Requirement-Driven**: Tests validate external contracts, behaviors, security barriers, and specifications as described in `ORIGINAL_REQUEST.md` and `PROJECT.md` without coupling to fragile private implementation details.
- **Methodology**: Systematic 4-tier design:
  - **Tier 1: Feature Coverage (≥5 per feature)**: Isolated functional happy paths testing equivalence-class representatives across all 16 features.
  - **Tier 2: Boundary & Corner Cases (≥5 per feature)**: Path traversal variations, Windows 8.3 aliases, alternate data streams (ADS), UNC paths, network socket evasion, password salt/hash edge cases, corpus schema edge cases, extreme fitness thresholds, hysteresis boundaries.
  - **Tier 3: Cross-Feature Interactions (Pairwise combinations)**: Security Sandbox + Agent Execution, Agent Reflection + Corpus Retrieval, Category Switching + Probation Rollback + Sandbox I/O, Git Remote Sync + Local Sandbox Confinement.
  - **Tier 4: Real-World Application Scenarios (≥8 scenarios)**: Multi-agent societies evolving over multi-tick simulation loops, dynamic category switching under environmental pressure, recursive reflection journals, and full end-to-end simulation within `SandboxContext`.

## Feature Inventory & Test Tier Mapping
| # | Feature | Source (Requirement) | Target Module | Tier 1 | Tier 2 | Tier 3 |
|---|---------|----------------------|---------------|:------:|:------:|:------:|
| 1 | Windows Path Confinement | ORIGINAL_REQUEST §R3 | `sandbox.validator` | 5 | 5 | ✓ |
| 2 | Subprocess Execution Guard | ORIGINAL_REQUEST §R3 | `sandbox.execution` | 5 | 5 | ✓ |
| 3 | Zero-Telemetry Socket Interception | ORIGINAL_REQUEST §R3 | `sandbox.network` | 5 | 5 | ✓ |
| 4 | Password-Protected Boundary Control | ORIGINAL_REQUEST §R3 | `sandbox.auth` | 5 | 5 | ✓ |
| 5 | Sandbox Runtime Hook Context | ORIGINAL_REQUEST §R3 | `sandbox.context` | 5 | 5 | ✓ |
| 6 | Philosophy Corpus (9 topics) | ORIGINAL_REQUEST §R1 | `knowledge_base/philosophy` | 5 | 5 | ✓ |
| 7 | Game Theory Corpus (6 topics) | ORIGINAL_REQUEST §R1 | `knowledge_base/game_theory` | 5 | 5 | ✓ |
| 8 | Political Ideology Corpus (5 topics) | ORIGINAL_REQUEST §R1 | `knowledge_base/political_ideology` | 5 | 5 | ✓ |
| 9 | Religious Ideology Corpus (4 topics) | ORIGINAL_REQUEST §R1 | `knowledge_base/religious_ideology` | 5 | 5 | ✓ |
| 10 | Psychology Corpus (5 topics) | ORIGINAL_REQUEST §R1 | `knowledge_base/psychology` | 5 | 5 | ✓ |
| 11 | Knowledge Base Catalog & Retriever | ORIGINAL_REQUEST §R1 | `knowledge_base.retriever` | 5 | 5 | ✓ |
| 12 | EvolutionaryAgent & Profile Model | ORIGINAL_REQUEST §R2 | `evolution.agent` | 5 | 5 | ✓ |
| 13 | Dynamic Category Switch Manager | ORIGINAL_REQUEST §R2 | `evolution.switcher` | 5 | 5 | ✓ |
| 14 | Probation & Rollback Mechanism | ORIGINAL_REQUEST §R2 | `evolution.switcher` | 5 | 5 | ✓ |
| 15 | Recursive Reflection Engine | ORIGINAL_REQUEST §R2 | `evolution.reflection` | 5 | 5 | ✓ |
| 16 | Git Remote Synchronization | ORIGINAL_REQUEST §R4 | Git CLI / Sync harness | 5 | 5 | ✓ |

## Test Architecture
- **Test Runner**: `pytest`
- **Invocation**: `pytest -v` or `python -m pytest tests/`
- **Configuration**: `pytest.ini` with `testpaths = tests`, strict markers, and pythonpath configuration.
- **Pass/Fail Semantics**: All test suites must execute with exit code 0, 0 failures, 0 errors.

### Directory Layout
```
kingdom_of_agents/
├── pytest.ini
├── TEST_INFRA.md
├── TEST_READY.md (published upon completion)
└── tests/
    ├── conftest.py
    ├── test_e2e_sandbox_security.py
    ├── test_e2e_corpus_retrieval.py
    ├── test_e2e_agent_evolution.py
    ├── test_e2e_github_sync.py
    └── test_e2e_full_simulation.py
```

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Multi-Agent Society Under Resource Scarcity | F1, F5, F6, F7, F12, F13, F15 | High |
| 2 | Hostile Sandbox Escape & Exfiltration Simulation | F1, F2, F3, F4, F5 | High |
| 3 | Full Corpus Ingestion and Cross-Domain Querying | F6, F7, F8, F9, F10, F11 | Medium |
| 4 | Rapid Ideological Oscillations and Probationary Rollback | F12, F13, F14, F15 | High |
| 5 | Long-Horizon Recursive Reflection and Regret Minimization | F11, F12, F15 | Medium |
| 6 | Authorized Boundary Expansion with Password Reconfiguration | F1, F4, F5 | Medium |
| 7 | Secure Automated Git Sync Under Sandboxed Context | F1, F2, F3, F5, F16 | High |
| 8 | Multi-Tick Full Society Simulation with Journal Persistence | F1-F15 | High |

## Coverage Thresholds
- **Tier 1 (Feature Coverage)**: ≥5 test cases/assertions per feature (≥80 tests total across all features).
- **Tier 2 (Boundary & Corner Cases)**: ≥5 test cases per feature (≥80 boundary tests total).
- **Tier 3 (Cross-Feature Combinations)**: ≥16 pairwise combination tests.
- **Tier 4 (Real-World Application Scenarios)**: ≥8 complex scenarios.
- **Total Suite Minimum**: ~184 test assertions / cases covering all 16 features.
