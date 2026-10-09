"""#122, its second half (gap G-5), option B: the test run is offline at the operating system's level.

The in-process guard (`tests/conftest.py`) refuses a connection the pytest process opens. A child a
test starts is another process, and 21 test files start them: one given a scrubbed environment, a
`curl` in a script, or the nightly's refresh child would reach the network unseen. On macOS
`make test` now runs pytest inside a `sandbox-exec` profile (`scripts/offline.sb`) that refuses every
outbound connection but loopback, so every child is offline whatever its language. CI's half is a
patch for the owner (`.github/workflows/**` is theirs).

The probe sends nothing: a UDP `connect()` only records a peer, so outside the sandbox it succeeds with
no packet, and inside it the operating system refuses it (`EPERM`).
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: A child's attempt to name a peer off this machine. TEST-NET-1, and UDP, so no packet in any case.
UDP_PROBE = (
    "import errno, socket\n"
    "s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
    "try:\n"
    "    s.connect(('192.0.2.1', 9))\n"
    "    print('reached')\n"
    "except OSError as e:\n"
    "    print('refused' if e.errno in (errno.EPERM, errno.EACCES, errno.ENETUNREACH) else e)\n"
)


def _make_test(uname: str) -> str:
    """The pytest command `make test` would run on `uname`; its comment lines are not commands."""
    lines = subprocess.run(["make", "-n", "test", f"UNAME_S={uname}"], cwd=ROOT, capture_output=True, text=True,
                           check=False, timeout=120).stdout.splitlines()
    return next((line for line in lines if "-m pytest" in line and not line.lstrip().startswith("#")), "")


def test_make_test_runs_the_suite_offline_on_macos() -> None:
    """#122 (option B): on macOS the suite runs inside the offline profile, and says it must be."""
    darwin = _make_test("Darwin")
    assert "sandbox-exec -f scripts/offline.sb" in darwin and "MODEL_RANKING_REQUIRE_OFFLINE=1" in darwin, darwin
    assert "sandbox-exec" not in _make_test("Linux"), "Linux has no sandbox-exec; CI's half is the owner's patch"


def test_a_run_that_must_be_offline_and_is_not_stops_before_any_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """#122: a run told it must be offline, where a child could still reach the network, stops at once
    rather than running every test with the guard missing (fail closed)."""
    from tests import conftest, skips

    monkeypatch.setenv("MODEL_RANKING_REQUIRE_OFFLINE", "1")
    monkeypatch.setattr(skips, "offline", lambda: False, raising=False)
    with pytest.raises(pytest.exit.Exception, match="offline"):
        conftest.pytest_sessionstart(None)  # type: ignore[arg-type]


@pytest.mark.needs("offline")
def test_a_child_process_the_suite_starts_cannot_name_an_outside_peer() -> None:
    """#122: a child of the test run is refused by the operating system, not by a Python guard it
    may not carry: a Python child with a scrubbed environment, and `curl`, which is no Python at all.
    It runs where the run is offline (`needs("offline")`): elsewhere the TCP half would send a packet."""
    child = subprocess.run([sys.executable, "-c", UDP_PROBE], capture_output=True, text=True, timeout=30,
                           check=False, env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
    assert child.stdout.strip() == "refused", child.stdout + child.stderr
    curl = subprocess.run(["curl", "-sS", "--max-time", "5", "-o", "/dev/null", "http://192.0.2.1:9/"],
                          capture_output=True, text=True, timeout=30, check=False)
    assert curl.returncode == 7, curl.stderr  # "couldn't connect": refused before a packet left


@pytest.mark.needs("offline", "macos")  # the resolver's socket path is macOS's (the W3 Tester's M1)
def test_a_child_process_cannot_look_a_name_up_either() -> None:
    """The W3 review's M5: the profile left the system resolver's socket open, so a child resolved
    `example.com` and the lookup left the machine. The resolver's socket is refused now; connecting to
    a unix socket sends nothing anywhere, so the probe is safe either way."""
    probe = ("import socket\ns = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n"
             "try:\n    s.connect('/private/var/run/mDNSResponder')\n    print('reached')\n"
             "except PermissionError:\n    print('refused')\n")
    child = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=30, check=False)
    assert child.stdout.strip() == "refused", child.stdout + child.stderr


