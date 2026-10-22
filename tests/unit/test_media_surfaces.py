"""#378 (D-218 clause 1): the five image and video surfaces, ranked on quality only.

Each surface ranks its own LMArena board on its own Elo scale (D-105), with no price column, no value
window and no budget filter: none of their models is priced per token, and a per-token price would
rank on a number that does not measure them. The answer's one pick is the best quality, and a missing
price is published as null, never as a zero a reader could take for a free model. The boards are the
recorded fixtures of `test_arena_media_boards.py`, ingested through the real entry point.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.arena import ARENA_BOARDS
from app.clients.fakes import FakeRawSource
from app.workflows.categories import CATEGORIES
from app.workflows.families import FAMILIES
from app.workflows.ingest import RunContext, ingest_arena
from app.workflows.rank import PRICING_ATTRIBUTION_LITELLM, category_ranking
from app.workflows.recommend import BUDGETS, recommend
from app.workflows.registry import reconcile

from .test_api_v1 import _seeded_db

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "arena_media"

#: surface -> (its board's config, the tie margin `docs/reviews/issue-378-media-calibration.md` records).
MEDIA = {
    "text_to_image": ("text_to_image", 3.8),
    "image_edit": ("image_edit", 3.4),
    "text_to_video": ("text_to_video", 12.3),
    "image_to_video": ("image_to_video", 9.9),
    "video_edit": ("video_edit", 16.3),
}


def _with_media_boards(path: Path) -> None:
    """The seeded artifact (prices, two coding boards), plus the five recorded media boards."""
    _seeded_db(path)
    conn = sqlite3.connect(path)
    run = RunContext(observed_at="2026-10-21T00:00:00+00:00")
    for config, _ in MEDIA.values():
        board = ARENA_BOARDS[config]
        ingest_arena(conn, FakeRawSource(board.id, (FIXTURES / f"{config}.json").read_text(encoding="utf-8")), run)
    reconcile(conn)
    conn.commit()
    conn.close()


@pytest.fixture()
def media_db(tmp_path: Path) -> Path:
    db = tmp_path / "pipeline.db"
    _with_media_boards(db)
    return db


@pytest.fixture()
def client(media_db: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MODEL_RANKING_DB", str(media_db))
    from app.adapter import main as adapter

    return TestClient(adapter.app)


@pytest.mark.parametrize("surface", sorted(MEDIA))
def test_each_media_surface_ranks_its_own_board_on_quality_only(surface: str) -> None:
    """D-218 clause 1: one board, Elo, no price and no value window; the D-148 tie margin as recorded."""
    config, close_call = MEDIA[surface]
    spec = CATEGORIES[surface]
    board = ARENA_BOARDS[config]
    assert (spec.primary_source, spec.primary_benchmark, spec.metric) == (board.id, board.benchmark, "elo")
    assert spec.priced is False
    assert spec.value_window is None
    assert spec.close_call == close_call
    assert spec.secondary_benchmark is None and spec.price_excludes is None
    assert FAMILIES[surface] == (board.id,)


def test_every_priced_surface_stays_priced() -> None:
    """Quality-only is the five media surfaces' rule, and no other surface's."""
    assert {name for name, spec in CATEGORIES.items() if not spec.priced} == set(MEDIA)


def test_a_media_board_ranks_every_model_it_names_with_no_price(media_db: Path) -> None:
    """No model on these boards has a per-token price, and each still ranks, in the board's order,
    under no price at all (never another surface's price, never a zero)."""
    conn = sqlite3.connect(media_db)
    try:
        for surface, (config, _) in MEDIA.items():
            rows = category_ranking(conn, CATEGORIES[surface])
            board = json.loads((FIXTURES / f"{config}.json").read_text(encoding="utf-8"))["rows"]
            # every name the media grammar reads; `image_edit` names one moving `-latest` alias (D-166)
            expected = len(board) - (1 if config == "image_edit" else 0)
            assert len(rows) == expected, (surface, len(rows))
            assert [r.score for r in rows] == sorted((r.score for r in rows), reverse=True)
            assert {(r.blended_per_m, r.input_per_m, r.output_per_m) for r in rows} == {(None, None, None)}
    finally:
        conn.close()


def test_a_media_name_is_never_read_as_a_text_model(media_db: Path) -> None:
    """A curated text rule matches by search, and `kling-o3-pro` contains OpenAI's `o3-pro`. On a media
    board the text rules do not apply, so the video model keeps its own identity, and the modality
    guard that refuses `GPT-Image-2` as a text model does not drop it from the image board."""
    conn = sqlite3.connect(media_db)
    try:
        linked = dict(conn.execute(
            "SELECT raw_name, model_id FROM scores WHERE source LIKE 'arena_%' AND raw_name IN (?, ?)",
            ("kling-o3-pro", "GPT-Image-2 (Medium)")).fetchall())
        displays = dict(conn.execute("SELECT id, display FROM models").fetchall())
    finally:
        conn.close()
    assert linked == {"kling-o3-pro": "kling-o3-pro", "GPT-Image-2 (Medium)": "gpt-image2"}
    assert (displays["kling-o3-pro"], displays["gpt-image2"]) == ("kling-o3-pro", "GPT-Image-2")


@pytest.mark.parametrize("surface", sorted(MEDIA))
def test_the_answer_is_one_best_quality_pick_whatever_the_budget(media_db: Path, surface: str) -> None:
    """No Best Value (no window) and no Budget Pick (no price); the budget filters nothing; no pricing
    source is cited, because none was read."""
    conn = sqlite3.connect(media_db)
    try:
        ranked = category_ranking(conn, CATEGORIES[surface])
        answers = {budget: recommend(conn, budget=budget, task=surface) for budget in BUDGETS}
    finally:
        conn.close()
    for budget, rec in answers.items():
        assert rec is not None, budget
        assert [p.label for p in rec.picks] == ["best_quality"]
        (pick,) = rec.picks
        assert (pick.model, pick.score) == (ranked[0].model, round(ranked[0].score, 1))
        assert (pick.blended_per_m, pick.input_per_m, pick.output_per_m) == (None, None, None)
        assert pick.why_fact["reason"] == "highest_score"
        assert rec.eligible_count == len(ranked), budget
        assert all("Pricing data" not in source for source in rec.sources)
        assert any("LMArena" in source for source in rec.sources)
    assert len({(a.picks[0].model_id, a.eligible_count) for a in answers.values() if a is not None}) == 1


def test_a_near_tie_with_the_runner_up_is_still_disclosed() -> None:
    """The tie margin applies on a quality-only surface too: two models inside it are called level."""
    from app.workflows.rank import RankingRow
    from app.workflows.recommend import _close_call

    spec = CATEGORIES["text_to_image"]

    def row(model: str, score: float) -> RankingRow:
        return RankingRow(model, "Other", score, "arena-crowd", "arena_text_to_image", "unspecified", None,
                          None, None, None, None, None, None, None)

    sentence, fact = _close_call(row("a", 1400.0), row("b", 1397.0), spec)
    assert sentence and fact == {"model": "b", "behind_by": 3.0, "unit": "Elo"}
    assert _close_call(row("a", 1400.0), row("b", 1390.0), spec) == (None, None)


def test_v1_publishes_the_quality_only_answer_with_null_prices(client: TestClient) -> None:
    """Through the real entry point: `priced: false` on `/v1/categories`, and an answer whose picks and
    ranking rows carry null prices, under any budget."""
    categories = {c["id"]: c for c in client.get("/v1/categories").json()["categories"]}
    assert {s for s, c in categories.items() if c["priced"] is False} == set(MEDIA)
    for surface in MEDIA:
        assert categories[surface]["score_anchor"] == categories[surface]["min_quality"] is not None
        body = client.get("/v1/recommendations", params={"task": surface, "budget": "low"}).json()
        (answer,) = body["answers"]
        assert answer["unavailable_reason"] is None
        assert [p["label"] for p in answer["picks"]] == ["best_quality"]
        prices = {(r["blended_per_m"], r["input_per_m"], r["output_per_m"]) for r in answer["picks"] + answer["ranking"]}
        assert prices == {(None, None, None)}, surface
        assert answer["eligible_count"] == len(answer["ranking"]) > 0


def test_v1_boards_lists_the_unpriced_models_apart_and_keeps_every_price(client: TestClient) -> None:
    """`/v1/boards` stands the media boards, and lists the models only they name apart, with no price
    field: every `models` entry keeps a number, as every client already decodes it."""
    body = client.get("/v1/boards").json()
    boards = {b["id"]: b for b in body["boards"]}
    unpriced = {m["id"] for m in body["unpriced_models"]}
    for config, _ in MEDIA.values():
        standing = {s["model"] for s in boards[ARENA_BOARDS[config].id]["standings"]}
        assert standing and standing <= unpriced | {m["id"] for m in body["models"]}
    assert all(isinstance(m["blended_per_m"], int | float) for m in body["models"])
    assert all("blended_per_m" not in m for m in body["unpriced_models"])
    assert not unpriced & {m["id"] for m in body["models"]}
    # the priced surfaces' standings and prices are what they were
    assert {m["id"] for m in body["models"]} == {"claude-4.5-opus", "gpt-5", "deepseek-v3.2"}


def test_the_refresh_fingerprints_a_media_surface_without_a_price_median(media_db: Path) -> None:
    """The refresh's guards read a quality-only surface with no median price and no budget cut."""
    from app.workflows.refresh import serving_summary

    conn = sqlite3.connect(media_db)
    try:
        summary = serving_summary(conn)
    finally:
        conn.close()
    for surface in MEDIA:
        assert surface not in summary.median_price
        assert set(summary.eligible[surface].values()) == {summary.surfaces[surface]} != {0}


def test_the_priced_surfaces_credit_their_prices_as_before(media_db: Path) -> None:
    """A priced answer still cites the price source it read."""
    conn = sqlite3.connect(media_db)
    try:
        rec = recommend(conn, budget="unlimited", task="agentic-coding")
    finally:
        conn.close()
    assert rec is not None and PRICING_ATTRIBUTION_LITELLM in rec.sources
    assert all(p.blended_per_m is not None for p in rec.picks)


@pytest.mark.parametrize("surface", sorted(MEDIA))
def test_a_surface_ranked_on_quality_only_gives_no_plan_answer(media_db: Path, surface: str) -> None:
    """D-218 clause 1 (#378, #405): a plan is a monthly price, and a quality-only surface takes no price, no
    value window and no budget, so the subscription answer is none under every budget. No test reached
    `recommend_subscription`'s quality-only branch before the release Tester (subscribe.py, uncovered)."""
    from app.workflows.subscribe import recommend_subscription

    conn = sqlite3.connect(media_db)
    try:
        assert {budget: recommend_subscription(conn, budget, surface) for budget in BUDGETS} == dict.fromkeys(BUDGETS)
        # A priced surface goes on to read the plans, which this artifact does not hold: the quality-only
        # answer above is none before any plan is read, not for want of plans.
        with pytest.raises(ValueError, match="plan_config"):
            recommend_subscription(conn, "unlimited", "coding")
    finally:
        conn.close()
