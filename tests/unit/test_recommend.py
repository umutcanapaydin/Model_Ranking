"""Recommendation engine tests — cite REQ-REC-001..004."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.epoch import EPOCH_ATTRIBUTION
from app.clients.fakes import FakeRawSource
from app.workflows.categories import CATEGORIES
from app.workflows.floors import derived_floor
from app.workflows.ingest import RunContext, ingest_aider, ingest_litellm, ingest_swebench
from app.workflows.rank import UnbuiltEvidenceError, build_price_medians
from app.workflows.recommend import (
    BUDGETS,
    CLOSE_CALL_PTS,
    VALUE_WINDOW_PTS,
    eligible_rows,
    pareto_frontier,
    recommend,
)
from app.workflows.registry import reconcile
from app.workflows.schema import connect

PRICING = json.dumps(
    {
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "deepseek-v3.2": {
            "mode": "chat",
            "input_cost_per_token": 2.8e-07,
            "output_cost_per_token": 4.1e-07,
        },
        "gemini-3-flash": {
            "mode": "chat",
            "input_cost_per_token": 5e-07,
            "output_cost_per_token": 3e-06,
        },
        "gpt-5-nano": {
            "mode": "chat",
            "input_cost_per_token": 5e-08,
            "output_cost_per_token": 4e-07,
        },
    }
)
SCORES = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {
                        "name": "live-SWE-agent + Claude 4.5 Opus",
                        "resolved": 79.2,
                        "date": "2025-12-15",
                    },
                    {"name": "mini-SWE-agent + GPT-5", "resolved": 74.4, "date": "2025-09-01"},
                    {
                        "name": "mini-SWE-agent + DeepSeek V3.2",
                        "resolved": 70.0,
                        "date": "2026-02-17",
                    },
                    {
                        "name": "mini-SWE-agent + Gemini 3 Flash",
                        "resolved": 75.8,
                        "date": "2026-02-17",
                    },
                    {"name": "mini-SWE-agent + GPT-5 nano", "resolved": 40.0, "date": "2025-09-01"},
                    # D-159 (M17-W1): the floor is derived from the WHOLE board, so the fixture is
                    # a board of realistic shape -- models nobody prices sit on it too. Twelve rows
                    # put the top third at the fourth, DeepSeek V3.2's 70.0.
                    *[{"name": f"some-agent + Unpriced Model {i}", "resolved": 30.0 + 4 * i,
                       "date": "2025-09-01"} for i in range(7)],
                ],
            }
        ]
    }
)
#: M13-W2 (REQ-UNC-002): the `date` here became LOAD-BEARING and was previously incidental.
#: `2026-02-17` against this fixture's `observed_at` of 2026-08-10 is 174 days — nearly twice
#: `STALE_NOTICE_DAYS`, so under the amended rule it no longer upgrades confidence and the test
#: below stopped testing what its name says. Moved inside the window so it keeps exercising "two
#: CURRENT benchmarks -> High"; the stale case gained its own test rather than being lost.
AIDER = """
- model: deepseek-v3.2
  pass_rate_2: 74.2
  total_cost: 3.5
  date: 2026-07-01
"""

#: The same board, last run 174 days before the anchor. Used only by the staleness test.
AIDER_STALE = """
- model: deepseek-v3.2
  pass_rate_2: 74.2
  total_cost: 3.5
  date: 2026-02-17
