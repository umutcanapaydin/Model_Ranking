"""R1 (the M21-W4 review): a Swift leg that hangs fails with its own message; it never stalls the gate.

`scripts/watchdog.py SECONDS COMMAND...` runs the command in a process group of its own and, past its
limit, kills the group with SIGKILL (never a crash dialog: no abort, no core) and exits 124. Both Swift
legs run each `swift test` under it (`make -n` shows it).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.unit.test_offline_run import _swift_runs

ROOT = Path(__file__).resolve().parents[2]
WATCHDOG = ROOT / "scripts" / "watchdog.py"


def test_a_command_past_its_limit_is_killed_with_its_own_message() -> None:
    started = time.monotonic()
    done = subprocess.run([sys.executable, str(WATCHDOG), "1", sys.executable, "-c", "import time; time.sleep(30)"],
                          capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 124, done
    assert "watchdog" in done.stderr and "1 s" in done.stderr, done.stderr
    assert time.monotonic() - started < 15


def test_a_command_inside_its_limit_keeps_its_own_exit_and_output() -> None:
    done = subprocess.run([sys.executable, str(WATCHDOG), "30", sys.executable, "-c", "print('ok'); raise SystemExit(3)"],
                          capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 3 and done.stdout.strip() == "ok", done


@pytest.mark.parametrize("leg", ["swift-test", "swift-test-parallel"])
def test_every_swift_run_in_both_legs_is_under_the_watchdog(leg: str) -> None:
    runs = _swift_runs(leg, "Darwin")
    assert runs and all("watchdog.py" in run for run in runs), runs


#: A child that starts a grandchild in a session of its own, as SwiftPM starts `xctest`, and writes its pid.
GRANDCHILD = (
    "import subprocess, sys, time\n"
    "g = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)\n"
    "open(sys.argv[1], 'w').write(str(g.pid))\n"
    "time.sleep(60)\n"
)


def _gone(pid: int, within: float = 5.0) -> bool:
    deadline = time.monotonic() + within
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def _grandchild(pidfile: Path) -> int:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not (pidfile.exists() and pidfile.read_text()):
        time.sleep(0.05)
    return int(pidfile.read_text())


def test_a_timeout_kills_a_grandchild_in_a_session_of_its_own(tmp_path: Path) -> None:
    """Round 2's M7: SwiftPM runs `xctest` in a group of its own, and the hung test outlived the kill."""
    pidfile = tmp_path / "grandchild.pid"
    done = subprocess.run([sys.executable, str(WATCHDOG), "2", sys.executable, "-c", GRANDCHILD, str(pidfile)],
                          capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 124, done
    assert _gone(_grandchild(pidfile)), "the grandchild outlived the watchdog"


def test_ctrl_c_reaches_the_child_and_its_grandchild(tmp_path: Path) -> None:
    """Round 2's M7: the terminal's SIGINT reached only the watchdog, which left the test running."""
    pidfile = tmp_path / "grandchild.pid"
    watchdog = subprocess.Popen([sys.executable, str(WATCHDOG), "60", sys.executable, "-c", GRANDCHILD, str(pidfile)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    grandchild = _grandchild(pidfile)
    watchdog.send_signal(signal.SIGINT)
    assert watchdog.wait(timeout=30) != 0
    assert _gone(grandchild), "the grandchild outlived Ctrl-C"
