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

BLEND_INPUT_WEIGHT = 0.75
BLEND_OUTPUT_WEIGHT = 0.25
BLEND_NOTE = "blended $/1M = input*0.75 + output*0.25"


@dataclass(frozen=True)
class RankingRow:
    """One line of the coding ranking (REQ-RANK-001)."""

    model: str
    vendor: str
    swebench_verified_pct: float
    swe_harness: str
    swe_date: str | None
    aider_polyglot_pct: float | None
    aider_run_cost_usd: float | None
    input_per_m: float
    output_per_m: float
    blended_per_m: float


def build_price_medians(conn: sqlite3.Connection) -> int:
    """Median input/output price per canonical model (REQ-CAN-003)."""
    by_model: dict[str, tuple[list[float], list[float]]] = {}
    for mid, i, o in conn.execute(
        "SELECT model_id, input_per_m, output_per_m FROM pricing WHERE model_id IS NOT NULL"
    ):
        ins, outs = by_model.setdefault(mid, ([], []))
        ins.append(i)
        outs.append(o)
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


def coding_ranking(conn: sqlite3.Connection) -> list[RankingRow]:
    """Best SWE-bench Verified score per model + Aider + median prices (REQ-RANK-001)."""
    rows = conn.execute("""
        WITH best_swe AS (
          SELECT model_id, MAX(score) AS swe FROM scores
          WHERE benchmark = 'SWE-bench Verified' AND model_id IS NOT NULL
          GROUP BY model_id
        ),
        swe_detail AS (
          -- deterministic tie-break: newest run first, then harness name (W3 review MINOR-3)
          SELECT s.model_id, s.harness, s.run_date, s.score,
                 ROW_NUMBER() OVER (
                   PARTITION BY s.model_id
                   ORDER BY s.run_date DESC, s.harness ASC
                 ) AS rn
          FROM scores s
          JOIN best_swe b ON b.model_id = s.model_id AND b.swe = s.score
          WHERE s.benchmark = 'SWE-bench Verified'
        ),
        best_aider AS (
          SELECT model_id, MAX(score) AS aider FROM scores
          WHERE benchmark = 'Aider polyglot' AND model_id IS NOT NULL
          GROUP BY model_id
        ),
        aider_cost AS (
          SELECT s.model_id, s.cost_total,
                 ROW_NUMBER() OVER (
                   PARTITION BY s.model_id ORDER BY s.run_date DESC, s.harness ASC
                 ) AS rn
          FROM scores s
          JOIN best_aider a ON a.model_id = s.model_id AND a.aider = s.score
          WHERE s.benchmark = 'Aider polyglot'
        )
        SELECT m.display, m.vendor, b.swe,
               (SELECT harness  FROM swe_detail d WHERE d.model_id = m.id AND d.rn = 1),
               (SELECT run_date FROM swe_detail d WHERE d.model_id = m.id AND d.rn = 1),
               a.aider,
               (SELECT cost_total FROM aider_cost c WHERE c.model_id = m.id AND c.rn = 1),
               p.in_m, p.out_m
        FROM models m
        JOIN best_swe b ON b.model_id = m.id
        JOIN px_median p ON p.model_id = m.id
        LEFT JOIN best_aider a ON a.model_id = m.id
        ORDER BY b.swe DESC, m.display
        """).fetchall()
    return [
        RankingRow(
            model=r[0],
            vendor=r[1],
            swebench_verified_pct=r[2],
            swe_harness=r[3],
            swe_date=r[4],
            aider_polyglot_pct=r[5],
            aider_run_cost_usd=r[6],
            input_per_m=r[7],
            output_per_m=r[8],
            blended_per_m=round(r[7] * BLEND_INPUT_WEIGHT + r[8] * BLEND_OUTPUT_WEIGHT, 2),
        )
        for r in rows
    ]


def export_ranking(
    ranking: list[RankingRow], out_dir: Path, generated_from: list[dict[str, str | int | None]]
) -> tuple[Path, Path]:
    """Write identical CSV + JSON artifacts with dataset metadata (REQ-RANK-002)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "coding_ranking.csv"
    json_path = out_dir / "coding_ranking.json"

    dicts = [asdict(r) for r in ranking]
    fields = list(RankingRow.__dataclass_fields__)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dicts)

    payload = {
        "note": BLEND_NOTE,
        "generated_from": generated_from,
        "rows": dicts,
    }
    json_path.write_text(json.dumps(payload, indent=2))
    return csv_path, json_path
