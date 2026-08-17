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


def test_source_names_are_unique() -> None:
    names = [source.name for source in REMOTE_SOURCES]
    assert len(names) == len(set(names)), f"duplicate source names: {names}"
