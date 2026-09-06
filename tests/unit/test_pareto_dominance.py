"""Pareto dominance in both engines — cites REQ-FIX-001.

**The defect these tests were written against, reproduced before it was diagnosed.** Both
`recommend.pareto_frontier` and `subscribe._pareto` asked

    o.score > r.score and o.price < r.price

which is strict on BOTH axes. Dominance is not strict on both: a row is dominated when another is
at least as good on each axis and strictly better on at least one. Under the shipped predicate a
model with the SAME score at a HIGHER price stayed on the frontier, and so did a model at the SAME
price with a LOWER score — neither of which is a trade-off a reader could act on, because in each
case one row is simply worse.

Measured against `advisor.db` at the time of writing: **9 of 27 (surface, budget) combinations
returned a frontier that was too large**, and `frontier_size` is a published `/v1` field the client
decodes at `Models.swift:73`.

**The severity is bounded deliberately, because overstating it would be its own defect.** The picks
did not change on that data: a wrongly-retained row is never strictly cheaper than the row that
should have dominated it, so `min(value_pool, key=price)` lands on the same model. What was wrong
was the published count and the claim it stands for — "these are the models not beaten on both
axes".

The equal-equal case is the one worth naming: two rows identical on score AND price dominate
nothing, because neither is strictly better on anything. Both must stay. A predicate that drops one
of them would be trading this bug for a worse one — a silently disappearing model.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.workflows.rank import RankingRow
from app.workflows.recommend import pareto_frontier
from app.workflows.subscribe import PlanRank, _pareto


def _ranking_row(model: str, score: float, blended: float) -> RankingRow:
    """A `RankingRow` whose only meaningful fields are the two the frontier reads.

    Built by reflection over the dataclass rather than by typing out every field, so that adding a
    field to `RankingRow` cannot silently turn this into a test of a stale shape.
    """
    values: dict[str, object] = {}
    for field in dataclasses.fields(RankingRow):
        annotation = str(field.type)
        if field.name == "model":
            values[field.name] = model
        elif field.name == "score":
            values[field.name] = score
        elif field.name == "blended_per_m":
            values[field.name] = blended
        elif field.name == "vendor":
            values[field.name] = "Vendor"
        elif "None" in annotation:
            values[field.name] = None
        elif "float" in annotation:
            values[field.name] = 0.0
        elif "str" in annotation:
            values[field.name] = "x"
        else:  # pragma: no cover - a new non-optional kind would fail loudly here
            raise AssertionError(f"unhandled field type on RankingRow.{field.name}: {annotation}")
    return RankingRow(**values)


def _plan_rank(plan: str, score: float, monthly: float) -> PlanRank:
    values: dict[str, object] = {}
    for field in dataclasses.fields(PlanRank):
        annotation = str(field.type)
        if field.name == "plan":
            values[field.name] = plan
        elif field.name == "score":
            values[field.name] = score
        elif field.name == "monthly_usd":
            values[field.name] = monthly
        elif "None" in annotation:
            values[field.name] = None
        elif "float" in annotation:
            values[field.name] = 0.0
        elif "int" in annotation:
            values[field.name] = 0
        elif "str" in annotation:
            values[field.name] = "x"
        else:  # pragma: no cover
            raise AssertionError(f"unhandled field type on PlanRank.{field.name}: {annotation}")
    return PlanRank(**values)


#: (name, rows as (id, score, cost), the ids that must survive).
#:
#: Every case states WHY in its name, because a frontier case reduced to numbers is unreadable six
#: months later — and this table is the specification of REQ-FIX-001, not an illustration of it.
CASES = [
    (
        "equal score, dearer row is dominated",
        [("cheap", 80.0, 2.0), ("dear", 80.0, 9.0)],
        {"cheap"},
    ),
    (
        "equal cost, lower-scoring row is dominated",
        [("better", 90.0, 5.0), ("worse", 70.0, 5.0)],
        {"better"},
    ),
    (
        "strictly dominated row is dominated (the case the shipped predicate got right)",
        [("best", 95.0, 1.0), ("worst", 60.0, 9.0)],
        {"best"},
    ),
    (
        "a genuine trade-off survives: better costs more",
        [("strong", 90.0, 9.0), ("thrifty", 70.0, 1.0)],
        {"strong", "thrifty"},
    ),
    (
        "identical rows dominate nothing and both survive",
        [("twin-a", 80.0, 5.0), ("twin-b", 80.0, 5.0)],
        {"twin-a", "twin-b"},
    ),
    (
        "one dominator removes several dominated rows at once",
        [("apex", 90.0, 1.0), ("same-score", 90.0, 4.0), ("same-cost", 50.0, 1.0)],
        {"apex"},
    ),
]


@pytest.mark.parametrize("name, rows, survivors", CASES, ids=[c[0] for c in CASES])
def test_model_engine_frontier(
    name: str, rows: list[tuple[str, float, float]], survivors: set[str]
) -> None:
    frontier = pareto_frontier([_ranking_row(*row) for row in rows])
    assert {row.model for row in frontier} == survivors, name


@pytest.mark.parametrize("name, rows, survivors", CASES, ids=[c[0] for c in CASES])
def test_subscription_engine_frontier(
    name: str, rows: list[tuple[str, float, float]], survivors: set[str]
) -> None:
    """The same table against the OTHER engine.

    V4C-49's shape: the rule was written twice, so fixing one copy and calling it done is how this
    project would have shipped half a repair. `subscribe._pareto` ranks plans on monthly price
    rather than blended $/1M, and the dominance question is identical.
    """
    frontier = _pareto([_plan_rank(*row) for row in rows])
    assert {row.plan for row in frontier} == survivors, name


def test_frontier_size_is_the_count_of_undominated_rows() -> None:
    """`frontier_size` is published, so the count is a claim and not an internal.

    The shipped predicate returned 3 here — it kept both rows that are beaten without being beaten
    on both axes at once, and a reader decoding `frontier_size` at `Models.swift:73` was told three
    models were on the trade-off curve when one was.
    """
    rows = [
        _ranking_row("apex", 90.0, 1.0),
        _ranking_row("same-score-dearer", 90.0, 4.0),
        _ranking_row("same-cost-worse", 50.0, 1.0),
    ]
    assert len(pareto_frontier(rows)) == 1


def test_the_frontier_stays_sorted_by_quality_then_price() -> None:
    """Order is load-bearing: `recommend` reads `frontier[0]` as the quality pick.

    A dominance fix that disturbed the ordering would change which model is called BEST QUALITY
    while every dominance test still passed, so the ordering is asserted separately rather than
    trusted to survive.
    """
    rows = [
        _ranking_row("mid", 80.0, 3.0),
        _ranking_row("top", 90.0, 8.0),
        _ranking_row("cheap", 60.0, 1.0),
    ]
    assert [row.model for row in pareto_frontier(rows)] == ["top", "mid", "cheap"]


def test_equal_scores_and_equal_prices_break_on_name() -> None:
    """The last term of the sort key, and the only tiebreak still reachable after the fix.

    **Writing this test found something the reviewer's mutant report implied and nobody stated:
    the PRICE term of `(-score, blended_per_m, model)` is now dead code.** Two frontier rows can
    only tie on score if they also tie on price — otherwise the cheaper one dominates the dearer
    one and never reaches the sort. So `blended_per_m` can never break a tie that `-score` left
    open. The first attempt at this test asserted an ordering of three equal-score rows at
    different prices and failed, because the correct frontier is one row.

    That is not a defect and the term is deliberately left in place: it costs nothing, it states
    the intended ordering, and removing it would make the key disagree with `min(value_pool,
    key=(blended_per_m, model))` two functions away. It is recorded so a future reader does not
    spend an hour writing the test that cannot exist.
    """
    rows = [_ranking_row("b", 80.0, 5.0), _ranking_row("a", 80.0, 5.0)]
    assert [r.model for r in pareto_frontier(rows)] == ["a", "b"]


def test_the_subscription_frontier_orders_the_same_way() -> None:
    """The second engine's key is `(-score, monthly_usd, plan)` and had the same untested tail."""
    rows = [_plan_rank("b", 80.0, 5.0), _plan_rank("a", 80.0, 5.0)]
    assert [r.plan for r in _pareto(rows)] == ["a", "b"]
