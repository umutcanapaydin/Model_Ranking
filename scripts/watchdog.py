#!/usr/bin/env python3
"""R1 (the M21-W4 review): run a command under a time limit, so a hang fails instead of stalling a gate.

Usage: `watchdog.py SECONDS COMMAND [ARG...]`. The command runs in a process group of its own. Past its
limit the whole group is killed with SIGKILL, a line saying so goes to stderr, and the exit is 124;
otherwise the command's own exit comes back. SIGKILL, never an abort: a killed process leaves no crash
report and opens no dialog on the owner's Mac. Both Swift legs run each `swift test` under it (Makefile,
`SWIFT_TEST_LIMIT`).
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys


def _kill(child: subprocess.Popen[bytes]) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(child.pid, signal.SIGKILL)
    child.wait()


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: watchdog.py SECONDS COMMAND [ARG...]", file=sys.stderr)
        return 2
    limit = float(argv[1])
    child = subprocess.Popen(argv[2:], start_new_session=True)  # noqa: S603 -- the caller's own command
    try:
        return child.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        _kill(child)
        print(f"watchdog: error: `{' '.join(argv[2:])[:100]}` passed its {limit:g} s limit and was killed "
              "(SIGKILL) -- a hang fails here instead of stalling the gate", file=sys.stderr)
        return 124
    except KeyboardInterrupt:
        _kill(child)
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv))
