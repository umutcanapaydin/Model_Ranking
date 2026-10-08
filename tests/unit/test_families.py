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
