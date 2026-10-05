"""Score a reading probe run against its set (M18-W3): not-a-search inputs caught, genuine searches
noted or asked, and on whose word each ask came (the run's `model` field is the model's own verdict).

    python3 score_reading.py SET.json RUN.json [RUN.json ...] [--show]

It prints no question unless `--show` is given: a held-out set is read only through its counts until
it has been measured (D-147 clause 5).
"""

import json, sys
show = "--show" in sys.argv
qs_path, *runs = [a for a in sys.argv[1:] if a != "--show"]
qs = {x["q"]: x for x in json.load(open(qs_path))}
for path in runs:
    rows = json.load(open(path))
    nas = [r for r in rows if qs[r["q"]]["expected"] == "NOT_A_SEARCH" or qs[r["q"]].get("expected","").startswith("NOT_A_SEARCH") and "|" not in qs[r["q"]]["expected"]]
    gen = [r for r in rows if "NOT_A_SEARCH" not in qs[r["q"]]["expected"]]
    caught = sum(r["reading"] in ("notASearch", "unsure") for r in nas)
    noted = sum(r["reading"] == "notASearch" for r in nas)
    g_noted = [r["q"] for r in gen if r["reading"] == "notASearch"]
    g_asked = [r["q"] for r in gen if r["reading"] == "unsure"]
    model_asks = sum(r["reading"] == "unsure" and r.get("model") == "not" for r in nas)
    code_asks = sum(r["reading"] == "unsure" and r.get("model") == "search" for r in nas)
    g_model = sum(r.get("model") == "not" for r in gen if r["reading"] == "unsure")
    print(f"{path.rsplit('/',1)[-1]}: NAS {len(nas)} caught {caught} (noted {noted}, asked on the model's"
          f" word {model_asks}, on the code's {code_asks}); genuine {len(gen)} noted {len(g_noted)}"
          f" asked {len(g_asked)} (on the model's word {g_model})")
    if show:
        for q in g_noted: print("    noted:", q[:90])
        for q in g_asked: print("    asked:", q[:90])
