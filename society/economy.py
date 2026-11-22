"""
EON Economic System & Transaction Ledger
Manages token issuance, transfers between clans, and currency velocity.
"""

from typing import Dict, List, Any
import time


class SocietyLedger:
    def __init__(self, initial_supply: int = 10000):
        self.total_supply = initial_supply
        self.balances: Dict[str, int] = {}
        self.transactions: List[Dict[str, Any]] = []

    def register_account(self, account_id: str, initial_balance: int = 1000):
        if account_id not in self.balances:
            self.balances[account_id] = initial_balance

    def transfer(self, sender: str, recipient: str, amount: int, memo: str = "") -> bool:
        if self.balances.get(sender, 0) < amount:
            return False
        self.balances[sender] -= amount
        self.balances[recipient] = self.balances.get(recipient, 0) + amount
        self.transactions.append({
            "timestamp": int(time.time()),
            "from": sender,
            "to": recipient,
            "amount": amount,
            "memo": memo
        })
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
        return True
