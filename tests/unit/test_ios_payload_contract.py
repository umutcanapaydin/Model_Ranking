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


def _struct_body(struct: str) -> str:
    """One struct's own source, bounded at the NEXT struct declaration.

    The bound is the whole point. The first version searched forward from `struct X:` for the next
    `enum CodingKeys` with no upper limit, so a struct that declares none silently inherited the
    NEXT struct's keys -- `SourceHealth` was tested against `SourceRow`'s field set and the test
    reported a missing `newest_run_date` that the API was never supposed to send there. A
    derivation that reads past its subject is worse than a hand-written list, because it looks
    authoritative.
    """
    source = SWIFT_MODELS.read_text(encoding="utf-8")
    start = source.index(f"struct {struct}:")
    following = re.search(r"^struct \w+[:\s]", source[start + 1 :], re.MULTILINE)
    return source[start : start + 1 + following.start()] if following else source[start:]


def _coding_keys(struct: str) -> dict[str, str]:
    """Map Swift property -> JSON key for one struct.

    `case primaryBenchmark = "primary_benchmark"` -> {"primaryBenchmark": "primary_benchmark"}
    `case title` -> {"title": "title"}

    A struct with NO CodingKeys block decodes by property name, so its properties ARE its keys.
    Returning an empty map for that case would silently exempt the struct from every assertion --
    which is how `SourceHealth` and `Query` would have passed while carrying nothing at all.
    """
    body = _struct_body(struct)
    if "enum CodingKeys" in body:
        block = body[body.index("enum CodingKeys") :]
        block = block[: block.index("}")]
        keys: dict[str, str] = {}
        for line in block.splitlines():
            match = re.match(r"\s*case\s+(.+?)\s*$", line)
            if not match:
                continue
            # Swift allows several cases on ONE line: `case model, vendor, score`. The first
            # version of this parser required end-of-line after a single name, so it silently
            # skipped every such line -- `RankedModel` parsed as 5 of its 11 fields, and a mutant
            # deleting `harness` from the published set walked straight through. An under-reading
            # parser does not fail; it EXEMPTS, which is the more dangerous half.
            for part in match.group(1).split(","):
                named = re.match(r'\s*(\w+)(?:\s*=\s*"([^"]+)")?\s*$', part)
                if named:
                    keys[named.group(1)] = named.group(2) or named.group(1)
        return keys
    return {name: name for name in re.findall(r"^\s*let\s+(\w+):", body, re.MULTILINE)}


def _optional_properties(struct: str) -> set[str]:
    """Swift properties declared `T?` -- the only ones allowed to arrive null."""
    body = _struct_body(struct)
    head = body[: body.index("enum CodingKeys")] if "enum CodingKeys" in body else body
    return {m.group(1) for m in re.finditer(r"let\s+(\w+):\s*[\w\[\]]+\?", head)}


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


def _declared_properties(struct: str) -> list[str]:
    """Every `let name:` in the struct's own body — what the parser must account for."""
    body = _struct_body(struct)
    head = body[: body.index("enum CodingKeys")] if "enum CodingKeys" in body else body
    return re.findall(r"^\s*let\s+(\w+):", head, re.MULTILINE)


def _assert_struct_is_satisfied(struct: str, entry: dict, where: str) -> None:
    """Every CodingKey of one Swift struct is present, and non-null where Swift demands non-null."""
    keys = _coding_keys(struct)
    optional = _optional_properties(struct)
    assert keys, f"{struct} declares no CodingKeys; the app's decoding contract cannot be derived"

    # THE PARSER MUST PROVE IT READ EVERYTHING. Swift requires an explicit CodingKeys enum to be
    # exhaustive, so a property with no key means this parser missed it -- and a missed key is a
    # silent exemption, not a visible failure. It has happened twice in this file already: a
    # forward search that ran past its struct, and a regex that could not see comma-separated
    # cases. This is the assertion that makes the next one loud.
    missed = sorted(set(_declared_properties(struct)) - set(keys))
    assert not missed, (
        f"{struct} declares {missed} and this parser produced no key for them, so nothing about "
        "those fields is being checked. Fix the parser, not the struct"
    )

    for prop, json_key in keys.items():
        assert json_key in entry, (
            f"the app decodes {json_key!r} into {struct}.{prop} and {where} does not carry it"
        )
        if prop not in optional:
            assert entry[json_key] is not None, (
                f"{struct}.{prop} is non-optional in Swift and {where} served null for "
                f"{json_key!r}; the app would fail to decode the WHOLE response, not this field"
            )


def test_the_categories_endpoint_serves_every_field_the_app_decodes() -> None:
    """REQ-API: the app discovers surfaces instead of hardcoding them, so this payload is load-bearing.

    Fails by renaming or removing any field in `/v1/categories` that `Category` names -- for
    example shortening `primary_benchmark` to `benchmark`, which no server-side test would notice.
    """
    client = TestClient(adapter.app)
    response = client.get("/v1/categories")
    assert response.status_code == 200

    served = response.json()["categories"]
    assert served, "the endpoint advertised no categories at all"
    for entry in served:
        _assert_struct_is_satisfied("Category", entry, f"surface {entry.get('id')!r}")


def test_the_recommendation_payload_satisfies_every_struct_the_app_decodes(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """The gap this file's own docstring did not cover, found by the M8 fresh-eyes review.

    The helpers here are generic and were called for `Category` ALONE. `Answer`, `Pick`,
    `RankedModel`, `SourceHealth` and `SourceRow` -- every struct that decodes an actual
    recommendation -- were ungated, while `ios/README.md`, W-038 and the M8 closure report all
    leaned on this file as the thing that means "a server-side rename can no longer break the app
    silently". It could. Renaming `blended_per_m`, or making `harness` nullable, would fail
    `Answer` at runtime with `EngineError.undecodable` while every Python test passed.

    That is this project's most-repeated shape once more: a control whose SCOPE is narrower than
    the sentence describing it. The machinery was already written; only the loop was missing.
    """
    from .test_api_v1 import _seeded_db

    db = tmp_path / "seeded.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")

    response = TestClient(adapter.app).get(
        "/v1/recommendations", params={"task": "coding", "budget": "unlimited"}
    )
    assert response.status_code == 200
    answers = response.json()["answers"]
    assert answers, "fixture assumption: the coding intent must return answers"

    checked = {"Answer": 0, "Pick": 0, "RankedModel": 0, "SourceHealth": 0, "SourceRow": 0}
    for answer in answers:
        _assert_struct_is_satisfied("Answer", answer, f"surface {answer.get('surface')!r}")
        checked["Answer"] += 1
        for pick in answer["picks"]:
            _assert_struct_is_satisfied("Pick", pick, f"pick {pick.get('label')!r}")
            checked["Pick"] += 1
        for row in answer["ranking"]:
            _assert_struct_is_satisfied("RankedModel", row, f"ranking row {row.get('model')!r}")
            checked["RankedModel"] += 1
        health = answer.get("source_health")
        if health is not None:
            _assert_struct_is_satisfied("SourceHealth", health, "source_health")
            checked["SourceHealth"] += 1
            for source in health["sources"]:
                _assert_struct_is_satisfied("SourceRow", source, f"source {source.get('source')!r}")
                checked["SourceRow"] += 1

    empty = sorted(name for name, count in checked.items() if count == 0)
    assert not empty, (
        f"{empty} were never reached by this fixture, so nothing about them was proven. A test "
        "that walks a tree proves only the branches the fixture grew"
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
