#!/usr/bin/env python3
"""Every `make <target>` a shipped document tells a reader to run must exist.

WHY. Targets were once removed from the Makefile and left standing as **blocking closure
checkboxes** in `docs/closure-checklist.md`, as active house rules in `.agents/rules/practices.md`,
and as advice in the orientation file. Every board was green. A reader following the closure
checklist would type `make journey URL=…` and get `No rule to make target` -- a control that is
present, documented, and unable to act. The principle: **anything a reader is told to type is an
interface.**

Exit 0 clean, 1 findings, 2 cannot run.
"""
import re, sys, pathlib

SKIP_DIRS = {"__pycache__", ".venv", "node_modules"}
# The watch list names REMOVED controls and the condition for their return; it is not an instruction.
SKIP_FILES = re.compile(r"watchlist\.md$")

# A record describes what was run when it was written: a field project's closure reports cited a
# target removed later, and this check failed the RECORDS. Removing a target must not retroactively
# falsify history. Records are skipped by artifact class (lib_record); live instruction surfaces are
# still fully checked.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import doc_text, documents, is_record as _is_record  # noqa: E402
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
    for p in documents(root):
        rel = p.relative_to(root)
        if any(d in rel.parts for d in SKIP_DIRS) or SKIP_FILES.search(p.name):
            continue
        if _is_record(p):
            continue                    # a record is history, not an instruction
        in_fence = False
        for i, line in enumerate(doc_text(p).splitlines(), 1):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            # An illustrative example from someone else's project is not an instruction to the reader.
            if "illustrative" in line:
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
