"""
EON Institution System
Full institution lifecycle: creation, registration, army mechanics, and persistence.
"""

from __future__ import annotations

import json
import os
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InstitutionType(Enum):
    Business = "Business"
    Bank = "Bank"
    WageringHall = "WageringHall"
    Army = "Army"
    Court = "Court"
    Guild = "Guild"
    MutualAid = "MutualAid"


class InstitutionStatus(Enum):
    Active = "Active"
    Dissolved = "Dissolved"


# ---------------------------------------------------------------------------
# Base Institution dataclass
# ---------------------------------------------------------------------------

@dataclass
class Institution:
    institution_id: str
    name: str
    institution_type: InstitutionType
    owner: str
    treasury_account: str          # agent/account holding the treasury tokens
    treasury_balance: float
    members: List[str] = field(default_factory=list)
    status: InstitutionStatus = InstitutionStatus.Active
    founded_day: int = 0
    metadata: dict = field(default_factory=dict)

    def dissolve(self) -> None:
        self.status = InstitutionStatus.Dissolved


# ---------------------------------------------------------------------------
# Army Institution
# ---------------------------------------------------------------------------

@dataclass
class ArmyInstitution(Institution):
    """
    Specialised institution with soldier management and conflict simulation.
    morale is a float 0.0–1.0; starts at 0.8.
    """
    soldiers: List[str] = field(default_factory=list)
    morale: float = 0.8

    SIGNING_BONUS: int = 10
    DAILY_WAGE: int = 3

    def recruit(self, agent: str, ledger=None) -> bool:
        """
        Recruit an agent.  Pays SIGNING_BONUS from treasury.
        Returns False if treasury cannot cover the bonus.
        """
        if self.treasury_balance < self.SIGNING_BONUS:
            return False
        self.treasury_balance -= self.SIGNING_BONUS
        if agent not in self.soldiers:
            self.soldiers.append(agent)
        if agent not in self.members:
            self.members.append(agent)
        return True

    def pay_wages(self) -> List[str]:
        """
        Pay DAILY_WAGE tokens per soldier from treasury.
        Soldiers desert (are removed) if the treasury runs dry mid-payment.
        Returns list of agents who deserted.
        """
        deserted: List[str] = []
        still_serving: List[str] = []
        for soldier in list(self.soldiers):
            if self.treasury_balance >= self.DAILY_WAGE:
                self.treasury_balance -= self.DAILY_WAGE
                still_serving.append(soldier)
            else:
                deserted.append(soldier)
        self.soldiers = still_serving
        # Deserters leave the institution's member list too
        for d in deserted:
            if d in self.members:
                self.members.remove(d)
        return deserted

    def simulate_conflict(self, opponent: "ArmyInstitution") -> dict:
        """
        Abstract conflict resolution based on size * morale * random factor.
        Returns {"winner": str, "casualties": int, "outcome": str}
        """
        my_score = len(self.soldiers) * self.morale * random.uniform(0.7, 1.3)
        opp_score = len(opponent.soldiers) * opponent.morale * random.uniform(0.7, 1.3)

        total_combatants = len(self.soldiers) + len(opponent.soldiers)
        casualties = max(1, int(total_combatants * random.uniform(0.05, 0.25)))

        if my_score >= opp_score:
            winner = self.name
            outcome = f"{self.name} prevailed over {opponent.name}."
        else:
            winner = opponent.name
            outcome = f"{opponent.name} prevailed over {self.name}."

        return {
            "winner": winner,
            "casualties": casualties,
            "outcome": outcome,
        }


# ---------------------------------------------------------------------------
# Institution Registry
# ---------------------------------------------------------------------------

