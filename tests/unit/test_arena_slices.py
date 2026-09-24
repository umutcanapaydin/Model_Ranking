"""M17-W2 P1 -- Arena's category slices, read from the dataset's own parquet file (#22, D-164).

Network-free: every parquet here is built in the test with `pyarrow`, and the one download test
goes through respx. The live shape (29 `text` slices, 11 `vision`, one publish date) is recorded
in `docs/plans/m17-wave-2-plan.md`.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from typing import Any

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import respx

from app.clients.arena import ARENA_BOARDS, ELO_BAND
from app.clients.arena_slices import (
    ARENA_SLICES,
    MAX_PARQUET_BYTES,
    SLICE_CONFIGS,
    ArenaSlice,
    ArenaSliceClient,
    parquet_url,
    parse_arena_slices,
)
from app.clients.protocols import SourceError

NEWEST = "2026-09-13"
OLDER = "2026-08-30"


def _parquet(rows: list[dict[str, Any]], *, drop: str | None = None) -> bytes:
    """A parquet file with the dataset's own columns, as `pyarrow` writes it."""
    columns: dict[str, list[Any]] = {
        "model_name": [r["model_name"] for r in rows],
        "organization": ["org" for _ in rows],
        "license": ["proprietary" for _ in rows],
        "rating": [r["rating"] for r in rows],
        "rating_lower": [r["rating"] - 5 for r in rows],
        "rating_upper": [r["rating"] + 5 for r in rows],
        "variance": [1.0 for _ in rows],
        "vote_count": [1000 for _ in rows],
        "rank": [1 for _ in rows],
        "category": [r["category"] for r in rows],
        "leaderboard_publish_date": [r.get("date", NEWEST) for r in rows],
    }
    if drop is not None:
        del columns[drop]
    sink = io.BytesIO()
    pq.write_table(pa.table(columns), sink)
    return sink.getvalue()


def _row(name: str, rating: float, category: str, date: str = NEWEST) -> dict[str, Any]:
    return {"model_name": name, "rating": rating, "category": category, "date": date}


LEGAL = ArenaSlice("text", "industry_legal_and_government", measured_rows=375)
OCR = ArenaSlice("vision", "ocr", measured_rows=108)
MULTI = ArenaSlice("text", "multi_turn", measured_rows=400)


# --- the parse -----------------------------------------------------------------------------------


def test_each_declared_slice_gets_its_own_rows_and_overall_is_not_one_of_them() -> None:
    raw = _parquet([
        _row("a", 1400.0, "overall"),
        _row("a", 1390.0, "industry_legal_and_government"),
        _row("b", 1380.0, "industry_legal_and_government"),
        _row("a", 1370.0, "multi_turn"),
        _row("c", 1360.0, "exclude_ties"),
    ])
    rows, skipped = parse_arena_slices(raw, [LEGAL, MULTI], source_url="u")

    assert {r.raw_name: r.score for r in rows[LEGAL.source_name]} == {"a": 1390.0, "b": 1380.0}
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a"]
    assert set(rows) == {LEGAL.source_name, MULTI.source_name}
    for board in (LEGAL, MULTI):
        for row in rows[board.source_name]:
            assert (row.source, row.benchmark, row.metric) == (board.source_name, board.benchmark, "elo")
            assert row.run_date == NEWEST
        assert skipped[board.source_name] == 0


def test_a_slice_is_served_only_on_its_configs_newest_date() -> None:
    """FP-M2-2, per slice: `vision/creative_writing` has 34 rows and none on the newest date."""
    raw = _parquet([
        _row("a", 1400.0, "overall"),
        _row("a", 1300.0, "multi_turn", OLDER),
        _row("b", 1310.0, "multi_turn", OLDER),
        _row("a", 1390.0, "industry_legal_and_government"),
    ])
    rows, skipped = parse_arena_slices(raw, [LEGAL, MULTI], source_url="u")

    assert rows[MULTI.source_name] == []
    assert skipped[MULTI.source_name] == 2, "a stale slice is refused AND counted"
    assert [r.raw_name for r in rows[LEGAL.source_name]] == ["a"]


def test_a_slice_absent_from_the_file_parses_to_nothing_rather_than_failing_the_rest() -> None:
    raw = _parquet([_row("a", 1390.0, "industry_legal_and_government")])
    rows, _ = parse_arena_slices(raw, [LEGAL, MULTI], source_url="u")
    assert rows[MULTI.source_name] == []
    assert len(rows[LEGAL.source_name]) == 1


@pytest.mark.parametrize("rating", [float("inf"), float("nan"), ELO_BAND[1] + 1, -1.0])
def test_a_rating_outside_the_elo_band_is_refused_and_counted(rating: float) -> None:
    raw = _parquet([
        _row("a", 1390.0, "industry_legal_and_government"),
        _row("bad", rating, "industry_legal_and_government"),
    ])
    rows, skipped = parse_arena_slices(raw, [LEGAL], source_url="u")
    assert [r.raw_name for r in rows[LEGAL.source_name]] == ["a"]
    assert skipped[LEGAL.source_name] == 1


def test_a_file_with_no_readable_date_is_refused_rather_than_served_undated() -> None:
    """P1 review M1: with no date, "the newest snapshot" cannot be chosen, and a file carrying two
    snapshots would serve a stale-but-higher rating as current. So the file fails closed."""
    raw = _parquet([
        _row("a", 1390.0, "industry_legal_and_government", ""),
        _row("b", 1380.0, "industry_legal_and_government", ""),
    ])
    with pytest.raises(SourceError, match="date"):
        parse_arena_slices(raw, [LEGAL], source_url="u")


