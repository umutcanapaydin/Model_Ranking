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
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from app.clients.epoch import EPOCH_ATTRIBUTION
from app.workflows.categories import CATEGORIES, CategorySpec
from app.workflows.schema import EFFORT_LEVELS

BLEND_INPUT_WEIGHT = 0.75
BLEND_OUTPUT_WEIGHT = 0.25
BLEND_NOTE = "blended $/1M = input*0.75 + output*0.25"
# REQ-ING-008 / D-101: attribution travels with every export.
# ATTRIBUTIONS is the CATALOGUE — every citation this project can owe. It is the right
# thing to print on a full export, which covers every source. It is the WRONG thing to
# print in a recommendation payload under a key named `sources` (W4 review BLOCKING-2):
# an `assistant` answer ranks purely on Arena Elo, and claiming SWE-bench, Aider and
# Epoch alongside it is a false provenance claim in a machine contract. Payloads build
# their list from the evidence they actually used, via `attributions_for`.
PRICING_ATTRIBUTION = (
    "Pricing data: BerriAI/litellm (MIT) and OpenRouter public model catalog (attribution required)"
)
ARENA_ATTRIBUTION = "Arena leaderboard data © LMArena — lmarena-ai/leaderboard-dataset (CC-BY-4.0)"
SWEBENCH_ATTRIBUTION = "Coding scores: swebench.com leaderboard (SWE-bench) and Aider polyglot leaderboard (Apache-2.0)"
ATTRIBUTIONS = (
    ARENA_ATTRIBUTION,
    PRICING_ATTRIBUTION,
    SWEBENCH_ATTRIBUTION,
    EPOCH_ATTRIBUTION,
)

# Which citation each `scores.source` value obliges. A source missing from this map is
# an unattributed source, which for a CC-BY feed is a licence breach — so it raises
# rather than silently dropping the obligation (fail loud, D-107 discipline).
SOURCE_ATTRIBUTION: dict[str, str] = {
    "arena": ARENA_ATTRIBUTION,
    "swebench": SWEBENCH_ATTRIBUTION,
    "aider": SWEBENCH_ATTRIBUTION,
    "epoch_swe_bench_verified": EPOCH_ATTRIBUTION,
    "epoch_deepswe_external": EPOCH_ATTRIBUTION,
}


def secondary_evidence_sources(conn: sqlite3.Connection, spec: CategorySpec) -> set[str]:
    """Sources that supplied the category's SECONDARY benchmark rows.

    M5 security review MINOR: a payload whose primary evidence is Epoch can still serve
    an Aider secondary score and grade its confidence "two independent benchmarks" —
    while citing only Epoch. The second benchmark is served data too, so it owes its
    citation.
    """
    if not spec.secondary_benchmark:
        return set()
    return {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT source FROM scores WHERE benchmark = ? AND model_id IS NOT NULL",
            (spec.secondary_benchmark,),
        )
    }


def attributions_for(evidence_sources: Iterable[str], *, priced: bool) -> tuple[str, ...]:
    """The citations a payload actually owes, in catalogue order.

    ``priced`` adds the pricing citation for payloads that rank on $/1M (the model
    engine). The subscription engine ranks on the curated plan table's monthly price
    and must not claim the per-token pricing feeds it never read.
    """
    owed = {PRICING_ATTRIBUTION} if priced else set()
    for source in evidence_sources:
        citation = SOURCE_ATTRIBUTION.get(source)
        if citation is None:
            msg = f"unattributed evidence source {source!r}; add it to SOURCE_ATTRIBUTION"
            raise ValueError(msg)
        owed.add(citation)
    return tuple(c for c in ATTRIBUTIONS if c in owed)


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
    evidence_source: str
    effort: str
    higher_effort: str | None
    higher_effort_score: float | None
    evidence_date: str | None
    secondary_score: float | None
    secondary_cost: float | None
    input_per_m: float
    output_per_m: float
    blended_per_m: float


