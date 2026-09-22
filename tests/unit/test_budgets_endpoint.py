"""REQ-API-010 / W-044 / D-134 — `/v1` gives ONE account of a query.

Measured before this existed: `budget=low` on `everyday` answers `eligible_count: 25` beside a
`ranking` array of 58 rows whose most expensive model is $36.09/1M. The array is unfiltered by
design (D-125 publishes every ranked model), and the cap the count was computed against — $2.00/1M
blended — was published nowhere. This app handles it on screen. Any other consumer received 58 rows
under a low-budget query with nothing saying they were unfiltered and no way to work it out.

The test that matters here is not "the endpoint returns the constants". It is
`test_the_published_cap_reproduces_the_engines_own_eligible_count`: a cap that does not reproduce
the count is a THIRD account of the same query, published in a new place, which would be worse than
the two accounts it was written to reconcile.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter
from app.workflows.rank import BLEND_INPUT_WEIGHT, BLEND_OUTPUT_WEIGHT
from app.workflows.recommend import BUDGETS


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MODEL_RANKING_DB", "advisor.db")
    monkeypatch.setenv("APP_ENV", "test")
    return TestClient(adapter.app)


def test_every_budget_the_engine_accepts_is_published(client: TestClient) -> None:
    """A cap list that omits a budget is the same defect one step over: a consumer would compute
    eligibility for two of three budgets and silently guess at the third."""
    published = {b["id"] for b in client.get("/v1/budgets").json()["budgets"]}

    assert published == set(BUDGETS), (
        f"the engine accepts {sorted(BUDGETS)} and publishes {sorted(published)}"
    )


def test_unlimited_publishes_no_cap_rather_than_a_large_one(client: TestClient) -> None:
    """`null` is the absence of a cap. A sentinel — 1e9, or the largest price seen — would invite a
    consumer to compare against it and get a different answer than the engine does."""
    caps = {b["id"]: b["blended_cap_per_m"] for b in client.get("/v1/budgets").json()["budgets"]}

    assert caps["unlimited"] is None
    assert caps["low"] == 2.0
    assert caps["medium"] == 8.0


@pytest.mark.artifact  # W-108
@pytest.mark.parametrize("budget", ["low", "medium"])
@pytest.mark.parametrize("task", ["everyday", "assistant", "coding"])
def test_the_published_cap_reproduces_the_engines_own_eligible_count(
    client: TestClient, budget: str, task: str
) -> None:
    """**The whole point.** Filter the published `ranking` by the published cap and the count must
    equal the `eligible_count` the engine reported — on real data, across surfaces and budgets.

    If these disagree, the endpoint has not reconciled anything; it has added a third account.
    """
    caps = {b["id"]: b["blended_cap_per_m"] for b in client.get("/v1/budgets").json()["budgets"]}
    cap = caps[budget]

    answers = client.get(
        "/v1/recommendations", params={"task": task, "budget": budget}
    ).json()["answers"]

    for answer in answers:
        ranking = answer.get("ranking") or []
        if not ranking:
            continue
        computed = sum(1 for row in ranking if row["blended_per_m"] <= cap)
        assert computed == answer["eligible_count"], (
            f"{answer['surface']}/{budget}: the published cap of {cap} says {computed} rows fit, "
            f"the engine says {answer['eligible_count']}. A consumer applying the published cap "
            "would disagree with the payload it came in"
        )


@pytest.mark.artifact  # W-108
def test_the_published_blend_reproduces_each_rows_blended_price(client: TestClient) -> None:
    """The weights are published so the cap can be CHECKED, not merely applied.

    A threshold nobody can reproduce is a number to trust. This asserts against the rows the API
    actually served rather than against the constants, so a change to either side is caught.
    """
    blend = client.get("/v1/budgets").json()["blend"]
    answers = client.get(
        "/v1/recommendations", params={"task": "everyday", "budget": "unlimited"}
    ).json()["answers"]

    rows = [row for answer in answers for row in (answer.get("ranking") or [])]
    assert rows, "fixture assumption: the surface must publish a ranking on real data"

    for row in rows:
        expected = round(
            row["input_per_m"] * blend["input_weight"]
            + row["output_per_m"] * blend["output_weight"],
            2,
        )
        assert abs(expected - row["blended_per_m"]) < 0.011, (
            f"{row['model']}: the published blend gives {expected}, the row says "
            f"{row['blended_per_m']}"
        )


def test_the_published_weights_are_the_engines_own(client: TestClient) -> None:
    """Fixture blindness guard for the test above: if the endpoint published weights of its own,
    both it and the rows could be wrong together and the reproduction would still hold."""
    blend = client.get("/v1/budgets").json()["blend"]

    assert blend["input_weight"] == BLEND_INPUT_WEIGHT
    assert blend["output_weight"] == BLEND_OUTPUT_WEIGHT


def test_the_endpoint_answers_without_touching_the_artifact(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """These are constants of the SCORING POLICY, not of the data. A consumer must be able to read
    them while the artifact is being republished — which, since M9, happens every twelve hours."""
    monkeypatch.setenv("MODEL_RANKING_DB", "/nonexistent/there-is-no-artifact-here.db")

    response = client.get("/v1/budgets")

    assert response.status_code == 200
    assert {b["id"] for b in response.json()["budgets"]} == set(BUDGETS)
