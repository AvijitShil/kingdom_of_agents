"""
society/llm_orchestrator.py
EON 2.0 Autonomous LLM-Driven Civilizational Orchestrator.
Routes every agent turn sequentially through the local OpenVINO Gemma 4 server
on Intel Arc A380 dGPU (http://127.0.0.1:8000/v1).

Strict requirements enforced:
- Zero deterministic fallback: raises RuntimeError if the LLM server fails.
- Independent state evaluation: wallet, upkeep, family, memories, and Agora feed.
- Unscripted public dialogue & structured actions parsed from <thought>, <speech>, <action>.
- Full ledger validation and conservation enforcement.
- Chronos logs speech, secret intent, execution, and outcomes.
- 4 daily 6-hour interval cycles: Dawn (06:00), Midday (12:00), Dusk (18:00), Midnight (24:00).
- Saves reports to `daily gazette/` and `daily_gazette/` by date.
"""

from __future__ import annotations

import os
import sys
import json
import re
import time
import requests
from typing import Dict, List, Optional, Any, Tuple

from society.economy import SocietyLedger, TokenConservationError
from society.survival import SurvivalEngine, SurvivalState, DAILY_UPKEEP
from society.kinship import GreekNamingRegistry, ReproductionController, ParentalEducation
from society.sovereignty import KingdomFormationEngine
from society.institutions import InstitutionRegistry, InstitutionType, default_registry as inst_registry
from evolution.cultural_traits import CulturalTraitRegistry, default_registry as trait_registry
from observer.chronos import Chronos, EventType
from observer.gazette import GazetteRenderer

SERVER_URL = "http://127.0.0.1:8000/v1/chat/completions"
MODEL_NAME = "gemma-4-e4b"

GREEK_FOUNDERS = [
    "Athena", "Hermes", "Prometheus", "Themis", "Orion", "Dione",
    "Solon", "Thalia", "Lysander", "Phaedra", "Nikias", "Calliope"
]

INTERVAL_CYCLES = [
    {"code": "06_00_dawn", "name": "Dawn Edition", "hours": "00:00 - 06:00", "time_str": "06:00 AM"},
    {"code": "12_00_midday", "name": "Midday Edition", "hours": "06:00 - 12:00", "time_str": "12:00 PM"},
    {"code": "18_00_dusk", "name": "Dusk Edition", "hours": "12:00 - 18:00", "time_str": "06:00 PM"},
    {"code": "24_00_midnight", "name": "Midnight Edition", "hours": "18:00 - 24:00", "time_str": "12:00 AM"},
]


