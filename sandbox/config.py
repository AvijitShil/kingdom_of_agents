"""
Sandbox Configuration and Data Models.

Defines default settings, system-protected files, designated model cache paths,
and configuration options for the SecuritySandbox subsystem.
"""

import os
import pathlib
from dataclasses import dataclass, field
from typing import List, Set, Optional


DEFAULT_PROJECT_ROOT: pathlib.Path = pathlib.Path(
    r"c:\Users\Subhajit\Documents\EON exp\kingdom_of_agents"
).resolve()

DEFAULT_DESIGNATED_MODEL_PATH: pathlib.Path = pathlib.Path(
    r"~\.cache\models\gemma-4-E4B-it-int4-ov"
).expanduser()

DEFAULT_PROTECTED_FILES: Set[str] = {
    ".sandbox_config.json",
    ".git/config",
    ".git/credentials",
}


@dataclass
class SandboxConfig:
    """Configuration settings for SecuritySandbox."""
    project_root: pathlib.Path = field(default_factory=lambda: DEFAULT_PROJECT_ROOT)
    config_file: str = ".sandbox_config.json"
    designated_model_path: pathlib.Path = field(
        default_factory=lambda: DEFAULT_DESIGNATED_MODEL_PATH
    )
    protected_files: Set[str] = field(
        default_factory=lambda: set(DEFAULT_PROTECTED_FILES)
    )
    allowed_loopback_hosts: Set[str] = field(
        default_factory=lambda: {"127.0.0.1", "localhost", "::1", "0.0.0.0"}
    )
