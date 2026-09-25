"""M17-W2 P2 -- the build stores each category slice as its own board (#22, D-156, D-164).

Every test here injects a fake download (`app.clients.fakes.fake_slice_client`); the network is
never reached. Tests without the `slices` marker build with no slices at all (`tests/conftest.py`).
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pytest

from app.clients.arena_slices import ARENA_SLICES, ArenaSlice
from app.clients.fakes import fake_slice_client, slice_parquet
from app.workflows import build as build_mod
from app.workflows.build import Carry, build
from app.workflows.categories import CATEGORIES
from app.workflows.schema import connect

from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

NEWEST = "2026-09-13"
NOW = dt.datetime(2026, 9, 24, 22, 0, tzinfo=dt.UTC)

LEGAL = ArenaSlice("text", "industry_legal_and_government", measured_rows=4)
MULTI = ArenaSlice("text", "multi_turn", measured_rows=4)
OCR = ArenaSlice("vision", "ocr", measured_rows=4)
BOARDS = (LEGAL, MULTI, OCR)


def _file(categories: dict[str, int], *, overall: int = 3) -> bytes:
    """`n` rows per category, plus an `overall` board the slices must never be confused with."""
    rows = [(f"m{i}", 1300.0 + i, "overall", NEWEST) for i in range(overall)]
    for category, n in categories.items():
        rows += [(f"m{i}", 1200.0 + i, category, NEWEST) for i in range(n)]
    return slice_parquet(rows)


def _ingest(conn: sqlite3.Connection, payloads: dict[str, bytes | None], carry: Carry | None = None):
    run = build_mod.RunContext()
    drift: list[str] = []
    reports, missing = build_mod._ingest_slices(
        conn, run, BOARDS, carry, drift, client=fake_slice_client(payloads)
    )
    return reports, missing, drift, run


def _rows(conn: sqlite3.Connection, source: str) -> list[tuple[str, str, float]]:
    return sorted(conn.execute(
        "SELECT raw_name, benchmark, score FROM scores WHERE source = ?", (source,)).fetchall())


@pytest.mark.slices
def test_each_slice_is_stored_under_its_own_source_and_benchmark() -> None:
    conn = connect(":memory:")
    try:
        reports, missing, _, run = _ingest(conn, {
            "text": _file({LEGAL.category: 3, MULTI.category: 2}),
            "vision": _file({"ocr": 2}),
        })
        assert missing == []
        assert {r.source: r.stored for r in reports} == {
            LEGAL.source_name: 3, MULTI.source_name: 2, OCR.source_name: 2}
        assert {r.source for r in run.reports} >= {b.source_name for b in BOARDS}
        for board in BOARDS:
            assert {benchmark for _, benchmark, _ in _rows(conn, board.source_name)} == {board.benchmark}
        # No slice row lands on a benchmark a surface ranks on (`rank.py` joins on benchmark).
        served = {b for spec in CATEGORIES.values()
                  for b in (spec.primary_benchmark, spec.secondary_benchmark) if b}
        slice_benchmarks = {row[0] for row in conn.execute(
            "SELECT DISTINCT benchmark FROM scores WHERE source LIKE 'arena\\_%\\_%' ESCAPE '\\'")}
        assert slice_benchmarks and not slice_benchmarks & served
    finally:
        conn.close()


@pytest.mark.slices
def test_a_slice_under_its_floor_fails_alone() -> None:
    """LEGAL's floor is 2 (half of 4); one row is a truncated slice, not a slow day."""
    conn = connect(":memory:")
    try:
        reports, missing, drift, _ = _ingest(conn, {
            "text": _file({LEGAL.category: 1, MULTI.category: 3}),
            "vision": _file({"ocr": 2}),
        })
        assert {r.source for r in reports} == {MULTI.source_name, OCR.source_name}
        assert _rows(conn, LEGAL.source_name) == [], "a rejected slice leaves nothing behind"
        assert len(missing) == 1 and missing[0].startswith(LEGAL.source_name)
        assert "floor" in missing[0]
        assert drift and drift[0].startswith(LEGAL.source_name)
    finally:
        conn.close()


@pytest.mark.slices
def test_a_slice_far_over_its_measured_size_fails_alone() -> None:
    """Security re-look 3, S-R3-5: a slice had a floor and no ceiling, and a 230 KB file stored
    100,000 rows where 402 were declared (a 76 MB artifact, a 21 s build). LEGAL is declared at 4
    rows, so its ceiling is 16."""
    conn = connect(":memory:")
    try:
        reports, missing, _, _ = _ingest(conn, {
            "text": _file({LEGAL.category: 17, MULTI.category: 3}),
            "vision": _file({"ocr": 2}),
        })
        assert {r.source for r in reports} == {MULTI.source_name, OCR.source_name}
        assert len(missing) == 1 and missing[0].startswith(LEGAL.source_name)
        assert "ceiling" in missing[0]
    finally:
        conn.close()


