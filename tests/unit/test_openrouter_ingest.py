"""OpenRouter pricing ingestion tests — cite REQ-ING-005 and REQ-ING-004."""

from __future__ import annotations

import json

import pytest

from app.clients.fakes import FakeRawSource
from app.clients.openrouter import parse_models
from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, ingest_openrouter
from app.workflows.schema import connect

FIXTURE = json.dumps(
    {
        "data": [
            {
                "id": "openai/gpt-5",
                "pricing": {"prompt": "0.00000125", "completion": "0.00001"},
                "context_length": 272000,
            },
            {
                "id": "anthropic/claude-4.5-opus",
                "pricing": {"prompt": "0.000005", "completion": "0.000025"},
            },
            {"id": "free/model", "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "broken/model", "pricing": {"prompt": "abc", "completion": "0.00001"}},
            {"id": "no-pricing/model"},
            "not-a-dict",
        ]
    }
)


def _fake() -> FakeRawSource:
    return FakeRawSource("openrouter", FIXTURE)


def test_parse_converts_string_prices_to_per_million() -> None:
    """REQ-ING-005: string $/token → float $/1M; free/unpriced skipped."""
    rows, skipped = parse_models(FIXTURE)
    by_alias = {r.alias: r for r in rows}
    assert set(by_alias) == {"openai/gpt-5", "anthropic/claude-4.5-opus"}
    assert by_alias["openai/gpt-5"].input_per_m == pytest.approx(1.25)
    assert by_alias["openai/gpt-5"].output_per_m == pytest.approx(10.0)
    assert by_alias["openai/gpt-5"].context == 272000
    assert skipped == 4  # free + broken + no-pricing + not-a-dict


def test_free_models_never_stored_as_zero() -> None:
    """REQ-ING-005: a 0-price entry is skipped, not stored (schema CHECK backs this)."""
    rows, _ = parse_models(FIXTURE)
    assert all(r.input_per_m > 0 and r.output_per_m > 0 for r in rows)


def test_ingest_stores_with_provenance_and_replaces() -> None:
    """REQ-ING-004: provenance stamped; re-run replaces the openrouter set only."""
    conn = connect()
    ingest_openrouter(conn, _fake(), RunContext(observed_at="t1"))
    report = ingest_openrouter(conn, _fake(), RunContext(observed_at="t2"))
    assert report.stored == 2
    stamps = {
        r[0]
        for r in conn.execute("SELECT DISTINCT observed_at FROM pricing WHERE source='openrouter'")
    }
    assert stamps == {"t2"}


def test_sources_replace_independently() -> None:
    """REQ-ING-004/-006: re-running openrouter must not touch litellm's rows."""
    from app.workflows.ingest import ingest_litellm

    conn = connect()
    litellm_payload = json.dumps(
        {
            "gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 1.25e-06,
                "output_cost_per_token": 1e-05,
            }
        }
    )
    ingest_litellm(conn, FakeRawSource("litellm", litellm_payload), RunContext(observed_at="L1"))
    ingest_openrouter(conn, _fake(), RunContext(observed_at="O1"))
    ingest_openrouter(conn, _fake(), RunContext(observed_at="O2"))
    litellm_stamp = conn.execute(
        "SELECT DISTINCT observed_at FROM pricing WHERE source='litellm'"
    ).fetchall()
    assert litellm_stamp == [("L1",)]


def test_duplicate_ids_do_not_abort_source() -> None:
    payload = json.dumps(
        {
            "data": [
                {"id": "x/y", "pricing": {"prompt": "0.000001", "completion": "0.000002"}},
                {"id": "x/y", "pricing": {"prompt": "0.000009", "completion": "0.000009"}},
            ]
        }
    )
    rows, skipped = parse_models(payload)
    assert len(rows) == 1
    assert skipped == 1


def test_price_string_edge_cases() -> None:
    """W1 review: '-1', '', '1e-3' price strings handled safely."""
    payload = json.dumps(
        {
            "data": [
                {"id": "neg/m", "pricing": {"prompt": "-1", "completion": "0.000001"}},
                {"id": "empty/m", "pricing": {"prompt": "", "completion": "0.000001"}},
                {"id": "exp/m", "pricing": {"prompt": "1e-06", "completion": "2e-06"}},
            ]
        }
    )
    rows, skipped = parse_models(payload)
    assert [r.alias for r in rows] == ["exp/m"]
    assert rows[0].input_per_m == pytest.approx(1.0)
    assert skipped == 2


def test_malformed_payload_fails_loudly() -> None:
    with pytest.raises(SourceError, match="malformed"):
        parse_models('{"nope": 1}')
    with pytest.raises(SourceError, match="not a list"):
        parse_models('{"data": "oops"}')
