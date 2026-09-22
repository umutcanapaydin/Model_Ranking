"""M13-W2: the facts a client needs in order to stop overstating, published under D-138.

REQ-UNC-001 needs the margin inside which the engine calls two models indistinguishable. REQ-UNC-002
needs the age of the second board that decides whether a pick counts as measured twice. REQ-UNC-003
needs an undated benchmark NAMED rather than described. The engine decided the first two and published
neither, so no client could render them without inventing them.

Each test here is written so that serving the WRONG number fails it, not merely serving none: a
margin that did not reproduce the engine's own `close_call` decision would be a second account of
one threshold, published somewhere new.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter
from app.workflows.categories import CATEGORIES
from app.workflows.rank import category_ranking
from app.workflows.recommend import pareto_frontier, secondary_age_days

from .test_api_v1 import _seeded_db


@pytest.fixture()
def seeded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "seeded.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    return db


def _served_categories() -> dict[str, dict]:
    response = TestClient(adapter.app).get("/v1/categories")
    assert response.status_code == 200
    return {entry["id"]: entry for entry in response.json()["categories"]}


def _raw_frontier_gap(db: Path, surface: str) -> float:
    """The gap the engine's `close_call` is decided on: RAW scores, frontier leader to runner-up."""
    conn = adapter.open_readonly(db)
    try:
        frontier = pareto_frontier(category_ranking(conn, CATEGORIES[surface]))
    finally:
        conn.close()
    assert len(frontier) > 1, "fixture assumption: a close call needs a runner-up on the frontier"
    return frontier[0].score - frontier[1].score


@pytest.mark.parametrize("side", ["inside", "outside"])
def test_the_served_margin_reproduces_the_engines_own_close_call_decision(
    seeded: Path, monkeypatch: pytest.MonkeyPatch, side: str
) -> None:
    """REQ-UNC-001, D-138: the margin a client bands with is the one the engine decides with.

    Both directions, because each catches a different wrong number. With the margin just above the
    real gap the engine declares a close call; with it just below, it does not. A route serving any
    other constant (`value_window` is the nearest wrong one) reproduces at most one of the two.
    """
    gap = _raw_frontier_gap(seeded, "coding")
    assert gap > 0.1, f"fixture assumption: the gap ({gap}) must leave room either side of it"
    margin = gap + 0.05 if side == "inside" else gap - 0.05
    monkeypatch.setitem(
        CATEGORIES, "coding", dataclasses.replace(CATEGORIES["coding"], close_call=margin)
    )

    served = _served_categories()["coding"]["close_call_margin"]
    body = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"}).json()
    answer = next(a for a in body["answers"] if a["surface"] == "coding")

    assert (answer["close_call"] is not None) == (side == "inside"), "the fixture did not steer"
    assert (gap <= served) == (
        answer["close_call"] is not None
    ), f"served margin {served} and the engine disagree about a {gap:.2f}-point gap"


def test_every_advertised_surface_publishes_its_margin_on_its_own_scale(seeded: Path) -> None:
    """All nine, because the client bands every ranking it shows and cannot band one it lacks."""
    served = _served_categories()
    for surface, spec in CATEGORIES.items():
        assert served[surface]["close_call_margin"] == spec.close_call, surface


def test_the_published_age_is_the_one_that_decided_the_count(seeded: Path) -> None:
    """REQ-UNC-002, D-138: the age a reader is shown is the engine's own, on the artifact's anchor.

    Aider polyglot's newest run is 2025-10-03 and the fixture's anchor is 2026-08-16: 317 days,
    well past the 90 at which the engine stops counting a second board.
    """
    conn = sqlite3.connect(seeded)
    conn.execute(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, run_date,"
        " source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            None,
            "an aider row",
            "Aider polyglot",
            "% correct",
            70.0,
            "aider",
            "2025-10-03",
            "aider",
            "https://aider.chat/docs/leaderboards/",
            "2026-08-16T00:00:00+00:00",
        ),
    )
    conn.commit()
    conn.close()

    served = _served_categories()
    reader = adapter.open_readonly(seeded)
    try:
        engine_age = secondary_age_days(reader, CATEGORIES["coding"])
    finally:
        reader.close()

    assert served["coding"]["secondary_benchmark"] == "Aider polyglot"
    assert served["coding"]["secondary_age_days"] == 317 == engine_age
    # A surface with no second board says so in both fields, rather than inheriting a neighbour's.
    assert served["expert"]["secondary_benchmark"] is None
    assert served["expert"]["secondary_age_days"] is None


