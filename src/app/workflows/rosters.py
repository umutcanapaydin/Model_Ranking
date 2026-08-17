"""Provider model rosters: the second documented source for plan→model links (REQ-ING-009).

A plan page that names no model cannot rank, and guessing is forbidden (M1 rule 4).
Some providers publish the list elsewhere — a help-centre article, a plan detail
page. That list is a SEPARATE source: its own URL, its own verification clock,
its own provenance on every link it creates.

Curated-data discipline is identical to `plans.py` (D-107): authored input FAILS
LOUD on any invalid row, the working set is replaced atomically, and a roster
name links to a model only through the registry — unmatched names DROP and are
counted, never guessed.
"""

from __future__ import annotations

import datetime as dt
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

import yaml

from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, SourceReport
from app.workflows.yaml_guard import safe_load_bounded

SOURCE_NAME = "rosters-curated"
LINK_SOURCE = "roster"
SCHEMA_VERSION = 1
PLAN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")


def _fail(msg: str) -> SourceError:
    return SourceError(f"{SOURCE_NAME}: {msg}")


@dataclass(frozen=True)
class RosterRow:
    """One provider roster attached to exactly one plan."""

    plan_id: str
    provider: str
    source_url: str
    last_verified: str
    scope: str  # WHICH section of the page this roster transcribes (review MINOR-1)
    models: tuple[str, ...]


@dataclass(frozen=True)
class RostersDoc:
    staleness_days: int
    rows: tuple[RosterRow, ...]


def _validate(entry: Any, seen: set[str]) -> RosterRow:  # noqa: C901
    # (complexity waiver, same as plans.py: one loud gate per field is the design)
    if not isinstance(entry, dict):
        raise _fail(f"roster entry is not a mapping: {entry!r}")
    plan_id = entry.get("plan_id")
    if not isinstance(plan_id, str) or not PLAN_ID_RE.match(plan_id):
        raise _fail(f"invalid plan_id {plan_id!r} (want kebab-case, >=3 chars)")
    if plan_id in seen:
        raise _fail(f"duplicate roster for plan {plan_id!r} — one roster per plan")
    raw_verified = entry.get("last_verified")
    verified = raw_verified.isoformat() if isinstance(raw_verified, dt.date) else raw_verified
    fields = {**entry, "last_verified": verified}
    for key in ("provider", "source_url", "last_verified", "scope"):
        val = fields.get(key)
        if not isinstance(val, str) or not val.strip():
            raise _fail(f"{plan_id}: field {key!r} missing or empty")
    if not str(fields["source_url"]).startswith("https://"):
        raise _fail(f"{plan_id}: source_url must be https, got {fields['source_url']!r}")
    try:
        dt.date.fromisoformat(fields["last_verified"])
    except ValueError as exc:
        raise _fail(f"{plan_id}: last_verified is not YYYY-MM-DD") from exc
    models = fields.get("models")
    if not isinstance(models, list) or not models:
        raise _fail(
            f"{plan_id}: 'models' must be a non-empty list — an empty roster is not a roster"
        )
    if any(not isinstance(m, str) or not m.strip() for m in models):
        raise _fail(f"{plan_id}: every roster model must be a non-empty string")
    if len(set(models)) != len(models):
        raise _fail(f"{plan_id}: duplicate name in models")
    return RosterRow(
        plan_id=plan_id,
        provider=fields["provider"].strip(),
        source_url=fields["source_url"].strip(),
        last_verified=fields["last_verified"].strip(),
        scope=fields["scope"].strip(),
        models=tuple(m.strip() for m in models),
    )


