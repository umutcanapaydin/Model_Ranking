"""Schema contract tests (REQ-ING-004 provenance surface; K.8 shared contract)."""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows.schema import connect, migrate, reset_source


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


def test_effort_migration_preserves_pre_wave_rows_and_expands_identity(tmp_path) -> None:
    """REQ-CAN-005: a pre-W2 DB gains effort without merging distinct effort rows."""
    db = tmp_path / "pre-w2.db"
    legacy = sqlite3.connect(db)
    legacy.executescript("""
        CREATE TABLE scores (
          model_id TEXT, raw_name TEXT NOT NULL, benchmark TEXT NOT NULL,
          metric TEXT NOT NULL, score REAL NOT NULL, harness TEXT NOT NULL,
          run_date TEXT, cost_total REAL, source TEXT NOT NULL,
          source_url TEXT NOT NULL, observed_at TEXT NOT NULL,
          UNIQUE (raw_name, benchmark, metric, harness, source)
        );
        INSERT INTO scores
          (raw_name, benchmark, metric, score, harness, source, source_url, observed_at)
        VALUES ('same-model', 'DeepSWE', '% resolved', 50, 'agent', 'epoch', 'https://x', 't');
        """)
    legacy.close()

    # `connect()` is the shipped DB entrypoint and must invoke the migration.
    conn = connect(str(db))
    assert conn.execute("SELECT effort FROM scores").fetchone() == ("unspecified",)

    base = ("same-model", "DeepSWE", "% resolved", "agent", "epoch")
    for effort, score in (("high", 60.0), ("max", 75.0)):
        conn.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort,"
            " source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (base[0], base[1], base[2], score, base[3], effort, base[4], "https://x", "t"),
        )
    assert conn.execute("SELECT COUNT(*) FROM scores").fetchone() == (3,)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort,"
            " source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (base[0], base[1], base[2], 61, base[3], "high", base[4], "https://x", "t"),
        )
    assert migrate(conn) == []


def test_scores_reject_unknown_effort() -> None:
    """REQ-CAN-005: unknown effort cannot be persisted as if it were comparable."""
    conn = connect()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort,"
            " source, source_url, observed_at)"
            " VALUES ('m', 'b', '%', 1.0, 'h', 'turbo', 's', 'u', 't')"
        )


def test_reset_source_rejects_unknown_table() -> None:
    """reset_source is closed against SQL injection via table name."""
    conn = connect()
    with pytest.raises(ValueError, match="unknown table"):
        reset_source(conn, "models; DROP TABLE models", "s")
