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


# --- The M20-W1 Tester (docs/reviews/m20-wave-1-tester.md) -------------------------------------------------


def test_a_board_the_refinement_table_adds_stands_outside_and_says_so() -> None:
    """covers REQ-CMB-001 (D-188 clause 1: "every other board stands outside every family with its reason:
    a language or a domain the question adds as a refinement"). The M3 test reads one way only: a reason
    may not claim a refinement the table lacks. This is the other way: a board the table adds stands
    outside every family, and its reason says the question adds it, so W3 finds it by its reason. Planted,
    `arena_text_chinese` given the "names no one language" reason stayed green before this test."""
    from .test_refinements import _entries

    added = {str(entry["board"]) for entry in _entries()}
    assert len(added) > 10, "the refinement table was not read"
    in_a_family = {board for family in families.FAMILIES.values() for board in family}
    assert not added & in_a_family, sorted(added & in_a_family)
    said = {board for board, reason in families.OUTSIDE_FAMILIES.items() if "refinement the question adds" in reason}
    assert said == added, {"added, reason silent": sorted(added - said), "reason claims it": sorted(said - added)}


def _arena_votes() -> dict[str, str]:
    """Each Arena board -> the vote it is drawn from, derived from its declared config, never a prefix list.

    A config named `<config>_<facet>` after another declared config is a facet of that config's vote: the
    module itself treats the `agent_*` configs that way (`_AGENT_FACET`). So `text_factuality` is drawn from
    `text`, `agent_steerability` from `agent`, and every `text` or `vision` slice from its config."""
    from app.clients.arena import ARENA_BOARDS
    from app.workflows import board_tables

    configs = {board.id: board.config for board in ARENA_BOARDS.values()}
    configs |= {board.source_name: board.config for board in board_tables.ARENA_SLICES}
    declared = set(configs.values())

    def vote(config: str) -> str:
        parents = [other for other in declared if config.startswith(other + "_")]
        return min(parents, key=len) if parents else config

    return {board: vote(config) for board, config in configs.items()}


#: Surfaces whose family holds two boards of one derived vote, left open for the owner: `arena_search` and
#: `arena_search_factuality` (config `search_factuality`, named as `agent_steerability` is). On the served
#: boards of 2026-10-08 they rank the same 27 models with a rank correlation of 0.92, the same as
#: `arena_agent` against its own steerability facet (0.921), which stands outside. The W1 Tester's M1.
#: Either the search factuality board leaves these families, or D-188 records that a factuality config is a
#: vote of its own and `_arena_votes` says so; either way this set empties.
#: Settled by the W1 Tester's M1: each search surface keeps its one board, so no family is open here.
_OPEN_ONE_VOTE_TWICE: set[str] = set()


def test_no_family_holds_two_boards_of_one_arena_vote() -> None:
    """covers REQ-CMB-001 (D-188 clause 1: "a family holds at most one board of each source (Arena's slices
    are facets of one vote)"). The M1 test reads a board's source from three hand-kept prefixes, so
    `arena_factuality` (config `text_factuality`) beside `arena` in `everyday` stayed green when planted.
    Here the vote is derived from the declared configs, and the derivation must find the facets."""
    votes = _arena_votes()
    shared = {vote for vote in votes.values() if list(votes.values()).count(vote) > 1}
    assert {"text", "vision", "agent"} <= shared, f"the derivation found no facets: {sorted(shared)}"
    assert votes["arena_factuality"] == "text" and votes["arena_agent_steerability"] == "agent"

    twice = {}
    for surface, family in families.FAMILIES.items():
        drawn = [votes.get(board, board) for board in family]
        if len(set(drawn)) != len(drawn):
            twice[surface] = family
    assert set(twice) - _OPEN_ONE_VOTE_TWICE == set(), {s: twice[s] for s in set(twice) - _OPEN_ONE_VOTE_TWICE}
    assert set(twice) >= _OPEN_ONE_VOTE_TWICE, "settled: drop it from _OPEN_ONE_VOTE_TWICE"


