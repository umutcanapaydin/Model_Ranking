#!/usr/bin/env python3
"""`make secrets`: gitleaks over the files git tracks -- what a push can carry -- with every match
redacted.

WHY NOT THE WHOLE TREE. The scan used to be `gitleaks detect --source . --no-git -v`: every file in
the working tree, untracked and ignored ones included, each match printed in full. A developer's
local notes holding a key failed the gate, and the key itself landed in the terminal, in the
agent's context and in the pre-push hook's output (field report, 2026-09-23). A file git does not
track cannot be pushed, so it is not this gate's to read; a file it does track is read as it stands
in the working tree, uncommitted edits included.

Fail direction: outside a git work tree, or when git cannot list the files, the whole tree is
scanned -- the old, wider behaviour. The fallback reads more, never less. Matches are always
redacted. Exit: gitleaks' own (0 clean · 1 leaks found) · 2 cannot run.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def tracked_files() -> list[str] | None:
    try:
        r = subprocess.run(["git", "ls-files", "-z", "--cached"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p for p in r.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


def gitleaks(where: str) -> int:
    # Run FROM the directory scanned, so reported paths -- and `.gitleaksignore` fingerprints, which
    # carry them -- read exactly as they do from the repository root.
    return subprocess.call(["gitleaks", "detect", "--source", ".", "--no-git", "--redact", "-v"], cwd=where)


def main() -> int:
    if shutil.which("gitleaks") is None:
        print("gitleaks not installed: cannot scan the tree for secrets. Install gitleaks (INSTALL.md)",
              file=sys.stderr)
        return 2
    files = tracked_files()
    if files is None:
        print("secrets: not a git work tree -- scanning every file here, redacted", flush=True)
        return gitleaks(".")
    with tempfile.TemporaryDirectory(prefix="secrets-") as tmp:
        n = 0
        for rel in files:
            src = Path(rel)
            if not src.is_file() or src.is_symlink():      # deleted in the tree, or a link out of it
                continue
            dst = Path(tmp) / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            n += 1
        print(f"secrets: scanning the {n} file(s) git tracks, as they stand in the working tree, redacted", flush=True)
        # Keep the project's own allowlist in force: it lives at the root and is tracked like any file.
        for cfg in (".gitleaks.toml", ".gitleaksignore"):
            if os.path.isfile(cfg) and not (Path(tmp) / cfg).exists():
                shutil.copyfile(cfg, Path(tmp) / cfg)
        return gitleaks(tmp)


if __name__ == "__main__":
    sys.exit(main())
