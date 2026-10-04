import json, sys
from collections import defaultdict
qs_path, *runs = sys.argv[1:]
qs = {x["q"]: x for x in json.load(open(qs_path))}
for path in runs:
    rows = json.load(open(path))
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        meta = qs[r["q"]]
        accepted = meta["expected"].split("|")
        got = "UNMEASURED" if r["unmeasured"] == "true" else r["surface"]
        by[meta.get("group", meta.get("class"))][1] += 1
        by[meta.get("group", meta.get("class"))][0] += got in accepted
    print(path.rsplit("/", 1)[-1], " ".join(f"{g}={a}/{n}" for g, (a, n) in sorted(by.items())))
