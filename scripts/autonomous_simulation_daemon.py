"""
EON Autonomous Simulation Daemon
Runs the living multi-agent society simulation continuously in the background,
executing a new simulation tick/edition every 6 hours (21,600 seconds).
Publishes The Kingdom Gazette, exports Agora transcripts, and synchronizes to GitHub.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.generate_daily_journal import run_day, get_simulation_date

LOG_FILE = os.path.join(REPO_ROOT, "scripts", "daemon.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


def get_next_simulation_day() -> int:
    """Determine the next simulation day by inspecting existing journal entries."""
    journal_dir = os.path.join(REPO_ROOT, "journal")
    if not os.path.isdir(journal_dir):
        return 1

    existing_files = [f for f in os.listdir(journal_dir) if f.endswith(".md") and f != "README.md"]
    # If Day 1 and Day 2 exist, next is 3
    return len(existing_files) + 1


def start_daemon(interval_hours: float = 6.0, max_days: int = 30):
    interval_seconds = int(interval_hours * 3600)
    logging.info("=" * 70)
    logging.info(f"🚀 EON Autonomous Simulation Daemon Initialized")
    logging.info(f"Cadence: Every {interval_hours} hours ({interval_seconds}s)")
    logging.info(f"Target: Running up to Day {max_days:02d}")
    logging.info(f"Logs: {LOG_FILE}")
    logging.info("=" * 70)

    while True:
        current_day = get_next_simulation_day()
        if current_day > max_days:
            logging.info(f"🏁 30-Day Simulation Horizon Reached (Day {current_day-1}). Daemon concluding.")
            break

        sim_date = get_simulation_date(current_day)
        logging.info(f"▶️ Executing Autonomous Simulation Tick: Day {current_day:02d}/30 ({sim_date})...")

        try:
            run_day(current_day)
            logging.info(f"✅ Day {current_day:02d} completed, Gazette published, and pushed to GitHub successfully.")
        except Exception as e:
            logging.error(f"❌ Error during Day {current_day:02d} execution: {e}", exc_info=True)

        next_run_time = datetime.now() + timedelta(seconds=interval_seconds)
        logging.info(f"⏳ Sleeping for {interval_hours} hours. Next autonomous run scheduled at: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("-" * 70)

        time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EON Autonomous Simulation Daemon")
    parser.add_argument("--hours", type=float, default=6.0, help="Interval between ticks in hours (default: 6.0)")
    parser.add_argument("--max-days", type=int, default=30, help="Maximum days to simulate (default: 30)")
    args = parser.parse_args()

    start_daemon(interval_hours=args.hours, max_days=args.max_days)
