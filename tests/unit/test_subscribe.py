"""REQ-REC-007/-008: subscription recommender — three plan answers, honesty intact."""

from __future__ import annotations

import json
import sqlite3

import pytest

from app.workflows.ingest import RunContext
from app.workflows.plans import ingest_plans
from app.workflows.rank import SWEBENCH_ATTRIBUTION
from app.workflows.recommend import main
from app.workflows.registry import reconcile_plans
from app.workflows.schema import connect
from app.workflows.subscribe import plan_ranking, recommend_subscription

# Registry-matchable names on purpose: Gemini 3.1 Pro -> gemini-3.1-pro,
# Claude 4.5 Opus -> claude-4.5-opus, GPT-5 -> gpt-5. "Mystery Model X" matches nothing.
DOC = """
schema: 1
staleness_days: 30
budget_caps_usd: {low: 10, medium: 25, unlimited: null}
plans:
  - id: cheap-plan
    provider: BudgetCo
    name: Cheap Plan
    monthly_usd: 8
    currency: USD
    region: US
    limits: entry tier
    included_models: [GPT-5]
    source_url: https://budgetco.example/pricing
    last_verified: 2026-08-15
  - id: mid-plan
    provider: MidCo
    name: Mid Plan
    monthly_usd: 20
    currency: USD
    region: US
    limits: flagship tier
    included_models: [Gemini 3.1 Pro]
    source_url: https://midco.example/pricing
    last_verified: 2026-08-15
  - id: top-plan
    provider: TopCo
    name: Top Plan
    monthly_usd: 100
    currency: USD
    region: US
    limits: max tier
    included_models: [Claude 4.5 Opus]
    source_url: https://topco.example/pricing
    last_verified: 2026-08-15
  - id: vague-plan
    provider: VagueCo
    name: Vague Plan
    monthly_usd: 15
    currency: USD
    region: US
    limits: frontier models, roster unpublished
    included_models: [Mystery Model X]
    source_url: https://vagueco.example/pricing
    last_verified: 2026-08-15
"""

SIX_SCOREABLE_DOC = DOC + """
  - id: extra-one
    provider: ExtraCo
    name: Extra One
    monthly_usd: 30
    currency: USD
    region: US
    limits: synthetic budget disclosure fixture
    included_models: [GPT-5]
    source_url: https://extra.example/one
    last_verified: 2026-08-15
  - id: extra-two
    provider: ExtraCo
    name: Extra Two
    monthly_usd: 40
    currency: USD
    region: US
    limits: synthetic budget disclosure fixture
    included_models: [Gemini 3.1 Pro]
    source_url: https://extra.example/two
    last_verified: 2026-08-15
  - id: extra-three
    provider: ExtraCo
    name: Extra Three
    monthly_usd: 50
    currency: USD
    region: US
    limits: synthetic budget disclosure fixture
    included_models: [Claude 4.5 Opus]
    source_url: https://extra.example/three
    last_verified: 2026-08-15
"""

SCORES = (
    # (model_id, raw_name, score) on SWE-bench Verified
    ("gpt-5", "agent + GPT-5", 70.0),
    ("gemini-3.1-pro", "agent + Gemini 3.1 Pro", 77.4),
    ("claude-4.5-opus", "agent + Claude 4.5 Opus", 79.2),
)


def _db(doc: str = DOC) -> sqlite3.Connection:
    conn = connect()
    ingest_plans(conn, doc, RunContext())
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    return conn


def test_three_labeled_plan_picks_unlimited_budget() -> None:
    rec = recommend_subscription(_db(), budget="unlimited", task="coding")
    assert rec is not None
    labels = [p.label for p in rec.picks]
    assert labels == ["best_quality", "best_value", "budget_pick"]
    assert rec.picks[0].plan == "Top Plan"  # 79.2 via Claude 4.5 Opus
    assert rec.picks[0].scored_by_model == "Claude 4.5 Opus"
    # Value: Pareto frontier, within 6.0 of 79.2 → Mid Plan (77.4 @ $20)
    assert rec.picks[1].plan == "Mid Plan"
    assert rec.picks[1].trade_off is not None
    # Budget pick: cheapest meeting floor 65.0 → Cheap Plan (70.0 @ $8)
    assert rec.picks[2].plan == "Cheap Plan"
    assert "minimum-quality bar" in rec.picks[2].why
    # W4 review BLOCKING-2: this fixture's evidence is swebench, so that is what the
    # payload cites — and it must NOT claim Epoch or the per-token pricing feeds the
    # plan engine never reads. REQ-LIC-001's Epoch half is proven on Epoch evidence in
    # test_subscription_payload_cites_epoch_only_when_it_ranks_on_epoch_evidence.
    assert rec.sources == (SWEBENCH_ATTRIBUTION,)


