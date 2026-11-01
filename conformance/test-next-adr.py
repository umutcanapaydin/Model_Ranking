#!/usr/bin/env python3
"""`make next-adr` prints the id `/log-decision` would have computed by reading the whole file.

WHY (v7.2, the owner's ruling of 2026-10-17). `/log-decision` now asks `scripts/next_adr.py` for the
next id instead of reading `docs/decisions.md`; a wrong number there is a reused id, which the ADR rules
forbid (seed B.5). The cases: the shipped placeholder, a filled D-100, the universal band never the
base, a gap, a superseded ADR still counted, process ids, and the package's own `docs/decisions.md`.

Exit: 0 every case - 1 one is wrong.
"""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("next_adr", ROOT / "scripts" / "next_adr.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CASES = [
    ("the shipped placeholder is filled first",
     "## D-001 — a\n## D-007 — b\n## P-001 — c\n## D-100 — `<First project decision>` (YOUR PROJECT STARTS HERE)\n",
     ("D-100", "P-002")),
    ("a filled D-100 is followed by D-101", "## D-005 — a\n## D-100 — Postgres\n", ("D-101", "P-001")),
    ("the universal band is never the base", "## D-001 — a\n## D-099 — b\n", ("D-100", "P-001")),
    ("the highest id, not the count", "## D-100 — a\n## D-104 — b\n## D-102 — c\n", ("D-105", "P-001")),
    ("a superseded ADR still holds its id",
     "## D-100 — a\n## D-101 — b\n**Status:** superseded by D-102\n## D-102 — c\n", ("D-103", "P-001")),
    ("process ids count on their own", "## P-001 — a\n## P-003 — b\n## D-100 — c\n", ("D-101", "P-004")),
    ("an id in prose is not a heading", "## D-100 — a\nSee D-250 later.\n", ("D-101", "P-001")),
    # #330: model_ranking's D-999 ("the agent opens drafts; a human merges") is a name, not a place in the
    # run of ids; `make next-adr` printed D-1000 after D-207.
    ("an id far past the run is a name, not the next place",
     "## D-100 — a\n## D-101 — b\n## D-999 — c\n## D-102 — d\n", ("D-103", "P-001")),
    ("an id far past the run is still counted once the run reaches it",
     "## D-100 — a\n## D-150 — b\n## D-180 — c\n", ("D-181", "P-001")),
    ("the D-999 a v6.0 install kept is not the base", "## D-206 — a\n## D-207 — b\n## D-999 — c\n",
     ("D-208", "P-001")),
]


def main() -> int:
    bad = []
    for name, text, want in CASES:
        got = mod.next_ids(text)
        if got != want:
            bad.append(f"  {name}: got {got}, want {want}")
    shipped = mod.next_ids((ROOT / "docs" / "decisions.md").read_text(encoding="utf-8"))
    if (ROOT / ".gp-distribution").is_file() and shipped[0] != "D-100":
        bad.append(f"  the package's docs/decisions.md: got {shipped[0]}, want D-100 (its placeholder)")
    if bad:
        print("test-next-adr FAIL (scripts/next_adr.py):")
        print("\n".join(bad))
        return 1
    print(f"test-next-adr PASS: {len(CASES)} cases -- the next project and process ids, the placeholder "
          "first, the universal band never the base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
