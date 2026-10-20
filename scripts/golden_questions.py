"""The golden question set's expected top 3, derived from the pinned snapshot (#289, D-202 clause 2).

`ios/EngineTests/Golden/golden-questions.json` holds 30 to 50 questions a reader types. Per question a
person writes what it asks: `question`, `language` (`en` or `tr`), `expected_surface`, and `disputed`
with its `reason` where the surface is not settled (a question that fits two surfaces). A miss that is
filed and not fixed carries `known_miss`, its issue number. Those fields are never written here.

This script writes the rest, from the snapshot of the hosted engine's `/v1/categories` and `/v1/boards`
beside it (`snapshot.json` says when it was fetched and from which build):

- `expected_top3`: the models at places 1 to 3 of the surface's family list (D-188), as ids, sorted.
  Tied models share a place, so a tie at third gives four. The family list is built here as
  `combineFamily` in `ios/ModelRanking/Engine/Combine.swift` builds it, from the published positions
  only: a board that ranks no one is left out, a model needs at least half of the remaining boards
  (rounded up), and its place is the mean of its percentile positions. `GoldenQuestionTests` builds the
  same list through the app's own code, so the two derivations are compared on every run.
- `expected_top3_names`: the same models by their display names, for the reader of the file.
- `top3_disputed` and `top3_reason`: whether the data leaves the top 3 unsettled. Two cases: the family
  has one board, so the screen shows the engine's cards and no list is built from the boards; or a
  board older than 90 days (or undated) changes the top 3, which the family's fresh boards alone would
  not give. The surface is still checked; the top 3 is reported, not asserted.

Never hand-edit a derived field. Correct the question, the surface or the snapshot, then re-derive:

    .venv/bin/python scripts/golden_questions.py            # rewrite the derived fields
    .venv/bin/python scripts/golden_questions.py --check    # exit 1 when the file is not derived
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import pathlib
import sys
from collections.abc import Mapping, Sequence
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "ios" / "EngineTests" / "Golden"
QUESTIONS = GOLDEN / "golden-questions.json"

#: How old a board's newest evaluation may be before it counts as old (D-188 clause 4, `freshForDays`).
FRESH_FOR_DAYS = 90
#: The places the golden test checks.
TOP = 3
#: D-202 clause 2: the set's size.
SIZE = (30, 50)
LANGUAGES = {"en", "tr"}
#: Written by a person, kept as they are, in this order.
HUMAN_FIELDS = ("question", "language", "expected_surface", "disputed", "reason", "known_miss", "not_a_search")
#: D-211 clause 2: the owner's two classes of input that get the note, not a ranking.
NOT_A_SEARCH_CLASSES = ("the task itself", "a question of fact")
#: Written by this script, in this order.
DERIVED_FIELDS = ("expected_top3", "expected_top3_names", "top3_disputed", "top3_reason")

Board = Mapping[str, Any]


class GoldenError(ValueError):
    """The golden file or its snapshot cannot be derived from: the derivation fails closed."""


def is_old(board: Board, as_of: datetime.date) -> bool:
    """Whether a board's newest evaluation is more than `FRESH_FOR_DAYS` whole days before `as_of`, or
    unknown, as `isStale` in `Combine.swift` draws the line."""
    date = board.get("evidence_date")
    if not date:
        return True
    return (as_of - datetime.date.fromisoformat(str(date)[:10])).days > FRESH_FOR_DAYS


def family_list(boards: Mapping[str, Board], models: Mapping[str, Any],
                family: Sequence[str]) -> tuple[list[tuple[str, int]], list[str]]:
    """The family's combined list as `[(model id, place)]` in order, and the boards it was built from."""
    ids = list(dict.fromkeys(family))
    used = [boards[i] for i in ids if i in boards and boards[i].get("standings")]
    if not used:
        return [], []
    coverage = max(1, (len(used) + 1) // 2)
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for board in used:
        size = len(board["standings"])
        span = float(max(size - 1, 1))
        listed: set[str] = set()
        for standing in board["standings"]:
            model = standing["model"]
            if model in listed:
                continue
            listed.add(model)
            percentile = min(max(int(standing["position"]), 1) - 1, size - 1) / span
            sums[model] = sums.get(model, 0.0) + percentile
            counts[model] = counts.get(model, 0) + 1
    # Nine places, rounded half away from zero as Swift's `rounded()` does: equal means stay equal.
    means = {model: math.floor(sums[model] / counts[model] * 1_000_000_000 + 0.5)
             for model in counts if counts[model] >= coverage and model in models}
    order = sorted(means, key=lambda model: (means[model], model))
    entries: list[tuple[str, int]] = []
    for index, model in enumerate(order):
        tied = index > 0 and means[order[index - 1]] == means[model]
        entries.append((model, entries[-1][1] if tied else index + 1))
    return entries, [board["id"] for board in used]


def top_places(entries: Sequence[tuple[str, int]], top: int = TOP) -> list[str]:
    """The models at places 1 to `top`, sorted by id: a set, since tied models share a place."""
    return sorted(model for model, place in entries if place <= top)


def surface_expectation(surface: str, categories: Mapping[str, Mapping[str, Any]],
                        boards: Mapping[str, Board], models: Mapping[str, Any],
                        as_of: datetime.date) -> dict[str, Any]:
    """The derived fields for one surface."""
    category = categories.get(surface)
    if category is None:
        raise GoldenError(f"the snapshot serves no surface {surface!r}")
    family = list(category.get("boards") or [category.get("primary_board")])
    entries, used = family_list(boards, models, family)
    top3 = top_places(entries)
    if not top3:
        raise GoldenError(f"the snapshot's family for {surface!r} ranks no model")
    reason = None
    if len(used) == 1:
        reason = (f"the family has one board ({used[0]}): the screen shows the engine's cards, "
                  "not a list built from the boards")
    else:
        old = [board for board in used if is_old(boards[board], as_of)]
        fresh = top_places(family_list(boards, models, [b for b in used if b not in old])[0]) if old else top3
        if fresh != top3:
            reason = (f"boards older than {FRESH_FOR_DAYS} days or undated ({', '.join(old)}) change the "
                      f"top 3; the fresh boards alone give {fresh}")
    names = {model["id"]: model["display"] for model in models.values()}
    return {"expected_top3": top3, "expected_top3_names": [names[m] for m in top3],
            "top3_disputed": reason is not None, "top3_reason": reason}


def check_entry(entry: Mapping[str, Any], index: int) -> None:
    """A person's fields, as the golden test reads them."""
    where = f"entry {index + 1} ({entry.get('question')!r})"
    if not isinstance(entry.get("question"), str) or not entry["question"].strip():
        raise GoldenError(f"{where}: no question")
    if entry.get("language") not in LANGUAGES:
        raise GoldenError(f"{where}: language must be one of {sorted(LANGUAGES)}")
    if not isinstance(entry.get("expected_surface"), str):
        raise GoldenError(f"{where}: no expected_surface")
    if not isinstance(entry.get("disputed"), bool):
        raise GoldenError(f"{where}: disputed must be true or false")
    if entry["disputed"] and not entry.get("reason"):
        raise GoldenError(f"{where}: a disputed question says why (reason)")
    if "known_miss" in entry and (entry["disputed"] or not isinstance(entry["known_miss"], int)):
        raise GoldenError(f"{where}: known_miss is an issue number, on a question that is not disputed")
    if "not_a_search" in entry and entry["not_a_search"] not in NOT_A_SEARCH_CLASSES:
        raise GoldenError(f"{where}: not_a_search names one of {list(NOT_A_SEARCH_CLASSES)} (D-211)")
    unknown = set(entry) - set(HUMAN_FIELDS) - set(DERIVED_FIELDS)
    if unknown:
        raise GoldenError(f"{where}: unknown fields {sorted(unknown)}")


def derive(entries: Sequence[Mapping[str, Any]], categories_payload: Mapping[str, Any],
           boards_payload: Mapping[str, Any], as_of: datetime.date) -> list[dict[str, Any]]:
    """Every entry with its derived fields written again from the snapshot. Fails closed: an empty or
    malformed set, or a snapshot that cannot answer a surface, is an error, never an empty answer."""
    if not SIZE[0] <= len(entries) <= SIZE[1]:
        raise GoldenError(f"the golden set holds {len(entries)} questions; D-202 asks for {SIZE[0]} to {SIZE[1]}")
    categories = {c["id"]: c for c in categories_payload.get("categories", [])}
    boards = {b["id"]: b for b in boards_payload.get("boards", [])}
    models = {m["id"]: m for m in boards_payload.get("models", [])}
    if not categories or not boards or not models:
        raise GoldenError("the snapshot holds no categories, boards or models")
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        check_entry(entry, index)
        if entry["question"] in seen:
            raise GoldenError(f"the question {entry['question']!r} is in the set twice")
        seen.add(entry["question"])
        written = {field: entry[field] for field in HUMAN_FIELDS if field in entry}
        written.setdefault("reason", None)
        written.update(surface_expectation(entry["expected_surface"], categories, boards, models, as_of))
        out.append(written)
    return out


def snapshot_day(folder: pathlib.Path) -> datetime.date:
    """The day the snapshot was fetched, in UTC: the day its boards' age is judged on."""
    meta = json.loads((folder / "snapshot.json").read_text(encoding="utf-8"))
    return datetime.date.fromisoformat(str(meta["fetched_at"])[:10])


def render(entries: Sequence[Mapping[str, Any]]) -> str:
    return json.dumps(list(entries), ensure_ascii=False, indent=2) + "\n"


def derive_file(folder: pathlib.Path) -> tuple[str, str]:
    """The golden file as it stands, and as it is derived from the snapshot beside it."""
    path = folder / QUESTIONS.name
    current = path.read_text(encoding="utf-8")
    entries = json.loads(current)
    if not isinstance(entries, list):
        raise GoldenError(f"{path} is not a list of questions")
    load = lambda name: json.loads((folder / name).read_text(encoding="utf-8"))  # noqa: E731
    derived = derive(entries, load("categories.json"), load("boards.json"), snapshot_day(folder))
    return current, render(derived)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the file is not as derived")
    parser.add_argument("--folder", type=pathlib.Path, default=GOLDEN)
    args = parser.parse_args(argv)
    try:
        current, derived = derive_file(args.folder)
    except (GoldenError, OSError, KeyError, ValueError) as error:
        print(f"golden-questions FAIL: {error}", file=sys.stderr)
        return 1
    if args.check:
        if current != derived:
            print("golden-questions FAIL: the expected top 3 is not as the snapshot derives it; run "
                  "scripts/golden_questions.py, never hand-edit a derived field", file=sys.stderr)
            return 1
        print("golden-questions PASS: every derived field is as the snapshot gives it")
        return 0
    (args.folder / QUESTIONS.name).write_text(derived, encoding="utf-8")
    print(f"golden-questions: derived {len(json.loads(derived))} questions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
