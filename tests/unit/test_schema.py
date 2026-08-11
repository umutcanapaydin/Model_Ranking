"""Schema contract tests (REQ-ING-004 provenance surface; K.8 shared contract)."""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows.schema import connect, reset_source


def test_schema_creates_all_tables() -> None:
    """K.8: the shared contract exposes exactly the four M1 tables."""
    conn = connect()
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"models", "pricing", "scores", "px_median"} <= tables


def test_pricing_rejects_zero_prices() -> None:
    """REQ-ING-001: a zero price cannot be stored (CHECK constraint)."""
    conn = connect()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO pricing (alias, input_per_m, output_per_m, source,"
            " source_url, observed_at) VALUES ('x', 0, 5, 's', 'u', 't')"
        )


@pytest.mark.parametrize("null_col", ["source", "source_url", "observed_at"])
def test_pricing_requires_provenance(null_col: str) -> None:
    """REQ-ING-004: source / source_url / observed_at are each NOT NULL."""
    conn = connect()
    values = {"source": "'s'", "source_url": "'u'", "observed_at": "'t'"}
    values[null_col] = "NULL"
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO pricing (alias, input_per_m, output_per_m, source,"
            f" source_url, observed_at) VALUES ('x', 1, 5, {values['source']},"
            f" {values['source_url']}, {values['observed_at']})"
        )


def test_scores_require_harness() -> None:
    """REQ-ING-002 (surface): a score without a harness cannot exist."""
    conn = connect()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness,"
            " source, source_url, observed_at)"
            " VALUES ('m', 'b', '%', 1.0, NULL, 's', 'u', 't')"
        )


def test_reset_source_rejects_unknown_table() -> None:
    """reset_source is closed against SQL injection via table name."""
    conn = connect()
    with pytest.raises(ValueError, match="unknown table"):
        reset_source(conn, "models; DROP TABLE models", "s")
