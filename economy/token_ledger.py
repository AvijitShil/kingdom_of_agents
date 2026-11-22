"""
economy/token_ledger.py
Thin wrapper that re-exports SocietyLedger and TokenConservationError and
adds a convenience factory for a fresh conserved ledger.
"""

from society.economy import SocietyLedger, TokenConservationError


def new_conserved_ledger() -> SocietyLedger:
    """Return a SocietyLedger pre-loaded with the founding civilization."""
    ledger = SocietyLedger()
    ledger.register_founding_civilization()
    return ledger


__all__ = ["SocietyLedger", "TokenConservationError", "new_conserved_ledger"]