"""


def _db() -> sqlite3.Connection:
    conn = connect()
    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", SCORES), run)
    ingest_aider(conn, FakeRawSource("aider", AIDER), run)
    reconcile(conn)
    # M7-W2: production builds the price medians in `app.workflows.build`, not inside
    # `recommend()`. A fixture that reconciles is standing in for that build, so it does
    # the same last step -- otherwise it seeds an artifact the engine correctly refuses.
    build_price_medians(conn)
    return conn


def test_three_labeled_deterministic_picks() -> None:
    """REQ-REC-001: exactly three labeled picks; every field populated; deterministic."""
    conn = _db()
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec1 = recommend(conn, "unlimited")
    rec2 = recommend(conn, "unlimited")
    assert rec1 is not None
    assert rec1 == rec2  # same state + inputs → same picks
    assert [p.label for p in rec1.picks] == ["best_quality", "best_value", "budget_pick"]
    for p in rec1.picks:
        assert p.model and p.vendor and p.why and p.confidence in ("High", "Medium")
        assert p.harness
    assert rec1.picks[0].model == "Claude 4.5 Opus"


def test_req_lic_001_epoch_citation_ships_where_epoch_data_is_served() -> None:
    """REQ-LIC-001 + W4 review BLOCKING-2: the citation rides the DATA, not the payload.

    CC-BY obliges attribution wherever the licensed data is served — so a payload that
    ranks on an Epoch row MUST carry the citation. The mirror obligation is just as
    real and is what BLOCKING-2 caught: a payload that never read Epoch must not claim
    it, because `sources` is a provenance claim in a machine contract.
    """
    from app.workflows.rank import SWEBENCH_ATTRIBUTION

    conn = _db()
    # Same benchmark, evidence supplied by the Epoch bundle instead of swebench.com.
    conn.execute(
        "UPDATE scores SET source = 'epoch_swe_bench_verified' WHERE benchmark = ?"
        # D-159: only the RANKED rows move; the surface's own board (swebench) keeps the models
        # nobody prices, so it still has a floor to recommend from. An empty own board has none,
        # and the Budget Pick then says so (test_the_budget_pick_says_when_its_board_is_empty).
        " AND model_id IS NOT NULL",
        ("SWE-bench Verified",),
    )
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "unlimited")
    assert rec is not None
    assert EPOCH_ATTRIBUTION in rec.sources
    # This fixture ALSO serves an Aider secondary score and grades confidence on it, so
    # it owes that citation too (M5 security review MINOR): served data, served credit.
    assert SWEBENCH_ATTRIBUTION in rec.sources
    assert any(p.secondary_score is not None for p in rec.picks)

    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    # The README must carry Epoch's prescribed citation text itself, not a paraphrase.
    assert EPOCH_ATTRIBUTION.removesuffix(" (CC-BY-4.0)") in readme
    assert "CC BY 4.0" in readme  # and name the licence


def test_payload_never_claims_a_source_it_did_not_read() -> None:
    """W4 review BLOCKING-2 citing test: `sources` is derived, not a static catalogue.

    This fixture holds swebench + aider scores and litellm prices — no Arena row and no
    Epoch row anywhere. The first cut stamped every payload with the full catalogue, so
    it claimed Arena AND Epoch regardless: two sources it never opened.
    """
    from app.workflows.rank import ARENA_ATTRIBUTION, PRICING_ATTRIBUTION, SWEBENCH_ATTRIBUTION

    rec = recommend(_db(), "unlimited")
    assert rec is not None
    assert rec.sources == (PRICING_ATTRIBUTION, SWEBENCH_ATTRIBUTION)
    assert ARENA_ATTRIBUTION not in rec.sources
    assert EPOCH_ATTRIBUTION not in rec.sources


def test_budget_filter_is_hard_constraint() -> None:
    """REQ-REC-002: low budget → no pick may exceed the threshold; constants tested."""
    conn = _db()
    assert BUDGETS["low"] == 2.0
    assert BUDGETS["medium"] == 8.0
    assert BUDGETS["unlimited"] is None
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "low")
    assert rec is not None
    for p in rec.picks:
        assert p.blended_per_m <= 2.0, f"{p.model} exceeds the low-budget cap"
    # the expensive leader must be gone
    assert all(p.model != "Claude 4.5 Opus" for p in rec.picks)


def test_an_unbuilt_database_is_refused_rather_than_answered_empty() -> None:
    """M7-W2 INVERTS this test, and the inversion is REQ-API-008.

    It used to assert that an EMPTY database returns None -- indistinguishable, to every caller,
    from "your budget excluded everything". That was safe only while `recommend()` built the price
    medians itself. Now that the build lives in `app.workflows.build`, an empty database is an
    UNBUILT ARTIFACT, and answering it with None is the 200-with-no-picks failure W-023 shipped.
    An evidence engine with no evidence fails closed and names the command that fixes it.

    The genuine "budget excluded everything" case is covered by
    `test_budget_filters_nonempty_ranking_to_none`, which seeds real rows first.
    """
    conn = connect()  # empty db: schema present, nothing ingested, medians never built
    with pytest.raises(UnbuiltEvidenceError, match=r"app\.workflows\.build"):
        recommend(conn, "low")


def test_pareto_non_dominance() -> None:
    """REQ-REC-003: no recommended model is worse AND more expensive than another."""
    conn = _db()
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "unlimited")
    assert rec is not None
    ranking = eligible_rows(
        __import__("app.workflows.rank", fromlist=["coding_ranking"]).coding_ranking(conn),
        "unlimited",
    )
    for p in rec.picks:
        dominated = any(o.score > p.score and o.blended_per_m < p.blended_per_m for o in ranking)
        assert not dominated, f"{p.model} is dominated"


def test_frontier_excludes_dominated_models() -> None:
    """REQ-REC-003: GPT-5 (74.4, $3.44) is dominated by Gemini 3 Flash (75.8, $1.12)."""
    conn = _db()
    from app.workflows.rank import build_price_medians, coding_ranking

    build_price_medians(conn)
    frontier = pareto_frontier(coding_ranking(conn))
    names = [r.model for r in frontier]
    assert "GPT-5" not in names
    assert "Gemini 3 Flash" in names


def test_value_pick_rule_within_window_cheapest() -> None:
    """REQ-REC-003: value = within VALUE_WINDOW_PTS of leader, cheapest on frontier."""
    assert VALUE_WINDOW_PTS == 6.0
    conn = _db()
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "unlimited")
    assert rec is not None
    value = rec.picks[1]
    # leader 79.2; window ≥73.2 → Gemini 3 Flash (75.8, $1.12) beats Claude ($11.25)
    assert value.model == "Gemini 3 Flash"
    assert value.trade_off is not None


def test_budget_pick_respects_min_quality() -> None:
    """REQ-REC-001/002 under D-159: the Budget Pick is the cheapest model clearing the floor the
    board itself sets -- the top third of its twelve rows, DeepSeek V3.2's 70.0 -- and nano (40)
    does not."""
    conn = _db()
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    assert derived_floor(conn, CATEGORIES["coding"]) == 70.0
    rec = recommend(conn, "unlimited")
    assert rec is not None
    cheap = rec.picks[2]
    assert cheap.model == "DeepSeek V3.2"
    assert cheap.why_fact["floor"] == 70.0


def test_confidence_grades_by_source_count() -> None:
    """REQ-REC-004 / REQ-UNC-002: DeepSeek has SWE + a CURRENT Aider → High; one source → Medium.

    The word "current" is M13-W2's amendment. A second benchmark only widens the evidence if it
    still describes the models being ranked; Aider's real board has not run since 2025-10-03 and
    was upgrading the coding budget pick on that basis. See
    `tests/unit/test_secondary_evidence_age.py` for the rule, and the sibling below for the
    end-to-end stale case.
    """
    conn = _db()
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "unlimited")
    assert rec is not None
    by_label = {p.label: p for p in rec.picks}
    assert by_label["budget_pick"].confidence == "High"
    assert by_label["best_quality"].confidence == "Medium"


def test_a_gap_wider_than_the_threshold_is_not_disclosed_as_a_close_call() -> None:
    """REQ-REC-004's NEGATIVE direction — M13-W1 tester MAJOR-3.

    A tester replaced `if gap <= close_pts:` with `if True:` and all 810 tests stayed green: a
    runner-up forty points behind would have been announced as "within the margin of error and
    either choice is defensible". `CLOSE_CALL_PTS == 1.5` was asserted as a CONSTANT and never as a
    THRESHOLD, and the sibling above asserts `close_call is None` for a different reason
    (a one-row frontier), so neither test touching close-call semantics constrained it.

    Here the frontier has two rows and the gap is 9.2 points — far outside 1.5 — so silence is the
    only correct answer.
    """
    conn = connect()
    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", SCORES), run)
    reconcile(conn)
    build_price_medians(conn)
    rec = recommend(conn, "unlimited")
    assert rec is not None
    # Claude 4.5 Opus 79.2 @ $11.25 and Gemini 3 Flash 75.8 @ $1.12 are a genuine trade-off, so
    # both are on the frontier -- the branch is REACHED, and must decline to fire.
    assert rec.frontier_size > 1
    assert rec.close_call is None


def test_a_stale_secondary_does_not_grade_up() -> None:
    """REQ-UNC-002 end to end: the same fixture, with the Aider board 174 days old.

    The unit test pins the rule; this pins that `recommend()` actually threads the board's age
    into the pick. A rule nothing calls is the shape this project has already shipped once, when
    nine green tests stood beside a `cheaper_phrase` the product could not reach.
    """
    conn = connect()
    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", SCORES), run)
    ingest_aider(conn, FakeRawSource("aider", AIDER_STALE), run)
    reconcile(conn)
    build_price_medians(conn)
    rec = recommend(conn, "unlimited")
    assert rec is not None
    by_label = {p.label: p for p in rec.picks}
    assert by_label["budget_pick"].confidence == "Medium"
    assert "Aider" not in by_label["budget_pick"].confidence_basis


def test_close_call_is_disclosed() -> None:
    """REQ-REC-004: a near-tie at the top is stated, not hidden.

    **Fixture corrected at M13-W1 (REQ-FIX-001), and the correction is the finding.** This test
    used to seed both models at EXACTLY 75.8 with different prices, and passed because the shipped
    Pareto predicate was strict on both axes and therefore kept a row that was equal on quality and
    dearer. So the "near-tie at the top" it asserted was a tie between one viable model and one
    that was simply worse — the product disclosed a trade-off nobody had to make.

    Under correct dominance the cheaper twin wins outright and there is no second frontier row, so
    the disclosure correctly disappears. The scores now differ by 0.9 — inside `CLOSE_CALL_PTS` and
    not equal — which is what a near-tie is, and what this criterion was always about.

    The exact-tie case did not lose its coverage: it moved to
    `test_an_equal_score_at_a_higher_price_is_not_a_close_call` below, which asserts the NEW
    behaviour rather than the old.
    """
    assert CLOSE_CALL_PTS == 1.5
    conn = connect()
    pricing = json.dumps(
        {
            "gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 1e-06,
                "output_cost_per_token": 4e-06,
            },
            "gemini-3-flash": {
                "mode": "chat",
                "input_cost_per_token": 5e-07,
                "output_cost_per_token": 3e-06,
            },
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "a + GPT-5", "resolved": 75.8, "date": "2025-09-01"},
                        {"name": "b + Gemini 3 Flash", "resolved": 74.9, "date": "2026-02-17"},
                    ],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    # M7-W2: production builds the price medians in `app.workflows.build`, not inside
    # `recommend()`. A fixture that reconciles is standing in for that build, so it does
    # the same last step -- otherwise it seeds an artifact the engine correctly refuses.
    build_price_medians(conn)
    rec = recommend(conn, "unlimited")
    assert rec is not None
    assert rec.close_call is not None
    assert "is only 0.9 points behind" in rec.close_call


def test_an_equal_score_at_a_higher_price_is_not_a_close_call() -> None:
    """REQ-FIX-001: a dearer twin is dominated, so there is no trade-off to disclose.

    This is the scenario `test_close_call_is_disclosed` used to carry, asserted the other way
    round. Two models at exactly 75.8 where one is cheaper: the cheaper one wins on both axes at
    once, the frontier is a single row, and calling that a close call would tell the reader they
    had a decision to make when they do not.
    """
    conn = connect()
    pricing = json.dumps(
        {
            "gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 1e-06,
                "output_cost_per_token": 4e-06,
            },
            "gemini-3-flash": {
                "mode": "chat",
                "input_cost_per_token": 5e-07,
                "output_cost_per_token": 3e-06,
            },
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "a + GPT-5", "resolved": 75.8, "date": "2025-09-01"},
                        {"name": "b + Gemini 3 Flash", "resolved": 75.8, "date": "2026-02-17"},
                    ],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    build_price_medians(conn)
    rec = recommend(conn, "unlimited")
    assert rec is not None
    assert rec.frontier_size == 1
    assert rec.close_call is None


def test_budget_pick_warns_when_quality_floor_unmet() -> None:
    """W4 review BLOCKING-1 regression: below-floor fallback must SAY so, never lie."""
    conn = connect()
    pricing = json.dumps(
        {
            "gpt-5-nano": {
                "mode": "chat",
                "input_cost_per_token": 5e-08,
                "output_cost_per_token": 4e-07,
            }
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    # The board's top is models this budget cannot buy (nobody prices them), so
                    # its top third sits above the one model that fits (D-159).
                    "results": [{"name": "mini-SWE-agent + GPT-5 nano", "resolved": 40.0},
                                *[{"name": f"some-agent + Frontier {i}", "resolved": 80.0 + i}
                                  for i in range(3)]],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    # M7-W2: production builds the price medians in `app.workflows.build`, not inside
    # `recommend()`. A fixture that reconciles is standing in for that build, so it does
    # the same last step -- otherwise it seeds an artifact the engine correctly refuses.
    build_price_medians(conn)
    rec = recommend(conn, "low")
    assert rec is not None
    cheap = rec.picks[2]
    assert cheap.score < cheap.why_fact["floor"]
    assert "WARNING" in cheap.why  # honest disclosure, not the standard floor text
    assert "minimum-quality bar." not in cheap.why


def test_budget_filters_nonempty_ranking_to_none() -> None:
    """REQ-REC-002: models EXIST but none fits the budget → None (not empty-db artifact)."""
    conn = connect()
    pricing = json.dumps(
        {
            "claude-4-5-opus": {
                "mode": "chat",
                "input_cost_per_token": 5e-06,
                "output_cost_per_token": 2.5e-05,
            }
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [{"name": "live-SWE-agent + Claude 4.5 Opus", "resolved": 79.2}],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    # M7-W2: production builds the price medians in `app.workflows.build`, not inside
    # `recommend()`. A fixture that reconciles is standing in for that build, so it does
    # the same last step -- otherwise it seeds an artifact the engine correctly refuses.
    build_price_medians(conn)
    assert recommend(conn, "unlimited") is not None  # sanity: it ranks
    assert recommend(conn, "low") is None  # $11.25 blended > $2 cap


def test_unknown_budget_raises() -> None:
    """The budget check runs BEFORE any database work, so an empty connection is the right fixture.

    M7-W2 note: this also pins the ordering. `require_price_medians` must not run first, or a
    caller's typo would be reported as an unbuilt artifact.
    """
    with pytest.raises(ValueError, match="unknown budget"):
        recommend(connect(), "yok-boyle-butce")


def test_secondary_score_rounds_and_absence_stays_absent(tmp_path, capsys) -> None:
    """W4 review MINOR-2 citing test: `round_optional_score` through the real CLI.

    REQ-REC-010 rounds the JSON contract, but the secondary (evidence-only) score is
    nullable — and the one thing a rounding helper must never do to a missing number is
    turn it into 0.0. Both halves are asserted in the same output: DeepSeek carries an
    Aider score with junk precision, the leader carries none.
    """
    from app.workflows.recommend import main

    conn = _db()
    conn.execute(
        "UPDATE scores SET score = 74.24444444 WHERE model_id = 'deepseek-v3.2'"
        " AND benchmark = 'Aider polyglot'"
    )
    conn.commit()
    db = tmp_path / "advisor.db"
    dest = sqlite3.connect(db)
    conn.backup(dest)
    dest.commit()
    dest.close()

    assert main(["--db", str(db), "--budget", "unlimited"]) == 0
    picks = {p["model"]: p for p in json.loads(capsys.readouterr().out)["picks"]}
    assert picks["DeepSeek V3.2"]["secondary_score"] == 74.2  # rounded, not raw
    assert picks["Claude 4.5 Opus"]["secondary_score"] is None  # absent, not 0.0


def test_model_engine_trade_off_never_claims_a_gap_the_fields_deny() -> None:
    """W4 re-review BLOCKING-A, model-engine half: same guard, second call site.

    `lead_phrase` is shared with the subscription engine, so the helper itself is
    defended there; this test pins the four CALL SITES in this module — inlining the raw
    delta back into any trade-off string reintroduces "0.1 points lower" between two
    picks the JSON both prints as 79.2.
    """
    conn = _db()
    conn.execute("UPDATE scores SET score = 79.249 WHERE model_id = 'claude-4.5-opus'")
    conn.execute("UPDATE scores SET score = 79.151 WHERE model_id = 'gemini-3-flash'")
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "unlimited")
    assert rec is not None
    assert rec.picks[0].score == rec.picks[1].score == 79.2
    assert rec.close_call is not None
    assert "is level" in rec.close_call
    trade_off = rec.picks[1].trade_off
    assert trade_off is not None
    assert trade_off.startswith("level with the leader,")
    assert "Liderden" not in trade_off


def test_secondary_benchmark_evidence_is_cited_too() -> None:
    """M5 security review MINOR citing test: a served secondary score owes its credit.

    The first cut derived attribution from PRIMARY evidence only, so a payload whose
    primary rows came from Epoch served an Aider secondary score, graded its confidence
    "two independent benchmarks" on it, and cited only Epoch.
    """
    from app.workflows.rank import SWEBENCH_ATTRIBUTION

    conn = _db()
    conn.execute(
        "UPDATE scores SET source = 'epoch_swe_bench_verified' WHERE benchmark = ?"
        # D-159: only the RANKED rows move; the surface's own board (swebench) keeps the models
        # nobody prices, so it still has a floor to recommend from. An empty own board has none,
        # and the Budget Pick then says so (test_the_budget_pick_says_when_its_board_is_empty).
        " AND model_id IS NOT NULL",
        ("SWE-bench Verified",),
    )
    build_price_medians(conn)  # M7-W2: production builds these in app.workflows.build
    rec = recommend(conn, "unlimited")
    assert rec is not None
    graded_on_two = [p for p in rec.picks if p.secondary_score is not None]
    assert graded_on_two, "fixture must serve a secondary score for this to mean anything"
    assert all(p.confidence == "High" for p in graded_on_two)
    assert SWEBENCH_ATTRIBUTION in rec.sources  # Aider's citation lives in this string
