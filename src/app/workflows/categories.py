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
    title_tr: str
    primary_benchmark: str
    metric: str  # metric name as stored in scores.metric
    score_unit: str  # human label for trade-off wording (REQ-REC-005)
    secondary_benchmark: str | None  # evidence-only; NEVER affects ordering (REQ-CAT-003)
    primary_source: str  # informational; health flags live on ingest reports (not persisted yet)
    # Engine thresholds on the category's NATIVE scale (M2-W4 review: data, not code branches):
    min_quality: float  # Budget Pick floor
    value_window: float  # Best Value: within N of the leader
    close_call: float  # near-tie disclosure threshold


CATEGORIES: dict[str, CategorySpec] = {
    "coding": CategorySpec(
        id="coding",
        title_tr="Kodlama",
        primary_benchmark="SWE-bench Verified",
        metric="% resolved",
        score_unit="puan",
        secondary_benchmark="Aider polyglot",
        primary_source="swebench",
        min_quality=65.0,
        value_window=6.0,
        close_call=1.5,
    ),
    "assistant": CategorySpec(
        id="assistant",
        title_tr="Günlük asistan / sohbet",
        primary_benchmark="Arena text",
        metric="elo",
        score_unit="Elo",
        secondary_benchmark=None,
        primary_source="arena",
        min_quality=1300.0,
        value_window=30.0,
        close_call=5.0,
    ),
}


def get_category(task: str) -> CategorySpec:
    """Lookup with a loud error listing valid tasks."""
    spec = CATEGORIES.get(task)
    if spec is None:
        msg = f"unknown task {task!r}; expected one of {sorted(CATEGORIES)}"
        raise ValueError(msg)
    return spec
