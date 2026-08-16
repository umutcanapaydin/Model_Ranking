"""REQ-ING-009: provider model rosters — a second documented source for plan links."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext
from app.workflows.plans import ingest_plans
from app.workflows.registry import reconcile_plans
from app.workflows.rosters import (
    LINK_SOURCE,
    SOURCE_NAME,
    ingest_rosters,
    main,
    parse_rosters,
    stale_rosters,
)
from app.workflows.schema import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_ROSTERS = REPO_ROOT / "data" / "rosters.yaml"
SEED_PLANS = REPO_ROOT / "data" / "plans.yaml"

PLANS = """
schema: 1
staleness_days: 30
budget_caps_usd: {dusuk: 10, orta: 25, sinirsiz: null}
plans:
  - id: quiet-plan
    provider: QuietCo
    name: Quiet Plan
    monthly_usd: 20
    currency: USD
    region: US
    limits: names no models on its own page
    included_models: []
    source_url: https://quietco.example/pricing
    last_verified: 2026-08-15
  - id: loud-plan
    provider: LoudCo
    name: Loud Plan
    monthly_usd: 30
    currency: USD
    region: US
    limits: names a model itself
    included_models: [Claude Opus 5]
    source_url: https://loudco.example/pricing
    last_verified: 2026-08-15
"""

ROSTERS = """
schema: 1
staleness_days: 30
rosters:
  - plan_id: quiet-plan
    provider: QuietCo
    source_url: https://quietco.example/help/models
    last_verified: 2026-08-15
    scope: search-models
    models: [Gemini 3.1 Pro, Totally Unknown Model X]
  - plan_id: loud-plan
    provider: LoudCo
    source_url: https://loudco.example/help/models
    last_verified: 2026-08-15
    scope: search-models
    models: [Claude Opus 5, Grok 4.5]
