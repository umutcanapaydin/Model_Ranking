"""REQ-SUB-005 / REQ-ING-011: coverage and source health are MEASURED, not noticed."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from unittest import mock

import pytest

from app.workflows.categories import CATEGORIES
from app.workflows.coverage import (
    PLAN_FRESH_DAYS,
    SOURCE_STALE_DAYS,
    main,
    plan_coverage,
    plan_evidence_health,
    source_health,
)
from app.workflows.ingest import RunContext
from app.workflows.plans import ingest_plans
from app.workflows.registry import reconcile_plans
from app.workflows.schema import connect
from app.workflows.subscribe import plan_ranking

PLANS = """
schema: 1
staleness_days: 30
budget_caps_usd: {low: 10, medium: 25, unlimited: null}
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


def _evidence_db() -> sqlite3.Connection:
    """Four plans exercising the exhaustive freshness partition."""
    conn = connect()
    conn.executemany(
        "INSERT INTO plans (id, provider, name, monthly_usd, currency, region, limits,"
        " source_url, last_verified, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                plan_id,
                "Provider",
                name,
                10.0,
                "USD",
                "US",
                "test",
                f"https://example.test/{plan_id}",
                "2026-08-15",
                "2026-08-16T00:00:00+00:00",
            )
            for plan_id, name in (
                ("fresh-plan", "Fresh Plan"),
                ("stale-plan", "Stale Plan"),
                ("undated-plan", "Undated Plan"),
                ("unscored-plan", "Unscored Plan"),
            )
        ],
    )
    conn.executemany(
        "INSERT INTO models (id, display, vendor) VALUES (?,?,?)",
        [
            ("glm-5.2", "GLM-5.2", "Zhipu"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro", "Google"),
            ("gpt-5.6-sol", "GPT-5.6 Sol", "OpenAI"),
        ],
    )
    conn.executemany(
        "INSERT INTO plan_models (plan_id, raw_name, model_id) VALUES (?,?,?)",
        [
            ("fresh-plan", "GLM-5.2", "glm-5.2"),
            ("stale-plan", "Gemini 3.1 Pro", "gemini-3.1-pro"),
            ("undated-plan", "GPT-5.6 Sol", "gpt-5.6-sol"),
        ],
    )
    conn.executemany(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
        " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "glm-5.2",
                "glm-5.2_max",
                "SWE-bench Verified",
                "% resolved",
                78.7,
                "inspect_ai",
                "2026-06-18",  # 59 days: fresh
                "epoch_swe_bench_verified",
                "https://epoch.ai/data/benchmark_data.zip",
                "2026-08-16T00:00:00+00:00",
            ),
            (
                "gemini-3.1-pro",
                "gemini-3.1-pro-preview-customtools",
                "SWE-bench Verified",
                "% resolved",
                75.6,
                "inspect_ai",
                "2026-06-17",  # 60 days: stale boundary
                "epoch_swe_bench_verified",
                "https://epoch.ai/data/benchmark_data.zip",
                "2026-08-16T00:00:00+00:00",
            ),
            (
                "gpt-5.6-sol",
                "gpt-5.6-sol_high",
                "SWE-bench Verified",
                "% resolved",
                72.7,
                "mini-swe-agent",
                None,
                "deepswe",
                "https://epoch.ai/benchmarks",
                "2026-08-16T00:00:00+00:00",
            ),
        ],
    )
    conn.commit()
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


def test_coverage_requires_the_category_metric_not_only_the_benchmark() -> None:
    """D-105: a foreign metric sharing the benchmark name cannot make a plan scoreable."""
    conn = _db()
    conn.execute(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
        " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "grok-4.5",
            "Grok 4.5",
            "SWE-bench Verified",
            "not % resolved",
            999.0,
            "foreign",
            "2026-08-15",
            "foreign",
            "https://example.test/foreign",
            "2026-08-15T00:00:00+00:00",
        ),
    )

    coding = next(row for row in plan_coverage(conn) if row.category == "coding")
    assert coding.scoreable == ("Scored Plan",)
    assert coding.unscoreable_no_scores == ("Linked But Unscored",)


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


