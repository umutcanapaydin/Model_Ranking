"""M8-W2 — `/v1` publishes the full ranking beside the picks (D-125).

This is the ONE contract revision D-124 permits during M8, so these tests carry more weight than
their size suggests: they pin what the change is, and — more importantly — what it did NOT touch.
A window opened for one reason is exactly where a second, unrelated change gets in.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from .test_api_v1 import _seeded_db

    db = tmp_path / "seeded.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")
    return TestClient(adapter.app)


def _answers(client: TestClient, task: str = "coding", budget: str = "unlimited") -> list[dict]:
    response = client.get(f"/v1/recommendations?task={task}&budget={budget}")
    assert response.status_code == 200
    return list(response.json()["answers"])


def test_every_answer_carries_the_full_ranking(client: TestClient) -> None:
    """The reason the change was made: the client could not open a category it could not see."""
    for answer in _answers(client):
        assert "ranking" in answer, f"{answer['surface']} publishes no ranking"
        assert len(answer["ranking"]) >= len(answer["picks"]), (
            "the ranking must contain at least as many models as the picks chose from"
        )


def test_the_ranking_is_in_the_engines_order_and_the_client_never_re_sorts(
    client: TestClient,
) -> None:
    """Trap 1: the order is the engine's answer to one question, not a list to re-sort.

    Asserted as a PROPERTY of the payload rather than as a promise about the client, because a
    property can fail a test and a promise cannot.
    """
    for answer in _answers(client):
        scores = [row["score"] for row in answer["ranking"]]
        assert scores == sorted(scores, reverse=True), (
            f"{answer['surface']}'s ranking is not in descending score order; the client would "
            "have to sort it, which is how the engine's ordering becomes the client's opinion"
        )


def test_a_ranking_row_is_not_a_pick(client: TestClient) -> None:
    """The distinction D-125 rests on: picks answer three questions, a ranking answers one.

    Serving "more picks" would have invented a fourth and fifth label. A ranking row carries no
    `label`, no `why` and no `trade_off`, because nothing chose it.
    """
    for answer in _answers(client):
        for row in answer["ranking"]:
            for pick_only in ("label", "why", "trade_off", "confidence", "confidence_basis"):
                assert pick_only not in row, (
                    f"a ranking row carries `{pick_only}`, which only a CHOSEN model has"
                )
            for needed in ("model", "vendor", "score", "metric", "blended_per_m"):
                assert row.get(needed) not in (None, ""), f"ranking row missing {needed}"


def test_the_ranking_publishes_only_its_declared_field_set(client: TestClient) -> None:
    """The M6 lesson in its fifth application: an allowlist, not whatever the dataclass holds.

    `RankingRow` carries fields the API does not publish (`evidence_source`, `secondary_cost`,
    `higher_effort*`). A row that leaked them would widen an unauthenticated surface silently.
    """
    for answer in _answers(client):
        for row in answer["ranking"]:
            undeclared = set(row) - adapter.PUBLIC_RANKING_FIELDS
            assert not undeclared, f"undeclared field(s) reached the ranking: {sorted(undeclared)}"


# --- what D-125 did NOT change -----------------------------------------------------------------


def test_ruling_a_survives_the_change(client: TestClient) -> None:
    """A window opened for one reason is where an unrelated change gets in. Not this one.

    `ranking` is per-answer by construction, so it cannot become a cross-surface leaderboard, and
    nothing about the two coding surfaces ranks one above the other.
    """
    answers = _answers(client)
    assert len(answers) == 2
    assert sorted(a["surface"] for a in answers) == ["agentic-coding", "coding"]

    banned = {"primary", "primary_surface", "top_pick", "display_order", "rank", "suggested"}
    for answer in answers:
        assert not (banned & set(answer)), "a precedence field arrived with the ranking"
        for row in answer["ranking"]:
            assert not (banned & set(row))

    body = client.get("/v1/recommendations?task=coding").json()
    assert body["surfaces_are_ranked"] is False


def test_the_picks_are_untouched_by_the_change(client: TestClient) -> None:
    """`picks` keeps its meaning and its field set; the ranking was ADDED beside it."""
    for answer in _answers(client):
        for pick in answer["picks"]:
            undeclared = set(pick) - adapter.PUBLIC_PICK_FIELDS
            assert not undeclared, f"the picks' field set moved: {sorted(undeclared)}"
            assert pick["label"] in {"best_quality", "best_value", "budget_pick"}


def test_a_surface_with_no_evidence_has_an_empty_ranking_and_still_says_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ranking must not become a way to look non-empty while answering nothing."""
    from app.workflows.schema import connect

    db = tmp_path / "unbuilt_surface.db"
    conn = connect(str(db))
    try:
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('m', 1.0, 2.0)")
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")
    (answer,) = _answers(TestClient(adapter.app), task="assistant")

    assert answer["ranking"] == []
    assert answer["picks"] == []
    assert answer["unavailable_reason"], "an empty answer must still say why it is empty"
