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
import fnmatch
import pathlib
import re
import subprocess
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
    finding_above = False
    for line in body.splitlines():
        h = re.match(r"^#{2,4}\s+(.*)$", line)
        if h:
            in_section = bool(DEFERRABLE.search(h.group(1)))
            finding_above = False
            continue
        if not in_section or not re.match(r"^\s*[-*]\s+\S", line):
            continue
        # An indented bullet belongs to the finding above it (the W3 Tester's M9); one with no finding
        # above it is still counted, so a verdict indented throughout fails closed.
        if re.match(r"^\s+[-*]\s", line) and finding_above:
            continue
        finding_above = True
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


#: The day this project adopted DevFlow (D-155) and moved to v6.4/v6.6 (D-161), and the version it
#: was on at the end of that day: a close written later declares at least this one.
DEVFLOW_ADOPTED = "2026-09-23"
CURRENT_AT_ADOPTION = (6, 6)
#: #83: closes dated from this day on are held to "a diff touching input parsing is HIGH".
INPUT_PARSING_HIGH_FROM = "2026-10-04"
#: #140: closes dated from this day on are held to their own plan's security globs.
PLAN_GLOBS_HIGH_FROM = "2026-10-06"


#: The gates' own globs, which every plan's list carries (the M21 closure fixes review's M7): a wave that changes a
#: gate is HIGH whatever its milestone's plan lists, so the gates do not lapse when a milestone ends.
STANDING_GLOBS = ("scripts/wave_check.py", "scripts/check_records.py", "scripts/commit_gate.py", "scripts/check_fast.py",
                  "scripts/client_decl_gate.py", "scripts/client_decl_fixtures/**", "Makefile", ".githooks/**",
                  ".claude/**")


def plan_globs(plan: pathlib.Path) -> list[str]:
    """#140: the security globs a milestone plan lists, under its `Security globs` bullet: every
    backticked path on the indented bullets that follow it. None (or no plan) is an empty list, which
    the caller refuses: a plan that names no globs cannot say what makes a wave HIGH."""
    if not plan.is_file():
        return []
    lines = plan.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next((i for i, line in enumerate(lines)
                  if re.match(r"^\s*-\s*\**\s*Security globs\b", line, re.I)), None)
    if start is None:
        return []
    globs: list[str] = []
    for line in lines[start + 1:]:
        # A bullet, or the continuation of one that wrapped (indented, no dash): the W3 review's M3.
        if not (re.match(r"^\s+-\s", line) or (re.match(r"^\s{3,}\S", line) and globs)):
            break
        globs += re.findall(r"`([^`]+)`", line)
    return list(dict.fromkeys([*globs, *STANDING_GLOBS])) if globs else globs


def _footprint_paths(touched: str) -> list[str]:
    """#140 and the W3 review's M2: the paths a footprint names, a brace form expanded
    (`Engine/{Models,EngineClient}.swift`)."""
    # A space inside braces is part of the brace form (the W3 Tester's M6).
    touched = re.sub(r"\{[^{}]*\}", lambda found: re.sub(r"\s+", "", found.group(0)), touched)
    paths: list[str] = []
    for token in re.split(r"[\s·]+", touched):
        pending = [token.strip("`,;()").removeprefix("./")]
        while pending:
            path = pending.pop()
            braced = re.match(r"^(.*?)\{([^{}]+)\}(.*)$", path)
            if braced:  # every group, one at a time
                pending += [f"{braced.group(1)}{part}{braced.group(3)}" for part in braced.group(2).split(",")]
            elif path:
                paths.append(path)
    return paths


def _touches(path: str, glob: str) -> bool:
    """A path matches a glob; a folder touches every glob beneath it (the W3 review's M2)."""
    if fnmatch.fnmatch(path, glob):
        return True
    # A folder, with its slash or without (the W3 Tester's M6), touches every glob beneath it.
    return glob.startswith(path.rstrip("/") + "/")


