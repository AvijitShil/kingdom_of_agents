"""
tests/test_token_conservation.py
EON 2.0 — conserved token economy tests.
"""

import pytest
from society.economy import SocietyLedger, TokenConservationError
from economy.banking import EmergentBank, BankRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fresh_ledger() -> SocietyLedger:
    """Return a ledger with the founding civilization already registered."""
    ledger = SocietyLedger()
    ledger.register_founding_civilization()
    return ledger


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_initial_supply_is_10000():
    """register_founding_civilization() must produce exactly 10,000 tokens."""
    ledger = fresh_ledger()
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()   # must not raise


def test_transfer_conserves_tokens():
    """A transfer between two accounts must not alter the total supply."""
    ledger = fresh_ledger()
    ledger.transfer("Athena", "Hermes", 100, memo="test transfer")
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()


def test_no_overdraft():
    """Transferring more than the sender's balance returns False and leaves totals unchanged."""
    ledger = fresh_ledger()
    before = sum(ledger.balances.values())
    result = ledger.transfer("Athena", "Hermes", 999_999, memo="overdraft attempt")
    assert result is False
    assert sum(ledger.balances.values()) == before
    ledger.assert_conservation()


def test_loan_conserves_tokens():
    """issue_loan() moves tokens; total must stay at 10,000."""
    ledger = fresh_ledger()
    loan_id = ledger.issue_loan("public_infrastructure", "Orion", 500, 0.05, "startup loan")
    assert loan_id is not None
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()


def test_repayment_conserves_tokens():
    """repay_loan() moves tokens back; total must stay at 10,000."""
    ledger = fresh_ledger()
    loan_id = ledger.issue_loan("public_infrastructure", "Orion", 300, 0.05, "loan for repayment test")
    assert loan_id is not None
    result = ledger.repay_loan(loan_id, 200)
    assert result is True
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()


def test_tax_conserves_tokens():
    """collect_tax() is a transfer; total must stay at 10,000."""
    ledger = fresh_ledger()
    result = ledger.collect_tax("public_infrastructure", "Athena", 100, "annual tithe")
    assert result is True
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()


def test_bank_deposit_conserves():
    """Depositing into a bank moves tokens between accounts; total unchanged."""
    ledger = fresh_ledger()
    bank = EmergentBank(name="Apollo_Bank", owner="Athena", ledger=ledger)
    result = bank.deposit("Athena", 200)
    assert result is True
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()


def test_bank_loan_conserves():
    """Bank issuing a loan from reserves; total must stay at 10,000."""
    ledger = fresh_ledger()
    bank = EmergentBank(name="Apollo_Bank", owner="Athena", ledger=ledger,
                        reserve_ratio=0.10)
    # Fund the bank via deposits
    bank.deposit("Athena", 400)
    bank.deposit("Hermes", 400)
    # Issue a loan from the bank
    loan_id = bank.issue_loan("Prometheus", 300, memo="merchant venture")
    assert loan_id is not None
    assert sum(ledger.balances.values()) == 10_000
    ledger.assert_conservation()


def test_gini_coefficient():
    """Gini is 0 for equal wealth, > 0 for unequal wealth."""
    # Equal distribution
    ledger_eq = SocietyLedger()
    for name in ["A", "B", "C", "D"]:
        ledger_eq.balances[name] = 2500
    assert ledger_eq.get_wealth_gini() == 0.0

    # Unequal distribution
    ledger_uneq = SocietyLedger()
    ledger_uneq.balances = {"A": 9000, "B": 500, "C": 300, "D": 200}
    gini = ledger_uneq.get_wealth_gini()
    assert gini > 0


def test_founding_agents_named_correctly():
    """All 12 Greek founding agents must be present with 500 tokens each."""
    expected_agents = [
        "Athena", "Hermes", "Prometheus", "Themis", "Orion", "Dione",
        "Solon", "Thalia", "Lysander", "Phaedra", "Nikias", "Calliope"
    ]
    ledger = fresh_ledger()
    for name in expected_agents:
        assert name in ledger.balances, f"{name} not found in balances"
        assert ledger.balances[name] == 500, (
            f"{name} has {ledger.balances[name]} tokens, expected 500"
        )
