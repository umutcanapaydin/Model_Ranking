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

import sqlite3
from dataclasses import dataclass

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
    conn.executescript("""
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
        );
        INSERT INTO scores__m5_effort
            (model_id, raw_name, benchmark, metric, score, harness, effort,
             run_date, cost_total, source, source_url, observed_at)
        SELECT model_id, raw_name, benchmark, metric, score, harness,
               COALESCE(effort, 'unspecified'),
               run_date, cost_total, source, source_url, observed_at
        FROM scores;
        DROP TABLE scores;
        ALTER TABLE scores__m5_effort RENAME TO scores;
        CREATE INDEX idx_scores_model ON scores (model_id);
        """)
    return True


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Add post-M1 columns to tables that predate them; returns what was added."""
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
    if applied:
        conn.commit()
    return applied


def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Open a connection with the schema applied + migrated (idempotent)."""
    conn = sqlite3.connect(path)
    conn.executescript(DDL)
    migrate(conn)
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
