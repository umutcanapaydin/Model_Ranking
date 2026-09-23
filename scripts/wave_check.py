#!/usr/bin/env python3
"""Is this file actually a FILLED wave-close checklist?

A check that asks only "does the file exist, are there empty cells, are three placeholders gone"
passes `README.md` -- and a gate that passes a file it was never meant to read signs off hollow
wave closes. So this reads the artefact `docs/wave-checklist.template.md` produces, and is written
against that template, not against an idea of one.

Refuses:
  * a filename that is not `m{N}-wave-{W}-close.md`, or no `record_type: wave` frontmatter
  * no `| # | Check | Evidence | ✅/WAIVED |` table, or a row with no evidence or no legal status
  * a row that FAILED, or a SKIPPED/WAIVED row that does not say PRESSURE or NO-ENVIRONMENT
  * an unsigned footer (`Filled by: … Date: … Wave commit range: …`) or one still a template
  * a footprint field (`Touched:`, `Mutant set author:`, `Observed RED:`, `Owner instruction:`,
    `K.8 contracts:`) missing or still a placeholder
  * a placeholder left in a cell the filler owns
  * a control with three skip/bypass rows in `docs/control-events.csv`, or SKIPPED/WAIVED rows
    with no such ledger
  * the Code-Reviewer or Tester verdict file missing beside it, or either one BLOCKING
  * from `v6.5`, either verdict file not declaring `**Independent:** yes`, unless the checklist's
    Code-Reviewer row is WAIVED and `docs/control-events.csv` has a row for this wave
  * from `v6.6`, a finding in either verdict's MINOR, K.9 or queued-risk section with no id, or
    with no row in the checklist's findings table saying what happened to it: fixed in this
    wave (a commit), filed (an issue number), or refused with a reason
  * from `v6.6`, no `Stopped at three attempts:` footprint line
The footprint fields and the review files are graded by the `process_version` the record declares
(see below). Exit 0 pass · 1 fail · 2 usage.
"""
import pathlib
import re
import sys

NAME_RE = re.compile(r"^m\d+-wave-\d+-close\.md$")          # anchored: `x-m1-wave-1-close.md` is not one
# The template's verdicts are `✅` and `WAIVED`. A FAILED gate is not a close: a wave-close gate that
# accepts an all-failed checklist is a rubber stamp.
STATUSES = {"PASS", "SKIPPED", "N/A", "✅", "WAIVED"}
FAIL_STATUSES = {"FAIL", "BLOCKED", "❌"}
HEADER_CELLS = {"check", "gate", "item", "#", "no", "step"}
PLACEHOLDER = re.compile(r"<[A-Za-z][A-Za-z0-9 _/-]{2,}>|\bTBD\b|\bTODO\b|\bFIXME\b")
LEDGER = pathlib.Path("docs/control-events.csv")
# The verdict sections whose findings the wave may leave unfixed. BLOCKING is not one: a BLOCKING
# verdict cannot close a wave at all.
DEFERRABLE = re.compile(r"MINOR|K\.9|Risks queued", re.I)
FINDING_ID = re.compile(r"^\s*[-*]\s+\*\*([A-Z]{1,3}\d+)\*\*")
# fixed `<sha>` · #<n> · refused — <a reason of a sentence>
DISPOSITION = re.compile(r"^(?:fixed\s+`?[0-9a-f]{7,40}`?|#\d+|refused\b\W+\w.{10,})", re.I)


def deferrable_findings(body: str) -> tuple[list[str], int]:
    """The ids of the findings under a MINOR / K.9 / queued-risk heading, and how many carry none.

    A bullet that says there is nothing (`- none`, `- —`) is not a finding.
    """
    ids: list[str] = []
    unnamed = 0
    in_section = False
    for line in body.splitlines():
        h = re.match(r"^#{2,4}\s+(.*)$", line)
        if h:
            in_section = bool(DEFERRABLE.search(h.group(1)))
            continue
        if not in_section or not re.match(r"^\s*[-*]\s+\S", line):
            continue
        if re.match(r"^\s*[-*]\s+(?:\*\*)?(?:none\b|n/a\b|—\s*$|-\s*$)", line, re.I):
            continue
        m = FINDING_ID.match(line)
        if m:
            ids.append(m.group(1))
        else:
            unnamed += 1
    return ids, unnamed


