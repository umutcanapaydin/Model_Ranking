"""Aider polyglot ingestion tests — cite REQ-ING-003 and REQ-ING-004."""

from __future__ import annotations

import pytest

from app.clients.aider import parse_polyglot, staleness_flag
from app.clients.fakes import FakeRawSource
from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, ingest_aider
from app.workflows.schema import connect

FIXTURE = """
- model: gpt-5
  pass_rate_2: 88.0
  total_cost: 12.5
  date: 2025-08-12
- model: claude-4-opus
  pass_rate_2: 72.0
  total_cost: 0.0
  date: 2025-06-01
- model: no-rate-entry
  total_cost: 1.0
- pass_rate_2: 50.0
"""


def _fake() -> FakeRawSource:
    return FakeRawSource("aider", FIXTURE)


def test_parse_skips_unusable_entries() -> None:
    """REQ-ING-003: entries without model or pass_rate_2 are skipped, not zeroed."""
    rows, skipped = parse_polyglot(FIXTURE)
    assert {r.raw_name for r in rows} == {"gpt-5", "claude-4-opus"}
    assert skipped == 2
    assert all(r.harness == "aider" for r in rows)


def test_zero_cost_becomes_null_not_zero() -> None:
    """An unreported 0.0 total_cost is stored as NULL, never as a real price."""
    rows, _ = parse_polyglot(FIXTURE)
    by_name = {r.raw_name: r for r in rows}
    assert by_name["gpt-5"].cost_total == 12.5
    assert by_name["claude-4-opus"].cost_total is None


def test_yaml_dates_normalized_to_iso_strings() -> None:
    rows, _ = parse_polyglot(FIXTURE)
    by_name = {r.raw_name: r for r in rows}
    assert by_name["gpt-5"].run_date == "2025-08-12"


def test_staleness_flag_fires_when_source_is_old() -> None:
    """REQ-ING-003: staleness is flagged relative to the run stamp, deterministically."""
    rows, _ = parse_polyglot(FIXTURE)
    flag = staleness_flag(rows, "2026-08-10T00:00:00+00:00")
    assert flag is not None
    assert "stale" in flag
    assert "2025-08-12" in flag


def test_staleness_flag_quiet_when_fresh() -> None:
    rows, _ = parse_polyglot(FIXTURE)
    assert staleness_flag(rows, "2025-08-20T00:00:00+00:00") is None


def test_ingest_surfaces_health_in_report() -> None:
    """REQ-ING-003: the run report carries the staleness flag, never hides it."""
    conn = connect()
    report = ingest_aider(conn, _fake(), RunContext(observed_at="2026-08-10T00:00:00+00:00"))
    assert report.stored == 2
    assert report.health is not None
    assert "stale" in report.health


def test_ingest_rerun_replaces_working_set() -> None:
    """REQ-ING-004: deterministic replacement for score sources too."""
    conn = connect()
    ingest_aider(conn, _fake(), RunContext(observed_at="t1"))
    ingest_aider(conn, _fake(), RunContext(observed_at="t2"))
    stamps = {
        r[0] for r in conn.execute("SELECT DISTINCT observed_at FROM scores WHERE source='aider'")
    }
    assert stamps == {"t2"}


def test_duplicate_model_runs_keep_best_score() -> None:
    """LIVE-run regression (2026-08-10): same model, multiple runs → keep best, never abort."""
    payload = """
- model: gpt-5
  pass_rate_2: 80.0
  date: 2025-05-01
- model: gpt-5
  pass_rate_2: 88.0
  date: 2025-08-12
- model: gpt-5
  pass_rate_2: 70.0
  date: 2025-02-01
"""
    rows, skipped = parse_polyglot(payload)
    assert len(rows) == 1
    assert rows[0].score == 88.0
    assert skipped == 2
    conn = connect()
    report = ingest_aider(conn, FakeRawSource("aider", payload), RunContext(observed_at="t"))
    assert report.stored == 1


def test_invalid_yaml_fails_loudly() -> None:
    with pytest.raises(SourceError, match="not valid YAML"):
        parse_polyglot("model: [broken")


def test_non_list_payload_fails_loudly() -> None:
    with pytest.raises(SourceError, match="not a list"):
        parse_polyglot("just: a-mapping")
