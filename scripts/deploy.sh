#!/usr/bin/env bash
set -e
# Activate the conda environment (adjust name if different)
conda activate EVY || true
# Export required environment variables
export SANDBOX_PASSWORD="${SANDBOX_PASSWORD:-default_password}"
export GITHUB_PAT="${GITHUB_PAT}"
# Start the FastAPI server in background
uvicorn server.server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
echo "FastAPI server started (PID $SERVER_PID)"
# Run a sample evolution tick
python -m evolution.run_tick
# Wait for the server to exit (or Ctrl+C to stop)
wait $SERVER_PID