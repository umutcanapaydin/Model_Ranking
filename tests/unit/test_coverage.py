"""REQ-SUB-005 / REQ-ING-011: coverage and source health are MEASURED, not noticed."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from unittest import mock

import pytest

from app.workflows.coverage import SOURCE_STALE_DAYS, main, plan_coverage, source_health
from app.workflows.ingest import RunContext
from app.workflows.plans import ingest_plans
from app.workflows.registry import reconcile_plans
from app.workflows.schema import connect

PLANS = """
schema: 1
staleness_days: 30
budget_caps_usd: {dusuk: 10, orta: 25, sinirsiz: null}
plans:
  - id: scored-plan
    provider: A
    name: Scored Plan
    monthly_usd: 20
    currency: USD
    region: US
    limits: x
    included_models: [Gemini 3 Pro]
    source_url: https://a.example/pricing
    last_verified: 2026-08-15
  - id: linked-but-unscored
    provider: B
    name: Linked But Unscored
    monthly_usd: 20
    currency: USD
    region: US
    limits: x
    included_models: [Grok 4.5]
    source_url: https://b.example/pricing
    last_verified: 2026-08-15
  - id: silent-plan
    provider: C
    name: Silent Plan
    monthly_usd: 20
    currency: USD
    region: US
    limits: x
    included_models: []
    source_url: https://c.example/pricing
    last_verified: 2026-08-15
