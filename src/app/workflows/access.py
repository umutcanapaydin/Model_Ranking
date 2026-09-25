"""Each model's accessibility, from Epoch's `model_metadata.csv` (M17-W3, #37).

The owner ruled (2026-09-25) that it is an attribute, not a board: W4 sends it to the phone for
filters such as "an open model I can host myself" or "can I use it commercially".

The file is keyed by Epoch's own model name, the spelling its boards use, so a name here resolves
to a model exactly as an Epoch score does: effort suffix off, a curated rule first, then a derived
identity (D-157) that is registered. Where two names of one model disagree, the model gets NO value
and the disagreement is counted -- a filter that guessed would put a restricted model under "open".
"""

from __future__ import annotations

import csv
import io
import sqlite3
from dataclasses import dataclass

from app.clients.protocols import SourceError
from app.workflows.registry import canonicalize_with_reason, derive_identity, resolve_effort

SOURCE = "epoch_access"
FILE = "model_metadata.csv"
#: The values the 2026-09 bundle uses. A value outside them is a changed file: refused and counted.
ACCESSIBILITY = frozenset({
    "API access", "Open weights (unrestricted)", "Open weights (restricted use)",
    "Open weights (non-commercial)", "Hosted access (no API)", "Unreleased", "Limited access",
})


@dataclass(frozen=True)
class AccessRow:
    raw_name: str
    accessibility: str


@dataclass(frozen=True)
class AccessReport:
    linked: int
    unlinked: int
    #: Models whose names disagree about their accessibility; they get no value.
    conflicting: tuple[str, ...]


def parse_metadata(text: str) -> tuple[list[AccessRow], int]:
    """The file's (name, accessibility) rows; returns (rows, skipped)."""
    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or ())
    if not {"model_version", "accessibility"} <= fields:
        msg = f"{SOURCE}: {FILE} has no model_version/accessibility columns (has {sorted(fields)})"
        raise SourceError(msg)
    rows: list[AccessRow] = []
    skipped = 0
    for record in reader:
        name = (record.get("model_version") or "").strip()
        value = (record.get("accessibility") or "").strip()
        if not name or value not in ACCESSIBILITY:
            skipped += 1
            continue
        rows.append(AccessRow(name, value))
    return rows, skipped


def store(conn: sqlite3.Connection, rows: list[AccessRow], *, source: str, source_url: str,
          observed_at: str) -> int:
    """Replace `source`'s rows (the build's working-set rule, REQ-ING-004)."""
    with conn:
        conn.execute("DELETE FROM access WHERE source = ?", (source,))
        conn.executemany(
            "INSERT OR REPLACE INTO access (raw_name, model_id, accessibility, source, source_url, "
            "observed_at) VALUES (?, NULL, ?, ?, ?, ?)",
            [(r.raw_name, r.accessibility, source, source_url, observed_at) for r in rows])
    return len(rows)


def _model_for(name: str, registered: set[str]) -> str | None:
    """The model an Epoch score under `name` would land on, if it is registered."""
    model_name = resolve_effort(name).model_name
    rule, _ = canonicalize_with_reason(model_name)
    if rule is not None:
        return rule.canonical_id if rule.canonical_id in registered else None
    derived = derive_identity(model_name)
    return derived.model_id if derived is not None and derived.model_id in registered else None


def link(conn: sqlite3.Connection) -> AccessReport:
    """Link every access row to its model (after `registry.reconcile`); count what did not link."""
    registered = {row[0] for row in conn.execute("SELECT id FROM models")}
    linked = unlinked = 0
    with conn:
        for (name,) in conn.execute("SELECT DISTINCT raw_name FROM access").fetchall():
            model_id = _model_for(name, registered)
            conn.execute("UPDATE access SET model_id = ? WHERE raw_name = ?", (model_id, name))
            linked, unlinked = (linked + 1, unlinked) if model_id else (linked, unlinked + 1)
    conflicting = tuple(row[0] for row in conn.execute(
        "SELECT model_id FROM access WHERE model_id IS NOT NULL GROUP BY model_id "
        "HAVING COUNT(DISTINCT accessibility) > 1 ORDER BY model_id"))
    return AccessReport(linked, unlinked, conflicting)


def served(conn: sqlite3.Connection) -> dict[str, str]:
    """model id -> accessibility, for the models whose names agree."""
    return dict(conn.execute(
        "SELECT model_id, MIN(accessibility) FROM access WHERE model_id IS NOT NULL "
        "GROUP BY model_id HAVING COUNT(DISTINCT accessibility) = 1 ORDER BY model_id").fetchall())
