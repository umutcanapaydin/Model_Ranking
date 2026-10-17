#!/usr/bin/env python3
"""Is this file a filled, consistent record of an unattended run?

A run (`/plan-run`, from `v7.1`) is the lane where the owner plans two to five milestones, answers
every open question once, and the agent works every wave of every milestone on one integration
branch without waiting for a merge -- stopping only for AGENTS.md §3's Escalate-NOW events and a
question the assumption ledger may not take. Its one record is `docs/plans/run-<name>.md`, copied
from `docs/run.template.md`; the next session resumes from it, and the owner reads it in the
morning. A record nobody grades drifts from the branch, so this grades it, and `make closes` runs
it on every run file in the tree.

Refuses:
  * a filename that is not `run-<name>.md`
  * `Mode:` not `heavy` or `light`; `Started:` not a date; `Ended:` neither `open` nor a dated
    reason (`all milestones closed`, `owner stopped`, `stopped at <class>, nothing independent left`)
  * `Rulings:` naming an ADR that `docs/decisions.md` does not hold -- the owner's answers are
    ADRs, not chat; a decisions file that cannot be read fails closed
  * a milestone or wave status outside its vocabulary, or a cell still a template placeholder
  * heavy mode: a milestone row whose plan file is missing; a `stacked` wave whose close record is
    missing (the close record is what `make wave-check` grades -- a stacked wave with none was
    never closed); a `closed` milestone with a wave still queued, running or stopped
  * a `stopped` wave with no row in Stops; a Stops row whose class is not one of the named
    events, or that says nothing about what the owner decides
  * an ended run with a wave still `running`; a run ended `stopped at` with no Stops row
Exit 0 pass · 1 fail · 2 usage.
"""
from __future__ import annotations

import pathlib
import re
import sys

NAME_RE = re.compile(r"^run-[a-z0-9][a-z0-9-]*\.md$")
DATE = r"\d{4}-\d{2}-\d{2}"
PLACEHOLDER = re.compile(r"<[A-Za-z][A-Za-z0-9 _/|-]{0,}>|\bTBD\b|\bTODO\b")
MILESTONE_STATUS = {"queued", "running", "closed", "stopped"}
WAVE_STATUS = {"queued", "running", "stacked", "stopped"}
WAVE_SHAPE = re.compile(r"^(m\d+-w\d+|issue-\d+)$")
MILESTONE_SHAPE = re.compile(r"^(M\d+|queue)$")
# The Escalate-NOW events of AGENTS.md §3, one name each, plus the two stops a run adds. A named
# list with its reason (AGENTS.md §3.5): the events are prose in AGENTS.md, and a run's stop must
# name which one it was, in a word a table can hold and a reader can count.
STOP_CLASSES = {
    "secret": "suspected secret",
    "scanner-suppression": "a scanner finding suppressed or waived",
    "blocking-high": "BLOCKING at HIGH, test-integrity included",
    "silent-fault": "a fault that stays green with no test",
    "control-change": "a CI, hook or gate-definition change",
    "dependency": "a critical-CVE or slopsquat dependency",
    "security-test": "a security-invariant test modified or deleted",
    "zone-or-criterion": "a ⛔-zone question or the meaning of an acceptance criterion",
    "scope-change": "a plan-invalidating scope change",
    "not-assumable": "a decision the owner reserved (a work-issue verdict's flagged decision, an approval "
                     "a skill asks for) that the run's decisions message did not cover",
    "environment": "a gate leg or tool that cannot run here (the network legs, a missing tool)",
    "owner": "the owner stopped the run",
}
SHA = re.compile(r"^[0-9a-f]{7,40}$")
ENDED_RE = re.compile(rf"^{DATE}\s+[—-]+\s+(all milestones closed|owner stopped|stopped at ([a-z-]+), nothing independent left)\s*$")
DECISIONS = pathlib.Path("docs/decisions.md")


