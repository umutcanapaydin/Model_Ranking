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
import socket
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: A child's attempt to name a peer off this machine. TEST-NET-1, and UDP, so no packet in any case.
UDP_PROBE = (
    "import socket\n"
    "s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
    "try:\n"
    "    s.connect(('192.0.2.1', 9))\n"
    "    print('reached')\n"
    "except PermissionError:\n"
    "    print('refused')\n"
)


def _make_test(uname: str) -> str:
    return subprocess.run(["make", "-n", "test", f"UNAME_S={uname}"], cwd=ROOT, capture_output=True, text=True,
                          check=False, timeout=120).stdout


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


def test_a_child_process_the_suite_starts_cannot_name_an_outside_peer() -> None:
    """#122: a child of the test run is refused by the operating system, not by a Python guard it
    may not carry."""
    child = subprocess.run([sys.executable, "-c", UDP_PROBE], capture_output=True, text=True, timeout=30,
                           check=False, env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
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
