#!/usr/bin/env python3
"""Derive a new surface's thresholds FROM the board, instead of writing them by hand.

    PYTHONPATH=src .venv/bin/python scripts/calibrate_board.py --config document --db advisor.db

**Why this is a script and not a paragraph in a review.** Every threshold in `CategorySpec` is
sized on the RANKED POPULATION — models that reconcile to the registry AND carry a price median —
and not on the board, because the engine can only recommend a model somebody can buy. Calibrating
against the board instead has produced wrong thresholds three times (W-037), each time in a
hand-written calculation nobody could re-run. This prints the same numbers from the same data every
time, and writes a JSON record beside them so a later reviewer can diff rather than recompute.

It writes NOTHING to the database. It fetches, reconciles in memory, and reports.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from pathlib import Path
from typing import Any

from app.clients.arena import ARENA_BOARDS, METRIC, ArenaClient, parse_arena
from app.workflows.categories import CategorySpec
from app.workflows.rank import ranked_population
from app.workflows.registry import canonicalize, resolve_effort


def provisional_spec(client: ArenaClient) -> CategorySpec:
    """A `CategorySpec` for a board that does not have one yet.

    `ranked_population` needs a spec to know which benchmark and metric it is counting. A new board
    has no spec — that is what this script exists to help write — so it gets a provisional one whose
    THRESHOLDS ARE PLACEHOLDERS and are never read: `category_ranking` orders by the primary
    benchmark and joins the price median, and touches none of the three numbers being derived.
    Spelling them as zero rather than as a guess keeps that visible.
    """
    return CategorySpec(
        id=f"provisional-{client.config}",
        title=f"(provisional) {client.benchmark}",
        primary_benchmark=client.benchmark,
        metric=METRIC,
        score_unit="Elo",
        secondary_benchmark=None,
        primary_source=client.name,
        min_quality=0.0,
        value_window=0.0,
        close_call=0.0,
    )


def threshold_candidates(ratings: list[float], overlap_gaps: list[float]) -> dict[str, float]:
    """CANDIDATES for the three numbers `CategorySpec` needs. Not an answer, and not a decision.

    **This function does not reproduce the shipped thresholds, and that is stated here rather than
    discovered later.** Run against today's artifact it returns a HIGHER floor than every one of the
    nine shipping surfaces — `assistant` 1450.9 against the shipped 1400, `coding` 75.8 against
    65.0. Two things differ and neither is settled by this file: the M8 review says the floor is the
    top third **of the board**, while `categories.py` says every threshold is sized on the **ranked
    population**, correcting itself on 2026-08-19 after W-037; and the populations have moved since
    the calibration snapshot in any case.

    So `--self-check` exists, and a new surface's numbers are not adopted from this script's output
    alone. Its job is to put the distribution and the candidates in front of whoever decides, from
    data rather than from memory, and to show its own disagreement with the shipped surfaces in the
    same breath. A calibration method that cannot reproduce the calibrations already in the product
    has not earned the right to set a new one.

    * `min_quality` — the Budget Pick floor, at the top third of the RANKED population. The
      `assistant` surface's 1400 is exactly this quantile on its own board.
    * `close_call` — the gap below which two models are not distinguishable. Taken from the board's
      OWN published 95% intervals: the median gap among pairs whose intervals still overlap. A
      threshold derived from the measurement's own uncertainty, rather than chosen.
    * `value_window` — Best Value's reach below the leader, at four times `close_call`, which is
      the ratio the shipped `assistant` surface uses (30 against 8).
    """
    ordered = sorted(ratings, reverse=True)
    third = ordered[min(len(ordered) - 1, max(0, round(len(ordered) / 3) - 1))]
    close = statistics.median(overlap_gaps) if overlap_gaps else 0.0
    return {
        "min_quality": round(third, 1),
        "close_call": round(close, 1),
        "value_window": round(close * 4, 1),
    }


def _display_of(conn: sqlite3.Connection, raw_name: str) -> str | None:
    """The display name the engine ranks this board row under, or None if it does not rank it."""
    rule = canonicalize(resolve_effort(raw_name).model_name)
    if rule is None:
        return None
    row = conn.execute("SELECT display FROM models WHERE id = ?", (rule.canonical_id,)).fetchone()
    return str(row[0]) if row else None


def _published_intervals(payload: dict[str, Any]) -> dict[str, tuple[float, float]]:
    """The board's own 95% intervals, keyed by the name the parser kept."""
    intervals: dict[str, tuple[float, float]] = {}
    for wrapper in payload.get("rows", []):
        record = wrapper.get("row") if isinstance(wrapper, dict) else None
        if not isinstance(record, dict):
            continue
        name, low, high = (
            record.get("model_name"),
            record.get("rating_lower"),
            record.get("rating_upper"),
        )
        if isinstance(name, str) and isinstance(low, int | float) and isinstance(high, int | float):
            intervals.setdefault(name, (float(low), float(high)))
    return intervals


