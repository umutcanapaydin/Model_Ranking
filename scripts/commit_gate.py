#!/usr/bin/env python3
"""The owner's ruling of 2026-10-10 on `commit-after-check-fast` ("fix and narrow"), as the M21 closure applies
it: which gate a commit needs.

`.githooks/commit-msg` (installed by `make hooks`) runs `HEAD`'s copy of this on the commit's staged paths and
subject, then runs the `make` target it prints, refusing the commit when that target fails:
- `check-fast` for a merge, a commit with nothing staged (a reworded amend), and any commit below's two
  rules leave;
- `check-docs` when every staged path is docs-only;
- `check-red` for a declared red test commit: the subject starts `test:` and says `red` as a word of its own
  (any case; not `red-to-green` or `red-ish`), and at least one staged path is a test (TEST_DIRS). It may
  carry code beside the test.

Docs-only, exactly: every staged path (added, changed, deleted, or either side of a rename) ends in `.md`, and
none lies under a code directory (CODE_DIRS). A file under `docs/` that is not Markdown, such as the ledger
`docs/control-events.csv` or a probe run's JSON, is not: the gates read it. `check-docs` still runs every leg
that reads Markdown; it leaves out only the Swift tests and the compiled gate, which read none
(`tests/unit/test_commit_gate.py`).

`check-red` leaves out the legs that run tests (`test`, `swift-test`, `conformance`, `client-decls`), and
builds instead: `swift-build-tests` compiles the Swift package and its tests, and `pytest-collect` imports
every Python test, so a red commit has no build or collection error. Lint, types and the records must pass.
Who checks that a red commit fails as it should: `docs/refusals.md` R-1.

The subject is the one git records (`%s`, the fixes review's round 2, M1): the message after the cleanup git
applies, then its first paragraph, joined. Git sets `GIT_EDITOR=:` for the hook when no editor ran (`-m`,
`-F`); then the default cleanup keeps `#` lines, so `git commit -m "#241 x" -m "test: x, red"` records the
subject `#241 x`. When the editor ran, it drops the lines that start with the comment string
(`core.commentChar`, `#` by default; `auto` is read as `#`). `commit.cleanup`, and `commit.verbose` or
`scissors` (which cut the message at the scissors line), are read from git's config. A `--cleanup` or `-v`
given on the command line is not visible to a hook.

Usage: `commit_gate.py --message-file FILE` reads the subject from the message git is about to record and the
staged paths from the index (`git diff --cached --name-only --no-renames -z`); `commit_gate.py --subject TEXT
PATH...` judges what it is given. It prints the target. The gates read the working tree, not the index, so a
file staged in part is gated as the tree holds it.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

#: Directories whose files are code, tests, gates or configuration, Markdown included.
CODE_DIRS = ("src/", "tests/", "ios/", "scripts/", "conformance/", ".claude/", ".githooks/", ".github/")
#: Where a red commit's tests live.
TEST_DIRS = ("tests/", "ios/EngineTests/", "ios/UITests/", "conformance/")
#: `red` as a word of its own: not inside `red-to-green`, `red-ish` or `reduce`.
RED = re.compile(r"(?<![\w-])red(?![\w-])", re.IGNORECASE)
#: The line `git commit -v` and `--cleanup=scissors` cut a message at, after the comment string and a space.
SCISSORS = "------------------------ >8 ------------------------"
#: What git counts as whitespace at a line's end.
SPACE = " \t\n\r"


def docs_only(path: str) -> bool:
    return path.endswith(".md") and not path.startswith(CODE_DIRS)


def declared_red(subject: str) -> bool:
    """A `test:` subject that says it is red."""
    return subject.startswith("test:") and RED.search(subject) is not None


def target(paths: list[str], subject: str = "", merge: bool = False) -> str:
    if merge or not paths:
        return "check-fast"
    if all(docs_only(path) for path in paths):
        return "check-docs"
    if declared_red(subject) and any(path.startswith(TEST_DIRS) for path in paths):
        return "check-red"
    return "check-fast"


def subject_of(message: str, strip: bool = False, comment: str = "#", cut: bool = False) -> str:
    """The subject git records for `message`: cut at the scissors line when `cut`, the lines that start with
    `comment` dropped when `strip`, then the first paragraph, each line without its trailing whitespace, joined
    by a space (git's `%s`)."""
    lines = message.split("\n")
    if cut:
        lines = lines[:next((i for i, line in enumerate(lines) if line == f"{comment} {SCISSORS}"), len(lines))]
    if strip:
        lines = [line for line in lines if not line.startswith(comment)]
    words: list[str] = []
    for line in (line.rstrip(SPACE) for line in lines):
        if line:
            words.append(line)
        elif words:
            break
    return " ".join(words)


def _config(name: str) -> str:
    done = subprocess.run(["git", "config", "--get", name], capture_output=True, text=True,  # noqa: S603, S607
                          check=False)
    return done.stdout.strip() if done.returncode == 0 else ""


def cleanup() -> tuple[bool, str, bool]:
    """(strip, comment, cut): the cleanup git applies to this commit's message, as far as a hook can see it."""
    editor = os.environ.get("GIT_EDITOR") != ":"   # git sets `:` for the hook when no editor ran
    mode = _config("commit.cleanup") or "default"
    comment = _config("core.commentString") or _config("core.commentChar") or "#"
    verbose = _config("commit.verbose").lower() not in ("", "false", "no", "off", "0")
    return (mode == "strip" or (mode == "default" and editor), "#" if comment == "auto" else comment,
            verbose or (mode == "scissors" and editor))


def merging() -> bool:
    """Whether the commit is a merge (`git merge`, or a commit that concludes one)."""
    return subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],  # noqa: S607
                          capture_output=True, check=False).returncode == 0


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
    subject = subject_of(args.message_file.read_text(encoding="utf-8", errors="replace"), *cleanup()) \
        if args.message_file else args.subject
    print(target(args.paths, subject) if args.paths else target(staged(), subject, merging()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