def parse_rosters(raw: str) -> RostersDoc:
    """Parse + validate the curated roster file; ANY invalid row aborts loudly."""
    try:
        doc = safe_load_bounded(raw, what="the curated roster table (data/rosters.yaml)")
    except yaml.YAMLError as exc:
        raise _fail(f"unparseable YAML: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_VERSION:
        raise _fail(f"top-level must be a mapping with schema: {SCHEMA_VERSION}")
    staleness = doc.get("staleness_days")
    if isinstance(staleness, bool) or not isinstance(staleness, int) or staleness <= 0:
        raise _fail(f"staleness_days must be a positive integer, got {staleness!r}")
    entries = doc.get("rosters")
    if not isinstance(entries, list) or not entries:
        raise _fail("no 'rosters' list — an empty file is a bug, not an empty market")
    seen: set[str] = set()
    rows: list[RosterRow] = []
    for entry in entries:
        row = _validate(entry, seen)
        seen.add(row.plan_id)
        rows.append(row)
    return RostersDoc(staleness_days=staleness, rows=tuple(rows))


def ingest_rosters(conn: sqlite3.Connection, raw: str, run: RunContext) -> SourceReport:
    """Attach roster links to plans that exist (REQ-ING-009).

    Fail-closed shape, in this order:
      1. parse (loud) — nothing touched on invalid input;
      2. a roster naming an UNKNOWN plan aborts: a link to a plan we do not carry
         is a curation error, not noise;
      3. replace only the roster-sourced links, leaving plan-page links intact —
         the two sources age and are re-verified independently.
    """
    doc = parse_rosters(raw)
    known = {pid for (pid,) in conn.execute("SELECT id FROM plans")}
    unknown = [r.plan_id for r in doc.rows if r.plan_id not in known]
    if unknown:
        raise _fail(f"roster references unknown plan id(s): {sorted(unknown)}")
    try:
        with conn:
            # REQ-SUB-008: the roster file's OWN window is persisted here, in the same transaction
            # that stores the links it governs. Writing it anywhere else would let a database carry
            # links from one roster policy and a window from another.
            conn.execute(
                "UPDATE plan_config SET roster_staleness_days = ? WHERE id = 1",
                (doc.staleness_days,),
            )
            conn.execute("DELETE FROM plan_models WHERE link_source = ?", (LINK_SOURCE,))
            conn.executemany(
                "INSERT INTO plan_models"
                " (plan_id, raw_name, link_source, source_url, last_verified)"
                " VALUES (?,?,?,?,?)"
                # Scoped to the ONE intended case (review MINOR-5): a name the plan
                # page already carries. A broad OR IGNORE would also swallow NOT NULL
                # violations, which must stay loud.
                " ON CONFLICT (plan_id, raw_name) DO NOTHING",
                [
                    (row.plan_id, name, LINK_SOURCE, row.source_url, row.last_verified)
                    for row in doc.rows
                    for name in row.models
                ],
            )
    except sqlite3.IntegrityError as exc:
        raise _fail(f"roster working set violates schema constraints: {exc}") from exc
    stored = conn.execute(
        "SELECT COUNT(*) FROM plan_models WHERE link_source = ?", (LINK_SOURCE,)
    ).fetchone()[0]
    declared = sum(len(r.models) for r in doc.rows)
    report = SourceReport(
        source=SOURCE_NAME,
        stored=stored,
        # A roster name the plan page ALREADY carries is not stored twice; the plan
        # page wins because it is the more specific statement. Counted, never silent.
        skipped=declared - stored,
    )
    run.reports.append(report)
    return report


def stale_rosters(raw: str, today: dt.date) -> list[str]:
    """Wall-clock re-verification for the roster file (REQ-ING-009's own clock)."""
    doc = parse_rosters(raw)
    out: list[str] = []
    for row in doc.rows:
        age = (today - dt.date.fromisoformat(row.last_verified)).days
        if age > doc.staleness_days:
            out.append(
                f"{row.plan_id}: roster last_verified {row.last_verified} is {age} days old"
                f" (window {doc.staleness_days}) — re-verify {row.source_url}"
            )
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (V4C-50). Exit codes match the project contract: 0/1/2."""
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="rosters", description=__doc__)
    parser.add_argument("--check-staleness", metavar="ROSTERS_YAML", required=True)
    parser.add_argument("--today", default=None, help="YYYY-MM-DD (tests/CI determinism)")
    args = parser.parse_args(argv)

    path = Path(args.check_staleness)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    try:
        today = (
            dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(tz=dt.UTC).date()
        )
    except ValueError:
        print(f"error: --today is not YYYY-MM-DD: {args.today!r}", file=sys.stderr)
        return 2
    try:
        msgs = stale_rosters(path.read_text(encoding="utf-8"), today)
    except SourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for msg in msgs:
        print(f"STALE: {msg}")
    if msgs:
        print(f"{len(msgs)} stale roster(s) — the provider model lists need a verification pass.")
        return 1
    print("all rosters within the staleness window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def roster_staleness_days(conn: sqlite3.Connection) -> int:
    """The window roster links are aged against — the ROSTER's own, never the plan table's.

    REQ-SUB-008 / W-008. Until M6 this number came from `plan_config.staleness_days`, the CURATED
    PLAN table's clock, while `data/rosters.yaml` declared its own and `check_staleness` above aged
    roster FILES against that one. Both are 30 on shipped data, so the two readings agreed and
    nothing failed — the divergence was a future defect with no test able to see it.

    Fails LOUD on an unset value rather than falling back to the plan window. A fallback here would
    reinstate exactly the coupling this function was written to remove, and it would do it silently,
    on the databases most likely to be old.
    """
    row = conn.execute("SELECT roster_staleness_days FROM plan_config WHERE id = 1").fetchone()
    if row is None:
        msg = "plan_config missing — ingest the curated plan table first"
        raise ValueError(msg)
    if row[0] is None:
        msg = (
            "plan_config.roster_staleness_days is unset — re-ingest data/rosters.yaml so the roster"
            " window comes from the roster policy (REQ-SUB-008); it is deliberately NOT defaulted"
            " to the plan table's window"
        )
        raise ValueError(msg)
    return int(row[0])
