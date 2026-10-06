#!/usr/bin/env python3
"""Run the wave-record validator over every record it can fairly be applied to (W-032).

**The problem this solves is not "run a loop".** `make check` did not include the wave-record
validator at all, so it never ran: one milestone's four records failed on the same three lines and
nobody knew until someone invoked the tool by hand at closure. A gate outside the command people
type is not a gate.

**The problem it must NOT create** is the one this project already filed against the pipeline as
GPF-001: a tool added later retroactively invalidating records written before it existed. Twenty
wave records predate the v5.0 migration and fail a template that did not exist when they were
written. Records are append-only; rewriting twenty of them to satisfy a tool would be rewriting
history to match the tool, which is the exact remedy GPF-001 argues against.

**So scope is declared, not assumed.** A record is in scope when it declares `process_version: v5.0`
— the stamp that says which process produced it. Anything older is reported as out of scope with a
count, never silently dropped.

That leaves one hole, and it is closed here: a record could dodge the gate by simply omitting the
stamp. So a record dated on or after the migration MUST declare it. Omission is a failure, not an
exemption.

Exit: 0 all in-scope records pass · 1 a record failed or dodged the stamp · 2 nothing to check
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import re
import sys

#: D-113 — the day this project migrated to v5.0.
#:
#: The anti-dodge rule below compares STRICTLY AFTER this date, not on-or-after, and the reason is
#: a real ambiguity rather than a convenience: the migration happened mid-day, so records dated
#: 2026-08-16 exist on BOTH sides of it — a milestone closed under v4.3.1 that morning and the
#: migration landed after. A date alone cannot separate them, and guessing would either exempt
#: records that should be gated or fail records for not carrying a stamp that did not yet exist.
#:
#: The hole this leaves is exactly one day wide and it closes by itself: no future record can be
#: dated 2026-08-16. Every record written since carries the stamp.
MIGRATION_DATE = "2026-08-16"

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATTERN = "docs/plans/m*-wave-*-close.md"


def _front(text: str, field: str) -> str | None:
    # `[ \t]*`, never `\s*`: `\s` crosses the newline, and an empty `date:` read the next line
    # (`---`) as its value (#17 Tester M2). A quoted value is the value (M3).
    match = re.search(rf"^{field}:[ \t]*['\"]?([^\s'\"]+)['\"]?[ \t]*$", text, re.MULTILINE)
    return match.group(1) if match else None


#: #82: the first milestone whose planned waves must each have a close record (GPF-001: a control
#: does not grade what was written before it existed; M17-W1's missing close is in its report).
EXPECTED_CLOSES_FROM = 18
#: `### W1 — ...`, `## Wave 1 — ...` and `### M19-W1 — ...` (W5 review M3: a shape it did not read
#: counted no waves, and so found none missing).
WAVE_HEADING = re.compile(r"^#{2,4}\s*(?:M\d+-)?W(?:ave\s*)?(\d+)\b(.*)$", re.M)
#: What looks like a wave heading at all; one this reads and `WAVE_HEADING` does not is reported
#: rather than skipped (W5 second review M9).
LOOKS_LIKE_A_WAVE = re.compile(r"^#{2,6}\s*[*_]*\s*(?:M\d+-)?(?:W\d|Wave\b).*$", re.M)
#: The plan marks a wave dropped with `(dropped` in its heading, not any use of the word.
DROPPED = re.compile(r"\(dropped\b", re.I)


def _excused_waves(ledger: pathlib.Path) -> set[str]:
    """The waves the ledger records as closed without a record (`wave-close,m18-w2,...`)."""
    if not ledger.is_file():
        return set()
    rows = (line.split(",") for line in ledger.read_text(encoding="utf-8").splitlines())
    return {cells[1].strip().lower() for cells in rows if len(cells) >= 2 and cells[0].strip() == "wave-close"}


def missing_closes(root: pathlib.Path) -> list[str]:
    """Each wave a CLOSED milestone's plan names that has no close record, is not marked dropped in
    the plan, and has no `wave-close` row in `docs/control-events.csv` (#82). A milestone is closed
    when its closure report exists; an open one still has waves in flight."""
    excused = _excused_waves(root / "docs" / "control-events.csv")
    missing: list[str] = []
    for report in sorted((root / "docs").glob("closure-report-m*.md")):
        found = re.fullmatch(r"closure-report-m(\d+)\.md", report.name)
        if found is None or int(found.group(1)) < EXPECTED_CLOSES_FROM:
            continue
        milestone = int(found.group(1))
        plan = root / "docs" / "plans" / f"m{milestone}-plan.md"
        if not plan.is_file():
            missing.append(f"m{milestone} closed with no plan at {plan.relative_to(root)}; its waves cannot be counted")
            continue
        text = plan.read_text(encoding="utf-8")
        waves = WAVE_HEADING.findall(text)
        if not waves:
            missing.append(f"m{milestone} closed and its plan names no wave this check can read; it "
                           "fails closed rather than finding nothing missing")
        missing += [f"m{milestone}'s plan has a wave heading this check cannot read: `{line.strip()}`"
                    for line in LOOKS_LIKE_A_WAVE.findall(text) if not WAVE_HEADING.match(line)]
        for wave, rest in waves:
            if DROPPED.search(rest) or f"m{milestone}-w{wave}" in excused:
                continue
            if not (root / "docs" / "plans" / f"m{milestone}-wave-{wave}-close.md").is_file():
                missing.append(f"m{milestone} W{wave} is in the plan and has no close record "
                               f"(docs/plans/m{milestone}-wave-{wave}-close.md); close it, mark it "
                               "dropped in the plan, or record a `wave-close` row in the ledger")
    return missing


#: #140: a wave a plan names outside a heading: `W3`, `Wave 3`, or `M19-W3` in M19's own plan.
#: Another milestone's wave and `W-108`, a warning's id, do not count.
NAMED_WAVE = re.compile(r"(?<![\w-])(?:M(\d+)-)?W(?:ave\s*)?(\d+)\b")


def headless_waves(root: pathlib.Path) -> list[str]:
    """#140: each wave a plan names in an amendment paragraph or a table's first column with no
    heading of its own. `missing_closes` counts waves by their headings, so one added by an
    amendment alone (as M18-W7 was) would have no close required of it. Every plan from M18 on,
    open or closed, so it is found while the milestone runs."""
    problems: list[str] = []
    for plan in sorted((root / "docs" / "plans").glob("m*-plan.md")):
        found = re.fullmatch(r"m(\d+)-plan\.md", plan.name)
        if found is None or int(found.group(1)) < EXPECTED_CLOSES_FROM:
            continue
        text = plan.read_text(encoding="utf-8")
        headed = {int(wave) for wave, _ in WAVE_HEADING.findall(text)}
        named: dict[int, str] = {}
        for paragraph in re.split(r"\n\s*\n", text):
            # Bold or not (the W3 review's M3); `M19-W3` counts for M19's plan only.
            if re.match(r"^\s*\**\s*Amendment\b", paragraph):
                for milestone, wave in NAMED_WAVE.findall(paragraph):
                    if not milestone or milestone == found.group(1):
                        named.setdefault(int(wave), "an amendment")
        for row in re.findall(r"^\|\s*W(\d+)\s*\|", text, re.M):
            named.setdefault(int(row), "a table")
        problems += [f"m{found.group(1)}'s plan names W{wave} in {where} and gives it no heading, so no "
                     f"close can be required of it; add `### W{wave} — ...` (#140)"
                     for wave, where in sorted(named.items()) if wave not in headed]
    return problems


def _load_wave_check():
    """Import the sibling validator by path; `scripts/` is not a package."""
    spec = importlib.util.spec_from_file_location("wave_check", ROOT / "scripts/wave_check.py")
    if spec is None or spec.loader is None:  # pragma: no cover - a missing sibling is a broken tree
        msg = "scripts/wave_check.py is missing; the wave-record validator cannot run"
        raise SystemExit(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    records = sorted(ROOT.glob(PATTERN))
    if not records:
        print(f"wave-check-all: no records match {PATTERN}")
        return 2

    in_scope: list[pathlib.Path] = []
    legacy: list[pathlib.Path] = []
    dodged: list[str] = []

    for record in records:
        text = record.read_text(encoding="utf-8")
        version = _front(text, "process_version")
        date = _front(text, "date") or ""
        # v5.0 and every later version (DevFlow v6.x, D-155, D-161) are in scope; derived, not
        # listed, so a new DevFlow version is graded the day its template stamps it.
        vm = re.fullmatch(r"v?(\d+)\.(\d+)(?:\.\d+)*", version or "")
        if vm and (int(vm.group(1)), int(vm.group(2))) >= (5, 0):
            in_scope.append(record)
        elif not date or date > MIGRATION_DATE:
            # #17: a record with no date cannot be assumed written before the migration.
            dodged.append(
                f"{record.relative_to(ROOT)} is "
                f"{'undated' if not date else 'dated ' + date + ', after the v5.0 migration,'} and "
                f"declares process_version={version!r}; the stamp is what puts a record in scope, "
                "so omitting it removes the record from the gate"
            )
        else:
            legacy.append(record)

    # Called IN-PROCESS rather than shelled out. The security lint rule on `subprocess` is right
    # here for a reason beyond itself: spawning an interpreter per record made this script's own
    # behaviour depend on which interpreter was on PATH, which is the same class of "the thing you
    # measured is not the thing that runs" this project keeps finding elsewhere.
    check = _load_wave_check()

    failed: list[str] = []
    for record in in_scope:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            code = check.main(["wave_check.py", str(record)])
        if code != 0:
            failed.append(f"{record.relative_to(ROOT)}\n{captured.getvalue()}".rstrip())

    unclosed = [*missing_closes(ROOT), *headless_waves(ROOT)]
    for message in failed:
        print(message)
    for message in [*dodged, *unclosed]:
        print(f"wave-check-all: {message}")

    if failed or dodged or unclosed:
        print(
            f"wave-check-all FAIL: {len(failed)} record(s) failed, {len(dodged)} without the stamp, "
            f"{len(unclosed)} planned wave(s) with no close or no heading"
        )
        return 1

    print(
        f"wave-check-all PASS: {len(in_scope)} v5.0-or-later record(s) validated; "
        f"{len(legacy)} pre-migration record(s) out of scope (GPF-001 — a tool may not retroactively "
        "invalidate records written before it existed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
