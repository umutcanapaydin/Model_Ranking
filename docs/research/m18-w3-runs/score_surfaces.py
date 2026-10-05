"""Score a surface-routing probe run against its set (M18-W3).

For each group: how many reached an accepted surface, and of those how many were answered directly
and how many only after the question back (`reading: unsure`, the second code review's B5). A run
from `RefinementProbe.swift` has no reading; its rows count as direct.

    python3 score_surfaces.py SET.json RUN.json [RUN.json ...]
"""

import json
import sys
from collections import defaultdict

qs_path, *runs = sys.argv[1:]
qs = {x["q"]: x for x in json.load(open(qs_path, encoding="utf-8"))}
for path in runs:
    rows = json.load(open(path, encoding="utf-8"))
    by = defaultdict(lambda: [0, 0, 0, 0])  # reached, of which asked first, noted, total
    for r in rows:
        meta = qs[r["q"]]
        group = meta.get("group", meta.get("class"))
        got = "UNMEASURED" if r["unmeasured"] == "true" else r["surface"]
        reading = r.get("reading", "search")
        b = by[group]
        b[3] += 1
        if reading == "notASearch":
            b[2] += 1
        elif got in meta["expected"].split("|"):
            b[0] += 1
            b[1] += reading == "unsure"
    print(path.rsplit("/", 1)[-1], " ".join(
        f"{g}={a}/{n}" + (f"(asked {k})" if k else "") + (f" noted {t}" if t else "")
        for g, (a, k, t, n) in sorted(by.items())))
