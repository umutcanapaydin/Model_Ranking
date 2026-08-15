"""REQ-SUB-001/-002: curated plan table — loud-fail validation + atomic ingest.

Curated data flips the discipline: fetched sources skip-and-count, an authored
file FAILS LOUD on any invalid row (a curation error is a bug, not noise).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext
from app.workflows.plans import SOURCE_NAME, ingest_plans, parse_plans
from app.workflows.registry import reconcile_plans
from app.workflows.schema import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "data" / "plans.yaml"

VALID = """
schema: 1
staleness_days: 30
budget_caps_usd: {dusuk: 10, orta: 25, sinirsiz: null}
plans:
  - id: test-plan
    provider: TestCo
    name: Test Plan
    monthly_usd: 20.0
    currency: USD
    region: US
    limits: "verbatim page text"
    included_models:
      - Gemini 3.1 Pro
      - Totally Unknown Model X
    source_url: https://example.com/pricing
    last_verified: 2026-08-15
"""


def _valid_with(**overrides: object) -> str:
    """Render VALID with one field replaced (string-level, keeps YAML simple)."""
    import yaml

    doc = yaml.safe_load(VALID)
    doc["plans"][0].update(overrides)
    return yaml.safe_dump(doc)


def test_parse_valid_plan_roundtrips_all_fields() -> None:
    rows = parse_plans(VALID)
    assert len(rows) == 1
    row = rows[0]
    assert row.id == "test-plan"
    assert row.monthly_usd == 20.0
    assert row.included_models == ("Gemini 3.1 Pro", "Totally Unknown Model X")
    assert row.source_url.startswith("https://")
    assert row.last_verified == "2026-08-15"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("last_verified", ""),  # REQ-SUB-003: a row without last_verified fails loud
        ("last_verified", "15/08/2026"),
        ("source_url", "http://example.com"),  # https only
        ("monthly_usd", 0),  # free tiers out of scope; CHECK > 0
        ("monthly_usd", -5),
        ("monthly_usd", True),  # bool is not a price (M1 rule 3 shape)
        ("limits", ""),
        ("id", "Bad_ID"),
    ],
)
def test_invalid_row_fails_loud(field: str, value: object) -> None:
    with pytest.raises(SourceError):
        parse_plans(_valid_with(**{field: value}))


def test_duplicate_plan_id_fails_loud() -> None:
    import yaml

    doc = yaml.safe_load(VALID)
    doc["plans"].append(dict(doc["plans"][0]))
    with pytest.raises(SourceError, match="duplicate plan id"):
        parse_plans(yaml.safe_dump(doc))


def test_empty_table_fails_loud() -> None:
    with pytest.raises(SourceError, match="empty curated table"):
        parse_plans(
            "schema: 1\nstaleness_days: 30\n"
            "budget_caps_usd: {dusuk: 10, orta: 25, sinirsiz: null}\nplans: []\n"
        )


def test_wrong_schema_version_fails_loud() -> None:
    with pytest.raises(SourceError, match="schema"):
        parse_plans("schema: 99\nplans: []\n")


def test_missing_staleness_window_fails_loud() -> None:
    """REQ-SUB-003: the window is DATA — a code default would be the M2-W4 debt class."""
    with pytest.raises(SourceError, match="staleness_days"):
        parse_plans(VALID.replace("staleness_days: 30\n", ""))


def test_missing_or_malformed_budget_caps_fail_loud() -> None:
    """REQ-REC-007: budget tiers are DATA; a code default is the same debt class."""
    with pytest.raises(SourceError, match="budget_caps_usd"):
        parse_plans(VALID.replace("budget_caps_usd: {dusuk: 10, orta: 25, sinirsiz: null}\n", ""))
    with pytest.raises(SourceError, match="dusuk < orta"):
        parse_plans(VALID.replace("{dusuk: 10, orta: 25", "{dusuk: 25, orta: 10"))
    with pytest.raises(SourceError, match="sinirsiz"):
        parse_plans(VALID.replace("sinirsiz: null", "sinirsiz: 999"))


def test_ingest_replaces_working_set_atomically() -> None:
    conn = connect()
    run = RunContext()
    report = ingest_plans(conn, VALID, run)
    assert report.source == SOURCE_NAME
    assert report.stored == 1
    assert report.skipped == 0
    # Re-ingest with a changed price: the working set is REPLACED, not appended.
    ingest_plans(conn, _valid_with(monthly_usd=25.0), run)
    rows = conn.execute("SELECT monthly_usd FROM plans").fetchall()
    assert rows == [(25.0,)]
    links = conn.execute("SELECT COUNT(*) FROM plan_models").fetchone()[0]
    assert links == 2  # replaced alongside, no duplicates


def test_failed_ingest_keeps_previous_working_set() -> None:
    conn = connect()
    run = RunContext()
    ingest_plans(conn, VALID, run)
    with pytest.raises(SourceError):
        ingest_plans(conn, _valid_with(monthly_usd=0), run)
    # Parse failed BEFORE any delete — the old set must survive (fail closed).
    assert conn.execute("SELECT COUNT(*) FROM plans").fetchone()[0] == 1


def test_reconcile_plans_links_explicit_names_and_counts_drops() -> None:
    """M1 rule 4 applied to plans: link only what a registry rule matches."""
    conn = connect()
    ingest_plans(conn, VALID, RunContext())
    report = reconcile_plans(conn)
    assert report.matched == 1  # Gemini 3.1 Pro -> gemini-3.1-pro (own id since M4-W1)
    assert report.dropped == 1  # Totally Unknown Model X: counted, never guessed
    assert report.dropped_names == ("Totally Unknown Model X",)
    linked = conn.execute(
        "SELECT model_id FROM plan_models WHERE raw_name = 'Gemini 3.1 Pro'"
    ).fetchone()[0]
    assert linked == "gemini-3.1-pro"
    unlinked = conn.execute(
        "SELECT model_id FROM plan_models WHERE raw_name = 'Totally Unknown Model X'"
    ).fetchone()[0]
    assert unlinked is None
    # The matched model is registered in models (visible to future ranking joins).
    assert conn.execute("SELECT vendor FROM models WHERE id='gemini-3.1-pro'").fetchone() == (
        "Google",
    )


def test_seed_dataset_meets_req_sub_002() -> None:
    """REQ-SUB-002 citing test: the REAL shipped seed parses and meets scope."""
    rows = parse_plans(SEED_PATH.read_text(encoding="utf-8"))
    assert len(rows) >= 10  # 9 at M3 + Google AI Plus, entered at M4-W4 (REQ-SUB-006)
    providers = {r.provider for r in rows}
    assert {"OpenAI", "Anthropic", "Google", "Perplexity"} <= providers
    for row in rows:  # REQ-SUB-003 half: provenance mandatory on every row
        assert row.source_url.startswith("https://")
        assert row.last_verified  # validated as a date by the parser
        assert row.currency == "USD"  # owner Q2: USD-first, no conversion
        assert row.monthly_usd > 0
    # Q1 scope sanity: the flagship $20 tiers are present.
    ids = {r.id for r in rows}
    assert {"chatgpt-plus", "claude-pro", "google-ai-pro", "perplexity-pro"} <= ids


def test_sub_dollar_price_survives_the_seed_exactly() -> None:
    """W4 review MINOR-5 citing test: REQ-SUB-006's price is $4.99, and it must STAY $4.99.

    Google AI Plus is the first sub-$10 fractional price in the table, and the cheapest
    plan in it — so it is the row the budget pick lands on. An int coercion, or a stray
    `round()` on the way through the store, would move the number the owner is asked to
    verify against the vendor's page. The parser and the database are both asserted.
    """
    rows = {r.id: r for r in parse_plans(SEED_PATH.read_text(encoding="utf-8"))}
    assert rows["google-ai-plus"].monthly_usd == 4.99
    conn = connect()
    ingest_plans(conn, SEED_PATH.read_text(encoding="utf-8"), RunContext())
    stored = conn.execute("SELECT monthly_usd FROM plans WHERE id = 'google-ai-plus'").fetchone()
    assert stored[0] == 4.99
    # ...and it is the table's minimum, i.e. the value a budget answer actually returns.
    assert conn.execute("SELECT MIN(monthly_usd) FROM plans").fetchone()[0] == 4.99


def test_seed_dataset_ingests_and_reconciles_end_to_end() -> None:
    conn = connect()
    run = RunContext()
    report = ingest_plans(conn, SEED_PATH.read_text(encoding="utf-8"), run)
    assert report.stored >= 6
    rec = reconcile_plans(conn)
    # M4-W1: the GPT-5.6 family and the dotted Gemini versions now have rules, so
    # every name the seed's pages state EXPLICITLY links — zero drops.
    assert rec.matched == 4  # GPT-5.6, GPT-5.6 Sol Pro, Gemini 3.1 Pro, Gemini 3 Pro
    assert rec.dropped_names == ()
    linked = conn.execute(
        "SELECT plan_id, raw_name, model_id FROM plan_models WHERE model_id IS NOT NULL"
        " ORDER BY plan_id, raw_name"
    ).fetchall()
    assert linked == [
        ("chatgpt-plus", "GPT-5.6", "gpt-5.6"),
        ("chatgpt-pro", "GPT-5.6 Sol Pro", "gpt-5.6-sol"),
        ("google-ai-plus", "Gemini 3.1 Pro", "gemini-3.1-pro"),
        ("google-ai-pro", "Gemini 3 Pro", "gemini-3-pro"),
        ("google-ai-pro", "Gemini 3.1 Pro", "gemini-3.1-pro"),
        ("google-ai-ultra", "Gemini 3.1 Pro", "gemini-3.1-pro"),
    ]


def test_schema_check_rejects_nonpositive_price_at_sqlite_layer() -> None:
    """REQ-SUB-001: the DDL CHECK itself, not only the parse gate (review MINOR-2)."""
    import sqlite3

    conn = connect()
    for bad in (0, -1):
        with pytest.raises(sqlite3.IntegrityError, match="monthly_usd"):
            conn.execute(
                "INSERT INTO plans (id, provider, name, monthly_usd, currency, region,"
                " limits, source_url, last_verified, observed_at)"
                " VALUES ('x-plan','X','X',?,'USD','US','x','https://x','2026-08-15','now')",
                (bad,),
            )


def test_infinite_price_fails_loud() -> None:
    """Review MINOR-1: .inf must not pass validation and reach the DB."""
    with pytest.raises(SourceError, match="finite"):
        parse_plans(VALID.replace("monthly_usd: 20.0", "monthly_usd: .inf"))


def test_validator_does_not_mutate_input() -> None:
    """Review MINOR-4: parse must not edit the caller's document."""
    import yaml

    doc = yaml.safe_load(VALID)
    before = repr(doc)
    parse_plans(yaml.safe_dump(doc))
    assert repr(doc) == before


def test_mid_transaction_failure_keeps_previous_working_set() -> None:
    """M3 security review NOTE-1 (INV-12 citing test): a failure AFTER the delete,
    mid-insert, must roll the whole replacement back — the old set survives."""

    conn = connect()
    ingest_plans(conn, VALID, RunContext())
    # A trigger that rejects the incoming row forces an IntegrityError INSIDE
    # the replacement transaction (parse passes; the DB itself fails).
    conn.execute(
        "CREATE TRIGGER reject_replacement BEFORE INSERT ON plans"
        " WHEN NEW.monthly_usd = 25.0"
        " BEGIN SELECT RAISE(ABORT, 'injected mid-transaction fault'); END"
    )
    with pytest.raises(SourceError, match="violates schema constraints"):
        ingest_plans(conn, _valid_with(monthly_usd=25.0), RunContext())
    row = conn.execute("SELECT monthly_usd FROM plans").fetchall()
    assert row == [(20.0,)]  # the OLD set, untouched
    assert conn.execute("SELECT COUNT(*) FROM plan_models").fetchone()[0] == 2
    cfg = conn.execute("SELECT staleness_days FROM plan_config WHERE id=1").fetchone()
    assert cfg == (30,)
