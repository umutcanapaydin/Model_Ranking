"""M20-W1 (#209, REQ-CMB-001, D-188 clause 1): the engine names, for every surface, its family: every
board that measures that task, the primary first. The phone combines a family (M20-W2) and never keeps
its own copy of one, so the engine's table is the only one, and every board it serves belongs to a
family or is named outside with its reason (AGENTS.md: derive, don't enumerate)."""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from app.workflows import families
from app.workflows.categories import CATEGORIES


def _declared_boards() -> set[str]:
    """Every board the build can write, from the declarations the build itself reads."""
    from app.workflows import board_tables, sources

    declared = {source.name for source in sources.REMOTE_SOURCES if source.writes_scores}
    declared |= {bundle.name for bundle in sources.LOCAL_BUNDLES}
    declared |= {board.source_name for board in sources.EPOCH_BOARDS}
    declared |= {board.source_name for board in board_tables.ARENA_SLICES}
    declared |= set(board_tables.EPOCH_EXTERNAL_ATTRIBUTION)
    assert len(declared) > 50, "the declared boards were not read"
    return declared


def test_every_surface_has_a_family_led_by_its_primary_board() -> None:
    assert set(families.FAMILIES) == set(CATEGORIES)
    for surface, spec in CATEGORIES.items():
        family = families.FAMILIES[surface]
        assert family and family[0] == spec.primary_source, surface
        assert len(set(family)) == len(family), f"{surface}: a board twice"


def test_every_family_board_is_a_declared_board() -> None:
    declared = _declared_boards()
    for surface, family in families.FAMILIES.items():
        assert set(family) <= declared, (surface, sorted(set(family) - declared))


def test_every_declared_board_is_in_a_family_or_named_outside_with_its_reason() -> None:
    declared = _declared_boards()
    in_a_family = {board for family in families.FAMILIES.values() for board in family}
    assert declared <= in_a_family | set(families.OUTSIDE_FAMILIES), sorted(declared - in_a_family - set(families.OUTSIDE_FAMILIES))
    assert not in_a_family & set(families.OUTSIDE_FAMILIES), sorted(in_a_family & set(families.OUTSIDE_FAMILIES))
    assert set(families.OUTSIDE_FAMILIES) <= declared, sorted(set(families.OUTSIDE_FAMILIES) - declared)
    assert all(reason.strip() for reason in families.OUTSIDE_FAMILIES.values())


@pytest.fixture
def client(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from app.adapter import main as adapter

    from .test_api_v1 import _seeded_db

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    return TestClient(adapter.app)


def test_the_categories_name_each_surfaces_family(client: TestClient) -> None:
    served = {c["id"]: c for c in client.get("/v1/categories").json()["categories"]}
    for surface in CATEGORIES:
        assert served[surface]["boards"] == list(families.FAMILIES[surface]), surface
        assert served[surface]["boards"][0] == served[surface]["primary_board"], surface


# --- The M20-W1 Code-Reviewer (docs/reviews/m20-wave-1-review.md) ------------------------------------------


def test_the_declared_boards_are_the_ones_the_engine_can_serve() -> None:
    """M4: the gate reads four kinds of declaration; a fifth would be served and no gate would see it.
    Every board the engine can attribute is one it can serve, so the two sets are compared."""
    from app.workflows.rank import SOURCE_ATTRIBUTION

    priced_only = {"litellm", "openrouter"}
    assert _declared_boards() == set(SOURCE_ATTRIBUTION) - priced_only


def _parent(board: str) -> str:
    """The board a facet belongs to: Arena's text, vision and agent boards publish slices of one vote."""
    for prefix, parent in (("arena_text_", "arena"), ("arena_vision_", "arena_vision"), ("arena_agent_", "arena_agent")):
        if board.startswith(prefix):
            return parent
    return board


def test_no_family_counts_one_board_twice_through_its_facets() -> None:
    """M1: a board and its own slice rank the same models from one vote, so together they would let one
    source outvote the others under D-188's coverage. A family holds at most one board of each source.
    Two publishers of one benchmark (SWE-bench's own and Epoch's) are two measurements (D-168 clause 5)."""
    for surface, family in families.FAMILIES.items():
        parents = [_parent(board) for board in family]
        assert len(set(parents)) == len(parents), (surface, family)


#: A surface's second benchmark, by the board that publishes it.
SECONDARY_BOARD = {"Aider polyglot": "aider", "MMLU": "epoch_mmlu"}


def test_each_surfaces_second_benchmark_is_in_its_family() -> None:
    """M2: `everyday` names MMLU as its second benchmark, and its family left MMLU out."""
    for surface, spec in CATEGORIES.items():
        if spec.secondary_benchmark is None:
            continue
        assert spec.secondary_benchmark in SECONDARY_BOARD, f"{surface}: name the board of {spec.secondary_benchmark}"
        assert SECONDARY_BOARD[spec.secondary_benchmark] in families.FAMILIES[surface], surface


def test_a_board_outside_as_a_refinement_is_one_the_refinement_table_adds() -> None:
    """M3: five boards said they were "a refinement the question adds", and the app's refinement table
    adds none of them. Every board outside for that reason is one the table names."""
    import re

    swift = (pathlib.Path(__file__).resolve().parents[2] / "ios" / "ModelRanking" / "Engine" / "Refinements.swift")
    added = set(re.findall(r'board: "([a-z_]+)"', swift.read_text(encoding="utf-8")))
    assert len(added) > 10, "the refinement table was not read"
    said = {board for board, reason in families.OUTSIDE_FAMILIES.items() if "refinement the question adds" in reason}
    assert said <= added, sorted(said - added)
