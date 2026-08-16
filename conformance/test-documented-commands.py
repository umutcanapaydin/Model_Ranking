#!/usr/bin/env python3
"""Every `make <target>` a shipped document tells a reader to run must exist.

WHY. The v5 control screen removed `check-templates`, `cold-start` and `journey` from the Makefile and
left them standing as **blocking closure checkboxes** in `docs/closure-checklist.md`, as ACTIVE house
rules in `.agents/rules/practices.md`, and as advice in `START_HERE.md`. Every board was green. A
customer following the closure checklist would type `make journey URL=…` and get
`No rule to make target`.

That is the packet's own opening sentence -- *a control that is present, documented, and unable to act*
-- produced by the repair round that was removing dead controls. Found by the Software seat, not by any
instrument. V4C-80 in one line: **anything a reader is told to type is an interface.**

Exit 0 clean, 1 findings, 2 cannot run.
"""
import re, sys, pathlib

SKIP_DIRS = {"__pycache__", ".venv", "node_modules", "archive"}
# Historical records describe what PAST versions did; they are not instructions.
SKIP_FILES = re.compile(r"HANDOVER-v[\d.]+-material\.md$|watchlist\.md$|CHANGELOG")
# Backticked or fenced ONLY. The first version matched bare prose and reported `make it`, `make the`
# and `make every` from sentences like "make it work" -- 12 false positives on its first run. A check
# that cries wolf gets switched off, and this one is guarding a defect that already shipped once.
CMD = re.compile(r"`make\s+([a-z][a-z0-9_-]*)")
FENCE = re.compile(r"^\s*```")


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    mk = root / "Makefile"
    if not mk.is_file():
        print("test-documented-commands CANNOT RUN: no Makefile"); return 2
    targets = set(re.findall(r"^([A-Za-z0-9_.-]+):", mk.read_text(encoding="utf-8"), re.M))

    bad, checked = [], 0
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if any(d in rel.parts for d in SKIP_DIRS) or SKIP_FILES.search(p.name):
            continue
        in_fence = False
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            # An illustrative example from someone else's project is not an instruction to the reader.
            if "illustrative" in line or "not a GP target" in line:
                continue
            if line.lstrip().startswith("<!--") or "~~" in line:
                continue                       # struck through or commented = already retired
            if in_fence and not line.lstrip().startswith("make "):
                continue
            found = CMD.findall(line) or ([line.split()[1]] if in_fence and line.lstrip().startswith("make ") and len(line.split()) > 1 else [])
            for t in found:
                checked += 1
                if t not in targets:
                    bad.append(f"{rel}:{i} tells the reader to run `make {t}`, which does not exist")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-documented-commands {'FAIL' if bad else 'PASS'}: "
          f"{checked} documented command(s), {len(bad)} dangling")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
