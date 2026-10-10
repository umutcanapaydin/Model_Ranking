#!/usr/bin/env python3
"""R1 (the M21-W4 review): run a command under a time limit, so a hang fails instead of stalling a gate.

Usage: `watchdog.py SECONDS COMMAND [ARG...]`. The command runs in a session of its own. Past its limit,
or on Ctrl-C or SIGTERM, the watchdog lists the command's descendants, sends SIGINT to each of their
process groups so a tool like SwiftPM can stop the test process it started in a group of its own, waits up
to GRACE_S seconds, then sends SIGKILL to every one of those groups and processes. A timeout exits 124 with
a line saying so; an interrupt exits 130; otherwise the command's own exit comes back. SIGINT and SIGKILL,
never an abort: a killed process leaves no crash report and opens no dialog on the owner's Mac. Both Swift
legs run each `swift test` under it (Makefile, `SWIFT_TEST_LIMIT`). Not seen: a descendant whose parent
had already exited when the listing (`pgrep -P`) was taken.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import time

#: How long the command's processes have to stop after SIGINT before SIGKILL.
GRACE_S = 3.0


def _tree(root: int) -> dict[int, int]:
    """`root` and its descendants, each with its process group: children from `pgrep -P` (which runs inside
    the offline profile, where the setuid `ps` may not), groups from `os.getpgid`."""
    found: dict[int, int] = {}
    stack = [root]
    while stack:
        pid = stack.pop()
        if pid in found:
            continue
        try:
            found[pid] = os.getpgid(pid)
        except (ProcessLookupError, PermissionError):
            continue
        listed = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True,  # noqa: S603, S607
                                check=False).stdout
        stack += [int(child) for child in listed.split() if child.isdigit()]
    return found


def _signal(tree: dict[int, int], sig: signal.Signals) -> None:
    own = os.getpgrp()
    for pgid in {g for g in tree.values() if g > 1 and g != own}:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(pgid, sig)
    if sig == signal.SIGKILL:
        for pid in tree:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(pid, sig)


def stop(child: subprocess.Popen[bytes]) -> None:
    """SIGINT to every group of the command's tree, a grace period, then SIGKILL to all of it."""
    tree = _tree(child.pid)
    _signal(tree, signal.SIGINT)
    deadline = time.monotonic() + GRACE_S
    while time.monotonic() < deadline and child.poll() is None:
        time.sleep(0.05)
    if child.poll() is None:
        tree.update(_tree(child.pid))
    _signal(tree, signal.SIGKILL)
    child.wait()


def _interrupted(signum: int, frame: object) -> None:
    raise KeyboardInterrupt


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: watchdog.py SECONDS COMMAND [ARG...]", file=sys.stderr)
        return 2
    limit = float(argv[1])
    signal.signal(signal.SIGTERM, _interrupted)
    signal.signal(signal.SIGINT, _interrupted)  # even where a shell started it with SIGINT ignored
    child = subprocess.Popen(argv[2:], start_new_session=True)  # noqa: S603 -- the caller's own command
    try:
        return child.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        stop(child)
        print(f"watchdog: error: `{' '.join(argv[2:])[:100]}` passed its {limit:g} s limit and was stopped "
              "(SIGINT, then SIGKILL, to its whole tree) -- a hang fails here instead of stalling the gate",
              file=sys.stderr)
        return 124
    except KeyboardInterrupt:
        stop(child)
        print("watchdog: interrupted; the command's whole tree was stopped", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv))
