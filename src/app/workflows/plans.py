"""Subscription-plan layer: curated table -> validated working set (REQ-SUB-001/-002).

The plan table is CURATED, IN-REPO DATA (`data/plans.yaml`) — no machine-readable
feed for consumer AI subscriptions exists anywhere (M0 research; the project's
moat). Because the data is authored rather than fetched, the discipline flips:
a fetched source skips-and-counts bad rows; a curated file FAILS LOUD on any
invalid row (a curation error is a bug, not noise).

Every row carries provenance (``source_url``) and a ``last_verified`` date;
values are probed against the provider's live page on the day they are entered
(the FP-M2-2 fixture lesson, applied to data curation). Staleness disclosure on
top of ``last_verified`` is wired in M3-W2.
"""

from __future__ import annotations

import datetime as dt
import math
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

import yaml

from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, SourceReport
from app.workflows.schema import PlanRow
from app.workflows.yaml_guard import safe_load_bounded

SOURCE_NAME = "plans-curated"
PLAN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
SCHEMA_VERSION = 1
_REQUIRED_STR = ("provider", "name", "currency", "region", "limits", "source_url", "last_verified")


def _fail(msg: str) -> SourceError:
    return SourceError(f"{SOURCE_NAME}: {msg}")


def _validate_plan(entry: Any, seen_ids: set[str]) -> PlanRow:  # noqa: C901
    # (complexity waiver: one loud gate per field is the design — curated data fails loud)
    if not isinstance(entry, dict):
        raise _fail(f"plan entry is not a mapping: {entry!r}")
    plan_id = entry.get("id")
    if not isinstance(plan_id, str) or not PLAN_ID_RE.match(plan_id):
        raise _fail(f"invalid plan id {plan_id!r} (want kebab-case, ≥3 chars)")
    if plan_id in seen_ids:
        raise _fail(f"duplicate plan id {plan_id!r}")
    # YAML parses a bare ISO date as datetime.date — normalize to the string form (no
    # caller-dict mutation; review MINOR: validators must not edit their input).
    raw_verified = entry.get("last_verified")
    last_verified = raw_verified.isoformat() if isinstance(raw_verified, dt.date) else raw_verified
    fields = {**entry, "last_verified": last_verified}
    for key in _REQUIRED_STR:
        val = fields.get(key)
        if not isinstance(val, str) or not val.strip():
            raise _fail(f"{plan_id}: field {key!r} missing or empty")
    price = fields.get("monthly_usd")
    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(price)
        or price <= 0
    ):
        raise _fail(f"{plan_id}: monthly_usd must be a finite number > 0, got {price!r}")
    if not str(fields["source_url"]).startswith("https://"):
        raise _fail(f"{plan_id}: source_url must be https, got {fields['source_url']!r}")
    try:
        dt.date.fromisoformat(fields["last_verified"])
    except ValueError as exc:
        raise _fail(
            f"{plan_id}: last_verified is not YYYY-MM-DD: {fields['last_verified']!r}"
        ) from exc
    models_raw = entry.get("included_models", [])
    if models_raw is None:
        models_raw = []
    if not isinstance(models_raw, list) or any(
        not isinstance(m, str) or not m.strip() for m in models_raw
    ):
        raise _fail(f"{plan_id}: included_models must be a list of non-empty strings")
    if len(set(models_raw)) != len(models_raw):
        raise _fail(f"{plan_id}: duplicate name in included_models")
    return PlanRow(
        id=plan_id,
        provider=fields["provider"].strip(),
        name=fields["name"].strip(),
        monthly_usd=float(price),
        currency=fields["currency"].strip(),
        region=fields["region"].strip(),
        limits=fields["limits"].strip(),
        included_models=tuple(models_raw),
        source_url=fields["source_url"].strip(),
        last_verified=fields["last_verified"].strip(),
    )


