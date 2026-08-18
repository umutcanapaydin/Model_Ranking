#!/usr/bin/env python3
"""Recompute every figure in docs/reviews/m3-elo-calibration.md (REQ-CAL-001).

Usage:  python3 scripts/arena_calibration.py <dir with arena_overall_*.json>

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


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    rows = load(argv[1])
    if not rows:
        print("no rows parsed — check the fetch (config=text, not default)")
        return 2

    ratings = sorted((r["rating"] for r in rows), reverse=True)
    leader = ratings[0]
    print(f"\nn={len(rows)}  max={leader:.1f}  min={ratings[-1]:.1f}  median={st.median(ratings):.1f}")
    print(f"publish dates: {sorted({r.get('leaderboard_publish_date') for r in rows})}")
    q = st.quantiles(ratings, n=100)  # Weibull / R type-6
    print(f"p75={q[74]:.1f}  p90={q[89]:.1f}  p95={q[94]:.1f}")

    widths = [r["rating_upper"] - r["rating_lower"] for r in rows]
    top = sorted(rows, key=lambda r: -r["rating"])[:30]
    print(
        f"95% CI width: median(all)={st.median(widths):.1f}  "
        f"median(top30)={st.median(r['rating_upper'] - r['rating_lower'] for r in top):.1f}"
    )

    print("\ncut   models  share  leader-cut")
    for cut in CUTS:
        n = sum(1 for x in ratings if x >= cut)
        print(f"{cut}  {n:5d}  {n / len(ratings) * 100:4.0f}%  {leader - cut:9.0f}")

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

    print("\nwithin-N-of-leader (value_window sizing):")
    for window in (15, 20, 25, 30, 40, 50):
        print(f"  {window:2d}: {sum(1 for x in ratings if leader - x <= window):3d} models")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
