#!/usr/bin/env python3
"""V3C-83 — is this file actually a FILLED closure report?

THE ASYMMETRY THIS CLOSES (2026-09-22). A wave close has had a mechanical verifier since v3.1:
`make wave-check` reads the filled checklist, demands evidence in every row and a legal status, and
refuses a sign-off line that is still a template. A MILESTONE close had none. `AGENTS.md` §4.2 and
`docs/closure-checklist.md` both mandate `docs/closure-report-m{N}.md`, and nothing ever asked
whether it exists, whether it was filled, or whether it is the artefact the template produces.

**The waves were gated and the milestones were not**, which is the wrong way round: a milestone is
where the owner's review happens, where deploy is unblocked, and where the six waves under it stop
being individually inspected.

WRITTEN AGAINST THE TEMPLATE, not against an idea of one. `wave_check.py` records that lesson three
times over: its first version accepted `README.md`, its second demanded headings the template does
not have and rejected 13 of 13 rows of correct work. So every rule below is read off
`docs/closure-report.template.md` -- the file the Makefile tells you to copy.

WHAT IT REFUSES, and each one is a real way a closure pack goes hollow:
  * a filename that is not `closure-report-m{N}.md` -- the same "gate that passes a file it was
    never meant to read" that signed off five wave closes
  * no `record_type: closure` frontmatter -- then `check_records.py` cannot see it at all
  * a missing section. §1 is what shipped, §1a is per wave, §1b is what was decided on the owner's
    behalf, §3 is the mechanical telemetry, §5 is the ledgers. A pack missing §1b is a pack that
    hides the judgment calls, which is the section's whole reason for existing.
  * a placeholder left anywhere -- `<criterion>`, `<run id>`, `<initials/date>`. The template is
    mostly angle brackets by design; a copy that still carries them was never filled.
  * an empty cell in a table that claims evidence
  * §6 empty. Every other section is ASSEMBLED from referents; §6 is the one section a human must
    write, and it is the comprehension-debt countermeasure. An empty §6 is the pack's failure mode.
  * more than 150 lines. The template states a hard cap of 2 pages and nothing enforced it; a pack
    too long to read defeats the review it exists to enable.

Exit: 0 pass · 1 fail · 2 usage.
"""
import pathlib
import re
import sys

NAME_RE = re.compile(r"^closure-report-m\d+\.md$")
PLACEHOLDER = re.compile(r"<[^<>\n]{3,}>|\bTBD\b|\bTODO\b|\bFIXME\b")
SECTIONS = [
    (r"^##\s*1\.\s", "§1 What shipped -- the criteria this milestone claims"),
    (r"^##\s*1a\.\s", "§1a Per-wave table -- one row per wave, each cell citing committed evidence"),
    (r"^##\s*1b\.\s", "§1b Decisions made on the owner's behalf -- the judgment calls"),
    (r"^##\s*2\.\s", "§2 Git record"),
    (r"^##\s*3\.\s", "§3 Trust telemetry -- computed, not asserted"),
    (r"^##\s*4\.\s", "§4 Security & invariants"),
    (r"^##\s*5\.\s", "§5 Ledgers -- nothing silent"),
    (r"^##\s*6\.\s", "§6 Architecture delta -- the one section a human writes"),
]
LINE_CAP = 150


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: closure_check.py FILE")
        return 2
    p = pathlib.Path(argv[0])
    if not p.is_file():
        print(f"closure_check CANNOT RUN: {p} does not exist -- copy "
              f"docs/closure-report.template.md to docs/closure-report-m{{N}}.md")
        return 2
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    bad: list[str] = []

    if not NAME_RE.match(p.name):
        bad.append(f"`{p.name}` is not a closure report filename. Expected "
                   f"`closure-report-m{{N}}.md` -- a gate that reads whatever it is handed is "
                   f"not a gate")
    if not re.match(r"^---\s*\n(.*?\n)?record_type:\s*closure\b", text, re.S):
        bad.append("no `record_type: closure` frontmatter -- a closure report is a governance "
                   "record, and `check_records.py` is blind to it without one")
    stem = p.stem
    m = re.search(r"^id:\s*(\S+)", text, re.M)
    if m and m.group(1) != stem:
        bad.append(f"frontmatter `id: {m.group(1)}` does not match the filename `{stem}` -- two "
                   f"milestones' packs with one id resolve to whichever the validator reads last")

    for pattern, why in SECTIONS:
        if not re.search(pattern, text, re.M):
            bad.append(f"missing {why}")

    for n, line in enumerate(lines, 1):
        hit = PLACEHOLDER.search(line)
        if hit and not line.lstrip().startswith(("<!--", ">")):
            bad.append(f"line {n} is still template: `{hit.group(0)[:48]}` -- a pack with "
                       f"placeholders was generated, not filled")
            break

    for n, line in enumerate(lines, 1):
        if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 1 and any(c == "" for c in cells):
            bad.append(f"line {n} has an empty cell in an evidence table -- an unfilled row is "
                       f"not a claim, and this pack is read as one")
            break

    body6 = re.split(r"^##\s*6\.\s", text, maxsplit=1, flags=re.M)
    if len(body6) == 2:
        prose = re.sub(r"^\*.*\*$", "", body6[1].strip(), flags=re.M).strip()
        if len(prose) < 120:
            bad.append("§6 is empty or near-empty. Every other section is ASSEMBLED from "
                       "referents; §6 is the one a human writes, and it is the whole "
                       "comprehension-debt countermeasure")

    if len(lines) > LINE_CAP:
        bad.append(f"{len(lines)} lines, cap is {LINE_CAP}. The template states a hard cap of two "
                   f"pages: a pack too long to read defeats the review it exists to enable")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"closure_check {'FAIL' if bad else 'PASS'}: {p.name}, {len(lines)} line(s), "
          f"{len(SECTIONS)} required section(s), {len(bad)} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
