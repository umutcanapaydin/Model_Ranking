"""REQ-RTR-002/-005 — the router's boundary, gated where a gate can actually run.

D-126 ruled this at M8: **the router picks the QUESTION; the engine answers it, and the router may
never say a model is good.** The boundary is enforced in Swift, and no Swift is executed by any
gate in this repository (W-038). So these tests hold the half that IS visible from here — the
relationship between what the engine advertises and what the client can do with it — and say
plainly what they do not cover.

The routing hints live in the client rather than in `/v1`, and that is a consequence rather than a
preference: the payload is frozen (D-115), D-124's single revision window was spent by D-125, and
the owner ruled on 2026-08-22 that this milestone finishes with what exists. A hint is not evidence,
so keeping it out of the contract is defensible — but a hand-maintained list keyed to ids the engine
owns is this project's most-repeated defect shape, and it has bitten here five times. This is the
gate that stops it being silent.
"""

from __future__ import annotations

import pathlib
import re

from fastapi.testclient import TestClient

from app.adapter import main as adapter

ROUTER = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/Router.swift"


def _hint_ids() -> set[str]:
    """The category ids the client has a routing hint for, parsed from the Swift."""
    source = ROUTER.read_text(encoding="utf-8")
    block = source[source.index("static let byID:") : source.index("unmeasuredFallback")]
    return set(re.findall(r'^\s*"([a-z-]+)":', block, re.MULTILINE))


def test_every_surface_the_engine_advertises_has_a_routing_hint() -> None:
    """A surface with no hint is one the router can never choose.

    The engine owns the id list and the client owns the descriptions, so they drift the moment a
    category is added — and the failure is silent in the worst way: the new surface is still
    reachable by tapping a chip, so nothing looks broken, while the front door quietly cannot send
    anyone there.
    """
    from app.workflows.categories import CATEGORIES

    hints = _hint_ids()
    assert hints, "no routing hints could be parsed; the derivation is broken, not clean"

    missing = sorted(set(CATEGORIES) - hints)
    assert not missing, (
        f"the engine ranks {missing} and the router has no description for them, so it can never "
        "route a question there"
    )

    stale = sorted(hints - set(CATEGORIES))
    assert not stale, (
        f"the router describes {stale}, which the engine does not serve; a hint outliving its "
        "surface is how the closed set stops being closed"
    )


def test_the_unmeasured_fallback_is_a_surface_the_engine_actually_serves() -> None:
    """REQ-RTR-005, and the owner's ruling that an unmeasured question goes to general chat.

    That is only honest because `assistant` is a MEASURED surface — a general-purpose chat model
    genuinely is the tool for a question nothing here measures specifically. Pointing the fallback
    at an id the engine does not serve would turn the front door into a dead end.
    """
    source = ROUTER.read_text(encoding="utf-8")
    match = re.search(r'unmeasuredFallback\s*=\s*"([a-z-]+)"', source)
    assert match, "the router has no fallback for a question the catalogue does not measure"

    served = {c["id"] for c in TestClient(adapter.app).get("/v1/categories").json()["categories"]}
    assert match.group(1) in served, (
        f"the unmeasured fallback is {match.group(1)!r} and the engine does not serve it"
    )


def test_the_router_validates_against_the_ids_the_engine_serves() -> None:
    """REQ-RTR-002's structural half: the closed set is the ENGINE's list, not a second copy.

    Where the platform allows it the set is a generation schema, so a recommendation is not
    expressible; everywhere else the outcome is checked against the same fetched list. Either way
    the ids come from `/v1/categories` at runtime. A router that validated against its own hint
    table would be checking itself.
    """
    source = ROUTER.read_text(encoding="utf-8")
    assert "within known: [String]" in source, "the router no longer takes the engine's id list"
    assert re.search(r"anyOf:\s*known", source), (
        "the on-device model's closed set is no longer built from the ids the engine serves"
    )
    assert re.search(r"known\.contains\(id\)", source), (
        "the model's answer is no longer checked against the engine's list; the schema should make "
        "that unreachable and an unreachable guard on a model's output is worth its two lines"
    )


def test_the_router_never_produces_anything_but_a_category_id() -> None:
    """D-126's absolute boundary, asserted on the TYPE the router can return.

    `RoutingOutcome` carries a category id, a tier and a flag. There is no field a recommendation,
    a model name or a sentence of praise could travel in — which is the only version of this
    guarantee that does not depend on a prompt being obeyed.
    """
    source = ROUTER.read_text(encoding="utf-8")
    block = source[source.index("struct RoutingOutcome") : source.index("var explanation")]
    fields = set(re.findall(r"let (\w+):", block))
    assert fields == {"categoryID", "tier", "unmeasured"}, (
        f"RoutingOutcome carries {sorted(fields)}; anything beyond a surface id, how it was chosen "
        "and whether it is measured is a channel for an opinion the router may not have"
    )


def test_nothing_typed_by_the_reader_reaches_the_engine() -> None:
    """REQ-RTR-004. The engine is asked for a SURFACE, never for a question.

    `/v1` takes `task` and `budget` and nothing else, and the router's only contribution to a
    request is which of nine ids the task is. The scoring path is untouched (D-104) because the
    typed text never enters it.
    """
    view = (ROUTER.parent.parent / "ContentView.swift").read_text(encoding="utf-8")
    code = "\n".join(line.split("//", 1)[0] for line in view.splitlines())

    assert "task = outcome.categoryID" in code, "the router's choice does not select the surface"
    assert not re.search(r"question[^\n]*URLQueryItem|URLQueryItem[^\n]*question", code), (
        "the reader's typed question is being put into a request to the engine"
    )

    client = (ROUTER.parent / "EngineClient.swift").read_text(encoding="utf-8")
    assert not re.search(r"\bquestion\b", client), (
        "the engine client mentions the reader's question; it must only ever send task and budget"
    )
