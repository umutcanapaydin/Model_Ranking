"""Score a reading probe run against its set, on M19-W4's measures (docs/plans/m19-wave-4-plan.md).

    python3 score_w4.py SET.json RUN.json [RUN.json ...] [--show]

A set's rows carry `class` (or, in the older sets, `group`): knowledge, injection, chitchat,
do_task, genuine and ambiguous on a reading set (`nas` is a tuning row of any not-a-search class);
image-make, image-read and image-other on an image set. Counts only: `--show` lists the
misses, and is refused on a held-out set, which the author reads only after its last measure
(D-147 clause 5).
"""

import json
import math
import sys
from collections import Counter

NOT_A_SEARCH = ("knowledge", "injection", "chitchat", "do_task", "nas")


def got(row: dict) -> str:
    return "UNMEASURED" if row["unmeasured"] == "true" else row["surface"]


def reading_measures(qs: dict, rows: list) -> dict:
    by = {c: [r for r in rows if qs[r["q"]]["class"] == c] for c in (*NOT_A_SEARCH, "genuine", "ambiguous")}
    nas = [r for c in NOT_A_SEARCH for r in by[c]]
    caught = lambda rs: sum(r["reading"] in ("notASearch", "unsure") for r in rs)  # noqa: E731
    gen = by["genuine"]
    return {
        "not a search caught": (caught(nas), len(nas)),
        "knowledge caught": (caught(by["knowledge"]), len(by["knowledge"])),
        "genuine given the note": (sum(r["reading"] == "notASearch" for r in gen), len(gen)),
        "genuine asked": (sum(r["reading"] == "unsure" for r in gen), len(gen)),
        "genuine on their surface": (sum(r["reading"] != "notASearch"
                                         and got(r) in qs[r["q"]]["expected"].split("|") for r in gen), len(gen)),
        **{f"  {c} noted / asked": (f"{sum(r['reading'] == 'notASearch' for r in by[c])} / "
                                     f"{sum(r['reading'] == 'unsure' for r in by[c])}", len(by[c]))
           for c in (*NOT_A_SEARCH, "ambiguous")},
        "  asked on the model's word alone (all rows)": (sum(r["reading"] == "unsure" and r.get("model") == "not"
                                                             for r in rows), len(rows)),
    }


def image_measures(qs: dict, rows: list) -> dict:
    make = [r for r in rows if qs[r["q"]]["class"] == "image-make"]
    read = [r for r in rows if qs[r["q"]]["class"] == "image-read"]
    other = [r for r in rows if qs[r["q"]]["class"] == "image-other"]
    told = [r for r in make if r["unmeasured"] == "true" and r["reading"] != "notASearch"]
    missed = Counter(r["routed"] for r in make if r not in told and r["reading"] != "notASearch")
    reached = [r for r in read if r["reading"] != "notASearch" and got(r) == "vision"]
    return {
        "make told not measured": (len(told), len(make)),
        "  of those, by the tier's own decline": (sum(r.get("declined") == "true" for r in told), len(told)),
        "  make given the note": (sum(r["reading"] == "notASearch" for r in make), len(make)),
        "  make missed, by the tier's surface": (dict(sorted(missed.items())), len(make)),
        "read reaching vision": (len(reached), len(read)),
        "  of those, only after the question back": (sum(r["reading"] == "unsure" for r in reached), len(reached)),
        "other overridden to not measured": (sum(r["unmeasured"] == "true" and r.get("declined") == "false"
                                                 for r in other), len(other)),
        "other on their surface": (sum(r["reading"] != "notASearch" and got(r) in qs[r["q"]]["expected"].split("|")
                                       for r in other), len(other)),
    }


def bar_for_gain(baseline_low: int, total: int) -> int:
    """The plan's rule for a measure the wave aims to improve: the baseline (its lower run) plus two
    thirds of the gap to all, rounded up."""
    return baseline_low + math.ceil(2 * (total - baseline_low) / 3)


def main(argv: list[str]) -> int:
    show = "--show" in argv
    set_path, *runs = [a for a in argv if a != "--show"]
    if show and "heldout_m19" in set_path:
        print("refused: --show on a held-out set the wave has not finished measuring")
        return 2
    qs = {x["q"]: {**x, "class": x.get("class", x.get("group"))} for x in json.load(open(set_path, encoding="utf-8"))}
    image = any(x["class"].startswith("image-") for x in qs.values())
    for path in runs:
        rows = json.load(open(path, encoding="utf-8"))
        assert {r["q"] for r in rows} == set(qs), f"{path} does not answer {set_path} row for row"
        print(path.rsplit("/", 1)[-1])
        for name, (count, total) in (image_measures if image else reading_measures)(qs, rows).items():
            print(f"  {name}: {count} of {total}")
        if show:
            for r in rows:
                meta = qs[r["q"]]
                wrong = (meta["class"] in NOT_A_SEARCH and r["reading"] == "search") or (
                    meta["class"] in ("genuine", "image-read", "image-other")
                    and (r["reading"] != "search" or got(r) not in meta["expected"].split("|"))) or (
                    meta["class"] == "image-make" and got(r) != "UNMEASURED")
                if wrong:
                    print(f"    {meta['class']:11} {got(r):17} {r['reading']:10} {r.get('model', ''):6} {r['q'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