def test_every_board_the_live_route_serves_is_in_a_family_or_named_outside(client: TestClient) -> None:
    """covers REQ-CMB-001 (plan §2 W1: "every board `/v1/boards` serves belongs to a family or is named as
    left out"). The other gates read the declarations; this one reads the live route the phone reads, and
    every family the live `/v1/categories` names is checked against the same placement. The seeded artifact
    carries two boards, so every declared Arena board is written into it first, as the build writes them."""
    import contextlib
    import os
    import sqlite3

    from app.workflows import board_tables

    with contextlib.closing(sqlite3.connect(os.environ["MODEL_RANKING_DB"])) as conn, conn:
        model, observed = conn.execute(
            "SELECT s.model_id, s.observed_at FROM scores s JOIN px_median p ON p.model_id = s.model_id LIMIT 1"
        ).fetchone()
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort, run_date, "
            "source, source_url, observed_at) "
            "VALUES (?, ?, ?, ?, 1000, ?, 'unspecified', '2026-10-01', ?, 'https://example.test', ?)",
            [(model, model, s.benchmark, s.metric, s.harness, s.source_name, observed) for s in board_tables.ARENA_SLICES],
        )
    served = {board["id"] for board in client.get("/v1/boards").json()["boards"]}
    assert len(served) > len(board_tables.ARENA_SLICES), f"the live route served too few boards: {sorted(served)}"
    named = {c["id"]: c["boards"] for c in client.get("/v1/categories").json()["categories"]}
    in_a_family = {board for family in named.values() for board in family}
    assert served <= in_a_family | set(families.OUTSIDE_FAMILIES), sorted(served - in_a_family - set(families.OUTSIDE_FAMILIES))
    assert {named[surface][0] for surface in named} & served, "no served board leads a family"


def test_d188_lists_every_family_as_the_code_holds_it() -> None:
    """The W1 Tester's M4: a board moved from one family to another passed every test, and D-188, which
    records the families, listed only their sizes. D-188's family table equals `FAMILIES`, board for
    board and in order."""
    import re

    text = (pathlib.Path(__file__).resolve().parents[2] / "docs" / "decisions.md").read_text(encoding="utf-8")
    adr = text.split("\n## D-188", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\s*\| `([a-z_-]+)` \| ((?:`[a-z0-9_]+`(?:, )?)+) \|$", adr, re.MULTILINE)
    tabled = {surface: tuple(re.findall(r"`([a-z0-9_]+)`", boards)) for surface, boards in rows}
    assert tabled == families.FAMILIES, {s: (tabled.get(s), f) for s, f in families.FAMILIES.items() if tabled.get(s) != f}


# --- The M20 repo review's M1 (docs/reviews/m20-repo-review.md) -------------------------------------------


def test_a_refinement_takes_the_place_of_its_votes_board_and_never_joins_beside_it() -> None:
    """covers REQ-CMB-004 (D-188 clauses 1 and 6, the M20 repo review's M1). Every refinement is a slice of
    Arena's text vote. Added beside the family's own text-vote board, it let one vote count twice, for the
    coverage and for the mean. So each surface a refinement may refine names that board, and a refinement
    takes its place: every family, with any refinement it allows, holds one board of each vote."""
    from .test_refinements import _entries

    votes = _arena_votes()
    entries = _entries()
    refined_surfaces = {str(surface) for entry in entries for surface in entry["surfaces"]}  # type: ignore[union-attr]
    assert set(families.REFINED_BOARD) == refined_surfaces, "a surface the table refines names no board, or the reverse"
    for surface, board in families.REFINED_BOARD.items():
        assert board in families.FAMILIES[surface], (surface, board)
        assert votes.get(board) == "text", (surface, board)
    for entry in entries:
        slice_board = str(entry["board"])
        assert votes.get(slice_board) == "text", slice_board
        for surface in entry["surfaces"]:  # type: ignore[union-attr]
            replaced = families.REFINED_BOARD[str(surface)]
            family = [slice_board if board == replaced else board for board in families.FAMILIES[str(surface)]]
            drawn = [votes.get(board, board) for board in family]
            assert len(set(drawn)) == len(drawn), (surface, family)


def test_the_categories_name_the_board_a_refinement_replaces(client: TestClient) -> None:
    """covers REQ-CMB-004: `/v1/categories` names, per surface, the board a refinement takes the place of,
    or `null` where no refinement refines it."""
    served = {c["id"]: c for c in client.get("/v1/categories").json()["categories"]}
    for surface in CATEGORIES:
        assert served[surface]["refined_board"] == families.REFINED_BOARD.get(surface), surface
