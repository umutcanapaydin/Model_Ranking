#!/usr/bin/env python3
"""No tracked file carries a merge-conflict marker (#341).

WHY. Run bug-night's merge of #333 left conflict markers in `docs/decisions.md`; the commit gate passed and the
records check read both sides as whole ADRs. A marker is a line that starts a conflict side (`<<<<<<< `,
`>>>>>>> `) or is exactly the separator (seven `=`). In Markdown, a fenced code block may show one as an
example; a heading's `===` underline is shorter or longer and is no marker. Binary files are skipped.

Exit: 0 none - 1 a marker, each printed as `path:line` - 2 git cannot list the tracked files (fail closed).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKER = re.compile(r"^(?:<{7} |>{7} |={7}$)")
FENCE = re.compile(r"^\s*(```|~~~)")


def findings(root: pathlib.Path) -> list[tuple[str, int]]:
    """Each `(path, line)` of a marker in a tracked text file under `root`."""
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    out: list[tuple[str, int]] = []
    for rel in sorted(n for n in listed.stdout.decode("utf-8", errors="replace").split("\0") if n):
        path = root / rel
        if not path.is_file() or path.is_symlink():
            continue
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            continue
        fenced = False
        markdown = path.suffix.lower() in {".md", ".markdown"}
        for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            if markdown and FENCE.match(line):
                fenced = not fenced
                continue
            if not fenced and MARKER.match(line):
                out.append((rel, number))
    return out


def main() -> int:
    try:
        found = findings(ROOT)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"conflict-markers CANNOT RUN: git cannot list the tracked files ({exc})")
        return 2
    for rel, number in found:
        print(f"{rel}:{number}: a merge-conflict marker")
    print(f"conflict-markers {'FAIL' if found else 'PASS'}: {len(found)} marker line(s) in tracked files")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
