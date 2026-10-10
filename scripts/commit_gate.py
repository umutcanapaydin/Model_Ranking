#!/usr/bin/env python3
"""The owner's ruling of 2026-10-10 on `commit-after-check-fast` ("fix and narrow"), as the M21 closure applies
it: which gate a commit needs.

`.githooks/commit-msg` (installed by `make hooks`) runs `HEAD`'s copy of this on the commit's staged paths and
subject, then runs the `make` target it prints, refusing the commit when that target fails:
- `check-docs` when every staged path is docs-only;
- `check-red` for a declared red test commit: the subject starts `test:`, says `red` (a word, any case), and
  at least one staged path is a test (TEST_DIRS);
- `check-fast` for any other commit.

Docs-only, exactly: every staged path (added, changed, deleted, or either side of a rename) ends in `.md`, and
none lies under a code directory (CODE_DIRS). A commit with no staged path is docs-only. A file under `docs/`
that is not Markdown, such as the ledger `docs/control-events.csv` or a probe run's JSON, is not: the gates
read it. `check-docs` still runs every leg that reads Markdown; it leaves out only the Swift tests and the
compiled gate, which read none (`tests/unit/test_commit_gate.py`).

`check-red` leaves out the legs that run tests (`test`, `swift-test`, `conformance`, `client-decls`); lint,
types, the records and the rest must pass. A red commit's own tests fail by design, and the Tester checks that
each fails only on its own tests.

Usage: `commit_gate.py --message-file FILE` reads the subject from the message git is about to record and the
staged paths from the index (`git diff --cached --name-only --no-renames -z`); `commit_gate.py --subject TEXT
PATH...` judges what it is given. It prints the target. The gates read the working tree, not the index, so a
file staged in part is gated as the tree holds it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

#: Directories whose files are code, tests, gates or configuration, Markdown included.
CODE_DIRS = ("src/", "tests/", "ios/", "scripts/", "conformance/", ".claude/", ".githooks/", ".github/")
#: Where a red commit's tests live.
TEST_DIRS = ("tests/", "ios/EngineTests/", "ios/UITests/", "conformance/")


def docs_only(path: str) -> bool:
    return path.endswith(".md") and not path.startswith(CODE_DIRS)


def declared_red(subject: str) -> bool:
    """A `test:` subject that says it is red."""
    return subject.startswith("test:") and re.search(r"\bred\b", subject, re.IGNORECASE) is not None


def target(paths: list[str], subject: str = "") -> str:
    if all(docs_only(path) for path in paths):
        return "check-docs"
    if declared_red(subject) and any(path.startswith(TEST_DIRS) for path in paths):
        return "check-red"
    return "check-fast"


def subject_of(message: str) -> str:
    """The first line of a commit message that is not a comment git strips."""
    return next((line.strip() for line in message.splitlines() if line.strip() and not line.startswith("#")), "")


def staged() -> list[str]:
    listed = subprocess.run(["git", "diff", "--cached", "--name-only", "--no-renames", "-z"],  # noqa: S607
                            capture_output=True, text=True, check=True)
    return [p for p in listed.stdout.split("\0") if p]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="commit_gate", description="the make target a commit needs")
    parser.add_argument("--message-file", type=Path, help="the commit message git is about to record")
    parser.add_argument("--subject", default="", help="the subject, when no message file is given")
    parser.add_argument("paths", nargs="*", help="the staged paths (default: the index)")
    args = parser.parse_args(argv)
    subject = subject_of(args.message_file.read_text(encoding="utf-8", errors="replace")) \
        if args.message_file else args.subject
    print(target(args.paths if args.paths else staged(), subject))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
