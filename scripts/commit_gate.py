#!/usr/bin/env python3
"""The owner's ruling of 2026-10-10 on `commit-after-check-fast` ("fix and narrow"): which gate a commit needs.

`.githooks/pre-commit` (installed by `make hooks`) runs this on the commit's staged paths and then runs the
`make` target it prints, refusing the commit when that target fails:
- `check-records` for a docs-only commit;
- `check-fast` for any other.

Docs-only, exactly: every staged path (added, changed or deleted) ends in `.md`, and none lies under a code
directory (CODE_DIRS). A commit with no staged path is docs-only. A file under `docs/` that is not Markdown,
such as the ledger `docs/control-events.csv` or a probe run's JSON, is not: the gates read it.

Usage: `commit_gate.py` reads the index (`git diff --cached --name-only -z`); `commit_gate.py PATH...` judges
the paths given. It prints the target. `make check-fast` reads the working tree, not the index, so a file
staged in part is gated as the tree holds it.
"""

from __future__ import annotations

import subprocess
import sys

#: Directories whose files are code, tests, gates or configuration, Markdown included.
CODE_DIRS = ("src/", "tests/", "ios/", "scripts/", "conformance/", ".claude/", ".githooks/", ".github/")


def docs_only(path: str) -> bool:
    return path.endswith(".md") and not path.startswith(CODE_DIRS)


def target(paths: list[str]) -> str:
    """`check-records` when every path is docs-only, else `check-fast`."""
    return "check-records" if all(docs_only(path) for path in paths) else "check-fast"


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        paths = argv[1:]
    else:
        staged = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"],  # noqa: S607
                                capture_output=True, text=True, check=True)
        paths = [p for p in staged.stdout.split("\0") if p]
    print(target(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
