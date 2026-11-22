"""
Zero-Telemetry Socket Interception and Network Egress Guard.

Intercepts low-level TCP and UDP socket operations (socket.connect, socket.connect_ex,
socket.sendto) and DNS lookups (socket.getaddrinfo, socket.gethostbyname,
socket.gethostbyname_ex) to strictly prohibit external data leakage and telemetry
while allowing local loopback connections (127.0.0.1, localhost, port 8000).
"""

import socket
import threading
from typing import Set, Tuple, Optional, Union, Any, List

from sandbox.exceptions import NetworkEgressBlocked

DEFAULT_LOOPBACK_HOSTS: Set[str] = {
    "127.0.0.1",
    "localhost",
    "::1",
    "0.0.0.0",
    "::ffff:127.0.0.1",
    "ip6-localhost",
    "ip6-loopback",
}

# Preserve genuine unpatched socket module functions at import time
_ORIG_SOCKET_CONNECT = socket.socket.connect
_ORIG_SOCKET_CONNECT_EX = socket.socket.connect_ex
_ORIG_SOCKET_SENDTO = socket.socket.sendto
_ORIG_GETADDRINFO = socket.getaddrinfo
_ORIG_GETHOSTBYNAME = socket.gethostbyname
_ORIG_GETHOSTBYNAME_EX = socket.gethostbyname_ex
_ORIG_GETHOSTBYADDR = socket.gethostbyaddr


