"""Category layer: use-case → primary benchmark, as DATA (REQ-CAT-001/-003).

Design rule (owner-signed, m2-plan §0/D-105): a category ranks ONLY on its
primary benchmark's native scale — Elo and % are never averaged together.
Secondary benchmarks are displayed as evidence, never blended into the order.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategorySpec:
    """One rankable use case (REQ-CAT-001)."""

    id: str
    title: str
    primary_benchmark: str
    metric: str  # metric name as stored in scores.metric
    score_unit: str  # human label for trade-off wording (REQ-REC-005)
    secondary_benchmark: str | None  # evidence-only; NEVER affects ordering (REQ-CAT-003)
    primary_source: str  # informational; health flags live on ingest reports (not persisted yet)
    # Engine thresholds on the category's NATIVE scale (M2-W4 review: data, not code branches):
    min_quality: float  # Budget Pick floor
    value_window: float  # Best Value: within N of the leader
    close_call: float  # near-tie disclosure threshold
    ranking_effort: str | None = None  # named comparable level; None = board has no effort policy
    # D-143 amendment (M14-W4 review M-3): the Elo score a reader sees as 50 / 100. PINNED, and
    # deliberately NOT `min_quality`: the floor is re-measured at every recalibration, and a
    # recalibration must not move every card's number without a new measurement. Set on Elo
    # surfaces only; `None` elsewhere (percentages are already out of 100, ECI stays rank-only).
    score_anchor: float | None = None


#: **Every threshold below is sized on the RANKED population** -- models that reconcile to the
#: registry AND carry a price median -- not on the full board. The engine can only recommend a
#: model somebody can buy, and the two populations differ by an order of magnitude (58 of 521
#: on ECI). Calibrating against the board has now produced wrong thresholds three times
#: (W-037); evidence and method: `docs/reviews/m8-category-calibration.md`, including its
#: 2026-08-19 correction section, which supersedes the table above it.
# --- M12-W2: the titles are what a reader MEETS, and they were written by people who already knew
# what a benchmark was ------------------------------------------------------------------------
#
# Renamed after a 60-year-old CFO used the app. Each new name says what the surface MEASURES rather
# than what the field calls it:
#
#   Everyday assistant / chat  ->  Chat
#   Everyday questions         ->  General knowledge
#   Expert reasoning           ->  Hard science questions   (GPQA is PhD-level science, not "for experts")
#   Computer use               ->  Operating a computer
#   Abstract reasoning         ->  Puzzles & pattern finding (ARC-AGI is unseen visual puzzles)
#
# `Coding`, `Mathematics` and `Web development` are unchanged: they already say what they measure.
#
# **`Agentic coding` is unchanged BY OWNER RULING**, and the council's suggested rename was
# reverted to honour it. Asked which names to simplify he answered, translated from Turkish:
# *"Coding, Agentic Coding ok — there is no simpler version of those, or of mathematics."* The
# lead agent renamed it anyway on the council's recommendation and the naming test caught it,
# because `Coding on its own` collides with `Coding` on its first word — the very defect the test
# exists for. Two corrections in one: the owner had already ruled, and the new name was worse.
#
# **Two of the nine used to begin with "Everyday"** — `assistant` was "Everyday assistant / chat"
# and `everyday` was "Everyday questions". The owner mixed them up on his own screen during the
# M11-W3.5 session, and so did the lead agent while reading his screenshots. That is not a naming
# preference; it is two labels a reader cannot tell apart.
#
# The IDs are untouched. They are the contract (`/v1/categories`, D-127); the titles are the
# product.

CATEGORIES: dict[str, CategorySpec] = {
    "coding": CategorySpec(
        id="coding",
        title="Coding",
        primary_benchmark="SWE-bench Verified",
        metric="% resolved",
        score_unit="points",
        secondary_benchmark="Aider polyglot",
        primary_source="swebench",
        min_quality=65.0,
        value_window=6.0,
        close_call=1.5,
    ),
    "assistant": CategorySpec(
        id="assistant",
        title="Chat",
        primary_benchmark="Arena text",
        metric="elo",
        score_unit="Elo",
        secondary_benchmark=None,
        primary_source="arena",
        # RECALIBRATED 2026-08-15 against the live overall board (REQ-CAL-001;
        # n=389, snapshot 2026-08-12; evidence + method: docs/reviews/m3-elo-calibration.md).
        # This is a DATA edit — the engine did not change.
        min_quality=1400.0,  # was 1300 (admitted 57% of the board); 1400 = top third, leader-108
        value_window=30.0,  # kept: ~4x the noise threshold; 13 candidates within reach of the top
        close_call=8.0,  # was 5; live 95% CIs still overlap for 64% of pairs 8-9 Elo apart
        score_anchor=1400.0,  # pinned 2026-09-20 (D-143); moves only by owner ruling
    ),
    # M5 owner-delegated board decision: DeepSWE is a separate surface because its
    # release dates are not evaluation dates and its harness materially disagrees
    # with Epoch SWE-bench for Gemini. Q1 fixes comparison at one DATA-owned level.
    "agentic-coding": CategorySpec(
        id="agentic-coding",
        title="Agentic coding",
        primary_benchmark="DeepSWE",
        metric="% resolved",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_deepswe_external",
        min_quality=50.0,
        value_window=6.0,
        close_call=1.5,
        ranking_effort="high",
    ),
    # ── D-127's new surfaces ────────────────────────────────────────────────────────────────────
    #
    # Every threshold below was MEASURED on the population the engine actually ranks -- the output
    # of `parse_board`, one row per model at its best score -- and not on the CSV's rows. The first
    # calibration used rows and was wrong wherever a board lists a model several times under
    # different scaffolds: terminalbench is 204 rows and 59 models. Evidence and method:
    # `docs/reviews/m8-category-calibration.md`.
    #
    # `min_quality` is the top third. `close_call` is measurement -- 2x the board's own stderr where
    # it publishes one, else the median gap between adjacent models. `value_window` is sized by how
    # many real alternatives survive it, because a window admitting one candidate turns Best Value
    # into a second copy of Best Quality. **None of the three may be borrowed from another
    # category** (D-105): the scales differ, and M8 found that the RULE does not transfer either.
    "everyday": CategorySpec(
        id="everyday",
        title="General knowledge",
        primary_benchmark="Epoch Capabilities Index",
        metric="ECI",
        score_unit="ECI",
        secondary_benchmark="MMLU",
        primary_source="epoch_eci",
        # Sized on the RANKED population -- reconciled and priced -- not the board: 58 models,
        # not 521. A 3-point window leaves 5 candidates, against coding's 7.
        min_quality=149.9,
        value_window=3.0,
        close_call=0.5,
    ),
    "expert": CategorySpec(
        id="expert",
        title="Hard science questions",
        primary_benchmark="GPQA Diamond",
        metric="% correct",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_gpqa",
        # 263 models, leader 94.8. GPQA publishes a stderr: median 2.52 points, so a gap under 5
        # points is not a difference anyone should act on.
        min_quality=83.6,
        value_window=5.0,
        close_call=5.0,
    ),
    "mathematics": CategorySpec(
        id="mathematics",
        title="Mathematics",
        primary_benchmark="AIME (mock)",
        metric="% correct",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_aime",
        # The noisiest board here: stderr median 4.74 points, so close_call is 9.5. The window has
        # to CLEAR that -- a narrower one would call a gap "within reach" while also calling the
        # same gap noise. On the 51 models that actually rank, 10 points admits 28. That is high
        # against coding's 7 and it is the honest number: AIME has three models tied at exactly
        # 100.0, so they are indistinguishable at the board's own precision (W-035).
        min_quality=84.4,
        value_window=10.0,
        close_call=9.5,
    ),
    "computer-use": CategorySpec(
        id="computer-use",
        title="Operating a computer",
        primary_benchmark="TerminalBench",
        metric="% resolved",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_terminalbench",
        # STRUCTURALLY THIN. 59 models on the board, 33 that reconcile and carry a price. Sized on
        # those 33, a 5-point window admits 5 candidates -- the 20 points an earlier draft argued
        # for was measured on the full board and would have admitted every model above the floor.
        min_quality=53.4,
        value_window=5.0,
        close_call=0.8,
    ),
    "abstract": CategorySpec(
        id="abstract",
        title="Puzzles & pattern finding",
        primary_benchmark="ARC-AGI",
        metric="% correct",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_arc_agi",
        # 168 on the board, 39 ranked. A 5-point window leaves 8 candidates; the 8-point window an
        # earlier draft proposed was sized on the board and admitted all 20 above the floor.
        min_quality=72.8,
        value_window=5.0,
        close_call=1.0,
    ),
    "web-dev": CategorySpec(
        id="web-dev",
        title="Web development",
        primary_benchmark="WebDev Arena",
        metric="elo",
        score_unit="Elo",
        secondary_benchmark=None,
        primary_source="epoch_webdev",
        # The other thin surface, on a different scale and for the same structural reason. 102 on
        # the board, 49 ranked; the leader sits 30 Elo above second. A 100-Elo window admits 3 of
        # those 49. Elo thresholds are NOT comparable to the percentage categories above -- that is
        # what D-105 forbids.
        min_quality=1478.9,
        value_window=100.0,
        close_call=6.8,
        score_anchor=1478.9,  # pinned 2026-09-20 (D-143); moves only by owner ruling
    ),
    # ── M14-W2: two boards of the dataset `assistant` already reads (D-142, D-145) ─────────────
    #
    # `min_quality` = the top third of the WHOLE board, counted over DISTINCT models (each model's
    # best rating). That is the rule the nine surfaces above were actually measured by (W-094), and
    # the owner ruled on 2026-09-20 that new surfaces follow it so the product has one rule (D-145).
    # Reproduce with `scripts/calibrate_board.py --config <board>`, which prints `board_third`.
    # Record: `docs/reviews/m14-category-calibration.md`.
    #
    # `close_call` is the median rating gap between pairs whose PUBLISHED 95% intervals overlap --
    # the board's own statement of what it cannot tell apart -- measured on the owner's machine on
    # 2026-09-18 (the intervals are not stored in the artifact). This is a different rule from M8's
    # "2 x stderr, else the median adjacent gap", and it is stated as one. `value_window` is sized
    # by candidate count on the ranked population, which is M8's rule.
    "document": CategorySpec(
        id="document",
        title="Working with documents",
        primary_benchmark="Arena document",
        metric="elo",
        score_unit="Elo",
        secondary_benchmark=None,
        primary_source="arena_document",
        # 36 distinct models on the board, 29 ranked. Board third 1467.5 admits 10 of 29 (the
        # ranked-third rule, 1471.0, would also admit 10). A 35-Elo window admits 7.
        min_quality=1467.5,
        value_window=35.0,
        close_call=8.7,
        score_anchor=1467.5,  # pinned 2026-09-20 (D-143); moves only by owner ruling
    ),
    "factuality": CategorySpec(
        id="factuality",
        title="Getting facts right",
        primary_benchmark="Arena factuality",
        metric="elo",
        score_unit="Elo",
        secondary_benchmark=None,
        primary_source="arena_factuality",
        # 143 distinct models on the board, 59 ranked, the densest board in the product (median
        # neighbour gap 1.4 Elo). Board third 1450.6 admits 32 of 59; the ranked-third rule
        # (1460.7) would admit 20 -- the surface where W-094's open question actually bites. A
        # 20-Elo window admits 6.
        min_quality=1450.6,
        value_window=20.0,
        close_call=4.0,
        score_anchor=1450.6,  # pinned 2026-09-20 (D-143); moves only by owner ruling
    ),
}


def get_category(task: str) -> CategorySpec:
    """Lookup with a loud error listing valid tasks."""
    spec = CATEGORIES.get(task)
    if spec is None:
        msg = f"unknown task {task!r}; expected one of {sorted(CATEGORIES)}"
        raise ValueError(msg)
    return spec
