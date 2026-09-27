"""M17-W5 P1 (#64, D-168) -- the refinement table the phone selects boards from.

D-168: a question selects a surface (its primary board) plus at most two declared refinements,
each an Arena slice. The table is hand-kept in the Engine layer
(`ios/ModelRanking/Engine/Refinements.swift`), so it is held here against what the engine serves: a
slice it stops serving, or a surface it renames, fails loudly instead of vanishing.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from app.clients.arena_slices import ARENA_SLICES
from app.workflows.categories import CATEGORIES

TABLE = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/Refinements.swift"
ENTRY = re.compile(
    r'Refinement\(\s*value:\s*"(?P<value>[^"]+)",\s*kind:\s*\.(?P<kind>\w+),\s*board:\s*"(?P<board>[^"]+)",'
    r'\s*surfaces:\s*\[(?P<surfaces>[^\]]*)\],\s*reason:\s*"(?P<reason>[^"]*)"'
)


def _entries() -> list[dict[str, object]]:
    text = TABLE.read_text(encoding="utf-8")
    entries = [
        {**m.groupdict(), "surfaces": re.findall(r'"([^"]+)"', m.group("surfaces"))}
        for m in ENTRY.finditer(text)
    ]
    # Every `Refinement(` in the file must have parsed, or an entry would escape every check below.
    assert len(entries) == text.count("Refinement(value:"), "an entry this test could not parse"
    return entries


def test_the_table_exists_and_is_not_empty() -> None:
    assert len(_entries()) >= 20


def test_every_refinement_names_a_board_the_engine_serves() -> None:
    served = {board.source_name for board in ARENA_SLICES}
    unknown = sorted(str(e["board"]) for e in _entries() if e["board"] not in served)
    assert not unknown, f"refinements naming boards the engine does not serve: {unknown}"


def test_every_refinement_refines_surfaces_that_exist_and_says_why() -> None:
    for entry in _entries():
        surfaces = entry["surfaces"]
        assert surfaces, f"{entry['value']} refines no surface"
        assert set(surfaces) <= set(CATEGORIES), f"{entry['value']} names an unknown surface"
        assert str(entry["reason"]).strip(), f"{entry['value']} has no reason"


def test_a_vision_slice_refines_only_the_vision_surface() -> None:
    for entry in _entries():
        if str(entry["board"]).startswith("arena_vision_"):
            assert entry["surfaces"] == ["vision"], entry["value"]


def test_values_are_unique_within_a_kind_and_never_the_decline_sentinel() -> None:
    seen: set[tuple[str, str]] = set()
    for entry in _entries():
        key = (str(entry["kind"]), str(entry["value"]))
        assert key not in seen, key
        seen.add(key)
        assert entry["value"] not in {"none", "__none__"}


@pytest.fixture()
def client(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from app.adapter import main as adapter

    from .test_api_v1 import _seeded_db

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    return TestClient(adapter.app)


def test_each_surface_names_its_primary_board(client: TestClient) -> None:
    """The phone needs the surface's first board by id: SWE-bench Verified is published by two
    boards (#53), so the benchmark's name cannot say which one the surface ranks on."""
    served = {c["id"]: c for c in client.get("/v1/categories").json()["categories"]}
    for surface, spec in CATEGORIES.items():
        assert served[surface]["primary_board"] == spec.primary_source
