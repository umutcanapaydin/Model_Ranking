#!/usr/bin/env python3
"""Create the issue-label vocabulary on this repository's GitHub remote -- only the missing ones.

WHY. Every lifecycle skill keys on labels (`severity:*`, `dev:done`, `qa:*`, `agent:*`), and
`.agents/rules/issues.md` says a label nobody created is a label no skill will ever match. Nothing
created them: a fresh repository has GitHub's nine defaults, so `/post-merge` swapping to `dev:done`
had no label to apply.

DERIVED, not typed: the set is read from the vocabulary table in `.agents/rules/issues.md`, so
adding a label there is the whole change. Existing labels are left exactly as they are -- no
recolouring, no renaming, no `--force`.

Without `gh` it cannot create anything, so it prints the vocabulary as a table to create by hand
on the repository's Labels page, and exits 2: the labels are still missing, and saying so is the
point.

Usage: python3 scripts/create_labels.py [--dry-run]
Exit: 0 done (or nothing missing) · 1 a `gh` call failed · 2 cannot run (no gh, no vocabulary).
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / ".agents" / "rules" / "issues.md"


def vocabulary() -> list[tuple[str, str]]:
    """(group, label) for every backticked label in the rows of the `| Group | Labels |` table."""
    rows: list[tuple[str, str]] = []
    in_table = False
    for line in RULES.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*Group\s*\|\s*Labels\s*\|", line):
            in_table = True
            continue
        if in_table and not line.startswith("|"):
            break
        if in_table:
            cells = line.split("|")
            if len(cells) > 2:
                group = cells[1].replace("*", "").strip()
                rows += [(group, name) for name in re.findall(r"`([^`]+)`", cells[2])]
    return rows


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    if not RULES.is_file():
        print(f"create_labels CANNOT RUN: {RULES.relative_to(ROOT)} is missing")
        return 2
    table = vocabulary()
    want = [name for _, name in table]
    if not want:
        print("create_labels CANNOT RUN: no label table found in .agents/rules/issues.md. An empty "
              "vocabulary is not a clean result.")
        return 2
    if not shutil.which("gh"):
        print("create_labels CANNOT RUN: gh not installed: cannot create the labels on GitHub.")
        print(f"Create the ones the repository's Labels page (Issues > Labels > New label) does not "
              f"already show -- {len(table)} in the vocabulary of {RULES.relative_to(ROOT)}:")
        width = max(len(group) for group, _ in table)
        for group, name in table:
            print(f"  {group:<{width}}  {name}")
        print("Once gh is installed (INSTALL.md), `make labels` creates whatever is still missing.")
        return 2
    r = subprocess.run(["gh", "label", "list", "--limit", "500", "--json", "name"],  # noqa: S607 -- `gh` from PATH, fixed argv
                       cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"create_labels CANNOT RUN: `gh label list` failed -- {r.stderr.strip()[:200]}")
        return 2
    have = {x["name"] for x in json.loads(r.stdout or "[]")}
    missing = [n for n in want if n not in have]
    print(f"create_labels: {len(want)} in the vocabulary, {len(want) - len(missing)} already exist, "
          f"{len(missing)} missing")
    failed = 0
    for name in missing:
        if dry:
            print(f"  would create `{name}`")
            continue
        c = subprocess.run(["gh", "label", "create", name], cwd=ROOT, capture_output=True,  # noqa: S603, S607
                           encoding="utf-8", errors="replace")
        print(f"  {'created' if c.returncode == 0 else 'FAILED '} `{name}`"
              + ("" if c.returncode == 0 else f" -- {c.stderr.strip()[:160]}"))
        failed += c.returncode != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
