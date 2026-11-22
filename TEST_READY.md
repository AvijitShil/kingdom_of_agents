![All tests passed](https://img.shields.io/badge/tests-passed-brightgreen)
# E2E Test Suite Ready

## Test Runner

- **Command**: `python -m pytest tests/ -v` (and bare `python -m pytest`)
- **Configuration**: `pytest.ini` with `testpaths = tests`, `pythonpath = . ..`, and strict markers (`tier1`..`tier5`, `security`, `corpus`, `evolution`, `adversarial`, `hardening`, `e2e`, `sync`, `skip_sandbox`).
- **Expected Outcome**: All 222 active tests pass with exit code 0 (0 failures, 0 errors, 0 warnings).

## Coverage Summary
| Tier | Count | Description |
|------|------:|-------------|
| 1. Feature Coverage | 46 | Isolated happy-path functional coverage across all 16 features (≥5 assertions per feature) |
| 2. Boundary & Corner Cases | 37 | Windows path traversal, 8.3 short names, NTFS ADS, UNC paths, device names, protected config files, shell operators, unapproved binaries, zero-telemetry socket blocking (`connect`, `connect_ex`, `sendto`), PBKDF2 600k rounds & 32-byte salt, corpus weight normalization ($\sum w_i = 1.0 \pm 10^{-4}$), hysteresis margins ($H_{margin}=0.15$), cooldowns ($\tau=3$), probationary rollback |
| 3. Cross-Feature Combinations | 8 | Pairwise interactions: Sandbox Context + Network + File I/O, Subprocess + Path Confinement, Boundary Expansion under Auth, Corpus Retrieval via Sandbox, In-memory Caching Latency (<1ms), Dynamic Retrieval during Evolution, Sandboxed Reflection Persistence, Sandboxed Git Sync |
| 4. Real-World Application Scenarios | 8 | Comprehensive multi-feature workload scenarios: Scenario 1 (Multi-Agent Scarcity Society), Scenario 2 (Hostile Sandbox Escape & Exfiltration Simulation), Scenario 3 (Full Corpus Ingestion & Cross-Domain Querying), Scenario 4 (Rapid Ideological Oscillations & Rollback), Scenario 5 (Long-Horizon Recursive Reflection), Scenario 6 (Authorized Boundary Expansion), Scenario 7 (Secure Automated Git Sync under Sandbox), Scenario 8 (Multi-Tick Full Society Simulation with Journal Persistence) |
| 5. Adversarial Hardening | 52 | Deep white-box adversarial stress testing across sandbox (14 tests), knowledge base (16 tests), and evolution (22 tests) subsystems: bitwise permission masks, Windows console handles (`CONIN$`, `CONOUT$`, `CLOCK$`), directory junctions, NT namespace paths, Unicode normalization, subprocess environment variables (`PYTHONPATH`, `PYTHONHOME`), argument path scanning (`--exec-path`, `-C`), reverse DNS blocking (`gethostbyaddr`), UDP positional flags, IPv6 destinations, multi-tenant concurrency, cascading exceptions, malformed config recovery, NaN/Inf validation, tolerance precision boundaries, negative weight rejection, empty/invalid axioms, loader fuzzing, regex/SQL injection queries, fitness mathematical stability, hysteresis flapping, cooldown underflow, probation rollback, and 50-agent society stress |
| **Total Dedicated E2E & Hardening Tests** | **151** | **E2E test suite in `tests/test_e2e_*.py` and `tests/test_tier5_adversarial_hardening.py`** |
| *Unit & Component Tests* | *71* | Target-scoped unit suites in `tests/test_sandbox_*.py`, `tests/test_corpus_retrieval.py`, and `tests/test_github_push_sync.py` |
| **Total Suite Items** | **222 passed** | **222 total collected items, exit code 0** |

## Feature Checklist
| Feature | Description | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|---------|-------------|:------:|:------:|:------:|:------:|:------:|
| F1 | Windows Path Confinement | 5 | 5 | ✓ | ✓ | ✓ |
| F2 | Subprocess Execution Guard | 5 | 5 | ✓ | ✓ | ✓ |
| F3 | Zero-Telemetry Socket Interception | 5 | 5 | ✓ | ✓ | ✓ |
| F4 | Password-Protected Boundary Control | 5 | 5 | ✓ | ✓ | ✓ |
| F5 | Sandbox Runtime Hook Context | 5 | 5 | ✓ | ✓ | ✓ |
| F6 | Philosophy Corpus (9 topics) | 5 | 5 | ✓ | ✓ | ✓ |
| F7 | Game Theory Corpus (6 topics) | 5 | 5 | ✓ | ✓ | ✓ |
| F8 | Political Ideology Corpus (5 topics) | 5 | 5 | ✓ | ✓ | ✓ |
| F9 | Religious Ideology Corpus (4 topics) | 5 | 5 | ✓ | ✓ | ✓ |
| F10 | Psychology Corpus (5 topics) | 5 | 5 | ✓ | ✓ | ✓ |
| F11 | Knowledge Base Catalog & Retriever | 5 | 5 | ✓ | ✓ | ✓ |
| F12 | EvolutionaryAgent & Profile Model | 5 | 5 | ✓ | ✓ | ✓ |
| F13 | Dynamic Category Switch Manager | 5 | 5 | ✓ | ✓ | ✓ |
| F14 | Probation & Rollback Mechanism | 5 | 5 | ✓ | ✓ | ✓ |
| F15 | Recursive Reflection Engine | 5 | 5 | ✓ | ✓ | ✓ |
| F16 | Git Remote Synchronization | 5 | 5 | ✓ | ✓ | ✓ |

## Test Suite Inventory
1. `pytest.ini`: Root configuration with strict markers and pythonpath resolution.
2. `tests/conftest.py`: Shared test fixtures (`isolated_project_dir`, `sandbox_admin_password`, `mock_harness_adapter`, `sample_ideological_profile`, and autouse `clean_sandbox_hooks`).
3. `tests/test_e2e_sandbox_security.py`: 48 tests covering Features 1–5, Scenarios 2 & 6.
4. `tests/test_e2e_corpus_retrieval.py`: 22 tests covering Features 6–11, Scenario 3.
5. `tests/test_e2e_agent_evolution.py`: 16 tests covering Features 12–15, Scenarios 4 & 5.
6. `tests/test_e2e_github_sync.py`: 11 tests covering Feature 16, Scenario 7.
7. `tests/test_e2e_full_simulation.py`: 2 tests covering Scenarios 1 & 8.
8. `tests/test_tier5_adversarial_hardening.py`: 52 tests covering Tier 5 Adversarial Hardening across Sandbox, Knowledge Base, and Evolution.
9. `tests/test_sandbox_path.py`: Unit tests for path validation.
10. `tests/test_sandbox_exec.py`: Unit tests for execution guard.
11. `tests/test_sandbox_auth.py`: Unit tests for authentication and PBKDF2.
12. `tests/test_sandbox_network.py`: Unit tests for zero-telemetry network guard.
13. `tests/test_sandbox_e2e.py`: Sandbox facade and context integration tests.
14. `tests/test_corpus_retrieval.py`: Unit tests for corpus catalog, models, loader, and retriever.
15. `tests/test_github_push_sync.py`: Unit tests for Git remote push synchronization.
