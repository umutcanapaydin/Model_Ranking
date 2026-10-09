"""#226 (M21-W2): the owner's judgement of answers, D-188's revisit (`docs/decisions.md`). The sheet shows,
per question, two lists in an order the owner cannot read (our family list and the primary board's own
first five, A and B by a seeded coin); the key says which is which; the scorer counts his choices."""

from __future__ import annotations

import csv
import json
import pathlib

import pytest
from scripts import judgement_sheet as sheet

ROWS = [
    {"q": "best model for coding", "surface": "coding", "family": ["A", "B"], "primary": ["B", "A"],
     "boards": ["swebench", "aider"]},
    {"q": "best ai for legal questions", "surface": "expert", "family": ["C", "D"], "primary": ["D", "E"],
     "boards": ["epoch_gpqa", "arena_text_expert"]},
    {"q": "which model reads my photos", "surface": "vision", "family": [], "primary": ["F"], "boards": ["arena_vision"]},
]


def _make(tmp_path: pathlib.Path, seed: int = 7) -> tuple[pathlib.Path, pathlib.Path]:
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps(ROWS), encoding="utf-8")
    out, key = tmp_path / "sheet.csv", tmp_path / "key.json"
    sheet.make(probe, out, key, seed=seed)
    return out, key


def test_the_sheet_blinds_which_list_is_ours_and_the_key_says(tmp_path: pathlib.Path) -> None:
    out, key = _make(tmp_path)
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    sides = json.loads(key.read_text(encoding="utf-8"))
    assert [row["question"] for row in rows] == [r["q"] for r in ROWS[:2]], "a question with no family list is left out"
    assert set(rows[0]) == {"n", "question", "surface", "A", "B", "choice", "note"}
    for row, side in zip(rows, sides, strict=True):
        family = " / ".join(next(r["family"] for r in ROWS if r["q"] == row["question"]))
        assert row[side["family"]] == family and side["family"] in ("A", "B")
        assert row["choice"] == ""
    assert "family" not in out.read_text(encoding="utf-8").lower(), "the sheet names which list is ours"


def test_the_coin_is_seeded_so_a_sheet_can_be_made_again(tmp_path: pathlib.Path) -> None:
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    first, _ = _make(tmp_path / "one", seed=3)
    second, _ = _make(tmp_path / "two", seed=3)
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_the_scorer_counts_each_choice_and_reads_the_revisit(tmp_path: pathlib.Path) -> None:
    out, key = _make(tmp_path)
    sides = json.loads(key.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    rows[0]["choice"] = sides[0]["primary"]
    rows[1]["choice"] = sides[1]["primary"]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = sheet.score(out, key)
    assert result == {"family": 0, "primary": 2, "same": 0, "unjudged": 0, "revisit": True}


def test_the_scorer_refuses_a_choice_it_cannot_read_and_a_key_for_another_sheet(tmp_path: pathlib.Path) -> None:
    out, key = _make(tmp_path)
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    rows[0]["choice"] = "maybe"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="choice"):
        sheet.score(out, key)
    key.write_text(json.dumps([{"question": "another", "family": "A", "primary": "B"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="key"):
        sheet.score(out, key)


# --- The M21-W2 review's M7 ----------------------------------------------------------------------------------


def _rows(n: int) -> list[dict[str, object]]:
    return [{"q": f"question {i}", "surface": "coding", "family": [f"F{i}"], "primary": [f"P{i}"], "boards": ["b"]}
            for i in range(n)]


def test_ours_lands_on_both_sides(tmp_path: pathlib.Path) -> None:
    """M7: with twelve rows the coin puts our list on A and on B, so "ours is always A" fails here."""
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps(_rows(12)), encoding="utf-8")
    sheet.make(probe, tmp_path / "sheet.csv", tmp_path / "key.json", seed=2026)
    sides = {side["family"] for side in json.loads((tmp_path / "key.json").read_text(encoding="utf-8"))}
    assert sides == {"A", "B"}


def test_a_tie_is_no_revisit_and_same_is_neither(tmp_path: pathlib.Path) -> None:
    """M7: a tie does not call D-188's revisit, and "same" counts for neither list."""
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps(_rows(4)), encoding="utf-8")
    out, key = tmp_path / "sheet.csv", tmp_path / "key.json"
    sheet.make(probe, out, key, seed=1)
    sides = json.loads(key.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    for row, side, choice in zip(rows, sides, ["primary", "family", "same", "SAME"], strict=True):
        row["choice"] = side.get(choice, choice)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert sheet.score(out, key) == {"family": 1, "primary": 1, "same": 2, "unjudged": 0, "revisit": False}


def test_the_key_is_never_written_inside_the_repository(tmp_path: pathlib.Path) -> None:
    """M7: the key, written beside the sheet in the repository, could be committed and seen before the
    owner judges; a key inside the repository is refused."""
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps(_rows(2)), encoding="utf-8")
    inside = sheet.ROOT / "docs/research/judgement/key.json"
    with pytest.raises(ValueError, match="key"):
        sheet.make(probe, tmp_path / "sheet.csv", inside)
    assert not inside.exists()
