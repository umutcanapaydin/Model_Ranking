#!/usr/bin/env python3
"""V3C-69 — is this file actually a FILLED wave-close checklist?

The version this replaces asked three questions: does the file exist, are there empty table cells, are
three named placeholders present. `README.md` answers those correctly, so `make wave-check
FILE=README.md` printed PASS. So did `docs/closure-checklist.md`. **The gate had no idea what a wave
checklist looks like** -- and it signed off five wave closes in the field, including the five where the
contract suite was skipped.

Checks now: the filename shape, the frontmatter, the required sections, that every row carries evidence
and a legal status, and that nothing is left as a placeholder. Exit 0 pass · 1 fail · 2 usage.
"""
import pathlib
import re
import sys

# v4.3.2 SECOND REPAIR (audit B5/B6). The first version was written against the fixture instead of
# against `docs/wave-checklist.template.md` -- the artefact the Makefile tells you to copy. Consequence:
# it REJECTED 13 of 13 rows of a correctly filled real checklist (the template's verdicts are `✅` and
# `WAIVED`, not `PASS`/`FAIL`; its header's first cell is `#`, so the header was scored as data), while
# still ACCEPTING a four-line file that merely contained the words "gates" and "evidence" somewhere.
# **A gate written to its own fixture proves the fixture, not the gate** -- and a gate that fails 100%
# of correct work is switched off within a week, which is worse than the one that passed README.md.
NAME_RE = re.compile(r"^m\d+-wave-\d+-close\.md$")          # anchored: `x-m1-wave-1-close.md` is not one
# `❌` removed: a close in which a gate FAILED is not a close. It was legal for one round because the
# check was written as "shape only", and a wave-CLOSE gate that accepts an all-failed checklist is a
# rubber stamp with extra steps.
STATUSES = {"PASS", "SKIPPED", "N/A", "✅", "WAIVED"}
FAIL_STATUSES = {"FAIL", "BLOCKED", "❌"}
HEADER_CELLS = {"check", "gate", "item", "#", "no", "step"}
NEEDED = ("gates", "evidence")
PLACEHOLDER = re.compile(r"<[A-Za-z][A-Za-z0-9 _/-]{2,}>|\bTBD\b|\bTODO\b|\bFIXME\b")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: wave_check.py FILE"); return 2
    p = pathlib.Path(argv[1])
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    bad: list[str] = []

    if not NAME_RE.match(p.name):
        bad.append(f"`{p.name}` is not a wave-close checklist filename. Expected "
                   "`m{N}-wave-{W}-close.md` -- this gate used to accept README.md")
    # The error message named `record_type: wave`; the check only asked whether the file began with
    # `---`. A file whose entire frontmatter was the word "gates" passed both this and the section test.
    if not re.match(r"^---\s*\n(.*?\n)?record_type:\s*wave\b", text, re.S):
        bad.append("no `record_type: wave` frontmatter -- a wave close is a governance record, and "
                   "`check_records.py` cannot see it without one")
    # THIRD attempt at this check, and the lesson is the same each time: the first demanded the
    # substring "gates" anywhere (a shopping list passed), the second demanded `## Gates` and
    # `## Evidence` HEADINGS -- which `docs/wave-checklist.template.md` does not have and never had.
    # **Both versions were written from an idea of what a checklist looks like instead of from the
    # template the Makefile tells you to copy.** The template's real shape is: an evidence column and
    # a signed footer. That is what is required.
    if not re.search(r"^\|\s*#\s*\|\s*check\s*\|.*evidence.*\|.*(?:✅|WAIVED|status)", text, re.I | re.M):
        bad.append("no `| # | Check | Evidence | ✅/WAIVED |` table -- this is not the artefact "
                   "`docs/wave-checklist.template.md` produces")
    # v4.3.2, SECOND PASS (audit B1). This rewrite ADDED the signed-footer requirement and, in the
    # same change, narrowed the placeholder scan from "the whole file" (what the old five-line Makefile
    # recipe did) to "table cells only". Net effect: a close whose signature line still read
    # `Filled by: <agent> · Date: <YYYY-MM-DD>` PASSED, where v4.3 had failed it.
    # **The round that made the signature mandatory removed the check that made it real.**
    # The footer is signed only if it carries no placeholders.
    footer = re.search(r"^.*Filled by:.*$", text, re.I | re.M)
    if footer and PLACEHOLDER.search(footer.group(0)):
        bad.append(f"the sign-off line is still a template: `{footer.group(0).strip()[:70]}` -- an "
                   "unsigned close names nobody and no commit range, so its evidence cannot be scoped")
    # v5.0 — the wave footprint. NOT a rule about parallelism: no check here compares one wave's paths
    # to another's, and none will until two milestones have filled these in. It is a rule that the
    # RECORD gets filled, because a metadata field nobody is asked for is the sediment this release
    # spent a day removing. The question it will eventually answer -- can waves run as parallel
    # subagents -- needs measurement, and measurement needs a collector.
    for field, why in (("Touched", "which paths this wave actually changed"),
                       ("K.8 contracts", "which shared interfaces it changed, or NONE")):
        m = re.search(rf"^\s*{re.escape(field)}:\s*(.*)$", text, re.M)
        if not m:
            bad.append(f"no `{field}:` line -- record {why}, from the diff and not from the plan")
        elif not m.group(1).strip() or PLACEHOLDER.search(m.group(1)):
            bad.append(f"`{field}:` is still a placeholder -- record {why}. Plan-time paths are a "
                       "prediction; close-time paths are a measurement")
    if not re.search(r"Filled by:.*Date:.*commit range", text, re.I):
        bad.append("no signed footer (`Filled by: … Date: … Wave commit range: …`) -- an unsigned "
                   "close names nobody and no commit range, so its evidence cannot be scoped")

    rows = evidence_less = 0
    for i, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set("".join(cells)) <= set("-: ") or cells[0].lower() in HEADER_CELLS:
            continue
        rows += 1
        # Match on the FIRST TOKEN, because Block D requires a skip to be written
        # `SKIPPED NO-ENVIRONMENT` -- and an exact-match test rejected the very format the rule above
        # it demands. Two rules in one file disagreeing about their own syntax is how a control gets
        # a reputation for being wrong, and a control with that reputation stops being run.
        # Scanning ALL cells let a row whose DESCRIPTION began with a status word satisfy the check
        # with an empty verdict cell. The verdict is the last cell; that is the only one that counts.
        last = cells[-1].upper().split()
        status = last[0] if last and last[0] in STATUSES else None
        if last and last[0] in FAIL_STATUSES:
            bad.append(f"line {i}: row `{cells[0][:38]}` is {last[0]} -- a wave does not close with a "
                       "failed gate. Fix it, or WAIVE it in the ledger with a reason")
        elif status is None:
            bad.append(f"line {i}: row `{cells[0][:38]}` carries no status in {sorted(STATUSES)}")
        elif status in ("SKIPPED", "WAIVED") and not re.search(r"PRESSURE|NO-ENVIRONMENT|ledger", line, re.I):
            # v4.3 Block D: a skip must declare which kind it is, or it is invisible to the 3x trigger
            bad.append(f"line {i}: SKIPPED without PRESSURE or NO-ENVIRONMENT -- an undeclared skip is "
                       "how the contract suite was skipped five times and nothing counted")
        # A NO-ENVIRONMENT skip has no command output by definition -- Block D asks it for something
        # else: who runs it, where, and when it last ran green. A DATE is that evidence. Demanding a
        # backticked path from a row that could not run is how a correct answer gets marked wrong, and
        # a gate that fails correct work gets switched off. (Caught by the positive fixture, which is
        # why the positive fixture exists.)
        ev = " ".join(cells[1:])
        has_ev = ("`" in ev or "http" in ev or re.search(r"\w+\.\w+:\d+", ev)
                  or (status in {"SKIPPED", "N/A", "WAIVED"} and re.search(r"\d{4}-\d{2}-\d{2}", ev)))
        if not has_ev:
            evidence_less += 1

    if rows == 0:
        bad.append("no checklist rows found -- this is not a filled checklist")
    elif evidence_less:
        bad.append(f"{evidence_less} of {rows} row(s) carry no evidence (a backticked path, a "
                   "`file:line`, or a URL). An unevidenced PASS is an opinion")
    # Placeholders are only meaningful INSIDE TABLE CELLS -- what the filler was supposed to replace.
    # The template's own guidance prose contains `<list>` as an instruction, and a gate that fails a
    # correctly filled checklist because the template explained itself is a gate that gets deleted.
    # (Caught by filling the real template, which is the test that should have been written first.)
    for i, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        # Only the cells the FILLER owns -- evidence and verdict. Column 2 is the template's own
        # description of the check and legitimately contains guidance like `<list>`; failing a
        # correctly filled checklist because the template described itself is how a gate loses its
        # audience. (Found by filling the real template rather than trusting the fixture.)
        owned = " | ".join([c.strip() for c in line.strip().strip("|").split("|")][2:])
        for m in PLACEHOLDER.finditer(owned):
            if m.group(0).lower() in ("<br>", "<br/>", "<sub>", "<code>", "<details>", "<summary>"):
                continue                              # inline HTML is not an unfilled placeholder
            bad.append(f"line {i}: unfilled placeholder `{m.group(0)}` in a checklist row")
            break
        else:
            continue
        break

    for b in bad:
        print(f"FAIL [V3C-69]: {b}")
    if bad:
        return 1
    print(f"wave-check PASS: {p} ({rows} row(s), all evidenced and statused)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
