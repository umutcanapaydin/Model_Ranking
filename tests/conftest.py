"""Test-suite environment declaration.

`app.adapter.main` validates its security configuration at import and, since the Stage-4.0 review,
an unset or unrecognised `APP_ENV` is the STRICT branch — a process that cannot tell where it runs
assumes production. That is the correct default and it is why importing the module in a bare test
environment now raises.

So the suite declares what it is, once, here. **This is a declaration, not a suppression:** the
tests that exercise the strict branch pass `env=` explicitly (`test_api_config.py`) or spawn a real
subprocess with `APP_ENV=production` set, and neither is affected by this line. What it removes is
only the accident of collection order deciding whether the app can be imported at all.
"""

from __future__ import annotations

import ipaddress
import os
import socket
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests import skips

os.environ.setdefault("APP_ENV", "test")


# --- #122 (M18-W7): no unit test reaches the network ----------------------------------------------
#
# The Swift suite holds this by construction (#59). The Python suite held it by convention: each
# client is mocked with `respx`, and only Arena's slice downloads were blocked. Now, from the moment
# pytest is configured (so fixtures of every scope, and code run at import, are covered), a
# connection, a datagram or a name lookup that reaches anything but this machine raises. The one way
# out is a live contract test (`tests/integration`, with `RUN_CONTRACT_TESTS=1`), test by test. A child
# process a test starts is NOT covered: no in-process guard reaches it (the W7 review's M1, #122).
LOCAL_NAMES = frozenset({"localhost", "127.0.0.1", "::1", ""})


def _is_local(host: object) -> bool:
    if isinstance(host, bytes):
        host = host.decode(errors="replace")
    if not isinstance(host, str):
        return False
    if host in LOCAL_NAMES:
        return True
    try:
        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


class NetworkReachedError(RuntimeError):
    """A unit test tried to reach a machine other than this one (#122)."""


_REAL: dict[str, object] = {}
#: Process-wide, not per thread: a live contract test's downloads run on a worker thread
#: (`protocols.bounded_get`), and a thread-local exemption stopped every one of them in CI (the M18
#: repo review's M1). Set before the test's fixtures, module-scoped ones included, and cleared after.
_LIFTED = {"on": False}


def _refuse_unless_local(host: object, what: str) -> None:
    if not _LIFTED["on"] and not _is_local(host):
        raise NetworkReachedError(f"a unit test {what} {host!r} (#122)")


def _install_network_guard() -> None:
    sock, real = socket.socket, _REAL
    real.update(connect=sock.connect, connect_ex=sock.connect_ex, sendto=sock.sendto, sendmsg=sock.sendmsg,
                getaddrinfo=socket.getaddrinfo, gethostbyname=socket.gethostbyname,
                gethostbyname_ex=socket.gethostbyname_ex, gethostbyaddr=socket.gethostbyaddr,
                getnameinfo=socket.getnameinfo)

    def address_host(address: object) -> object:
        return address[0] if isinstance(address, tuple) and address else address

    def connect(self: socket.socket, address: object) -> None:
        if self.family != socket.AF_UNIX:
            _refuse_unless_local(address_host(address), "reached")
        real["connect"](self, address)  # type: ignore[operator]

    def connect_ex(self: socket.socket, address: object) -> int:
        if self.family != socket.AF_UNIX:
            _refuse_unless_local(address_host(address), "reached")
        return real["connect_ex"](self, address)  # type: ignore[operator, no-any-return]

    def sendto(self: socket.socket, data: bytes, *args: object) -> int:
        if self.family != socket.AF_UNIX:
            _refuse_unless_local(address_host(args[-1]), "sent a datagram to")
        return real["sendto"](self, data, *args)  # type: ignore[operator, no-any-return]

    def sendmsg(self: socket.socket, buffers: object, *args: object, **kwargs: object) -> int:
        address = kwargs.get("address", args[2] if len(args) > 2 else None)
        if self.family != socket.AF_UNIX and address is not None:  # the W7 Tester's T3
            _refuse_unless_local(address_host(address), "sent a datagram to")
        return real["sendmsg"](self, buffers, *args, **kwargs)  # type: ignore[operator, no-any-return]

    def lookup(name: str, position: int = 0) -> object:
        def guarded(*args: object, **kwargs: object) -> object:
            _refuse_unless_local(args[position] if len(args) > position else None, "looked up")
            return real[name](*args, **kwargs)  # type: ignore[operator]
        return guarded

    def getnameinfo(sockaddr: object, flags: int) -> object:
        _refuse_unless_local(address_host(sockaddr), "looked up")
        return real["getnameinfo"](sockaddr, flags)  # type: ignore[operator]

    sock.connect, sock.connect_ex, sock.sendto, sock.sendmsg = connect, connect_ex, sendto, sendmsg  # type: ignore[method-assign, assignment]
    socket.getaddrinfo = lookup("getaddrinfo")  # type: ignore[assignment]
    socket.gethostbyname = lookup("gethostbyname")  # type: ignore[assignment]
    socket.gethostbyname_ex = lookup("gethostbyname_ex")  # type: ignore[assignment]
    socket.gethostbyaddr = lookup("gethostbyaddr")  # type: ignore[assignment]
    socket.getnameinfo = getnameinfo  # type: ignore[assignment]