def _tier(evidence: str) -> str | None:
    """The tier row 1 records: its first tier word, so "MED, not HIGH" is MED (the W3 Tester's M6)."""
    found = re.search(r"\b(HIGH|MED|LOW)\b", evidence)
    return found.group(1) if found else None


def _glob_problems(p: pathlib.Path, touched: str, evidence: str) -> list[str]:
    """#140: a close whose footprint touches one of its plan's security globs must be HIGH."""
    ids = re.match(r"m(\d+)-wave-\d+-close\.md$", p.name)
    plan = p.parent / f"m{ids.group(1)}-plan.md" if ids else p.parent / "missing-plan.md"
    globs = plan_globs(plan)
    if not globs:
        return [f"`{plan.name}` names no security globs (a `Security globs` bullet with backticked paths), so "
                "no rule can say what makes this wave HIGH; it fails closed (#140)"]
    hits = sorted({f"{path} ({glob})" for path in _footprint_paths(touched) for glob in globs if _touches(path, glob)})
    if hits and _tier(evidence) != "HIGH":
        return [f"the footprint touches its plan's security globs ({', '.join(hits)}) and row 1 does not "
                "record the wave as HIGH -- a diff touching a security glob is HIGH (#140)"]
    return []


#: D-192 (#183, #201, #202, #203): closes dated from this day on are read against their commit range's
#: history and the ledger. A gate does not invalidate a record written before it (GPF-001).
HISTORY_RULES_FROM = "2026-10-10"
#: A commit that changes one of these changes code (#201).
CODE_DIRS = ("src/", "ios/", "scripts/", ".claude/", ".githooks/")


def _git(root: pathlib.Path, *args: str) -> str | None:
    """git's output, or None when the command fails (no repository, an unknown ref)."""
    try:
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60,  # noqa: S603, S607
                              check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _history_absent(root: pathlib.Path) -> str | None:
    """Why there is no history to read here, or None. CI's test job checks out one commit."""
    if _git(root, "rev-parse", "--is-inside-work-tree") != "true":
        return "no git history here"
    if _git(root, "rev-parse", "--is-shallow-repository") == "true":
        return "a shallow clone, as CI's test job checks out one commit"
    return None


def _close_date(text: str) -> str | None:
    dated = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    return dated.group(1) if dated else None


def _row1_evidence(text: str) -> str:
    tier_row = re.search(r"^\|\s*1\s*\|.*$", text, re.M)
    cells = [c.strip() for c in tier_row.group(0).strip().strip("|").split("|")] if tier_row else []
    return cells[2] if len(cells) > 2 else ""


def _merged(root: pathlib.Path, commit: str) -> bool:
    return any(_git(root, "merge-base", "--is-ancestor", commit, ref) is not None for ref in ("origin/main", "main"))


def _wave_base(root: pathlib.Path, ids: re.Match[str] | None, end: str) -> str | None:
    """Where the wave starts: the latest of these that the end's history holds -- the milestone's base on main,
    the merge base with the previous milestone's closure branch (`origin/closure/m<N-1>` or `closure/m<N-1>`,
    the M21 repo review's M2: a milestone stacked on an unmerged closure), and the commit that added the
    previous wave's close. A plan's `**Base:**` line is not read: a docs-only edit must not narrow a range
    (the M21 closure fixes review's M5)."""
    candidates = [next((b for ref in ("origin/main", "main") if (b := _git(root, "merge-base", end, ref))), None)]
    if ids:
        milestone, wave = int(ids.group(1)), int(ids.group(2))
        candidates.append(next((b for ref in (f"origin/closure/m{milestone - 1}", f"closure/m{milestone - 1}")
                                if (b := _git(root, "merge-base", end, ref))), None))
        if wave > 1:
            rel = f"docs/plans/m{milestone}-wave-{wave - 1}-close.md"
            added = (_git(root, "log", "--diff-filter=A", "--format=%H", end, "--", rel) or "").splitlines()
            candidates.append(added[-1] if added else None)
    base = None
    for commit in candidates:
        if not commit or _git(root, "merge-base", "--is-ancestor", commit, end) is None:
            continue
        if base is None or _git(root, "merge-base", "--is-ancestor", base, commit) is not None:
            base = commit
    return base


