"""Database schema for model_ranking (M1) — shared contract, K.8.

Plain sqlite3 DDL + typed row containers. The SQLite file is disposable and
rebuilt from sources on every pipeline run (D-100). Every changing record
carries provenance fields (REQ-ING-004): ``source``, ``source_url``,
``observed_at``.

Tables
------
models      canonical model registry (filled in W3, REQ-CAN-001)
pricing     per-alias API prices from pricing sources (W1, REQ-ING-001)
scores      benchmark score records — ALWAYS model+harness pairs (W2, REQ-ING-002)
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
    harness     TEXT NOT NULL,        -- a score is a model+harness pair (REQ-ING-002)
    run_date    TEXT,
    cost_total  REAL,
    source      TEXT NOT NULL,
    source_url  TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    UNIQUE (raw_name, benchmark, metric, harness, source)
);
CREATE INDEX IF NOT EXISTS idx_pricing_model ON pricing (model_id);
CREATE INDEX IF NOT EXISTS idx_scores_model  ON scores  (model_id);
CREATE TABLE IF NOT EXISTS px_median (
    model_id TEXT PRIMARY KEY,
    in_m     REAL NOT NULL,
    out_m    REAL NOT NULL
);
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
class ScoreRow:
    """One benchmark score record; harness is mandatory (REQ-ING-002)."""

    raw_name: str
    benchmark: str
    metric: str
    score: float
    harness: str
    run_date: str | None
    cost_total: float | None
    source: str
    source_url: str


def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Open a connection with the schema applied (idempotent)."""
    conn = sqlite3.connect(path)
    conn.executescript(DDL)
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
