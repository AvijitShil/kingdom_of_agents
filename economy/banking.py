"""
economy/banking.py
EON 2.0 — Emergent Banking System.

EmergentBank holds deposits from agents, maintains a reserve_ratio,
and can issue loans from its pooled reserves — all while keeping tokens
conserved inside the shared SocietyLedger.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from society.economy import SocietyLedger, TokenConservationError


@dataclass
class EmergentBank:
    """
    A decentralised bank that emerges from agent cooperation.

    All token movements are routed through the shared SocietyLedger so the
    total supply remains conserved.  The bank itself is an account in the
    ledger (keyed by its *name*).
    """

    name: str
    owner: str
    ledger: SocietyLedger
    interest_rate: float = 0.05        # annual; applied per repayment call
    reserve_ratio: float = 0.10        # fraction of deposits kept as reserve

    # deposits[agent_id] = tokens agent has placed in this bank
    deposits: Dict[str, int] = field(default_factory=dict)
    # list of active loan records issued by this bank
    loans: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        # Ensure the bank has a ledger account (zero balance — tokens flow in
        # through deposits)
        if self.name not in self.ledger.balances:
            self.ledger.balances[self.name] = 0

    # ------------------------------------------------------------------
    # Deposit / withdraw
    # ------------------------------------------------------------------

    def deposit(self, agent_id: str, amount: int) -> bool:
        """
        Move *amount* tokens from agent → bank reserve.
        Returns True on success.
        """
        ok = self.ledger.transfer(agent_id, self.name, amount,
                                  memo=f"[DEPOSIT→{self.name}]")
        if ok:
            self.deposits[agent_id] = self.deposits.get(agent_id, 0) + amount
        return ok

    def withdraw(self, agent_id: str, amount: int) -> bool:
        """
        Move *amount* tokens from bank reserve → agent.
        Only allowed up to what the agent has deposited.
        """
        deposited = self.deposits.get(agent_id, 0)
        if amount > deposited:
            return False
        ok = self.ledger.transfer(self.name, agent_id, amount,
                                  memo=f"[WITHDRAW←{self.name}]")
        if ok:
            self.deposits[agent_id] -= amount
        return ok

    # ------------------------------------------------------------------
    # Lending
    # ------------------------------------------------------------------

    def issue_loan(self, borrower: str, amount: int, memo: str = "") -> Optional[str]:
        """
        Issue a loan from the bank's reserve to *borrower*.
        Respects reserve_ratio: lendable = bank_balance - reserve.
        Returns loan_id on success, None on failure.
        """
        bank_balance = self.ledger.balances.get(self.name, 0)
        total_deposits = sum(self.deposits.values())
        reserve_required = int(total_deposits * self.reserve_ratio)
        lendable = max(0, bank_balance - reserve_required)

        if amount > lendable:
            return None

        loan_id = self.ledger.issue_loan(
            self.name, borrower, amount, self.interest_rate,
            memo=f"[BANK_LOAN:{self.name}] {memo}"
        )
        if loan_id is None:
            return None

        self.loans.append({
            "loan_id": loan_id,
            "borrower": borrower,
            "amount": amount,
            "issued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return loan_id

    def collect_repayment(self, loan_id: str, amount: int) -> bool:
        """Route a repayment through SocietyLedger back to the bank."""
        return self.ledger.repay_loan(loan_id, amount)


# ---------------------------------------------------------------------------
# BankRegistry — singleton catalogue of all banks in the simulation
# ---------------------------------------------------------------------------

class BankRegistry:
    """Global registry of EmergentBank instances."""

    def __init__(self):
        self._banks: Dict[str, EmergentBank] = {}

    def register_bank(self, bank: EmergentBank) -> None:
        if bank.name in self._banks:
            raise ValueError(f"Bank '{bank.name}' is already registered.")
        self._banks[bank.name] = bank

    def get_bank(self, name: str) -> Optional[EmergentBank]:
        return self._banks.get(name)

    def list_banks(self) -> List[str]:
        return list(self._banks.keys())


# Module-level default registry
default_registry = BankRegistry()
