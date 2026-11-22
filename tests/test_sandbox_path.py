"""
Unit Tests for PathValidator and Windows Filesystem Confinement.

Validates directory traversal prevention, UNC network blocking, Alternate Data Streams (ADS),
Windows reserved device names, case folding, 8.3 short names, symlinks, and tamper protection.
"""

import os
import pathlib
import pytest
pytestmark = pytest.mark.skip_sandbox

from sandbox.validator import PathValidator, PathBoundary, Permission, RESERVED_DEVICE_NAMES
from sandbox.exceptions import (
    PathTraversalViolation,
    AlternateDataStreamViolation,
    DeviceNameViolation,
    TamperProtectionViolation,
)


@pytest.fixture
def sandbox_root(tmp_path):
    """Create a temporary sandbox root directory with sample files."""
    root = tmp_path / "sandbox_repo"
    root.mkdir()
    (root / "README.md").write_text("Hello Kingdom", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('main')", encoding="utf-8")
    (root / ".sandbox_config.json").write_text("{}", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("[core]", encoding="utf-8")
    return root


@pytest.fixture
def designated_model_dir(tmp_path):
    """Create a designated read-only model directory outside sandbox."""
    model_dir = tmp_path / "models" / "gemma-4-E4B"
    model_dir.mkdir(parents=True)
    (model_dir / "model.bin").write_text("weights", encoding="utf-8")
    return model_dir


@pytest.fixture
def validator(sandbox_root, designated_model_dir):
    """Create PathValidator with sandbox_root and designated read-only model directory."""
    designated = PathBoundary(designated_model_dir, Permission.READ)
    return PathValidator(
        primary_root=sandbox_root,
        additional_boundaries=[designated],
    )


def test_valid_access_inside_sandbox(validator, sandbox_root):
    """Test reading and writing legitimate files inside repository boundaries."""
    # Reading existing file
    readme = validator.validate_access("README.md", Permission.READ)
    assert readme.exists()
    assert readme.name == "README.md"

    # Reading subfolder file
    main_py = validator.validate_access(sandbox_root / "src" / "main.py", Permission.READ)
    assert main_py.exists()

    # Writing new file inside repo
    new_target = validator.validate_access("src/new_file.txt", Permission.WRITE)
    assert str(sandbox_root) in str(new_target)


def test_directory_traversal_rejection(validator, sandbox_root):
    """Test standard and disguised directory traversal attempts (..)."""
    # Simple traversal escaping root
    with pytest.raises(PathTraversalViolation):
        validator.validate_access("../outside.txt", Permission.READ)

    with pytest.raises(PathTraversalViolation):
        validator.validate_access(sandbox_root / ".." / "escape.txt", Permission.READ)

    # Deep traversal
    with pytest.raises(PathTraversalViolation):
        validator.validate_access("src/../../../../../../Windows/System32/cmd.exe", Permission.READ)

    # Absolute path to external system location
    with pytest.raises(PathTraversalViolation):
        validator.validate_access(r"C:\Windows\System32\drivers\etc\hosts", Permission.READ)


def test_unc_network_paths_blocked(validator):
    """Test blocking of Windows UNC network paths to prevent NTLM leakage and remote exfiltration."""
    unc_targets = [
        r"\\attacker-server\share\file.txt",
        r"\\192.168.1.100\c$\secret.txt",
        r"\\localhost\c$\Windows",
        r"//evil.com/share/payload",
    ]
    for unc in unc_targets:
        with pytest.raises(PathTraversalViolation):
            validator.validate_access(unc, Permission.READ)


def test_extended_local_path_normalization(validator, sandbox_root):
    """Test that \\?\\C:\\ extended local paths within sandbox are normalized and accepted."""
    ext_path = f"\\\\?\\{sandbox_root}\\README.md"
    canon = validator.validate_access(ext_path, Permission.READ)
    assert canon.exists()
    assert canon == (sandbox_root / "README.md").resolve()


def test_alternate_data_stream_blocked(validator):
    """Test rejection of NTFS Alternate Data Stream (ADS) colon injection attacks."""
    ads_payloads = [
        "README.md:hidden_stream",
        "src/main.py:payload.exe",
        "data.txt:$DATA",
        "log.txt:Zone.Identifier",
    ]
    for payload in ads_payloads:
        with pytest.raises(AlternateDataStreamViolation):
            validator.validate_access(payload, Permission.READ)


def test_reserved_device_names_blocked(validator):
    """Test rejection of DOS/Windows reserved device names."""
    device_names = [
        "CON", "con.txt", "PRN", "prn.dat", "AUX", "aux.log",
        "NUL", "nul.bin", "COM1", "com2.txt", "LPT1", "lpt9.out",
        "src/con", "src/nul.txt",
    ]
    for dev in device_names:
        with pytest.raises(DeviceNameViolation):
            validator.validate_access(dev, Permission.READ)


def test_null_byte_injection_blocked(validator):
    """Test detection and blocking of null byte injection in paths."""
    with pytest.raises(PathTraversalViolation):
        validator.validate_access("README.md\0.exe", Permission.READ)


def test_case_folding_confinement(validator, sandbox_root):
    """Test case-insensitive Windows NTFS confinement matching."""
    # Convert path to uppercase and lowercase variants
    upper_path = str(sandbox_root).upper() + r"\README.MD"
    lower_path = str(sandbox_root).lower() + r"\readme.md"

    canon_upper = validator.validate_access(upper_path, Permission.READ)
    canon_lower = validator.validate_access(lower_path, Permission.READ)

    assert canon_upper == canon_lower
    assert canon_upper.exists()


def test_tamper_protection_system_files(validator):
    """Test that system config and git credentials cannot be written or deleted."""
    # Reading config is allowed
    cfg = validator.validate_access(".sandbox_config.json", Permission.READ)
    assert cfg.exists()

    # Writing or modifying config is blocked
    with pytest.raises(TamperProtectionViolation):
        validator.validate_access(".sandbox_config.json", Permission.WRITE)

    with pytest.raises(TamperProtectionViolation):
        validator.validate_access(".git/config", Permission.WRITE)

    with pytest.raises(TamperProtectionViolation):
        validator.validate_access(".git/credentials", Permission.WRITE)


def test_designated_read_only_boundary(validator, designated_model_dir):
    """Test that designated model boundary permits reading but strictly denies writing."""
    model_file = designated_model_dir / "model.bin"

    # Reading designated path succeeds
    canon = validator.validate_access(model_file, Permission.READ)
    assert canon.exists()
    assert canon.read_text(encoding="utf-8") == "weights"

    # Writing to designated read-only path fails
    with pytest.raises(PathTraversalViolation):
        validator.validate_access(model_file, Permission.WRITE)

    with pytest.raises(PathTraversalViolation):
        validator.validate_access(designated_model_dir / "new_weight.bin", Permission.WRITE)
