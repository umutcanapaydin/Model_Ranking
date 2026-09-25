"""M17-W3 P1 (#37) -- every board no surface ranks on is published and guarded (D-164).

D-164 clause 1 says "each declared board". M17-W2 fingerprinted Arena's slices only, so the five
Epoch-run boards this wave adds (SimpleQA Verified, FrontierMath Tiers 1-3 and Tier 4, chess and
mystery puzzles), which no surface ranks on, would have been neither published on a change nor
guarded. The set is DERIVED from the declared tables and `CATEGORIES`, never listed by hand.
"""

from __future__ import annotations

import pytest

from app.clients.arena_slices import ARENA_SLICES
from app.workflows import boards
from app.workflows.categories import CATEGORIES
from app.workflows.refresh import ServingSummary, degradations, serving_summary, upward_anomalies
from app.workflows.schema import connect
from app.workflows.sources import EPOCH_BOARDS

NEW_EPOCH = {
    "epoch_simpleqa": ("simpleqa_verified.csv", "SimpleQA Verified"),
    "epoch_frontiermath": ("frontiermath_tiers_1_3_v2.csv", "FrontierMath Tiers 1-3"),
    "epoch_frontiermath_t4": ("frontiermath_tier_4_v2.csv", "FrontierMath Tier 4"),
    "epoch_chess": ("chess_puzzles.csv", "Chess puzzles"),
    "epoch_mystery": ("mystery_game_puzzles.csv", "Mystery game puzzles"),
}


def test_the_five_epoch_boards_the_owner_ruled_are_declared_like_gpqa() -> None:
    """Owner ruling 2026-09-25: classes A and B. Each has GPQA Diamond's shape: `mean_score` on a
    0-1 scale, dated by `Started at` (measured on the 2026-09 bundle)."""
    declared = {board.source_name: board for board in EPOCH_BOARDS}
    for source, (file, benchmark) in NEW_EPOCH.items():
        board = declared[source]
        assert (board.file, board.benchmark) == (file, benchmark)
        assert (board.score_column, board.date_column, board.scale, board.maximum) == (
            "mean_score", "Started at", "fraction", 1.0)
    labels = [board.benchmark for board in EPOCH_BOARDS]
    assert len(labels) == len(set(labels)), "two Epoch boards share a benchmark label"


def test_the_uncovered_set_is_every_declared_board_no_surface_ranks_on() -> None:
    uncovered = {board.source for board in boards.uncovered()}
    assert set(NEW_EPOCH) <= uncovered
    assert {s.source_name for s in ARENA_SLICES} <= uncovered
    used = {spec.primary_source for spec in CATEGORIES.values()}
    assert not uncovered & used, "a board a surface ranks on is fingerprinted twice"
    assert "epoch_gpqa" not in uncovered  # `expert` ranks on it


def test_the_set_is_derived_from_the_surfaces_not_listed(monkeypatch: pytest.MonkeyPatch) -> None:
    """A surface that starts ranking on a board takes it out of the set, with no edit here."""
    import dataclasses

    spec = next(iter(CATEGORIES.values()))
    taken = dataclasses.replace(spec, id="probe", primary_source="epoch_chess",
                                primary_benchmark="Chess puzzles")
    monkeypatch.setitem(CATEGORIES, "probe", taken)
    assert "epoch_chess" not in {board.source for board in boards.uncovered()}


def _store(conn, source: str, benchmark: str, names: list[str]) -> None:  # type: ignore[no-untyped-def]
    conn.executemany(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
        "source_url, observed_at) VALUES (?, ?, '% correct', ?, 'epoch', 'unspecified', ?, 'u', 'z')",
        [(name, benchmark, 50.0 + i, source) for i, name in enumerate(names)])


def test_a_change_on_an_uncovered_epoch_board_moves_the_fingerprint() -> None:
    conn = connect(":memory:")
    try:
        before = serving_summary(conn).digest
        _store(conn, "epoch_chess", "Chess puzzles", ["m0", "m1"])
        after = serving_summary(conn)
        assert after.digest != before
        assert after.boards["epoch_chess"] == frozenset({"m0", "m1"})
    finally:
        conn.close()


def test_an_uncovered_epoch_board_losing_a_quarter_is_refused_and_a_new_one_is_not() -> None:
    names = frozenset(f"m{i}" for i in range(8))
    live = ServingSummary(digest="a", surfaces={}, models={}, median_price={}, eligible={},
                          boards={"epoch_chess": names})
    shrunk = ServingSummary(digest="b", surfaces={}, models={}, median_price={}, eligible={},
                            boards={"epoch_chess": frozenset(list(names)[:5])})
    assert any("epoch_chess" in reason for reason in degradations(live, shrunk))
    empty = ServingSummary(digest="c", surfaces={}, models={}, median_price={}, eligible={})
    assert not upward_anomalies(empty, live), "a board's first night is a publish (D-164 clause 3)"


def test_a_board_a_surface_shows_only_as_secondary_evidence_is_still_a_board() -> None:
    """Wave review M2. A secondary benchmark never orders a ranking and reaches the ranked rows only
    for models that rank, so its board's losses and changes are nobody's unless they are here.
    `epoch_mmlu` is `everyday`'s secondary evidence."""
    uncovered = {board.source for board in boards.uncovered()}
    assert "epoch_mmlu" in uncovered
