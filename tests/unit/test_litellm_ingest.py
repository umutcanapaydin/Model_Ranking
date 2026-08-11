"""LiteLLM ingestion tests — cite REQ-ING-001 and REQ-ING-004 (partial)."""

from __future__ import annotations

import json

import pytest

from app.clients.fakes import FakeRawSource
from app.clients.litellm import parse_pricing
from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, ingest_litellm
from app.workflows.schema import connect

FIXTURE = json.dumps(
    {
        "gpt-5": {
            "mode": "chat",
            "input_cost_per_token": 1.25e-06,
            "output_cost_per_token": 1e-05,
            "max_input_tokens": 272000,
        },
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
        "missing-output": {"mode": "chat", "input_cost_per_token": 1e-06},
        "zero-price": {"mode": "chat", "input_cost_per_token": 0, "output_cost_per_token": 0},
        "an-embedding": {
            "mode": "embedding",
            "input_cost_per_token": 1e-07,
            "output_cost_per_token": 1e-07,
        },
        "sample_spec": "not-a-dict",
    }
)


def _fake() -> FakeRawSource:
    return FakeRawSource("litellm", FIXTURE)


def test_parse_skips_unpriced_and_nonchat_entries() -> None:
    """REQ-ING-001: missing/zero prices and non-chat modes are SKIPPED, not zeroed."""
    rows, skipped = parse_pricing(FIXTURE)
    aliases = {r.alias for r in rows}
    assert aliases == {"gpt-5", "claude-4-5-opus"}
    assert skipped == 4


def test_parse_converts_to_per_million() -> None:
    """REQ-ING-001: prices are stored as $/1M tokens."""
    rows, _ = parse_pricing(FIXTURE)
    gpt5 = next(r for r in rows if r.alias == "gpt-5")
    assert gpt5.input_per_m == pytest.approx(1.25)
    assert gpt5.output_per_m == pytest.approx(10.0)
    assert gpt5.context == 272000


def test_ingest_stores_rows_with_provenance() -> None:
    """REQ-ING-001 + REQ-ING-004: rows land with non-null provenance + run stamp."""
    conn = connect()
    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    report = ingest_litellm(conn, _fake(), run)
    assert report.stored == 2
    assert report.skipped == 4
    rows = conn.execute("SELECT source, source_url, observed_at FROM pricing").fetchall()
    assert len(rows) == 2
    assert all(all(v is not None for v in row) for row in rows)
    assert {r[2] for r in rows} == {"2026-08-10T00:00:00+00:00"}


def test_ingest_rerun_is_deterministic() -> None:
    """REQ-ING-004: a re-run REPLACES the working set (no accumulation, no leftovers)."""
    conn = connect()
    ingest_litellm(conn, _fake(), RunContext(observed_at="t1"))
    ingest_litellm(conn, _fake(), RunContext(observed_at="t2"))
    n = conn.execute("SELECT COUNT(*) FROM pricing").fetchone()[0]
    assert n == 2
    stamps = {r[0] for r in conn.execute("SELECT DISTINCT observed_at FROM pricing")}
    assert stamps == {"t2"}, "t1 rows must be replaced, not kept"


def test_failed_insert_rolls_back_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transaction semantics: a mid-insert failure must not leave a half-replaced set."""
    import app.workflows.ingest as ing
    from app.workflows.schema import PricingRow

    conn = connect()
    ingest_litellm(conn, _fake(), RunContext(observed_at="t1"))

    def bad_parse(raw: str, **kw: str) -> tuple[list[PricingRow], int]:
        return [PricingRow("bad", -1.0, 5.0, None, "litellm", "fixture://payload")], 0

    monkeypatch.setattr(ing, "parse_pricing", bad_parse)
    with pytest.raises(Exception, match="CHECK constraint"):
        ingest_litellm(conn, _fake(), RunContext(observed_at="t2"))
    stamps = {r[0] for r in conn.execute("SELECT DISTINCT observed_at FROM pricing")}
    assert stamps == {"t1"}, "old working set must survive a failed re-run"


def test_parse_skips_bool_and_negative_prices() -> None:
    """REQ-ING-001 edge: JSON true / negative prices are skipped, never stored."""
    payload = json.dumps(
        {
            "bool-price": {
                "mode": "chat",
                "input_cost_per_token": True,
                "output_cost_per_token": 1e-06,
            },
            "negative": {
                "mode": "chat",
                "input_cost_per_token": -1e-06,
                "output_cost_per_token": 1e-06,
            },
        }
    )
    rows, skipped = parse_pricing(payload)
    assert rows == []
    assert skipped == 2


def test_invalid_json_raises_source_error() -> None:
    """Architecture §3: a bad payload aborts THIS source loudly."""
    with pytest.raises(SourceError, match="not valid JSON"):
        parse_pricing("{broken")


def test_failing_source_propagates() -> None:
    """A fetch failure surfaces as SourceError; nothing is written."""
    conn = connect()
    with pytest.raises(SourceError, match="configured to fail"):
        ingest_litellm(conn, FakeRawSource("litellm", None), RunContext())
    assert conn.execute("SELECT COUNT(*) FROM pricing").fetchone()[0] == 0
