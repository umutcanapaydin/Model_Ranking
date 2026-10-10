"""#185 (M21-W1, REQ-SRC-010): `web-dev` reads LMArena's own WebDev board, under the dataset card's
CC-BY-4.0 grant, where it read Epoch's copy of it. D-185 left Epoch's copy out of the public artifact
(arena.ai's site terms), which left `web-dev` dark on the hosted engine once its licence table applies;
LMArena publishes the same board in `lmarena-ai/leaderboard-dataset` (the `webdev` config)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.clients.arena import ARENA_BOARDS
from app.workflows import families, public
from app.workflows.board_tables import ARENA_ATTRIBUTION
from app.workflows.categories import CATEGORIES
from app.workflows.rank import SOURCE_ATTRIBUTION
from app.workflows.sources import REMOTE_SOURCES

from .test_api_v1 import _seeded_db
from .test_public_artifact import EXPECTED_LEFT_OUT


def test_web_dev_ranks_on_lmarenas_own_board() -> None:
    spec = CATEGORIES["web-dev"]
    board = ARENA_BOARDS["webdev"]
    assert (spec.primary_source, spec.primary_benchmark) == (board.id, board.benchmark) == (
        "arena_webdev", "Arena WebDev")
    assert SOURCE_ATTRIBUTION["arena_webdev"] == ARENA_ATTRIBUTION
    assert "CC-BY-4.0" in ARENA_ATTRIBUTION


def test_the_webdev_board_is_an_optional_source_as_every_arena_board_is() -> None:
    entry = next(source for source in REMOTE_SOURCES if source.name == "arena_webdev")
    assert entry.required is False
    assert entry.minimum_rows == ARENA_BOARDS["webdev"].minimum_rows


def test_the_family_reads_one_webdev_vote_and_epochs_copy_stands_outside() -> None:
    """D-188 clause 1: Epoch's copy is the same vote as LMArena's board, so the family holds LMArena's."""
    assert families.FAMILIES["web-dev"] == ("arena_webdev", "arena_text_coding")
    assert "epoch_webdev" in families.OUTSIDE_FAMILIES


def test_the_public_artifact_keeps_web_devs_board_under_d185s_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The issue's done-when: with D-185's licence table applied, `web-dev`'s board survives."""
    monkeypatch.setattr(public, "LEFT_OUT", {source: "planted for the test" for source in EXPECTED_LEFT_OUT})
    assert CATEGORIES["web-dev"].primary_source not in public.LEFT_OUT
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, run_date, source,"
                     " source_url, observed_at) SELECT model_id, raw_name, 'Arena WebDev', 'elo', 1500.0,"
                     " 'arena-crowd', NULL, 'arena_webdev', 'https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset',"
                     " observed_at FROM scores WHERE source = 'swebench' LIMIT 3")
    public.derive(built, served)
    with sqlite3.connect(served) as conn:
        assert conn.execute("SELECT count(*) FROM scores WHERE source = 'arena_webdev'").fetchone()[0] == 3
