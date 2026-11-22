import uuid, json, time, os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class EventType(Enum):
    SPEECH = "SPEECH"
    TRANSACTION = "TRANSACTION"
    BIRTH = "BIRTH"
    DEATH = "DEATH"
    MARRIAGE = "MARRIAGE"
    EDUCATION = "EDUCATION"
    CLAN_FORMATION = "CLAN_FORMATION"
    KINGDOM_FORMATION = "KINGDOM_FORMATION"
    INSTITUTION_CREATION = "INSTITUTION_CREATION"
    CONFLICT = "CONFLICT"
    TREATY = "TREATY"
    FAIR = "FAIR"
    CULTURAL_TRAIT_EMERGENCE = "CULTURAL_TRAIT_EMERGENCE"
    SURVIVAL_STATE_CHANGE = "SURVIVAL_STATE_CHANGE"
    ELECTION = "ELECTION"
    PROTEST = "PROTEST"
    REVOLT = "REVOLT"

@dataclass
class ChronosEvent:
    event_id: str              # UUID4
    event_type: EventType
    sim_day: int               # simulation day number
    sim_date: str              # e.g. "2026-11-26"
    agents: List[str]          # agents involved
    speech: str                # what agents said/proposed
    intent: str                # what they intended to achieve
    executed_action: str       # what actually happened
    outcome: str               # result/consequence
    metadata: dict             # extra context
    logged_at: str             # real-world timestamp

@dataclass
class AgentRunningProfile:
    name: str
    birth_day: int
    parents: List[str]
    children: List[str]
    spouse: Optional[str]
    clan: Optional[str]
    kingdom: Optional[str]
    wealth_history: List[dict]   # [{"day": int, "balance": int}]
    survival_state: str
    cultural_traits: List[str]   # trait_ids adopted
    businesses: List[str]        # institution_ids owned
    notable_events: List[str]    # event_ids
    last_updated_day: int

@dataclass
class ClanRunningProfile:
    name: str
    leader: str
    members: List[str]
    formation_day: int
    treasury_balance: int
    wealth_gini: float
    notable_events: List[str]
    last_updated_day: int

@dataclass
class KingdomRunningProfile:
    name: str
    ruler: str
    member_clans: List[str]
    population: int
    treasury_balance: int
    army_size: int
    formation_day: int
    political_condition: str   # "stable", "unrest", "at_war", "collapsed"
    notable_events: List[str]
    last_updated_day: int

class Chronos:
    """
    Independent civilization observer. Never influences agents.
    Logs all events with speech/intent/execution/outcome distinction.
    Maintains running profiles updated only on meaningful change.
    Persists all records across restarts.
    """
    
    def __init__(self, journal_root: str = "journal"):
        self.journal_root = journal_root
        self._ensure_dirs()
        self.agent_profiles: Dict[str, AgentRunningProfile] = {}
        self.clan_profiles: Dict[str, ClanRunningProfile] = {}
        self.kingdom_profiles: Dict[str, KingdomRunningProfile] = {}
        self._day_events: List[ChronosEvent] = []  # events for current day
    
    def _ensure_dirs(self):
        for sub in ["daily", "agents", "generations", "institutions", 
                    "kingdoms", "economy", "transcripts"]:
            os.makedirs(os.path.join(self.journal_root, sub), exist_ok=True)
    
    def log_event(self, event_type: EventType, sim_day: int, sim_date: str,
                  agents: List[str], speech: str, intent: str,
                  executed_action: str, outcome: str,
                  metadata: dict = None) -> str:
        """Log a civilization event. Returns event_id."""
        event = ChronosEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            sim_day=sim_day,
            sim_date=sim_date,
            agents=agents,
            speech=speech,
            intent=intent,
            executed_action=executed_action,
            outcome=outcome,
            metadata=metadata or {},
            logged_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        self._day_events.append(event)
        # Append to agent-specific logs
        for agent in agents:
            self._append_agent_log(agent, event)
        return event.event_id
    
    def _append_agent_log(self, agent: str, event: ChronosEvent) -> None:
        """Append event to agent's jsonl file."""
        path = os.path.join(self.journal_root, "agents", f"{agent}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event_id": event.event_id,
                "type": event.event_type.value,
                "day": event.sim_day,
                "date": event.sim_date,
                "speech": event.speech,
                "intent": event.intent,
                "executed_action": event.executed_action,
                "outcome": event.outcome,
                "metadata": event.metadata
            }) + "\n")
    
    def update_agent_profile(self, name: str, **kwargs) -> None:
        """Update agent running profile only when meaningful change occurs."""
        if name not in self.agent_profiles:
            self.agent_profiles[name] = AgentRunningProfile(
                name=name, birth_day=kwargs.get("birth_day", 0),
                parents=kwargs.get("parents", []),
                children=kwargs.get("children", []),
                spouse=kwargs.get("spouse"),
                clan=kwargs.get("clan"),
                kingdom=kwargs.get("kingdom"),
                wealth_history=[], survival_state="SECURE",
                cultural_traits=[], businesses=[], notable_events=[],
                last_updated_day=0
            )
        profile = self.agent_profiles[name]
        changed = False
        for k, v in kwargs.items():
            if hasattr(profile, k) and getattr(profile, k) != v:
                setattr(profile, k, v)
                changed = True
        if changed:
            profile.last_updated_day = kwargs.get("day", profile.last_updated_day)
        # Persist profile
        path = os.path.join(self.journal_root, "agents", f"{name}_profile.json")
        with open(path, "w", encoding="utf-8") as f:
            import dataclasses
            json.dump(dataclasses.asdict(profile), f, indent=2)
    
    def log_generation(self, child: str, parent1: str, parent2: str,
                       inherited_traits: list, day: int, sim_date: str) -> None:
        """Log birth/generation event."""
        path = os.path.join(self.journal_root, "generations", f"gen_day{day:03d}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "child": child, "parent1": parent1, "parent2": parent2,
                "inherited_traits": inherited_traits, "day": day, "date": sim_date
            }) + "\n")
    
    def flush_day(self, sim_day: int, sim_date: str) -> None:
        """Write all day's events to transcripts. Called at end of each day."""
        path = os.path.join(self.journal_root, "transcripts", f"{sim_date}_events.jsonl")
        import dataclasses
        with open(path, "w", encoding="utf-8") as f:
            for ev in self._day_events:
                f.write(json.dumps(dataclasses.asdict(ev), default=str) + "\n")
        self._day_events = []
    
    def get_days_events(self) -> List[ChronosEvent]:
        return list(self._day_events)
    
    def load_agent_profiles(self) -> None:
        """Reload all agent profiles from disk on restart."""
        agents_dir = os.path.join(self.journal_root, "agents")
        for fname in os.listdir(agents_dir):
            if fname.endswith("_profile.json"):
                with open(os.path.join(agents_dir, fname), "r") as f:
                    data = json.load(f)
                profile = AgentRunningProfile(**data)
                self.agent_profiles[profile.name] = profile
