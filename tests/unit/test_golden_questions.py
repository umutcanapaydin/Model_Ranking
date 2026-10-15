"""#289 (D-202 clause 2): the golden question set's expected top 3 is derived from the pinned snapshot by
`scripts/golden_questions.py`, never written by hand, and the set stays apart from the held-out sets."""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import shutil
from typing import Any

import pytest
from scripts import golden_questions as golden

ROOT = pathlib.Path(__file__).resolve().parents[2]
DAY = datetime.date(2026, 10, 15)


def _board(board_id: str, models: list[str], date: str | None = "2026-10-01",
           positions: list[int] | None = None) -> dict[str, Any]:
    places = positions or list(range(1, len(models) + 1))
    return {"id": board_id, "evidence_date": date,
            "standings": [{"model": m, "position": p, "effort": "x"} for m, p in zip(models, places, strict=True)]}


def _payloads(boards: list[dict[str, Any]], families: dict[str, list[str]]) -> tuple[dict[str, Any], dict[str, Any]]:
    ids = sorted({s["model"] for b in boards for s in b["standings"]})
    categories = {"categories": [{"id": k, "primary_board": v[0], "boards": v} for k, v in families.items()]}
    return categories, {"boards": boards, "models": [{"id": m, "display": m.upper()} for m in ids]}


def _entries(surface: str, n: int = 30) -> list[dict[str, Any]]:
    return [{"question": f"question {i}", "language": "en", "expected_surface": surface, "disputed": False,
             "reason": None} for i in range(n)]


def test_a_model_needs_half_the_boards_and_is_placed_by_its_mean_percentile() -> None:
    boards = {b["id"]: b for b in [_board("a", ["m1", "m2", "m3"]), _board("b", ["m3", "m2", "m4"]),
                                   _board("c", ["m2", "m5"])]}
    models = {m: {} for m in ["m1", "m2", "m3", "m4", "m5"]}
    entries, used = golden.family_list(boards, models, ["a", "b", "c", "a"])
    assert used == ["a", "b", "c"]
    # Coverage 2 of 3: m2 (0.5, 0.5, 0) and m3 (1, 0) enter; m1, m4 and m5 are on one board only.
    assert entries == [("m2", 1), ("m3", 2)]


def test_tied_models_share_a_place_so_a_tie_at_third_gives_four() -> None:
    boards = {"a": _board("a", ["m1", "m2", "m3", "m4", "m5"], positions=[1, 2, 3, 3, 5])}
    entries, _ = golden.family_list(boards, {m: {} for m in ["m1", "m2", "m3", "m4", "m5"]}, ["a"])
    assert entries == [("m1", 1), ("m2", 2), ("m3", 3), ("m4", 3), ("m5", 5)]
    assert golden.top_places(entries) == ["m1", "m2", "m3", "m4"]


def test_a_board_that_ranks_no_one_or_is_not_served_changes_nothing() -> None:
    boards = {"a": _board("a", ["m1", "m2"]), "empty": _board("empty", [])}
    entries, used = golden.family_list(boards, {"m1": {}, "m2": {}}, ["a", "empty", "absent"])
    assert used == ["a"]
    assert entries == [("m1", 1), ("m2", 2)]


def test_a_one_board_family_leaves_the_top_three_unsettled() -> None:
    categories, boards = _payloads([_board("solo", ["m1", "m2", "m3", "m4"])], {"chat": ["solo"]})
    out = golden.derive(_entries("chat"), categories, boards, DAY)[0]
    assert out["expected_top3"] == ["m1", "m2", "m3"]
    assert out["expected_top3_names"] == ["M1", "M2", "M3"]
    assert out["top3_disputed"] is True
    assert "one board (solo)" in out["top3_reason"]


def test_an_old_board_that_changes_the_top_three_leaves_it_unsettled_and_one_that_does_not_is_settled() -> None:
    fresh = _board("fresh", ["m1", "m2", "m3", "m4"])
    old = _board("old", ["m4", "m3", "m2", "m1"], date="2025-01-01")
    agreeing = _board("undated", ["m1", "m2", "m3", "m4"], date=None)
    categories, boards = _payloads([fresh, old, agreeing], {"moved": ["fresh", "old"], "same": ["fresh", "undated"]})
    moved, same = golden.derive(_entries("moved", 15) + [{**e, "expected_surface": "same", "question": f"s {i}"}
                                                         for i, e in enumerate(_entries("same", 15))],
                                categories, boards, DAY)[0::15]
    assert moved["top3_disputed"] is True
    assert "old" in moved["top3_reason"]
    assert same["top3_disputed"] is False
    assert same["top3_reason"] is None


