"""
Runtime Sandbox Context Manager.

Hooks builtins.open, io.open, subprocess.Popen, and network sockets during
agent execution to enforce path boundary validation, binary confinement,
and network egress restrictions across runtime operations.
Supports re-entrant nesting and thread-safe reference counting.
"""

import io
import builtins
import subprocess
import threading
from typing import Optional, Union, Any, List

from sandbox.validator import PathValidator, Permission
from sandbox.execution import ExecutionGuard
from sandbox.network import NetworkGuard

# Preserve genuine unpatched references at import time
_ORIG_BUILTIN_OPEN = builtins.open
_ORIG_IO_OPEN = io.open
_ORIG_SUBPROCESS_POPEN = subprocess.Popen


class SandboxContext:
    """
    Context manager activating runtime interception hooks:
    1. Intercepts io.open and builtins.open (capturing open() and pathlib.Path I/O)
    2. Intercepts subprocess.Popen (enforcing binary and cwd confinement)
    3. Intercepts socket operations and DNS lookups (via NetworkGuard)
    Implements reference counting and re-entrancy depth tracking.
    """

    _lock = threading.RLock()
    _global_depth = 0
    _active_contexts: List["SandboxContext"] = []
    _thread_local = threading.local()

    def __init__(
        self,
        validator: PathValidator,
        execution: ExecutionGuard,
        network: NetworkGuard,
    ):
        self.validator = validator
        self.execution = execution
        self.network = network

        self._depth = 0
        self._orig_builtin_open = _ORIG_BUILTIN_OPEN
        self._orig_io_open = _ORIG_IO_OPEN
        self._orig_subprocess_popen = _ORIG_SUBPROCESS_POPEN

    def __enter__(self):
        with SandboxContext._lock:
            # Self-heal if hooks were externally unpatched
            if builtins.open is _ORIG_BUILTIN_OPEN and SandboxContext._global_depth > 0:
                SandboxContext._global_depth = 0
                SandboxContext._active_contexts.clear()

            # 1. Install network guard
            self.network.install()

            # 2. Update depth counters and stacks
            self._depth += 1
            SandboxContext._global_depth += 1
            SandboxContext._active_contexts.append(self)

            if not hasattr(SandboxContext._thread_local, "stack"):
                SandboxContext._thread_local.stack = []
            SandboxContext._thread_local.stack.append(self)

            # 3. Only install hooks on transition from 0 to 1
            if SandboxContext._global_depth == 1:
                ctx_cls = SandboxContext

                def safe_open(file, mode="r", *args, **kwargs):
                    if isinstance(file, int):
                        # File descriptor (stdin, stdout, stderr, etc.)
                        return _ORIG_IO_OPEN(file, mode, *args, **kwargs)

                    mode_str = str(mode)
                    perm = Permission.READ
                    if any(m in mode_str for m in ("w", "a", "+", "x")):
                        perm = Permission.WRITE

                    active_ctx = None
                    stack = getattr(ctx_cls._thread_local, "stack", None)
                    if stack:
                        active_ctx = stack[-1]
                    elif ctx_cls._active_contexts:
                        active_ctx = ctx_cls._active_contexts[-1]

                    if active_ctx is not None:
                        canon_path = active_ctx.validator.validate_access(file, perm)
                        return _ORIG_IO_OPEN(str(canon_path), mode, *args, **kwargs)
                    return _ORIG_IO_OPEN(file, mode, *args, **kwargs)

                def safe_popen(args, **kwargs):
                    cwd = kwargs.get("cwd")
                    active_ctx = None
                    stack = getattr(ctx_cls._thread_local, "stack", None)
                    if stack:
                        active_ctx = stack[-1]
                    elif ctx_cls._active_contexts:
                        active_ctx = ctx_cls._active_contexts[-1]

                    if active_ctx is not None:
                        sanitized_args = active_ctx.execution.validate_command(args, cwd=cwd)
                    else:
                        sanitized_args = args

                    kwargs["shell"] = False
                    return _ORIG_SUBPROCESS_POPEN(sanitized_args, **kwargs)

                builtins.open = safe_open
                io.open = safe_open
                subprocess.Popen = safe_popen

            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with SandboxContext._lock:
            if self._depth > 0:
                self._depth -= 1
                SandboxContext._global_depth = max(0, SandboxContext._global_depth - 1)

                # Pop from thread-local stack
                stack = getattr(SandboxContext._thread_local, "stack", None)
                if stack and self in stack:
                    for i in range(len(stack) - 1, -1, -1):
                        if stack[i] is self:
                            del stack[i]
                            break

                # Pop from global active contexts
                for i in range(len(SandboxContext._active_contexts) - 1, -1, -1):
                    if SandboxContext._active_contexts[i] is self:
                        del SandboxContext._active_contexts[i]
                        break

                # Decrement network guard
                self.network.uninstall()

                # Only restore original functions when all nested/concurrent contexts exit
                if SandboxContext._global_depth == 0:
                    builtins.open = _ORIG_BUILTIN_OPEN
                    io.open = _ORIG_IO_OPEN
                    subprocess.Popen = _ORIG_SUBPROCESS_POPEN

        return False

    @property
    def is_active(self) -> bool:
        return self._depth > 0
