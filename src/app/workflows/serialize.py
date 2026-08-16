"""The ONE serializer. Every rendering of a recommendation derives from here (REQ-API-003).

**The defect this module removes.** Until M6-W2 there were two hand-maintained renderings of the
same object: the CLI printed `asdict(rec)`, and the `/v1` adapter built a dictionary by naming all
nineteen `Pick` fields and all ten `Recommendation` fields by hand. The hand-written one was correct
on the day it was written and structurally unable to stay that way — the W1 code review proved it by
deleting `"stale_notice"` from it, and all thirteen tests stayed green.

That is the same shape as the defect M5's closure security review caught: two artifacts of ONE run
disagreeing, with every gate green. The remedy is not a better mirror, it is no mirror. A field added
to `Pick` reaches every rendering because none of them enumerates fields.

**What each rendering is still allowed to do:** add its own envelope around this, and choose which
fields to relocate. It may not restate a value the engine already produced.

**This module imports no engine module, on purpose.** The first version named both recommendation
classes in its signature, which created `serialize -> subscribe -> recommend` and made a deferred
import inside `recommend.main` load-bearing without anything saying so — a later import tidy would
have broken the CLI at runtime rather than at lint. The function only needs a dataclass INSTANCE, so
it asks for that structurally and the cycle does not exist.
"""

from __future__ import annotations

from dataclasses import Field, asdict, is_dataclass
from typing import Any, ClassVar, Protocol, runtime_checkable


@runtime_checkable
class DataclassInstance(Protocol):
    """Any dataclass instance. Structural, so no engine module is imported to name one."""

    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


def _jsonable(value: Any) -> Any:
    """Tuples become lists, at every depth. JSON has no tuple."""
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def recommendation_json(rec: DataclassInstance) -> dict[str, Any]:
    """A recommendation as plain JSON-safe data, field for field, with nothing enumerated.

    `asdict` walks the dataclass, so this function cannot fall behind the engine.

    Tuples become lists **at every depth**. The first version converted only the top level, and its
    docstring said "tuples become lists" — so `equivalent_plans[0]["members"]` came back a tuple
    while the sentence everyone would trust said otherwise. Harmless in `json.dumps`, and exactly
    the kind of definition a later reader builds on.

    D-109 is NOT applied here. Scores are rounded once, at the point the engine builds a `Pick`
    (`recommend._pick`), and rounding a second time at the boundary would be a second opinion about
    a number the engine has already published.

    Both recommendation shapes go through here. The subscription rendering was left on its own
    `asdict` call in the first version of this wave, and the W2 review found the consequence
    immediately: deleting `equivalent_plans` from the printed subscription JSON left every test
    green — the same defect the W1 review had just found in the model rendering, reproduced one
    wave later in the sibling path, inside the wave whose purpose was to make it impossible.
    """
    if not is_dataclass(rec) or isinstance(rec, type):
        msg = f"recommendation_json expects a dataclass instance, got {type(rec).__name__}"
        raise TypeError(msg)
    return {key: _jsonable(value) for key, value in asdict(rec).items()}
