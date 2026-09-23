#!/usr/bin/env python3
"""Is this file actually a FILLED closure report?

The closure report `docs/closure-report-m{N}.md` is written only when the owner turns the milestone
Quality Gate on (AGENTS.md §6, Stage 4.1; `docs/closure-checklist.md` §B.1). When it exists it is
the owner's review pack for the milestone, and `make closes` grades it inside `make check`: a pack
that was generated and never filled would otherwise pass as a milestone that closed.

WRITTEN AGAINST THE TEMPLATE, not against an idea of one: every rule below is read off
`docs/closure-report.template.md`, the file the Makefile tells you to copy. (`wave_check.py` shows
why: its first version accepted `README.md`, its second rejected every row of correct work.)

WHAT IT REFUSES, and each one is a real way a closure pack goes hollow:
  * a filename that is not `closure-report-m{N}.md` -- a gate that reads whatever it is handed
  * no `record_type: closure` frontmatter -- then `check_records.py` cannot see it at all
  * a frontmatter `id` that differs from the filename -- two milestones' packs sharing an id
  * a missing section. §1 is what shipped, §1a is per wave, §1b is what was decided on the owner's
    behalf, §3 is the mechanical telemetry, §5 is the ledgers. A pack missing §1b hides the
    judgment calls, which is that section's whole reason for existing.
  * a §1 criterion with no citing test `file:line`, or whose status is not ✅ -- the Quality Gate
    is "every criterion has a citing test, and a milestone with a failing criterion does not close"
  * a placeholder left anywhere -- `<criterion>`, `<run id>`, `<initials/date>`
  * an empty cell in a table that claims evidence
  * §6 empty. Every other section is ASSEMBLED from referents; §6 is the one section a human must
    write, and it is the comprehension-debt countermeasure.
  * more than 150 lines. The template states a hard cap of two pages; a pack too long to read
    defeats the review it exists to enable.

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
    (r"^##\s*4\.\s", "§4 Security & invariants -- the invariants table and ⛔-zone touches "
                     "(the release security review is Stage 5.1, not a milestone)"),
    (r"^##\s*5\.\s", "§5 Ledgers -- nothing silent"),
    (r"^##\s*6\.\s", "§6 Architecture delta -- the one section a human writes"),
]
LINE_CAP = 150


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):    # a console that cannot encode a character prints `?`
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
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

    # §1 is read for its CONTENT, not only its shape: a pack whose citing test was `none` and whose
    # status was `❌ FAILED` must not pass.
    in_s1 = False
    for n, line in enumerate(lines, 1):
        if re.match(r"^##\s*1\.\s", line):
            in_s1 = True
            continue
        if in_s1 and line.startswith("## "):
            break
        if not in_s1 or not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower().startswith("acceptance"):
            continue
        if not re.search(r"[\w./-]+:\d+", cells[1]):
            bad.append(f"line {n}: criterion `{cells[0][:40]}` has no citing test `file:line` "
                       f"(`{cells[1][:30]}`) -- BLOCKING at the Quality Gate")
        if "✅" not in cells[3] or re.search(r"❌|FAIL", cells[3], re.I):
            bad.append(f"line {n}: criterion `{cells[0][:40]}` is `{cells[3][:20]}` -- a milestone "
                       f"with a criterion that is not ✅ does not close")

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
