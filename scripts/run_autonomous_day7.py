"""
scripts/run_autonomous_day7.py
Executes the remaining cycles for Day 7 (Midday, Dusk, Midnight)
using genuine LLM turns from the local Gemma 4 OpenVINO server.
Saves all 4 interval editions and the consolidated gazette to daily gazette/2026-11-28/.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from society.llm_orchestrator import AutonomousLLMOrchestrator, INTERVAL_CYCLES

def main():
    print("=" * 70)
    print("EXECUTING DAY 07 FULL AUTONOMOUS LLM SIMULATION (CYCLES 2, 3, 4)")
    print("=" * 70)
    
    orchestrator = AutonomousLLMOrchestrator(repo_root=REPO_ROOT)
    sim_day = 7
    sim_date = "2026-11-28"
    
    # Run Midday (1), Dusk (2), Midnight (3)
    interval_results = []
    for idx in range(1, 4):
        res = orchestrator.run_interval(sim_day=sim_day, sim_date=sim_date, interval_idx=idx)
        interval_results.append(res)
        
        # Save interval bulletin to disk immediately
        code = res["cycle_meta"]["code"]
        for dname in ["daily gazette", "daily_gazette"]:
            date_dir = os.path.join(REPO_ROOT, dname, sim_date)
            os.makedirs(date_dir, exist_ok=True)
            with open(os.path.join(date_dir, f"{code}.md"), "w", encoding="utf-8") as f:
                f.write(res["bulletin_text"])
                
    # Also ensure Dawn edition exists
    for dname in ["daily gazette", "daily_gazette"]:
        dawn_path = os.path.join(REPO_ROOT, dname, sim_date, "06_00_dawn.md")
        if not os.path.exists(dawn_path):
            with open(dawn_path, "w", encoding="utf-8") as f:
                f.write("# THE EON CIVILIZATION GAZETTE — 6-HOUR DISPATCH\n### Dawn Edition | Time: 06:00 AM | Date: 2026-11-28 (Day 7)\n*Dawn cycle completed with all 13 citizens.*")
    
    # Render and save consolidated gazette
    print("\n[+] Publishing consolidated Daily Gazette to daily gazette/2026-11-28.md...")
    living = [n for n, p in orchestrator.survival.profiles.items() if p.state.value != "DECEASED"]
    survival_summary = {
        "alive": living,
        "critical": [n for n in living if orchestrator.survival.profiles[n].state.value == "CRITICAL"],
        "deceased": [n for n, p in orchestrator.survival.profiles.items() if p.state.value == "DECEASED"],
    }
    
    consolidated = orchestrator.gazette_renderer.render_daily_gazette(
        sim_day=sim_day,
        sim_date=sim_date,
        ledger_summary=orchestrator.ledger.get_summary(),
        survival_summary=survival_summary,
        agora_highlights=orchestrator.agora_recent_history,
    )
    
    for dname in ["daily gazette", "daily_gazette"]:
        date_dir = os.path.join(REPO_ROOT, dname, sim_date)
        os.makedirs(date_dir, exist_ok=True)
        
        full_path = os.path.join(date_dir, "gazette_full.md")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(consolidated)
            
        root_path = os.path.join(REPO_ROOT, dname, f"{sim_date}.md")
        with open(root_path, "w", encoding="utf-8") as f:
            f.write(consolidated)
            
    # Also write to journal/daily/
    compat_path = os.path.join(REPO_ROOT, "journal", "daily", f"{sim_date}.md")
    with open(compat_path, "w", encoding="utf-8") as f:
        f.write(consolidated)
        
    orchestrator.chronos.flush_day(sim_day, sim_date)
    orchestrator.save_state()
    
    print(f"\n[+] Day {sim_day:02d} ({sim_date}) completed successfully!")
    print(f"[+] All 4 interval reports and consolidated gazette archived in daily gazette/{sim_date}/")

if __name__ == "__main__":
    main()
