"""
Unit Tests for PasswordManager and Boundary Authorization.

Validates PBKDF2-HMAC-SHA256 hashing, 600,000 iterations, 32-byte cryptographic salt,
constant-time digest verification, wrong password rejection, password rotation,
and password-gated boundary configuration.
"""

import json
import pytest

from sandbox.auth import (
    PasswordManager,
    PBKDF2_ITERATIONS,
    SALT_BYTES,
    MIN_PASSWORD_LENGTH,
    DEFAULT_ADMIN_PASSWORD,
)
from sandbox.exceptions import AuthenticationError
from sandbox import SecuritySandbox, Permission


@pytest.fixture
def config_file(tmp_path):
    """Path to a temporary sandbox config file."""
    return tmp_path / ".sandbox_config.json"


@pytest.fixture
def auth_manager(config_file):
    """Create a PasswordManager with default password."""
    return PasswordManager(config_path=config_file)


def test_pbkdf2_initialization_and_metadata(auth_manager, config_file):
    """Test cryptographic parameters: 600k iterations, 32-byte salt, SHA-256."""
    assert config_file.exists()
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["algorithm"] == "PBKDF2-HMAC-SHA256"
    assert data["iterations"] == PBKDF2_ITERATIONS
    assert data["iterations"] == 600_000

    # Salt must be 32 bytes (64 hex characters)
    salt_bytes = bytes.fromhex(data["salt_hex"])
    assert len(salt_bytes) == SALT_BYTES
    assert len(salt_bytes) == 32

    # SHA256 digest is 32 bytes (64 hex characters)
    hash_bytes = bytes.fromhex(data["hash_hex"])
    assert len(hash_bytes) == 32


def test_correct_password_verification(auth_manager):
    """Test verification and authorization with correct default administrator password."""
    assert auth_manager.verify_password(DEFAULT_ADMIN_PASSWORD) is True
    assert auth_manager.authenticate_and_authorize(DEFAULT_ADMIN_PASSWORD) is True


def test_wrong_password_rejection(auth_manager):
    """Test that wrong passwords return False and raise AuthenticationError."""
    wrong_passwords = [
        "incorrect_pw",
        "EON_Kingdom_Admin_2026",
        "Admin12345678!",
        "",
        "   ",
    ]
    for pw in wrong_passwords:
        assert auth_manager.verify_password(pw) is False
        with pytest.raises(AuthenticationError):
            auth_manager.authenticate_and_authorize(pw)


def test_password_rotation_and_persistence(auth_manager, config_file):
    """Test changing password, verifying new password, and loading from disk."""
    new_pw = "New_Secure_Admin_Password_2026!#"

    # Change password
    auth_manager.change_password(
        current_password=DEFAULT_ADMIN_PASSWORD,
        new_password=new_pw,
    )

    # Old password no longer valid
    assert auth_manager.verify_password(DEFAULT_ADMIN_PASSWORD) is False

    # New password valid
    assert auth_manager.verify_password(new_pw) is True
    assert auth_manager.authenticate_and_authorize(new_pw) is True

    # Reload from disk into fresh PasswordManager
    fresh_manager = PasswordManager(config_path=config_file)
    assert fresh_manager.verify_password(new_pw) is True
    assert fresh_manager.verify_password(DEFAULT_ADMIN_PASSWORD) is False


def test_password_change_rejections(auth_manager):
    """Test password change validation: wrong current password or short new password."""
    # Wrong current password
    with pytest.raises(AuthenticationError):
        auth_manager.change_password("wrong_current_pw", "Valid_New_Password_123!")

    # Short new password (< 12 chars)
    with pytest.raises(ValueError):
        auth_manager.change_password(DEFAULT_ADMIN_PASSWORD, "Short1!")


def test_sandbox_boundary_management_password_protection(tmp_path):
    """Test that SecuritySandbox boundary changes require password authorization."""
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    extra_dir = tmp_path / "external_data"
    extra_dir.mkdir()

    sandbox = SecuritySandbox(
        project_root=sandbox_root,
        config_file=".sandbox_config.json",
        default_password="My_Secret_Admin_Pass_2026!",
    )

    # Attempt to add allowed path with wrong password fails
    with pytest.raises(AuthenticationError):
        sandbox.add_allowed_path(extra_dir, "r", "wrong_password")

    # Add allowed path with correct password succeeds
    boundary = sandbox.add_allowed_path(extra_dir, "r", "My_Secret_Admin_Pass_2026!")
    assert boundary.permission == Permission.READ

    # Path is now accessible
    test_file = extra_dir / "data.txt"
    test_file.write_text("allowed data", encoding="utf-8")
    assert sandbox.read_text(test_file) == "allowed data"

    # Attempt to remove allowed path with wrong password fails
    with pytest.raises(AuthenticationError):
        sandbox.remove_allowed_path(extra_dir, "wrong_password")

    # Remove allowed path with correct password succeeds
    sandbox.remove_allowed_path(extra_dir, "My_Secret_Admin_Pass_2026!")

    # Path is no longer accessible
    with pytest.raises(Exception):
        sandbox.read_text(test_file)



def test_iteration_downgrade_tampering_prevented(tmp_path):
    """Test that setting iterations < PBKDF2_ITERATIONS is clamped to PBKDF2_ITERATIONS floor."""
    cfg = tmp_path / ".sandbox_config.json"
    dummy_salt = "aa" * 32
    dummy_hash = "bb" * 32

    # Tamper with iterations = 1
    cfg.write_text(
        json.dumps({
            "algorithm": "PBKDF2-HMAC-SHA256",
            "iterations": 1,
            "salt_hex": dummy_salt,
            "hash_hex": dummy_hash,
        }),
        encoding="utf-8",
    )
    pm = PasswordManager(config_path=cfg)
    assert pm._iterations == PBKDF2_ITERATIONS
    assert pm._iterations == 600_000

    # Tamper with iterations = 0
    cfg.write_text(
        json.dumps({
            "algorithm": "PBKDF2-HMAC-SHA256",
            "iterations": 0,
            "salt_hex": dummy_salt,
            "hash_hex": dummy_hash,
        }),
        encoding="utf-8",
    )
    pm0 = PasswordManager(config_path=cfg)
    assert pm0._iterations == PBKDF2_ITERATIONS

    # Tamper with non-int iterations
    cfg.write_text(
        json.dumps({
            "algorithm": "PBKDF2-HMAC-SHA256",
            "iterations": "invalid_iterations",
            "salt_hex": dummy_salt,
            "hash_hex": dummy_hash,
        }),
        encoding="utf-8",
    )
    pm_invalid = PasswordManager(config_path=cfg)
    assert pm_invalid._iterations == PBKDF2_ITERATIONS


def test_non_string_password_verification_safe(auth_manager):
    """Test that None and non-string password inputs safely return False without raising AttributeError."""
    non_strings = [None, 12345, 0, True, False, [], {}, (1, 2), b"bytes_password"]
    for val in non_strings:
        assert auth_manager.verify_password(val) is False
        with pytest.raises(AuthenticationError):
            auth_manager.authenticate_and_authorize(val)

    with pytest.raises(AuthenticationError):
        auth_manager.change_password(None, "New_Valid_Password_1234!")

    with pytest.raises(ValueError):
        auth_manager.change_password(DEFAULT_ADMIN_PASSWORD, None)
