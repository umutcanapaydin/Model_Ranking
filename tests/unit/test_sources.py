"""M7-W1 — the source registry agrees with the filesystem (REQ-ING-012).

`sources.py` makes the builder and the smoke gate agree with *each other*. It cannot make either
agree with *reality* — that is this file's job, and it does it by producing the list of clients
from `src/app/clients/` with `ast` rather than typing one out.

This is the M6 lesson in executable form: **an enumeration that is typed out is a denylist wearing
better clothes**, and every one of the four found in M6 was missing exactly the member that
mattered. A registry of five sources that nobody derives is the fifth.
"""

from __future__ import annotations

import ast
import pathlib

from app.workflows.sources import LOCAL_BUNDLES, REMOTE_SOURCES

CLIENTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "src" / "app" / "clients"


def _client_classes() -> dict[str, str]:
    """Every `*Client` class defined under src/app/clients/, produced from the tree."""
    found: dict[str, str] = {}
    for path in sorted(CLIENTS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Client"):
                found[node.name] = path.name
    return found


def test_the_walk_finds_clients_at_all() -> None:
    """A derivation that silently finds nothing would make every test below vacuously pass."""
    classes = _client_classes()
    assert len(classes) >= 5, f"expected the real client modules, walked up {classes}"


def test_every_client_is_either_ingested_or_declared_a_local_bundle() -> None:
    """The check the typed-out list cannot do: nothing may be silently absent.

    A new client added to src/app/clients/ fails here until someone decides, in writing, whether
    the builder ingests it or whether it is an owner-placed artifact that must never be fetched.
    """
    declared_remote = {source.client.__name__ for source in REMOTE_SOURCES}
    declared_local = {bundle.client_class for bundle in LOCAL_BUNDLES}
    declared = declared_remote | declared_local

    undeclared = {
        name: module for name, module in _client_classes().items() if name not in declared
    }
    assert not undeclared, (
        "these clients exist but the source registry neither ingests them nor declares them "
        f"local bundles: {undeclared}"
    )


def test_the_registry_names_nothing_that_does_not_exist() -> None:
    """The other direction: a client deleted from the tree must not linger in the registry."""
    existing = set(_client_classes())
    declared_local = {bundle.client_class for bundle in LOCAL_BUNDLES}

    assert declared_local <= existing, f"local bundles name absent classes: {declared_local - existing}"
    for source in REMOTE_SOURCES:
        assert source.client.__name__ in existing, f"{source.name} names an absent client"


def test_local_bundles_state_why_they_are_never_fetched() -> None:
    """D-101's boundary is a reason, not a status. An empty reason is an undocumented exemption."""
    for bundle in LOCAL_BUNDLES:
        assert bundle.reason.strip(), f"{bundle.name} is excluded from the build with no reason"


def test_every_remote_source_declares_a_non_zero_floor() -> None:
    """A floor of zero would let a 200-carrying-an-empty-list pass as a working dependency."""
    for source in REMOTE_SOURCES:
        assert source.minimum_rows > 0, f"{source.name} has no floor; a hollow feed would pass"


def test_arena_is_the_only_optional_source() -> None:
    """D-121 permits exactly one exception, and an exception nobody pins becomes the default.

    Added by the Stage-3b Tester: flipping `arena` back to required, and separately flipping the
    dataclass default to `required=False` for every source, both left the suite green. `required`
    is the flag that decides whether an upstream outage produces a refusal or a quiet artifact, so
    its value is an acceptance criterion, not an implementation detail.
    """
    optional = {source.name for source in REMOTE_SOURCES if not source.required}
    assert optional == {"arena"}, f"D-121 names arena and only arena as optional; found {optional}"


def test_every_source_a_category_names_as_primary_exists_in_the_registry() -> None:
    """The registry's names are the join key the blinded-surface report is derived through.

    `build.py:_surfaces_left_without_evidence` matches `CATEGORIES[*].primary_source` against
    `RemoteSource.name`. Renaming a source therefore silently empties the surface report rather
    than breaking loudly — the mutant that renamed `arena` stayed green.
    """
    from app.workflows.categories import CATEGORIES

    known = {source.name for source in REMOTE_SOURCES} | {b.name for b in LOCAL_BUNDLES}
    unknown = {
        task: spec.primary_source
        for task, spec in CATEGORIES.items()
        if spec.primary_source not in known
    }
    assert not unknown, f"categories name primary sources the registry does not define: {unknown}"


def test_a_registry_name_matches_the_name_its_client_writes_rows_under() -> None:
    """The join key the M7-W1 rejection-rollback silently depends on.

    Added by the Stage-3b Tester at re-review. `build.py` rolls a rejected source back with
    `reset_source(conn, table, source.name)` — the REGISTRY's name — while `ingest.py` writes every
    row under `source.name` of the CLIENT. Those are two different objects that happen to agree
    today, and nothing asserted it: if they ever diverge the rollback deletes nothing, the rejected
    feed's rows stay in the artifact, `source_health` then reports the source as PRESENT, and the
    serving path's "no evidence source" disclosure never fires. That is the exact chain D-121
    stakes itself on, broken by a name mismatch nobody would look for.
    """
    for source in REMOTE_SOURCES:
        client = source.client()
        assert client.name == source.name, (
            f"registry calls it {source.name!r} but its client writes rows as {client.name!r}; "
            "the rejection rollback keys on the registry name and would delete nothing"
        )


def test_source_names_are_unique() -> None:
    names = [source.name for source in REMOTE_SOURCES]
    assert len(names) == len(set(names)), f"duplicate source names: {names}"


def test_the_registry_name_matches_the_client_name_it_rolls_back_by() -> None:
    """MINOR-6: the rollback's join key is asserted, not assumed.

    `_ingest_sources` rolls a rejected source back with `reset_source(conn, table, source.name)` —
    the REGISTRY name. The rows were written under `client.name`. All five agree today and nothing
    said so, which is the same silent-divergence class this file exists for: if a registry entry is
    ever renamed without its client, the rollback stops matching and MINOR-1 comes back with no
    test to notice.
    """
    for source in REMOTE_SOURCES:
        client_name = getattr(source.client(), "name", None)
        assert client_name == source.name, (
            f"registry calls it {source.name!r} but its client writes rows as {client_name!r}; "
            "the rejected-source rollback joins on the registry name and would miss them"
        )