def _remove_network_guard() -> None:
    for name in ("connect", "connect_ex", "sendto", "sendmsg"):
        if name in _REAL:
            setattr(socket.socket, name, _REAL[name])
    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo"):
        if name in _REAL:
            setattr(socket, name, _REAL[name])
    _REAL.clear()


_ROOT = Path(__file__).resolve().parents[1]

#: #143 (the M18 closure security seat's S8): the guard allows this machine, so a proxy variable
#: naming a proxy here would carry a unit test's request out through it. The run hides them, and a
#: live contract test gets them back for its own run.
_SAVED_PROXIES: dict[str, str] = {}
#: How an xdist controller hands its hidden proxies to the workers it starts after hiding them.
_HANDED = "model_ranking_hidden_proxies"


def proxy_names() -> list[str]:
    """Every variable urllib reads as a proxy (`getproxies_environment`): a name that ends in
    `_proxy`, in any case, but `no_proxy`. Derived from urllib's rule, not listed (the fix Tester's
    K2: `Https_Proxy` passed a list of six)."""
    return [name for name in os.environ if name.lower().endswith("_proxy") and name.lower() != "no_proxy"]


def _hide_proxies() -> None:
    for name in proxy_names():
        _SAVED_PROXIES[name] = os.environ.pop(name)


def handed_proxies(config: object) -> dict[str, str]:
    """What an xdist controller handed this worker (the fix Tester's R2): the controller hid the
    proxies before it started its workers, so a worker's own environment holds none to give back."""
    handed = getattr(config, "workerinput", {}).get(_HANDED, {})
    return {str(name): str(value) for name, value in handed.items()}


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node: Any) -> None:
    node.workerinput[_HANDED] = dict(_SAVED_PROXIES)


#: #150: with every proxy variable hidden, urllib's `getproxies()`, which httpx asks, falls back on
#: macOS to the System Configuration's proxies, so a system proxy here would do what a variable did.
#: The fallback is looked up by name when `getproxies()` runs, so replacing it covers httpx too.
_REAL_SYSTEM_PROXIES: Any = getattr(urllib.request, "getproxies_macosx_sysconf", None)


def system_proxies() -> dict[str, str]:
    """No system proxy for a unit test; a live contract test asks the real fallback."""
    if _LIFTED["on"] and _REAL_SYSTEM_PROXIES is not None:
        return dict(_REAL_SYSTEM_PROXIES())
    return {}


def is_live_contract_test(path: object) -> bool:
    """A test under this repository's `tests/integration`, in a run that asked for the live sources.

    The path is read from the repository down (the M18 closure Tester's R2): read whole, a checkout
    under any folder named `integration` lifted the guard for every test in a contract run."""
    if os.environ.get("RUN_CONTRACT_TESTS") != "1":
        return False
    where = Path(str(path))
    if where.is_absolute():
        try:
            where = where.resolve().relative_to(_ROOT)
        except ValueError:
            return False
    return where.parts[:2] == ("tests", "integration")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: pytest.Item) -> Iterator[None]:
    _LIFTED["on"] = is_live_contract_test(item.path)  # before the fixtures, whatever their scope
    if _LIFTED["on"]:
        os.environ.update(_SAVED_PROXIES)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> Iterator[None]:
    yield
    _LIFTED["on"] = False
    _hide_proxies()


