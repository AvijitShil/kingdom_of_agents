"""
Password Management and Cryptographic Boundary Authorization.

Implements PBKDF2-HMAC-SHA256 authentication with 600,000 iterations, 32-byte salt,
constant-time hash comparison, and tamper-resistant configuration management.
"""

import os
import json
import secrets
import hashlib
import pathlib
from typing import Optional, Union, Dict, Any

from sandbox.exceptions import AuthenticationError

PBKDF2_ITERATIONS: int = 600_000
SALT_BYTES: int = 32
MIN_PASSWORD_LENGTH: int = 12
DEFAULT_ADMIN_PASSWORD: str = "EON_Kingdom_Admin_2026!"


class PasswordManager:
    """
    Manages sandbox administrative authentication and boundary modification privileges.
    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations and 32-byte cryptographic salt.
    """

    def __init__(
        self,
        config_path: Union[str, pathlib.Path],
        default_password: Optional[str] = None,
    ):
        self.config_path = pathlib.Path(config_path).resolve()
        self._salt: Optional[bytes] = None
        self._hash: Optional[bytes] = None
        self._iterations: int = PBKDF2_ITERATIONS
        self.load_or_initialize(default_password=default_password)

    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """Derive PBKDF2-HMAC-SHA256 key from password and salt."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._iterations,
        )

    def load_or_initialize(self, default_password: Optional[str] = None):
        """Load stored password hash or initialize with secure default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "salt_hex" in data and "hash_hex" in data:
                    salt = bytes.fromhex(data["salt_hex"])
                    pw_hash = bytes.fromhex(data["hash_hex"])
                    if len(salt) == SALT_BYTES and len(pw_hash) == 32:
                        self._salt = salt
                        self._hash = pw_hash
                        try:
                            cfg_iter = int(data.get("iterations", PBKDF2_ITERATIONS))
                        except (ValueError, TypeError):
                            cfg_iter = PBKDF2_ITERATIONS
                        self._iterations = max(cfg_iter, PBKDF2_ITERATIONS)
                        return
            except Exception:
                pass

        initial_pw = (
            default_password
            or os.getenv("SANDBOX_ADMIN_PASSWORD")
            or DEFAULT_ADMIN_PASSWORD
        )
        self._salt = secrets.token_bytes(SALT_BYTES)
        self._hash = self._hash_password(initial_pw, self._salt)
        self._save()

    def _save(self):
        """Persist salt, hash, and metadata into configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data: Dict[str, Any] = {
            "algorithm": "PBKDF2-HMAC-SHA256",
            "iterations": self._iterations,
            "salt_hex": self._salt.hex() if self._salt else "",
            "hash_hex": self._hash.hex() if self._hash else "",
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def verify_password(self, password: str) -> bool:
        """Verify password using constant-time digest comparison."""
        if not isinstance(password, str):
            return False
        if not self._salt or not self._hash:
            return False
        candidate_hash = self._hash_password(password, self._salt)
        return secrets.compare_digest(candidate_hash, self._hash)

    def authenticate_and_authorize(self, password: str) -> bool:
        """
        Verify password and authorize administrative action.
        Raises AuthenticationError if password verification fails.
        """
        if not self.verify_password(password):
            raise AuthenticationError(
                "Administrative authorization failed: Invalid sandbox password."
            )
        return True

    def change_password(self, current_password: str, new_password: str):
        """Change administrator password after verifying the current password."""
        self.authenticate_and_authorize(current_password)
        if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"New password must be a string of at least {MIN_PASSWORD_LENGTH} characters in length."
            )
        self._salt = secrets.token_bytes(SALT_BYTES)
        self._hash = self._hash_password(new_password, self._salt)
        self._save()
