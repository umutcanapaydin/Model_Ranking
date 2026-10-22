"""#378 (D-218 clause 1): LMArena's five image and video boards, read as five boards of the dataset.

The boards are configs of the same `lmarena-ai/leaderboard-dataset`, under the same CC-BY-4.0 grant and
through the same documented endpoint as every Arena board this project reads, with the same columns.
Each fixture under `tests/fixtures/arena_media/` is the whole overall board recorded from the real
dataset on 2026-10-21, as `ArenaClient.fetch_raw` merges it. The four `*_style_control` configs stay
unread: each is a board the product already reads, with style effects controlled for (a duplicate).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from app.clients.arena import ARENA_BOARDS, METRIC, ROWS_API, ArenaClient, parse_arena
from app.clients.protocols import SourceError
from app.workflows.board_tables import ARENA_ATTRIBUTION
from app.workflows.rank import SOURCE_ATTRIBUTION
from app.workflows.sources import REMOTE_SOURCES

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "arena_media"

#: config -> (source id, benchmark label, models on the recorded overall board, its publish date).
MEDIA_BOARDS = {
    "image_edit": ("arena_image_edit", "Arena image edit", 60, "2026-10-20"),
    "text_to_image": ("arena_text_to_image", "Arena text-to-image", 82, "2026-10-07"),
    "image_to_video": ("arena_image_to_video", "Arena image-to-video", 48, "2026-09-22"),
    "text_to_video": ("arena_text_to_video", "Arena text-to-video", 48, "2026-09-22"),
    "video_edit": ("arena_video_edit", "Arena video edit", 10, "2026-08-27"),
}
STYLE_CONTROL = ("text_style_control", "vision_style_control", "document_style_control", "search_style_control")


def _recorded(config: str) -> str:
    return (FIXTURES / f"{config}.json").read_text(encoding="utf-8")


@pytest.mark.parametrize("config", sorted(MEDIA_BOARDS))
def test_each_media_board_is_registered_under_its_own_source_and_benchmark(config: str) -> None:
    """D-218 clause 1, REQ-SRC-011: one source id and one benchmark per board, never another board's."""
    source, benchmark, _, _ = MEDIA_BOARDS[config]
    board = ARENA_BOARDS[config]
    client = ArenaClient(config=config)
    assert (board.id, board.config, board.benchmark) == (source, config, benchmark)
    assert (client.name, client.benchmark) == (source, benchmark)
    assert f"config={config}" in client.url


@pytest.mark.parametrize("config", sorted(MEDIA_BOARDS))
def test_each_recorded_media_board_parses_whole_under_its_own_label(config: str) -> None:
    """The parser keeps every model of the recorded board, as Elo, under the board's own labels."""
    source, benchmark, models, published = MEDIA_BOARDS[config]
    rows, skipped = parse_arena(_recorded(config), source=source, benchmark=benchmark)
    assert (len(rows), skipped) == (models, 0)
    assert {(r.source, r.benchmark, r.metric, r.harness) for r in rows} == {(source, benchmark, METRIC, "arena-crowd")}
    assert {r.run_date for r in rows} == {published}
    # and a real day clears the board's truncation floor, which a truncated read does not
    assert ARENA_BOARDS[config].minimum_rows < models


@pytest.mark.parametrize("config", sorted(MEDIA_BOARDS))
def test_each_media_board_is_an_optional_attributed_source_the_build_reads(config: str) -> None:
    """Optional as every Arena board is (D-121), floored as its own board (W-024), credited as LMArena."""
    source, *_ = MEDIA_BOARDS[config]
    entry = next(s for s in REMOTE_SOURCES if s.name == source)
    assert entry.required is False
    assert entry.minimum_rows == ARENA_BOARDS[config].minimum_rows
    assert entry.client().name == source
    assert entry.client.__name__ != "ArenaClient"  # a named client, as the registry guard requires
    assert SOURCE_ATTRIBUTION[source] == ARENA_ATTRIBUTION


@pytest.mark.parametrize("config", STYLE_CONTROL)
def test_the_style_control_configs_stay_unread_as_duplicates(config: str) -> None:
    """D-218 clause 1: each is a board already read, with style controlled for; reading it would be
    a second answer to one question."""
    assert config not in ARENA_BOARDS
    with pytest.raises(SourceError, match="no board registered"):
        ArenaClient(config=config)


def test_the_fixtures_are_the_recorded_overall_boards_and_nothing_else() -> None:
    """A fixture holds one board: every row is the overall category, and each says where it came from."""
    for config in MEDIA_BOARDS:
        payload = json.loads(_recorded(config))
        assert f"config={config}" in payload["_note"]
        assert {wrapper["row"]["category"] for wrapper in payload["rows"]} == {"overall"}


@respx.mock
@pytest.mark.parametrize("config", sorted(MEDIA_BOARDS))
def test_a_page_nested_past_the_recursion_limit_fails_the_board_and_nothing_else(config: str) -> None:
    """D-121 (the queue-1021 integration review's M2, checked on #378's boards): `RecursionError` from a page's
    `json.loads` is bad input, not a builder bug, so it fails this optional board as `SourceError` and never aborts
    the night."""
    respx.get(ROWS_API).mock(return_value=httpx.Response(200, text="[" * 100_000))
    with pytest.raises(SourceError, match="arena fetch failed"):
        ArenaClient(config=config).fetch_raw()
