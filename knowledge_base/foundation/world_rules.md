# Foundation: EON World Rules & Invariants

The EON simulation operates under immutable physical and economic invariants. Agents cannot alter these rules; they must adapt within them.

## 1. The Token Conservation Law
- The civilization starts with exactly **10,000 tokens**.
- The centralized double-entry ledger enforces conservation: no tokens can be created ex nihilo, duplicated, or destroyed without an invariant assertion failure (`TokenConservationError`).
- Every transfer transfers tokens from sender to receiver: `Balance_A_new = Balance_A - X`, `Balance_B_new = Balance_B + X`.

## 2. Daily Survival Upkeep
- Each simulated day, each living agent faces metabolic survival costs:
  - **Food**: 5 tokens
  - **Water**: 4 tokens
  - **Shelter**: 3 tokens
  - **Healthcare**: 2 tokens
  - **Total Baseline**: 14 tokens/day.
- Survival Minimum: Food (5) + Water (4) = 9 tokens. Inability to pay 9 tokens forces agent into `CRITICAL` status.
- Three consecutive days in `CRITICAL` state results in permanent `DECEASED` status (simulated death).

## 3. Reproduction & Demographics
- Agents choose autonomously whether to reproduce.
- Global capacity limit: **≤ 10 births per simulated day**.
- Reproduction prerequisites: Both parents must maintain at least 28 tokens (2x daily upkeep) to ensure parental solvency.
- Children receive unique Greek names and inherit parental knowledge and cultural traits.