def _names_wave(heading: str, milestone: str, wave: int) -> bool:
    """Whether a process-log heading names the wave: `M21-W4`, or a span `M21-W1 to W4`."""
    for first, last in re.findall(rf"\bM{milestone}-W(\d+)(?:\s*(?:to|-|\u2013|\u2014|and)\s*W?(\d+))?", heading):
        if int(first) == wave or (last and int(first) <= wave <= int(last)):
            return True
    return False


def history_problems(close: pathlib.Path, text: str, root: pathlib.Path) -> tuple[list[str], str | None]:
    """D-192 clause 2, as the M21-W4 review left it: what a close owes its wave's history.

    The range is read as `git diff A...B` reads it, from the merge base of its two ends, whatever its dots
    (M4), and an end `HEAD` is pinned to the last commit that changes the close, or HEAD while the close
    has edits not yet committed (round 3's M1). It starts at the wave's base or
    before it (`_wave_base`) and holds a commit (M3); a start the history no longer holds is read from the
    merge base the footer records (``merge base `sha` ``), else from the wave's base (M4). Then:
    - #183: every path the range changed, both sides of a rename, is held to the plan's security globs;
    - #201: an ADR the range adds first appears in a commit that changes no code, after no code commit of the
      range that cites it, and after no code commit at all unless the plan named it before;
    - #203: `docs/process-log.md` has a heading naming the wave (`M21-W4`, or a span `M21-W1 to W4`), dated
      inside the range.
    A close whose adding commit is on main is not read again, even after a later branch edits it: the rules
    ran on its branch before the merge (the Tester's M1). A close dated
    before `HISTORY_RULES_FROM` is not read if it was committed before then too (GPF-001).

    Returns (problems, skipped): `skipped` says why the history was not read."""
    ids = re.match(r"m(\d+)-wave-(\d+)-close\.md$", close.name)
    date = _close_date(text)
    absent = _history_absent(root)
    if absent:
        if date is not None and date < HISTORY_RULES_FROM:
            return [], None
        return [], f"the history rules (#183, #201, #203) read nothing: {absent}"
    rel = close.resolve().relative_to(root.resolve()).as_posix() if close.resolve().is_relative_to(
        root.resolve()) else close.name
    added = (_git(root, "log", "--diff-filter=A", "--format=%H %cs", "--", rel) or "").splitlines()
    added_day = added[-1].split()[1] if added else None
    # The range ends at the last commit that changes the close (round 3's M1), or at HEAD while the close
    # has edits not yet committed: work after the close's first commit is the wave's too.
    last_sha = (_git(root, "log", "-1", "--format=%H", "--", rel) or "") or None
    if last_sha and (_git(root, "show", f"{last_sha}:{rel}") or "").strip() != text.strip():
        last_sha = None
    if date is not None and date < HISTORY_RULES_FROM and added_day is not None and added_day < HISTORY_RULES_FROM:
        return [], None
    found = re.search(r"Wave commit range:\s*`([^`]+)`", text)
    if not found:
        return ["the footer names no `Wave commit range` in backticks for git to read; it fails closed (#183)"], None
    spec = found.group(1).strip()
    start, _, typed_end = spec.partition("..." if "..." in spec else "..")
    if typed_end.strip() not in ("", "HEAD"):
        return [f"the commit range `{spec}` must end at HEAD, the commit that adds the close, not at "
                f"`{typed_end.strip()}`: an end the author names can leave the wave's last commits out (#183)"], None
    own = added[-1].split()[0] if added else None  # merged is asked of the commit that added the close (Tester M1)
    if own and _merged(root, own):
        return [], f"`{close.name}` is merged into main: the history rules ran on its branch before the merge (#183)"
    end = last_sha or "HEAD"
    unreadable = [f"the commit range `{spec}` cannot be read in this history; it fails closed (#183)"]
    if _git(root, "rev-parse", "--verify", f"{end}^{{commit}}") is None:
        return unreadable, None
    wave_base = _wave_base(root, ids, end)
    recorded = re.search(r"merge base `([0-9a-f]{7,40})`", text)
    start_sha = (_git(root, "rev-parse", "--verify", f"{start}^{{commit}}")
                 or (recorded and _git(root, "rev-parse", "--verify", f"{recorded.group(1)}^{{commit}}")) or wave_base)
    base = _git(root, "merge-base", start_sha, end) if start_sha else None
    if base is None:
        return unreadable, None
    problems: list[str] = []
    if wave_base and _git(root, "merge-base", "--is-ancestor", base, wave_base) is None:
        problems.append(f"the commit range `{spec}` starts at `{base[:7]}`, after the wave's base `{wave_base[:7]}` "
                        "(the previous wave's close, or the milestone's base on main): a range narrower than the "
                        "wave is refused (#183)")
    if not (_git(root, "rev-list", f"{base}..{end}") or "").split():
        problems.append(f"the commit range `{spec}` holds no commit: an empty range is refused (#183)")
        return problems, None
    changed: set[str] = set()
    for line in (_git(root, "diff", "--name-status", "-M", base, end) or "").splitlines():
        changed.update(line.split("\t")[1:])  # a rename's old path and its new one

    plan_rel = f"docs/plans/m{ids.group(1)}-plan.md" if ids else "docs/plans/missing-plan.md"
    globs = plan_globs(root / plan_rel)
    hits = sorted({f"{path} ({glob})" for path in changed for glob in globs if _touches(path, glob)})
    if hits and _tier(_row1_evidence(text)) != "HIGH":
        problems.append(f"the commit range `{spec}` changes its plan's security globs ({', '.join(hits)}) and row 1 "
                        "does not record the wave as HIGH -- the range's diff is the authority, not the footprint (#183)")

    def adrs(log: str) -> set[str]:
        return set(re.findall(r"^## (D-\d+)\b", log, re.M))

    added_adrs = adrs(_git(root, "show", f"{end}:docs/decisions.md") or "") - adrs(
        _git(root, "show", f"{base}:docs/decisions.md") or "")
    for adr in sorted(added_adrs, key=lambda d: int(d[2:])):
        touching = set()
        for pattern in (f"^## {adr}[^0-9]", f"^## {adr}$"):
            touching |= set((_git(root, "log", "--format=%H", "-G", pattern, f"{base}..{end}", "--",
                                  "docs/decisions.md") or "").split())
        first = [sha for sha in (_git(root, "rev-list", "--reverse", f"{base}..{end}") or "").split() if sha in touching]
        if not first:
            problems.append(f"{adr} is added in the range and no commit in it adds its heading -- the rule cannot "
                            "tell when the decision was written (#201)")
            continue
        files = (_git(root, "show", "--name-only", "--format=", first[0]) or "").splitlines()
        named = bool(re.search(rf"\b{re.escape(adr)}\b", _git(root, "show", f"{first[0]}^:{plan_rel}") or ""))
        earlier = [entry.split("\x1f", 1) for entry in (_git(root, "log", "--format=%h\x1f%B\x1e", f"{base}..{first[0]}^",
                                                                 "--", *CODE_DIRS) or "").split("\x1e") if entry.strip()]
        if any(f.startswith(CODE_DIRS) for f in files) and not named:
            problems.append(f"{adr} first appears in `{first[0][:7]}`, which also changes code, and the plan did not "
                            "name it before -- write the decision before the code it governs (#201)")
        elif earlier and (not named or any(re.search(rf"\b{re.escape(adr)}\b", msg) for _, msg in earlier)):
            problems.append(f"{adr} first appears in `{first[0][:7]}`, after the range's code commit "
                            f"`{earlier[0][0].strip()}` -- write the decision before the code it governs (#201)")

    days = (_git(root, "log", "--format=%cs", f"{base}..{end}") or "").split()
    log_path = root / "docs" / "process-log.md"  # the log as it stands: a stacked wave may add an earlier one's entry
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    low, high = min(days), max(days)
    headings = [(d, d[:8] + tail if tail else d, rest)
                for d, tail, rest in re.findall(r"^## (\d{4}-\d{2}-\d{2})(?:/(\d{2}))?(.*)$", log, re.M)]
    wave_name = f"M{ids.group(1)}-W{ids.group(2)}" if ids else "the wave"
    if not any(first_day <= high and last_day >= low and (not ids or _names_wave(rest, ids.group(1), int(ids.group(2))))
               for first_day, last_day, rest in headings):
        problems.append(f"`docs/process-log.md` has no heading naming {wave_name} dated inside the range ({low} to "
                        f"{high}) -- a session starts from the process log (#203)")
    return problems, None