@dataclass(frozen=True)
class PlansDoc:
    """The whole curated document: thresholds as DATA + validated rows (REQ-SUB-003/-007)."""

    staleness_days: int
    cap_dusuk: float  # monthly-USD budget caps for --subscription (owner-tunable data)
    cap_orta: float
    rows: tuple[PlanRow, ...]


def _validate_caps(caps: Any) -> tuple[float, float]:
    """budget_caps_usd is DATA (owner-tunable) — validate shape + ordering loudly."""
    if not isinstance(caps, dict) or set(caps) != {"low", "medium", "unlimited"}:
        raise _fail(
            f"budget_caps_usd must map exactly low/medium/unlimited (data, not a code default),"
            f" got {caps!r}"
        )
    if caps["unlimited"] is not None:
        raise _fail("budget_caps_usd.unlimited must be null (uncapped by definition)")
    for name in ("low", "medium"):
        val = caps[name]
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
            raise _fail(f"budget_caps_usd.{name} must be a finite number, got {val!r}")
    if not 0 < float(caps["low"]) < float(caps["medium"]):
        raise _fail(
            f"budget caps must satisfy 0 < low < medium, got {caps['low']!r}/{caps['medium']!r}"
        )
    return float(caps["low"]), float(caps["medium"])


def parse_plans_doc(raw: str) -> PlansDoc:
    """Parse + validate the curated plan table; ANY invalid row aborts loudly.

    ``staleness_days`` is REQUIRED at the top level — a default in code would be
    a threshold living as a code branch, the exact M2-W4 latent-debt class.
    """
    try:
        doc = safe_load_bounded(raw, what="the curated plan table (data/plans.yaml)")
    except yaml.YAMLError as exc:
        raise _fail(f"unparseable YAML: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_VERSION:
        raise _fail(f"top-level must be a mapping with schema: {SCHEMA_VERSION}")
    staleness = doc.get("staleness_days")
    if isinstance(staleness, bool) or not isinstance(staleness, int) or staleness <= 0:
        raise _fail(
            f"staleness_days must be a positive integer at the top level (data, not a code"
            f" default), got {staleness!r}"
        )
    cap_dusuk, cap_orta = _validate_caps(doc.get("budget_caps_usd"))
    entries = doc.get("plans")
    if not isinstance(entries, list) or not entries:
        raise _fail("no 'plans' list — an empty curated table is a bug, not an empty market")
    rows: list[PlanRow] = []
    seen: set[str] = set()
    for entry in entries:
        row = _validate_plan(entry, seen)
        seen.add(row.id)
        rows.append(row)
    return PlansDoc(
        staleness_days=staleness,
        cap_dusuk=float(cap_dusuk),
        cap_orta=float(cap_orta),
        rows=tuple(rows),
    )


def parse_plans(raw: str) -> list[PlanRow]:
    """Row-only view of parse_plans_doc (kept for W1 call sites and tests)."""
    return list(parse_plans_doc(raw).rows)


def ingest_plans(conn: sqlite3.Connection, raw: str, run: RunContext) -> SourceReport:
    """Replace the WHOLE plan working set atomically (REQ-SUB-002).

    The curated table is one document, so the unit of replacement is the whole
    table — not per-source rows. Rollback on any violation keeps the previous
    working set (same fail-closed shape as _store_pricing / _store_scores).
    """
    doc = parse_plans_doc(raw)
    rows = doc.rows
    try:
        with conn:
            conn.execute("DELETE FROM plan_models")
            conn.execute("DELETE FROM plans")
            conn.execute(
                "INSERT OR REPLACE INTO plan_config (id, staleness_days, cap_dusuk, cap_orta)"
                " VALUES (1, ?, ?, ?)",
                (doc.staleness_days, doc.cap_dusuk, doc.cap_orta),
            )
            conn.executemany(
                "INSERT INTO plans (id, provider, name, monthly_usd, currency, region,"
                " limits, source_url, last_verified, observed_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        r.id,
                        r.provider,
                        r.name,
                        r.monthly_usd,
                        r.currency,
                        r.region,
                        r.limits,
                        r.source_url,
                        r.last_verified,
                        run.observed_at,
                    )
                    for r in rows
                ],
            )
            conn.executemany(
                "INSERT INTO plan_models (plan_id, raw_name) VALUES (?,?)",
                [(r.id, name) for r in rows for name in r.included_models],
            )
    except sqlite3.IntegrityError as exc:
        raise _fail(f"plan working set violates schema constraints: {exc}") from exc
    report = SourceReport(source=SOURCE_NAME, stored=len(rows), skipped=0)
    run.reports.append(report)
    return report


