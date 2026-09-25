"""The boards no surface ranks on, derived rather than listed (D-164, M17-W3 #37).

D-164 makes a board published content: its standings are in the refresh fingerprint and the
quarter-lost / quarter-new guards apply to it. A board a surface ranks on is already covered by that
surface's ranking; every OTHER declared board -- Arena's category slices, the Epoch boards no
surface uses -- is covered here. The set is derived from the declared tables and `CATEGORIES` at
call time, so a board a surface starts ranking on leaves it with no edit here, and a board declared
tomorrow joins it the same way.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.clients.arena_slices import ARENA_SLICES
from app.workflows.categories import CATEGORIES
from app.workflows.sources import EPOCH_BOARDS


@dataclass(frozen=True)
class Board:
    """One declared board: the source its rows carry and the benchmark label they are stored under."""

    source: str
    benchmark: str


def declared() -> list[Board]:
    """Every board the build declares as data."""
    return [Board(s.source_name, s.benchmark) for s in ARENA_SLICES] + [
        Board(b.source_name, b.benchmark) for b in EPOCH_BOARDS
    ]


def uncovered() -> list[Board]:
    """The declared boards no surface ranks on, as primary source or as either benchmark."""
    sources = {spec.primary_source for spec in CATEGORIES.values()}
    benchmarks = {b for spec in CATEGORIES.values()
                  for b in (spec.primary_benchmark, spec.secondary_benchmark) if b}
    return sorted((b for b in declared() if b.source not in sources and b.benchmark not in benchmarks),
                  key=lambda b: b.source)