#: From this date a close carries `Session started in the repository: yes` or `no` (row 8 of the template).
SESSION_FIELD_FROM = "2026-10-11"
SESSION_FIELD = re.compile(r"Session started in the repository:\s*(yes|no)\b", re.I)


def _outside_parentheses(listed: str) -> list[str]:
    entries, depth, current = [], 0, ""
    for ch in listed:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and depth == 0:
            entries.append(current)
            current = ""
        else:
            current += ch
    return [*entries, current]


def _ledger_rows(text: str) -> list[list[str]]:
    """The ledger's rows, read as CSV (a reason may hold commas inside its quotes), without the header and
    the comment lines."""
    import csv

    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")
             and not ln.lower().startswith("control,")]
    return [[c.strip() for c in row] for row in csv.reader(lines) if row]


#: The ledger's kinds (its header names each).
KINDS = ("skip", "bypass", "ruling", "review", "within-scope")
#: How the owner's ruling begins: both real rulings do (the fixes review's round 2, M3).
OWNER_RULING = re.compile(r"the owner, \d{4}-\d{2}-\d{2}\b", re.IGNORECASE)


def _owners_ruling(row: list[str]) -> bool:
    return len(row) >= 5 and row[2].lower() == "ruling" and OWNER_RULING.match(row[3]) is not None