def _overlapping_gaps(
    rankable: list[str], by_name: dict[str, float], intervals: dict[str, tuple[float, float]]
) -> list[float]:
    """Rating gaps between pairs whose published intervals still overlap."""
    gaps: list[float] = []
    for i, a in enumerate(rankable):
        for b in rankable[i + 1 :]:
            if a not in intervals or b not in intervals:
                continue
            (a_low, a_high), (b_low, b_high) = intervals[a], intervals[b]
            if a_low <= b_high and b_low <= a_high:
                gaps.append(abs(by_name[a] - by_name[b]))
    return gaps


def _self_check(db: str) -> int:
    """Hold the method against the surfaces already in the product, and print the disagreement."""
    from app.workflows.categories import CATEGORIES

    conn = sqlite3.connect(db)
    print(f"{'surface':16s} {'n':>4s} {'shipped':>10s} {'this method':>12s} {'diff':>8s}")
    for cid, spec in CATEGORIES.items():
        rows = ranked_population(conn, spec)
        if not rows:
            print(f"{cid:16s} {'-':>4s} {spec.min_quality:10.1f} {'no data':>12s}")
            continue
        mine = threshold_candidates([r.score for r in rows], [1.0])["min_quality"]
        print(
            f"{cid:16s} {len(rows):4d} {spec.min_quality:10.1f} {mine:12.1f} "
            f"{mine - spec.min_quality:+8.1f}"
        )
    print(
        "\nA non-zero diff column means this method is NOT the one that set the shipped numbers.\n"
        "Read `docs/reviews/m8-category-calibration.md` and its 2026-08-19 correction before\n"
        "adopting any candidate below."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="calibrate_board")
    parser.add_argument("--config", required=True, choices=sorted(ARENA_BOARDS))
    parser.add_argument("--db", default="advisor.db")
    parser.add_argument("--out", default=None, help="write the JSON record here")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="print this method's floor beside every SHIPPED surface's, and exit; no network",
    )
    args = parser.parse_args(argv)

    if args.self_check:
        return _self_check(args.db)

    client = ArenaClient(config=args.config)
    raw = client.fetch_raw()
    rows, skipped = parse_arena(
        raw, source=client.name, source_url=client.url, benchmark=client.benchmark
    )
    payload = json.loads(raw)

    intervals = _published_intervals(payload)
    by_name = {r.raw_name: r.score for r in rows}

    # **The engine's accessor, not a query of my own.** REQ-EVI-002 and the guard in
    # `test_ranked_population.py` exist because this question has been answered from whatever data
    # was nearest three times, and each answer was a wrong calibration. The rows must be in the
    # database first, so this is run AFTER a build that ingested the board.
    conn = sqlite3.connect(args.db)
    population = ranked_population(conn, provisional_spec(client))
    ranked_models = {row.model for row in population}
    ratings = [row.score for row in population]

    rankable = [n for n in by_name if _display_of(conn, n) in ranked_models]
    dropped = [n for n in by_name if n not in set(rankable)]

    gaps = _overlapping_gaps(rankable, by_name, intervals)

    # D-145: the floor the product SHIPS is the top third of the WHOLE board over distinct models
    # (each model's best rating), not of the ranked population. Printed so the shipped number is
    # reproduced by this script rather than asserted beside it (M14-W2 review M3).
    board_best: dict[str, float] = {}
    for row in rows:
        key = row.raw_name
        rule = canonicalize(resolve_effort(row.raw_name).model_name)
        if rule is not None:
            key = rule.canonical_id
        board_best[key] = max(board_best.get(key, row.score), row.score)
    board_ordered = sorted(board_best.values(), reverse=True)
    board_third = (
        board_ordered[max(0, round(len(board_ordered) / 3) - 1)] if board_ordered else None
    )

    record: dict[str, Any] = {
        "board_distinct_models": len(board_ordered),
        "board_third_D145": round(board_third, 1) if board_third is not None else None,
        "config": args.config,
        "source": client.name,
        "benchmark": client.benchmark,
        "board_rows": len(rows),
        "skipped": skipped,
        "ranked_population": len(rankable),
        "dropped": sorted(dropped),
        "overlapping_pairs": len(gaps),
        "rating_min": round(min(ratings), 1) if ratings else None,
        "rating_max": round(max(ratings), 1) if ratings else None,
        "threshold_candidates": threshold_candidates(ratings, gaps) if ratings else None,
    }

    print(json.dumps(record, indent=2, ensure_ascii=False))
    if args.out:
        with Path(args.out).open("w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, ensure_ascii=False)
        print(f"\nwritten: {args.out}", file=sys.stderr)
    if not ratings:
        print("\nNO RANKABLE MODEL — this board cannot define a surface today.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
