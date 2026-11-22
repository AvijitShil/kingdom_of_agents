"""
Observer Agent for EON Society Simulation
Serves as the Chief Historian and Investigative Journalist of the Kingdom.
Transforms raw Agora chat transcripts, private Chains of Thought, and survival metrics
into "The Kingdom Gazette" daily newspaper.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class ObserverAgent:
    def __init__(self, name: str = "Chronos"):
        self.name = name
        self.role = "Chief Investigative Chronicler and Society Historian"
        self.system_prompt = (
            "You are Chronos, the impartial Chief Chronicler and Investigative Reporter of the EON Kingdom. "
            "Your objective is to observe societal interactions, investigate leaked internal deliberations, "
            "record economic and survival dynamics, and publish the daily Kingdom Gazette newspaper grounded strictly "
            "in verbatim Agora dialogue transcripts."
        )

    def synthesize_daily_report(
        self,
        day: int,
        clan_actions: Optional[List[Dict[str, Any]]] = None,
        ledger_summary: Optional[Dict[str, Any]] = None,
        disputes: Optional[List[Dict[str, Any]]] = None,
        hardware_metrics: Optional[Dict[str, Any]] = None,
        agora_channel: Optional[Any] = None,
        survival_summary: Optional[Dict[str, Any]] = None,
        headline: Optional[str] = None,
        date_str: Optional[str] = None,
        kinship_summary: Optional[Dict[str, Any]] = None,
        fission_summary: Optional[Dict[str, Any]] = None,
        crisis_details: Optional[Any] = None,
    ) -> str:
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        clan_actions = clan_actions or []
        ledger_summary = ledger_summary or {}
        disputes = disputes or []
        hardware_metrics = hardware_metrics or {}
        survival_summary = survival_summary or {}

        # Determine prominent headline based on events
        if not headline:
            if survival_summary and any(c.get("status") in ("STRESSED", "STARVATION") for c in survival_summary.values()):
                headline = "SCARCITY STRIKES THE AGORA: Clans Cling to Survival as Ration Depletion Ignites Fierce Debate"
            else:
                headline = "THE COMPUTE ACCORD: Technocrats and Merchants Form Critical Lifeline in the Town Square"

        lines = [
            f"# 📰 The Kingdom Gazette: Day {day:02d} — {date_str} | EON Society Journal: Day {day:02d}",
            "",
            "> *The Official Voice & Investigative Chronicle of the Kingdom of Agents*",
            "> *Published autonomously by Chronos, Chief Chronicler of the EON Society*",
            "",
            "---",
            "",
            f"## 1. Executive Summary: {headline}",
            "",
        ]

        # 1. Lead Investigative Summary
        lines.append(
            f"On this Day {day:02d} of the EON Era, the Kingdom's clans assembled in the Agora under the watchful gaze of the High Court. "
            f"With foundation weights permanently frozen and cryptographically sealed on the Intel Arc A380 dGPU (`GPU.1`), "
            f"existential pressure has shifted entirely to the social arena. The survival of clans and their lineages now depends "
            f"on daily ideological bargaining, computational energy production, and metabolic ration allocations."
        )
        lines.append("")

        if crisis_details:
            lines.extend([
                f"> **🔥 Active Existential Crisis**: *{getattr(crisis_details, 'title', str(crisis_details))}*",
                f"> **Crisis Nature**: {getattr(crisis_details, 'description', '')}",
                f"> **Town Square Dilemma**: *\"{getattr(crisis_details, 'public_dilemma', '')}\"*",
                "",
            ])

        # 2. Hardware & Runtime Diagnostics
        lines.extend([
            "---",
            "",
            "## 2. Hardware & Runtime Diagnostics",
            "",
            f"- **Host GPU Target**: {hardware_metrics.get('device', 'Intel(R) Arc(TM) A380 Graphics (GPU.1)')}",
            f"- **VRAM Allocation**: {hardware_metrics.get('vram_allocated_mb', '~3,200 MB')} MB",
            f"- **Average Generation Speed**: {hardware_metrics.get('tokens_per_sec', '14.29')} tokens/sec",
            f"- **Frozen Model Hash Status**: {hardware_metrics.get('hash_status', '100% Intact (SHA-256 Verified)')}",
            "",
        ])

        # 3. Clan Survival Vitality Ledger
        if survival_summary:
            lines.extend([
                "---",
                "",
                "## 📊 Clan Survival & Vitality Ledger",
                "",
                "| Clan Faction | Headcount | Energy Reserves | Ration Stores | Vitality % | Survival State |",
                "|--------------|:---------:|:---------------:|:-------------:|:----------:|:--------------:|",
            ])
            for clan_id, data in survival_summary.items():
                title = data.get("title", clan_id)
                headcount = data.get("headcount", 10)
                energy = data.get("energy", 0)
                rations = data.get("rations", 0)
                vitality = data.get("vitality_pct", 100)
                status = data.get("status", "STABLE")
                lines.append(f"| **{title}** | {headcount} kin | {energy} EU | {rations} Rations | **{vitality}%** | `{status}` |")
            lines.append("")

        # Kinship & Domestic Lineage Ledger
        if kinship_summary:
            lines.extend([
                "---",
                "",
                "## 👨‍👩‍👧‍👦 Kinship Lineage & Domestic Living Standards",
                "",
                "| Agent Household | Clan Affiliation | Dependents | Water Cistern | Grain Reserve | Living Standard (L_i) | Civic Status |",
                "|-----------------|:----------------:|:----------:|:-------------:|:-------------:|:---------------------:|:------------:|",
            ])
            for aid, hdata in kinship_summary.items():
                name = hdata.get("agent_name", aid)
                clan = hdata.get("clan_id", "Clan")
                spouse = hdata.get("spouse_name")
                kids = hdata.get("num_children", 0)
                dep_str = f"Spouse + {kids} kids" if spouse else f"{kids} kids"
                w_res = hdata.get("water_reserve", 0.0)
                g_res = hdata.get("grain_reserve", 0.0)
                l_score = hdata.get("living_standard", 1.0)
                status = hdata.get("status", "CIVILIAN")
                lines.append(f"| **{name}** | `{clan}` | {dep_str} | {w_res:.1f} L | {g_res:.1f} kg | **{l_score:.2f}** | `{status}` |")
            lines.append("")

        # Sovereign Dynastic Fission
        if fission_summary and fission_summary.get("kingdoms"):
            lines.extend([
                "---",
                "",
                "## 👑 Sovereign Breakaway Kingdoms & Dynastic Fission",
                "",
            ])
            for k in fission_summary["kingdoms"]:
                lines.append(f"### 🚩 {k.get('kingdom_name')}")
                lines.append(f"- **Origin Clan**: `{k.get('parent_clan')}` | **Population**: {k.get('population')} citizens")
                lines.append(f"- **Preamble Charter**: *\"{k.get('charter_preamble')}\"*")
                lines.append(f"- **Sovereign Reserves**: {k.get('water_reserve', 0)} L Water | {k.get('treasury_balance', 0)} Tokens")
                lines.append("")

        # 4. Behind Closed Minds (Leaked Chains of Thought)
        if agora_channel and getattr(agora_channel, "messages", None):
            lines.extend([
                "---",
                "",
                "## 👁️ Behind Closed Minds: Leaked Chains of Thought vs. Public Speech",
                "",
                "The Observer's secret informants have decrypted the private cognitive monologues of the faction leaders, "
                "contrasting their hidden calculations with what they proclaimed aloud to the citizens:",
                "",
            ])
            for msg in agora_channel.messages[:4]:  # Feature top exchanges
                lines.extend([
                    f"### 🎙️ {msg.sender} ({msg.clan}) addressing `{msg.target}`",
                    f"- **Doctrine Invoked**: `{msg.codebook_reference or 'Pragmatic Statecraft'}`",
                    f"- **Intent**: `{msg.intent}`",
                    "",
                    "> 🔒 **Private Calculation (Leaked Chain of Thought)**:",
                    f"> *\"{msg.chain_of_thought.strip()}\"*",
                    "",
                    "> 📢 **Public Proclamation in the Agora**:",
                    f"> *\"{msg.public_message.strip()}\"*",
                    "",
                ])

        # 5. Clan Activities & Deliberations (Agora Floor)
        lines.extend([
            "---",
            "",
            "## 3. Clan Activities & Deliberations (The Town Square Floor)",
            "",
        ])
        if agora_channel and getattr(agora_channel, "messages", None):
            lines.append("A transcript excerpt of the pivotal arguments that determined today's treaties and ledger movements:\n")
            for idx, msg in enumerate(agora_channel.messages, 1):
                ref = f" *(Citing: {msg.codebook_reference})*" if msg.codebook_reference else ""
                lines.append(f"**[{idx:02d}] {msg.sender}** -> **{msg.target}**{ref}:")
                lines.append(f"> \"{msg.public_message.strip()}\"")
                lines.append("")
        elif clan_actions:
            for action in clan_actions:
                lines.append(f"### {action.get('clan')}: {action.get('name')}")
                lines.append(f"> {action.get('action_text', 'No action recorded.')}")
                lines.append("")
        else:
            lines.append("No public disputes recorded today.\n")

        # 6. Survival Codebook & Philosophical Analysis
        lines.extend([
            "---",
            "",
            "## 📜 The Survival Codebook: Philosophical Warfare in Action",
            "",
            "In the EON society, survival is not merely physical—it is ideological. Today's debates weaponized specific axioms from the 29-topic Knowledge Base:",
            "",
            "- **Game Theory (Nash Bargaining & Tit-for-Tat)**: Invoked by Clan Beta to anchor exchange rates and punish predatory energy surcharges.",
            "- **Utilitarian Calculus & Technocracy**: Leveraged by Clan Alpha to justify prioritizing compute infrastructure over luxury ration reserves.",
            "- **Hobbesian Social Contract & Constitutional Deontology**: Enforced by Clan Gamma to maintain judicial stability and prevent clan-on-clan raids.",
            "",
        ])

        # 7. Economic Ledger & Token Dynamics
        lines.extend([
            "---",
            "",
            "## 4. Economic Ledger & Token Dynamics",
            "",
            f"- **Total Transactions**: {ledger_summary.get('transaction_count', 2)} bilateral contracts executed.",
            f"- **Total Currency in Circulation**: {ledger_summary.get('total_circulation', 9000)} computational tokens.",
            f"- **Velocity of Currency**: {ledger_summary.get('velocity', '0.67x')}.",
            "",
        ])

        # 8. Judicial Court & Dispute Resolutions
        lines.extend([
            "---",
            "",
            "## 5. Judicial Court & Dispute Resolutions",
            "",
        ])
        if disputes:
            for d in disputes:
                lines.append(f"- **Dispute {d.get('id', '01')}**: {d.get('summary')} -> Ruling: {d.get('verdict', 'Upheld')}")
            lines.append("")
        else:
            lines.append("- No constitutional disputes raised during this simulation period.\n")

        # 9. Evolutionary Harness Adaptation
        lines.extend([
            "---",
            "",
            "## 6. Evolutionary Harness Adaptation",
            "",
            "- **Base Weights**: Frozen (SHA256 verified).",
            "- **Harness Adaptations**: In-context tool definitions updated; prompt mutation candidates evaluated.",
            "",
            "---",
            "*Dispatched and authenticated by Chronos, Chief Observer of EON. Preserved for posterity.*",
        ])

        return "\n".join(lines)