@dataclass(frozen=True)
class StalePlan:
    """One plan row past the staleness window (REQ-SUB-003 — disclosed, never hidden)."""

    plan_id: str
    name: str
    last_verified: str
    days_over: int


def stale_plans(conn: sqlite3.Connection) -> tuple[StalePlan, ...]:
    """Deterministic staleness: last_verified vs THIS ingest's observed_at stamp.

    Same proxy shape as the M2 stale_notice, same documented blind spot: a
    database that is never re-ingested cannot report itself stale (no
    wall-clock anchor, by determinism design — D-104). The wall-clock check
    lives in the CI cadence job (`--check-staleness`, REQ-SUB-004).
    """
    cfg = conn.execute("SELECT staleness_days FROM plan_config WHERE id = 1").fetchone()
    if cfg is None:
        return ()
    window = int(cfg[0])
    out: list[StalePlan] = []
    for plan_id, name, verified, observed in conn.execute(
        "SELECT id, name, last_verified, observed_at FROM plans ORDER BY id"
    ):
        try:
            age = (dt.date.fromisoformat(str(observed)[:10]) - dt.date.fromisoformat(verified)).days
        except ValueError as exc:
            # last_verified is parser-gated and observed_at is a RunContext stamp, so this
            # is unreachable through any in-repo write path — only out-of-band DB edits.
            # Fail LOUD: a corrupt date must never make a stale row look fresh (W2 review).
            raise _fail(f"{plan_id}: unparseable date in DB (out-of-band edit?): {exc}") from exc
        if age > window:
            out.append(StalePlan(plan_id, name, verified, age - window))
    return tuple(out)


def check_staleness(raw: str, today: dt.date) -> list[str]:
    """Wall-clock re-verification check for CI (REQ-SUB-004).

    Returns one message per plan row whose last_verified is older than the
    document's own staleness_days relative to ``today``. Empty = all fresh.
    """
    doc = parse_plans_doc(raw)
    msgs: list[str] = []
    for row in doc.rows:
        age = (today - dt.date.fromisoformat(row.last_verified)).days
        if age > doc.staleness_days:
            msgs.append(
                f"{row.id}: last_verified {row.last_verified} is {age} days old"
                f" (window {doc.staleness_days}) — re-verify {row.source_url}"
            )
    return msgs


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (V4C-50: the cadence job enters HERE, not a unit shim).

    Exit codes match the recommend CLI contract: 0 ok, 1 stale rows found,
    2 usage/file error.
    """
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="plans", description=__doc__)
    parser.add_argument("--check-staleness", metavar="PLANS_YAML", required=True)
    parser.add_argument("--today", default=None, help="YYYY-MM-DD (tests/CI determinism)")
    args = parser.parse_args(argv)

    path = Path(args.check_staleness)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    try:
        # UTC explicitly — a local-TZ date would move the boundary ±1 day per runner TZ.
        today = (
            dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(tz=dt.UTC).date()
        )
    except ValueError:
        print(f"error: --today is not YYYY-MM-DD: {args.today!r}", file=sys.stderr)
        return 2
    try:
        msgs = check_staleness(path.read_text(encoding="utf-8"), today)
    except SourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for msg in msgs:
        print(f"STALE: {msg}")
    if msgs:
        print(f"{len(msgs)} stale plan row(s) — the table needs a verification pass.")
        return 1
    print("all plan rows within the staleness window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