def test_a_date_column_typed_as_a_timestamp_is_read_as_its_date() -> None:
    """P1 review M1: the live column is a string today; a typed column must not read as undated."""
    import datetime as dt

    columns = {
        "model_name": ["a", "b"],
        "rating": [1390.0, 1380.0],
        "category": ["multi_turn", "multi_turn"],
        "leaderboard_publish_date": [dt.datetime(2026, 9, 13), dt.datetime(2026, 8, 30)],
    }
    sink = io.BytesIO()
    pq.write_table(pa.table(columns), sink)
    rows, skipped = parse_arena_slices(sink.getvalue(), [MULTI], source_url="u")
    assert [(r.raw_name, r.run_date) for r in rows[MULTI.source_name]] == [("a", NEWEST)]
    assert skipped[MULTI.source_name] == 1


def test_a_file_that_is_not_parquet_is_a_source_error() -> None:
    with pytest.raises(SourceError, match="parquet"):
        parse_arena_slices(b"<html>rate limited</html>", [LEGAL], source_url="u")


@pytest.mark.parametrize("column", ["model_name", "rating", "category", "leaderboard_publish_date"])
def test_a_missing_column_is_a_source_error(column: str) -> None:
    raw = _parquet([_row("a", 1390.0, "industry_legal_and_government")], drop=column)
    with pytest.raises(SourceError, match=column):
        parse_arena_slices(raw, [LEGAL], source_url="u")


def test_a_file_declaring_more_rows_than_the_bound_is_refused_before_it_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The metadata is checked BEFORE the table is materialised: a small compressed file can
    declare a huge table, and reading it first is paying for it first."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_PARQUET_ROWS", 2)
    raw = _parquet([_row(f"m{i}", 1300.0 + i, "multi_turn") for i in range(3)])
    with pytest.raises(SourceError, match="rows"):
        parse_arena_slices(raw, [MULTI], source_url="u")


def test_a_file_declaring_more_uncompressed_bytes_than_the_bound_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_UNCOMPRESSED_BYTES", 10)
    raw = _parquet([_row("a", 1390.0, "multi_turn")])
    with pytest.raises(SourceError, match="bytes"):
        parse_arena_slices(raw, [MULTI], source_url="u")


def test_a_duplicate_name_on_one_slice_keeps_the_best_rating_and_counts_the_other() -> None:
    raw = _parquet([_row("a", 1300.0, "multi_turn"), _row("a", 1350.0, "multi_turn")])
    rows, skipped = parse_arena_slices(raw, [MULTI], source_url="u")
    assert [(r.raw_name, r.score) for r in rows[MULTI.source_name]] == [("a", 1350.0)]
    assert skipped[MULTI.source_name] == 1


# --- the download --------------------------------------------------------------------------------


@respx.mock
def test_the_client_downloads_its_configs_own_parquet_file() -> None:
    body = _parquet([_row("a", 1390.0, "industry_legal_and_government")])
    route = respx.get(parquet_url("text")).mock(return_value=httpx.Response(200, content=body))
    client = ArenaSliceClient("text")
    assert client.fetch_bytes() == body
    assert route.call_count == 1
    assert client.url == parquet_url("text")
    assert "lmarena-ai/leaderboard-dataset" in client.url


@respx.mock
def test_a_download_over_the_cap_is_cut_off() -> None:
    respx.get(parquet_url("vision")).mock(
        return_value=httpx.Response(200, content=b"x" * (MAX_PARQUET_BYTES + 1))
    )
    with pytest.raises(SourceError, match="exceeded"):
        ArenaSliceClient("vision").fetch_bytes()


def test_an_unknown_config_is_refused() -> None:
    with pytest.raises(SourceError, match="config"):
        ArenaSliceClient("text_style_control")


# --- the declared table --------------------------------------------------------------------------


def test_the_table_is_the_35_boards_the_owner_ruled() -> None:
    """Owner ruling 2026-09-24: every meaningful slice (26 `text`, 9 `vision`)."""
    by_config = {c: {s.category for s in ARENA_SLICES if s.config == c} for c in SLICE_CONFIGS}
    assert len(by_config["text"]) == 26
    assert len(by_config["vision"]) == 9
    assert len(ARENA_SLICES) == 35


def test_the_left_out_slices_stay_out() -> None:
    """Each with its reason in the plan: already read, a method variant, an intersection, stale."""
    declared = {(s.config, s.category) for s in ARENA_SLICES}
    for left_out in [
        ("text", "overall"),
        ("vision", "overall"),
        ("text", "exclude_ties"),
        ("text", "hard_prompts_english"),
        ("vision", "creative_writing"),
    ]:
        assert left_out not in declared


def test_every_board_has_its_own_source_id_and_benchmark() -> None:
    """`category_ranking` joins on benchmark: a shared label merges two boards (M14-W2)."""
    ids = [s.source_name for s in ARENA_SLICES]
    labels = [s.benchmark for s in ARENA_SLICES]
    assert len(set(ids)) == len(ids)
    assert len(set(labels)) == len(labels)
    overall_ids = {b.id for b in ARENA_BOARDS.values()}
    overall_labels = {b.benchmark for b in ARENA_BOARDS.values()}
    assert not set(ids) & overall_ids
    assert not set(labels) & overall_labels


def test_every_floor_is_below_its_measured_count_and_above_zero() -> None:
    for board in ARENA_SLICES:
        assert 0 < board.minimum_rows < board.measured_rows, board


# --- the serving process -------------------------------------------------------------------------


def test_the_serving_process_never_loads_pyarrow() -> None:
    """D-154: the server imports `app.clients.*` (W-125), so the import must stay inside the parse."""
    probe = "import sys, app.adapter.main\nprint('pyarrow' in sys.modules)"
    loaded = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True,
        env={**os.environ, "APP_ENV": "test", "PYTHONPATH": "src"},
    ).stdout.strip()
    assert loaded == "False"
