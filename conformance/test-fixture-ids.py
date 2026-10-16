#!/usr/bin/env python3
"""No conformance fixture carries a milestone number a project can reach, or a name a project's own records take.

WHY (DevFlow #16, D5; measured 2026-10-12). The fixtures shipped as `m1-wave-2-close`,
`m1-wave-3-close`, `m1-wave-2-review`, `closure-report-m7` and `closure-report-m8`: the names a
project's own first milestone and seventh close take. A search for one project's M1 W2 review found
the fixture's PASS verdict; `scripts/wave_check.py` derives a plan path from the file's name, so an
`m1` fixture pointed at that project's real `docs/plans/m1-plan.md`; another project's `wave_check`
fork had to exclude `conformance/` to keep its own records apart from the fixtures. The checkers'
filename rules (`m{N}-wave-{W}-close.md`, `closure-report-m{N}.md`) forbid a `fixture-` prefix, so
the fixtures take milestone numbers no project reaches -- m901, m907, m908 -- and this keeps it so.

Two rules, both DERIVED from the tree rather than listed here:
  1. every fixture under `conformance/` whose stem or frontmatter `id:` carries a milestone number
     (`m<N>-...`, `closure-report-m<N>`) has N >= FLOOR. Below it, a project could reach the id;
  2. no fixture shares a name (stem or `id:`) with a record under `docs/` of the tree this runs in
     -- in the package that is the shipped seed records, in an installation the project's own.
The fixture side is every `.md` under `conformance/` but the directory's README; files are seen
through `git ls-files` where the tree is a repository and by walking it where it is not (a scratch
copy), and the output says which. An empty fixture side is a failure, never a vacuous pass.

Exit: 0 clean - 1 a fixture a project could reach, a shared name, or an empty fixture side.
"""
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FLOOR = 900
ID_RE = re.compile(r"\A---\s*\n(?:.*\n)*?id:\s*(\S+)", re.M)
MILESTONE_RE = re.compile(r"(?:^|-)m(\d+)(?:-|$)")
SKIP = {"conformance/README.md"}


def tracked(prefix: str) -> tuple[list[str], str]:
    """Relative `.md` paths under `prefix`, and how they were seen (git, or a walk)."""
    try:
        out = subprocess.run(["git", "ls-files", "--", f"{prefix}/"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.split()
        if out:
            return [p for p in out if p.endswith(".md")], "git"
    except (OSError, subprocess.CalledProcessError):
        pass
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT / prefix):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".venv", "__pycache__", "node_modules")]
        for f in filenames:
            if f.endswith(".md"):
                found.append(str((pathlib.Path(dirpath) / f).relative_to(ROOT)).replace(os.sep, "/"))
    return sorted(found), "walk"


def names(prefix: str) -> tuple[dict[str, str], str]:
    """name -> the file it came from, for every .md under `prefix`: the stem and the frontmatter id."""
    paths, how = tracked(prefix)
    found: dict[str, str] = {}
    for rel in paths:
        if rel in SKIP:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        found.setdefault(path.stem, rel)
        m = ID_RE.match(path.read_text(encoding="utf-8", errors="replace"))
        if m:
            found.setdefault(m.group(1), rel)
    return found, how


def main() -> int:
    fixtures, how = names("conformance")
    records, _ = names("docs")
    if not fixtures:
        print(f"test-fixture-ids FAIL: derived 0 fixture name(s) under conformance/ (seen via {how}); "
              "an empty side proves nothing")
        return 1
    bad: list[str] = []
    for name, rel in sorted(fixtures.items()):
        m = MILESTONE_RE.search(name)
        if m and int(m.group(1)) < FLOOR:
            bad.append(f"{rel}: `{name}` carries milestone {int(m.group(1))}, which a project could "
                       f"reach -- fixtures take numbers from m{FLOOR} up")
    for name in sorted(set(fixtures) & set(records)):
        bad.append(f"{fixtures[name]}: `{name}` is also the name of the record {records[name]}")
    if bad:
        print("test-fixture-ids FAIL: fixtures named like a project's records:")
        for b in bad:
            print(f"  {b}")
        return 1
    print(f"test-fixture-ids PASS: {len(fixtures)} fixture name(s) under conformance/, all milestone "
          f"numbers >= {FLOOR}, none shared with the {len(records)} record name(s) under docs/ "
          f"(files seen via {how})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