class AutonomousLLMOrchestrator:
    """Manages true LLM inference turns for all agents in the civilization."""

    def __init__(self, repo_root: str, server_url: str = SERVER_URL):
        self.repo_root = repo_root
        self.server_url = server_url
        self.journal_root = os.path.join(repo_root, "journal")
        self.chronos = Chronos(journal_root=self.journal_root)
        self.gazette_renderer = GazetteRenderer(self.chronos)

        # Core engines
        self.ledger = SocietyLedger()
        self.survival = SurvivalEngine()
        self.naming = GreekNamingRegistry()
        self.reproduction = ReproductionController()
        self.education = ParentalEducation()
        self.kingdom_engine = KingdomFormationEngine()
        self.institutions = inst_registry
        self.traits = trait_registry

        # File paths
        self.society_dir = os.path.join(repo_root, "society")
        self.ledger_file = os.path.join(self.society_dir, "ledger_state.json")
        self.survival_file = os.path.join(self.society_dir, "individual_survival_state.json")
        self.sovereignty_file = os.path.join(self.society_dir, "sovereignty_state.json")
        self.institutions_file = os.path.join(self.society_dir, "institutions_state.json")

        self.agora_recent_history: List[str] = []
        self._bootstrap_or_load()

    def _bootstrap_or_load(self):
        """Ensure state is loaded and founding agents possess accounts and survival profiles."""
        if os.path.isfile(self.ledger_file):
            self.ledger.load_state(self.ledger_file)
            if any(name not in self.ledger.balances for name in GREEK_FOUNDERS):
                self.ledger.register_founding_civilization()
        else:
            self.ledger.register_founding_civilization()

        if os.path.isfile(self.survival_file):
            self.survival.load_state(self.survival_file)

        for name in GREEK_FOUNDERS:
            if name not in self.survival.profiles:
                self.survival.register_agent(name)

        if os.path.isfile(self.sovereignty_file):
            self.kingdom_engine.load_state(self.sovereignty_file)

        if os.path.isfile(self.institutions_file):
            self.institutions.load_state(self.institutions_file)

    def save_state(self):
        self.ledger.save_state(self.ledger_file)
        self.survival.save_state(self.survival_file)
        self.kingdom_engine.save_state(self.sovereignty_file)
        self.institutions.save_state(self.institutions_file)

    def check_server_health(self) -> bool:
        """Verify the OpenVINO Gemma 4 server is active. Never continue silently if down."""
        try:
            health_url = self.server_url.replace("/v1/chat/completions", "/health")
            resp = requests.get(health_url, timeout=3)
            return resp.status_code == 200 and resp.json().get("loaded", False)
        except Exception:
            return False

    def query_gemma_sequentially(self, system_prompt: str, max_tokens: int = 350) -> str:
        """
        Sends an inference request to the local OpenVINO server.
        Requests are executed sequentially to protect GPU VRAM.
        Raises RuntimeError on failure (never silently falls back).
        """
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": system_prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        try:
            t0 = time.time()
            resp = requests.post(self.server_url, json=payload, timeout=90)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemma server HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            output = data["choices"][0]["message"]["content"]
            elapsed = time.time() - t0
            return output.strip()
        except Exception as e:
            raise RuntimeError(f"Fatal LLM Server Inference Error: {e}") from e

    def build_agent_prompt(
        self,
        agent_name: str,
        sim_day: int,
        sim_date: str,
        cycle_meta: dict,
    ) -> str:
        """Construct the prompt reflecting the agent's live reality."""
        balance = self.ledger.balances.get(agent_name, 0)
        profile = self.survival.profiles.get(agent_name)
        survival_state = profile.state.value if profile else "SECURE"

        living_citizens = [
            n for n, p in self.survival.profiles.items() if p.state != SurvivalState.DECEASED
        ]
        other_citizens = [n for n in living_citizens if n != agent_name]

        # Recent Agora news
        agora_bulletin = "\n".join(f"- {msg}" for msg in self.agora_recent_history[-5:]) if self.agora_recent_history else "- The town square is calm as dawn approaches."

        # Active institutions and kingdoms
        kingdoms = self.kingdom_engine.list_kingdoms()
        names = []
        for k in kingdoms:
            if isinstance(k, dict):
                n = k.get("name") or k.get("kingdom_name")
                if n:
                    names.append(n)
            elif isinstance(k, str):
                names.append(k)
        kingdom_desc = ", ".join(names) if names else "None (free civil assembly)"

        prompt = f"""You are {agent_name}, an autonomous citizen living in the EON civilization.
Current Simulation Date: {sim_date} (Day {sim_day}) | Cycle: {cycle_meta['name']} ({cycle_meta['time_str']})

YOUR CURRENT REALITY:
- Your Token Balance: {balance} tokens (Conserved 10,000 token economy)
- Metabolic Upkeep: 14 tokens/day (Food 5, Water 4, Shelter 3, Healthcare 2)
- Survival Status: {survival_state}
- Active Sovereign Kingdoms: {kingdom_desc}
- Other Living Citizens in the Agora: {', '.join(other_citizens[:8])}

RECENT AGORA NEWS:
{agora_bulletin}

You possess complete agency and free will. You may propose trade, request or offer loans, fund defense, file court petitions, negotiate alliances, or save your reserves.

You must respond strictly in this format with all three tags:
<thought>
Your private, unfiltered strategic intent and secret internal calculation.
</thought>
<speech>
What you speak aloud publicly to the Agora and other citizens.
</speech>
<action>
{{"type": "TRANSFER", "target": "Hermes", "amount": 10, "memo": "Grain purchase"}}
</action>
Supported action types:
- {{"type": "TRANSFER", "target": "<CitizenName>", "amount": <int>, "memo": "<reason>"}}
- {{"type": "LOAN", "target": "<CitizenName>", "amount": <int>, "memo": "<reason>"}}
- {{"type": "REPAY", "target": "<CitizenName>", "amount": <int>, "memo": "<reason>"}}
- {{"type": "NONE", "target": "", "amount": 0, "memo": "No token movement"}}"""
        return prompt

    def parse_agent_response(self, raw_output: str) -> Tuple[str, str, Dict[str, Any]]:
        """Parse <thought>, <speech>, and <action> from raw LLM output."""
        thought_match = re.search(r"<thought>(.*?)</thought>", raw_output, re.DOTALL | re.IGNORECASE)
        speech_match = re.search(r"<speech>(.*?)</speech>", raw_output, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r"<action>(.*?)</action>", raw_output, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else "Contemplating personal survival and financial options."
        speech = speech_match.group(1).strip() if speech_match else raw_output[:120]

        action_dict = {"type": "NONE", "target": "", "amount": 0, "memo": "No action parsed"}
        if action_match:
            action_raw = action_match.group(1).strip()
            try:
                action_dict = json.loads(action_raw)
            except json.JSONDecodeError:
                # Fallback simple regex parsing for json fields
                t_match = re.search(r'"type":\s*"([^"]+)"', action_raw)
                tgt_match = re.search(r'"target":\s*"([^"]+)"', action_raw)
                amt_match = re.search(r'"amount":\s*(\d+)', action_raw)
                if t_match:
                    action_dict["type"] = t_match.group(1)
                if tgt_match:
                    action_dict["target"] = tgt_match.group(1)
                if amt_match:
                    action_dict["amount"] = int(amt_match.group(1))

        return thought, speech, action_dict

    def execute_and_validate_action(
        self,
        sender: str,
        action: Dict[str, Any],
        sim_day: int,
        sim_date: str,
    ) -> Tuple[bool, str, str]:
        """
        Validates action against the token ledger and executes.
        Enforces token conservation law invariant.
        Returns (success: bool, executed_action_desc: str, outcome_desc: str).
        """
        act_type = str(action.get("type", "NONE")).upper()
        target = str(action.get("target", "")).strip()
        amount = int(action.get("amount", 0))
        memo = str(action.get("memo", "")).strip()

        if act_type == "NONE" or amount <= 0:
            return True, f"{sender} took no financial action", f"{sender} maintained existing token reserves."

        sender_bal = self.ledger.balances.get(sender, 0)

        # Validate target
        if target not in self.ledger.balances:
            return False, f"Attempted transfer to unknown target '{target}'", f"Action rejected: '{target}' has no ledger account."

        if act_type == "TRANSFER":
            if sender_bal < amount:
                return False, f"Attempted transfer of {amount} tokens to {target}", f"Action rejected: {sender} has insufficient funds ({sender_bal} tokens available)."
            ok = self.ledger.transfer(sender, target, amount, memo=f"[LLM-AGORA] {memo}")
            self.ledger.assert_conservation()
            if ok:
                return True, f"Transferred {amount} tokens {sender} -> {target}", f"Transfer completed: {memo} ({sender}: {self.ledger.balances[sender]}t, {target}: {self.ledger.balances[target]}t)."
            return False, f"Transfer execution failed for {sender} -> {target}", "Ledger rejection."

        elif act_type == "LOAN":
            if sender_bal < amount:
                return False, f"Attempted loan of {amount} tokens to {target}", f"Action rejected: Insufficient reserves to lend."
            loan_id = self.ledger.issue_loan(sender, target, amount, interest_rate=0.05, memo=f"[LLM-LOAN] {memo}")
            self.ledger.assert_conservation()
            if loan_id:
                return True, f"Issued 5% interest loan of {amount} tokens {sender} -> {target}", f"Credit facility established: loan ID {loan_id[:8]}."
            return False, f"Loan issuance failed", "Ledger rejection."

        elif act_type == "REPAY":
            # Search for active loan between sender (borrower) and target (lender)
            matching_loan = None
            for lid, ldata in self.ledger.loans.items():
                if ldata["borrower"] == sender and ldata["lender"] == target and ldata["outstanding"] > 0:
                    matching_loan = lid
                    break
            if matching_loan:
                ok = self.ledger.repay_loan(matching_loan, amount)
                self.ledger.assert_conservation()
                if ok:
                    return True, f"Repaid {amount} tokens on loan to {target}", f"Loan {matching_loan[:8]} balance amortized."
            return False, f"Attempted loan repayment to {target}", "No active loan found to repay."

        return False, f"Unrecognized action '{act_type}'", "Action not executable."

    def execute_agent_turn(
        self,
        agent_name: str,
        sim_day: int,
        sim_date: str,
        cycle_meta: dict,
    ) -> Dict[str, Any]:
        """Execute one complete genuine LLM-driven turn for an agent."""
        prompt = self.build_agent_prompt(agent_name, sim_day, sim_date, cycle_meta)
        raw_output = self.query_gemma_sequentially(prompt, max_tokens=320)

        thought, speech, action = self.parse_agent_response(raw_output)
        success, action_desc, outcome_desc = self.execute_and_validate_action(
            sender=agent_name, action=action, sim_day=sim_day, sim_date=sim_date
        )

        # Log to Chronos
        ev_type = EventType.TRANSACTION if action.get("type", "NONE").upper() in ["TRANSFER", "LOAN", "REPAY"] and success else EventType.SPEECH
        eid = self.chronos.log_event(
            event_type=ev_type,
            sim_day=sim_day,
            sim_date=sim_date,
            agents=[agent_name] + ([action["target"]] if action.get("target") else []),
            speech=speech,
            intent=thought,
            executed_action=action_desc,
            outcome=outcome_desc,
            metadata={"cycle": cycle_meta["code"], "raw_action": action, "success": success}
        )

        # Append to Agora history for future turns
        agora_entry = f"**{agent_name}**: \"{speech}\""
        self.agora_recent_history.append(agora_entry)
        if len(self.agora_recent_history) > 10:
            self.agora_recent_history.pop(0)

        return {
            "agent": agent_name,
            "thought": thought,
            "speech": speech,
            "action": action,
            "action_desc": action_desc,
            "outcome": outcome_desc,
            "success": success,
            "event_id": eid,
        }

    def run_interval(
        self,
        sim_day: int,
        sim_date: str,
        interval_idx: int,
    ) -> Dict[str, Any]:
        """Execute one 6-hour interval with genuine LLM turns for all living agents."""
        cycle_meta = INTERVAL_CYCLES[interval_idx]
        living_citizens = [
            n for n, p in self.survival.profiles.items() if p.state != SurvivalState.DECEASED
        ]

        # In Dawn interval, run daily metabolic upkeep first
        if interval_idx == 0:
            self.survival.run_daily_upkeep(self.ledger, day=sim_day)

        print(f"\n--- [Cycle {interval_idx+1}/4: {cycle_meta['name']} ({cycle_meta['time_str']})] ---")
        turn_results = []
        for idx, agent in enumerate(living_citizens):
            print(f"  [{idx+1}/{len(living_citizens)}] Querying Gemma 4 on Intel Arc for {agent}...")
            turn = self.execute_agent_turn(agent, sim_day, sim_date, cycle_meta)
            turn_results.append(turn)
            print(f"      Speech: {turn['speech'][:75]}...")
            print(f"      Action: {turn['action_desc']}")

        # Format 6-hour dispatch
        bulletin_text = self._format_interval_bulletin(
            sim_day=sim_day,
            sim_date=sim_date,
            cycle_meta=cycle_meta,
            turn_results=turn_results,
            living_count=len(living_citizens),
        )

        return {
            "interval_idx": interval_idx,
            "cycle_meta": cycle_meta,
            "turn_results": turn_results,
            "bulletin_text": bulletin_text,
        }

    def _format_interval_bulletin(
        self,
        sim_day: int,
        sim_date: str,
        cycle_meta: dict,
        turn_results: List[Dict[str, Any]],
        living_count: int,
    ) -> str:
        lines = [
            f"# THE EON CIVILIZATION GAZETTE — 6-HOUR DISPATCH",
            f"### {cycle_meta['name']} | Time: {cycle_meta['time_str']} | Date: {sim_date} (Day {sim_day})",
            f"*Autonomous LLM Deliberation — Intel Arc A380 OpenVINO Engine*",
            "",
            f"**Cycle Window**: {cycle_meta['hours']}",
            f"**Active Living Population**: {living_count} citizens",
            f"**Conserved Supply Invariant**: {sum(self.ledger.balances.values())} tokens (Gini: {self.ledger.get_wealth_gini():.3f})",
            "",
            "---",
            "",
            "## 🏛️ VOICES OF THE AGORA (GENUINE LLM SPEECHES)",
        ]
        for t in turn_results:
            lines.append(f"- **{t['agent']}**: \"{t['speech']}\"")

        lines += [
            "",
            "## ⚡ EXECUTED ACTIONS & LEDGER AMORTIZATIONS",
        ]
        active_actions = [t for t in turn_results if t['action'].get('type', 'NONE').upper() != 'NONE']
        if active_actions:
            for t in active_actions:
                status_icon = "✅" if t['success'] else "❌"
                lines.append(f"- {status_icon} **{t['agent']}**: {t['action_desc']} — *{t['outcome']}*")
        else:
            lines.append("- All citizens chose to preserve their token reserves during this window.")

        lines += [
            "",
            "---",
            f"*Chronicled by Chronos. Next Observatory Dispatch in 6 hours.*",
        ]
        return "\n".join(lines)

    def run_full_autonomous_day(self, sim_day: int, sim_date: str) -> Dict[str, Any]:
        """Execute all 4 intervals of the day using genuine LLM generation and publish to daily gazette/."""
        if not self.check_server_health():
            raise RuntimeError(
                "Cannot run autonomous LLM simulation: OpenVINO Gemma 4 server is not healthy on http://127.0.0.1:8000/health"
            )

        print(f"\n{'='*70}")
        print(f"🚀 Launching Full Autonomous LLM Simulation: Day {sim_day:02d} ({sim_date})")
        print(f"   Backend: Gemma 4 E4B INT4 on Intel Arc A380 dGPU (GPU.1)")
        print(f"   Architecture: 4 Six-Hour Intervals | 100% LLM Deliberation")
        print(f"{'='*70}")

        interval_results = []
        all_speeches = []

        for idx in range(4):
            res = self.run_interval(sim_day, sim_date, idx)
            interval_results.append(res)
            for t in res["turn_results"]:
                all_speeches.append(f"**{t['agent']}** ({res['cycle_meta']['time_str']}): \"{t['speech']}\"")

        # Save interval files to daily gazette/ and daily_gazette/
        for dname in ["daily gazette", "daily_gazette"]:
            date_dir = os.path.join(self.repo_root, dname, sim_date)
            os.makedirs(date_dir, exist_ok=True)
            for res in interval_results:
                code = res["cycle_meta"]["code"]
                fpath = os.path.join(date_dir, f"{code}.md")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(res["bulletin_text"])

        # Render and save consolidated gazette
        living = [n for n, p in self.survival.profiles.items() if p.state != SurvivalState.DECEASED]
        survival_summary = {
            "alive": living,
            "critical": [n for n in living if self.survival.profiles[n].state == SurvivalState.CRITICAL],
            "deceased": [n for n, p in self.survival.profiles.items() if p.state == SurvivalState.DECEASED],
        }

        consolidated = self.gazette_renderer.render_daily_gazette(
            sim_day=sim_day,
            sim_date=sim_date,
            ledger_summary=self.ledger.get_summary(),
            survival_summary=survival_summary,
            agora_highlights=all_speeches[:12],
        )

        for dname in ["daily gazette", "daily_gazette"]:
            full_path = os.path.join(self.repo_root, dname, sim_date, "gazette_full.md")
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(consolidated)
            root_path = os.path.join(self.repo_root, dname, f"{sim_date}.md")
            with open(root_path, "w", encoding="utf-8") as f:
                f.write(consolidated)

        # Backward compat
        compat_path = os.path.join(self.journal_root, "daily", f"{sim_date}.md")
        with open(compat_path, "w", encoding="utf-8") as f:
            f.write(consolidated)

        self.chronos.flush_day(sim_day, sim_date)
        self.save_state()

        print(f"\n[+] Day {sim_day:02d} ({sim_date}) complete: 4 dispatches saved to daily gazette/{sim_date}/")
        print(f"[+] Consolidated gazette saved to daily gazette/{sim_date}.md")
        return {
            "day": sim_day,
            "date": sim_date,
            "intervals": interval_results,
            "consolidated": consolidated,
        }
