# Kingdom of Agents: Longitudinal EON Society Simulation

This repository hosts the **30-Day Longitudinal EON Society Simulation** powered by **Gemma 4 E4B** (`OpenVINO/gemma-4-E4B-it-int4-ov`) running on an **Intel Arc A380 (6GB VRAM)** dedicated GPU (`GPU.1`) via OpenVINO GenAI, coordinated with the **DeepSeek Harness** architectural foundation.

---

## 🏛️ Core Research Principles (From EON Plan)

1. **Permanently Frozen Foundation Model**:
   - The weights of `gemma-4-E4B-it-int4-ov` remain 100% frozen.
   - Verified daily via cryptographic SHA-256 integrity checks (`harness/frozen_guard.py`).
2. **Recursive Harness Adaptation**:
   - Adaptation occurs exclusively through prompt mutation, tool generation, dynamic memory retrieval, and external agent orchestration.
   - Built on DeepSeek Harness's "Everything is a Plugin" modular philosophy.
3. **Multi-Clan Autonomous Society**:
   - Multiple clans (e.g. Ironforge Technocrats, Sylvan Arbiters, Solar Scribes) with distinct utility functions, laws, currencies, and court dispute mechanisms.
4. **Observer Agent & Daily Journaling**:
   - A dedicated Observer Agent records society metrics, trade volume, law changes, token throughput, and architectural mutations daily into `journals/YYYY-MM-DD.md`.
   - Automated git commits track 30 days of longitudinal evolution.

---

## ⚙️ Architecture & Hardware

```
                     ┌───────────────────────────────────────────────┐
                     │          EON Society Multi-Agent Core         │
                     │  (Clans, Ledger, Dispute Court, Observer)     │
                     └───────────────────────┬───────────────────────┘
                                             │
                     ┌───────────────────────▼───────────────────────┐
                     │          DeepSeek Harness Adapter             │
                     │    (Plugin Manager, Tool Invoker, Memory)     │
                     └───────────────────────┬───────────────────────┘
                                             │ HTTP /v1/chat/completions
                     ┌───────────────────────▼───────────────────────┐
                     │      Local OpenAI-Compatible Server           │
                     │               (FastAPI)                       │
                     └───────────────────────┬───────────────────────┘
                                             │ OpenVINO C++ Runtime
    ┌────────────────────────────────────────┴────────────────────────────────────────┐
    │                                                                                 │
    ▼                                                                                 ▼
┌────────────────────────────────────────┐       ┌────────────────────────────────────────┐
│        Host RAM / Intel Core i9        │       │       Intel Arc A380 6GB (GPU.1)       │
│  - Text Embeddings (0.64 GB)           │       │  - Language Model Core (2.68 GB AWQ)   │
│  - Per-Layer Text Embeddings (2.69 GB) │       │  - Sliding Window KV Cache             │
│  - Vision Embeddings (0.16 GB)         │       │                                        │
└────────────────────────────────────────┘       └────────────────────────────────────────┘
```

---

## 📂 Repository Layout

```
kingdom_of_agents/
├── README.md               # Architecture, principles, and run guide
├── server/
│   └── server.py           # FastAPI OpenAI-compatible OpenVINO GenAI server
├── harness/
│   ├── adapter.py          # DeepSeek Harness bridge to local OpenVINO engine
│   ├── frozen_guard.py     # Base model weight integrity & hash verification
│   └── candidates/         # Dynamic harness mutation candidates
├── agents/
│   ├── base.py             # Agent abstract base class & token budgeting
│   ├── clan_a.py           # Clan Alpha: The Technocrats
│   ├── clan_b.py           # Clan Beta: The Merchants
│   ├── clan_c.py           # Clan Gamma: The Jurists
│   └── observer.py         # Dedicated EON society observer & historian
├── society/
│   ├── economy.py          # Currency issuance & token transaction ledger
│   ├── court.py            # Conflict resolution & arbitration rules
│   └── alliance.py         # Cross-clan treaties & agreements
├── memory/
│   ├── episodic.py         # Daily interaction logs & episodic memory
│   └── semantic.py         # Shared cultural norms & legal precedents
├── skills/
│   └── registry.py         # Tool registry & dynamically discovered skills
├── journals/
│   └── 2026-11-22.md       # Day 01 Society & Evolution Report
└── scripts/
    ├── run_society.py      # Run one tick / day of society evolution
    └── test_hardware.py    # Arc A380 benchmark & device diagnostic
```

---

## 🚀 Quickstart

```bash
# Set your GitHub PAT (required for push)
export GITHUB_PAT="<your_pat>"
# Optional: set sandbox password
export SANDBOX_PASSWORD="default_password"
# Run deployment script
bash scripts/deploy.sh
```

This will start the FastAPI server and run a sample evolution tick.

[Walkthrough](walkthrough.md)

### 1. Launch the OpenVINO Gemma 4 Server
```bash
python server/server.py --device GPU.1 --port 8000
```

### 2. Run Daily Society Step & Journal Commit
```bash
python scripts/run_society.py --day 1
```