def test_plan_evidence_health_partitions_every_plan_once() -> None:
    """REQ-ING-011b: selected evidence yields fresh/stale/undated/unscored exactly once."""
    health = plan_evidence_health(_evidence_db(), CATEGORIES["coding"], today=dt.date(2026, 8, 16))

    assert PLAN_FRESH_DAYS == 60
    assert (health.total_plans, health.fresh, health.stale, health.undated, health.unscored) == (
        4,
        1,
        1,
        1,
        1,
    )
    assert sum((health.fresh, health.stale, health.undated, health.unscored)) == 4
    by_id = {plan.plan_id: plan for plan in health.plans}
    assert len(by_id) == 4
    assert (by_id["fresh-plan"].status, by_id["fresh-plan"].age_days) == ("fresh", 59)
    assert (by_id["stale-plan"].status, by_id["stale-plan"].age_days) == ("stale", 60)
    assert by_id["undated-plan"].status == "undated"
    assert by_id["unscored-plan"].status == "unscored"


def test_plan_evidence_health_uses_selected_row_not_source_max() -> None:
    """REQ-ING-011b: a fresh source row must not mask a stale selected plan row."""
    conn = _evidence_db()
    source = {row.source: row for row in source_health(conn, today=dt.date(2026, 8, 16))}[
        "epoch_swe_bench_verified"
    ]
    plans = {
        row.plan_id: row
        for row in plan_evidence_health(
            conn, CATEGORIES["coding"], today=dt.date(2026, 8, 16)
        ).plans
    }

    assert source.newest_run_date == "2026-06-18"
    assert source.stale is False
    stale = plans["stale-plan"]
    assert (stale.status, stale.evidence_date, stale.selected_model) == (
        "stale",
        "2026-06-17",
        "Gemini 3.1 Pro",
    )
    assert stale.evidence_source == "epoch_swe_bench_verified"


@pytest.mark.parametrize("bad_date", ["not-a-date", "2026-06-18junk"])
def test_invalid_selected_evidence_date_fails_loudly(bad_date: str) -> None:
    """REQ-ING-011b: corrupt selected dates are not silently relabelled undated."""
    conn = _evidence_db()
    conn.execute("UPDATE scores SET run_date = ? WHERE model_id = 'glm-5.2'", (bad_date,))

    with pytest.raises(ValueError, match="selected evidence date is not ISO-8601"):
        plan_evidence_health(conn, CATEGORIES["coding"], today=dt.date(2026, 8, 16))


def test_cli_returns_usage_error_for_invalid_selected_evidence_date(tmp_path, capsys) -> None:
    """REQ-ING-011b: corrupt evidence fails through the frozen CLI 0/1/2 contract."""
    db = tmp_path / "invalid-evidence.db"
    conn = _db(path=str(db))
    conn.execute("UPDATE scores SET run_date = 'not-a-date'")
    conn.commit()
    conn.close()

    assert main(["--db", str(db), "--today", "2026-08-16"]) == 2
    assert "selected evidence date is not ISO-8601" in capsys.readouterr().err


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
    conn = _db(path=str(db))
    raw_score = 75.6198347107438
    conn.execute("UPDATE scores SET score = ?", (raw_score,))
    conn.commit()
    ranking = plan_ranking(conn, CATEGORIES["coding"])
    assert ranking[0].score == raw_score  # D-109: selection compares unrounded evidence
    conn.close()

    # assistant has zero coverage in this fixture -> exit 1, and the JSON still prints
    assert main(["--db", str(db), "--today", "2026-08-15"]) == 1
    out = json.loads(capsys.readouterr().out)
    coding = next(c for c in out["plan_coverage"] if c["category"] == "coding")
    assert coding["scoreable_plans"] == 1
    assert coding["unscoreable_no_links"] == ["Silent Plan"]
    assert out["source_health"][0]["source"] == "swebench"
    coding_health = next(h for h in out["plan_evidence_health"] if h["category"] == "coding")
    assert coding_health["total_plans"] == 3
    assert coding_health["fresh"] == 1
    assert coding_health["unscored"] == 2
    scored = next(plan for plan in coding_health["plans"] if plan["plan"] == "Scored Plan")
    assert scored["score"] == 75.6  # D-109: round exactly once at the JSON/report boundary

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


def test_coverage_cli_read_only_survives_a_path_containing_a_question_mark(tmp_path) -> None:
    """M5 security review: `as_posix()` concatenation let a path defeat `mode=ro`.

    A '?' in the database path terminated the URI, so the mode parameter was dropped
    AND sqlite fell back to CREATING a database — a read-only command that writes. The
    migrate command already used `as_uri()`; this one does now too.
    """
    tricky = tmp_path / "advisor?x.db"
    _db(path=str(tricky)).close()
    size_before = tricky.stat().st_size

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
        assert main(["--db", str(tricky), "--today", "2026-08-15"]) in (0, 1)

    assert probes and "readonly" in probes[0], probes
    assert tricky.stat().st_size == size_before
