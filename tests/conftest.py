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
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("APP_ENV", "test")


# --- #122 (M18-W7): no unit test reaches the network ----------------------------------------------
#
# The Swift suite holds this by construction (#59). The Python suite held it by convention: each
# client is mocked with `respx`, and only Arena's slice downloads were blocked. Now a connection to
# anything but this machine, or a name lookup of anything but `localhost`, raises in every test.
# The live contract tests (`RUN_CONTRACT_TESTS=1`) are the one way out, and they say so by running
# with that variable set.
LOCAL_NAMES = frozenset({"localhost", "127.0.0.1", "::1", ""})


def _is_local(host: object) -> bool:
    if not isinstance(host, str) or host in LOCAL_NAMES:
        return isinstance(host, str)
    try:
        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


class NetworkReachedError(RuntimeError):
    """A unit test tried to reach a machine other than this one (#122)."""


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    if os.environ.get("RUN_CONTRACT_TESTS") == "1":
        yield
        return
    real_connect, real_connect_ex, real_lookup = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo

    def refuse(address: object) -> None:
        if not (isinstance(address, tuple) and _is_local(address[0])):
            raise NetworkReachedError(f"a unit test reached the network: {address!r} (#122)")

    def connect(self: socket.socket, address: object) -> None:
        if self.family != socket.AF_UNIX:
            refuse(address)
        real_connect(self, address)  # type: ignore[arg-type]

    def connect_ex(self: socket.socket, address: object) -> int:
        if self.family != socket.AF_UNIX:
            refuse(address)
        return real_connect_ex(self, address)  # type: ignore[arg-type]

    def getaddrinfo(host: object, *args: object, **kwargs: object) -> object:
        if not _is_local(host.decode() if isinstance(host, bytes) else host):
            raise NetworkReachedError(f"a unit test looked up {host!r} (#122)")
        return real_lookup(host, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    yield


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


def pytest_configure(config: pytest.Config) -> None:
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
    if os.environ.get("MODEL_RANKING_REQUIRE_ARTIFACT") == "1" and not ARTIFACT.is_file():
        pytest.exit(
            f"W-108: this run must execute the tests that read {ARTIFACT}, and it is missing "
            "(MODEL_RANKING_REQUIRE_ARTIFACT=1). Build it, or run pytest without the flag.",
            returncode=4,
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    needing = [item for item in items if item.get_closest_marker("artifact")]
    if not needing or ARTIFACT.is_file():
        return
    skip = pytest.mark.skip(reason=f"W-108: needs the built {ARTIFACT}, which is not in the repo")
    for item in needing:
        item.add_marker(skip)
