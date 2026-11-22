"""
scripts/run_llm_cycle.py
Test script to run all 12 founding agents through one complete interval cycle
using the local Gemma 4 server on Intel Arc A380 dGPU.
"""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from society.llm_orchestrator import AutonomousLLMOrchestrator

def main():
    print("=" * 70)
    print("TEST: Running All 12 Founding Agents Through One Complete LLM Cycle")
    print("=" * 70)
    
    orchestrator = AutonomousLLMOrchestrator(repo_root=REPO_ROOT)
    
    if not orchestrator.check_server_health():
        print("[-] FATAL: Server is not healthy at http://127.0.0.1:8000/health")
        sys.exit(1)
        
    print("[+] Server connection verified: Gemma 4 on Intel Arc A380 is READY.")
    
    # Run Interval 0 (Dawn) for Day 7
    sim_day = 7
    sim_date = "2026-11-28"
    
    t0 = time.time()
    res = orchestrator.run_interval(sim_day=sim_day, sim_date=sim_date, interval_idx=0)
    elapsed = time.time() - t0
    
    print("\n" + "=" * 70)
    print(f"Cycle Complete in {elapsed:.2f} seconds ({elapsed/12:.2f}s per agent)")
    print("=" * 70)
    print(res["bulletin_text"])
    print("=" * 70)

if __name__ == "__main__":
    main()
