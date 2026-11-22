"""
EON Economic System & Transaction Ledger
Manages token issuance, transfers between clans, and currency velocity.
EON 2.0: Conserved token economy — total supply is always exactly 10,000.
"""

from typing import Dict, List, Any, Optional
import time
import uuid


class TokenConservationError(Exception):
    """Raised when the total token supply deviates from the fixed supply."""
    pass


class SocietyLedger:
    FIXED_SUPPLY = 10_000

    FOUNDING_AGENTS = [
        "Athena", "Hermes", "Prometheus", "Themis", "Orion", "Dione",
        "Solon", "Thalia", "Lysander", "Phaedra", "Nikias", "Calliope"
    ]

    def __init__(self, initial_supply: int = 10000):
        self.total_supply = initial_supply
        self.balances: Dict[str, int] = {}
        self.transactions: List[Dict[str, Any]] = []
        # Loan records: loan_id -> dict
        self.loans: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Existing API (backward-compatible)
    # ------------------------------------------------------------------

    def register_account(self, account_id: str, initial_balance: int = 1000):
        if account_id not in self.balances:
            self.balances[account_id] = initial_balance

    def transfer(self, sender: str, recipient: str, amount: int, memo: str = "") -> bool:
        if self.balances.get(sender, 0) < amount:
            return False
        self.balances[sender] -= amount
        self.balances[recipient] = self.balances.get(recipient, 0) + amount
        tx = {
            "tx_id": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "from": sender,
            "to": recipient,
            "amount": amount,
            "memo": memo,
            "balances_snapshot": {sender: self.balances[sender],
                                   recipient: self.balances[recipient]},
        }
        self.transactions.append(tx)
        return True

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_circulation": sum(self.balances.values()),
            "transaction_count": len(self.transactions),
            "balances": self.balances,
            "velocity": f"{len(self.transactions) / max(1, len(self.balances)):.2f}x"
        }

    def save_state(self, filepath: str) -> None:
        """Persist account balances and transaction history to JSON."""
        import json, os
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {
            "total_supply": self.total_supply,
            "balances": self.balances,
            "transactions": self.transactions,
            "loans": self.loans,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        """Load account balances and transaction history from JSON."""
        import json, os
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.total_supply = data.get("total_supply", self.total_supply)
        self.balances = data.get("balances", self.balances)
        self.transactions = data.get("transactions", self.transactions)
        self.loans = data.get("loans", self.loans)
        return True

    # ------------------------------------------------------------------
    # EON 2.0 — Conservation & founding civilization
    # ------------------------------------------------------------------

    def assert_conservation(self) -> None:
        """Raise TokenConservationError if the total token supply != FIXED_SUPPLY."""
        total = sum(self.balances.values())
        if total != self.FIXED_SUPPLY:
            raise TokenConservationError(
                f"Token conservation violated: expected {self.FIXED_SUPPLY}, got {total}"
            )

    def register_founding_civilization(self) -> None:
        """
        Bootstrap the conserved economy with 12 Greek founding agents (500 each)
        plus three system reserves, summing to exactly 10,000.

          12 agents × 500 = 6,000
          public_infrastructure  = 2,000
          market_liquidity       = 1,000
          emergency_reserve      = 1,000
          ─────────────────────────────
          Total                  = 10,000
        """
        # Reset everything so we start clean
        self.balances = {}
        self.transactions = []
        self.loans = {}

        for name in self.FOUNDING_AGENTS:
            self.balances[name] = 500          # 12 × 500 = 6,000

        self.balances["public_infrastructure"] = 2000
        self.balances["market_liquidity"] = 1000
        self.balances["emergency_reserve"] = 1000

        self.assert_conservation()  # sanity-check immediately

    # ------------------------------------------------------------------
    # EON 2.0 — Loan system
    # ------------------------------------------------------------------

    def issue_loan(
        self,
        lender: str,
        borrower: str,
        amount: int,
        interest_rate: float,
        memo: str = "",
    ) -> Optional[str]:
        """
        Transfer *amount* tokens from lender to borrower and record a debt.
        Returns the loan_id on success, None if lender has insufficient funds.
        """
        if self.balances.get(lender, 0) < amount:
            return None

        loan_id = str(uuid.uuid4())
        ok = self.transfer(lender, borrower, amount, memo=f"[LOAN:{loan_id}] {memo}")
        if not ok:
            return None

        self.loans[loan_id] = {
            "loan_id": loan_id,
            "lender": lender,
            "borrower": borrower,
            "principal": amount,
            "outstanding": amount,
            "interest_rate": interest_rate,
            "memo": memo,
            "issued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return loan_id

    def repay_loan(self, loan_id: str, amount: int) -> bool:
        """
        Transfer *amount* tokens back from borrower to lender, reduce outstanding debt.
        Returns True on success, False if loan not found or insufficient balance.
        """
        loan = self.loans.get(loan_id)
        if loan is None:
            return False

        borrower = loan["borrower"]
        lender = loan["lender"]
        repay_amount = min(amount, loan["outstanding"])

        ok = self.transfer(borrower, lender, repay_amount,
                           memo=f"[REPAYMENT:{loan_id}]")
        if not ok:
            return False

        loan["outstanding"] -= repay_amount
        return True

    # ------------------------------------------------------------------
    # EON 2.0 — Tax system
    # ------------------------------------------------------------------

    def collect_tax(
        self,
        taxing_entity: str,
        citizen: str,
        amount: int,
        memo: str = "",
    ) -> bool:
        """Transfer *amount* tokens from citizen to taxing_entity as a tax."""
        return self.transfer(citizen, taxing_entity, amount,
                             memo=f"[TAX] {memo}")

    # ------------------------------------------------------------------
    # EON 2.0 — Wealth inequality
    # ------------------------------------------------------------------

    def get_wealth_gini(self) -> float:
        """
        Compute the Gini coefficient of agent token balances.
        Returns 0.0 for perfect equality, approaching 1.0 for maximum inequality.
        """
        values = sorted(self.balances.values())
        n = len(values)
        if n == 0:
            return 0.0
        total = sum(values)
        if total == 0:
            return 0.0
        cumulative = 0
        gini_sum = 0
        for i, v in enumerate(values, 1):
            cumulative += v
            gini_sum += cumulative
        # Standard formula: G = (2 * Σ(rank * value) / (n * total)) - (n+1)/n
        rank_weighted = sum((i + 1) * v for i, v in enumerate(values))
        gini = (2 * rank_weighted) / (n * total) - (n + 1) / n
        return round(gini, 6)
