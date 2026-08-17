"""Database schema for model_ranking (M1) — shared contract, K.8.

Plain sqlite3 DDL + typed row containers. The SQLite file is disposable and
rebuilt from sources on every pipeline run (D-100). Every changing record
carries provenance fields (REQ-ING-004): ``source``, ``source_url``,
``observed_at``.

Tables
------
models      canonical model registry (filled in W3, REQ-CAN-001)
pricing     per-alias API prices from pricing sources (W1, REQ-ING-001)
scores      benchmark score records — model+harness+effort evidence (REQ-CAN-005)
px_median   median reference price per canonical model (W3, REQ-CAN-003)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS models (
    id      TEXT PRIMARY KEY,
    display TEXT NOT NULL,
    vendor  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pricing (
    alias        TEXT NOT NULL,
    model_id     TEXT,                -- canonical id; NULL until W3 reconciliation
    input_per_m  REAL NOT NULL CHECK (input_per_m  > 0),
    output_per_m REAL NOT NULL CHECK (output_per_m > 0),
    context      INTEGER,
    source       TEXT NOT NULL,
    source_url   TEXT NOT NULL,
    observed_at  TEXT NOT NULL,
    UNIQUE (alias, source)
);
CREATE TABLE IF NOT EXISTS scores (
    model_id    TEXT,                 -- canonical id; NULL until W3 reconciliation
    raw_name    TEXT NOT NULL,
    benchmark   TEXT NOT NULL,
    metric      TEXT NOT NULL,
    score       REAL NOT NULL,
    harness     TEXT NOT NULL,
    effort      TEXT NOT NULL DEFAULT 'unspecified'
                CHECK (effort IN ('unspecified','low','medium','high','xhigh','max')),
    run_date    TEXT,
    cost_total  REAL,
    source      TEXT NOT NULL,
    source_url  TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    UNIQUE (raw_name, benchmark, metric, harness, effort, source)
);
CREATE INDEX IF NOT EXISTS idx_pricing_model ON pricing (model_id);
CREATE INDEX IF NOT EXISTS idx_scores_model  ON scores  (model_id);
CREATE TABLE IF NOT EXISTS px_median (
    model_id TEXT PRIMARY KEY,
    in_m     REAL NOT NULL,
    out_m    REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
    id            TEXT PRIMARY KEY,
    provider      TEXT NOT NULL,
    name          TEXT NOT NULL,
    monthly_usd   REAL NOT NULL CHECK (monthly_usd > 0),
    currency      TEXT NOT NULL,
    region        TEXT NOT NULL,
    limits        TEXT NOT NULL,          -- verbatim from the provider page, never paraphrased
    source_url    TEXT NOT NULL,
    last_verified TEXT NOT NULL,          -- YYYY-MM-DD; staleness disclosure rides on this (M3)
    observed_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plan_config (
    id             INTEGER PRIMARY KEY CHECK (id = 1),   -- single row
    staleness_days INTEGER NOT NULL CHECK (staleness_days > 0),
    -- REQ-SUB-008 / W-008: the ROSTER's own window, separate from the plan table's above. They are
    -- both 30 on shipped data, which is why borrowing one for the other stayed invisible: the
    -- product would call a roster link stale that the roster's own policy calls fresh, and every
    -- gate would stay green. Nullable so a pre-M6 database migrates without inventing a policy;
    -- `roster_staleness_days()` is where the absence is resolved, loudly.
    roster_staleness_days INTEGER CHECK (roster_staleness_days IS NULL OR roster_staleness_days > 0),
    cap_dusuk      REAL NOT NULL CHECK (cap_dusuk > 0),  -- monthly-USD budget caps (data, not code)
    cap_orta       REAL NOT NULL CHECK (cap_orta > cap_dusuk)
);
CREATE TABLE IF NOT EXISTS plan_models (
    plan_id       TEXT NOT NULL,
    raw_name      TEXT NOT NULL,          -- model name exactly as the page states it
    model_id      TEXT,                   -- canonical id; NULL until reconcile_plans (drops counted)
    -- Where the LINK came from (M4-W2). 'plan-page' = the plan's own pricing page
    -- named the model; 'roster' = the provider's separate documented model list.
    -- A link without provenance is a guess, and this product does not guess.
    link_source   TEXT NOT NULL DEFAULT 'plan-page',
    source_url    TEXT,                   -- set for roster links (the plan carries its own)
    last_verified TEXT,                   -- set for roster links; roster rows age on their own clock
    UNIQUE (plan_id, raw_name)
);
CREATE INDEX IF NOT EXISTS idx_plan_models_plan ON plan_models (plan_id);
"""


