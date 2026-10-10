"""R1 (the M21-W4 review): a Swift leg that hangs fails with its own message; it never stalls the gate.

`scripts/watchdog.py SECONDS COMMAND...` runs the command in a process group of its own and, past its
limit, kills the group with SIGKILL (never a crash dialog: no abort, no core) and exits 124. Both Swift
legs run each `swift test` under it (`make -n` shows it).
"""

from __future__ import annotations

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