def ledger_strikes(rows: list[list[str]]) -> list[str]:
    """The controls with three or more `skip` or `bypass` rows after their last `ruling` by the owner (the owner's
    ruling of 2026-10-10, as the M21 closure fixes review's round 2, M3 left it): a row counts by its place in
    the file, after that ruling, whatever its date. A `review` or `within-scope` row is recorded and counts
    nothing: it neither strikes nor resets. A new bypass after a ruling still counts."""
    ruled: dict[str, int] = {row[0]: n for n, row in enumerate(rows) if _owners_ruling(row)}
    counts: dict[str, int] = {}
    for n, row in enumerate(rows):
        if len(row) >= 3 and row[2].lower() in ("skip", "bypass") and n > ruled.get(row[0], -1):
            counts[row[0]] = counts.get(row[0], 0) + 1
    return sorted(control for control, n in counts.items() if n >= 3)


def ledger_problems(rows: list[list[str]], today: str | None = None) -> list[str]:
    """The fixes review's M3, as round 2 left it: every row's kind is one of KINDS; its date is ISO (YYYY-MM-DD)
    and at most a day after today's UTC date, so a row the owner dates in UTC+3 passes CI while a future date
    cannot hold later rows back; and a `ruling`'s reason starts `the owner, YYYY-MM-DD`, since only the owner's
    ruling resets a count."""
    import datetime as dt

    latest = (dt.date.fromisoformat(today) if today else dt.datetime.now(dt.UTC).date()) + dt.timedelta(days=1)
    found: list[str] = []
    for row in rows:
        where = f"the ledger row `{','.join(row[:3])}`"
        if len(row) < 3 or row[2].lower() not in KINDS:
            found.append(f"{where} has the kind `{row[2] if len(row) >= 3 else ''}`, not one of {', '.join(KINDS)}")
        date = row[-1] if row else ""
        try:
            iso = re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) is not None and dt.date.fromisoformat(date).isoformat() == date
        except ValueError:
            iso = False
        if not iso:
            found.append(f"{where} is dated `{date}`, not YYYY-MM-DD")
        elif dt.date.fromisoformat(date) > latest:
            found.append(f"{where} is dated {date}, more than a day after today ({latest - dt.timedelta(days=1)}, UTC)")
        if len(row) >= 4 and row[2].lower() == "ruling" and not _owners_ruling(row):
            found.append(f"{where} is a ruling whose reason does not start `the owner, YYYY-MM-DD`; only the owner's "
                         "ruling resets a control's count")
    return found


