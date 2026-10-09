"""M21-W2's scorer (#66, #222): counts only, never a question."""
import collections, json, sys
P, Q = sys.argv[1], sys.argv[2]
labels = {r["q"]: r for r in json.load(open(Q))}
def rows(name):
    return [r for r in json.load(open(f"{P}/{name}.json")) if r["q"] in labels]
def right(r, lab):
    want = lab["surface"].split("|")
    if want == ["none"]:
        return r["reading"] != "search"
    return r["reading"] == "search" and r["unmeasured"] == "false" and r["surface"] in want
for name in ["before-wording-1", "before-wording-2", "after-wording-1", "after-wording-2",
             "before-model-1", "before-model-2", "after-model-1", "after-model-2"]:
    rs = rows(name); c = collections.Counter(); n = collections.Counter()
    for r in rs:
        lab = labels[r["q"]]
        for k in ("all", lab["lang"], "g" + lab["group"]):
            n[k] += 1; c[k] += right(r, lab)
    searches = [r for r in rs if labels[r["q"]]["surface"] != "none"]
    nons = [r for r in rs if labels[r["q"]]["surface"] == "none"]
    print(name, " ".join(f"{k}:{c[k]}/{n[k]}" for k in ["all", "en", "tr"] + [f"g{i}" for i in range(1, 9)]),
          f"| searches {len(searches)}: not-measured {sum(r['unmeasured'] == 'true' for r in searches)},"
          f" note {sum(r['reading'] == 'notASearch' for r in searches)}, asked {sum(r['reading'] == 'unsure' for r in searches)}"
          f" | non-searches {len(nons)}: note {sum(r['reading'] == 'notASearch' for r in nons)},"
          f" asked {sum(r['reading'] == 'unsure' for r in nons)}")