def test_a_board_ninety_days_old_is_fresh_and_ninety_one_is_old() -> None:
    assert not golden.is_old({"evidence_date": "2026-07-17"}, DAY)
    assert golden.is_old({"evidence_date": "2026-07-16"}, DAY)
    assert golden.is_old({"evidence_date": None}, DAY)


@pytest.mark.parametrize(("change", "message"), [
    (lambda e: e[:29], "29 questions"),
    (lambda e: e + _entries("chat", 21), "51 questions"),
    (lambda e: [{**e[0], "expected_surface": "nowhere"}, *e[1:]], "no surface 'nowhere'"),
    (lambda e: [{**e[0], "language": "de"}, *e[1:]], "language"),
    (lambda e: [{**e[0], "disputed": True}, *e[1:]], "says why"),
    (lambda e: [{**e[0], "known_miss": "soon"}, *e[1:]], "known_miss"),
    (lambda e: [{**e[0], "note": "x"}, *e[1:]], "unknown fields"),
    (lambda e: [e[0], e[0], *e[2:]], "twice"),
])
def test_the_derivation_fails_closed(change: Any, message: str) -> None:
    categories, boards = _payloads([_board("solo", ["m1"])], {"chat": ["solo"]})
    with pytest.raises(golden.GoldenError, match=message):
        golden.derive(change(_entries("chat")), categories, boards, DAY)


def test_an_empty_snapshot_is_an_error_not_an_empty_answer() -> None:
    with pytest.raises(golden.GoldenError, match="no categories"):
        golden.derive(_entries("chat"), {"categories": []}, {"boards": [], "models": []}, DAY)


def test_the_committed_golden_file_is_as_the_snapshot_derives_it() -> None:
    assert golden.main(["--check"]) == 0
    entries = json.loads(golden.QUESTIONS.read_text(encoding="utf-8"))
    assert golden.SIZE[0] <= len(entries) <= golden.SIZE[1]
    assert {e["language"] for e in entries} == {"en", "tr"}


def test_a_hand_edited_top_three_fails_the_check_and_rederiving_restores_it(tmp_path: pathlib.Path) -> None:
    folder = tmp_path / "Golden"
    shutil.copytree(golden.GOLDEN, folder)
    path = folder / golden.QUESTIONS.name
    entries = json.loads(path.read_text(encoding="utf-8"))
    entries[0]["expected_top3"] = ["a-model-i-like"]
    path.write_text(golden.render(entries), encoding="utf-8")
    assert golden.main(["--check", "--folder", str(folder)]) == 1
    assert golden.main(["--folder", str(folder)]) == 0
    assert golden.main(["--check", "--folder", str(folder)]) == 0
    assert path.read_text(encoding="utf-8") == golden.QUESTIONS.read_text(encoding="utf-8")


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    if isinstance(value, dict):
        return [s for item in value.values() for s in _strings(item)]
    return []


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def test_the_golden_set_is_apart_from_the_held_out_sets() -> None:
    """D-191: no golden question is a copy or a near copy (half its words or more shared) of a question in
    the router's probe sets or the judgement sheet's. A paraphrase in other words is the author's to avoid;
    this catches the copy."""
    sets = [*sorted((ROOT / "scripts" / "router_probe").glob("*.json")),
            ROOT / "docs" / "research" / "judgement" / "questions.json"]
    pool = [s for path in sets for s in _strings(json.loads(path.read_text(encoding="utf-8")))
            if len(s.split()) >= 3]
    assert len(pool) > 100, "the held-out sets were not read, so nothing was compared"
    near = []
    for entry in json.loads(golden.QUESTIONS.read_text(encoding="utf-8")):
        mine = _words(entry["question"])
        for theirs in pool:
            other = _words(theirs)
            if len(mine & other) / len(mine | other) >= 0.5:
                near.append((entry["question"], theirs))
    assert not near, f"golden questions too close to a held-out one: {near}"


def test_the_snapshot_is_a_resource_of_the_test_target_only() -> None:
    """REQ-APP-001: the app target bundles no fixture. The Golden folder is declared on the test target."""
    manifest = (ROOT / "ios" / "Package.swift").read_text(encoding="utf-8")
    code = "\n".join(line.split("//")[0] for line in manifest.splitlines())
    assert code.count("resources:") == 1
    assert code.index(".testTarget(") < code.index('resources: [.copy("Golden")]')
    assert not list((ROOT / "ios" / "ModelRanking").rglob("golden-questions.json"))