def test_budget_cap_filters_before_scoring() -> None:
    rec = recommend_subscription(_db(), budget="medium", task="coding")
    assert rec is not None
    assert {p.plan for p in rec.picks} <= {"Cheap Plan", "Mid Plan"}  # $100 plan excluded
    assert rec.picks[0].plan == "Mid Plan"
    rec = recommend_subscription(_db(), budget="low", task="coding")
    assert rec is not None
    assert all(p.plan == "Cheap Plan" for p in rec.picks)


def test_budget_notice_counts_only_scoreable_plans_excluded_by_price() -> None:
    """REQ-REC-013: six scoreable rows under low budget disclose five priced-out rows."""
    rec = recommend_subscription(_db(SIX_SCOREABLE_DOC), budget="low", task="coding")
    assert rec is not None
    assert rec.eligible_count == 1
    assert rec.excluded_by_budget == 5
    assert rec.budget_notice == "The budget cap excluded 5 scoreable plan(s) from the options."
    assert rec.unscored_plans == ("Vague Plan",)

    unlimited = recommend_subscription(_db(SIX_SCOREABLE_DOC), budget="unlimited", task="coding")
    assert unlimited is not None
    assert unlimited.excluded_by_budget == 0
    assert unlimited.budget_notice is None


def test_unscored_plan_is_disclosed_never_ranked() -> None:
    rec = recommend_subscription(_db(), budget="unlimited", task="coding")
    assert rec is not None
    assert rec.unscored_plans == ("Vague Plan",)
    assert all(p.plan != "Vague Plan" for p in rec.picks)


def test_no_rankable_plan_returns_none() -> None:
    conn = connect()
    ingest_plans(conn, DOC, RunContext())
    reconcile_plans(conn)  # no scores inserted → nothing rankable
    assert recommend_subscription(conn, "unlimited", "coding") is None


def test_quality_floor_unmet_warns_instead_of_pretending() -> None:
    """The M1-W4 honesty lesson, on the plan axis."""
    conn = _db()
    conn.execute("UPDATE scores SET score = 40.0")  # everyone below the 65.0 floor
    rec = recommend_subscription(conn, "unlimited", "coding")
    assert rec is not None
    assert "WARNING" in rec.picks[2].why
    assert "trading quality away" in rec.picks[2].why


def test_stale_plan_rows_disclosed_in_output() -> None:
    """REQ-REC-008: the output names stale rows and their dates."""
    doc = DOC.replace("last_verified: 2026-08-15", "last_verified: 2026-05-01", 1)  # cheap-plan
    conn = connect()
    run = RunContext()
    run.observed_at = "2026-08-15T00:00:00+00:00"
    ingest_plans(conn, doc, run)
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    rec = recommend_subscription(conn, "unlimited", "coding")
    assert rec is not None
    assert rec.stale_notice is not None
    assert "Cheap Plan" in rec.stale_notice
    assert "2026-05-01" in rec.stale_notice


def test_close_call_disclosed_on_near_tie() -> None:
    conn = _db()
    conn.execute(
        "UPDATE scores SET score = 78.5 WHERE model_id = 'gemini-3.1-pro'"
    )  # gap 0.7 ≤ 1.5
    rec = recommend_subscription(conn, "unlimited", "coding")
    assert rec is not None
    assert rec.close_call is not None
    assert "Mid Plan" in rec.close_call


def test_plan_ranking_orders_by_score_then_price() -> None:
    from app.workflows.categories import CATEGORIES

    ranking = plan_ranking(_db(), CATEGORIES["coding"])
    assert [r.plan_id for r in ranking] == ["top-plan", "mid-plan", "cheap-plan"]
    assert ranking[0].score == 79.2
    assert ranking[0].evidence_source == "swebench"
    assert ranking[0].evidence_source_url == "https://x"
    assert ranking[0].evidence_raw_name == "agent + Claude 4.5 Opus"