class NetworkGuard:
    """
    Guards network sockets against outbound exfiltration and telemetry.
    Permits local loopback traffic (required for OpenVINO local server on port 8000).
    Maintains re-entrant depth tracking and thread safety.
    """

    _lock = threading.RLock()
    _global_depth = 0
    _active_guards: List["NetworkGuard"] = []

    def __init__(self, allowed_hosts: Optional[Set[str]] = None):
        self.allowed_hosts: Set[str] = set(
            h.lower() for h in (allowed_hosts or DEFAULT_LOOPBACK_HOSTS)
        )
        self._depth = 0
        self._original_connect = _ORIG_SOCKET_CONNECT
        self._original_connect_ex = _ORIG_SOCKET_CONNECT_EX
        self._original_sendto = _ORIG_SOCKET_SENDTO
        self._original_getaddrinfo = _ORIG_GETADDRINFO
        self._original_gethostbyname = _ORIG_GETHOSTBYNAME
        self._original_gethostbyname_ex = _ORIG_GETHOSTBYNAME_EX
        self._original_gethostbyaddr = _ORIG_GETHOSTBYADDR

    def is_destination_allowed(self, address: Any) -> bool:
        """Check if target network destination is within the loopback whitelist."""
        if address is None:
            return True

        if isinstance(address, tuple) and len(address) >= 1:
            host = str(address[0]).lower().strip("[]")
        elif isinstance(address, str):
            host = address.lower().strip("[]")
        else:
            return False

        return host in self.allowed_hosts

    def install(self):
        """Install socket and DNS hooks into Python's socket module."""
        with NetworkGuard._lock:
            # Self-heal if hooks were externally unpatched (e.g. by test runner fixtures)
            if socket.socket.connect is _ORIG_SOCKET_CONNECT and NetworkGuard._global_depth > 0:
                NetworkGuard._global_depth = 0
                NetworkGuard._active_guards.clear()

            self._depth += 1
            NetworkGuard._global_depth += 1
            NetworkGuard._active_guards.append(self)

            if NetworkGuard._global_depth == 1:
                guard_cls = NetworkGuard

                def safe_connect(sock_instance, address):
                    with guard_cls._lock:
                        if not any(g.is_destination_allowed(address) for g in guard_cls._active_guards):
                            dest_str = (
                                f"{address[0]}:{address[1]}"
                                if isinstance(address, tuple) and len(address) >= 2
                                else str(address)
                            )
                            raise NetworkEgressBlocked(
                                f"Outbound network egress blocked: Connection attempt to '{dest_str}' rejected."
                            )
                    return _ORIG_SOCKET_CONNECT(sock_instance, address)

                def safe_connect_ex(sock_instance, address):
                    with guard_cls._lock:
                        if not any(g.is_destination_allowed(address) for g in guard_cls._active_guards):
                            dest_str = (
                                f"{address[0]}:{address[1]}"
                                if isinstance(address, tuple) and len(address) >= 2
                                else str(address)
                            )
                            raise NetworkEgressBlocked(
                                f"Outbound network egress blocked: Connection attempt to '{dest_str}' rejected via connect_ex."
                            )
                    return _ORIG_SOCKET_CONNECT_EX(sock_instance, address)

                def safe_sendto(sock_instance, data, *args, **kwargs):
                    address = None
                    if args:
                        address = args[0] if len(args) == 1 else args[1]
                    elif "address" in kwargs:
                        address = kwargs["address"]

                    if address is not None:
                        with guard_cls._lock:
                            if not any(g.is_destination_allowed(address) for g in guard_cls._active_guards):
                                dest_str = (
                                    f"{address[0]}:{address[1]}"
                                    if isinstance(address, tuple) and len(address) >= 2
                                    else str(address)
                                )
                                raise NetworkEgressBlocked(
                                    f"Outbound UDP transmission blocked: Egress attempt to '{dest_str}' rejected."
                                )
                    return _ORIG_SOCKET_SENDTO(sock_instance, data, *args, **kwargs)

                def safe_getaddrinfo(host, port=None, *args, **kwargs):
                    if host is not None and str(host).strip():
                        h = str(host).lower().strip("[]")
                        with guard_cls._lock:
                            if not any(g.is_destination_allowed(h) for g in guard_cls._active_guards):
                                raise NetworkEgressBlocked(
                                    f"Outbound DNS resolution blocked: Lookup attempt for '{host}' rejected."
                                )
                    return _ORIG_GETADDRINFO(host, port, *args, **kwargs)

                def safe_gethostbyname(hostname):
                    if hostname is not None and str(hostname).strip():
                        h = str(hostname).lower().strip("[]")
                        with guard_cls._lock:
                            if not any(g.is_destination_allowed(h) for g in guard_cls._active_guards):
                                raise NetworkEgressBlocked(
                                    f"Outbound DNS resolution blocked: Lookup attempt for '{hostname}' rejected."
                                )
                    return _ORIG_GETHOSTBYNAME(hostname)

                def safe_gethostbyname_ex(hostname):
                    if hostname is not None and str(hostname).strip():
                        h = str(hostname).lower().strip("[]")
                        with guard_cls._lock:
                            if not any(g.is_destination_allowed(h) for g in guard_cls._active_guards):
                                raise NetworkEgressBlocked(
                                    f"Outbound DNS resolution blocked: Lookup attempt for '{hostname}' rejected."
                                )
                    return _ORIG_GETHOSTBYNAME_EX(hostname)

                def safe_gethostbyaddr(ip_address):
                    if ip_address is not None and str(ip_address).strip():
                        h = str(ip_address).lower().strip("[]")
                        with guard_cls._lock:
                            if not any(g.is_destination_allowed(h) for g in guard_cls._active_guards):
                                raise NetworkEgressBlocked(
                                    f"Outbound DNS resolution blocked: Reverse lookup attempt for '{ip_address}' rejected."
                                )
                    return _ORIG_GETHOSTBYADDR(ip_address)

                socket.socket.connect = safe_connect
                socket.socket.connect_ex = safe_connect_ex
                socket.socket.sendto = safe_sendto
                socket.getaddrinfo = safe_getaddrinfo
                socket.gethostbyname = safe_gethostbyname
                socket.gethostbyname_ex = safe_gethostbyname_ex
                socket.gethostbyaddr = safe_gethostbyaddr

    def uninstall(self):
        """Restore original unpatched socket methods when depth drops to 0."""
        with NetworkGuard._lock:
            if self._depth > 0:
                self._depth -= 1
                NetworkGuard._global_depth = max(0, NetworkGuard._global_depth - 1)
                for i in range(len(NetworkGuard._active_guards) - 1, -1, -1):
                    if NetworkGuard._active_guards[i] is self:
                        del NetworkGuard._active_guards[i]
                        break

                if NetworkGuard._global_depth == 0:
                    socket.socket.connect = _ORIG_SOCKET_CONNECT
                    socket.socket.connect_ex = _ORIG_SOCKET_CONNECT_EX
                    socket.socket.sendto = _ORIG_SOCKET_SENDTO
                    socket.getaddrinfo = _ORIG_GETADDRINFO
                    socket.gethostbyname = _ORIG_GETHOSTBYNAME
                    socket.gethostbyname_ex = _ORIG_GETHOSTBYNAME_EX
                    socket.gethostbyaddr = _ORIG_GETHOSTBYADDR

    @property
    def is_active(self) -> bool:
        return self._depth > 0