#: A commit named in a record: 7 to 40 hex digits.
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")


def _gate_target(root: pathlib.Path, sha: str) -> str | None:
    """What scripts/commit_gate.py names for a commit (its paths with --no-renames, its subject; a merge is
    never docs-only or red, round 2's M4), or None when the history cannot show the commit."""
    import importlib.util

    paths = _git(root, "show", "--no-renames", "--name-only", "--format=", sha)
    subject = _git(root, "log", "-1", "--format=%s", sha)
    parents = _git(root, "rev-list", "--parents", "-n", "1", sha)
    if paths is None or subject is None or parents is None:
        return None
    spec = importlib.util.spec_from_file_location("commit_gate", pathlib.Path(__file__).resolve().parent / "commit_gate.py")
    if spec is None or spec.loader is None:
        return None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return str(gate.target([p for p in paths.splitlines() if p], subject, merge=len(parents.split()) > 2))


def _bypassed_commits(said: str, wave_id: str, rows: list[list[str]], root: pathlib.Path | None,
                      notes: list[str] | None) -> list[str]:
    """The fixes review's M4: each commit row 9's Bypass names has a ledger row of the wave or its milestone whose
    reason names it -- a `bypass`, or a `within-scope` only where the commit is docs-only or a declared red test
    commit by commit_gate's own rule. On a full history a SHA no commit holds is a problem (round 2); where
    there is none, or a shallow one, the within-scope row is taken as written, and the note says SKIPPED."""
    found: list[str] = []
    full = root is not None and _history_absent(root) is None
    for sha in dict.fromkeys(SHA.findall(said)):
        if full and root is not None and _git(root, "rev-parse", "-q", "--verify", f"{sha}^{{commit}}") is None:
            found.append(f"row 9's Bypass names {sha}, and no commit in this history is {sha} (round 2's M4)")
            continue
        named = [row for row in rows if len(row) >= 4
                 and any(tok.startswith(sha[:7]) or sha.startswith(tok) for tok in SHA.findall(row[3]))]
        if any(row[2].lower() == "bypass" for row in named):
            continue
        if any(row[2].lower() == "within-scope" for row in named):
            gated = _gate_target(root, sha) if full and root is not None else None
            if gated is None:
                if notes is not None:
                    notes.append(f"row 9's Bypass names {sha}, whose within-scope row this history cannot confirm")
                continue
            if gated in ("check-docs", "check-red"):
                continue
            found.append(f"row 9's Bypass names {sha}, a commit commit_gate gates with {gated}: its row cannot be "
                         "within-scope; it is a bypass (the fixes review's M4)")
            continue
        found.append(f"row 9's Bypass names {sha}, and `docs/control-events.csv` has no row for {wave_id} or its "
                     "milestone whose reason names it (the fixes review's M4)")
    return found


