#!/usr/bin/env python3
"""Recompute every figure in docs/reviews/m3-elo-calibration.md (REQ-CAL-001, REQ-EVI-002).

Usage:  python3 scripts/arena_calibration.py <dir with arena_overall_*.json>
                                             [--db PATH] [--category assistant]

**Two populations, and confusing them is W-037.** The board describes arena's MEASUREMENT: how
many models it rates, how wide their intervals are, how often two adjacent ratings are
indistinguishable. Those figures are properties of the board and are computed from the JSON
regardless of what this project can serve.

A THRESHOLD is not a property of the board. `min_quality` and `value_window` describe the
population the engine can actually recommend — reconciled to the registry AND priced — which on
ECI was 58 models where the board had 521. Sizing a window against the board admits models that
are not in it. This script has therefore been split: the threshold sections REFUSE to run without
`--db`, and when given one they read `app.workflows.rank.ranked_population`, which is the name
REQ-EVI-002 exists to give that population. They do not re-derive it here — a second definition of
the ranked population is the defect, not the fix.

The JSON pages come from the documented HF datasets-server /filter endpoint (see
the record for the exact curl). This script exists because a calibration whose
numbers cannot be recomputed is an assertion, not evidence — the M3 closure
review had to reimplement it from scratch to check the record.

Conventions (they change the published figures — state them, never imply them):
  * percentiles: Weibull / R type-6 == statistics.quantiles(..., exclusive)
  * overlap buckets: floor-bucketed by rating gap, width 2, labelled by the floor
  * two ratings "overlap" when their 95% CIs intersect (lower_i <= upper_j and
    lower_j <= upper_i)
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

from app.workflows.categories import get_category
from app.workflows.rank import ranked_population
from app.workflows.schema import open_readonly

CUTS = (1500, 1450, 1425, 1400, 1350, 1300)
TOP_N_PAIRS = 60


def load(directory: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(Path(directory).glob("arena_overall_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "rows" not in payload:
            print(f"!! {path}: no rows (payload={str(payload)[:80]})")
            continue
        print(f"   {Path(path).name}: num_rows_total={payload.get('num_rows_total')}")
        rows.extend(r["row"] for r in payload["rows"])
    return rows


def ranked_ratings(db: str, category: str) -> list[float]:
    """The scores the engine can actually recommend on this surface, newest-first.

    One call, and deliberately no query of its own. REQ-EVI-002 is not "restrict the board
    somewhere"; it is "there is ONE definition and callers use it". A copy of the join here would
    satisfy the sentence and reproduce the bug the sentence was written about.
    """
    conn = open_readonly(db)
    try:
        rows = ranked_population(conn, get_category(category))
    finally:
        conn.close()
    return sorted((row.score for row in rows), reverse=True)


def _thresholds_refused(board_n: int) -> None:
    """The blind surface says so (D-121). It does not fall back to the board."""
    print("\n" + "=" * 72)
    print("THRESHOLD SECTIONS REFUSED — no --db given.")
    print(
        f"  The cut table and the value_window sizing describe the population this engine\n"
        f"  RANKS, not the {board_n} rows arena publishes. Computing them from the board is\n"
        f"  W-037, three times over. Re-run with:\n"
        f"    --db advisor.db [--category assistant]"
    )
    print("=" * 72)


def parse_args(argv: list[str]) -> tuple[str, str | None, str] | None:
    """`<dir> [--db PATH] [--category ID]`. Returns None when the usage is wrong."""
    args = list(argv[1:])
    options = {"--db": None, "--category": "assistant"}
    for flag in ("--db", "--category"):
        if flag not in args:
            continue
        index = args.index(flag)
        if index + 1 >= len(args):
            print(f"{flag} needs a value")
            return None
        options[flag] = args[index + 1]
        del args[index : index + 2]
    if len(args) != 1:
        print(__doc__)
        return None
    return args[0], options["--db"], str(options["--category"])


def report_board(rows: list[dict]) -> None:
    """Arena's MEASUREMENT. Every figure here is a property of the board and says so."""
    ratings = sorted((r["rating"] for r in rows), reverse=True)
    print(f"\nBOARD n={len(rows)}  max={ratings[0]:.1f}  min={ratings[-1]:.1f}  median={st.median(ratings):.1f}")
    print(f"publish dates: {sorted({r.get('leaderboard_publish_date') for r in rows})}")
    q = st.quantiles(ratings, n=100)  # Weibull / R type-6
    print(f"p75={q[74]:.1f}  p90={q[89]:.1f}  p95={q[94]:.1f}   (BOARD, not the ranked population)")

    widths = [r["rating_upper"] - r["rating_lower"] for r in rows]
    top = sorted(rows, key=lambda r: -r["rating"])[:30]
    print(
        f"95% CI width: median(all)={st.median(widths):.1f}  "
        f"median(top30)={st.median(r['rating_upper'] - r['rating_lower'] for r in top):.1f}"
    )

    print(f"\nCI-overlap by rating gap (all pairs in the top {TOP_N_PAIRS}):")
    pool = sorted(rows, key=lambda r: -r["rating"])[:TOP_N_PAIRS]
    buckets: dict[int, list[int]] = {}
    for i, a in enumerate(pool):
        for b in pool[i + 1 :]:
            gap = a["rating"] - b["rating"]
            key = int(gap // 2) * 2
            hit = buckets.setdefault(key, [0, 0])
            hit[1] += 1
            if a["rating_lower"] <= b["rating_upper"] and b["rating_lower"] <= a["rating_upper"]:
                hit[0] += 1
    for key in sorted(buckets):
        overlapping, total = buckets[key]
        if total >= 8 and key <= 14:
            print(f"  gap {key:2d}-{key + 1}: {overlapping / total * 100:5.1f}% overlap  (n={total})")


def main(argv: list[str]) -> int:
    parsed = parse_args(argv)
    if parsed is None:
        return 2
    directory, db, category = parsed
    rows = load(directory)
    if not rows:
        print("no rows parsed — check the fetch (config=text, not default)")
        return 2
    report_board(rows)

    # --- the THRESHOLDS: a property of what this engine can serve (REQ-EVI-002) ---------------
    if db is None:
        _thresholds_refused(len(rows))
        return 0

    served = ranked_ratings(db, category)
    if not served:
        print(f"\nranked population for '{category}' is EMPTY — nothing to calibrate against.")
        return 2
    dropped = len(rows) - len(served)
    print(
        f"\nRANKED POPULATION ({category}): n={len(served)}  "
        f"max={served[0]:.1f}  min={served[-1]:.1f}  median={st.median(served):.1f}"
    )
    print(f"  the board carries {len(rows)}; {dropped} of them are unreconciled or unpriced")

    leader = served[0]
    print("\ncut   models  share  leader-cut   (ranked population)")
    for cut in CUTS:
        n = sum(1 for x in served if x >= cut)
        print(f"{cut}  {n:5d}  {n / len(served) * 100:4.0f}%  {leader - cut:9.0f}")

    print("\nwithin-N-of-leader (value_window sizing, ranked population):")
    for window in (15, 20, 25, 30, 40, 50):
        print(f"  {window:2d}: {sum(1 for x in served if leader - x <= window):3d} models")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
