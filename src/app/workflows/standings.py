"""Every board's standings, as positions: what the phone combines on the device (D-160, D-167).

The phone fetches this whole payload whatever the question is, so the request reveals nothing about
the question (D-167 clause 1). It carries POSITIONS and no score, so no code on the phone can
average two scales, whatever a later change tries (D-105, D-167 clause 2).

A board is a source: every source holds exactly one benchmark under one metric (measured on the
2026-09-25 candidate, and refused here if that ever stops being true). The models that stand on it
are the ones the engine can rank: reconciled AND priced, the population every surface ranks
(REQ-EVI-002). Effort follows D-112, as every surface does: a board a surface ranks at one effort
(`ranking_effort`) stands at that effort; any other board stands on each model's best evidence, and
every standing says which effort its evidence was run at, so the phone can disclose an unequal
comparison (M17-W4 review B1).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from app.workflows import access
from app.workflows.categories import CATEGORIES
from app.workflows.rank import (
    BLEND_INPUT_WEIGHT,
    BLEND_OUTPUT_WEIGHT,
    SOURCE_ATTRIBUTION,
    attributions_for,
)

#: The metrics served today, every one higher-is-better. A position needs to know which way a board
#: runs; a metric not named here is refused rather than ranked the wrong way round.
HIGHER_IS_BETTER = frozenset({"elo", "ips", "% correct", "% resolved", "% pass_rate_2", "ECI"})

# Every rankable row, with what picking a model's evidence row needs.
_ROWS = """
    SELECT s.source, s.benchmark, s.metric, s.model_id, s.score, s.effort, s.run_date, s.observed_at,
           s.harness, s.raw_name
    FROM scores s
    JOIN models m ON m.id = s.model_id
    JOIN px_median p ON p.model_id = s.model_id
"""


@dataclass(frozen=True)
class _Row:
    source: str
    benchmark: str
    metric: str
    model: str
    score: float
    effort: str
    run_date: str | None
    observed_at: str
    harness: str
    raw_name: str


def _policies() -> dict[tuple[str, str], str]:
    """(source, benchmark) -> the effort a surface ranks that board at (D-112)."""
    return {(spec.primary_source, spec.primary_benchmark): spec.ranking_effort
            for spec in CATEGORIES.values() if spec.ranking_effort}


def _evidence(rows: list[_Row]) -> _Row:
    """A model's evidence row on a board: its best score, and among equal scores the newest run,
    then harness and name, as `rank.category_ranking` breaks the same tie (M1-W3 MINOR-3)."""
    ordered = sorted(rows, key=lambda r: (r.harness, r.raw_name))
    ordered.sort(key=lambda r: r.run_date or "", reverse=True)
    ordered.sort(key=lambda r: r.score, reverse=True)
    return ordered[0]


def board_standings(conn: sqlite3.Connection) -> dict[str, Any]:
    """The `/v1/boards` payload, without the API version the route adds. Raises ValueError on an
    unattributed source, a metric whose direction is not declared, or a source holding more than
    one board."""
    policies = _policies()
    grouped: dict[str, dict[str, list[_Row]]] = {}
    shape: dict[str, tuple[str, str]] = {}
    for raw in conn.execute(_ROWS):
        row = _Row(*raw)
        if row.metric not in HIGHER_IS_BETTER:
            msg = f"{row.source}: metric {row.metric!r} has no declared direction; add it to HIGHER_IS_BETTER"
            raise ValueError(msg)
        if shape.setdefault(row.source, (row.benchmark, row.metric)) != (row.benchmark, row.metric):
            msg = f"{row.source}: holds more than one board ({shape[row.source][0]!r}, {row.benchmark!r})"
            raise ValueError(msg)
        policy = policies.get((row.source, row.benchmark))
        if policy is not None and row.effort != policy:
            continue
        grouped.setdefault(row.source, {}).setdefault(row.model, []).append(row)

    boards: list[dict[str, Any]] = []
    for source in sorted(grouped):
        attributions_for([source], priced=False)  # raises on an unattributed source
        evidence = sorted((_evidence(rows) for rows in grouped[source].values()),
                          key=lambda r: (-r.score, r.model))
        standings: list[dict[str, Any]] = []
        for index, row in enumerate(evidence):
            # Competition ranking: tied models share a position, so a tie's order means nothing (#44).
            tied = index > 0 and evidence[index - 1].score == row.score
            position = standings[-1]["position"] if tied else index + 1
            standings.append({"model": row.model, "position": position, "effort": row.effort})
        kept = [r for rows in grouped[source].values() for r in rows]
        dated = [r.run_date for r in kept if r.run_date]
        benchmark, metric = shape[source]
        boards.append({
            "id": source, "benchmark": benchmark, "metric": metric,
            "ranking_effort": policies.get((source, benchmark)),
            "evidence_date": max(dated) if dated else None,
            "observed_at": max(r.observed_at for r in kept)[:10],
            "attribution": SOURCE_ATTRIBUTION[source],
            "standings": standings,
        })

    accessibility = access.served(conn)
    standing_models = {s["model"] for board in boards for s in board["standings"]}
    models = [
        {"id": mid, "display": display, "vendor": vendor,
         "blended_per_m": round(in_m * BLEND_INPUT_WEIGHT + out_m * BLEND_OUTPUT_WEIGHT, 2),
         "accessibility": accessibility.get(mid)}
        for mid, display, vendor, in_m, out_m in conn.execute(
            "SELECT m.id, m.display, m.vendor, p.in_m, p.out_m FROM models m "
            "JOIN px_median p ON p.model_id = m.id ORDER BY m.id")
        if mid in standing_models
    ]
    return {
        "attributions": list(attributions_for([b["id"] for b in boards], priced=True)),
        "boards": boards,
        "models": models,
    }


def standings_row_count(payload: dict[str, Any]) -> int:
    """How many (board, model) positions a payload publishes: the boot-time egress bound."""
    return sum(len(board["standings"]) for board in payload["boards"])