def findings_table(text: str) -> dict[str, str]:
    """`review M1` -> `#42`, read from the checklist's findings table (`| finding | disposition |`)."""
    rows: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == "finding" and cells[1].lower() == "disposition":
            in_table = True
            continue
        if in_table and len(cells) >= 2 and not set("".join(cells)) <= set("-: "):
            rows[" ".join(cells[0].lower().split())] = cells[1]
    return rows


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


#: The day this project adopted DevFlow (D-155) and moved to v6.4/v6.6 (D-161).
DEVFLOW_ADOPTED = "2026-09-23"


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):    # a console that cannot encode a character prints `?`
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    if len(argv) != 2:
        print("usage: wave_check.py FILE")
        return 2
    p = pathlib.Path(argv[1])
    text = p.read_text(encoding="utf-8", errors="replace")
    bad: list[str] = []

    if not NAME_RE.match(p.name):
        bad.append(f"`{p.name}` is not a wave-close checklist filename. Expected "
                   "`m{N}-wave-{W}-close.md` -- this gate used to accept README.md")
    if not re.match(r"^---\s*\n(.*?\n)?record_type:\s*wave\b", text, re.S):
        bad.append("no `record_type: wave` frontmatter -- a wave close is a governance record, and "
                   "`check_records.py` cannot see it without one")
    # The template's real shape is an evidence column and a signed footer; headings are not part
    # of it, and demanding them rejected every correctly filled close.
    if not re.search(r"^\|\s*#\s*\|\s*check\s*\|.*evidence.*\|.*(?:✅|WAIVED|status)", text, re.I | re.M):
        bad.append("no `| # | Check | Evidence | ✅/WAIVED |` table -- this is not the artefact "
                   "`docs/wave-checklist.template.md` produces")
    # The footer is signed only if it carries no placeholders: requiring a sign-off line while
    # accepting `Filled by: <agent>` makes the signature decoration.
    footer = re.search(r"^.*Filled by:.*$", text, re.I | re.M)
    if footer and PLACEHOLDER.search(footer.group(0)):
        bad.append(f"the sign-off line is still a template: `{footer.group(0).strip()[:70]}` -- an "
                   "unsigned close names nobody and no commit range, so its evidence cannot be scoped")

    # The wave footprint: recorded from the diff at close, not from the plan. Plan-time paths are a
    # prediction, close-time paths a measurement. `Mutant set author` keeps a self-designed
    # fault-injection set from reading like independent evidence; `Observed RED` records that a
    # test can fail, not only that it exists; `Owner instruction` quotes what was asked, so the
    # difference between asked and built is visible in the record.
    #
    # Graded by the version the RECORD declares, never by today's template: a wave close is
    # append-only evidence, and grading an earlier close by rules written later turns every one of
    # them red after an upgrade (UPGRADING.md). A record that declares no version gets today's
    # rules. What this gives up: a NEW record could declare an old version to skip a rule; the
    # template and `/close-wave` write the current version, and a backdated one shows in the diff.
    vm = re.search(r"^process_version:\s*v?(\d+(?:\.\d+)*)\s*$", text, re.M)
    version = tuple(int(x) for x in vm.group(1).split(".")) if vm else None
    # model_ranking (D-155 adoption review MINOR-1, D-161): the declared version is trusted only for
    # records written by the day this project adopted DevFlow. A close dated later that declares an
    # older version is graded by today's rules -- the hole the paragraph above names, closed here.
    dated = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    if dated is not None and dated.group(1) > DEVFLOW_ADOPTED:
        version = None

    def since(*v: int) -> bool:
        return version is None or version >= v

    for field, why, introduced in (
            ("Touched", "which paths this wave actually changed", (5, 0)),
            ("Mutant set author", "who designed the fault-injection set (self-designed = supporting evidence only)", (5, 1)),
            ("Observed RED", "the mutation and the assertion that failed for the cited reason", (5, 1)),
            ("Owner instruction", "the owner's words, verbatim, that this wave implements", (5, 1)),
            ("K.8 contracts", "which shared interfaces it changed, or NONE", (5, 0)),
            ("Stopped at three attempts", "each problem this wave stopped on after three failed "
             "attempts, with the bug issue that now carries it, or NONE", (6, 6))):
        if not since(*introduced):
            continue
        m = re.search(rf"^\s*{re.escape(field)}:\s*(.*)$", text, re.M)
        if not m:
            bad.append(f"no `{field}:` line -- record {why}, from the diff and not from the plan")
        elif (not m.group(1).strip() or PLACEHOLDER.search(m.group(1))
              # Anything still wrapped in <angle brackets> is a template placeholder, whatever its
              # punctuation: the check cannot be pickier about placeholder spelling than templates.
              or (m.group(1).strip().startswith("<") and m.group(1).strip().endswith(">"))):
            bad.append(f"`{field}:` is still a placeholder -- record {why}. Plan-time paths are a "
                       "prediction; close-time paths are a measurement")
    if not re.search(r"Filled by:.*Date:.*commit range", text, re.I):
        bad.append("no signed footer (`Filled by: … Date: … Wave commit range: …`) -- an unsigned "
                   "close names nobody and no commit range, so its evidence cannot be scoped")

    # Rows are the checklist's own table only: parsing starts at its `| # | Check |` header and
    # stops at the first non-table line. Scoring every table in the record as checklist rows made
    # authors rewrite legitimate structure as bullets to appease the tool.
    rows = evidence_less = 0
    review_waived = False            # the Code-Reviewer row is WAIVED: the independence out
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
        # The verdict is the LAST cell, matched on its first token so `SKIPPED NO-ENVIRONMENT`
        # is legal. Scanning every cell let a description that began with a status word stand in
        # for an empty verdict.
        last = cells[-1].upper().split()
        status = last[0] if last and last[0] in STATUSES else None
        if status == "WAIVED" and "Code-Reviewer" in cells[1]:
            review_waived = True
        if last and last[0] in FAIL_STATUSES:
            bad.append(f"line {i}: row `{cells[0][:38]}` is {last[0]} -- a wave does not close with a "
                       "failed gate. Fix it, or WAIVE it in the ledger with a reason")
        elif status is None:
            bad.append(f"line {i}: row `{cells[0][:38]}` carries no status in {sorted(STATUSES)}")
        elif status in ("SKIPPED", "WAIVED") and not re.search(r"PRESSURE|NO-ENVIRONMENT|ledger", line, re.I):
            # an undeclared skip is invisible to the three-strikes count
            bad.append(f"line {i}: SKIPPED without PRESSURE or NO-ENVIRONMENT -- an undeclared skip is "
                       "how the contract suite was skipped five times and nothing counted")
        # A NO-ENVIRONMENT skip has no command output by definition; a DATE (when it last ran
        # green, who runs it) is its evidence. Demanding a path from a row that could not run marks
        # a correct answer wrong.
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
    # Placeholders count only in the cells the filler owns -- evidence and verdict. Column 2 is the
    # template's own description of the check and legitimately contains guidance like `<list>`.
    for i, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        owned = " | ".join([c.strip() for c in line.strip().strip("|").split("|")][2:])
        for m in PLACEHOLDER.finditer(owned):
            if m.group(0).lower() in ("<br>", "<br/>", "<sub>", "<code>", "<details>", "<summary>"):
                continue                              # inline HTML is not an unfilled placeholder
            bad.append(f"line {i}: unfilled placeholder `{m.group(0)}` in a checklist row")
            break
        else:
            continue
        break

    # `docs/control-events.csv` is the ONE ledger of skips and bypasses, and the only one a gate
    # counts; wave-checklist row 9 summarises it. Three rows naming the same control turn this
    # gate red: the CONTROL goes under review, not the people. A counter nobody counts is prose.
    ledger_waves: set = set()        # the waves the ledger has a row for
    if LEDGER.is_file():
        from collections import Counter
        counts: Counter = Counter()
        for ln in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("#") or ln.lower().startswith("control,") or not ln.strip():
                continue
            cells = [c.strip() for c in ln.split(",")]
            if len(cells) >= 2:
                ledger_waves.add(cells[1])
            if len(cells) >= 3 and cells[2].lower() in ("skip", "bypass"):
                counts[cells[0]] += 1
        for control, n in sorted(counts.items()):
            if n >= 3:
                bad.append(f"`{control}` has {n} recorded skip/bypass events in {LEDGER} -- three "
                           "is the review threshold. The CONTROL goes under review before this wave "
                           "closes: fix it, re-scope it, or refuse it in docs/refusals.md. Do not "
                           "record a fourth")
    elif re.search(r"\|\s*(SKIPPED|WAIVED)\b", text):
        bad.append(f"this checklist carries SKIPPED/WAIVED rows but {LEDGER} does not exist -- a skip "
                   "that is not counted is a skip that becomes permanent. Create the ledger "
                   "(header: control,wave,kind,reason,date) and record each one")

    # Every wave closes on TWO fresh-eyes reviews, as separate subagents -- Code-Reviewer, then
    # Tester (`/close-wave`). Both verdict files must exist beside the checklist
    # (`<dir>/../reviews/`), each with a `## Verdict`, and neither may be BLOCKING. Required from
    # process_version v6.0.1, the first template that asked for them.
    m = NAME_RE.match(p.name)
    ids = re.match(r"m(\d+)-wave-(\d+)", p.name)
    wave_id = f"m{ids.group(1)}-w{ids.group(2)}" if ids else ""
    dispositions = findings_table(text)
    if m and since(6, 0, 1):
        reviews = p.resolve().parent.parent / "reviews"
        stem = p.name[: -len("-close.md")]
        for kind, who in (("review", "Code-Reviewer"), ("tester", "Tester")):
            f = reviews / f"{stem}-{kind}.md"
            if not f.is_file():
                bad.append(f"no {who} verdict at `{f.parent.name}/{f.name}` -- a wave closes on two "
                           "separate fresh-eyes reviews; run `/close-wave`")
                continue
            body = f.read_text(encoding="utf-8", errors="replace")
            v = re.search(r"^##\s*Verdict\s*\n+\s*(PASS|MINOR|BLOCKING)\b", body, re.M)
            if not v:
                bad.append(f"`{f.name}` carries no `## Verdict` of PASS / MINOR / BLOCKING")
            elif v.group(1) == "BLOCKING":
                bad.append(f"`{f.name}` is BLOCKING -- flush the fixes and re-review before the wave closes")
            # From v6.5 each verdict DECLARES that its reviewer did not write the code under review.
            # A declaration, not a proof: no file can show which session wrote it. What it buys is
            # that the claim is made in writing, by the reviewer, where a false one can be found.
            # The author reviewing is legal only as a waiver the ledger counts.
            if since(6, 5) and not (review_waived and wave_id in ledger_waves) and not re.search(
                    r"^\s*\*\*Independent:\*\*[ \t]*yes\b", body, re.M | re.I):
                bad.append(f"`{f.name}` does not declare `**Independent:** yes` -- a reviewer that "
                           "wrote the code cannot close the wave; if the author reviewed, mark the "
                           "row WAIVED with a row in docs/control-events.csv")
            # From v6.6 a finding the wave does not fix leaves the wave as an issue. Every finding
            # in a MINOR / K.9 / queued-risk section carries an id (`**M1**`), and the checklist's
            # findings table says what happened to each: fixed here, filed, or refused with a
            # reason. Before this, review findings were "queued to next M" inside a file nobody
            # queried -- one field project wrote 99 review files and filed no issue from them.
            if since(6, 6):
                found, unnamed = deferrable_findings(body)
                if unnamed:
                    bad.append(f"`{f.name}` has {unnamed} MINOR/K.9/queued finding(s) with no id -- "
                               "start each with `**M1**` (MINOR), `**K1**` (K.9) or `**R1**` (risk) "
                               "so the checklist can say what happened to it")
                for fid in found:
                    key = f"{kind} {fid.lower()}"
                    d = dispositions.get(key)
                    if d is None:
                        bad.append(f"`{f.name}` finding {fid} has no row in the checklist's findings "
                                   f"table (`| {kind} {fid} | ... |`) -- fix it in this wave and cite "
                                   "the commit, or /file-issue it and cite the number")
                    elif not DISPOSITION.match(d):
                        bad.append(f"finding `{kind} {fid}` has disposition `{d[:40]}` -- write fixed "
                                   "`<sha>`, `#<issue>`, or `refused — <why the finding is wrong>`")

    for b in bad:
        print(f"FAIL [wave-check]: {b}")
    if bad:
        return 1
    print(f"wave-check PASS: {p} ({rows} row(s), all evidenced and statused)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
