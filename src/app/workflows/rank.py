"""Coding ranking + median prices + export (REQ-CAN-003, REQ-RANK-001/-002).

Reference price per canonical model is the MEDIAN across its alias/provider
prices — never the minimum, so an outlier cheap variant cannot become the
model's price (REQ-CAN-003, spike lesson). Blended price = input*0.75 +
output*0.25 $/1M tokens (documented in every export).
"""

from __future__ import annotations

import csv
import json
import sqlite3
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

from app.workflows.categories import CATEGORIES, CategorySpec

BLEND_INPUT_WEIGHT = 0.75
BLEND_OUTPUT_WEIGHT = 0.25
BLEND_NOTE = "blended $/1M = input*0.75 + output*0.25"
# REQ-ING-008 / D-101: attribution travels with every export
ATTRIBUTIONS = (
    "Arena leaderboard data © LMArena — lmarena-ai/leaderboard-dataset (CC-BY-4.0)",
    "Pricing data: BerriAI/litellm (MIT) and OpenRouter public model catalog (attribution required)",
    "Coding scores: swebench.com leaderboard (SWE-bench) and Aider polyglot leaderboard (Apache-2.0)",
)


@dataclass(frozen=True)
class RankingRow:
    """One line of a category ranking (REQ-RANK-001, generalized in M2 REQ-CAT-002).

    ``score`` is ALWAYS on the category's primary-benchmark scale (REQ-CAT-003);
    ``secondary_*`` is evidence-only and never affects ordering.
    """

    model: str
    vendor: str
    score: float
    harness: str
    evidence_date: str | None
    secondary_score: float | None
    secondary_cost: float | None
    input_per_m: float
    output_per_m: float
    blended_per_m: float


def build_price_medians(conn: sqlite3.Connection) -> int:
    """Reference price per canonical model (REQ-CAN-003 + REQ-ING-006).

    Two stages so no source outweighs another by alias count: median WITHIN
    each (model, source) first, then median ACROSS the per-source medians.
    """
    per_source: dict[tuple[str, str], tuple[list[float], list[float]]] = {}
    for mid, src, i, o in conn.execute(
        "SELECT model_id, source, input_per_m, output_per_m FROM pricing"
        " WHERE model_id IS NOT NULL"
    ):
        ins, outs = per_source.setdefault((mid, src), ([], []))
        ins.append(i)
        outs.append(o)
    by_model: dict[str, tuple[list[float], list[float]]] = {}
    for (mid, _src), (ins, outs) in per_source.items():
        m_ins, m_outs = by_model.setdefault(mid, ([], []))
        m_ins.append(statistics.median(ins))
        m_outs.append(statistics.median(outs))
    with conn:
        conn.execute("DELETE FROM px_median")
        conn.executemany(
            "INSERT INTO px_median (model_id, in_m, out_m) VALUES (?,?,?)",
            [
                (mid, round(statistics.median(ins), 3), round(statistics.median(outs), 3))
                for mid, (ins, outs) in by_model.items()
            ],
        )
    return len(by_model)


def category_ranking(conn: sqlite3.Connection, spec: CategorySpec) -> list[RankingRow]:
    """Best primary-benchmark score per model + median prices (REQ-CAT-002).

    Ordering uses ONLY the primary benchmark (REQ-CAT-003); the category's
    secondary benchmark (if any) joins as display evidence.
    """
    secondary = spec.secondary_benchmark or "__none__"
    rows = conn.execute(
        """
        WITH best_primary AS (
          SELECT model_id, MAX(score) AS best FROM scores
          WHERE benchmark = :primary AND model_id IS NOT NULL
          GROUP BY model_id
        ),
        primary_detail AS (
          -- deterministic tie-break: newest run first, then harness name (M1-W3 MINOR-3)
          SELECT s.model_id, s.harness, s.run_date, s.score,
                 ROW_NUMBER() OVER (
                   PARTITION BY s.model_id
                   ORDER BY s.run_date DESC, s.harness ASC
                 ) AS rn
          FROM scores s
          JOIN best_primary b ON b.model_id = s.model_id AND b.best = s.score
          WHERE s.benchmark = :primary
        ),
        best_secondary AS (
          SELECT model_id, MAX(score) AS sec FROM scores
          WHERE benchmark = :secondary AND model_id IS NOT NULL
          GROUP BY model_id
        ),
        secondary_cost AS (
          SELECT s.model_id, s.cost_total,
                 ROW_NUMBER() OVER (
                   PARTITION BY s.model_id ORDER BY s.run_date DESC, s.harness ASC
                 ) AS rn
          FROM scores s
          JOIN best_secondary a ON a.model_id = s.model_id AND a.sec = s.score
          WHERE s.benchmark = :secondary
        )
        SELECT m.display, m.vendor, b.best,
               (SELECT harness  FROM primary_detail d WHERE d.model_id = m.id AND d.rn = 1),
               (SELECT run_date FROM primary_detail d WHERE d.model_id = m.id AND d.rn = 1),
               a.sec,
               (SELECT cost_total FROM secondary_cost c WHERE c.model_id = m.id AND c.rn = 1),
               p.in_m, p.out_m
        FROM models m
        JOIN best_primary b ON b.model_id = m.id
        JOIN px_median p ON p.model_id = m.id
        LEFT JOIN best_secondary a ON a.model_id = m.id
        ORDER BY b.best DESC, m.display
        """,
        {"primary": spec.primary_benchmark, "secondary": secondary},
    ).fetchall()
    return [
        RankingRow(
            model=r[0],
            vendor=r[1],
            score=r[2],
            harness=r[3],
            evidence_date=r[4],
            secondary_score=r[5],
            secondary_cost=r[6],
            input_per_m=r[7],
            output_per_m=r[8],
            blended_per_m=round(r[7] * BLEND_INPUT_WEIGHT + r[8] * BLEND_OUTPUT_WEIGHT, 2),
        )
        for r in rows
    ]


def coding_ranking(conn: sqlite3.Connection) -> list[RankingRow]:
    """M1 API kept as a regression lock (REQ-REC-005): coding via the category layer."""
    return category_ranking(conn, CATEGORIES["coding"])


def export_ranking(
    ranking: list[RankingRow],
    out_dir: Path,
    generated_from: list[dict[str, str | int | None]],
    category: str = "coding",
) -> tuple[Path, Path]:
    """Write identical CSV + JSON artifacts with dataset metadata (REQ-RANK-002).

    Filenames derive from the category (M2-W3 review: assistant export must not
    overwrite the coding artifact).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{category}_ranking.csv"
    json_path = out_dir / f"{category}_ranking.json"

    dicts = [asdict(r) for r in ranking]
    fields = list(RankingRow.__dataclass_fields__)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dicts)

    payload = {
        "note": BLEND_NOTE,
        "attribution": ATTRIBUTIONS,
        "generated_from": generated_from,
        "rows": dicts,
    }
    json_path.write_text(json.dumps(payload, indent=2))
    return csv_path, json_path
