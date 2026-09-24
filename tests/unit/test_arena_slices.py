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
from app.clients.fakes import slice_parquet
from app.clients.protocols import SourceError

NEWEST = "2026-09-13"
OLDER = "2026-08-30"


def _parquet(rows: list[dict[str, Any]], *, drop: str | None = None) -> bytes:
    """The canonical fake's file (`app.clients.fakes.slice_parquet`), from this file's row dicts."""
    return slice_parquet(
        [(r["model_name"], r["rating"], r["category"], r.get("date", NEWEST)) for r in rows],
        drop=drop,
    )


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


def _typed(**overrides: Any) -> bytes:
    """A two-row file whose columns can be given any arrow type (the review's hostile files)."""
    columns: dict[str, Any] = {
        "model_name": pa.array(["a", "b"]),
        "rating": pa.array([1390.0, 1380.0]),
        "category": pa.array(["multi_turn", "multi_turn"]),
        "leaderboard_publish_date": pa.array([NEWEST, NEWEST]),
    }
    columns.update(overrides)
    sink = io.BytesIO()
    pq.write_table(pa.table(columns), sink)
    return sink.getvalue()


@pytest.mark.parametrize(
    ("column", "values"),
    [
        # Wave review B1 / security S1: a date32 at its maximum made `to_pylist` raise OverflowError,
        # which is not a SourceError, so the build re-raised it and the whole nightly cycle failed.
        ("leaderboard_publish_date", pa.array([2**31 - 1] * 2, type=pa.date32())),
        ("leaderboard_publish_date", pa.array([2**62] * 2, type=pa.date64())),
        ("leaderboard_publish_date", pa.array([0, 1], type=pa.timestamp("s"))),
        ("rating", pa.array(["1390", "1380"])),
        ("model_name", pa.array([1, 2])),
        ("category", pa.array([1.0, 2.0])),
    ],
)
def test_a_column_of_an_unexpected_type_is_refused_before_it_is_read(
    column: str, values: Any
) -> None:
    """The live file's types (string, double, string, string) are the only ones read: anything else
    is a changed file, refused as one before a value is converted."""
    with pytest.raises(SourceError, match=f"column {column} has type"):
        parse_arena_slices(_typed(**{column: values}), [MULTI], source_url="u")


def test_any_failure_inside_the_reader_is_reported_as_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security S1: an allowlist of exception classes is how OverflowError escaped. Whatever the
    library raises inside the reader becomes an error the parent turns into a SourceError."""
    from app.clients import parquet_reader

    def explode(*_: object, **__: object) -> None:
        raise OverflowError("date out of range")

    monkeypatch.setattr(pq.ParquetFile, "iter_batches", explode)
    answer = parquet_reader.read_rows(_parquet([_row("a", 1390.0, "multi_turn")]), _limits())
    assert "OverflowError" in answer["error"]


def _limits() -> dict[str, int]:
    import app.clients.arena_slices as module

    return module.reader_limits()


@pytest.mark.parametrize(
    ("program", "match"),
    [
        ("import os; os.abort()", "reader"),               # a native crash, as a segfault would be
        ("print('not json')", "reader"),                    # an answer that is not the protocol
        ("import sys; sys.exit(7)", "reader"),
    ],
)
def test_a_reader_that_fails_is_a_source_error(
    monkeypatch: pytest.MonkeyPatch, program: str, match: str
) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "_reader_command", lambda: [sys.executable, "-c", program])
    with pytest.raises(SourceError, match=match):
        parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")


def test_a_reader_that_hangs_is_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "_reader_command",
                        lambda: [sys.executable, "-c", "import time; time.sleep(30)"])
    monkeypatch.setattr(module, "READER_TIMEOUT_S", 0.5)
    with pytest.raises(SourceError, match="seconds"):
        parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")


def test_a_file_that_would_exhaust_memory_is_stopped_at_the_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Re-review BLOCKING-R1 / S-R1: pyarrow decodes a whole column chunk before any check in
    Python runs, so 256 distinct 1 MiB names decode to 256 MiB whatever the batch size. The
    footer's claim is taken away (as a forged footer would) and the ceiling is what stops it."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_UNCOMPRESSED_BYTES", 2**40)
    monkeypatch.setattr(module, "MAX_READER_RSS", 160 * 2**20)
    names = [f"{i:08d}" + "a" * (2**20 - 8) for i in range(256)]
    sink = io.BytesIO()
    pq.write_table(pa.table({
        "model_name": pa.array(names), "rating": [1200.0] * 256,
        "category": ["multi_turn"] * 256, "leaderboard_publish_date": [NEWEST] * 256,
    }), sink, compression="zstd", use_dictionary=False)
    with pytest.raises(SourceError, match="memory"):
        parse_arena_slices(sink.getvalue(), [MULTI], source_url="u")


def test_rows_are_counted_as_they_are_read_not_as_the_footer_declares(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Security re-look S-R2: the footer's row count can be forged. With the footer's own check
    taken out, the count kept while reading still stops the read."""
    from app.clients import parquet_reader

    monkeypatch.setattr(parquet_reader, "_check_footer", lambda *_: None)
    limits = {**_limits(), "max_rows": 2}
    answer = parquet_reader.read_rows(
        _parquet([_row(f"m{i}", 1300.0, "multi_turn") for i in range(3)]), limits)
    assert "rows" in answer["error"]