def test_an_undated_second_board_publishes_no_age(seeded: Path) -> None:
    """`everyday`'s second board is MMLU, whose rows carry no run date: unknown, never zero.

    The rows are really there. The first version of this test ran against a fixture with no MMLU
    rows at all, so it proved only that an empty board has no age (M13-W2 review MINOR-7).
    """
    conn = sqlite3.connect(seeded)
    conn.executemany(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, run_date,"
        " source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                None,
                f"mmlu row {n}",
                "MMLU",
                "% correct",
                80.0 + n,
                "epoch",
                None,
                "epoch_mmlu",
                "https://epoch.ai/",
                "2026-08-16T00:00:00+00:00",
            )
            for n in range(3)
        ],
    )
    conn.commit()
    assert conn.execute("SELECT count(*) FROM scores WHERE benchmark = 'MMLU'").fetchone()[0] == 3
    conn.close()

    served = _served_categories()
    assert served["everyday"]["secondary_benchmark"] == "MMLU"
    assert served["everyday"]["secondary_age_days"] is None


def test_discovery_answers_when_the_artifact_exists_but_cannot_be_opened(
    seeded: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Tester seat's surviving mutant: `_secondary_ages` raising here stayed green.

    A file that exists and will not open is the case the `is_file()` guard does not cover, and a
    raise would turn the app's navigation route into a 500.
    """

    def refuse(_path: Path) -> sqlite3.Connection:
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(adapter, "open_readonly", refuse)
    served = _served_categories()
    assert set(served) == set(CATEGORIES)
    assert all(entry["secondary_age_days"] is None for entry in served.values())


@pytest.mark.parametrize("artifact", ["unset", "missing", "not-sqlite"])
def test_discovery_answers_without_an_artifact_and_says_the_age_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact: str
) -> None:
    """The app builds its navigation from this route; an absent artifact must not blank it.

    The margins are policy constants and still arrive. The ages are facts about an artifact that is
    not there, so they arrive as null rather than as an error or a zero.
    """
    if artifact == "unset":
        monkeypatch.delenv("MODEL_RANKING_DB", raising=False)
    elif artifact == "missing":
        monkeypatch.setenv("MODEL_RANKING_DB", str(tmp_path / "absent.db"))
    else:
        junk = tmp_path / "junk.db"
        junk.write_text("this is not a database", encoding="utf-8")
        monkeypatch.setenv("MODEL_RANKING_DB", str(junk))

    served = _served_categories()
    assert set(served) == set(CATEGORIES)
    assert all(entry["close_call_margin"] is not None for entry in served.values())
    assert all(entry["secondary_age_days"] is None for entry in served.values())


def test_an_undated_surface_names_its_benchmark_on_the_live_route(seeded: Path) -> None:
    """REQ-UNC-003: the undated source is NAMED on screen, through the real entry point.

    The fixture's DeepSWE board carries release dates only, which is the shipping board's shape.
    """
    body = TestClient(adapter.app).get("/v1/recommendations", params={"task": "agentic-coding"})
    answer = body.json()["answers"][0]

    assert answer["evidence_dating"] == "undated"
    assert answer["evidence_dating_note"].startswith(
        "The DeepSWE evidence in this answer carries no evaluation dates"
    ), answer["evidence_dating_note"]


def test_a_mixed_answer_names_its_benchmark_too() -> None:
    """The other branch that describes undated evidence, reached directly: no fixture yields it."""
    from app.workflows.recommend import Pick

    def pick(date: str | None) -> Pick:
        return Pick(
            label="best_quality",
            model="m",
            vendor="v",
            score=1.0,
            metric="% correct",
            secondary_score=None,
            blended_per_m=1.0,
            input_per_m=1.0,
            output_per_m=1.0,
            evidence_date=date,
            harness="h",
            effort=None,
            higher_effort=None,
            higher_effort_score=None,
            effort_note=None,
            confidence="Medium",
            confidence_basis="b",
            why="w",
            trade_off=None,
            why_fact={},
            trade_off_fact=None,
        )

    dating, note = adapter._evidence_dating((pick("2026-08-01"), pick(None)), "GPQA Diamond")
    assert dating == "mixed"
    assert note is not None and "GPQA Diamond" in note


def test_the_recommendations_route_did_not_gain_a_field(seeded: Path) -> None:
    """D-138's claim is that the frozen answer's FIELD SET did not move. Asserted, not stated.

    Not "byte-identical", which the first version of D-138 said and which was false: this wave
    changes the VALUE of `evidence_dating_note` so that it names its benchmark (REQ-UNC-003). The
    comparison is against the frozen key set itself, so ANY added field fails here — the first
    version checked for three names and let a fourth through (M13-W2 review MAJOR-1).
    """
    from .test_api_v1 import ANSWER_KEYS

    served = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"}).json()
    assert served["answers"]
    for answer in served["answers"]:
        assert set(answer) == ANSWER_KEYS, set(answer) ^ ANSWER_KEYS



def test_every_elo_surface_publishes_its_pinned_score_anchor(seeded: Path) -> None:
    """REQ-SCR-003 (M14-W4, D-143): an Elo score is converted against a PINNED anchor.

    The anchor is a pinned constant per surface -- data only an owner ruling moves. Never the
    current board's maximum, which would move a model's score whenever a different model joined,
    and (review M-3) not `min_quality` either, which every recalibration re-measures. A scale that
    is already out of 100 publishes no anchor (identity), and ECI publishes none because D-143
    leaves it rank-only.
    """
    served = _served_categories()
    for surface, spec in CATEGORIES.items():
        anchor = served[surface]["score_anchor"]
        if spec.metric == "elo":
            assert anchor == PINNED_SCORE_ANCHORS[surface], surface
        else:
            assert anchor is None, surface
    assert {s for s, spec in CATEGORIES.items() if spec.metric == "elo"} == set(PINNED_SCORE_ANCHORS)


#: The anchors as the owner ruled them (D-143). A recalibration that edits `min_quality` leaves this
#: table alone; moving a card's number out of 100 means editing THIS table, in a reviewed change.
PINNED_SCORE_ANCHORS = {
    "assistant": 1400.0,
    "web-dev": 1478.9,
    "document": 1467.5,
    "factuality": 1450.6,
    # M15-W3, pinned 2026-09-22 from `scripts/calibrate_board.py` (D-145's board-third rule).
    "vision": 1248.2,
    "search": 1206.9,
    "search_factuality": 1203.7,
}


def test_the_served_anchor_does_not_follow_a_moved_floor(
    seeded: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-146 clause 2, through `/v1/categories`. The M14 closure seat's MAJOR-8.

    Every pinned anchor currently equals its surface's `min_quality`, so an endpoint serving the
    FLOOR passes every assertion that compares the served number to the pinned table. The seat ran
    that mutant and it survived. Here one surface's floor is moved and its anchor is not: an
    endpoint reading the floor now serves a number no ruling produced, which is precisely the
    regression -- a recalibration moving every card's number with no new measurement of any model.
    """
    surface = "document"
    spec = CATEGORIES[surface]
    moved = dataclasses.replace(spec, min_quality=spec.min_quality + 123.0)
    monkeypatch.setitem(CATEGORIES, surface, moved)

    served = _served_categories()
    assert served[surface]["score_anchor"] == PINNED_SCORE_ANCHORS[surface]
    assert served[surface]["score_anchor"] != moved.min_quality


def test_a_recalibration_cannot_move_the_anchor() -> None:
    """Review M-3: the anchor is its own field, so moving the floor leaves every /100 number alone."""
    from dataclasses import replace

    for surface, spec in CATEGORIES.items():
        if spec.metric != "elo":
            continue
        moved = replace(spec, min_quality=spec.min_quality + 50)
        assert moved.score_anchor == spec.score_anchor, surface
