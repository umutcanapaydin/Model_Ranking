"""Schema contract tests (REQ-ING-004 provenance surface; K.8 shared contract)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from app.workflows.schema import connect, main, migrate, reset_source


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


def test_explicit_migrate_cli_preserves_legacy_rows_and_is_idempotent(tmp_path, capsys) -> None:
    """W-004 / REQ-CAN-005: the operator command reaches migration without mutating read CLIs."""
    db = tmp_path / "legacy.db"
    legacy = sqlite3.connect(db)
    legacy.executescript(
        "CREATE TABLE plan_models (plan_id TEXT NOT NULL, raw_name TEXT NOT NULL,"
        " model_id TEXT, UNIQUE (plan_id, raw_name));"
        "INSERT INTO plan_models (plan_id, raw_name) VALUES ('old-plan', 'Old Model');"
        "CREATE TABLE scores (model_id TEXT, raw_name TEXT NOT NULL, benchmark TEXT NOT NULL,"
        " metric TEXT NOT NULL, score REAL NOT NULL, harness TEXT NOT NULL, run_date TEXT,"
        " cost_total REAL, source TEXT NOT NULL, source_url TEXT NOT NULL, observed_at TEXT NOT NULL,"
        " UNIQUE (raw_name, benchmark, metric, harness, source));"
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, source, source_url,"
        " observed_at) VALUES ('old-model', 'DeepSWE', '% resolved', 50, 'agent', 'epoch',"
        " 'https://x', 't');"
    )
    legacy.close()

    assert main(["migrate", "--db", str(db)]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["applied"] == [
        "plan_models.link_source",
        "plan_models.source_url",
        "plan_models.last_verified",
        "scores.effort",
    ]
    assert first["applied_count"] == 4

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT plan_id, raw_name, link_source FROM plan_models").fetchone() == (
        "old-plan",
        "Old Model",
        "plan-page",
    )
    assert conn.execute("SELECT raw_name, effort FROM scores").fetchone() == (
        "old-model",
        "unspecified",
    )
    conn.close()

    assert main(["migrate", "--db", str(db)]) == 0
    assert json.loads(capsys.readouterr().out)["applied"] == []


def test_explicit_migrate_cli_refuses_missing_or_non_database_file(tmp_path, capsys) -> None:
    """W-004: an operator typo must not create a new empty database or hide invalid input."""
    missing = tmp_path / "missing.db"
    assert main(["migrate", "--db", str(missing)]) == 2
    assert not missing.exists()
    assert "db not found" in json.loads(capsys.readouterr().out)["error"]

    broken = tmp_path / "broken.db"
    broken.write_text("not sqlite", encoding="utf-8")
    assert main(["migrate", "--db", str(broken)]) == 2
    assert "db unusable" in json.loads(capsys.readouterr().out)["error"]


def test_explicit_migrate_cli_refuses_invalid_legacy_rows_without_writing(tmp_path, capsys) -> None:
    """W-004: an invalid legacy row is rejected before DDL touches the owner database."""
    db = tmp_path / "invalid-legacy.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE scores (model_id TEXT, raw_name TEXT NOT NULL, benchmark TEXT NOT NULL,"
        " metric TEXT NOT NULL, score REAL NOT NULL, harness TEXT NOT NULL, effort TEXT NOT NULL,"
        " run_date TEXT, cost_total REAL, source TEXT NOT NULL, source_url TEXT NOT NULL,"
        " observed_at TEXT NOT NULL, UNIQUE (raw_name, benchmark, metric, harness, source));"
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source,"
        " source_url, observed_at) VALUES ('old-model', 'DeepSWE', '% resolved', 50, 'agent',"
        " 'turbo', 'epoch', 'https://x', 't');"
    )
    before_schema = conn.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
    ).fetchall()
    before_rows = conn.execute("SELECT * FROM scores").fetchall()
    conn.close()
    before_bytes = db.read_bytes()

    assert main(["migrate", "--db", str(db)]) == 2
    assert "unsupported effort" in json.loads(capsys.readouterr().out)["error"]
    assert db.read_bytes() == before_bytes

    unchanged = sqlite3.connect(db)
    assert (
        unchanged.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
        == before_schema
    )
    assert unchanged.execute("SELECT * FROM scores").fetchall() == before_rows
    assert unchanged.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='scores__m5_effort'"
    ).fetchone() == (0,)
    unchanged.close()


def test_explicit_migrate_cli_rolls_back_a_failure_after_score_rebuild_starts(
    tmp_path, capsys
) -> None:
    """W-004: DDL and the score-table rebuild are one transaction, including late failure."""
    db = tmp_path / "late-failure.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE scores (model_id TEXT, raw_name TEXT NOT NULL, benchmark TEXT NOT NULL,"
        " metric TEXT NOT NULL, score REAL NOT NULL, harness TEXT NOT NULL, effort TEXT NOT NULL,"
        " run_date TEXT, cost_total REAL, source TEXT NOT NULL, source_url TEXT NOT NULL,"
        " observed_at TEXT NOT NULL, UNIQUE (raw_name, benchmark, metric, harness, source));"
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source,"
        " source_url, observed_at) VALUES ('old-model', 'DeepSWE', '% resolved', 50, 'agent',"
        " 'high', 'epoch', 'https://x', 't');"
        "CREATE TABLE shadow (model_id TEXT);"
        "CREATE INDEX idx_scores_model ON shadow(model_id);"
    )
    before_schema = conn.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
    ).fetchall()
    before_rows = conn.execute("SELECT * FROM scores").fetchall()
    conn.close()
    before_bytes = db.read_bytes()

    assert main(["migrate", "--db", str(db)]) == 2
    assert "already exists" in json.loads(capsys.readouterr().out)["error"]
    assert db.read_bytes() == before_bytes

    unchanged = sqlite3.connect(db)
    assert (
        unchanged.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
        == before_schema
    )
    assert unchanged.execute("SELECT * FROM scores").fetchall() == before_rows
    assert unchanged.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='scores__m5_effort'"
    ).fetchone() == (0,)
    unchanged.close()


def test_reset_source_rejects_unknown_table() -> None:
    """reset_source is closed against SQL injection via table name."""
    conn = connect()
    with pytest.raises(ValueError, match="unknown table"):
        reset_source(conn, "models; DROP TABLE models", "s")


def test_explicit_migrate_cli_refuses_a_legacy_table_it_cannot_repair(tmp_path, capsys) -> None:
    """W4 review BLOCKING-1: exit 0 must never be printed over a database the read
    paths cannot use.

    The first cut validated exactly two tables by hand, so a pre-M3 `plans` missing
    `observed_at` migrated "successfully" — and the next `recommend --subscription`
    died with `no such column: observed_at`, which is the precise symptom W-004 was
    written to remove. The validator now derives its requirement from the shipped DDL,
    so a column added tomorrow is covered tomorrow.
    """
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE plans (
            id TEXT PRIMARY KEY, provider TEXT, name TEXT, monthly_usd REAL,
            currency TEXT, region TEXT, limits TEXT, source_url TEXT, last_verified TEXT
        );
        CREATE TABLE plan_models (plan_id TEXT, raw_name TEXT, model_id TEXT);
        """)
    conn.execute(
        "INSERT INTO plans VALUES ('p','Prov','Plan',9.99,'USD','US','x','https://x','2026-08-15')"
    )
    conn.commit()
    conn.close()
    before = db.read_bytes()

    assert main(["migrate", "--db", str(db)]) == 2
    error = json.loads(capsys.readouterr().out)["error"]
    assert "plans" in error and "observed_at" in error
    assert db.read_bytes() == before  # refused BEFORE the first write


