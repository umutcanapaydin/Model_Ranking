"""W3 DeepSWE source wiring and real-engine measurement (REQ-ING-011b/-SUB-007)."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import pytest

from app.clients.deepswe import (
    EPOCH_DEEPSWE_FILE,
    SOURCE_NAME,
    DeepSWEClient,
)
from app.clients.epoch import EPOCH_BUNDLE_URL, EpochClient
from app.clients.fakes import FakeRawSource
from app.clients.protocols import SourceError
from app.workflows.categories import CATEGORIES
from app.workflows.coverage import main as coverage_main
from app.workflows.coverage import plan_coverage, plan_evidence_health, source_health
from app.workflows.ingest import RunContext, ingest_deepswe, ingest_epoch, ingest_swebench
from app.workflows.plans import ingest_plans
from app.workflows.recommend import main as recommend_main
from app.workflows.registry import reconcile, reconcile_plans
from app.workflows.rosters import ingest_rosters
from app.workflows.schema import connect
from app.workflows.subscribe import plan_ranking

SOURCE_URL = f"{EPOCH_BUNDLE_URL}#{EPOCH_DEEPSWE_FILE}"
DEEPSWE_CSV = """Model version,Pass@1,Harness,Reasoning effort,Release date
gpt-5.6-sol_high,0.60,mini-swe-agent,high,2026-07-09
claude-opus-5_max,0.70,mini-swe-agent,medium,2026-07-01
kimi-k2.7-code,0.30,mini-swe-agent,,2026-07-01
gpt-5.6-terra_max,not-a-score,mini-swe-agent,max,2026-07-01
"""


def _source(payload: str = DEEPSWE_CSV, **kwargs: object) -> FakeRawSource:
    return FakeRawSource(
        SOURCE_NAME,
        payload,
        url=SOURCE_URL,
        last_verified=kwargs.get("last_verified", "2026-08-15"),
    )


def test_local_client_reads_only_the_allowlisted_board(tmp_path: Path) -> None:
    """REQ-ING-010: runtime reads an explicit local board with its own clock."""
    (tmp_path / EPOCH_DEEPSWE_FILE).write_text(DEEPSWE_CSV, encoding="utf-8")
    (tmp_path / "other.csv").write_text("secret", encoding="utf-8")

    client = DeepSWEClient(tmp_path, last_verified="2026-08-15")

    assert (client.name, client.url, client.last_verified) == (
        SOURCE_NAME,
        SOURCE_URL,
        "2026-08-15",
    )
    assert client.fetch_raw() == DEEPSWE_CSV


def test_local_client_rejects_urls_bad_clock_and_missing_board(tmp_path: Path) -> None:
    """REQ-ING-010 negative boundary: no fetch fallback and no invented clock."""
    with pytest.raises(SourceError, match="local unpacked bundle"):
        DeepSWEClient(EPOCH_BUNDLE_URL, last_verified="2026-08-15")
    with pytest.raises(SourceError, match=f"{SOURCE_NAME}: last_verified"):
        DeepSWEClient(tmp_path, last_verified="15/08/2026")
    with pytest.raises(SourceError, match="missing CSV"):
        DeepSWEClient(tmp_path, last_verified="2026-08-15").fetch_raw()


def test_ingest_publishes_effort_accounting_and_keeps_release_dates_out() -> None:
    """REQ-CAN-005/REQ-ING-011b: unknown/conflict counts and undated evidence survive wiring."""
    conn = connect()
    run = RunContext(observed_at="2026-08-16T00:00:00+00:00")

    report = ingest_deepswe(conn, _source(), run)

    assert (
        report.source,
        report.stored,
        report.skipped,
        report.effort_unknown,
        report.effort_conflicts,
        report.last_verified,
    ) == (SOURCE_NAME, 2, 2, 1, 1, "2026-08-15")
    assert run.reports == [report]
    assert conn.execute(
        "SELECT raw_name, score, harness, effort, run_date, source_url, observed_at"
        " FROM scores ORDER BY raw_name"
    ).fetchall() == [
        (
            "claude-opus-5_max",
            70.0,
            "mini-swe-agent",
            "medium",
            None,
            SOURCE_URL,
            run.observed_at,
        ),
        (
            "gpt-5.6-sol_high",
            60.0,
            "mini-swe-agent",
            "high",
            None,
            SOURCE_URL,
            run.observed_at,
        ),
    ]


def test_workflow_requires_and_validates_the_independent_verification_clock() -> None:
    """REQ-ING-010: a fake cannot bypass the production clock boundary."""
    run = RunContext(observed_at="2026-08-16T00:00:00+00:00")
    missing = FakeRawSource(SOURCE_NAME, DEEPSWE_CSV, url=SOURCE_URL)
    invalid = _source(last_verified="2026-02-30")

    with pytest.raises(SourceError, match="last_verified is mandatory"):
        ingest_deepswe(connect(), missing, run)
    with pytest.raises(SourceError, match=f"{SOURCE_NAME}: last_verified"):
        ingest_deepswe(connect(), invalid, run)


def test_rerun_replaces_only_deepswe_rows() -> None:
    """REQ-ING-004: DeepSWE replacement cannot erase another score source."""
    conn = connect()
    ingest_swebench(
        conn,
        FakeRawSource(
            "swebench",
            json.dumps(
                {
                    "leaderboards": [
                        {
                            "name": "Verified",
                            "results": [{"name": "agent + GPT-5.6 Sol", "resolved": 50.0}],
                        }
                    ]
                }
            ),
        ),
        RunContext(observed_at="swebench"),
    )
    ingest_deepswe(conn, _source(), RunContext(observed_at="deep-old"))
    replacement = DEEPSWE_CSV.replace("gpt-5.6-sol_high,0.60", "gpt-5.6-sol_high,0.61")

    report = ingest_deepswe(conn, _source(replacement), RunContext(observed_at="deep-new"))

    assert report.stored == 2
    assert conn.execute("SELECT COUNT(*) FROM scores WHERE source = 'swebench'").fetchone() == (1,)
    assert conn.execute(
        "SELECT score, observed_at FROM scores WHERE source = ? AND raw_name = ?",
        (SOURCE_NAME, "gpt-5.6-sol_high"),
    ).fetchone() == (61.0, "deep-new")


@pytest.mark.skipif(not os.getenv("EPOCH_DATA_DIR"), reason="set EPOCH_DATA_DIR for local contract")
def test_real_board_reproduces_signed_coverage_and_undated_health(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """REQ-ING-011b/REQ-SUB-007: shipped path yields coding 5/10 and agentic 6/10."""
    root = Path(__file__).resolve().parents[2]
    bundle = Path(os.environ["EPOCH_DATA_DIR"])
    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    run = RunContext(observed_at="2026-08-16T00:00:00+00:00")
    ingest_plans(conn, (root / "data/plans.yaml").read_text(encoding="utf-8"), run)
    ingest_rosters(conn, (root / "data/rosters.yaml").read_text(encoding="utf-8"), run)
    ingest_epoch(conn, EpochClient(bundle, last_verified="2026-08-15"), run)
    report = ingest_deepswe(conn, DeepSWEClient(bundle, last_verified="2026-08-15"), run)
    plan_links = reconcile_plans(conn)
    scores = reconcile(conn)

    assert (report.stored, report.skipped, report.effort_unknown, report.effort_conflicts) == (
        49,
        1,
        1,
        0,
    )
    assert plan_links == type(plan_links)(
        matched=10,
        dropped=3,
        dropped_names=("Kimi K3", "Nemotron 3 Ultra", "Sonar 2"),
    )
    assert (scores.scores_matched, scores.scores_dropped) == (74, 7)
    assert conn.execute(
        "SELECT effort, COUNT(*) FROM scores WHERE source = ? GROUP BY effort ORDER BY effort",
        (SOURCE_NAME,),
    ).fetchall() == [
        ("high", 13),
        ("low", 8),
        ("max", 9),
        ("medium", 9),
        ("xhigh", 10),
    ]

    coverage = {row.category: row for row in plan_coverage(conn)}
    assert (coverage["coding"].scoreable_plans, coverage["agentic-coding"].scoreable_plans) == (
        5,
        6,
    )
    assert set(coverage["agentic-coding"].scoreable) == {
        "ChatGPT Pro",
        "Google AI Plus",
        "Google AI Pro",
        "Google AI Ultra",
        "Perplexity Max",
        "Perplexity Pro",
    }

    health = plan_evidence_health(conn, CATEGORIES["agentic-coding"], today=dt.date(2026, 8, 16))
    assert (health.fresh, health.stale, health.undated, health.unscored) == (0, 0, 6, 4)
    selected = [row for row in health.plans if row.status == "undated"]
    assert all(
        row.evidence_date is None
        and row.age_days is None
        and row.evidence_source == SOURCE_NAME
        and row.harness == "mini-swe-agent"
        for row in selected
    )
    ranking = plan_ranking(conn, CATEGORIES["agentic-coding"])
    assert len(ranking) == 6
    assert all(row.effort == "high" and row.evidence_source == SOURCE_NAME for row in ranking)

    deep_health = next(
        row for row in source_health(conn, dt.date(2026, 8, 16)) if row.source == SOURCE_NAME
    )
    assert (
        deep_health.rows,
        deep_health.newest_run_date,
        deep_health.age_days,
        deep_health.stale,
    ) == (
        49,
        None,
        None,
        True,
    )

    conn.close()
    assert coverage_main(["--db", str(db), "--today", "2026-08-16"]) == 1
    payload = json.loads(capsys.readouterr().out)
    cli_coverage = {row["category"]: row for row in payload["plan_coverage"]}
    assert (
        cli_coverage["coding"]["scoreable_plans"],
        cli_coverage["agentic-coding"]["scoreable_plans"],
    ) == (5, 6)
    cli_health = next(
        row for row in payload["plan_evidence_health"] if row["category"] == "agentic-coding"
    )
    assert (
        cli_health["fresh"],
        cli_health["stale"],
        cli_health["undated"],
        cli_health["unscored"],
    ) == (0, 0, 6, 4)
    cli_source = next(row for row in payload["source_health"] if row["source"] == SOURCE_NAME)
    assert (cli_source["rows"], cli_source["newest_run_date"], cli_source["stale"]) == (
        49,
        None,
        True,
    )

    assert (
        recommend_main(
            [
                "--db",
                str(db),
                "--budget",
                "dusuk",
                "--task",
                "agentic-coding",
                "--subscription",
            ]
        )
        == 0
    )
    recommendation = json.loads(capsys.readouterr().out)
    assert recommendation["eligible_count"] == 1
    assert recommendation["excluded_by_budget"] == 5
    assert recommendation["budget_notice"] is not None
    assert "5" in recommendation["budget_notice"]
    assert "skorlanabilir plan" in recommendation["budget_notice"]
    assert any(
        "Epoch AI" in source and "CC-BY-4.0" in source for source in recommendation["sources"]
    )