def field(text: str, name: str) -> str | None:
    m = re.search(rf"^{re.escape(name)}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else None


def table(text: str, heading: str) -> list[tuple[int, list[str]]]:
    """The rows of the table under `## <heading>`: (line number, cells), header and rule excluded."""
    rows: list[tuple[int, list[str]]] = []
    in_section = in_table = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            in_section = line[3:].strip().lower().startswith(heading.lower())
            in_table = False
            continue
        if not in_section:
            continue
        s = line.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not in_table:
            in_table = True            # the header row
            continue
        if set("".join(cells)) <= set("-: "):
            continue                   # the rule row
        rows.append((n, cells))
    return rows


def decisions_held(root: pathlib.Path = pathlib.Path(".")) -> dict[str, str] | None:
    """ADR id -> its section's text, from docs/decisions.md; None when the file is missing."""
    p = root / DECISIONS
    if not p.is_file():
        return None
    held: dict[str, str] = {}
    current: str | None = None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^##\s+((?:D|P)-\d+)\b", line)
        if m:
            current = m.group(1)
            held[current] = ""
        elif current:
            held[current] += line + "\n"
    return held


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    if len(argv) != 2:
        print("usage: run_check.py docs/plans/run-<name>.md")
        return 2
    p = pathlib.Path(argv[1])
    if not p.is_file():
        print(f"FAIL [run-check]: {p} is not a file")
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    bad: list[str] = []

    if not NAME_RE.match(p.name):
        bad.append(f"`{p.name}` is not a run record filename -- expected `run-<name>.md` "
                   "(docs/run.template.md)")
    mode = (field(text, "Mode") or "").strip("`")
    if mode not in ("heavy", "light"):
        bad.append(f"`Mode:` is `{mode or 'missing'}` -- write `heavy` or `light`, the brief's working mode")
    started = field(text, "Started") or ""
    if not re.fullmatch(DATE, started):
        bad.append(f"`Started:` is `{started or 'missing'}` -- a date, YYYY-MM-DD")
    ended = field(text, "Ended") or ""
    ended_m = ENDED_RE.match(ended)
    if ended != "open" and not ended_m:
        bad.append(f"`Ended:` is `{ended[:50] or 'missing'}` -- `open` while the run runs, else "
                   "`<date> — all milestones closed`, `<date> — owner stopped` or "
                   "`<date> — stopped at <class>, nothing independent left`")
    if ended_m and ended_m.group(2) and ended_m.group(2) not in STOP_CLASSES:
        bad.append(f"`Ended:` stops at `{ended_m.group(2)}`, which is not a stop class "
                   f"({', '.join(sorted(STOP_CLASSES))})")
    rulings = field(text, "Rulings") or ""
    if not rulings:
        bad.append("no `Rulings:` line -- the ADRs the owner's answers became, or `none`")
    elif rulings.strip("`") != "none":
        ids = re.findall(r"\b(?:D|P)-\d+\b", rulings)
        if not ids:
            bad.append(f"`Rulings:` is `{rulings[:40]}` -- ADR ids (`D-<n>`, `P-<n>`) or `none`")
        held = decisions_held()
        if held is None:
            bad.append(f"cannot read {DECISIONS}, so no ruling can be checked -- a run whose rulings "
                       "nobody can find has no rulings (fail closed)")
        else:
            for i in ids:
                if i not in held:
                    bad.append(f"ruling `{i}` is not in {DECISIONS} -- an answer in chat is not a "
                               "ruling until `/log-decision` writes it")
                elif "owner ruling" not in held[i].lower():
                    bad.append(f"ruling `{i}` carries no `**Owner ruling:**` line -- the ADR must say it "
                               "is the owner's answer to this run's decisions message (/log-decision)")
    in_stops = False      # a stop's question may quote `<script>`; the Stops table is not scanned
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            in_stops = line[3:].strip().lower().startswith("stops")
        owned = (line.lstrip().startswith("|") and not in_stops) or re.match(
            r"^(Mode|Started|Ended|Integration branch|Plan PR|Rulings):", line)
        if owned and PLACEHOLDER.search(line):
            bad.append(f"line {n}: a template placeholder is still in a line the run owns: "
                       f"`{line.strip()[:60]}`")
            break

    milestones = table(text, "Milestones")
    waves = table(text, "Waves")
    stops = table(text, "Stops")
    if not milestones:
        bad.append("no milestone rows -- a run with nothing to run is not a run")
    wave_status: dict[str, str] = {}
    for n, cells in waves:
        if len(cells) < 5:
            bad.append(f"line {n}: a wave row needs 5 cells: Wave | Branch | PR | Close record | Status")
            continue
        wave, close, status = cells[0].strip("`"), cells[3].strip("`"), cells[4].lower()
        if not WAVE_SHAPE.match(wave):
            bad.append(f"line {n}: wave `{wave}` is not `m<N>-w<W>` or `issue-<n>`")
        if status not in WAVE_STATUS:
            bad.append(f"line {n}: wave `{wave}` status `{cells[4]}` is not one of {sorted(WAVE_STATUS)}")
        wave_status[wave] = status
        # An unreadable mode gets the heavier rules: a run that cannot say its mode is not light.
        if mode != "light" and status == "stacked":
            if close == "none" or not pathlib.Path(close).is_file():
                bad.append(f"line {n}: wave `{wave}` is stacked and its close record `{close}` does "
                           "not exist -- a wave is stacked only after `/close-wave` wrote and "
                           "committed its checklist (`make wave-check`)")
    for n, cells in milestones:
        if len(cells) < 5:
            bad.append(f"line {n}: a milestone row needs 5 cells: # | Milestone | Base | Plan | Status")
            continue
        ms, base, plan, status = cells[1].strip("`"), cells[2].strip("`"), cells[3].strip("`"), cells[4].lower()
        if base != "none" and not SHA.match(base):
            bad.append(f"line {n}: milestone `{ms}` base `{base[:20]}` is neither `none` nor a sha")
        if status in ("running", "closed", "stopped") and base == "none":
            bad.append(f"line {n}: milestone `{ms}` is {status} and names no `Base` sha -- the integration "
                       "head its first wave was cut from is what the Tester and the cross-wave review range from")
        if not MILESTONE_SHAPE.match(ms):
            bad.append(f"line {n}: milestone `{ms}` is not `M<N>` (heavy) or `queue` (light)")
        if status not in MILESTONE_STATUS:
            bad.append(f"line {n}: milestone `{ms}` status `{cells[4]}` is not one of {sorted(MILESTONE_STATUS)}")
        if mode != "light" and not pathlib.Path(plan).is_file():
            bad.append(f"line {n}: milestone `{ms}` names plan `{plan}`, which does not exist -- "
                       "`/plan-run` writes one plan per milestone before the run starts")
        # Light: every wave row (issue-<n>) belongs to the one `queue` milestone.
        mine = (lambda w: True) if mode == "light" else (lambda w, p=ms.lower() + "-w": w.startswith(p))
        if status == "closed":
            open_waves = [w for w, s in wave_status.items() if mine(w) and s != "stacked"]
            if open_waves:
                bad.append(f"line {n}: milestone `{ms}` is closed while its wave(s) "
                           f"{', '.join(open_waves)} are not stacked")
            if not any(mine(w) for w in wave_status):
                bad.append(f"line {n}: milestone `{ms}` is closed and no wave row belongs to it")
        if status == "running" and ended != "open":
            bad.append(f"line {n}: the run has ended and milestone `{ms}` is still running -- close it, "
                       "or mark it stopped")
    stopped_waves = {w for w, s in wave_status.items() if s == "stopped"}
    stop_waves: set[str] = set()
    for n, cells in stops:
        if len(cells) < 5:
            bad.append(f"line {n}: a stop row needs 5 cells: When | Wave | Class | What the owner decides | Continued on")
            continue
        wave, cls, question = cells[1].strip("`"), cells[2].strip("`").lower(), cells[3]
        stop_waves.add(wave)
        if cls not in STOP_CLASSES:
            bad.append(f"line {n}: stop class `{cls}` is not one of {sorted(STOP_CLASSES)} -- a stop "
                       "names the Escalate-NOW event it was, or `not-assumable`, or `owner`")
        if len(question.strip()) < 10:
            bad.append(f"line {n}: the stop on `{wave}` says nothing about what the owner decides -- "
                       "the question, in a sentence, is what the owner reads in the morning")
    for w in sorted(stopped_waves - stop_waves):
        bad.append(f"wave `{w}` is stopped and Stops has no row for it -- a stop nobody wrote down "
                   "is a wave that silently died")
    if ended != "open":
        running = [w for w, s in wave_status.items() if s == "running"]
        if running:
            bad.append(f"the run has ended and wave(s) {', '.join(running)} are still running -- "
                       "stack them or mark them stopped")
        if ended_m and ended_m.group(2) and not stops:
            bad.append("the run ended `stopped at` and Stops is empty -- the stop that ended it is "
                       "a row the owner reads")

    for b in bad:
        print(f"FAIL [run-check]: {b}")
    if bad:
        return 1
    n_stacked = sum(1 for s in wave_status.values() if s == "stacked")
    print(f"run-check PASS: {p} ({mode}; {len(milestones)} milestone(s), {len(waves)} wave(s), "
          f"{n_stacked} stacked, {len(stops)} stop(s); {ended})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
