"""#122 (M18-W7): a unit test that reaches the network fails, whatever client it uses."""

from __future__ import annotations

import socket
import threading
from pathlib import Path

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


def test_the_other_socket_doors_are_closed_too() -> None:
    """The W7 review's M1: name lookups other than `getaddrinfo`, and a UDP datagram, passed."""
    with pytest.raises(NetworkReachedError):
        socket.gethostbyname("example.com")
    with pytest.raises(NetworkReachedError):
        socket.gethostbyaddr("192.0.2.1")
    with pytest.raises(NetworkReachedError):
        socket.getnameinfo(("192.0.2.1", 80), 0)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp, pytest.raises(NetworkReachedError):
        udp.sendto(b"x", ("192.0.2.1", 9))


# --- The M18-W7 Tester's additions. Each door is tried with a call that sends nothing even if the
# door were open: a UDP `connect` only sets the peer, and a numeric name needs no resolver.

#: Read when this module is imported, before any fixture runs. The guard is installed when pytest is
#: configured, so this is already the guarded lookup.
_LOOKUP_AT_IMPORT = socket.getaddrinfo


def test_the_guard_is_in_place_before_any_test_module_is_imported() -> None:
    """Tester (M18-W7): the W7 review's M1 moved the guard to `pytest_configure`, so code run at
    import, and fixtures of every scope, are covered. Installed per test instead, the suite passed."""
    assert _LOOKUP_AT_IMPORT is socket.getaddrinfo, "the lookup seen at import is not the guarded one"
    assert _LOOKUP_AT_IMPORT.__module__ == NetworkReachedError.__module__


def test_the_connect_doors_refuse_a_numeric_address() -> None:
    """Tester (M18-W7): `create_connection` and `httpx` look the name up first, so the planted
    requests above stop at `getaddrinfo` and never reach `connect`. With the `connect` or
    `connect_ex` door open, or IPv6 left out of it, the suite stayed green."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp, pytest.raises(NetworkReachedError):
        udp.connect(("192.0.2.1", 9))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp, pytest.raises(NetworkReachedError):
        udp.connect_ex(("192.0.2.1", 9))
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as udp6, pytest.raises(NetworkReachedError):
        udp6.connect(("2001:db8::1", 9))
    with pytest.raises(NetworkReachedError):
        socket.gethostbyname_ex("192.0.2.1")


def test_only_a_live_contract_test_steps_out_of_the_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tester (M18-W7): the step-out is `RUN_CONTRACT_TESTS=1` AND a test under `tests/integration`,
    and the guard is back after it. CI's contract job sets the variable for a whole run, so a step-out
    by the variable alone would lift the guard from every unit test in it."""
    from types import SimpleNamespace

    from tests import conftest

    step_out = conftest._live_contract_tests_may_reach_out.__wrapped__

    def lifted(path: str, value: str | None) -> bool:
        if value is None:
            monkeypatch.delenv("RUN_CONTRACT_TESTS", raising=False)
        else:
            monkeypatch.setenv("RUN_CONTRACT_TESTS", value)
        steps = step_out(SimpleNamespace(node=SimpleNamespace(path=Path(path))))
        try:
            next(steps)
            return bool(conftest._LIFTED.on)
        finally:
            steps.close()
            left_lifted = bool(getattr(conftest._LIFTED, "on", False))
            conftest._LIFTED.on = False
            assert not left_lifted, "the guard was left lifted after the test"

    assert lifted("tests/integration/test_x_contract.py", "1")
    assert not lifted("tests/unit/test_x.py", "1")
    assert not lifted("tests/integration/test_x_contract.py", None)
    assert not lifted("tests/integration/test_x_contract.py", "0")
