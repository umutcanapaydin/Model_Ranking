"""The M21 closure security seat's S2: the Bash guard's own time bound.

Below Claude Code 2.1.295 a hook that times out lets the call through, so the guard's own deadline is the
only bound there. It is a timer thread that writes the BLOCKED line and exits 2: it works where SIGALRM
does not (Windows' Git Bash, which INSTALL.md supports) and stops a long call into C as well.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD_DIR = ROOT / ".claude" / "hooks"


def _run(setup: str, command: str) -> subprocess.CompletedProcess[str]:
    program = (f"import sys; sys.path.insert(0, {str(GUARD_DIR)!r}); import bash_guard as g\n{setup}\n"
               "sys.exit(g.main())\n")
    return subprocess.run([sys.executable, "-c", program], input=json.dumps({"tool_input": {"command": command}}),
                          capture_output=True, text=True, timeout=60, check=False)


def test_a_deadline_near_zero_blocks_even_git_status() -> None:
    """Mutant G2 (the timer never started) survived every gate."""
    done = _run("g.DEADLINE_S = 1e-6", "git status")
    assert done.returncode == 2 and "BLOCKED" in done.stderr, done


def test_the_deadline_holds_where_there_is_no_sigalrm() -> None:
    """On Windows `signal.setitimer` does not exist; the guard then blocked every call, `git status` too."""
    setup = "import signal\nfor name in ('setitimer', 'SIGALRM', 'ITIMER_REAL', 'alarm'):\n    if hasattr(signal, name): delattr(signal, name)"
    assert _run(setup, "git status").returncode == 0
    assert _run(setup + "\ng.DEADLINE_S = 1e-6", "git status").returncode == 2
