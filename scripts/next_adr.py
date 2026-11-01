#!/usr/bin/env python3
"""`make next-adr`: the next free ADR ids in `docs/decisions.md`, without reading the file into a session.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit E-28). `/log-decision` told the agent to read
`docs/decisions.md` for the next id; in the largest field project that file is 5,000 lines, about 80k
tokens per ADR spent on one number. This prints it.

Project ADRs start at D-100 (D-001..D-099 is the universal band, never the base): the next one is the
highest `## D-<n>` heading at or above 100, plus one -- or D-100 while D-100 is still the shipped
`<First project decision>` placeholder, which the first decision fills. Process ADRs are `P-<n>`.
D-999 is not in the project band: DevFlow v6.0 shipped one under that number ("the agent opens drafts;
a human merges"), and a project that kept it got `D-1000` as its next id (Project-J, v7.2.1).

Exit: 0 printed - 2 no `docs/decisions.md` (nothing to number against; fail closed).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
#: #330: the widest step between two ids in the run; a farther id is a name (D-999), not the next place.
GAP = 100
HEADING = re.compile(r"^##[ \t]+([DP])-(\d+)\b(.*)$", re.M)


def next_ids(text: str) -> tuple[str, str]:
    project, process, placeholder = [], [], False
    for kind, num, rest in HEADING.findall(text):
        n = int(num)
        if kind == "P":
            process.append(n)
        elif 100 <= n < 999:
            project.append(n)
            placeholder |= n == 100 and "<First project decision>" in rest
    if not project or (placeholder and project == [100]):
        d = 100
    else:
        # #330: an id more than GAP past the one before it is a name, not a place in the run (this project's
        # D-999, "the agent opens drafts", sat after D-207 and made the next id D-1000).
        run = sorted(set(project))
        last = run[0]
        for n in run[1:]:
            if n - last > GAP:
                break
            last = n
        d = last + 1
    return f"D-{d}", f"P-{max(process, default=0) + 1:03d}"


def main() -> int:
    path = ROOT / "docs" / "decisions.md"
    if not path.is_file():
        print("next-adr CANNOT RUN: no docs/decisions.md -- there is nothing to number against")
        return 2
    d, p = next_ids(path.read_text(encoding="utf-8", errors="replace"))
    print(f"{d}  -- the next project ADR (append it at the end of docs/decisions.md)")
    print(f"{p}  -- the next process ADR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
