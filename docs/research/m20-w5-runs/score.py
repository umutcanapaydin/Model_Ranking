"""Scores the M20-W5 runs (#195) against the held-out set's labels: `python3 score.py RUNS_DIR SET`.
Rows whose question the set no longer holds (two dropped as duplicates of tuning questions) are skipped.
It prints counts only, never a question."""
import json, sys, collections
P = sys.argv[1]; Q = sys.argv[2]
labels = {r["q"]: r for r in json.load(open(Q))}
_load = json.load
def load(path):
    return [r for r in _load(open(path)) if r["q"] in labels]
def surface_ok(row, lab):
    want = lab["surface"].split("|")
    if want == ["none"]:
        return row["reading"] != "search"
    return row["reading"] == "search" and row["unmeasured"] == "false" and row["surface"] in want
def score(path):
    rows = load(path); ok = collections.Counter(); n = collections.Counter()
    for r in rows:
        lab = labels[r["q"]]
        for key in ("all", lab["lang"], "g" + lab["group"]):
            n[key] += 1; ok[key] += surface_ok(r, lab)
    return ok, n
for name in ["before-wording-1", "before-wording-2", "after-wording-1", "after-wording-2",
             "before-model-1", "before-model-2", "after-model-1", "after-model-2"]:
    ok, n = score(f"{P}/{name}.json")
    print(name, " ".join(f"{k}:{ok[k]}/{n[k]}" for k in ["all", "en", "tr"] + [f"g{i}" for i in range(1, 9)]))
rows = load(f"{P}/after-family.json")
lang_ok = dom_ok = lang_fp = dom_fp = lang_need = dom_need = 0
for r in rows:
    lab = labels[r["q"]]
    got_l = set(filter(None, r["language"].split(","))); got_d = set(filter(None, r["domain"].split(",")))
    want_l = set() if lab["language"] == "none" else {lab["language"]}
    want_d = set() if lab["domain"] == "none" else {lab["domain"]}
    lang_ok += got_l == want_l; dom_ok += got_d == want_d
    lang_fp += bool(got_l - want_l); dom_fp += bool(got_d - want_d)
    lang_need += bool(want_l); dom_need += bool(want_d)
print(f"refinements read from the words: language right {lang_ok}/{len(rows)} (needed on {lang_need}; a wrong one added on {lang_fp}); domain right {dom_ok}/{len(rows)} (needed on {dom_need}; a wrong one added on {dom_fp})")
fam = [r for r in rows if "top10" in r and r["reading"] == "search" and r["unmeasured"] == "false"]
multi = [r for r in fam if len(r["boards"].split(",")) > 1]
overlap = [len(set(r["top10"].split(",")) & set(r.get("primaryTop10", "").split(","))) for r in multi]
same1 = sum(r["top10"].split(",")[0] == r.get("primaryTop10", "").split(",")[0] for r in multi)
print(f"answered with a list: {len(fam)}/{len(rows)}; from more than one board: {len(multi)}; "
      f"top-10 shared with the primary board's own top 10: mean {sum(overlap)/max(1,len(overlap)):.1f}, min {min(overlap, default=0)}, max {max(overlap, default=0)}; same first model: {same1}/{len(multi)}")
sizes = collections.Counter(len(r["boards"].split(",")) for r in fam)
print("boards per list:", dict(sorted(sizes.items())))
ent = [(int(r["entries"]), int(r.get("primarySize", 0))) for r in multi]
print("models listed, combined vs primary (mean):", round(sum(a for a, _ in ent)/max(1,len(ent)),1), round(sum(b for _, b in ent)/max(1,len(ent)),1))
