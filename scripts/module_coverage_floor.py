#!/usr/bin/env python3
"""Per-module coverage floor — the half a global percentage cannot do (W-041).

**Why this exists.** A repository-wide figure of 88% concealed a module at 32%: `epoch_board.py`,
the single reader behind six of the nine served surfaces, reached a closing tree with zero tests
naming it. Every gate was green. A global floor would not have moved, because one small module
cannot shift a 3000-statement total. **The risk lives in new code, and new code is small.**

So this asks a different question, per file: *is any module carrying materially less proof than the
rest of the repository?* The floor is absolute rather than relative to the median, because a median
moves when the repository does and a project should not have its gate loosened by writing a large
untested module.

Exemptions are NAMED and carry a reason. An exemption whose file no longer exists is itself a
failure — an exemption that outlives its subject silently widens the next time the name is reused.

Usage:  coverage_floor.py [coverage.json]
Exit:   0 clean · 1 a module is below the floor, or an exemption is stale · 2 no coverage data
"""

from __future__ import annotations

import json
import pathlib
import sys

#: Absolute per-module floor, in percent of statements+branches.
FLOOR = 60.0

#: file path -> the reason it is exempt. Every entry must name why proof is not available HERE,
#: not why it was inconvenient to write.
EXEMPT: dict[str, str] = {
    "src/app/workflows/board_measurement.py": (
        "A replayable one-off comparison of the mounted coding boards, written to produce a "
        "measurement for a specific wave's review and kept so that measurement can be reproduced. "
        "Nothing in the serving or build path imports it. It is a candidate for deletion under the "
        "schema-narrowness rule rather than a candidate for tests."
    ),
}


def main(argv: list[str]) -> int:
    path = pathlib.Path(argv[1] if len(argv) > 1 else "coverage.json")
    if not path.is_file():
        print(f"coverage-floor: no coverage data at {path}; run the suite with --cov-report=json")
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    files = data.get("files", {})
    if not files:
        print("coverage-floor: coverage data names no files")
        return 2

    stale = sorted(name for name in EXEMPT if name not in files)
    low: list[tuple[str, float]] = []
    for name, entry in sorted(files.items()):
        if name in EXEMPT:
            continue
        percent = float(entry["summary"]["percent_covered"])
        if percent < FLOOR:
            low.append((name, percent))

    for name, percent in low:
        print(f"coverage-floor: {name} is at {percent:.0f}%, below the {FLOOR:.0f}% floor")
    for name in stale:
        print(
            f"coverage-floor: {name} is exempted and no longer exists; remove the exemption rather "
            "than leaving it to widen when the name is reused"
        )

    if low or stale:
        print(f"coverage-floor FAIL: {len(low)} module(s) below floor, {len(stale)} stale exemption(s)")
        return 1

    print(f"coverage-floor PASS: {len(files)} module(s), floor {FLOOR:.0f}%, {len(EXEMPT)} exempt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
