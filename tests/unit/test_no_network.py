"""#122 (M18-W7): a unit test that reaches the network fails, whatever client it uses."""

from __future__ import annotations

import contextlib
import os
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
    # The W7 Tester's T3: the other way to send a datagram.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp, pytest.raises(NetworkReachedError):
        udp.sendmsg([b"x"], [], 0, ("192.0.2.1", 9))


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

    def lifted(path: str, value: str | None) -> bool:
        if value is None:
            monkeypatch.delenv("RUN_CONTRACT_TESTS", raising=False)
        else:
            monkeypatch.setenv("RUN_CONTRACT_TESTS", value)
        item = SimpleNamespace(path=Path(path))
        setup = conftest.pytest_runtest_setup(item)  # the hookwrappers, driven as pytest drives them
        next(setup)
        on = bool(conftest._LIFTED["on"])
        setup.close()
        teardown = conftest.pytest_runtest_teardown(item, None)
        next(teardown)
        # The test's fixtures are torn down here, still under the test's own rule (closure Tester R1).
        assert bool(conftest._LIFTED["on"]) == on, "the lift changed before the fixtures were torn down"
        with contextlib.suppress(StopIteration):
            next(teardown)
        left_lifted = bool(conftest._LIFTED["on"])
        conftest._LIFTED["on"] = False
        assert not left_lifted, "the guard was left lifted after the test"
        return on

    assert lifted("tests/integration/test_x_contract.py", "1")
    assert not lifted("tests/unit/test_x.py", "1")
    assert not lifted("tests/integration/test_x_contract.py", None)
    assert not lifted("tests/integration/test_x_contract.py", "0")


def test_a_live_contract_test_may_reach_out_from_any_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """The M18 repo review's M1: the step-out was per thread, and a contract test's downloads run on
    a worker thread, so every live contract test failed in CI. The rule is read here directly; no
    real request is made."""
    from tests import conftest

    monkeypatch.setenv("RUN_CONTRACT_TESTS", "1")
    assert conftest.is_live_contract_test("tests/integration/test_x.py")
    assert not conftest.is_live_contract_test("tests/unit/test_x.py")
    monkeypatch.setitem(conftest._LIFTED, "on", True)
    outcome: list[object] = []
    worker = threading.Thread(target=lambda: outcome.append(conftest._refuse_unless_local("example.com", "x")))
    worker.start()
    worker.join(5)
    assert outcome == [None], "a worker thread was refused while the step-out was on"
    monkeypatch.setitem(conftest._LIFTED, "on", False)
    with pytest.raises(NetworkReachedError):
        conftest._refuse_unless_local("example.com", "looked up")


def test_a_checkout_under_a_folder_named_integration_stays_guarded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The M18 closure Tester's R2: the rule read the whole path, so in a contract run a checkout
    under any folder named `integration` lifted the guard for every unit test. It reads the path
    from the repository down."""
    from tests import conftest

    monkeypatch.setenv("RUN_CONTRACT_TESTS", "1")
    assert not conftest.is_live_contract_test("/home/ci/integration/model_ranking/tests/unit/test_api_v1.py")
    assert not conftest.is_live_contract_test(conftest._ROOT / "tests" / "unit" / "integration" / "test_x.py")
    assert conftest.is_live_contract_test(conftest._ROOT / "tests" / "integration" / "test_x_contract.py")


def test_a_proxy_in_the_shell_reaches_no_unit_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """#143 (the M18 closure security seat's S8). The guard allows this machine, so a proxy variable
    naming a proxy here would carry a unit test's request out through it. The run hides the proxy
    variables; a live contract test gets them back for its own run, and loses them after."""
    from types import SimpleNamespace

    from tests import conftest

    assert not conftest.proxy_names(), "a unit test sees a proxy variable"
    saved = dict(conftest._SAVED_PROXIES)
    try:
        monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
        monkeypatch.setenv("all_proxy", "socks5://127.0.0.1:9")
        monkeypatch.setenv("Ftp_Proxy", "http://127.0.0.1:9")  # any case (the fix Tester's K2)
        monkeypatch.setenv("NO_PROXY", "localhost")  # not a proxy: left alone
        conftest._hide_proxies()
        assert not conftest.proxy_names()
        assert os.environ.get("NO_PROXY") == "localhost"

        def during(path: str) -> bool:
            item = SimpleNamespace(path=Path(path))
            setup = conftest.pytest_runtest_setup(item)
            next(setup)
            seen = os.environ.get("HTTPS_PROXY") == "http://127.0.0.1:9"
            setup.close()
            teardown = conftest.pytest_runtest_teardown(item, None)
            next(teardown)
            with contextlib.suppress(StopIteration):
                next(teardown)
            conftest._LIFTED["on"] = False
            assert "HTTPS_PROXY" not in os.environ, "the proxy outlived the test that was given it"
            return seen

        monkeypatch.setenv("RUN_CONTRACT_TESTS", "1")
        assert during("tests/integration/test_x_contract.py"), "a live contract test lost the proxy"
        assert not during("tests/unit/test_x.py"), "a unit test was handed the proxy"
    finally:
        conftest._SAVED_PROXIES.clear()
        conftest._SAVED_PROXIES.update(saved)


def test_an_xdist_worker_is_handed_the_proxies_its_controller_hid() -> None:
    """The fix Tester's R2: the controller hides the proxies before it starts its workers, so under
    `-n` a live contract test on a worker had none to get back. The controller hands them over in
    the worker's input, and the worker takes them as its own to give back."""
    from types import SimpleNamespace

    from tests import conftest

    saved = dict(conftest._SAVED_PROXIES)
    try:
        conftest._SAVED_PROXIES.clear()
        conftest._SAVED_PROXIES["HTTPS_PROXY"] = "http://127.0.0.1:9"
        node = SimpleNamespace(workerinput={})
        conftest.pytest_configure_node(node)
        worker = SimpleNamespace(workerinput=node.workerinput)
        assert conftest.handed_proxies(worker) == {"HTTPS_PROXY": "http://127.0.0.1:9"}
        assert conftest.handed_proxies(SimpleNamespace()) == {}, "a run without xdist is handed nothing"
    finally:
        conftest._SAVED_PROXIES.clear()
        conftest._SAVED_PROXIES.update(saved)


@pytest.mark.skipif(not hasattr(__import__("urllib.request").request, "getproxies_macosx_sysconf"),
                    reason="macOS's System Configuration fallback (#150)")
def test_a_system_proxy_reaches_no_unit_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """#150. With every proxy variable hidden (#143), urllib's `getproxies()`, which httpx asks,
    falls back on macOS to the System Configuration's proxies. A system proxy on this machine would
    carry a unit test's request out. The operating system's answer is planted below urllib."""
    import urllib.request

    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)  # an empty environment is what lets the fallback run
    monkeypatch.setattr(urllib.request, "_get_proxies", lambda: {"https": "http://127.0.0.1:9"})
    assert urllib.request.getproxies() == {}, "a system proxy reached a unit test"


def test_a_live_contract_test_keeps_the_system_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """#150: the system's proxies are hidden from a unit test only; a live contract test asks the
    real fallback, as it gets the proxy variables back."""
    from tests import conftest

    monkeypatch.setattr(conftest, "_REAL_SYSTEM_PROXIES", lambda: {"https": "http://127.0.0.1:9"})
    assert conftest.system_proxies() == {}
    monkeypatch.setitem(conftest._LIFTED, "on", True)
    assert conftest.system_proxies() == {"https": "http://127.0.0.1:9"}
