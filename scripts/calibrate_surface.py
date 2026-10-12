#!/usr/bin/env python3
"""Derive a surface's thresholds from the board the build already holds (D-194 clause 4, #265).

    PYTHONPATH=src .venv/bin/python scripts/calibrate_surface.py --surface computer-use --db ARTIFACT \\
        --stderr 1.648 --stderr-from "TB 4.0's accuracy_ci95_half_width / 1.96, median of 21 submissions" \\
        --out docs/research/d194-computer-use-calibration.json

`scripts/calibrate_board.py` reads Arena's boards only. A surface moved to a licensed board (D-194) is sized
on the RANKED POPULATION the artifact holds for it (`rank.ranked_population`: models that reconcile and
carry a price), under M8's two rules (`docs/reviews/m8-category-calibration.md`):

- `close_call` is measurement: twice the board's own standard error, which the caller states and names.
- `value_window` is sized by candidates. Its edge sits at the middle of the first gap below the leader
  that is wider than `close_call` and leaves at least `MIN_CANDIDATES` models within reach, so the window
  never splits two models the board cannot tell apart. With no such gap it reaches the floor.

It writes NOTHING to the database: the artifact is opened read-only (INV-23).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.workflows.categories import CATEGORIES
from app.workflows.floors import derived_floor
from app.workflows.rank import ranked_population
from app.workflows.schema import open_readonly

#: Fewer than three models within reach makes Best Value into Best Quality (M8).
MIN_CANDIDATES = 3


def _half(value: float) -> float:
    return round(value * 2) / 2


def thresholds(scores: list[float], *, floor: float, stderr: float) -> dict[str, Any]:
    """The pair for a board whose models above ``floor`` score ``scores``, and the candidates it leaves."""
    if not stderr > 0:
        msg = f"a standard error must be positive, got {stderr}"
        raise ValueError(msg)
    close_call = round(2 * stderr, 1)
    above = sorted((s for s in scores if s >= floor), reverse=True)
    if not above:
        msg = "no model scores at or above the floor"
        raise ValueError(msg)
    lead = above[0]
    for i in range(MIN_CANDIDATES, len(above)):
        if above[i - 1] - above[i] > close_call:
            window = _half(((lead - above[i - 1]) + (lead - above[i])) / 2)
            return {"close_call": close_call, "value_window": window, "candidates": i}
    return {"close_call": close_call, "value_window": _half(lead - floor), "candidates": len(above)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="calibrate_surface")
    parser.add_argument("--surface", required=True, choices=sorted(CATEGORIES))
    parser.add_argument("--db", required=True, help="a built artifact holding the surface's board")
    parser.add_argument("--stderr", required=True, type=float, help="the board's own standard error")
    parser.add_argument("--stderr-from", required=True, help="where the standard error was measured")
    parser.add_argument("--out", default=None, help="write the JSON record here")
    args = parser.parse_args(argv)

    spec = CATEGORIES[args.surface]
    conn = open_readonly(Path(args.db))
    rows = ranked_population(conn, spec)
    floor = derived_floor(conn, spec)
    if not rows or floor is None:
        print(f"{args.surface}: the artifact holds no ranked population for {spec.primary_source}", file=sys.stderr)
        return 2
    picked = thresholds([r.score for r in rows], floor=floor, stderr=args.stderr)
    record = {
        "surface": args.surface,
        "source": spec.primary_source,
        "benchmark": spec.primary_benchmark,
        "ranked_population": len(rows),
        "floor": floor,
        "above_floor": [[r.model, r.score] for r in sorted(rows, key=lambda r: -r.score) if r.score >= floor],
        "stderr": args.stderr,
        "stderr_from": args.stderr_from,
        "rule": "close_call = 2 x stderr; value_window ends mid-gap in the first gap wider than close_call "
                f"past {MIN_CANDIDATES} candidates, else at the floor (D-194 clause 4)",
        **picked,
    }
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