def test_a_child_process_still_reaches_loopback() -> None:
    """#122: the engine tests talk to a server on loopback; the profile leaves it open."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    host, port = listener.getsockname()
    try:
        child = subprocess.run([sys.executable, "-c",
                                f"import socket; socket.create_connection(({host!r}, {port}), timeout=5); print('ok')"],
                               capture_output=True, text=True, timeout=30, check=False)
        assert child.stdout.strip() == "ok", child.stdout + child.stderr
    finally:
        listener.close()


def _make_test_in(env: dict[str, str]) -> str:
    lines = subprocess.run(["make", "-n", "test"], cwd=ROOT, capture_output=True, text=True, check=False, timeout=120,
                           env={**os.environ, **env}).stdout.splitlines()
    return next((line for line in lines if "-m pytest" in line and not line.lstrip().startswith("#")), "")


def test_make_test_still_counts_the_skips_ci_will_take() -> None:
    """The W3 review's M4: with `--derive` removed from `make test`, every test stayed green (#137)."""
    lines = subprocess.run(["make", "-n", "test"], cwd=ROOT, capture_output=True, text=True, check=False,
                           timeout=120).stdout
    assert "scripts/coverage_floor.py --derive" in lines


def test_the_environment_cannot_turn_the_offline_run_off() -> None:
    """The W3 review's M6: `UNAME_S=Linux` in the environment removed the sandbox and its refusal on
    a Mac (`?=`). Only the command line may name the system, as the tests here do."""
    assert _make_test_in({"UNAME_S": "Linux"}) == _make_test_in({})


def test_make_tests_own_marker_requires_the_offline_run_on_a_mac(monkeypatch: pytest.MonkeyPatch) -> None:
    """The W3 Tester's M3: `MAKEFLAGS=UNAME_S=Linux` in the environment still removed the sandbox and
    its flag from `make test`. The run `make test` marks (MODEL_RANKING_REQUIRE_ARTIFACT=1, set by the
    recipe itself) must be offline on a Mac, whatever names the system."""
    from tests import conftest, skips

    monkeypatch.delenv("MODEL_RANKING_REQUIRE_OFFLINE", raising=False)
    monkeypatch.setenv("MODEL_RANKING_REQUIRE_ARTIFACT", "1")
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(skips, "offline", lambda: False)
    with pytest.raises(pytest.exit.Exception, match="offline"):
        conftest.pytest_sessionstart(None)  # type: ignore[arg-type]


def _swift_runs(target: str, uname: str) -> list[str]:
    """Each `swift test` command a Swift leg runs, as `make -n` prints its recipe on `uname`."""
    printed = subprocess.run(["make", "-n", target, f"UNAME_S={uname}"], cwd=ROOT, capture_output=True, text=True,
                             check=False, timeout=120).stdout.splitlines()
    commands = "\n".join(line for line in printed if not line.lstrip().startswith("#"))
    return re.findall(r"[^`;(\n]*\bswift test\b[^`;)\n]*", commands)


@pytest.mark.parametrize("leg", ["swift-test", "swift-test-parallel"])
def test_both_swift_legs_run_inside_the_offline_profile_on_macos(leg: str) -> None:
    """#179: since #149 the Swift suite starts child processes, which its tripwire cannot see. On
    macOS every `swift test` a leg runs is inside the offline profile, with SwiftPM's own sandbox off
    (it cannot nest); `OfflineGuardTests` shows a child refused. Linux has no `sandbox-exec`."""
    darwin = _swift_runs(leg, "Darwin")
    assert darwin, f"`make -n {leg}` printed no swift test"
    for run in darwin:
        assert "sandbox-exec -f ../scripts/offline.sb" in run and "--disable-sandbox" in run, run
    assert not any("sandbox-exec" in run for run in _swift_runs(leg, "Linux"))