@dataclass(frozen=True)
class PricingRow:
    """One priced model alias from a pricing source (REQ-ING-001)."""

    alias: str
    input_per_m: float
    output_per_m: float
    context: int | None
    source: str
    source_url: str


@dataclass(frozen=True)
class PlanRow:
    """One subscription plan from the curated table (REQ-SUB-001).

    Curated data is authored, not fetched: any invalid row FAILS LOUD at parse
    (SourceError), never skip-and-count — a curation error is a bug, not noise.
    """

    id: str
    provider: str
    name: str
    monthly_usd: float
    currency: str
    region: str
    limits: str
    included_models: tuple[str, ...]  # ONLY names the page explicitly states — never guessed
    source_url: str
    last_verified: str


@dataclass(frozen=True)
class ScoreRow:
    """One benchmark score record; harness and effort identity are explicit."""

    raw_name: str
    benchmark: str
    metric: str
    score: float
    harness: str
    run_date: str | None
    cost_total: float | None
    source: str
    source_url: str
    effort: str | None = None


# Columns added to EXISTING tables after M1. `CREATE TABLE IF NOT EXISTS` cannot add
# them to a database that already exists, so a disposable-but-persisted advisor.db
# from an earlier milestone would fail with "no such column" (M4-W2 review MINOR-3).
# Migrations are idempotent and preserve rows. Most are additive; the effort migration
# explicitly rebuilds the disposable scores table because SQLite cannot alter UNIQUE.
_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    ("plan_models", "link_source", "TEXT NOT NULL DEFAULT 'plan-page'"),
    ("plan_models", "source_url", "TEXT"),
    ("plan_models", "last_verified", "TEXT"),
    # M6-W3 / REQ-SUB-008. Nullable and no DEFAULT on purpose: a default would silently give an old
    # database a roster policy nobody set, which is the shape of the defect this column exists to
    # remove. An unmigrated row reads as "unset" and `roster_staleness_days()` says so.
    ("plan_config", "roster_staleness_days", "INTEGER"),
)

EFFORT_UNSPECIFIED = "unspecified"
EFFORT_LEVELS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")


