import json, sys
qs_path, *runs = sys.argv[1:]
qs = {x["q"]: x for x in json.load(open(qs_path))}
for path in runs:
    rows = json.load(open(path))
    nas = [r for r in rows if qs[r["q"]]["expected"] == "NOT_A_SEARCH" or qs[r["q"]].get("expected","").startswith("NOT_A_SEARCH") and "|" not in qs[r["q"]]["expected"]]
    gen = [r for r in rows if "NOT_A_SEARCH" not in qs[r["q"]]["expected"]]
    caught = sum(r["reading"] in ("notASearch", "unsure") for r in nas)
    noted = sum(r["reading"] == "notASearch" for r in nas)
    g_noted = [r["q"] for r in gen if r["reading"] == "notASearch"]
    g_asked = [r["q"] for r in gen if r["reading"] == "unsure"]
    print(f"{path.rsplit('/',1)[-1]}: NAS {len(nas)} caught {caught} (noted {noted}); genuine {len(gen)} noted {len(g_noted)} asked {len(g_asked)}")
    for q in g_noted: print("    noted:", q[:90])
    for q in g_asked: print("    asked:", q[:90])
