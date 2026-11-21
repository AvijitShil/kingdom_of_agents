"""
EON Frozen Foundation Model Guard
Strict cryptographic verification that Gemma 4 base weights remain 100% unchanged.
"""

import os
import hashlib
import json
from typing import Dict

BASE_MODEL_DIR = os.path.expanduser(r"~\.cache\models\gemma-4-E4B-it-int4-ov")
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "frozen_manifest.json")


def compute_sha256(filepath: str, block_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()


def generate_manifest(model_dir: str = BASE_MODEL_DIR) -> Dict[str, str]:
    manifest = {}
    for fname in os.listdir(model_dir):
        if fname.endswith(".bin") or fname.endswith(".xml") or fname.endswith(".json"):
            fpath = os.path.join(model_dir, fname)
            if os.path.isfile(fpath):
                manifest[fname] = compute_sha256(fpath)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def verify_integrity(model_dir: str = BASE_MODEL_DIR) -> bool:
    if not os.path.exists(MANIFEST_FILE):
        print(f"[FrozenGuard] No manifest found at {MANIFEST_FILE}. Creating initial frozen manifest...")
        generate_manifest(model_dir)
        print("[FrozenGuard] Initial manifest created.")
        return True

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        recorded_manifest = json.load(f)

    all_intact = True
    for fname, expected_hash in recorded_manifest.items():
        fpath = os.path.join(model_dir, fname)
        if not os.path.exists(fpath):
            print(f"[CRITICAL ALERT] Frozen model file missing: {fname}")
            all_intact = False
            continue
        current_hash = compute_sha256(fpath)
        if current_hash != expected_hash:
            print(f"[CRITICAL ALERT] HASH MISMATCH on frozen weight {fname}!")
            print(f"  Expected: {expected_hash}")
            print(f"  Current:  {current_hash}")
            all_intact = False

    if all_intact:
        print(f"[FrozenGuard] VERIFIED: All {len(recorded_manifest)} base model artifacts are 100% frozen and intact.")
    return all_intact


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else BASE_MODEL_DIR
    success = verify_integrity(target)
    sys.exit(0 if success else 1)
