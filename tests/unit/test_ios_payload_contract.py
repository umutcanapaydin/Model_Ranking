"""The iOS client's decoding contract, derived from the Swift source rather than restated here.

The app decodes `/v1/categories` into a `Category` struct whose `CodingKeys` name the exact JSON
fields it requires. Renaming or dropping one of those fields in the adapter is a change the Python
suite cannot currently see: every server-side test passes, `/health` answers 200, and the app fails
at runtime with `EngineError.undecodable` — a shape this project has already met on the server side
under a different name (a control that runs, is cited, and protects nothing).

The keys are PARSED OUT OF `Models.swift`, deliberately, following the precedent set by
`test_sources.py`, which derives the client list from `src/app/clients/` with `ast` so the registry
cannot silently disagree with the tree. Typing the field names here would create a third copy of
the contract, and a copy is the thing being guarded against.

Scope is honest and narrow: this proves the FIELDS the app names are present and non-null where the
struct demands non-null. It does not compile Swift and does not prove the app works -- there is no
iOS test target in this repository at all, which is its own gap.
"""

from __future__ import annotations

import pathlib
import re

from fastapi.testclient import TestClient

from app.adapter import main as adapter

SWIFT_MODELS = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/Models.swift"


def _coding_keys(struct: str) -> dict[str, str]:
    """Map Swift property -> JSON key for one struct's CodingKeys block.

    `case primaryBenchmark = "primary_benchmark"` -> {"primaryBenchmark": "primary_benchmark"}
    `case title` -> {"title": "title"}
    """
    source = SWIFT_MODELS.read_text(encoding="utf-8")
    start = source.index(f"struct {struct}:")
    block = source[source.index("enum CodingKeys", start) : source.index("}", source.index("enum CodingKeys", start))]
    keys: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r'\s*case\s+(\w+)(?:\s*=\s*"([^"]+)")?\s*$', line)
        if match:
            keys[match.group(1)] = match.group(2) or match.group(1)
    return keys


def _optional_properties(struct: str) -> set[str]:
    """Swift properties declared `T?` -- the only ones allowed to arrive null."""
    source = SWIFT_MODELS.read_text(encoding="utf-8")
    start = source.index(f"struct {struct}:")
    body = source[start : source.index("enum CodingKeys", start)]
    return {m.group(1) for m in re.finditer(r"let\s+(\w+):\s*[\w\[\]]+\?", body)}


def test_the_swift_category_struct_can_be_parsed_at_all() -> None:
    """A fixture assumption, asserted so a rename of the struct fails loudly rather than silently.

    If `Models.swift` moves or `Category` is renamed, every other test in this file would otherwise
    error in collection with an opaque `ValueError: substring not found` and read like a broken
    test rather than a broken contract.
    """
    assert SWIFT_MODELS.is_file(), f"the iOS models file is not where this test looks: {SWIFT_MODELS}"
    keys = _coding_keys("Category")
    assert keys, "Category declares no CodingKeys; the app's decoding contract cannot be derived"
    assert "id" in keys and "title" in keys


def test_the_categories_endpoint_serves_every_field_the_app_decodes() -> None:
    """REQ-API: the app discovers surfaces instead of hardcoding them, so this payload is load-bearing.

    Fails by renaming or removing any field in `/v1/categories` that `Category` names -- for
    example shortening `primary_benchmark` to `benchmark`, which no server-side test would notice.
    """
    keys = _coding_keys("Category")
    optional = _optional_properties("Category")

    client = TestClient(adapter.app)
    response = client.get("/v1/categories")
    assert response.status_code == 200

    served = response.json()["categories"]
    assert served, "the endpoint advertised no categories at all"

    for entry in served:
        for prop, json_key in keys.items():
            assert json_key in entry, (
                f"the app decodes {json_key!r} into Category.{prop} and surface "
                f"{entry.get('id')!r} does not carry it"
            )
            if prop not in optional:
                assert entry[json_key] is not None, (
                    f"Category.{prop} is non-optional in Swift and {entry.get('id')!r} served "
                    f"null for {json_key!r}; the app would fail to decode the whole list"
                )


def test_every_advertised_category_is_one_the_recommendations_route_accepts() -> None:
    """Discovery and query must agree, or the app offers a chip that answers 422.

    The strip is built from `/v1/categories` and each chip issues
    `/v1/recommendations?task=<id>`. Nothing today makes the two routes read the same map -- they
    both happen to, and this is what makes that a fact rather than a coincidence.
    """
    client = TestClient(adapter.app)
    advertised = [c["id"] for c in client.get("/v1/categories").json()["categories"]]
    assert advertised

    for task in advertised:
        response = client.get("/v1/recommendations", params={"task": task, "budget": "unlimited"})
        assert response.status_code in (200, 503), (
            f"the app advertises {task!r} as a tappable surface and the recommendations route "
            f"answered {response.status_code}"
        )


def test_the_discovery_surface_advertises_every_category_the_engine_can_rank() -> None:
    """API-04, found by an independent tester: nothing asserted the LIST was complete.

    The client has no roster of its own — that was a deliberate decision, so the engine stays the
    single source of the surface list. The consequence is that `/v1/categories` IS the product's
    navigation: serving three of nine makes six surfaces unreachable from the app, while
    `test_the_categories_endpoint_serves_every_field_the_app_decodes` iterates whatever is served
    and passes, and `test_every_advertised_category_is_one_the_recommendations_route_accepts`
    checks only the other direction.

    Dies to: `for spec in list(CATEGORIES.values())[:3]` in the endpoint.
    """
    from app.workflows.categories import CATEGORIES

    client = TestClient(adapter.app)
    advertised = {c["id"] for c in client.get("/v1/categories").json()["categories"]}

    missing = sorted(set(CATEGORIES) - advertised)
    assert not missing, (
        f"the engine can rank {missing} and the discovery surface does not offer them; the app "
        "has no list of its own, so these surfaces are unreachable"
    )
    assert advertised == set(CATEGORIES), f"unknown surfaces advertised: {advertised - set(CATEGORIES)}"


def test_ruling_a_holds_on_the_discovery_surface_too() -> None:
    """API-05: the same flag is asserted on `/v1/recommendations` and was free on `/v1/categories`.

    `surfaces_are_ranked` is Ruling A in one boolean. `test_ranking_payload.py` pins it on the
    recommendations payload; the identical field here was unasserted, so flipping it to `True`
    told every client that this list is ordered by quality — the exact claim the engine refuses to
    make — with the whole suite green.
    """
    body = TestClient(adapter.app).get("/v1/categories").json()
    assert body["surfaces_are_ranked"] is False, (
        "the discovery surface claims its categories are ranked; Ruling A says the order carries "
        "no meaning and the engine publishes no ordering between surfaces"
    )
