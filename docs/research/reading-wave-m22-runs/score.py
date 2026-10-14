"""The reading wave's scorer (#222, #237): counts only, never a question.

    python3 docs/research/reading-wave-m22-runs/score.py

A run row names the held-out question by its row in `reading_heldout_m22_questions.json`, so these runs
hold no question text. A search is right when it is read as a search, measured, and on a surface its
label allows; a question that is not a search is right when it is not read as one.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
SET = HERE.parents[2] / "scripts/router_probe/reading_heldout_m22_questions.json"
labels = [label for _, label in json.loads(SET.read_text(encoding="utf-8"))]


def right(row: dict, label: str) -> bool:
    if label == "NOT_A_SEARCH":
        return row["reading"] != "search"
    return row["reading"] == "search" and row["unmeasured"] == "false" and row["surface"] in label.split("|")


for name in ["before-wording-1", "before-wording-2", "after-wording-1", "after-wording-2", "review-wording-1",
             "review-wording-2", "before-model-1", "before-model-2"]:
    rows = json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
    searches = [r for r in rows if labels[r["row"]] != "NOT_A_SEARCH"]
    others = [r for r in rows if labels[r["row"]] == "NOT_A_SEARCH"]
    print(f"{name}: right {sum(right(r, labels[r['row']]) for r in rows)}/{len(rows)}"
          f" | searches {len(searches)}: right {sum(right(r, labels[r['row']]) for r in searches)},"
          f" not measured {sum(r['unmeasured'] == 'true' for r in searches)},"
          f" asked {sum(r['reading'] == 'unsure' for r in searches)}"
          f" | not a search {len(others)}: caught {sum(r['reading'] != 'search' for r in others)}")