def higher_effort_evidence(
    conn: sqlite3.Connection,
    model_id: str,
    spec: CategorySpec,
    *,
    harness: str,
    source: str,
) -> tuple[str | None, float | None]:
    """Higher-effort score for the selected model+harness+source evidence identity."""
    if spec.ranking_effort is None:
        return None, None
    try:
        current = EFFORT_LEVELS.index(spec.ranking_effort)
    except ValueError as exc:
        raise ValueError(f"unknown ranking effort {spec.ranking_effort!r}") from exc
    for effort in reversed(EFFORT_LEVELS[current + 1 :]):
        row = conn.execute(
            "SELECT MAX(score) FROM scores WHERE model_id = ? AND benchmark = ?"
            " AND metric = ? AND effort = ? AND harness = ? AND source = ?",
            (model_id, spec.primary_benchmark, spec.metric, effort, harness, source),
        ).fetchone()
        if row is not None and row[0] is not None:
            return effort, row[0]
    return None, None


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
          WHERE benchmark = :primary AND metric = :metric
            AND (:effort IS NULL OR effort = :effort) AND model_id IS NOT NULL
          GROUP BY model_id
        ),
        primary_detail AS (
          -- deterministic tie-break: newest run first, then harness name (M1-W3 MINOR-3)
          SELECT s.model_id, s.harness, s.source, s.raw_name, s.effort, s.run_date, s.score,
                 ROW_NUMBER() OVER (
                   PARTITION BY s.model_id
                   ORDER BY s.run_date DESC, s.harness ASC, s.source ASC, s.raw_name ASC
                 ) AS rn
          FROM scores s
          JOIN best_primary b ON b.model_id = s.model_id AND b.best = s.score
          WHERE s.benchmark = :primary AND s.metric = :metric
            AND (:effort IS NULL OR s.effort = :effort)
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
        SELECT m.id, m.display, m.vendor, b.best,
               (SELECT harness  FROM primary_detail d WHERE d.model_id = m.id AND d.rn = 1),
               (SELECT source   FROM primary_detail d WHERE d.model_id = m.id AND d.rn = 1),
               (SELECT effort   FROM primary_detail d WHERE d.model_id = m.id AND d.rn = 1),
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
        {
            "primary": spec.primary_benchmark,
            "metric": spec.metric,
            "secondary": secondary,
            "effort": spec.ranking_effort,
        },
    ).fetchall()
    ranking: list[RankingRow] = []
    for r in rows:
        higher_effort, higher_score = higher_effort_evidence(
            conn, r[0], spec, harness=r[4], source=r[5]
        )
        ranking.append(
            RankingRow(
                model=r[1],
                vendor=r[2],
                score=r[3],
                harness=r[4],
                evidence_source=r[5],
                effort=r[6],
                higher_effort=higher_effort,
                higher_effort_score=higher_score,
                evidence_date=r[7],
                secondary_score=r[8],
                secondary_cost=r[9],
                input_per_m=r[10],
                output_per_m=r[11],
                blended_per_m=round(r[10] * BLEND_INPUT_WEIGHT + r[11] * BLEND_OUTPUT_WEIGHT, 2),
            )
        )
    return ranking


def coding_ranking(conn: sqlite3.Connection) -> list[RankingRow]:
    """M1 API kept as a regression lock (REQ-REC-005): coding via the category layer."""
    return category_ranking(conn, CATEGORIES["coding"])


#: Metadata lines the export writes above the header (REQ-LIC-002). Read them with
#: `read_export_csv` rather than reinventing the skip at each call site — a reader that each
#: consumer writes for itself is the same hand-mirror class the /v1 serializer just removed.
EXPORT_COMMENT_PREFIX = "#"


def read_export_csv(path: Path) -> list[dict[str, str]]:
    """Read an exported ranking CSV, skipping the LEADING attribution/blend-note lines.

    Leading, not "any line starting with `#`". The first version filtered every such line in the
    file, so a model whose name begins with `#` would have lost its row silently — the file, the
    JSON half's row count and every existing assertion would all have stayed plausible. A reader
    that quietly drops data is worse than one that fails, and this was found by review rather than
    by any test, because nothing in the fixtures is named that way.

    Metadata only ever precedes the header, so the skip stops at the first non-comment line.
    """
    lines = path.read_text().splitlines()
    start = 0
    while start < len(lines) and lines[start].startswith(EXPORT_COMMENT_PREFIX):
        start += 1
    return list(csv.DictReader(lines[start:]))


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

    # D-109: comparison keeps raw precision; every score is rounded once here,
    # at the CSV/JSON boundary. Import locally to avoid the rank -> recommend ->
    # rank module cycle while retaining the single ratified rounding helpers.
    from app.workflows.recommend import round_optional_score, round_score

    dicts = []
    for row in ranking:
        item = asdict(row)
        item["score"] = round_score(row.score)
        item["secondary_score"] = round_optional_score(row.secondary_score)
        item["higher_effort_score"] = round_optional_score(row.higher_effort_score)
        dicts.append(item)
    # W4 review BLOCKING-2: an export cites the sources IT carries, not the catalogue.
    attribution = attributions_for({r.evidence_source for r in ranking}, priced=True)

    fields = list(RankingRow.__dataclass_fields__)
    with csv_path.open("w", newline="") as f:
        # REQ-LIC-002. M5's security review left this half unattributed: the JSON cited its sources
        # and the CSV of the SAME RUN cited nothing. A CC-BY obligation ships where the data is
        # served, and this is the file an analyst actually opens — "it is in the other file" is not
        # a licence position. Metadata rides as `#` comment lines ABOVE the header so a reader that
        # skips comments gets exactly the table it got before; the header is still the first
        # non-comment line.
        for line in (BLEND_NOTE, *attribution):
            f.write(f"# {line}\n")
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dicts)

    payload = {
        "note": BLEND_NOTE,
        "attribution": attribution,
        "generated_from": generated_from,
        "rows": dicts,
    }
    json_path.write_text(json.dumps(payload, indent=2))
    return csv_path, json_path