"""


def _db(plans: str = PLANS, rosters: str | None = ROSTERS):
    conn = connect()
    run = RunContext()
    ingest_plans(conn, plans, run)
    if rosters is not None:
        ingest_rosters(conn, rosters, run)
    return conn


def test_roster_links_a_plan_whose_page_names_nothing() -> None:
    """The whole point: a silent plan becomes rankable WITHOUT guessing."""
    conn = _db()
    rows = conn.execute(
        "SELECT raw_name, link_source, source_url, last_verified FROM plan_models"
        " WHERE plan_id = 'quiet-plan' ORDER BY raw_name"
    ).fetchall()
    assert rows == [
        ("Gemini 3.1 Pro", LINK_SOURCE, "https://quietco.example/help/models", "2026-08-15"),
        (
            "Totally Unknown Model X",
            LINK_SOURCE,
            "https://quietco.example/help/models",
            "2026-08-15",
        ),
    ]


def test_plan_page_link_wins_over_roster_and_is_counted() -> None:
    """A name the plan page states itself is the more specific statement; the
    duplicate roster entry is skipped and COUNTED, never silently dropped."""
    conn = connect()
    run = RunContext()
    ingest_plans(conn, PLANS, run)
    report = ingest_rosters(conn, ROSTERS, run)
    assert report.source == SOURCE_NAME
    assert report.stored == 3  # 4 declared - 1 already carried by the plan page
    assert report.skipped == 1
    kept = conn.execute(
        "SELECT link_source FROM plan_models WHERE plan_id='loud-plan' AND raw_name='Claude Opus 5'"
    ).fetchone()[0]
    assert kept == "plan-page"


def test_roster_links_reconcile_through_the_registry_and_count_drops() -> None:
    conn = _db()
    rep = reconcile_plans(conn)
    assert rep.dropped_names == ("Totally Unknown Model X",)
    linked = conn.execute(
        "SELECT model_id FROM plan_models WHERE raw_name = 'Gemini 3.1 Pro'"
    ).fetchone()[0]
    assert linked == "gemini-3.1-pro"


def test_roster_for_an_unknown_plan_fails_loud() -> None:
    """A link to a plan we do not carry is a curation error, not noise."""
    bad = ROSTERS.replace("plan_id: quiet-plan", "plan_id: ghost-plan")
    with pytest.raises(SourceError, match="unknown plan id"):
        _db(rosters=bad)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_url", "http://quietco.example/help"),
        ("last_verified", "15/08/2026"),
        ("provider", ""),
        ("scope", ""),  # review MINOR-1: the transcribed scope is required DATA
    ],
)
def test_invalid_roster_row_fails_loud(field: str, value: str) -> None:
    import yaml

    doc = yaml.safe_load(ROSTERS)
    doc["rosters"][0][field] = value
    with pytest.raises(SourceError):
        parse_rosters(yaml.safe_dump(doc))


def test_empty_or_duplicate_rosters_fail_loud() -> None:
    with pytest.raises(SourceError, match="not a roster"):
        parse_rosters(
            "schema: 1\nstaleness_days: 30\nrosters:\n  - plan_id: quiet-plan\n"
            "    provider: Q\n    source_url: https://q.example\n"
            "    scope: search-models\n"
            "    last_verified: 2026-08-15\n    models: []\n"
        )
    dup = ROSTERS.replace("plan_id: loud-plan", "plan_id: quiet-plan")
    with pytest.raises(SourceError, match="duplicate roster"):
        parse_rosters(dup)


def test_reingest_replaces_only_roster_links() -> None:
    """The two sources age independently; re-ingesting one must not disturb the other."""
    conn = _db()
    before = conn.execute(
        "SELECT COUNT(*) FROM plan_models WHERE link_source = 'plan-page'"
    ).fetchone()[0]
    smaller = ROSTERS.replace(
        "models: [Gemini 3.1 Pro, Totally Unknown Model X]", "models: [Grok 4.5]"
    )
    ingest_rosters(conn, smaller, RunContext())
    assert (
        conn.execute("SELECT COUNT(*) FROM plan_models WHERE link_source='plan-page'").fetchone()[0]
        == before
    )
    assert (
        conn.execute("SELECT COUNT(*) FROM plan_models WHERE plan_id='quiet-plan'").fetchone()[0]
        == 1
    )


def test_shipped_roster_file_is_valid_and_fresh_on_entry_day() -> None:
    """REQ-ING-009 citing test: the REAL data/rosters.yaml, against the real plans."""
    conn = connect()
    run = RunContext()
    ingest_plans(conn, SEED_PLANS.read_text(encoding="utf-8"), run)
    report = ingest_rosters(conn, SEED_ROSTERS.read_text(encoding="utf-8"), run)
    # Perplexity Pro (8) + Max (10) = 18 declared. Both plans carry no plan-page
    # models, so nothing overlaps and nothing is skipped — the plan-page-wins path
    # is exercised by the synthetic fixture above, not by shipped data (review MINOR-7).
    assert (report.stored, report.skipped) == (18, 0)
    assert stale_rosters(SEED_ROSTERS.read_text(encoding="utf-8"), dt.date(2026, 8, 15)) == []
    # Every roster row carries its own provenance.
    missing = conn.execute(
        "SELECT COUNT(*) FROM plan_models WHERE link_source='roster'"
        " AND (source_url IS NULL OR last_verified IS NULL)"
    ).fetchone()[0]
    assert missing == 0


def test_cli_exit_codes_through_real_entrypoint(tmp_path, capsys) -> None:
    p = tmp_path / "rosters.yaml"
    p.write_text(ROSTERS, encoding="utf-8")
    assert main(["--check-staleness", str(p), "--today", "2026-08-15"]) == 0
    assert main(["--check-staleness", str(p), "--today", "2026-12-01"]) == 1
    assert "STALE: quiet-plan" in capsys.readouterr().out
    assert main(["--check-staleness", str(tmp_path / "nope.yaml")]) == 2


# ── M4-W2 review BLOCKING-1: the tie-break and the output provenance were
# shipped WITHOUT a citing test — both fault injections stayed green. That is
# the escalate-now "stay-green fault" class, so these tests are mandatory.


def _scored_db(page_score: float, roster_score: float):
    """One plan carrying BOTH a plan-page link and a roster link, to two models."""
    conn = connect()
    run = RunContext()
    ingest_plans(
        conn,
        # Grok 4.5 sorts AFTER Claude Opus 5 alphabetically on purpose: if the
        # plan-page tie-break is removed, the display-name tie-break would pick
        # the roster model instead, so the test below actually discriminates.
        PLANS.replace("included_models: []", "included_models: [Grok 4.5]", 1),
        run,
    )
    ingest_rosters(
        conn,
        ROSTERS.replace(
            "models: [Gemini 3.1 Pro, Totally Unknown Model X]", "models: [Claude Opus 5]"
        ),
        run,
    )
    reconcile_plans(conn)
    for model_id, raw, score in (
        ("grok-4.5", "agent + Grok 4.5", page_score),
        ("claude-5-opus", "agent + Claude Opus 5", roster_score),
    ):
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    # both models need a price to be rankable
    for model_id in ("grok-4.5", "claude-5-opus"):
        conn.execute(
            "INSERT INTO px_median (model_id, in_m, out_m) VALUES (?,?,?)", (model_id, 1.0, 2.0)
        )
    return conn


def test_plan_page_link_wins_a_score_tie_and_the_pick_says_so() -> None:
    """On an EQUAL score the plan's own page is the more specific statement."""
    from app.workflows.categories import CATEGORIES
    from app.workflows.subscribe import plan_ranking

    ranking = plan_ranking(_scored_db(70.0, 70.0), CATEGORIES["coding"])
    quiet = next(r for r in ranking if r.plan_id == "quiet-plan")
    assert quiet.scored_by_model == "Grok 4.5"
    assert quiet.scored_via == "plan-page"
    assert quiet.link_source_url is None  # plan-page links use the plan's own provenance


