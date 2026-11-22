"""
Sandbox Security Exceptions.

Hierarchical exception taxonomy for application-level confinement,
path validation, subprocess execution, network egress, and boundary authorization.
"""


class SecuritySandboxViolation(Exception):
    """Base exception for all sandbox security policy violations."""
    pass


class PathTraversalViolation(SecuritySandboxViolation):
    """Raised when an operation attempts to access files outside allowed boundaries or via illegal traversal."""
    pass


class AlternateDataStreamViolation(SecuritySandboxViolation):
    """Raised when an NTFS Alternate Data Stream pattern (colon injection) is detected."""
    pass


class DeviceNameViolation(SecuritySandboxViolation):
    """Raised when a reserved Windows device name (CON, PRN, AUX, NUL, COM1-9, LPT1-9) is accessed."""
    pass


class ExecutionBlockedViolation(SecuritySandboxViolation):
    """Raised when command execution or binary invocation violates sandbox policy."""
    pass


class NetworkEgressBlocked(SecuritySandboxViolation):
    """Raised when outbound network communication is attempted outside loopback whitelist."""
    pass


class AuthenticationError(SecuritySandboxViolation):
    """Raised when password authentication fails during boundary modification."""
    pass


class TamperProtectionViolation(SecuritySandboxViolation):
    """Raised when an unauthorized write or delete targeting sandbox configuration or system files is attempted."""
    pass