def test_migration_validator_requirements_are_derived_from_the_shipped_ddl() -> None:
    """The guard above is only as good as its source: prove it reads the real DDL.

    A hand-maintained copy of the schema drifts from the schema — that drift is what
    BLOCKING-1 was. Every table the DDL declares must be covered, and the only columns
    exempt are the ones a migration can actually add.
    """
    from app.workflows.schema import _MIGRATIONS, _ddl_columns

    ddl = _ddl_columns()
    assert {
        "models",
        "pricing",
        "scores",
        "px_median",
        "plans",
        "plan_config",
        "plan_models",
    } <= set(ddl)
    assert "observed_at" in ddl["plans"]  # the column BLOCKING-1 let through
    migratable = {column for _, column, _ in _MIGRATIONS} | {"effort"}
    # Anything NOT addable by a migration must be demanded of an existing table.
    assert "observed_at" not in migratable
    assert "link_source" in migratable  # M4-W2 added it to an existing table


def test_ddl_applier_survives_a_trailing_comment() -> None:
    """W4 review MINOR-5: a comment must never take the application down.

    `_apply_ddl` hand-splits the DDL (deliberately — `executescript` would commit the
    open transaction). Its leftover check treated a comment-only remainder as an
    incomplete statement, so adding a trailing `-- note` line to DDL made every
    `connect()` raise.
    """
    import app.workflows.schema as schema_module

    original = schema_module.DDL
    try:
        schema_module.DDL = original + "-- a maintainer's note\n"
        conn = schema_module.connect()
        assert conn.execute("SELECT COUNT(*) FROM plans").fetchone() == (0,)
        conn.close()
    finally:
        schema_module.DDL = original