# --- W-108: the tests that read the real artifact ------------------------------------------------
#
# Forty-five tests read `advisor.db`, the built artifact, which is gitignored and holds licensed
# upstream data this PUBLIC repository may not redistribute. On a fresh clone they failed as 45
# errors that meant nothing, so no one outside the owner's machine could tell a real failure from
# a missing file. They are marked `artifact` and SKIPPED, by name, where the file is absent -- and
# `make test` sets MODEL_RANKING_REQUIRE_ARTIFACT=1, so on the machine that must run them a missing
# artifact is a hard error rather than a quiet skip. A skip that can hide the owner's run would be
# the "skipped job reports SUCCESS" defect this project has already paid for once.
ARTIFACT = Path("advisor.db")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--ci-skips-report", default=None,
                     help="#137: write how many tests CI's test job will skip, from their `needs` markers")


def pytest_configure(config: pytest.Config) -> None:
    skips.configure(config)  # #137: the `needs` marker
    _install_network_guard()  # #122: before collection, so imports and every fixture are covered
    _hide_proxies()  # #143
    if _REAL_SYSTEM_PROXIES is not None:  # #150: macOS only; no other platform falls back here
        urllib.request.getproxies_macosx_sysconf = system_proxies
    _SAVED_PROXIES.update(handed_proxies(config))
    config.addinivalue_line(
        "markers", "artifact: reads the built advisor.db (gitignored; W-108). Skipped where absent."
    )
    config.addinivalue_line(
        "markers", "slices: builds with Arena's category slices, through an injected fake client."
    )
    config.addinivalue_line(
        "markers", "slice_download: reaches ArenaSliceClient.fetch_bytes: respx-mocked in unit tests, the live file in the env-gated contract test."
    )


# --- M17-W2: the build's category slices stay off the network ------------------------------------
#
# `build()` reads `ARENA_SLICES` at call time, like every other source table, and downloads each
# config's file from the internet. Tests never reach the network (permission-matrix §3), and nine
# test files build an artifact while patching only the source tables that existed before the
# slices. So every test builds with NO slices unless it is marked `slices`, and a marked test
# injects its own client. A declaration of what the suite does, not a suppression:
# `tests/unit/test_build_slices.py` builds with the real table and a fake download, and asserts
# that an unmarked test sees none.
#
# Below the table, the client itself refuses to download in every test (re-review MINOR-R2: a guard
# on the build's default missed `fetch_slices` and `measure_slices`). Only a test marked
# `slice_download` reaches the real method: unit tests that mock the transport with respx, and the
# env-gated live contract test (RUN_CONTRACT_TESTS=1).
def _tests_never_reach_the_network(self: object) -> bytes:
    from app.clients.protocols import SourceError

    msg = "tests never reach the network: inject a fake slice client (app.clients.fakes)"
    raise SourceError(msg)


@pytest.fixture(autouse=True)
def _slices_stay_off_the_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.clients.arena_slices import ArenaSliceClient
    from app.workflows import build as build_mod

    if request.node.get_closest_marker("slice_download") is None:
        monkeypatch.setattr(ArenaSliceClient, "fetch_bytes", _tests_never_reach_the_network)
    if request.node.get_closest_marker("slices") is None:
        monkeypatch.setattr(build_mod, "ARENA_SLICES", ())


def pytest_sessionstart(session: pytest.Session) -> None:
    # In the controlling process, before any worker collects: raised inside an xdist worker the
    # same refusal surfaces as an INTERNALERROR traceback that does not say what is missing.
    if os.environ.get("MODEL_RANKING_REQUIRE_OFFLINE") == "1" and not skips.offline():
        pytest.exit(
            "#122: this run must be offline at the operating system's level (MODEL_RANKING_REQUIRE_OFFLINE=1), "
            "and a child process could still reach the network. Run it through `make test`, which wraps it in "
            "scripts/offline.sb on macOS.",
            returncode=4,
        )
    if os.environ.get("MODEL_RANKING_REQUIRE_ARTIFACT") == "1" and not ARTIFACT.is_file():
        pytest.exit(
            f"W-108: this run must execute the tests that read {ARTIFACT}, and it is missing "
            "(MODEL_RANKING_REQUIRE_ARTIFACT=1). Build it, or run pytest without the flag.",
            returncode=4,
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    # #137: every skip goes through `needs` (`tests/skips.py`), which also counts CI's.
    skips.apply(config, items)


def pytest_unconfigure(config: pytest.Config) -> None:
    _remove_network_guard()
    os.environ.update(_SAVED_PROXIES)
    if _REAL_SYSTEM_PROXIES is not None:
        urllib.request.getproxies_macosx_sysconf = _REAL_SYSTEM_PROXIES
