"""REQ-SUB-003/-004: staleness disclosed deterministically; cadence check via the real CLI."""

from __future__ import annotations

import datetime as dt

from app.workflows.ingest import RunContext
from app.workflows.plans import check_staleness, ingest_plans, main, stale_plans
from app.workflows.schema import connect

FRESH = "2026-08-15"
OLD = "2026-06-01"

DOC = f"""
schema: 1
staleness_days: 30
plans:
  - id: fresh-plan
    provider: A
    name: Fresh Plan
    monthly_usd: 10
    currency: USD
    region: US
    limits: x
    source_url: https://a.example/pricing
    last_verified: {FRESH}
  - id: old-plan
    provider: B
    name: Old Plan
    monthly_usd: 10
    currency: USD
    region: US
    limits: x
    source_url: https://b.example/pricing
    last_verified: {OLD}
"""


def _conn_with(doc: str, observed: str):
    conn = connect()
    run = RunContext()
    run.observed_at = observed
    ingest_plans(conn, doc, run)
    return conn


def test_stale_plans_is_deterministic_vs_ingest_stamp() -> None:
    """Staleness compares last_verified to THIS ingest's observed_at, not wall clock."""
    conn = _conn_with(DOC, "2026-08-15T12:00:00+00:00")
    stale = stale_plans(conn)
    assert [s.plan_id for s in stale] == ["old-plan"]
    assert stale[0].days_over == (dt.date(2026, 8, 15) - dt.date(2026, 6, 1)).days - 30
    assert stale[0].last_verified == OLD


def test_boundary_exactly_window_days_is_not_stale() -> None:
    """30-day window: age == 30 is fresh; 31 is stale (strict >)."""
    doc = DOC.replace(OLD, "2026-07-16")  # exactly 30 days before 2026-08-15
    conn = _conn_with(doc, "2026-08-15T00:00:00+00:00")
    assert stale_plans(conn) == ()
    doc = DOC.replace(OLD, "2026-07-15")  # 31 days
    conn = _conn_with(doc, "2026-08-15T00:00:00+00:00")
    assert [s.plan_id for s in stale_plans(conn)] == ["old-plan"]


def test_window_is_read_from_data_not_code() -> None:
    """Changing staleness_days in the DOCUMENT changes the verdict — no code edit."""
    doc = DOC.replace("staleness_days: 30", "staleness_days: 90")
    conn = _conn_with(doc, "2026-08-15T00:00:00+00:00")
    assert stale_plans(conn) == ()  # 75-day-old row is fine under a 90-day window


def test_check_staleness_wall_clock_messages_carry_source_url() -> None:
    msgs = check_staleness(DOC, today=dt.date(2026, 8, 15))
    assert len(msgs) == 1
    assert "old-plan" in msgs[0]
    assert "https://b.example/pricing" in msgs[0]  # the re-verify pointer is the remedy


def test_cli_exit_codes_through_real_entrypoint(tmp_path, capsys) -> None:
    """V4C-50: the cadence job's exact entrypoint — exit 1 stale, 0 fresh, 2 usage."""
    p = tmp_path / "plans.yaml"
    p.write_text(DOC, encoding="utf-8")
    assert main(["--check-staleness", str(p), "--today", "2026-08-15"]) == 1
    assert "STALE: old-plan" in capsys.readouterr().out
    assert main(["--check-staleness", str(p), "--today", "2026-07-01"]) == 0
    assert main(["--check-staleness", str(tmp_path / "missing.yaml")]) == 2
    assert main(["--check-staleness", str(p), "--today", "not-a-date"]) == 2
    p.write_text("schema: 1\n", encoding="utf-8")
    assert main(["--check-staleness", str(p), "--today", "2026-08-15"]) == 2


def test_shipped_seed_is_fresh_on_entry_day() -> None:
    """The real data/plans.yaml passes its own cadence check on the day it was authored."""
    from pathlib import Path

    seed = (Path(__file__).resolve().parents[2] / "data" / "plans.yaml").read_text(encoding="utf-8")
    assert check_staleness(seed, today=dt.date(2026, 8, 15)) == []


def test_corrupt_db_date_fails_loud_never_fresh() -> None:
    """W2 review MINOR-1: an out-of-band corrupt date must not mask staleness."""
    import pytest

    from app.clients.protocols import SourceError

    conn = _conn_with(DOC, "2026-08-15T00:00:00+00:00")
    conn.execute("UPDATE plans SET observed_at = 'garbage' WHERE id = 'old-plan'")
    with pytest.raises(SourceError, match="out-of-band"):
        stale_plans(conn)