def test_higher_scoring_roster_link_still_wins_and_carries_its_source() -> None:
    """The tie-break is a TIE-break — it must not suppress a better roster model."""
    from app.workflows.categories import CATEGORIES
    from app.workflows.subscribe import plan_ranking

    ranking = plan_ranking(_scored_db(60.0, 77.0), CATEGORIES["coding"])
    quiet = next(r for r in ranking if r.plan_id == "quiet-plan")
    assert quiet.scored_by_model == "Claude Opus 5"
    assert quiet.scored_via == "roster"
    assert quiet.link_source_url == "https://quietco.example/help/models"
    assert quiet.link_last_verified == "2026-08-15"


def test_recommendation_text_states_which_source_named_the_model() -> None:
    """REQ-ING-009 honesty half: the user is told WHERE the link came from."""
    from app.workflows.subscribe import recommend_subscription

    rec = recommend_subscription(_scored_db(60.0, 77.0), "sinirsiz", "coding")
    assert rec is not None
    quality = rec.picks[0]
    assert quality.scored_via == "roster"
    assert "sağlayıcının yayımladığı plan model listesinde" in quality.why
    assert quality.link_source_url == "https://quietco.example/help/models"
    assert quality.link_last_verified == "2026-08-15"


def test_selected_stale_roster_clock_is_disclosed_through_cli(tmp_path, capsys) -> None:
    """W-003 / REQ-REC-008: a fresh price cannot mask the selected roster link's old clock."""
    conn = _scored_db(60.0, 77.0)
    conn.execute(
        "UPDATE plans SET observed_at='2026-08-16T00:00:00+00:00'," " last_verified='2026-08-15'"
    )
    conn.execute(
        "UPDATE plan_models SET last_verified='2026-05-01'"
        " WHERE plan_id='quiet-plan' AND link_source='roster'"
    )
    conn.commit()
    db = tmp_path / "advisor.db"
    target = sqlite3.connect(db)
    conn.backup(target)
    target.close()
    conn.close()

    from app.workflows.recommend import main as recommend_main

    assert (
        recommend_main(
            ["--db", str(db), "--budget", "sinirsiz", "--task", "coding", "--subscription"]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["picks"][0]["plan"] == "Quiet Plan"
    assert payload["picks"][0]["link_last_verified"] == "2026-05-01"
    assert payload["stale_notice"] is not None
    assert "Quiet Plan" in payload["stale_notice"]
    assert "2026-05-01" in payload["stale_notice"]
    assert "roster" in payload["stale_notice"]
    assert "https://quietco.example/help/models" in payload["stale_notice"]
    assert any("Epoch AI" in source and "CC-BY-4.0" in source for source in payload["sources"])


def test_stale_unselected_roster_link_is_not_disclosed() -> None:
    """W-003: staleness follows the selected evidence row, not every candidate link."""
    from app.workflows.subscribe import recommend_subscription

    conn = _scored_db(80.0, 77.0)  # plan-page model wins for quiet-plan
    conn.execute(
        "UPDATE plan_models SET last_verified='2026-05-01'"
        " WHERE plan_id='quiet-plan' AND link_source='roster'"
    )
    rec = recommend_subscription(conn, "sinirsiz", "coding")
    assert rec is not None
    assert rec.stale_notice is None


def test_selected_roster_staleness_boundary_is_data_owned() -> None:
    """W-003: the plan-config 30-day boundary is fresh; age 31 is stale."""
    from app.workflows.subscribe import recommend_subscription

    conn = _scored_db(60.0, 77.0)
    conn.execute("UPDATE plans SET observed_at='2026-08-16T00:00:00+00:00'")
    conn.execute(
        "UPDATE plan_models SET last_verified='2026-07-17'"
        " WHERE plan_id='quiet-plan' AND link_source='roster'"
    )
    fresh = recommend_subscription(conn, "sinirsiz", "coding")
    assert fresh is not None and fresh.stale_notice is None

    conn.execute(
        "UPDATE plan_models SET last_verified='2026-07-16'"
        " WHERE plan_id='quiet-plan' AND link_source='roster'"
    )
    stale = recommend_subscription(conn, "sinirsiz", "coding")
    assert stale is not None and "2026-07-16" in (stale.stale_notice or "")


def test_migration_repairs_a_pre_wave_database(tmp_path) -> None:
    """Review MINOR-3: a persisted DB from before this wave must keep working."""
    import sqlite3

    from app.workflows.schema import migrate

    db = tmp_path / "legacy.db"
    legacy = sqlite3.connect(db)
    legacy.executescript(
        "CREATE TABLE plan_models (plan_id TEXT NOT NULL, raw_name TEXT NOT NULL,"
        " model_id TEXT, UNIQUE (plan_id, raw_name));"
    )
    legacy.execute("INSERT INTO plan_models (plan_id, raw_name) VALUES ('old-plan','Old Model')")
    legacy.commit()
    applied = migrate(legacy)
    assert applied == [
        "plan_models.link_source",
        "plan_models.source_url",
        "plan_models.last_verified",
    ]
    row = legacy.execute("SELECT plan_id, link_source, source_url FROM plan_models").fetchone()
    assert row == ("old-plan", "plan-page", None)  # existing rows default to the page source
    assert migrate(legacy) == []  # idempotent