def test_cli_subscription_through_real_entrypoint(tmp_path, capsys) -> None:
    """V4C-50 + REQ-REC-007: the exact shipped command line."""
    db = tmp_path / "advisor.db"
    conn = connect(str(db))  # real schema + real ingest path below
    ingest_plans(conn, DOC, RunContext())
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    conn.commit()
    conn.close()

    assert main(["--db", str(db), "--budget", "medium", "--task", "coding", "--subscription"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["picks"][0]["plan"] == "Mid Plan"
    assert out["unscored_plans"] == ["Vague Plan"]

    # exit 1: no eligible plan (low excludes everything rankable after price bump)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE plans SET monthly_usd = 500")
    conn.commit()
    conn.close()
    assert main(["--db", str(db), "--budget", "low", "--task", "coding", "--subscription"]) == 1
    assert "no eligible plan" in capsys.readouterr().out

    # exit 2: DB without an ingested plan table config
    empty = tmp_path / "empty.db"
    connect(str(empty)).close()
    assert main(["--db", str(empty), "--budget", "medium", "--subscription"]) == 2


def test_model_path_regression_untouched(tmp_path, capsys) -> None:
    """--subscription is additive: the model CLI behaves exactly as before."""
    empty = tmp_path / "m.db"
    connect(str(empty)).close()
    assert main(["--db", str(empty), "--budget", "unlimited", "--task", "coding"]) == 1
    assert "no eligible model" in capsys.readouterr().out


def test_missing_plan_config_fails_with_usage_error() -> None:
    with pytest.raises(ValueError, match="plan_config missing"):
        recommend_subscription(connect(), "medium", "coding")


def test_plan_priced_exactly_at_cap_is_eligible_through_cli(tmp_path, capsys) -> None:
    """W3 review MINOR-1+2: cap boundary is INCLUSIVE (<=) and stale disclosure
    survives the real entrypoint — both asserted through main() (V4C-50)."""
    doc = DOC.replace("monthly_usd: 20", "monthly_usd: 25")  # mid-plan lands ON the medium cap
    doc = doc.replace("last_verified: 2026-08-15", "last_verified: 2026-05-01", 1)  # cheap stale
    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    run = RunContext()
    run.observed_at = "2026-08-15T00:00:00+00:00"
    ingest_plans(conn, doc, run)
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    conn.commit()
    conn.close()
    assert main(["--db", str(db), "--budget", "medium", "--task", "coding", "--subscription"]) == 0
    out = json.loads(capsys.readouterr().out)
    # Boundary: the $25 plan under cap 25 MUST be eligible — and it wins on score.
    assert out["picks"][0]["plan"] == "Mid Plan"
    assert out["picks"][0]["monthly_usd"] == 25
    # REQ-REC-008 through the real entrypoint: the stale row is named with its date.
    assert out["stale_notice"] is not None
    assert "Cheap Plan" in out["stale_notice"]
    assert "2026-05-01" in out["stale_notice"]


def test_scores_are_rounded_at_the_output_boundary_not_in_the_math() -> None:
    """REQ-REC-010: the JSON contract carries 1 decimal; ranking keeps full precision.

    Arena hands us values like 1481.5937567329202. An app rendering that shows
    precision the benchmark does not have — but rounding BEFORE the comparison
    would let two models tie that are not actually tied.
    """
    from app.workflows.categories import CATEGORIES
    from app.workflows.subscribe import plan_ranking

    conn = _db()
    conn.execute("UPDATE scores SET score = 77.44444444 WHERE model_id = 'gemini-3.1-pro'")
    conn.execute("UPDATE scores SET score = 77.45555555 WHERE model_id = 'claude-4.5-opus'")
    # the ranking still separates them on the raw values...
    ranking = plan_ranking(conn, CATEGORIES["coding"])
    assert ranking[0].score == 77.45555555
    assert ranking[0].score != ranking[1].score
    # ...while the OUTPUT rounds once, at the boundary
    rec = recommend_subscription(conn, "unlimited", "coding")
    assert rec is not None
    assert rec.picks[0].score == 77.5
    assert all(len(str(p.score).split(".")[1]) <= 1 for p in rec.picks)


TWIN_DOC = DOC.replace(
    """  - id: vague-plan
    provider: VagueCo
    name: Vague Plan
    monthly_usd: 15
    currency: USD
    region: US
    limits: frontier models, roster unpublished
    included_models: [Mystery Model X]""",
    """  - id: twin-plan
    provider: TwinCo
    name: Twin Plan
    monthly_usd: 12
    currency: USD
    region: US
    limits: same engine, different badge
    included_models: [Gemini 3.1 Pro]""",
)


def _member_names(rec) -> tuple[str, ...]:
    """Every equivalent plan name, flattened.

    REQ-REC-014 (W-002) turned `equivalent_plans` from a flat name tuple into labelled groups, so
    the assertions that only care about WHICH plans are equivalent flatten it here. The assertions
    that care about the structure itself live in `test_serializer_parity.py`.
    """
    return tuple(sorted(m.plan for g in rec.equivalent_plans for m in g.members))


def test_equivalent_plans_are_named_when_the_three_labels_collapse() -> None:
    """REQ-REC-009 as evidence allows it: when several plans name the SAME model they
    are indistinguishable on quality, so the answer says so and points at the cheapest
    instead of manufacturing variety (measured live at M4-W4: three <=$25 plans all
    scoring 1479.6 via Gemini 3.1 Pro)."""
    rec = recommend_subscription(_db(TWIN_DOC), "medium", "coding")
    assert rec is not None
    # mid-plan ($20) and twin-plan ($12) both rank on Gemini 3.1 Pro at 77.4
    assert _member_names(rec) == ("Mid Plan",)
    assert rec.equivalence_note is not None
    assert "Gemini 3.1 Pro" in rec.equivalence_note
    # W4 review BLOCKING-2: `"Twin Plan" in note` passed on the plan LIST alone and so
    # could not fail — the claim under test is that the note names the cheapest of the
    # group WITH its price. Assert the sentence that carries the claim.
    assert "The cheapest in this group is Twin Plan ($12.00/month)." in rec.equivalence_note
    assert "Monthly difference for the same model: $12.00 — $20.00." in rec.equivalence_note
    # and when no picked plan has a twin, nothing is claimed
    solo = recommend_subscription(_db(), "unlimited", "coding")
    assert solo is not None
    assert solo.equivalent_plans == ()
    assert solo.equivalence_note is None


def test_equivalence_is_computed_for_every_label_not_only_the_quality_pick() -> None:
    """W4 review BLOCKING-1 citing test. The first cut compared plans only against the
    QUALITY pick, so on live data it stayed SILENT in the case that mattered most: the
    top plan was alone, while best_value and budget_pick both collapsed onto a plan that
    a $99.99 plan ties exactly. Here Top Plan ($100, Claude) is alone, and the collapse
    is on the value pick — the note must still fire and name the cheap twin.
    """
    rec = recommend_subscription(_db(TWIN_DOC), "unlimited", "coding")
    assert rec is not None
    assert rec.picks[0].plan == "Top Plan"  # quality pick has NO twin
    assert rec.picks[1].plan == "Twin Plan"  # value pick does
    assert _member_names(rec) == ("Mid Plan",)
    assert rec.equivalence_note is not None
    assert "The cheapest in this group is Twin Plan ($12.00/month)." in rec.equivalence_note


def test_rounding_never_reaches_the_pareto_comparison() -> None:
    """W4 review MINOR-1 citing test: REQ-REC-010 rounds at the OUTPUT boundary only.

    Mid Plan beats Twin Plan by 0.04 — a real gap that disappears at 1 decimal. If
    `round_score` moved into `plan_ranking`/`_pareto`, the two would tie and the cheaper
    plan would take the quality label. The output still shows both as 77.4; the ORDER is
    what proves the math ran on raw values.
    """
    conn = _db(TWIN_DOC)
    conn.execute("UPDATE scores SET score = 77.44 WHERE model_id = 'gemini-3.1-pro'")
    conn.execute(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
        " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "gpt-5",
            "agent + GPT-5 (tuned)",
            "SWE-bench Verified",
            "% resolved",
            77.40,
            "test-agent",
            "2026-08-01",
            "swebench",
            "https://x",
            "2026-08-15T00:00:00+00:00",
        ),
    )
    # Cheap Plan (GPT-5) 77.40 @ $8 vs Mid Plan (Gemini) 77.44 @ $20 vs Twin Plan 77.44 @ $12
    rec = recommend_subscription(conn, "medium", "coding")
    assert rec is not None
    assert rec.picks[0].plan == "Twin Plan"  # 77.44 raw beats 77.40 raw
    assert rec.picks[0].score == 77.4  # ...and the OUTPUT is still rounded
    assert rec.picks[0].scored_by_model == "Gemini 3.1 Pro"
    # Cheap Plan would have won the quality label had the comparison seen 77.4 == 77.4.
    assert "Cheap Plan" not in _member_names(rec)


def test_a_sub_rounding_gap_never_prints_as_a_zero_delta() -> None:
    """W4 re-review BLOCKING-A citing test: the display delta is guarded in EVERY string.

    A raw gap of 0.098 is real (the threshold uses it) but both scores round to the same
    77.4 the JSON carries, so any sentence between them claiming a gap contradicts the
    fields it sits next to. `close_call` AND the per-pick `trade_off` must both say "same
    score". The fixture is deliberately chosen so `round(a) - round(b)` (0.0) differs from
    `round(a - b)` (0.1): it fails BOTH if the zero-guard goes and if `shown_gap` rounds
    after subtracting instead of before.
    """
    conn = _db()
    conn.execute("UPDATE scores SET score = 77.449 WHERE model_id = 'claude-4.5-opus'")
    conn.execute("UPDATE scores SET score = 77.351 WHERE model_id = 'gemini-3.1-pro'")
    conn.execute("UPDATE plans SET monthly_usd = 30 WHERE id = 'top-plan'")
    rec = recommend_subscription(conn, "unlimited", "coding")
    assert rec is not None
    assert rec.picks[0].score == rec.picks[1].score == 77.4  # the fields are identical...
    assert rec.close_call is not None
    assert "is level" in rec.close_call  # ...so the prose may not claim a gap
    assert "0.0" not in rec.close_call
    trade_off = rec.picks[1].trade_off
    assert trade_off is not None
    assert trade_off.startswith("level with the leader,")
    assert "Liderden" not in trade_off  # the raw-gap phrasing must not survive


def test_equivalence_never_names_a_plan_the_budget_excluded() -> None:
    """W4 re-review MINOR-2 citing test: the group is built from the CAP-FILTERED rows.

    Top Plan ($100) names the same model as Mid Plan ($20). Under `medium` ($25) it is not
    a purchasable option, so naming it — and stretching the quoted price span to $100 —
    would be advice the user cannot act on. Building the group from the unfiltered
    ranking instead of `rows` turns this red.
    """
    doc = DOC.replace("included_models: [Claude 4.5 Opus]", "included_models: [Gemini 3.1 Pro]")
    rec = recommend_subscription(_db(doc), "medium", "coding")
    assert rec is not None
    assert rec.equivalent_plans == ()  # Mid Plan's only twin is over the cap
    assert rec.equivalence_note is None
    # sanity: without the cap the same data DOES pair them
    unlimited = recommend_subscription(_db(doc), "unlimited", "coding")
    assert unlimited is not None
    assert _member_names(unlimited) == ("Top Plan",)  # picked Mid Plan ($20), tied Top ($100)


def test_equivalence_group_membership_is_resolved_by_plan_id_not_name() -> None:
    """W4 re-review MINOR-3 citing test: `plans.name` has no UNIQUE constraint.

    Two curated rows may share a display name. Re-resolving group membership by name
    then drags an unrelated plan — scoring a DIFFERENT model — into the price span the
    note claims is "the same model". Here the $100 namesake ranks on Claude 4.5 Opus and
    must not appear in the Gemini group's $8—$20 span, nor inflate its count.
    """
    doc = DOC.replace(
        """  - id: vague-plan
    provider: VagueCo
    name: Vague Plan
    monthly_usd: 15""",
        """  - id: namesake-plan
    provider: OtherCo
    name: Twin Plan
    monthly_usd: 150""",
    ).replace(
        "    limits: frontier models, roster unpublished\n    included_models: [Mystery Model X]",
        "    limits: same NAME, different engine\n    included_models: [Claude 4.5 Opus]",
    )
    doc = doc.replace(
        """  - id: mid-plan
    provider: MidCo
    name: Mid Plan""",
        """  - id: mid-plan
    provider: MidCo
    name: Twin Plan""",
    )
    conn = _db(doc)
    # cheap-plan (GPT-5) is re-pointed at the Gemini score so it ties mid-plan exactly
    conn.execute("UPDATE scores SET score = 77.4 WHERE model_id = 'gpt-5'")
    conn.execute(
        "UPDATE plan_models SET raw_name = 'Gemini 3.1 Pro', model_id = 'gemini-3.1-pro'"
        " WHERE plan_id = 'cheap-plan'"
    )
    rec = recommend_subscription(conn, "unlimited", "coding")
    assert rec is not None
    note = rec.equivalence_note
    assert note is not None
    assert (
        "2 plans link to the same model (Gemini 3.1 Pro)" in note
    )  # NOT 3 — the namesake is not tied
    assert (
        "2 plans link to the same model (Gemini 3.1 Pro), so they are"
        " indistinguishable on quality: Cheap Plan, Twin Plan."
        " The cheapest in this group is Cheap Plan ($8.00/month)."
        " Monthly difference for the same model: $8.00 — $20.00."
    ) in note  # the $150 namesake is in the OTHER group, never in this span


def test_equivalence_note_says_which_members_rest_on_a_roster() -> None:
    """M4 closure L-1 citing test: the group sentence may not claim a plan PAGE names
    the model when the link came from the provider's separate model list.

    Live, this is asserted about Perplexity Pro, whose plan page names no model version
    at all — the roster (M4-W2) is what links it. The per-pick `why` text already draws
    this line; the group sentence must draw the same one, and must stay SILENT about
    provenance when every member is plan-page-linked.
    """
    conn = _db(TWIN_DOC)
    conn.execute(
        "UPDATE plan_models SET link_source = 'roster',"
        " source_url = 'https://twinco.example/models', last_verified = '2026-08-15'"
        " WHERE plan_id = 'twin-plan'"
    )
    # REQ-SUB-008: this fixture inserts roster links by hand rather than through `ingest_rosters`,
    # so it must also supply the roster policy that governs them. A database carrying roster links
    # with no roster window is incoherent, and `roster_staleness_days` now says so loudly instead
    # of quietly borrowing the plan table's number.
    conn.execute("UPDATE plan_config SET roster_staleness_days = 30 WHERE id = 1")
    rec = recommend_subscription(conn, "medium", "coding")
    assert rec is not None
    note = rec.equivalence_note
    assert note is not None
    assert "the same model" in note and "listeliyor" not in note  # links to, not lists
    assert "For Twin Plan the source is the provider's published model" in note
    # ...and with no roster link in the group, no provenance clause is added at all
    plain = recommend_subscription(_db(TWIN_DOC), "medium", "coding")
    assert plain is not None
    assert plain.equivalence_note is not None
    assert "the source is the provider's published model" not in plain.equivalence_note


def test_budget_that_prices_out_everything_still_says_how_many(tmp_path, capsys) -> None:
    """W4 review MINOR-1 citing test: the no-answer case is where the count matters MOST.

    `recommend_subscription` returns None when the cap excludes every scoreable plan,
    and the first cut computed `excluded_by_budget` AFTER that early return — so the
    user who most needs "your budget excluded all of them" got a bare error, while the
    ledger already recorded W-006 as FIXED. Asserted through the real CLI.
    """
    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    ingest_plans(conn, DOC, RunContext())
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    # Price every scoreable plan above the low cap ($10).
    conn.execute("UPDATE plans SET monthly_usd = 99 WHERE id != 'vague-plan'")
    conn.commit()
    conn.close()

    assert main(["--db", str(db), "--budget", "low", "--task", "coding", "--subscription"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "no eligible plan for this budget"
    assert payload["scoreable_plans"] == 3
    assert payload["excluded_by_budget"] == 3
    assert payload["budget_notice"] == (
        "The budget cap excluded 3 scoreable plan(s) from the options."
    )
