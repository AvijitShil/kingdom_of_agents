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
