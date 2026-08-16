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
}


def get_category(task: str) -> CategorySpec:
    """Lookup with a loud error listing valid tasks."""
    spec = CATEGORIES.get(task)
    if spec is None:
        msg = f"unknown task {task!r}; expected one of {sorted(CATEGORIES)}"
        raise ValueError(msg)
    return spec