class InstitutionRegistry:
    """
    Central registry for all institutions in the simulation.
    Supports creation helpers, lookup, dissolution, and JSON persistence.
    """

    def __init__(self):
        self._institutions: Dict[str, Institution] = {}

    # ---- factory helpers ------------------------------------------------

    def create_institution(
        self,
        name: str,
        institution_type: InstitutionType,
        owner: str,
        treasury_account: str,
        treasury_balance: float = 0.0,
        founded_day: int = 0,
    ) -> Institution:
        inst_id = f"inst_{uuid.uuid4().hex[:8]}"
        inst = Institution(
            institution_id=inst_id,
            name=name,
            institution_type=institution_type,
            owner=owner,
            treasury_account=treasury_account,
            treasury_balance=treasury_balance,
            founded_day=founded_day,
        )
        self._institutions[inst_id] = inst
        return inst

    def create_army(
        self,
        name: str,
        owner: str,
        treasury_account: str,
        treasury_balance: float = 0.0,
        founded_day: int = 0,
        morale: float = 0.8,
    ) -> ArmyInstitution:
        inst_id = f"army_{uuid.uuid4().hex[:8]}"
        army = ArmyInstitution(
            institution_id=inst_id,
            name=name,
            institution_type=InstitutionType.Army,
            owner=owner,
            treasury_account=treasury_account,
            treasury_balance=treasury_balance,
            founded_day=founded_day,
            morale=morale,
        )
        self._institutions[inst_id] = army
        return army

    # ---- CRUD -----------------------------------------------------------

    def register(self, institution: Institution) -> None:
        self._institutions[institution.institution_id] = institution

    def get(self, institution_id: str) -> Optional[Institution]:
        return self._institutions.get(institution_id)

    def dissolve(self, institution_id: str) -> bool:
        inst = self._institutions.get(institution_id)
        if inst is None:
            return False
        inst.dissolve()
        return True

    def list_active(self) -> List[Institution]:
        return [i for i in self._institutions.values() if i.status == InstitutionStatus.Active]

    def list_all(self) -> List[Institution]:
        return list(self._institutions.values())

    # ---- persistence ----------------------------------------------------

    def save_state(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        records = {}
        for iid, inst in self._institutions.items():
            rec = {
                "institution_id": inst.institution_id,
                "name": inst.name,
                "institution_type": inst.institution_type.value,
                "owner": inst.owner,
                "treasury_account": inst.treasury_account,
                "treasury_balance": inst.treasury_balance,
                "members": inst.members,
                "status": inst.status.value,
                "founded_day": inst.founded_day,
                "metadata": inst.metadata,
                "is_army": isinstance(inst, ArmyInstitution),
            }
            if isinstance(inst, ArmyInstitution):
                rec["soldiers"] = inst.soldiers
                rec["morale"] = inst.morale
            records[iid] = rec
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def load_state(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)
        self._institutions = {}
        for iid, rec in records.items():
            is_army = rec.pop("is_army", False)
            inst_type = InstitutionType(rec["institution_type"])
            status = InstitutionStatus(rec["status"])
            if is_army:
                soldiers = rec.pop("soldiers", [])
                morale = rec.pop("morale", 0.8)
                inst = ArmyInstitution(
                    institution_id=rec["institution_id"],
                    name=rec["name"],
                    institution_type=inst_type,
                    owner=rec["owner"],
                    treasury_account=rec["treasury_account"],
                    treasury_balance=rec["treasury_balance"],
                    members=rec["members"],
                    status=status,
                    founded_day=rec["founded_day"],
                    metadata=rec.get("metadata", {}),
                    soldiers=soldiers,
                    morale=morale,
                )
            else:
                inst = Institution(
                    institution_id=rec["institution_id"],
                    name=rec["name"],
                    institution_type=inst_type,
                    owner=rec["owner"],
                    treasury_account=rec["treasury_account"],
                    treasury_balance=rec["treasury_balance"],
                    members=rec["members"],
                    status=status,
                    founded_day=rec["founded_day"],
                    metadata=rec.get("metadata", {}),
                )
            self._institutions[iid] = inst
        return True


default_registry = InstitutionRegistry()

