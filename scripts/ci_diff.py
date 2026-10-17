#!/usr/bin/env python3
"""`make ci-diff`: what DevFlow's workflows say that this repository's do not -- one command for the owner.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit E-19). An agent never edits
`.github/workflows/**`, so every workflow change waits for the owner -- and in all three field projects
`ci.yml` had drifted from the version installed, its fixes sitting as diffs in issues for days. This
prints the difference between the workflows of the DevFlow tag this tree installed (`.gp/installed`) and
the ones committed here, and the one command that applies it, for `docs/owner-actions.md`.

Advisory: exit 0 with the diff or with what is missing (no marker, the tag not fetched); exit 2 only when
git cannot run here.
"""
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")


def main() -> int:
    if shutil.which("git") is None:
        print("ci-diff CANNOT RUN: git is not installed")
        return 2
    marker = ROOT / ".gp" / "installed"
    m = re.search(r"^gp_version:\s*(\S+)", marker.read_text(encoding="utf-8")) if marker.is_file() else None
    if not m:
        print("ci-diff: no `.gp/installed` with a `gp_version:` -- `make install` writes it; nothing to compare")
        return 0
    tag = m.group(1)
    if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}").returncode != 0:
        print(f"ci-diff: the DevFlow tag `{tag}` is not in this clone -- `git fetch devflow --tags` "
              "(INSTALL.md), then run this again")
        return 0
    diff = git("diff", "HEAD", tag, "--", ".github/workflows")
    if not diff.stdout.strip():
        print(f"ci-diff: .github/workflows matches DevFlow `{tag}` -- nothing for the owner")
        return 0
    print(diff.stdout, end="")
    print(f"\nci-diff: the workflows differ from DevFlow `{tag}` (above). The owner reads it and applies "
          f"it with:\n  git diff HEAD {tag} -- .github/workflows | git apply -3\n"
          "A project's own workflow change shows here too: keep it by leaving that hunk out.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