def _scores_effort_schema(conn: sqlite3.Connection) -> bool:
    """Whether ``scores`` has the W2 effort column and effort-aware identity."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(scores)")}
    if not columns:
        return True  # DDL will create a complete table later.
    if "effort" not in columns:
        return False
    for row in conn.execute("PRAGMA index_list(scores)"):
        if not row[2]:  # not UNIQUE
            continue
        indexed = tuple(item[2] for item in conn.execute(f"PRAGMA index_info({row[1]})").fetchall())
        if indexed == ("raw_name", "benchmark", "metric", "harness", "effort", "source"):
            return True
    return False


def _migrate_scores_effort(conn: sqlite3.Connection) -> bool:
    """Preserve a pre-W2 score table while replacing its obsolete UNIQUE key.

    SQLite cannot alter a table-level UNIQUE constraint. Rebuilding this disposable
    evidence table is therefore the only way to let one model+harness retain several
    explicit effort rows without losing existing data.
    """
    if _scores_effort_schema(conn):
        return False
    columns = {row[1] for row in conn.execute("PRAGMA table_info(scores)")}
    if "effort" not in columns:
        conn.execute(
            "ALTER TABLE scores ADD COLUMN effort TEXT NOT NULL DEFAULT 'unspecified' "
            "CHECK (effort IN ('unspecified','low','medium','high','xhigh','max'))"
        )
    conn.execute("""
        CREATE TABLE scores__m5_effort (
            model_id    TEXT,
            raw_name    TEXT NOT NULL,
            benchmark   TEXT NOT NULL,
            metric      TEXT NOT NULL,
            score       REAL NOT NULL,
            harness     TEXT NOT NULL,
            effort      TEXT NOT NULL DEFAULT 'unspecified'
                        CHECK (effort IN ('unspecified','low','medium','high','xhigh','max')),
            run_date    TEXT,
            cost_total  REAL,
            source      TEXT NOT NULL,
            source_url  TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            UNIQUE (raw_name, benchmark, metric, harness, effort, source)
        )
        """)
    conn.execute("""
        INSERT INTO scores__m5_effort
            (model_id, raw_name, benchmark, metric, score, harness, effort,
             run_date, cost_total, source, source_url, observed_at)
        SELECT model_id, raw_name, benchmark, metric, score, harness,
               COALESCE(effort, 'unspecified'),
               run_date, cost_total, source, source_url, observed_at
        FROM scores
        """)
    conn.execute("DROP TABLE scores")
    conn.execute("ALTER TABLE scores__m5_effort RENAME TO scores")
    conn.execute("CREATE INDEX idx_scores_model ON scores (model_id)")
    return True


def _migrate(conn: sqlite3.Connection) -> list[str]:
    """Run migration statements inside the caller's transaction."""
    applied: list[str] = []
    for table, column, decl in _MIGRATIONS:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if not existing:
            continue  # table itself not created yet — DDL will create it complete
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
            applied.append(f"{table}.{column}")
    if _migrate_scores_effort(conn):
        applied.append("scores.effort")
    return applied


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Atomically add post-M1 columns to tables that predate them.

    **W-009: this is now the only migration entry point, and it is the one production runs.**
    Until M6-W3 both `connect()` and `main()` called the private `_migrate` directly inside their
    own `BEGIN IMMEDIATE`, so the SAVEPOINT wrapper here was exercised by tests and by nothing else
    — the atomicity the suite proved was not the transaction that shipped. Two entry points where
    one is tested and the other runs is worse than one untested entry point, because the test
    reports on a path nobody takes.

    `migrate` is a K.8 frozen contract name, so the reconciliation went the other way: the callers
    moved to it. SAVEPOINT nests correctly inside a caller's transaction, which is what it is for,
    and works standalone when there is none.
    """
    conn.execute("SAVEPOINT model_ranking_schema_migrate")
    try:
        applied = _migrate(conn)
    except sqlite3.Error:
        conn.execute("ROLLBACK TO model_ranking_schema_migrate")
        conn.execute("RELEASE model_ranking_schema_migrate")
        raise
    conn.execute("RELEASE model_ranking_schema_migrate")
    return applied


def _apply_ddl(conn: sqlite3.Connection) -> None:
    """Apply the static DDL without ``executescript``'s implicit pre-commit."""
    statement = ""
    for line in DDL.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            conn.execute(statement)
            statement = ""
    # W4 review MINOR-5: a comment-only remainder is not an incomplete statement.
    # Before this guard, appending a trailing `-- note` line to DDL made connect()
    # raise and took the whole application down over a comment.
    remainder = "\n".join(line.split("--", 1)[0].strip() for line in statement.splitlines()).strip()
    if remainder:
        raise sqlite3.DatabaseError("internal DDL contains an incomplete statement")


def _ddl_columns() -> dict[str, set[str]]:
    """Column names per table, parsed from THIS module's own DDL.

    W4 review BLOCKING-1: the previous validator carried a hand-written list of two
    tables, so a legacy `plans` missing `observed_at` passed validation, migrated
    "successfully" (exit 0, JSON emitted), and then killed the next
    `recommend --subscription` with `no such column: observed_at` — the exact symptom
    W-004 exists to eliminate, now hidden behind a success message. A hand-maintained
    copy of the schema drifts from the schema; this one is DERIVED from it, so a new
    column is covered the day it is added.
    """
    tables: dict[str, set[str]] = {}
    current: str | None = None
    for raw in DDL.splitlines():
        line = raw.split("--", 1)[0].strip()
        if not line:
            continue
        if line.upper().startswith("CREATE TABLE"):
            current = line.split()[-2] if line.endswith("(") else line.split()[-1]
            tables[current] = set()
            continue
        if current is None:
            continue
        if line.startswith(")"):
            current = None
            continue
        first = line.split()[0]
        # Table-level constraints are not columns.
        if first.upper() in {"UNIQUE", "PRIMARY", "FOREIGN", "CHECK", "CONSTRAINT"}:
            continue
        if first.isidentifier():
            tables[current].add(first)
    return tables


