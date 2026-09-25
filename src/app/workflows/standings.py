"""Every board's standings, as positions: what the phone combines on the device (D-160, D-167).

The phone fetches this whole payload whatever the question is, so the request reveals nothing about
the question (D-167 clause 1). It carries POSITIONS and no score, so no code on the phone can
average two scales, whatever a later change tries (D-105, D-167 clause 2).

A board is a source: every source holds exactly one benchmark under one metric (measured on the
2026-09-25 candidate, and refused here if that ever stops being true). A model stands on a board by
its best row there, among the models the engine can rank: reconciled AND priced, the population
every surface ranks (REQ-EVI-002).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from app.workflows import access
from app.workflows.rank import (
    BLEND_INPUT_WEIGHT,
    BLEND_OUTPUT_WEIGHT,
    SOURCE_ATTRIBUTION,
    attributions_for,
)

API_VERSION = "v1"

#: The metrics served today, every one higher-is-better. A position needs to know which way a board
#: runs; a metric not named here is refused rather than ranked the wrong way round.
HIGHER_IS_BETTER = frozenset({"elo", "ips", "% correct", "% resolved", "% pass_rate_2", "ECI"})

# The rankable rows of every board: each model's best score there, with the board's dates. One
# query, so the payload and the boot bound (`standings_row_count`) count the same set.
_BEST = """
    SELECT s.source, s.benchmark, s.metric, s.model_id, MAX(s.score) AS best
    FROM scores s
    JOIN models m ON m.id = s.model_id
    JOIN px_median p ON p.model_id = s.model_id
    GROUP BY s.source, s.benchmark, s.metric, s.model_id
"""


def standings_row_count(conn: sqlite3.Connection) -> int:
    """How many (board, model) positions the payload would publish: the boot-time egress bound."""
    return int(conn.execute(f"SELECT COUNT(*) FROM ({_BEST})").fetchone()[0])  # noqa: S608


def _board_dates(conn: sqlite3.Connection) -> dict[str, tuple[str | None, str | None]]:
    """source -> (newest evaluation date, newest observation date), over its rankable rows."""
    return {
        source: (evidence, observed[:10] if observed else None)
        for source, evidence, observed in conn.execute(
            "SELECT s.source, MAX(s.run_date), MAX(s.observed_at) FROM scores s "
            "JOIN px_median p ON p.model_id = s.model_id GROUP BY s.source")
    }


def board_standings(conn: sqlite3.Connection) -> dict[str, Any]:
    """The `/v1/boards` payload. Raises ValueError on an unattributed source, a metric whose
    direction is not declared, or a source holding more than one board."""
    rows = conn.execute(f"{_BEST} ORDER BY s.source, best DESC, s.model_id").fetchall()
    boards: dict[str, dict[str, Any]] = {}
    last: dict[str, tuple[float, int]] = {}
    dates = _board_dates(conn)
    for source, benchmark, metric, model_id, best in rows:
        if metric not in HIGHER_IS_BETTER:
            msg = f"{source}: metric {metric!r} has no declared direction; add it to HIGHER_IS_BETTER"
            raise ValueError(msg)
        board = boards.get(source)
        if board is None:
            attributions_for([source], priced=False)  # raises on an unattributed source
            evidence, observed = dates.get(source, (None, None))
            board = boards[source] = {
                "id": source, "benchmark": benchmark, "metric": metric, "evidence_date": evidence,
                "observed_at": observed, "attribution": SOURCE_ATTRIBUTION[source], "standings": [],
            }
        elif (board["benchmark"], board["metric"]) != (benchmark, metric):
            msg = f"{source}: holds more than one board ({board['benchmark']!r}, {benchmark!r})"
            raise ValueError(msg)
        standing = board["standings"]
        # Competition ranking: tied models share a position, so a tie's order means nothing (#44).
        previous = last.get(source)
        position = previous[1] if previous and previous[0] == best else len(standing) + 1
        last[source] = (best, position)
        standing.append({"model": model_id, "position": position})

    accessibility = _accessibility(conn)
    standing_models = {s["model"] for board in boards.values() for s in board["standings"]}
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
        "api_version": API_VERSION,
        "attributions": list(attributions_for(boards, priced=True)),
        "boards": [boards[source] for source in sorted(boards)],
        "models": models,
    }


def _accessibility(conn: sqlite3.Connection) -> dict[str, str]:
    """W3's attribute; an artifact built before it has the table missing and serves none."""
    return access.served(conn)