def skip_ledger_problems(text: str, wave_id: str, ledger: list[list[str]], root: pathlib.Path | None = None,
                         notes: list[str] | None = None) -> list[str]:
    """D-192 clause 3 (#202), as the M21-W4 review left it: each gate row 9 lists as skipped (the label in
    any case, its list split on commas outside parentheses), each checklist row whose status says SKIPPED or
    WAIVED, and a close whose field says `Session started in the repository: no`, has a
    `docs/control-events.csv` row for the wave or its milestone. Prose about the session is not read; from
    `SESSION_FIELD_FROM` the field is required."""
    date = _close_date(text)
    if date is not None and date < HISTORY_RULES_FROM:
        return []
    owners = {wave_id, wave_id.split("-")[0]}
    rows = [row for row in ledger if len(row) >= 2 and row[1].strip() in owners]

    def ledgered(control: str) -> bool:
        return any(row[0].strip().lower() == control for row in rows)

    problems: list[str] = []
    listed = re.search(r"gates\s*\**\s*SKIPPED\s*\**\s*[:\u2014\u2013-]\s*(.*?)(?:\s·\s|`|$)", text, re.M | re.I)
    for entry in (_outside_parentheses(listed.group(1)) if listed else []):
        name = re.sub(r"^make\s+", "", entry.split("(")[0].strip().lower())
        name = re.sub(r"\s+", "-", name).strip(".-")
        if name and name != "none" and not ledgered(name):
            problems.append(f"row 9 lists `{entry.strip()}` as skipped and `docs/control-events.csv` has no `{name}` "
                            f"row for {wave_id} or its milestone -- a skip the ledger does not count becomes "
                            "permanent (#202)")
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) >= 4 and re.match(r"\d+[a-z]?$", cells[0]) and re.search(r"\b(SKIPPED|WAIVED)\b|\bN/A\b",
                                                                              cells[-1], re.I):
            said = cells[1]  # the check cell: the control a row skipped is the one it names (round 3's M2)
            if not any(re.search(r"(?<![\w-])" + r"[-\s]+".join(map(re.escape, row[0].strip().split("-"))) + r"(?![\w-])",
                                 said, re.I) for row in rows):
                problems.append(f"row {cells[0]} ({cells[1][:60]}) is marked `{cells[-1]}` and `docs/control-events.csv` "
                                f"has no row for {wave_id} or its milestone naming the control it skipped (#202)")
    row8 = next((cells for line in text.splitlines() if line.startswith("|")
                 for cells in [[c.strip() for c in line.strip().strip("|").split("|")]] if cells and cells[0] == "8"), None)
    answers = SESSION_FIELD.findall(row8[2]) if row8 and len(row8) > 2 else []
    if len({a.lower() for a in answers}) > 1:
        problems.append("row 8's evidence says both `Session started in the repository: yes` and `no` (#202)")
    field = SESSION_FIELD.search(row8[2]) if row8 and len(row8) > 2 else None
    bypass = re.search(r"Bypass:\s*(.*?)(?:\s\|\s|$)", text, re.M)
    said = bypass.group(1).strip().strip("`. ") if bypass else ""
    if said and not said.lower().startswith("none") and not any(
            re.search(r"(?<![\w-])" + re.escape(row[0].strip()) + r"(?![\w-])", said, re.I) for row in rows):
        problems.append(f"row 9's `Bypass: {said[:60]}` names no control `docs/control-events.csv` has a row for, for "
                        f"{wave_id} or its milestone -- a bypass the ledger does not count is invisible to the "
                        "three-row rule (#202, the M21 repo review's M1)")
    if said and not said.lower().startswith("none"):
        # Round 2's M4: each control of the ledger the field names needs a row of its own for the wave.
        for control in dict.fromkeys(row[0].strip().lower() for row in ledger if row and row[0].strip()):
            if re.search(r"(?<![\w-])" + re.escape(control) + r"(?![\w-])", said, re.I) and not ledgered(control):
                problems.append(f"row 9's `Bypass:` names `{control}`, and `docs/control-events.csv` has no `{control}` "
                                f"row for {wave_id} or its milestone (round 2's M4)")
        problems += _bypassed_commits(said, wave_id, rows, root, notes)
    if field and field.group(1).lower() == "no" and not ledgered("repository-hooks"):
        problems.append(f"the close says `Session started in the repository: no`, and `docs/control-events.csv` "
                        f"has no `repository-hooks` row for {wave_id} or its milestone (#202, #142)")
    if not field and date is not None and date >= SESSION_FIELD_FROM:
        problems.append("the close does not say `Session started in the repository: yes` or `no` (row 8, #202)")
    return problems


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
    # model_ranking (D-155 adoption review MINOR-1, D-161; v6.6 upgrade review MAJOR-1/2): the
    # hole the paragraph above names is closed by REFUSING it, not by regrading. A close with no
    # date, or dated after the day this project reached DevFlow v6.6, must declare v6.6 or later;
    # it is then graded by the version it declares, so a DevFlow release adding a field later does
    # not turn it red. A close dated on or before that day keeps what it declares (GPF-001).
    dated = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    if (vm is not None and version is not None and version < CURRENT_AT_ADOPTION
            and (dated is None or dated.group(1) > DEVFLOW_ADOPTED)):
        bad.append(f"declares process_version {vm.group(1)} but is "
                   f"{'undated' if dated is None else 'dated ' + dated.group(1)}: a close written "
                   f"after {DEVFLOW_ADOPTED} declares v{'.'.join(map(str, CURRENT_AT_ADOPTION))} or "
                   "later -- an older stamp would skip the rules written since (D-161)")

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
    # #83: the template escalates to HIGH a wave whose diff touches input parsing, and M17-W2 and W3
    # were not. From the day this check exists, a close whose footprint names `src/app/clients/`
    # must carry HIGH on its risk-tier row (row 1).
    # An undated close is held to it too, and the footprint is read up to the next footprint field
    # or the end of its block, in whatever order the fields come (W5 review M4).
    if dated is None or dated.group(1) >= INPUT_PARSING_HIGH_FROM:
        touched = re.search(r"^\s*Touched:(.*?)(?=^\s*(?:Mutant set author|Observed RED|Owner instruction|"
                            r"K\.8 contracts|Stopped at three attempts|Hand-kept lists):|^```|\Z)",
                            text, re.M | re.S)
        tier_row = re.search(r"^\|\s*1\s*\|.*$", text, re.M)
        # The EVIDENCE cell: the check column of the template itself says "LOW/MED/HIGH; auto-HIGH"
        # (W5 second review M10).
        cells = [c.strip() for c in tier_row.group(0).strip().strip("|").split("|")] if tier_row else []
        evidence = cells[2] if len(cells) > 2 else ""
        if (touched and re.search(r"src/app/clients\b", touched.group(1))
                and not re.search(r"\bHIGH\b", evidence)):
            bad.append("the footprint touches `src/app/clients` (input parsing) and row 1 does not "
                       "record the wave as HIGH -- a diff touching input parsing is HIGH (#83)")
        if dated is None or dated.group(1) >= PLAN_GLOBS_HIGH_FROM:
            bad += _glob_problems(p, touched.group(1) if touched else "", evidence)
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

    # D-192 clauses 2 and 3 (#183, #201, #202, #203): the commit range's history and the ledger.
    if milestone_match and p.resolve().relative_to(root).parts[:1] != ("conformance",):
        history, skipped = history_problems(p, text, root)
        bad.extend(history)
        if skipped:
            print(f"SKIPPED [wave-check]: {skipped}")
        ledger_rows = (_ledger_rows(LEDGER.read_text(encoding="utf-8", errors="replace"))
                       if LEDGER.is_file() else [])
        wave_ids = re.match(r"m(\d+)-wave-(\d+)", p.name)
        if wave_ids:
            notes: list[str] = []
            bad.extend(skip_ledger_problems(text, f"m{wave_ids.group(1)}-w{wave_ids.group(2)}", ledger_rows,
                                            root=root, notes=notes))
            for note in notes:
                print(f"SKIPPED [wave-check]: {note}")

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
        ledger_list = _ledger_rows(LEDGER.read_text(encoding="utf-8", errors="replace"))
        ledger_waves = {row[1] for row in ledger_list if len(row) >= 2}
        bad.extend(ledger_problems(ledger_list))
        for control in ledger_strikes(ledger_list):
            bad.append(f"`{control}` has three or more skip/bypass events in {LEDGER} since its last ruling "
                       "or review -- three is the review threshold. The CONTROL goes under review before this "
                       "wave closes: fix it, re-scope it, or refuse it in docs/refusals.md, and record the "
                       "ruling as a `ruling` row. Do not record a fourth")
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
