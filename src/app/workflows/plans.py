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
from typing import Any

import yaml

from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, SourceReport
from app.workflows.schema import PlanRow

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


def parse_plans(raw: str) -> list[PlanRow]:
    """Parse + validate the curated plan table; ANY invalid row aborts loudly."""
    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise _fail(f"unparseable YAML: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_VERSION:
        raise _fail(f"top-level must be a mapping with schema: {SCHEMA_VERSION}")
    entries = doc.get("plans")
    if not isinstance(entries, list) or not entries:
        raise _fail("no 'plans' list — an empty curated table is a bug, not an empty market")
    rows: list[PlanRow] = []
    seen: set[str] = set()
    for entry in entries:
        row = _validate_plan(entry, seen)
        seen.add(row.id)
        rows.append(row)
    return rows


def ingest_plans(conn: sqlite3.Connection, raw: str, run: RunContext) -> SourceReport:
    """Replace the WHOLE plan working set atomically (REQ-SUB-002).

    The curated table is one document, so the unit of replacement is the whole
    table — not per-source rows. Rollback on any violation keeps the previous
    working set (same fail-closed shape as _store_pricing / _store_scores).
    """
    rows = parse_plans(raw)
    try:
        with conn:
            conn.execute("DELETE FROM plan_models")
            conn.execute("DELETE FROM plans")
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
