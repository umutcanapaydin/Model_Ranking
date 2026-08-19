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
        title="Everyday assistant / chat",
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
        title="Everyday questions",
        primary_benchmark="Epoch Capabilities Index",
        metric="ECI",
        score_unit="ECI",
        secondary_benchmark="MMLU",
        primary_source="epoch_eci",
        # 521 models, leader 161.7, median 144.6. A 3-point window leaves 42 candidates.
        min_quality=149.9,
        value_window=3.0,
        close_call=0.5,
    ),
    "expert": CategorySpec(
        id="expert",
        title="Expert reasoning",
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
        # same gap noise. 15 points leaves 77 candidates.
        min_quality=84.4,
        value_window=10.0,
        close_call=9.5,
    ),
    "computer-use": CategorySpec(
        id="computer-use",
        title="Computer use",
        primary_benchmark="TerminalBench",
        metric="% resolved",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_terminalbench",
        # STRUCTURALLY THIN, and the wide window is the honest consequence rather than a preference.
        # 59 models. The top six cluster between 78.4 and 84.7 and then drop to 69.9, so a 10-point
        # window admits six candidates at ANY floor from the 50th to the 75th percentile. 20 points
        # offers eleven. This surface will be saying "20 points below the leader" where coding says
        # "3.5 points below, and 84% cheaper" -- disclosed in the trade-off sentence, never hidden.
        min_quality=53.4,
        value_window=5.0,
        close_call=0.8,
    ),
    "abstract": CategorySpec(
        id="abstract",
        title="Abstract reasoning",
        primary_benchmark="ARC-AGI",
        metric="% correct",
        score_unit="points",
        secondary_benchmark=None,
        primary_source="epoch_arc_agi",
        # 168 models, leader 98.0. An 8-point window leaves 30 candidates.
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
        # The other thin surface, on a different scale and for the same structural reason. 102
        # models; the leader sits 30 Elo above second and the top twelve span 160, so a 30-Elo
        # window admits ONE candidate at every floor tested. 150 Elo offers nine. Elo thresholds
        # are NOT comparable to the percentage categories above -- that is what D-105 forbids.
        min_quality=1478.9,
        value_window=100.0,
        close_call=6.8,
    ),
}


def get_category(task: str) -> CategorySpec:
    """Lookup with a loud error listing valid tasks."""
    spec = CATEGORIES.get(task)
    if spec is None:
        msg = f"unknown task {task!r}; expected one of {sorted(CATEGORIES)}"
        raise ValueError(msg)
    return spec
