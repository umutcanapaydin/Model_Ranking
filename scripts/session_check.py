#!/usr/bin/env python3
"""`make session-check`: is this Claude Code session actually governed by this repository?

Claude Code loads a project's `.claude/settings.json` -- the guards, the post-edit check -- only
from the directory it was STARTED in. Started one directory up, every guard is silently off while
the skills, the rules and the Makefile all still look present. A field project ran like that for
days: 89 `rm -rf` and two pushes to the default branch went through a guard that never loaded, and
no pre-push hook had been installed either (2026-09-26). A second project ran its whole 313-hour
session from the home directory: no hook fired, no agent profile and no skill was registered
("Unknown skill"), and one force push went through (measured 2026-10-12).

How it knows. The project's SessionStart hook drops `<git common dir>/devflow-sessions/<session id>`
when -- and only when -- that settings file loaded. Claude Code gives every shell the same id as
`CLAUDE_CODE_SESSION_ID`, so a missing marker means the settings did not load for this session.
Measured with a nested session: started at the root, the marker equals the id; started one level
up, there is no marker.

Two sessions have no marker for a reason the check cannot tell apart, so the failure line says both:
  * the session was started outside the repository root -- then none of this repository's agent
    profiles, skills or hooks is registered either, not only the guards;
  * the session is the one that INSTALLED or UPGRADED DevFlow -- the SessionStart hook did not
    exist when the session began, so no marker could be written. Two field projects recorded skip
    rows for this and one hit the three-skips lock; the answer is to finish the merge and start a
    new session, not to record a skip.

What it checks, and says it checked: the marker for this session id, and that `core.hooksPath`
resolves to this clone's `.githooks`. It does NOT read what `.githooks/pre-push` runs, and the PASS
line no longer claims it does (DevFlow #16, K1: "pre-push runs make gate" was read as proof).

  * not inside Claude Code (CI, a terminal, the pre-push hook of a human push) -> nothing to check
  * inside Claude Code and git cannot name the work tree -> FAIL (closed): a check that cannot read
    its subject grades nothing; until v7.1 this case passed
  * inside Claude Code with no marker for this session -> FAIL, with both reasons above
  * inside Claude Code with no pre-push hook in this clone -> FAIL: run `make hooks`

Exit: 0 governed, or not a Claude Code session · 1 not governed, or cannot be read.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def resolved(path: str, base: str) -> str | None:
    p = Path(path)
    if not p.is_absolute() and not (len(path) > 1 and path[1] == ":"):   # C:/... on Windows
        p = Path(base) / p
    return str(p.resolve()) if p.is_dir() else None


def main() -> int:
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # The CI issue agent runs Claude Code in a fresh checkout: no SessionStart marker and no
        # `make hooks` were ever possible there, and CI itself is the enforcement (v7.2).
        print("session-check: in GitHub Actions -- CI is the enforcement here, nothing to check")
        return 0
    if not sid:
        print("session-check: not inside a Claude Code session -- nothing to check")
        return 0
    top, common = git("rev-parse", "--show-toplevel"), git("rev-parse", "--git-common-dir")
    if not top or not common:
        # Fail CLOSED (DevFlow #16, S5). A git that is missing, or a directory that is not a work
        # tree, is exactly where no guard of this repository can be loaded; passing here certified
        # the one session the check exists to refuse.
        print(f"FAIL [session-check]: cannot read the git work tree from {os.getcwd()} (git "
              "missing, or not inside a repository), so nothing can show that this session loaded "
              "any repository's settings -- fail closed. Start Claude Code in the repository root")
        return 1
    common_dir = resolved(common, top) or common
    marker = Path(common_dir) / "devflow-sessions" / sid
    bad: list[str] = []
    if not marker.is_file():
        bad.append(f"no SessionStart marker `{marker}` for this session, so this Claude Code session "
                   f"did not load {top}/.claude/settings.json: the guards and the post-edit check are "
                   "OFF. Two causes, same cure. (1) The session was started outside the repository "
                   f"root -- then no agent profile (`.claude/agents/`), no skill (`.claude/skills/`) "
                   "and no hook of this repository is registered in it either. (2) This is the "
                   "session that installed or upgraded DevFlow -- the SessionStart hook did not "
                   "exist when it began, so no marker could be written. Either way: finish and merge "
                   "what is in hand, then START A NEW SESSION from the repository root. Do not record "
                   "a skip row in docs/control-events.csv for this; a new session is the fix")
    hp = git("config", "core.hooksPath") or ""
    want = resolved(".githooks", top)
    if not hp or resolved(hp, top) != want:
        bad.append(f"core.hooksPath is `{hp or 'unset'}`, not this clone's `.githooks`, so git runs "
                   "no pre-push hook from this repository before a push. Run `make hooks`")
    for b in bad:
        print(f"FAIL [session-check]: {b}")
    if bad:
        return 1
    print(f"session-check PASS: checked the SessionStart marker for this session (`{marker}`, "
          "present) and core.hooksPath (resolves to this clone's .githooks). Not checked: what "
          ".githooks/pre-push runs when git calls it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