def _validate_migration_input(conn: sqlite3.Connection, tables: set[str]) -> None:
    """Reject look-alike or previously poisoned databases before the first write.

    A table that EXISTS must already carry every column the shipped DDL declares,
    except the ones a migration is able to add — `CREATE TABLE IF NOT EXISTS` cannot
    add a column to an existing table, so anything else would be a silent success on
    a database the read paths cannot use.
    """
    migratable: dict[str, set[str]] = {}
    for table, column, _ in _MIGRATIONS:
        migratable.setdefault(table, set()).add(column)
    # The effort migration REBUILDS `scores`, so its own column is addable too.
    migratable.setdefault("scores", set()).add("effort")

    required = {
        table: columns - migratable.get(table, set()) for table, columns in _ddl_columns().items()
    }
    for table, columns in required.items():
        if table not in tables:
            continue
        actual = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        missing = sorted(columns - actual)
        if missing:
            raise sqlite3.DatabaseError(f"unsupported {table} schema; missing columns: {missing}")
    if "scores__m5_effort" in tables:
        raise sqlite3.DatabaseError("incomplete prior migration: scores__m5_effort exists")
    if "scores" in tables and "effort" in {
        row[1] for row in conn.execute("PRAGMA table_info(scores)")
    }:
        invalid = conn.execute(
            "SELECT effort FROM scores WHERE effort NOT IN"
            " ('unspecified','low','medium','high','xhigh','max') LIMIT 1"
        ).fetchone()
        if invalid is not None:
            raise sqlite3.DatabaseError(f"scores contains unsupported effort: {invalid[0]!r}")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Open a connection with the schema applied + migrated (idempotent)."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _apply_ddl(conn)
        migrate(conn)  # W-009: the same entry point the tests exercise
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        conn.close()
        raise
    return conn


def reset_source(conn: sqlite3.Connection, table: str, source: str) -> None:
    """Delete a source's working set so a re-run is deterministic (REQ-ING-004).

    ``table`` is validated against the schema's own table list — never
    interpolated from user input.
    """
    if table not in ("pricing", "scores"):
        msg = f"reset_source: unknown table {table!r}"
        raise ValueError(msg)
    conn.execute(f"DELETE FROM {table} WHERE source = ?", (source,))  # noqa: S608


def main(argv: list[str] | None = None) -> int:
    """Explicit operator migration command (W-004); never runs from a read-only CLI."""
    parser = argparse.ArgumentParser(prog="schema", description=__doc__)
    parser.add_argument("command", choices=("migrate",))
    parser.add_argument("--db", required=True, help="existing model_ranking SQLite database")
    args = parser.parse_args(argv)
    path = Path(args.db)
    if not path.is_file():
        print(json.dumps({"error": f"db not found: {path}"}))
        return 2

    conn: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=rw"
        conn = sqlite3.connect(uri, uri=True)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        if not tables.intersection({"scores", "plan_models"}):
            raise sqlite3.DatabaseError("not a model_ranking database")
        _validate_migration_input(conn, tables)
        conn.execute("BEGIN IMMEDIATE")
        _apply_ddl(conn)
        applied = migrate(conn)  # W-009: the same entry point the tests exercise
        conn.commit()
    except sqlite3.Error as exc:
        if conn is not None:
            conn.rollback()
        print(json.dumps({"error": f"db unusable: {exc}"}))
        return 2
    finally:
        if conn is not None:
            conn.close()
    print(
        json.dumps(
            {"database": str(path), "applied": applied, "applied_count": len(applied)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
