"""M17 closure, Stage 4.0 security seat MINOR-2 -- every client's rows meet one rule where they are stored.

Two sibling parsers kept upstream text as a date: `arena.py` truncated `<script>alert(1)</script>` to
`<script>al`, and `swebench.py` kept 3,960 characters of prose. `/v1/boards` then served either one as
`evidence_date`, and the W5 detail screen shows the Arena one. SWE-bench also accepted `Infinity` as a
score, which made coding's derived floor `null` and `/v1/recommendations?task=coding` answer 500.
`epoch_board.py` and `arena_slices.py` had each been fixed on their own. The rule now sits where every
client meets (`ingest._store_scores`), so the next client inherits it instead of re-deriving it.
"""

from __future__ import annotations

import json
import math

import pytest

from app.clients.arena import parse_arena
from app.clients.protocols import SourceError
from app.clients.swebench import parse_verified
from app.workflows.ingest import RunContext, _store_scores
from app.workflows.schema import ScoreRow, connect

RUN = RunContext(observed_at="2026-09-29T00:00:00+00:00")


def _row(**over: object) -> ScoreRow:
    base: dict[str, object] = {
        "raw_name": "m", "benchmark": "B", "metric": "elo", "score": 1.0, "harness": "h",
        "run_date": None, "cost_total": None, "source": "arena", "source_url": "u",
    }
    base.update(over)
    return ScoreRow(**base)  # type: ignore[arg-type]


def _dates(conn: object) -> list[object]:
    return [r[0] for r in conn.execute("SELECT run_date FROM scores ORDER BY raw_name")]  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("raw", "stored"),
    [
        ("2026-09-18", "2026-09-18"),
        ("2026-09-18T12:00:00+00:00", "2026-09-18"),
        pytest.param("<script>alert(1)</script>", None, id="script-tag"),
        ("2026-13-40", None),
        pytest.param("x" * 3960, None, id="3960-characters-of-prose"),
        ("", None),
    ],
)
def test_a_stored_date_is_a_calendar_date_or_nothing(raw: str, stored: str | None) -> None:
    conn = connect(":memory:")
    _store_scores(conn, "arena", [_row(run_date=raw)], RUN)
    assert _dates(conn) == [stored]


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_a_non_finite_score_refuses_the_source(value: float) -> None:
    """Refused loudly, not dropped: the source then carries its last good data (D-156)."""
    conn = connect(":memory:")
    with pytest.raises(SourceError, match="finite"):
        _store_scores(conn, "swebench", [_row(score=value, source="swebench")], RUN)
    assert conn.execute("SELECT count(*) FROM scores").fetchone()[0] == 0


def test_the_arena_parsers_date_is_bounded_where_it_is_stored() -> None:
    raw = json.dumps({"num_rows_total": 1, "rows": [{"row_idx": 0, "row": {
        "model_name": "m1", "rating": 1400.0, "rank": 1, "vote_count": 100, "category": "overall",
        "leaderboard_publish_date": "<script>alert(1)</script>"}}]})
    rows, _ = parse_arena(raw)
    assert rows, "the fixture must reach the store, or this proves nothing"
    conn = connect(":memory:")
    _store_scores(conn, "arena", rows, RUN)
    assert _dates(conn) == [None]


def test_the_swebench_parsers_date_and_infinity_are_bounded_where_they_are_stored() -> None:
    prose = json.dumps({"leaderboards": [{"name": "Verified", "results": [
        {"name": "Agent + Model", "resolved": 50.0, "date": "prose " * 660}]}]})
    rows, _ = parse_verified(prose)
    assert rows
    conn = connect(":memory:")
    _store_scores(conn, "swebench", rows, RUN)
    assert _dates(conn) == [None]

    infinite = json.dumps({"leaderboards": [{"name": "Verified", "results": [
        {"name": "Agent + Model", "resolved": float("inf")}]}]})
    rows, _ = parse_verified(infinite)
    assert rows
    with pytest.raises(SourceError, match="finite"):
        _store_scores(connect(":memory:"), "swebench", rows, RUN)


def test_a_missing_score_is_refused_as_a_source_error_not_a_type_error() -> None:
    """M17 closure Tester N3 (#92): `math.isfinite(None)` raised `TypeError`, which no caller turns
    into a failed SOURCE, so a parser that yielded no score ended the whole build."""
    with pytest.raises(SourceError, match="probe"):
        _store_scores(connect(), "probe", [_row(score=None)], RunContext(observed_at="t"))


def test_a_row_the_schema_refuses_is_a_source_error() -> None:
    """N3's other half: the `IntegrityError` path, which no test reached, aborts the SOURCE."""
    conn = connect()
    conn.execute("CREATE TRIGGER refuse BEFORE INSERT ON scores BEGIN SELECT RAISE(ABORT, 'no'); END")
    with pytest.raises(SourceError):
        _store_scores(conn, "probe", [_row()], RunContext(observed_at="t"))
