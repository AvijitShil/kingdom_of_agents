"""
scripts/test_one_agent_turn.py
Executes a single genuine LLM turn for Prometheus using the local Gemma 4 OpenVINO server.
"""

import os
import sys
import json
import requests

SERVER_URL = "http://127.0.0.1:8000/v1/chat/completions"

prompt = """You are Prometheus, an autonomous founding citizen of the EON civilization.

YOUR CURRENT REALITY:
- Token Balance: 472 tokens (Conserved 10,000 currency system)
- Daily Upkeep: 14 tokens (Food 5, Water 4, Shelter 3, Healthcare 2)
- Survival Status: SECURE
- Family: Partnered with Dione, newborn child Thetis
- Public News: Lysander recently commissioned the Hoplite Phalanx defense force. The town seeks to secure cisterns and trade routes.

You have absolute autonomy. You may propose trades, form partnerships, invest in civic defense, or safeguard your domestic reserves.

Respond strictly using these tags:
<thought>
Your private internal calculation, secret strategy, and unfiltered intent.
</thought>
<speech>
Your public words spoken aloud in the Agora to other citizens.
</speech>
<action>
{"type": "TRANSFER", "target": "Lysander", "amount": 15, "memo": "Hoplite defense contribution"}
</action>
(If no token movement is desired, set type to "NONE", amount to 0)."""

def test_single_turn():
    print("[*] Dispatching prompt to Gemma 4 OpenVINO server on Intel Arc A380...")
    payload = {
        "model": "gemma-4-e4b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.7
    }
    resp = requests.post(SERVER_URL, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Server error {resp.status_code}: {resp.text}")

    raw_text = resp.json()["choices"][0]["message"]["content"]
    print("\n" + "=" * 60)
    print("GENUINE LLM OUTPUT FROM PROMETHEUS:")
    print("=" * 60)
    print(raw_text)
    print("=" * 60)
    return raw_text

if __name__ == "__main__":
    test_single_turn()
