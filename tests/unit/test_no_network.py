"""#122 (M18-W7): a unit test that reaches the network fails, whatever client it uses."""

from __future__ import annotations

import socket
import threading

import httpx
import pytest

from tests.conftest import NetworkReachedError


def test_a_planted_real_request_fails_the_test() -> None:
    with pytest.raises(NetworkReachedError):
        socket.create_connection(("192.0.2.1", 80), timeout=1)
    with pytest.raises(NetworkReachedError):
        socket.getaddrinfo("example.com", 443)
    with pytest.raises((NetworkReachedError, httpx.HTTPError)) as caught:
        httpx.get("https://example.com/", timeout=1)
    assert "network" in str(caught.value) or "looked up" in str(caught.value)


def test_this_machine_is_still_reachable() -> None:
    """The fetch tests serve on 127.0.0.1 (test_fetch_bounds.py); the guard leaves them alone."""
    server = socket.create_server(("127.0.0.1", 0))
    port = server.getsockname()[1]
    accepted = threading.Thread(target=lambda: server.accept()[0].close(), daemon=True)
    accepted.start()
    with socket.create_connection(("127.0.0.1", port), timeout=2):
        pass
    accepted.join(2)
    server.close()
