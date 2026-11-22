# EON 2.0 — Economic Record Format

## Overview

The `journal/economy/` directory stores human-readable and machine-parseable records of all economic events that occur inside EON's conserved token economy.

Every record corresponds to a **transaction** (transfer, loan issuance, loan repayment, tax collection, or bank deposit/withdrawal) that happened in a `SocietyLedger` instance.

---

## Invariant

> **Total tokens = 10,000 at all times.**  
> No record may cause `sum(balances.values()) ≠ 10,000`.  
> Any violation raises `TokenConservationError`.

---

## Record Fields

Each economic record is a JSON object (or equivalent Python dict) with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `tx_id` | `str` (UUID4) | Unique transaction identifier |
| `date` | `str` (ISO 8601 UTC) | Wall-clock time of the transaction |
| `timestamp` | `int` | Unix epoch seconds |
| `from` | `str` | Sender account ID |
| `to` | `str` | Receiver account ID |
| `amount` | `int` | Tokens transferred (must be > 0) |
| `memo` | `str` | Human-readable purpose; tags prepended in brackets |
| `balances_snapshot` | `dict` | `{sender: balance, receiver: balance}` *after* the transaction |

### Memo Tag Conventions

| Prefix | Meaning |
|--------|---------|
| `[LOAN:<loan_id>]` | Token transfer constituting a loan issuance |
| `[REPAYMENT:<loan_id>]` | Token transfer constituting a loan repayment |
| `[TAX]` | Tax collection |
| `[DEPOSIT→<bank>]` | Agent deposit into an EmergentBank |
| `[WITHDRAW←<bank>]` | Agent withdrawal from an EmergentBank |
| `[BANK_LOAN:<bank>]` | Bank-issued loan from pooled reserves |

---

## Loan Records

Loans are stored separately in `SocietyLedger.loans` (and persisted in the JSON snapshot):

| Field | Type | Description |
|-------|------|-------------|
| `loan_id` | `str` (UUID4) | Matches the `[LOAN:<id>]` tag in transactions |
| `lender` | `str` | Account providing the tokens |
| `borrower` | `str` | Account receiving the tokens |
| `principal` | `int` | Original loan amount |
| `outstanding` | `int` | Remaining balance (decremented on repayment) |
| `interest_rate` | `float` | Annual rate (e.g., `0.05` = 5%) |
| `memo` | `str` | Loan purpose |
| `issued_at` | `str` (ISO 8601) | Loan creation time |

---

## Example Transaction

```json
{
  "tx_id": "a3f7c2d1-8b4e-4f6a-9c0d-1e2f3a4b5c6d",
  "date": "2026-11-22T21:00:00Z",
  "timestamp": 1764039600,
  "from": "Athena",
  "to": "Hermes",
  "amount": 100,
  "memo": "payment for oracle consultation",
  "balances_snapshot": {
    "Athena": 400,
    "Hermes": 600
  }
}
```

---

## Founding Civilization Allocation

| Account | Tokens | Purpose |
|---------|--------|---------|
| Athena | 500 | Founding agent |
| Hermes | 500 | Founding agent |
| Prometheus | 500 | Founding agent |
| Themis | 500 | Founding agent |
| Orion | 500 | Founding agent |
| Dione | 500 | Founding agent |
| Solon | 500 | Founding agent |
| Thalia | 500 | Founding agent |
| Lysander | 500 | Founding agent |
| Phaedra | 500 | Founding agent |
| Nikias | 500 | Founding agent |
| Calliope | 500 | Founding agent |
| public_infrastructure | 2,000 | Shared public goods |
| market_liquidity | 1,000 | Trade facilitation reserve |
| emergency_reserve | 1,000 | Crisis response fund |
| **Total** | **10,000** | **Fixed forever** |

---

## File Structure

```
journal/economy/
├── README.md           ← this file
└── <date>/
    └── ledger_snapshot_<timestamp>.json   ← periodic or event-triggered snapshots
```

Snapshots are written via `SocietyLedger.save_state(filepath)` and can be replayed with `SocietyLedger.load_state(filepath)`.