def test_a_value_longer_than_any_real_one_is_refused() -> None:
    """Security S2: one long value, repeated by dictionary encoding, grows by rows x length when
    the rows become Python strings. A real model name is well under the bound."""
    raw = _parquet([_row("x" * 1000, 1390.0, "multi_turn")])
    with pytest.raises(SourceError, match="longer"):
        parse_arena_slices(raw, [MULTI], source_url="u")


def test_decoding_past_the_budget_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security S2: the footer's sizes are the writer's claims. What is actually decoded is counted
    batch by batch, and the read stops at the budget."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_DECODED_BYTES", 64)
    raw = _parquet([_row(f"m{i}", 1300.0 + i, "multi_turn") for i in range(50)])
    with pytest.raises(SourceError, match="decoded"):
        parse_arena_slices(raw, [MULTI], source_url="u")


@pytest.mark.parametrize("stray", ["2026-09-1~", "2026-09-2 ", "not a date", "2026-13-40"])
def test_a_date_that_is_not_a_date_never_becomes_the_newest(stray: str) -> None:
    """Security re-look S-R4: compared as text, `2026-09-1~` sorts above every real date."""
    raw = _parquet([
        _row("a", 1390.0, "multi_turn"),
        _row("z", 1500.0, "industry_legal_and_government", stray),
    ])
    rows, skipped = parse_arena_slices(raw, [MULTI, LEGAL], source_url="u")
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a"]
    assert rows[LEGAL.source_name] == [] and skipped[LEGAL.source_name] == 1


def test_a_row_dated_in_the_future_is_refused_and_does_not_move_the_newest_date() -> None:
    """Security S4: the newest date was an unchecked maximum, so one stray `9999-12-31` row would
    have darkened every slice of the config."""
    raw = _parquet([
        _row("a", 1390.0, "multi_turn"),
        _row("b", 1380.0, "multi_turn"),
        _row("z", 1500.0, "industry_legal_and_government", "9999-12-31"),
    ])
    rows, skipped = parse_arena_slices(raw, [MULTI, LEGAL], source_url="u")
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a", "b"]
    assert rows[LEGAL.source_name] == []
    assert skipped[LEGAL.source_name] == 1


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


@pytest.mark.slice_download
@respx.mock
def test_the_client_downloads_its_configs_own_parquet_file() -> None:
    body = _parquet([_row("a", 1390.0, "industry_legal_and_government")])
    route = respx.get(parquet_url("text")).mock(return_value=httpx.Response(200, content=body))
    client = ArenaSliceClient("text")
    assert client.fetch_bytes() == body
    assert route.call_count == 1
    assert client.url == parquet_url("text")
    assert "lmarena-ai/leaderboard-dataset" in client.url


@pytest.mark.slice_download
@respx.mock
def test_a_download_over_the_cap_is_cut_off() -> None:
    respx.get(parquet_url("vision")).mock(
        return_value=httpx.Response(200, content=b"x" * (MAX_PARQUET_BYTES + 1))
    )
    with pytest.raises(SourceError, match="exceeded"):
        ArenaSliceClient("vision").fetch_bytes()


@pytest.mark.slice_download
@respx.mock
def test_a_redirect_to_a_malformed_host_is_a_source_error() -> None:
    """Security re-look S-R3: `Location: http://xn--/x` raised IDNAError out of the shared download
    helper, which ended the build and lost the other config's valid slices."""
    respx.get(parquet_url("text")).mock(
        return_value=httpx.Response(302, headers={"Location": "http://xn--/x"}))
    with pytest.raises(SourceError, match="arena_slices_text"):
        ArenaSliceClient("text").fetch_bytes()


def test_no_test_downloads_a_slice_file() -> None:
    """Re-review MINOR-R2: the suite's guard sits on the client itself, so every path to a download
    (the build's default client, `fetch_slices`, `measure_slices`) meets it. Checked by identity,
    so this test never downloads anything even when the guard is gone."""
    assert ArenaSliceClient.fetch_bytes.__name__ == "_tests_never_reach_the_network"


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


def _loads_pyarrow(module: str) -> bool:
    probe = f"import sys, {module}\nprint('pyarrow' in sys.modules)"
    return subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True,
        env={**os.environ, "APP_ENV": "test", "PYTHONPATH": "src"},
    ).stdout.strip() == "True"


@pytest.mark.parametrize("module", ["app.adapter.main", "app.clients.arena_slices"])
def test_neither_the_server_nor_the_slice_module_loads_pyarrow(module: str) -> None:
    """D-154: the server imports `app.clients.*` (W-125), so pyarrow is imported inside the read.

    The server imports `arena_slices` itself (through `rank.SOURCE_ATTRIBUTION`), so both halves
    fail on a top-level `import pyarrow`. The module half stays: it holds the rule even if the
    server's path to the module goes away (P1 review M2).
    """
    assert not _loads_pyarrow(module)