"""


def _db(run_date: str = "2026-08-01", path: str = ":memory:") -> sqlite3.Connection:
    conn = connect(path)
    ingest_plans(conn, PLANS, RunContext())
    reconcile_plans(conn)
    conn.execute(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
        " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "gemini-3-pro",
            "agent + Gemini 3 Pro",
            "SWE-bench Verified",
            "% resolved",
            77.4,
            "test-agent",
            run_date,
            "swebench",
            "https://x",
            "2026-08-15T00:00:00+00:00",
        ),
    )
    conn.commit()  # leave no open write transaction: a caller may reopen this file
    return conn


def test_coverage_counts_and_explains_every_unscoreable_plan() -> None:
    """The number alone is not enough: a plan that cannot rank must say WHY."""
    cov = {c.category: c for c in plan_coverage(_db())}
    coding = cov["coding"]
    assert (coding.total_plans, coding.scoreable_plans) == (3, 1)
    assert coding.scoreable == ("Scored Plan",)
    # Silent Plan names nothing at all; Linked But Unscored links fine but has no
    # score on THIS benchmark — two different problems with two different fixes.
    assert coding.unscoreable_no_links == ("Silent Plan",)
    assert coding.unscoreable_no_scores == ("Linked But Unscored",)
    # The assistant category has no Arena rows here, so nothing is scoreable there.
    assert cov["assistant"].scoreable_plans == 0


def test_source_health_flags_a_source_that_went_quiet() -> None:
    """REQ-ING-011: the M3 owner-run finding (SWE-bench 170 days old) is now computed."""
    health = {h.source: h for h in source_health(_db(), today=dt.date(2026, 8, 15))}
    swe = health["swebench"]
    assert swe.rows == 1
    assert swe.newest_run_date == "2026-08-01"
    assert swe.age_days == 14
    assert swe.stale is False
    old = {h.source: h for h in source_health(_db("2026-01-01"), today=dt.date(2026, 8, 15))}
    assert old["swebench"].age_days == 226
    assert old["swebench"].stale is True


def test_stale_window_matches_the_engines_disclosure_window() -> None:
    """One definition of 'old' — the report and the product must never disagree."""
    from app.workflows.recommend import STALE_NOTICE_DAYS

    assert SOURCE_STALE_DAYS == STALE_NOTICE_DAYS


def test_boundary_exactly_at_the_window_is_not_stale() -> None:
    conn = _db("2026-05-17")  # exactly 90 days before 2026-08-15
    assert source_health(conn, today=dt.date(2026, 8, 15))[0].stale is False
    conn = _db("2026-05-16")  # 91 days
    assert source_health(conn, today=dt.date(2026, 8, 15))[0].stale is True


def test_cli_reports_json_and_fails_loud_on_zero_coverage(tmp_path, capsys) -> None:
    """V4C-50: the exact command CI runs. Exit 1 when a category can answer nothing."""
    db = tmp_path / "advisor.db"
    _db(path=str(db)).close()

    # assistant has zero coverage in this fixture -> exit 1, and the JSON still prints
    assert main(["--db", str(db), "--today", "2026-08-15"]) == 1
    out = json.loads(capsys.readouterr().out)
    coding = next(c for c in out["plan_coverage"] if c["category"] == "coding")
    assert coding["scoreable_plans"] == 1
    assert coding["unscoreable_no_links"] == ["Silent Plan"]
    assert out["source_health"][0]["source"] == "swebench"

    assert main(["--db", str(tmp_path / "missing.db")]) == 2
    assert main(["--db", str(db), "--today", "nope"]) == 2


def test_coverage_is_read_only() -> None:
    """A metric that mutates the thing it measures is not a metric."""
    conn = _db()
    before = conn.execute("SELECT COUNT(*) FROM plan_models").fetchone()[0]
    plan_coverage(conn)
    source_health(conn, dt.date(2026, 8, 15))
    assert conn.execute("SELECT COUNT(*) FROM plan_models").fetchone()[0] == before


@pytest.mark.parametrize("bad_date", ["not-a-date", ""])
def test_unparseable_run_date_is_reported_not_guessed(bad_date: str) -> None:
    conn = _db()
    conn.execute("UPDATE scores SET run_date = ?", (bad_date,))
    health = source_health(conn, today=dt.date(2026, 8, 15))[0]
    assert health.age_days is None
    # Review MINOR-1: unknown age must fail TOWARD disclosure. A source with rows
    # and no readable date is not evidence of freshness.
    assert health.stale is True


def test_links_that_all_dropped_count_as_no_links() -> None:
    """The LIVE shape (review): links exist as rows but resolve to NULL — that is
    a curation gap, not a benchmark gap, and the report must say the right one."""
    conn = _db()
    conn.execute("UPDATE plan_models SET model_id = NULL WHERE plan_id = 'linked-but-unscored'")
    coding = next(c for c in plan_coverage(conn) if c.category == "coding")
    assert "Linked But Unscored" in coding.unscoreable_no_links
    assert "Linked But Unscored" not in coding.unscoreable_no_scores


def test_cli_opens_the_database_read_only(tmp_path) -> None:
    """M4 closure (security MINOR-4): the read-only claim is a MECHANISM, not a comment.

    `test_coverage_is_read_only` proves the two functions do not write today. This proves
    the CLI could not write even if a future edit tried: the handle it opens rejects
    writes at the SQLite layer. The probe runs INSIDE the spy because `main()` closes the
    connection before returning. Dropping `mode=ro` from `main()` turns this red.
    """
    db = tmp_path / "advisor.db"
    _db(path=str(db)).close()

    probes: list[str] = []
    real_connect = sqlite3.connect

    def spy(*args: object, **kwargs: object) -> sqlite3.Connection:
        conn = real_connect(*args, **kwargs)  # type: ignore[arg-type]
        try:
            conn.execute("DELETE FROM plans")
        except sqlite3.OperationalError as exc:
            probes.append(str(exc))
        else:  # pragma: no cover - only reached when the handle is writable
            conn.rollback()
            probes.append("WRITE ACCEPTED")
        return conn

    with mock.patch.object(sqlite3, "connect", spy):
        assert main(["--db", str(db), "--today", "2026-08-15"]) in (0, 1)

    assert probes, "the CLI must open the database through sqlite3.connect"
    assert "readonly" in probes[0], probes[0]
