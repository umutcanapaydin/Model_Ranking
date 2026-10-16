#!/usr/bin/env python3
"""AGENTS.md's optional §2a holds nothing bootstrap-check's [C1] reads as an unfilled placeholder.

WHY (v7.1.1; model_ranking deleted §2a to get green). §2a ("two agents on one repository") sits in the
PROJECT section, above the UNIVERSAL marker, and `scripts/bootstrap-check.sh` [C1] fails on any
placeholder there, with no allowlist. v7.1 wrote `<tool>`, `<branch>`, `<skill>` and `<title>` into it as
notation, so every project that kept the section -- the Codex projects it was written for -- failed
Stage 0. The section now writes examples; this keeps it so.

DERIVED, not enumerated: the pattern is the script's own `PH='...'` line, read from it here; a script
whose pattern cannot be read is a failure, never a vacuous pass. The section is `## 2a.` to the next
heading or the UNIVERSAL marker. In the package (`.gp-distribution`) a missing §2a is a failure; in an
installation the section is optional and a project may have deleted it.

Exit: 0 clean - 1 a placeholder in §2a, no readable pattern, or no §2a in the package.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "bootstrap-check.sh"
AGENTS = ROOT / "AGENTS.md"


def placeholder_re() -> re.Pattern | None:
    if not SCRIPT.is_file():
        return None
    m = re.search(r"^PH='([^'\n]+)'", SCRIPT.read_text(encoding="utf-8", errors="replace"), re.M)
    if not m:
        return None
    try:
        return re.compile(m.group(1))
    except re.error:
        return None


def section_2a(text: str) -> list[tuple[int, str]] | None:
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^##\s+2a\.", ln)), None)
    if start is None:
        return None
    out = [(start + 1, lines[start])]
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## ") or "UNIVERSAL" in lines[i]:
            break
        out.append((i + 1, lines[i]))
    return out


def main() -> int:
    ph = placeholder_re()
    if ph is None:
        print(f"test-agents-2a FAIL: no readable `PH='...'` pattern in {SCRIPT.relative_to(ROOT)} -- "
              "the pattern [C1] grades with cannot be derived (fail closed)")
        return 1
    if not AGENTS.is_file():
        print("test-agents-2a FAIL: no AGENTS.md")
        return 1
    sec = section_2a(AGENTS.read_text(encoding="utf-8", errors="replace"))
    if sec is None:
        if (ROOT / ".gp-distribution").is_file():
            print("test-agents-2a FAIL: the package's AGENTS.md has no `## 2a.` section -- nothing is "
                  "graded (an empty derived set is a failure)")
            return 1
        print("test-agents-2a PASS: AGENTS.md carries no §2a here -- optional, and this project deleted it")
        return 0
    hits = [(n, m.group(0)) for n, ln in sec for m in ph.finditer(ln)]
    for n, h in hits:
        print(f"  FAIL AGENTS.md:{n}: `{h}` in §2a -- bootstrap-check [C1] reads it as an unfilled field "
              "above the UNIVERSAL marker, so every project that keeps §2a fails Stage 0; write an example")
    print(f"test-agents-2a {'FAIL' if hits else 'PASS'}: {len(sec)} line(s) of AGENTS.md §2a against "
          f"bootstrap-check's own pattern `{ph.pattern}`, {len(hits)} placeholder(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
