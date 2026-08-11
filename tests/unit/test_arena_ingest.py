"""Arena leaderboard ingestion tests — cite REQ-ING-007 and REQ-ING-004."""

from __future__ import annotations

import json

import pytest

from app.clients.arena import ATTRIBUTION, parse_arena
from app.clients.fakes import FakeRawSource
from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, ingest_arena
from app.workflows.schema import connect


def _wrap(rows: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "rows": [{"row_idx": i, "row": r} for i, r in enumerate(rows)],
            "num_rows_total": len(rows),
        }
    )


FIXTURE = _wrap(
    [
        {
            "model_name": "gpt-5-chat",
            "rating": 1420.5,
            "rank": 1,
            "vote_count": 50000,
            "category": "overall",
            "leaderboard_publish_date": "2026-08-01",
        },
        {
            "model_name": "claude-4.5-opus",
            "rating": 1415.2,
            "rank": 2,
            "vote_count": 42000,
            "category": "overall",
            "leaderboard_publish_date": "2026-08-01",
        },
        {
            "model_name": "gemini-3-pro",
            "rating": 1418.0,
            "rank": 1,
            "category": "creative_writing",
            "leaderboard_publish_date": "2026-08-01",
        },
        {"model_name": "broken-row", "rating": None, "category": "overall"},
        {"model_name": "gpt-5-chat", "rating": 1400.0, "category": "overall"},
    ]
)


def test_prefers_overall_category_slice() -> None:
    """REQ-ING-007: the 'overall' slice ranks; other category slices are skipped."""
    rows, skipped = parse_arena(FIXTURE)
    names = {r.raw_name for r in rows}
    assert names == {"gpt-5-chat", "claude-4.5-opus"}
    assert skipped == 3  # creative_writing slice + broken row + duplicate


def test_elo_stored_with_metric_and_harness() -> None:
    """REQ-ING-007: rating → metric='elo', harness='arena-crowd', publish date kept."""
    rows, _ = parse_arena(FIXTURE)
    top = next(r for r in rows if r.raw_name == "gpt-5-chat")
    assert top.benchmark == "Arena text"
    assert top.metric == "elo"
    assert top.harness == "arena-crowd"
    assert top.score == 1420.5  # duplicate at 1400 lost to keep-best
    assert top.run_date == "2026-08-01"


def test_only_newest_snapshot_is_kept() -> None:
    """FP-M2-2 red test: several publish dates in one split → only the newest ranks.

    Live catch 2026-08-11: text/latest holds many snapshots, so keeping the highest
    rating per model could surface a STALE-but-higher score as current.
    """
    payload = _wrap(
        [
            {
                "model_name": "m1",
                "rating": 1500.0,
                "category": "overall",
                "leaderboard_publish_date": "2026-06-10",
            },
            {
                "model_name": "m1",
                "rating": 1450.0,
                "category": "overall",
                "leaderboard_publish_date": "2026-08-10",
            },
            {
                "model_name": "m2",
                "rating": 1400.0,
                "category": "overall",
                "leaderboard_publish_date": "2026-08-10",
            },
        ]
    )
    rows, skipped = parse_arena(payload)
    by_name = {r.raw_name: r for r in rows}
    assert set(by_name) == {"m1", "m2"}
    assert by_name["m1"].score == 1450.0, "newest snapshot wins over the higher old rating"
    assert by_name["m1"].run_date == "2026-08-10"
    assert skipped == 1  # the June row


def test_no_overall_slice_falls_back_to_all_rows() -> None:
    """Tolerance branch: a dataset without a 'full' category still parses."""
    payload = _wrap([{"model_name": "m1", "rating": 1300.0, "category": "english"}])
    rows, skipped = parse_arena(payload)
    assert len(rows) == 1
    assert skipped == 0


def test_ingest_stores_and_replaces_deterministically() -> None:
    """REQ-ING-004: provenance + working-set replacement for arena."""
    conn = connect()
    ingest_arena(conn, FakeRawSource("arena", FIXTURE), RunContext(observed_at="t1"))
    report = ingest_arena(conn, FakeRawSource("arena", FIXTURE), RunContext(observed_at="t2"))
    assert report.stored == 2
    stamps = {
        r[0] for r in conn.execute("SELECT DISTINCT observed_at FROM scores WHERE source='arena'")
    }
    assert stamps == {"t2"}


def test_attribution_constant_names_license() -> None:
    """REQ-ING-008: the attribution string names the dataset and CC-BY-4.0."""
    assert "CC-BY-4.0" in ATTRIBUTION
    assert "lmarena-ai/leaderboard-dataset" in ATTRIBUTION


def test_dropped_wrappers_are_counted() -> None:
    """W2 review: non-dict / row-less wrapper entries count as skipped, never silent."""
    payload = json.dumps(
        {
            "rows": [
                {"row": {"model_name": "m1", "rating": 1300.0, "category": "overall"}},
                "not-a-dict",
                {"row_idx": 9},
            ],
            "num_rows_total": 3,
        }
    )
    rows, skipped = parse_arena(payload)
    assert len(rows) == 1
    assert skipped == 2


def test_malformed_payload_fails_loudly() -> None:
    with pytest.raises(SourceError, match="malformed"):
        parse_arena('{"nope": 1}')
    with pytest.raises(SourceError, match="not a list"):
        parse_arena('{"rows": "oops"}')
