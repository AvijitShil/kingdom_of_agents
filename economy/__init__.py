"""
economy package — EON 2.0 conserved token economy.
Re-exports SocietyLedger and TokenConservationError for convenience.
"""

from society.economy import SocietyLedger, TokenConservationError

__all__ = ["SocietyLedger", "TokenConservationError"]