@pytest.mark.slices
def test_a_failed_download_fails_every_slice_of_that_config_and_no_other() -> None:
    conn = connect(":memory:")
    try:
        reports, missing, _, _ = _ingest(conn, {"text": None, "vision": _file({"ocr": 2})})
        assert [r.source for r in reports] == [OCR.source_name]
        assert sorted(m.split(":", 1)[0] for m in missing) == sorted(
            [LEGAL.source_name, MULTI.source_name])
    finally:
        conn.close()


@pytest.mark.slices
def test_a_failed_download_carries_each_slice_on_its_own(tmp_path: Path) -> None:
    """D-156 per slice: the live artifact's rows come back for each slice of the failed config."""
    live_path = tmp_path / "live.db"
    live = connect(str(live_path))
    try:
        _ingest(live, {"text": _file({LEGAL.category: 3, MULTI.category: 2}),
                       "vision": _file({"ocr": 2})})
        live.commit()
    finally:
        live.close()

    conn = connect(":memory:")
    try:
        stamp = (NOW - dt.timedelta(days=2)).isoformat(timespec="seconds")
        carry = Carry(live=live_path, now=NOW,
                      last_ok={b.source_name: stamp for b in BOARDS})
        _, missing, _, _ = _ingest(conn, {"text": None, "vision": _file({"ocr": 2})}, carry)
        assert missing == []
        assert set(carry.carried) == {LEGAL.source_name, MULTI.source_name}
        assert len(_rows(conn, LEGAL.source_name)) == 3
        assert len(_rows(conn, MULTI.source_name)) == 2
    finally:
        conn.close()


@pytest.mark.slices
def test_build_reads_the_slice_table_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    """The seam reaches the caller: `build()` reads `ARENA_SLICES` and `ARENA_SLICE_CLIENT` from the
    module when it runs, as it reads every other source table (M8's lesson)."""
    monkeypatch.setattr(build_mod, "ARENA_SLICES", (OCR,))
    monkeypatch.setattr(build_mod, "ARENA_SLICE_CLIENT",
                        fake_slice_client({"vision": _file({"ocr": 3})}))
    conn = connect(":memory:")
    try:
        report = build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML,
                       sources=_sources(), minimum_models=2)
        assert OCR.source_name in {r.source for r in report.sources}
        assert len(_rows(conn, OCR.source_name)) == 3
    finally:
        conn.close()


def test_an_unmarked_test_builds_with_no_slices_so_it_never_reaches_the_network() -> None:
    """`tests/conftest.py`'s declaration, asserted where it would otherwise be assumed."""
    assert build_mod.ARENA_SLICES == ()


@pytest.mark.slices
def test_the_production_table_is_the_one_the_build_reads() -> None:
    assert build_mod.ARENA_SLICES == ARENA_SLICES
    assert len(ARENA_SLICES) == 35


@pytest.mark.slices
def test_every_slice_is_attributed() -> None:
    """CC-BY-4.0: a served row with no citation raises at request time (`rank.SOURCE_ATTRIBUTION`).
    Derived from the declared table, never from an `arena_` prefix."""
    from app.clients.arena import ATTRIBUTION
    from app.workflows.rank import SOURCE_ATTRIBUTION

    for board in ARENA_SLICES:
        assert SOURCE_ATTRIBUTION.get(board.source_name) == ATTRIBUTION, board.source_name


@pytest.mark.slices
def test_a_hostile_file_fails_its_slices_and_never_the_build() -> None:
    """Wave review B1 / security S1, through the build: the review's 1.3 KB file, a date32 at its
    maximum, ends as a missing slice, never as an exception out of the ingest."""
    import io

    import pyarrow as pa
    import pyarrow.parquet as pq

    sink = io.BytesIO()
    pq.write_table(pa.table({
        "model_name": ["a", "b"], "rating": [1390.0, 1380.0],
        "category": [LEGAL.category, MULTI.category],
        "leaderboard_publish_date": pa.array([2**31 - 1] * 2, type=pa.date32()),
    }), sink)
    conn = connect(":memory:")
    try:
        reports, missing, _, _ = _ingest(conn, {"text": sink.getvalue(), "vision": _file({"ocr": 2})})
        assert [r.source for r in reports] == [OCR.source_name]
        assert sorted(m.split(":", 1)[0] for m in missing) == sorted(
            [LEGAL.source_name, MULTI.source_name])
    finally:
        conn.close()


@pytest.mark.slices
def test_slice_rows_do_not_crowd_the_unmatched_names_queue() -> None:
    """Wave review K2: the queue ranks names by row count, and a slice repeats its `overall`
    board's names up to 26 times. Slice rows add no name `overall` lacks, so they are not counted."""
    conn = connect(":memory:")
    try:
        conn.executemany(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
            "source_url, observed_at) VALUES (?, ?, 'elo', 1, 'h', 'unspecified', ?, 'u', 'z')",
            [("only-in-slices", b.benchmark, b.source_name) for b in BOARDS]
            + [("in-overall", "Arena text", "arena")])
        assert build_mod._most_unmatched(conn, set()) == ["in-overall"]
    finally:
        conn.close()

