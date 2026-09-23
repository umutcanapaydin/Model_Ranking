#!/usr/bin/env python3
"""AGENTS.md stays within the hard cap it states about itself.

WHY. AGENTS.md says "≤150 hard cap" in its own last lines, and shipped at 176: the rule every agent
reads first was the one nothing checked. A project adding its §1-2 context landed near 185. The cap
is read FROM the file (the sentence that states it), not typed here — one fact, one place.

Exit: 0 within the cap · 1 over it, or the file states no cap (a cap nobody can find is not a cap)
· 2 cannot run (no AGENTS.md).
"""
import pathlib
import re
import sys

PKG = pathlib.Path(__file__).resolve().parent.parent
CAP_RE = re.compile(r"≤\s*(\d+)\s*hard cap")


def main() -> int:
    agents = PKG / "AGENTS.md"
    if not agents.is_file():
        print("test-agents-cap CANNOT RUN: no AGENTS.md")
        return 2
    text = agents.read_text(encoding="utf-8", errors="replace")
    m = CAP_RE.search(text)
    if not m:
        print("test-agents-cap FAIL: AGENTS.md states no hard cap (a less-than-or-equal sign, the "
              "number, then `hard cap`) -- the diet rule has lost the number it is graded against")
        return 1
    cap, lines = int(m.group(1)), len(text.splitlines())
    if lines > cap:
        print(f"test-agents-cap FAIL: AGENTS.md is {lines} lines, over its own {cap}-line hard cap. "
              "Move detail to `.agents/rules/`; the file every agent reads first is the one that must "
              "stay short")
        return 1
    print(f"test-agents-cap PASS: AGENTS.md {lines} of {cap} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
