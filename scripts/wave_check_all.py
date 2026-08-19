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
    match = re.search(rf"^{field}:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


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
        if version == "v5.0":
            in_scope.append(record)
        elif date > MIGRATION_DATE:
            dodged.append(
                f"{record.relative_to(ROOT)} is dated {date}, after the v5.0 migration, and "
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

    for message in failed:
        print(message)
    for message in dodged:
        print(f"wave-check-all: {message}")

    if failed or dodged:
        print(
            f"wave-check-all FAIL: {len(failed)} record(s) failed, {len(dodged)} without the stamp"
        )
        return 1

    print(
        f"wave-check-all PASS: {len(in_scope)} v5.0 record(s) validated; "
        f"{len(legacy)} pre-migration record(s) out of scope (GPF-001 — a tool may not retroactively "
        "invalidate records written before it existed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
