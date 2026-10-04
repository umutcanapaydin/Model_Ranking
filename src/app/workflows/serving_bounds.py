"""The artifact-size bounds the engine serves under, in one place for the engine and the refresh.

The engine checks them when it starts (`app.adapter.main.validate_startup_config`), and never trims
at serve time. Until M18-W4 that was the only check: the nightly refresh (D-154) published a new
artifact under the running process, and a night that grew it past a bound was served until the next
restart, which then refused to start (#57). D-173 clause 4 runs the same check on the refresh's
candidate before it is published, so the two cannot disagree: both read `bounds_from_env` and call
`egress_problems`.

This module is a workflow, not the adapter, because the refresh imports nothing from `app.adapter`
(REQ-REF-007).
"""

from __future__ import annotations

import contextlib
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.workflows.categories import CATEGORIES
from app.workflows.rank import category_ranking
from app.workflows.schema import open_readonly
from app.workflows.standings import board_standings, standings_row_count

#: The route the standings bound protects. The adapter owns `/v1`'s version; this names the route in
#: an operator's message and decides nothing.
BOARDS_ROUTE = "/v1/boards"


#: The environment variables the bounds are read from. The engine's nightly refresh runs in a child
#: process with an allowlisted environment (`app.adapter.nightly.CHILD_ENV`), which includes these,
#: so the child checks its candidate against the bounds the engine serves under (W4 review B1).
BOUND_VARIABLES = (
    "MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS",
    "MODEL_RANKING_MAX_PUBLISHED_STANDINGS_ROWS",
    "MODEL_RANKING_MAX_RANKED_ROWS",
)


@dataclass(frozen=True)
class ServingBounds:
    """The three bounds. Each is a runaway guard, not a product limit; see `bounds_from_env`."""

    #: The largest ranking ONE answer may publish (D-125's `ranking` array).
    answer_rows: int
    #: The largest `/v1/boards` payload, in (board, model) positions (D-167).
    standings_rows: int
    #: The largest ranked-model count the process will hold in memory.
    ranked_rows: int


def bounds_from_env() -> ServingBounds:
    """The bounds in force, each overridable by its environment variable.

    - **Answer rows, 500.** The largest surface today is 58 rows, and 500 caps one answer near ~100 KB.
      Raising it is a deliberate egress decision, which is why the variable's name says what it costs.
    - **Standings positions, 25,000.** Measured on 2026-09-25: 6,955 positions, 500 KB (36 KB
      gzipped); the guard sits about 3.6 times above that.
    - **Ranked models, 5,000.** The Stage-4.0 pass found ~10,000 ranked models using 58% of the VM
      `fly.toml` declares and ~50,000 OOM-killed, against 73 in the shipped artifact.
    """
    return ServingBounds(
        answer_rows=int(os.environ.get("MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS", "500")),
        standings_rows=int(os.environ.get("MODEL_RANKING_MAX_PUBLISHED_STANDINGS_ROWS", "25000")),
        ranked_rows=int(os.environ.get("MODEL_RANKING_MAX_RANKED_ROWS", "5000")),
    )


def standings_problem(db: Path, limit: int) -> str | None:
    """Why `/v1/boards` could not be served from `db`: the payload's own refusals, and its egress
    bound. None when it can be, or when the artifact cannot be asked at all (the adapter's
    `_database_unusable` reports that)."""
    try:
        conn = open_readonly(db)
    except sqlite3.Error:
        return None
    try:
        positions = standings_row_count(board_standings(conn))
    except ValueError as exc:
        return f"MODEL_RANKING_DB cannot publish {BOARDS_ROUTE}: {exc}"
    except sqlite3.Error:
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()
    if positions > limit:
        return (
            f"MODEL_RANKING_DB would publish {positions} standings positions on "
            f"{BOARDS_ROUTE}; this process refuses past {limit}. "
            "The payload is not truncated to fit -- the phone keeps what it receives, and a "
            "short board would be served as the whole board. Raise "
            "MODEL_RANKING_MAX_PUBLISHED_STANDINGS_ROWS knowing it raises what every phone "
            "downloads each day"
        )
    return None


def largest_surface_row_count(db: Path) -> tuple[str, int] | None:
    """The biggest ranking any single answer would publish, and which surface it is.

    Calls `category_ranking` rather than mirroring its join in a COUNT query. A second copy of that
    query would be a second definition of "what gets published", and this project has spent several
    milestones on what happens when two definitions of the same set drift apart.
    """
    try:
        conn = open_readonly(db)
    except sqlite3.Error:
        return None
    try:
        worst = ("", 0)
        for name, spec in CATEGORIES.items():
            size = len(category_ranking(conn, spec))
            if size > worst[1]:
                worst = (name, size)
        return worst
    except sqlite3.Error:
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()


def ranked_row_count(db: Path) -> int | None:
    """How many models the artifact can actually rank, or None if it cannot be asked.

    Counts DISTINCT reconciled models carrying a score, which is what `category_ranking` joins over
    and therefore what the process pays memory for. An unreadable database returns None here rather
    than raising: the adapter's `_database_unusable` is the check that reports that, and two checks
    reporting the same fault in different words is how an operator learns to skim them.
    """
    try:
        conn = open_readonly(db)
    except sqlite3.Error:
        return None
    try:
        row = conn.execute(
            "SELECT count(DISTINCT model_id) FROM scores WHERE model_id IS NOT NULL"
        ).fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()


def egress_problems(db: Path, bounds: ServingBounds) -> list[str]:
    """Every bound `db` is past, each in words an operator can act on; empty when it is within all."""
    out: list[str] = []
    largest = largest_surface_row_count(db)
    if largest is not None and largest[1] > bounds.answer_rows:
        out.append(
            f"MODEL_RANKING_DB would publish {largest[1]} ranking rows in a single answer on "
            f"the {largest[0]!r} surface; this process refuses past "
            f"{bounds.answer_rows}. The response is not truncated to fit — a silently "
            "shortened ranking is one the reader believes is complete. Narrow what the build "
            "ingests, or raise MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS knowing it raises what "
            "one unauthenticated request costs to serve"
        )

    standings = standings_problem(db, bounds.standings_rows)
    if standings is not None:
        out.append(standings)

    ranked = ranked_row_count(db)
    if ranked is not None and ranked > bounds.ranked_rows:
        out.append(
            f"MODEL_RANKING_DB ranks {ranked} models; this process refuses past "
            f"{bounds.ranked_rows}. Measured at Stage 4.0: ~10,000 ranked models reach 58% of a "
            "256 MiB VM and ~50,000 are OOM-killed. Raise MODEL_RANKING_MAX_RANKED_ROWS with "
            "the VM, or narrow what the build ingests"
        )
    return out
