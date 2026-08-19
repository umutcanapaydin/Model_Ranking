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


@pytest.fixture
def unrounded_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """The shared fixture cannot exercise rounding, because every score in it is already round.

    That is not a small detail — it is why the first version of the two tests below passed with the
    rounding REMOVED. A fixture whose values cannot violate the invariant makes any assertion about
    that invariant unfalsifiable, which is a test that reads as a gate and is a decoration.

    `83.47107438016529` is a real shape: SWE-bench Verified reports resolved/total, and 101/121 is
    exactly this number. `0.6` is the classic float that survives naive rounding checks.
    """
    import sqlite3

    from .test_api_v1 import _seeded_db

    db = tmp_path / "unrounded.db"
    _seeded_db(db)
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "UPDATE scores SET score = 83.47107438016529"
            " WHERE score = (SELECT max(score) FROM scores)"
        )
        # The SECONDARY benchmark has to EXIST before it can be unrounded. Removing only
        # `round_optional_score` stayed green twice: first because the seeded scores were already
        # round, then because this fixture carries no Aider rows at all, so `secondary_score` is
        # None everywhere and the mutant is equivalent HERE while remaining live in production.
        # A fixture that cannot reach a field cannot defend it.
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness,"
            " source_url, observed_at) VALUES ('claude-4.5-opus', 'Claude 4.5 Opus', 'aider',"
            " 'Aider polyglot', '% resolved', 61.9834710743809, 'aider', 'fixture://x', 't')"
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")
    return TestClient(adapter.app)


def test_one_model_has_one_score_in_one_payload(unrounded_client: TestClient) -> None:
    """D-109, at the boundary D-125 added and forgot to round.

    `_ranking_json` published `RankingRow` fields raw while every other output boundary called
    `round_score` — so the SAME model arrived twice in the SAME answer with two different numbers:
    `83.5` under `picks` and `83.47107438016529` under `ranking`. The phone rendered them one above
    the other, `83.5 % resolved` and `83.471 % resolved`, and the client comment claiming "the
    engine rounds at its own output boundary; this prints what it sent" was false for every row.

    D-109's own rationale names this shape: prose that contradicts the JSON beside it. On the Elo
    surfaces it is worse — an unrounded Elo publishes as `1481.5937567329202`.

    Found by the M8 fresh-eyes code review, which was the first independent read of that range.
    """
    for answer in _answers(unrounded_client):
        by_model = {row["model"]: row["score"] for row in answer["ranking"]}
        for pick in answer["picks"]:
            if pick["model"] in by_model:
                assert pick["score"] == by_model[pick["model"]], (
                    f"{pick['model']} on surface {answer['surface']} is published as "
                    f"{pick['score']} in picks and {by_model[pick['model']]} in ranking; one "
                    "model, one payload, two scores"
                )


def test_no_published_ranking_number_carries_more_precision_than_the_engine_rounds_to(
    unrounded_client: TestClient,
) -> None:
    """The other direction, so the fix cannot be satisfied by making the PICKS raw instead.

    Asserting only that the two agree would be satisfied by rounding neither. This pins the actual
    contract: what leaves the boundary is what `round_score` produces.
    """
    for answer in _answers(unrounded_client):
        for row in answer["ranking"]:
            assert row["score"] == round(row["score"], 1), (
                f"{row['model']} publishes {row['score']}, which is not rounded at the output "
                "boundary (D-109)"
            )
            if row["secondary_score"] is not None:
                assert row["secondary_score"] == round(row["secondary_score"], 1)
