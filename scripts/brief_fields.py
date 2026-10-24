#!/usr/bin/env python3
"""The owner's setup answers, read from `docs/project-brief.md` -- the one place they live.

`/setup-project` writes the brief; these fields are the ones a script acts on, so they are read
here and nowhere else:

  Working mode:                    light | heavy   (unset or unreadable: heavy -- more checks, not fewer)
  Deploy commands:                 none | a comma-separated list the deploy gate guards
  Paths that make a change HIGH:   none | comma-separated globs (a change touching one needs security)
  QA verification:                 off | on        (unset: off -- a bug closes when its fix merges)

    python3 scripts/brief_fields.py mode          # prints light or heavy
    python3 scripts/brief_fields.py get "<field>" # prints the raw answer, or nothing
Exit 0, always: an absent brief is an answer (the defaults), not an error.

**The policy fields are read at the protected base** (AGENTS.md section 5, base-pinned policy; #283):
`Working mode:`, `Paths that make a change HIGH:` and `Deploy commands:` decide the reviews a change owes and
what the deploy gate guards, so `review_need.py` and `deploy_gate.py` read them from the brief as a base
commit holds it (`root_at`), never from the change under evaluation. A base commit git cannot read is an
error (`RuntimeError`), not the defaults: a policy read from nowhere would answer for the change.
"""
from __future__ import annotations

import atexit
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BRIEF = Path("docs/project-brief.md")
_PLACEHOLDER = re.compile(r"^<[^>]*>$")
#: The fields that decide what a change owes (#283): read at the base, and a change to one is a policy edit.
POLICY_FIELDS = ("Working mode", "Paths that make a change HIGH", "Deploy commands")
#: The branches whose merge-base with HEAD is the protected base, in the order they are tried.
DEFAULT_BRANCHES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")


def field(name: str, root: Path | str = ".") -> str | None:
    """The answer on the first line naming `name:`, stripped of Markdown; None if absent or a placeholder."""
    p = Path(root) / BRIEF
    if not p.is_file():
        return None
    want = name.lower() + ":"
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        low = line.lower()
        at = low.find(want)
        if at < 0:
            continue
        rest = line[at + len(want):]
        # The answer is in code spans when there are any -- the template writes every field that
        # way, one span (`a, b`) or one per item (`a`, `b`); all of them, joined, since reading only
        # the first left a second deploy command unguarded. Else the text before a *(explanation)*,
        # which may run onto later lines. A code span is taken as written: a glob's `**` is kept.
        before = re.split(r"\s\*\(", rest, maxsplit=1)[0]
        spans = re.findall(r"`([^`]*)`", before)
        rest = ", ".join(s.strip() for s in spans) if spans else before.strip().strip("*_ ").strip()
        if not rest or _PLACEHOLDER.match(rest):
            return None
        return rest
    return None


def listing(name: str, root: Path | str = ".") -> list[str]:
    """A comma-separated answer as a list; `none` or absent is the empty list."""
    raw = field(name, root)
    if not raw or raw.strip().lower() in ("none", "no", "-", "—"):
        return []
    return [x.strip().strip("`").strip() for x in raw.split(",") if x.strip().strip("`").strip()]


def mode(root: Path | str = ".") -> str:
    raw = (field("Working mode", root) or "").lower()
    return "light" if raw.startswith("light") else "heavy"


def qa_on(root: Path | str = ".") -> bool:
    return (field("QA verification", root) or "").lower().startswith("on")


def _git(repo: Path | str, *args: str) -> subprocess.CompletedProcess[str]:
    """git's answer; no git, or one that hangs, is a failed answer (exit 127), never a crash: the deploy gate
    asks this on every Bash call the guard judges, and a crash there would refuse `ls`."""
    try:
        # #410 round 1's B1: a `refs/replace/` ref would answer for the base this reads; never honour one.
        return subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args], capture_output=True,  # noqa: S603, S607
                              encoding="utf-8", errors="replace", check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        return subprocess.CompletedProcess(["git", *args], 127, "", str(error))


def root_at(rev: str, repo: Path | str = ".") -> Path:
    """A throwaway root holding `docs/project-brief.md` as commit `rev` of the repository at `repo` held it,
    empty when that commit holds no brief (an absent brief is an answer: the defaults). RuntimeError when
    `rev` is not a commit git can read there, or its brief cannot be read (#283: fail closed)."""
    commit = _git(repo, "rev-parse", "--verify", "-q", f"{rev}^{{commit}}")
    if commit.returncode != 0 or not commit.stdout.strip():
        raise RuntimeError(f"the commit {rev!r} cannot be read, so the brief's policy fields there cannot be")
    sha = commit.stdout.strip()
    text = ""
    if _git(repo, "cat-file", "-e", f"{sha}:{BRIEF.as_posix()}").returncode == 0:
        shown = _git(repo, "show", f"{sha}:{BRIEF.as_posix()}")
        if shown.returncode != 0:
            raise RuntimeError(f"{BRIEF.as_posix()} at {sha[:7]} cannot be read")
        text = shown.stdout
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, True)
    (tmp / "docs").mkdir()
    (tmp / BRIEF).write_text(text, encoding="utf-8")
    return tmp


def protected_base(repo: Path | str = ".", head: str = "HEAD") -> str | None:
    """The merge-base of `head` with the first of DEFAULT_BRANCHES git knows in `repo`, or None."""
    for ref in DEFAULT_BRANCHES:
        found = _git(repo, "merge-base", ref, head)
        if found.returncode == 0 and found.stdout.strip():
            return found.stdout.strip()
    return None


def policy(root: Path | str = ".") -> dict[str, str | None]:
    """Each policy field's raw answer in the brief under `root` (None: absent or a placeholder)."""
    return {name: field(name, root) for name in POLICY_FIELDS}


def main(argv: list[str]) -> int:
    if argv[:1] == ["mode"]:
        print(mode())
    elif argv[:1] == ["get"] and len(argv) == 2:
        print(field(argv[1]) or "")
    else:
        print("usage: brief_fields.py mode | get \"<field>\"")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
