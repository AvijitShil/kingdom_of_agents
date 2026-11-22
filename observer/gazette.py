"""
observer/gazette.py
EON 2.0 â€” Historical newspaper-style Daily Gazette renderer.
"""

import os
from typing import List, Dict, Optional
from observer.chronos import Chronos, EventType


class GazetteRenderer:
    """Renders the Daily Civilization Gazette in historical newspaper format."""

    def __init__(self, chronos: Chronos):
        self.chronos = chronos

    def render_daily_gazette(
        self,
        sim_day: int,
        sim_date: str,
        ledger_summary: dict,
        survival_summary: dict,
        agora_highlights: list,
        extra_context: Optional[dict] = None,
    ) -> str:
        """
        Render a full historical newspaper-style gazette for the day.
        Uses running profiles + day's events.
        """
        lines = []
        lines.append("# THE EON CIVILIZATION GAZETTE")
        lines.append(f"## Simulated Date: {sim_date} | Simulation Day {sim_day}")
        lines.append("*Chronicled by Chronos, the Impartial Observer*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Demographics
        alive = survival_summary.get("alive", [])
        deceased = survival_summary.get("deceased", [])
        critical = survival_summary.get("critical", [])
        newborns = [e for e in self.chronos.get_days_events() if e.event_type == EventType.BIRTH]

        lines.append("## 📊 DEMOGRAPHICS")
        lines.append(f"- **Population**: {len(alive)} living citizens")
        lines.append(f"- **Deaths today**: {len(deceased)}")
        lines.append(f"- **Births today**: {len(newborns)}")
        for nb in newborns:
            lines.append(f"  - {nb.outcome}")
        lines.append("")

        # 2. Kingdoms & Political Order
        lines.append("## 👑 KINGDOMS & POLITICAL ORDER")
        if self.chronos.kingdom_profiles:
            for kname, kp in self.chronos.kingdom_profiles.items():
                lines.append(f"### Kingdom of {kp.name}")
                lines.append(f"- **Ruler**: {kp.ruler}  |  **Population**: {kp.population}")
                lines.append(f"- **Treasury**: {kp.treasury_balance} tokens  |  **Army**: {kp.army_size} soldiers")
                lines.append(f"- **Political Condition**: {kp.political_condition}")
        else:
            lines.append("*No kingdoms have yet been declared; founding citizens deliberate in free assembly.*")
        lines.append("")

        # 3. Clans
        lines.append("## 🏕️ CLANS & FACTIONS")
        if self.chronos.clan_profiles:
            for cname, cp in self.chronos.clan_profiles.items():
                lines.append(f"- **{cp.name}**: Leader {cp.leader}, {len(cp.members)} members, Gini {cp.wealth_gini:.2f}")
        else:
            lines.append("*Citizens operate across kinship networks without centralized clan monopolies.*")
        lines.append("")

        # 4. Economy & Token Ledger
        lines.append("## 💰 ECONOMY & TOKEN LEDGER")
        lines.append(f"- **Total supply**: {ledger_summary.get('total_circulation', 10000)} tokens (strictly conserved)")
        lines.append(f"- **Transactions today**: {ledger_summary.get('transaction_count', 0)}")
        lines.append(f"- **Wealth velocity**: {ledger_summary.get('velocity', '0.00x')}")
        tx_events = [e for e in self.chronos.get_days_events() if e.event_type == EventType.TRANSACTION]
        for tx in tx_events[:5]:
            lines.append(f"  - {tx.executed_action}: {tx.outcome}")
        lines.append("")

        # 5. Agora — Public Discourse
        lines.append("## 🏛️ AGORA — PUBLIC DISCOURSE")
        for highlight in agora_highlights[:8]:
            lines.append(f"- {highlight}")
        if not agora_highlights:
            lines.append("*The Agora was quiet today.*")
        lines.append("")

        # 6. Cultural Developments
        lines.append("## 🎭 CULTURAL DEVELOPMENTS")
        cultural_events = [e for e in self.chronos.get_days_events() if e.event_type == EventType.CULTURAL_TRAIT_EMERGENCE]
        for ce in cultural_events:
            lines.append(f"- **New practice emerged**: {ce.outcome}")
        if not cultural_events:
            lines.append("*No new cultural traits emerged today; ancestral traditions preserved.*")
        lines.append("")

        # 7. Conflicts & Unrest
        lines.append("## ⚔️ CONFLICTS & DISPUTES")
        conflict_events = [e for e in self.chronos.get_days_events() if e.event_type in (EventType.CONFLICT, EventType.REVOLT, EventType.PROTEST)]
        for ce in conflict_events:
            lines.append(f"- **{ce.event_type.value}**: {ce.outcome}")
        if not conflict_events:
            lines.append("*Civil harmony maintained throughout the day.*")
        lines.append("")

        # 8. Survival Alerts
        lines.append("## ⚠️ SURVIVAL ALERTS")
        if critical:
            for name in critical:
                lines.append(f"- 🔴 **{name}** is in CRITICAL condition")
        if deceased:
            for name in deceased:
                lines.append(f"- ☠️ **{name}** has perished")
        if not critical and not deceased:
            lines.append("*All citizens successfully secured daily food, water, and shelter.*")
        lines.append("")

        # 9. Next Day Watchlist
        lines.append("## 🔭 EVENTS TO WATCH TOMORROW")
        if critical:
            lines.append(f"- Survival status of critical citizens: {', '.join(critical)}")
        lines.append("- Agora market openings and credit settlements.")
        lines.append("- New trade partnerships and family developments.")
        lines.append("")

        lines.append("---")
        lines.append("*End of Gazette. Historical archives preserved by Chronos.*")

        return "\n".join(lines)

    def save_gazette(self, gazette_text: str, sim_date: str) -> str:
        """Save gazette to journal/daily/YYYY-MM-DD.md. Returns path."""
        daily_dir = os.path.join(self.chronos.journal_root, "daily")
        os.makedirs(daily_dir, exist_ok=True)
        path = os.path.join(daily_dir, f"{sim_date}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(gazette_text)
        return path
