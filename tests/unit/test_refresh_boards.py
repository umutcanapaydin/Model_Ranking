"""M17-W2 P3 -- D-164: a board is published content, and the refresh guards it as a board (#22).

Through the real cycle (`refresh`), with one real declared slice (`vision/captioning`) and a fake
download. Before D-164 a candidate that changed only a board read as "nothing a user would notice
changed" and was thrown away, and nothing guarded a board no surface ranks on.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.arena_slices import ARENA_SLICES
from app.clients.fakes import fake_slice_client, slice_parquet
from app.workflows import build as build_mod
from app.workflows.refresh import (
    EXIT_PUBLISHED,
    EXIT_REFUSED,
    refresh,
    serving_summary,
    status_path,
)
from app.workflows.schema import connect

from .test_build import _sources

pytestmark = pytest.mark.slices

BOARD = next(b for b in ARENA_SLICES if b.source_name == "arena_vision_captioning")
NEWEST = "2026-09-13"


def _file(names: list[str], *, bump: float = 0.0) -> bytes:
    rows = [(name, 1200.0 + i + bump, BOARD.category, NEWEST) for i, name in enumerate(names)]
    rows += [("m-overall", 1300.0, "overall", NEWEST)]
    return slice_parquet(rows)


def _names(n: int, prefix: str = "m") -> list[str]:
    return [f"{prefix}{i}" for i in range(n)]


def _upstream(monkeypatch: pytest.MonkeyPatch, payload: bytes | None, *, boards=(BOARD,)) -> None:
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    monkeypatch.setattr(build_mod, "ARENA_SLICES", boards)
    monkeypatch.setattr(build_mod, "ARENA_SLICE_CLIENT", fake_slice_client({"vision": payload}))


def _board(live: Path) -> list[tuple[str, float]]:
    return sorted(sqlite3.connect(live).execute(
        "SELECT raw_name, score FROM scores WHERE source = ?", (BOARD.source_name,)).fetchall())


def _published(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, names: list[str]) -> Path:
    live = tmp_path / "advisor.db"
    _upstream(monkeypatch, _file(names))
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason
    assert len(_board(live)) == len(names)
    return live


def test_a_candidate_that_changes_only_a_board_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-164 clause 1. Every surface is the same; one board's ratings moved."""
    live = _published(tmp_path, monkeypatch, _names(30))
    _upstream(monkeypatch, _file(_names(30), bump=7.0))
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason
    assert _board(live)[0][1] == 1207.0


def test_the_fingerprint_moves_with_a_board_and_only_with_it() -> None:
    conn = connect(":memory:")
    try:
        before = serving_summary(conn).digest
        conn.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
            "source_url, observed_at) VALUES ('m0', ?, 'elo', 1200.04, 'arena-crowd', "
            "'unspecified', ?, 'u', 'z')", (BOARD.benchmark, BOARD.source_name))
        added = serving_summary(conn)
        assert added.digest != before
        assert added.slices[BOARD.source_name] == frozenset({"m0"})
        conn.execute("UPDATE scores SET score = 1200.01, observed_at = 'y'")
        assert serving_summary(conn).digest == added.digest, (
            "a move below the output boundary's rounding (D-109), or a new timestamp, is not news")
    finally:
        conn.close()


def test_the_night_the_boards_first_arrive_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-164 clause 3: a board seen for the first time is returning, not new."""
    live = tmp_path / "advisor.db"
    _upstream(monkeypatch, None, boards=())
    assert refresh(live)[1] == EXIT_PUBLISHED
    _upstream(monkeypatch, _file(_names(30)))
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason
    assert len(_board(live)) == 30


def test_a_board_that_loses_a_quarter_of_its_names_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-164 clause 2 (D-128's limit). 30 -> 22 loses 27%, and stays above the row floor (17)."""
    live = _published(tmp_path, monkeypatch, _names(30))
    _upstream(monkeypatch, _file(_names(22)))
    outcome, code = refresh(live)
    assert code == EXIT_REFUSED
    assert BOARD.source_name in outcome.reason and "D-164" in outcome.reason
    assert len(_board(live)) == 30, "the live artifact is untouched"


def test_a_board_whose_names_are_a_quarter_new_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-164 clause 2 (D-132's limit): 30 names plus 11 never seen is 27% new."""
    live = _published(tmp_path, monkeypatch, _names(30))
    _upstream(monkeypatch, _file(_names(30) + _names(11, "new")))
    outcome, code = refresh(live)
    assert code == EXIT_REFUSED
    assert BOARD.source_name in outcome.reason and "D-164" in outcome.reason


def test_ordinary_movement_on_a_board_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Below both limits: two names gone and two new on thirty."""
    live = _published(tmp_path, monkeypatch, _names(30))
    _upstream(monkeypatch, _file(_names(28) + _names(2, "new")))
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason


def test_an_expired_board_drops_instead_of_freezing_the_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-156 clause 3 for a board: past 30 days its rows go, and the loss guard excuses exactly that."""
    live = _published(tmp_path, monkeypatch, _names(30))
    old = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=45)).isoformat(timespec="seconds")
    with sqlite3.connect(live) as db:
        db.execute("UPDATE scores SET observed_at = ? WHERE source = ?", (old, BOARD.source_name))
    record = json.loads(status_path(live).read_text(encoding="utf-8"))
    record["sources_last_ok"][BOARD.source_name] = old
    status_path(live).write_text(json.dumps(record), encoding="utf-8")

    _upstream(monkeypatch, None)
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason
    assert _board(live) == []
