"""M17-W3 P2 (#37, #24) -- the six Agent Arena configs become boards, on their own metric.

Measured 2026-09-25: each `agent*` config's `latest` file has 43 rows, one category (`overall`), and
IPS scores (τ̂) in a `score` column -- not Bradley-Terry Elo in `rating`, per the dataset card. The
scores run from -0.25 to 0.35, so an Elo board's band (0 to 5000) would refuse half of them. They
are stored under the metric `ips`, each board with its own label, and can never meet an Elo board
in one ranking (D-105).
"""

from __future__ import annotations

import pytest

from app.clients.arena import ELO_BAND, IPS_BAND, score_rows
from app.clients.arena_slices import ARENA_SLICES, SLICE_CONFIGS, parse_arena_slices
from app.clients.fakes import slice_parquet
from app.clients.protocols import SourceError
from app.workflows.categories import CATEGORIES

AGENT_CONFIGS = ("agent", "agent_bash_recovery_steps", "agent_praise_complaint",
                 "agent_steerability", "agent_task_outcome_explicit", "agent_tool_hallucination")
AGENT = [board for board in ARENA_SLICES if board.metric == "ips"]
NEWEST = "2026-09-24"


def test_the_six_agent_boards_are_declared_on_their_own_metric() -> None:
    assert sorted(board.config for board in AGENT) == sorted(AGENT_CONFIGS)
    assert set(AGENT_CONFIGS) <= set(SLICE_CONFIGS)
    for board in AGENT:
        assert (board.category, board.value_column, board.measured_rows) == ("overall", "score", 43)
        assert board.source_name == f"arena_{board.config}"
        assert board.benchmark.startswith("Agent Arena")
        assert (board.minimum_rows, board.maximum_rows) == (21, 172)


def test_an_ips_board_never_shares_a_label_with_an_elo_board_or_a_surface() -> None:
    """D-105: rankings join on benchmark and metric. An IPS label that an Elo board or a surface
    also used would put two scales into one ranking."""
    ips = {board.benchmark for board in AGENT}
    elo = {board.benchmark for board in ARENA_SLICES if board.metric == "elo"}
    served = {b for spec in CATEGORIES.values() for b in (spec.primary_benchmark, spec.secondary_benchmark) if b}
    assert len(ips) == len(AGENT) and not ips & elo and not ips & served
    assert all(spec.metric != "ips" for spec in CATEGORIES.values())


def _agent_file(scores: list[float], *, column: str = "score") -> bytes:
    import io

    import pyarrow as pa
    import pyarrow.parquet as pq

    n = len(scores)
    table = pa.table({
        "model_name": [f"m{i}" for i in range(n)], column: scores,
        "category": ["overall"] * n, "leaderboard_publish_date": [NEWEST] * n,
    })
    sink = io.BytesIO()
    pq.write_table(table, sink)
    return sink.getvalue()


def test_an_agent_file_is_read_from_its_score_column_negative_values_kept() -> None:
    board = next(b for b in AGENT if b.config == "agent")
    rows, refused = parse_arena_slices(_agent_file([0.13, -0.16, 0.0]), [board], source_url="u")
    parsed = rows[board.source_name]
    assert sorted(r.score for r in parsed) == [-0.16, 0.0, 0.13]
    assert {(r.metric, r.harness, r.benchmark) for r in parsed} == {("ips", "arena-agent", board.benchmark)}
    assert refused[board.source_name] == 0


def test_an_agent_file_without_its_score_column_is_refused() -> None:
    board = next(b for b in AGENT if b.config == "agent")
    with pytest.raises(SourceError, match="score"):
        parse_arena_slices(_agent_file([0.1], column="rating"), [board], source_url="u")


def test_each_metric_keeps_its_own_band() -> None:
    """An IPS value outside (-1, 1) is refused; an Elo board still refuses a negative rating."""
    entries = [{"model_name": "a", "score": 1.5}, {"model_name": "b", "score": -0.3},
               {"model_name": "c", "rating": -5.0}]
    ips, ips_refused = score_rows(entries[:2], source="s", source_url="u", benchmark="b",
                                  value_key="score", metric="ips", harness="arena-agent", band=IPS_BAND)
    assert [r.raw_name for r in ips] == ["b"] and ips_refused == 1
    elo, elo_refused = score_rows(entries[2:], source="s", source_url="u", benchmark="b")
    assert elo == [] and elo_refused == 1
    assert ELO_BAND[0] >= 0 and IPS_BAND == (-1.0, 1.0)


def test_the_arena_slices_still_read_their_rating() -> None:
    """The column map is per config: the Elo slices are unchanged."""
    board = next(b for b in ARENA_SLICES if b.config == "text" and b.category == "multi_turn")
    raw = slice_parquet([("a", 1300.0, "multi_turn", "2026-09-13")])
    rows, _ = parse_arena_slices(raw, [board], source_url="u")
    assert [(r.score, r.metric) for r in rows[board.source_name]] == [(1300.0, "elo")]
