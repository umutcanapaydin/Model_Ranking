"""#588: a parametrize id that holds its input overflows PYTEST_CURRENT_TEST on Linux.

pytest exports the running test's node id in `PYTEST_CURRENT_TEST`, and a subprocess inherits it.
Linux `execve` refuses any single argument or environment string above `MAX_ARG_STRLEN`
(32 pages, 131,072 bytes), so a test whose id carries a 200,000-character input cannot start a
subprocess on CI, while the Mac (no per-string limit) passes it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_ARG_STRLEN = 131_072
# `PYTEST_CURRENT_TEST=<node id> (teardown)` plus its terminating NUL is the string execve measures.
OVERHEAD = len("PYTEST_CURRENT_TEST=") + len(" (teardown)") + 1


def test_588_no_node_id_in_the_release_delta_tester_overflows_a_linux_environment_string() -> None:
    """Fault: a parametrize case with no id, whose input becomes its node id."""
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
         "tests/unit/test_release_delta_1102_tester.py"],
        cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
    ids = [line for line in done.stdout.splitlines() if "::" in line]
    assert done.returncode == 0 and ids, (done.returncode, done.stderr[-500:])
    too_long = [nodeid[:120] for nodeid in ids if len(nodeid.encode()) + OVERHEAD > MAX_ARG_STRLEN]
    assert too_long == [], too_long
