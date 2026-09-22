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


#: REQ-REV-001 was written at M11. GPF-001 already ruled that a tool may not retroactively
#: invalidate records written before it existed, so the FORMAT half of this gate -- cite a review
#: record, and let it declare its seat -- applies from M11 onward. The other half does not scope:
#: citing a file that DOES NOT EXIST was wrong in every era, and the first run of this gate found
#: exactly one, in the one wave record that claimed an independent review (W-056).
SEAT_RULE_FROM_MILESTONE = 11


def review_seat_problems(text: str, root: pathlib.Path, milestone: int | None) -> list[str]:
    """REQ-REV-001 — a self-review may not close a wave GREEN.

    **What this checks, stated narrowly because the opposite claim is this project's own recurring
    defect.** It does NOT verify that a review ran in a separate session; no file can show that. It
    checks one thing: a wave-close record whose review row is PASS must cite a review record, and
    that record must declare `seat: independent`. A review declaring `seat: author` forces the row
    to be WAIVED, which Block D already forces to name a ledger id, which puts it in front of the
    owner.

    So the gate converts "the author reviewed their own code" from a sentence in a record into a
    thing that cannot pass silently. Whether `independent` is TRUE remains a claim the process
    makes -- and the reason that is acceptable here is that the failure this rule exists to stop
    was never a lie. K.7 was bypassed four times in the open, each time recorded, and closed green
    anyway.
    """
    bad: list[str] = []
    # PASS ONE -- every line, every era, no status filter. The first version of this function put
    # the broken-citation check AFTER the `WAIVED`/`SKIPPED` early exit, and the W-056 remediation
    # then set the offending row to WAIVED: the record that motivated this entire gate became
    # invisible to it, by way of its own fix. Reported by the independent seat as BLOCKING-3, which
    # is the first thing that seat existed to do.
    for i, line in enumerate(text.splitlines(), 1):
        for rel in re.findall(r"`(docs/reviews/[^`]+\.md)`", line):
            if ".." in rel:
                bad.append(f"line {i}: cites `{rel}`, which escapes `docs/reviews/`. A wave record "
                           "that can cite itself as its own review is not a citation")
            elif not (root / rel).is_file():
                bad.append(f"line {i}: cites `{rel}`, which does not exist. A review that is not a "
                           "file is a claim about a conversation")

    # PASS TWO -- the RECORD-level rule, which applies from M11 (GPF-001).
    #
    # **This asks nothing about row LABELS, and that is the whole repair.** The first version found
    # the review row by grepping the name cell for `review|K.7`, so renaming row 3 to "Fresh eyes
    # per tier" made the gate skip it entirely and the record closed green with no review cited and
    # none in existence. Reproduced by the independent seat against a copy of a real wave record:
    # baseline PASS, rename, still PASS, exit 0. The gate failed OPEN on a label it did not know.
    #
    # A gate whose scope is set by free text a filler chooses is a gate the filler can switch off
    # without meaning to. So the question moved from "is this row a review row" -- which only the
    # label answers -- to one the record answers as a whole:
    #
    #   **does this close cite a review by a seat that did not write the code, or does it name a
    #   ledger row for the bypass?**
    #
    # Both remedies stay available and neither can be renamed away.
    if milestone is not None and milestone < SEAT_RULE_FROM_MILESTONE:
        return bad

    cited = {r for r in re.findall(r"`(docs/reviews/[^`]+\.md)`", text) if ".." not in r}
    # **A review dated before this close cannot have read this close's code.** M12's four waves all
    # closed K.7 green citing council records from the day before, and the rows said so in as many
    # words — "the review preceded the code" — which is the proof, not the defence. The seats had
    # reviewed the PREVIOUS milestone and named findings this one implemented; nobody independently
    # read the code until Stage 4.0, which then found two blocking defects in it.
    #
    # The gate could not see it: it asked whether a cited review exists and declares an independent
    # seat, and had no notion of whether that seat could have SEEN the work. Dates are a coarse
    # instrument and they are the one the records carry.
    #
    # An older review may still be CITED — it is often what shaped the wave — but it cannot
    # discharge K.7 for code written after it. The wave waives instead, and the waiver names its
    # ledger row, which is what puts the bypass in front of the owner (V4C-13).
    wave_date = re.search(r"^date:\s*(\S+)\s*$", text, re.M)
    seats: dict[str, str | None] = {}
    stale: list[str] = []
    for rel in sorted(cited):
        path = root / rel
        if not path.is_file():
            continue  # already reported in pass one, in every era
        front = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", path.read_text(encoding="utf-8"), re.S)
        # FRONTMATTER ONLY. Reading `^seat:` from anywhere in the file meant a four-line document
        # with no frontmatter at all, containing the prose line `seat: independent`, closed a wave
        # green -- measured by the seat that reviewed this gate.
        found = re.search(r"^seat:\s*(\S+)\s*$", front.group(1), re.M) if front else None
        review_date = re.search(r"^date:\s*(\S+)\s*$", front.group(1), re.M) if front else None
        if wave_date and review_date and review_date.group(1) < wave_date.group(1):
            stale.append(f"`{rel}` ({review_date.group(1)})")
            continue
        seats[rel] = found.group(1) if found else None

    if any(seat == "independent" for seat in seats.values()):
        return bad

    # No independent review. Then the bypass has to be COUNTED (V4C-13), which means a waived or
    # skipped row naming a ledger id. Block D already forces a waiver to declare its kind; this is
    # the half AGENTS.md claimed and did not have.
    waived_with_ledger = any(
        re.search(r"\bW-\d{3}\b", line)
        and re.search(r"\b(WAIVED|SKIPPED)\b", line.upper())
        for line in text.splitlines()
        if line.lstrip().startswith("|")
    )
    if waived_with_ledger:
        return bad

    unseated = sorted(rel for rel, seat in seats.items() if seat is None)
    if unseated:
        bad.append(f"cites {', '.join(f'`{r}`' for r in unseated)}, which declare no `seat:` -- "
                   "REQ-REV-001 requires every review a v5.0 close relies on to say whether the "
                   "seat wrote the code")
    elif seats:
        authored = sorted(rel for rel, seat in seats.items() if seat != "independent")
        bad.append(f"the only review(s) cited are {', '.join(f'`{r}`' for r in authored)}, and "
                   "none declares `seat: independent`. A self-review does not close a wave green "
                   "-- waive a row with its ledger id so the bypass is counted (V4C-13)")
    elif stale:
        bad.append(f"the only review(s) cited are {', '.join(stale)}, dated BEFORE this close "
                   f"({wave_date.group(1) if wave_date else '?'}) — a review cannot have read code "
                   "written after it. Cite a review of THIS work, or waive a row naming its "
                   "ledger id")
    else:
        bad.append("this close cites no review record at all, and waives nothing. A review that "
                   "is not a file is a claim about a conversation -- cite one with "
                   "`seat: independent`, or waive a row naming its ledger id")
    return bad
    for i, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        # Match on the CHECK-NAME cell, not the whole line. Case-insensitive and not a fixed
        # phrase, because the seat proved a self-review passed simply by relabelling the row
        # `Fresh-eyes code review`. But scanning the WHOLE line over-corrects the other way: this
        # record's own rows 2 and 5 mention "self-review" and "test_review_seat_gate.py" in their
        # EVIDENCE, and were read as review rows that cite nothing. The check being performed lives
        # in one cell; that is the only cell that says what a row IS.
        name = cells[1] if len(cells) >= 3 else cells[0]
        if not re.search(r"K\.7|review", name, re.I):
            continue
        status = cells[-1].upper().split()[0] if cells[-1].split() else ""
        cited = [r for r in re.findall(r"`(docs/reviews/[^`]+\.md)`", line) if ".." not in r]
        if status in ("SKIPPED", "WAIVED"):
            # Block D makes a waiver declare its KIND. AGENTS.md additionally claims a waived review
            # row names a LEDGER ROW, and that claim was false until the seat checked it: a row
            # reading `WAIVED -- PRESSURE`, admitting a self-review in its own text and citing no
            # review at all, passed. The claim is now true.
            if not re.search(r"\bW-\d{3}\b", line):
                bad.append(f"line {i}: the review row is {status} and names no ledger row. A bypass "
                           "that is not counted is invisible to the 3x trigger (V4C-13)")
            continue
        if not cited:
            bad.append(f"line {i}: the review row passes but cites no review record. A review that "
                       "is not a file is a claim about a conversation")
            continue
        for rel in cited:
            path = root / rel
            if not path.is_file():
                continue  # already reported above, in every era
            # FRONTMATTER ONLY. Reading `^seat:` from anywhere in the file meant a four-line
            # document with no frontmatter at all, containing the prose line `seat: independent`,
            # closed a wave green -- verified by the independent seat. The frontmatter block is the
            # part `check_records.py` validates; the body is prose, and prose is what this whole
            # rule exists to stop being evidence.
            body = path.read_text(encoding="utf-8")
            front = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", body, re.S)
            seat = re.search(r"^seat:\s*(\S+)\s*$", front.group(1), re.M) if front else None
            if seat is None:
                bad.append(f"line {i}: `{rel}` declares no `seat:` -- REQ-REV-001 requires every "
                           "review a v5.0 close relies on to say whether the seat wrote the code")
            elif seat.group(1) != "independent":
                bad.append(f"line {i}: `{rel}` declares `seat: {seat.group(1)}` and the row is "
                           f"{status or 'PASS'}. A self-review does not close a wave green -- WAIVE "
                           "the row with its ledger id so the bypass is counted (V4C-13)")
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: wave_check.py FILE")
        return 2
    p = pathlib.Path(argv[1])
    text = p.read_text(encoding="utf-8", errors="replace")
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
    # v5.1 (Increment 15, Block D). Three more recorded fields, same shape as the footprint:
    #  P-1  Mutant set author -- 23/23=100% self-designed read exactly like evidence next to 12/47=25.5%
    #       independent over the same range. A self-designed set is supporting evidence, never sufficient.
    #  P-11 Observed RED -- three tests written to close review findings could not fail (fixtures never
    #       reached what they asserted). "A test exists" and "a test can fail" are different claims;
    #       the row now records the mutation and which assertion went red.
    #  Owner instruction -- the measured failure direction was an agent substituting its own better
    #       idea for the owner's stated requirement, TWICE, while every control stayed green. The
    #       checklist quotes the instruction verbatim so the diff between asked and built is visible
    #       in the artefact instead of only in the owner's reaction.
    # model_ranking, DevFlow v6.0 adoption (D-155). The three v5.1 fields below are required of a
    # record that declares a process version AFTER v5.0. This project's 41 wave records declare
    # v5.0 and were written before the fields existed; GPF-001 rules that a tool may not
    # retroactively invalidate them. A record with no declared version keeps the full rule.
    declared = re.search(r"^process_version:\s*(\S+)", text, re.M)
    dated = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    # Adoption review MINOR-1: a DECLARED version alone let a record written later claim the old
    # template. The skip also needs a date on or before the DevFlow adoption.
    pre_v51 = (declared is not None and declared.group(1) in {"v5.0", "v4.3", "v4.3.1", "v4.2", "v4.1"}
               and dated is not None and dated.group(1) <= "2026-09-23")
    later = {"Mutant set author", "Observed RED", "Owner instruction"}
    for field, why in (("Touched", "which paths this wave actually changed"),
                       ("Mutant set author", "who designed the fault-injection set (self-designed = supporting evidence only, P-1)"),
                       ("Observed RED", "the mutation and the assertion that failed for the cited reason (P-11)"),
                       ("Owner instruction", "the owner's words, verbatim, that this wave implements"),
                       ("K.8 contracts", "which shared interfaces it changed, or NONE")):
        if pre_v51 and field in later:
            continue
        m = re.search(rf"^\s*{re.escape(field)}:\s*(.*)$", text, re.M)
        if not m:
            bad.append(f"no `{field}:` line -- record {why}, from the diff and not from the plan")
        elif (not m.group(1).strip() or PLACEHOLDER.search(m.group(1))
              # A template placeholder is anything still wrapped in <angle brackets>, whatever its
              # punctuation. The narrow PLACEHOLDER class missed `<who designed ...; ... (P-1)>`
              # because of the semicolon -- an unfilled field passed the first falsification run of
              # this very change. The check exists BECAUSE fields go unfilled; it cannot be pickier
              # about placeholder spelling than templates are.
              or (m.group(1).strip().startswith("<") and m.group(1).strip().endswith(">"))):
            bad.append(f"`{field}:` is still a placeholder -- record {why}. Plan-time paths are a "
                       "prediction; close-time paths are a measurement")
    if not re.search(r"Filled by:.*Date:.*commit range", text, re.I):
        bad.append("no signed footer (`Filled by: … Date: … Wave commit range: …`) -- an unsigned "
                   "close names nobody and no commit range, so its evidence cannot be scoped")

    rows = evidence_less = 0
    # v5.1 (harvest 2 B.5 / P-10). Parsing EVERY pipe-line as a checklist row meant any other table in
    # the record -- a "claimed vs independently measured" comparison, say -- was scored as unevidenced
    # checklist rows and failed the file. The field cost: authors rewrote legitimate structure as
    # bullet lists to appease the tool. **A validator that punishes structure teaches people to put
    # less structure in records.** Rows are now anchored to the checklist's own header table: parsing
    # starts at the `| # | Check |...` header and stops at the first non-table line. Other tables are
    # someone else's business.
    in_checklist = False
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if not stripped.startswith("|"):
            in_checklist = False
            continue
        first_cell = stripped.strip("|").split("|")[0].strip().lower()
        if first_cell in HEADER_CELLS:
            in_checklist = True
            continue
        if not in_checklist:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set("".join(cells)) <= set("-: "):
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

    # The repo root is derived from the record's OWN path rather than the cwd, because this gate is
    # invoked both from `make` and per-file by `wave_check_all.py`, and a cwd-relative lookup would
    # make the review-record check silently vacuous from one of them. A check that passes because it
    # found nothing to look at is this project's most-repeated defect.
    root = next((a for a in p.resolve().parents if (a / "docs").is_dir()), p.resolve().parent)
    milestone_match = re.match(r"m(\d+)-wave-", p.name)
    # DevFlow's conformance fixtures (`conformance/wave/`) cite review records that do not exist, on
    # purpose: a fixture demonstrates a record's SHAPE and names absent artifacts. The review-seat
    # rule is this project's, about this project's records, so it does not grade the package's
    # fixtures (the same boundary DevFlow's X4 draws around `conformance/`).
    if p.resolve().relative_to(root).parts[:1] != ("conformance",):
        bad.extend(review_seat_problems(
            text, root, int(milestone_match.group(1)) if milestone_match else None))

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

    # v5.1 (P-9 + the skip ledger, merged per PM). V4C-13's three-strikes trigger has existed since
    # v4.0 and has never once fired by mechanism -- it fired ONCE, because one scrupulous author
    # hand-wrote "this is the third" into a record, and even that hand count was wrong (two records
    # both claimed "second"). A counter nobody counts is prose. `docs/control-events.csv` is ONE
    # machine-readable ledger for skips AND bypasses; three rows naming the same control turn this
    # gate red -- the control goes under review, not the people.
    ledger = pathlib.Path("docs/control-events.csv")
    if ledger.is_file():
        from collections import Counter
        counts: Counter = Counter()
        for ln in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("#") or ln.lower().startswith("control,") or not ln.strip():
                continue
            cells = [c.strip() for c in ln.split(",")]
            if len(cells) >= 3 and cells[2].lower() in ("skip", "bypass"):
                counts[cells[0]] += 1
        for control, n in sorted(counts.items()):
            if n >= 3:
                bad.append(f"`{control}` has {n} recorded skip/bypass events in docs/control-events.csv "
                           "-- V4C-13's threshold. The CONTROL goes under review before this wave "
                           "closes: fix it, re-scope it, or refuse it in docs/refusals.md. Do not "
                           "record a fourth")
    else:
        # SKIPPED/WAIVED rows demand the ledger exist -- a waiver with no counter is how five skips
        # went unread in the field until six engine defects surfaced at the owner gate.
        if re.search(r"\|\s*(SKIPPED|WAIVED)\b", text):
            bad.append("this checklist carries SKIPPED/WAIVED rows but docs/control-events.csv does "
                       "not exist -- a skip that is not counted is a skip that becomes permanent. "
                       "Create the ledger (header: control,wave,kind,reason,date) and record each one")

    for b in bad:
        print(f"FAIL [V3C-69]: {b}")
    if bad:
        return 1
    print(f"wave-check PASS: {p} ({rows} row(s), all evidenced and statused)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
