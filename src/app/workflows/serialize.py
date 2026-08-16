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
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.workflows.recommend import Recommendation


def recommendation_json(rec: Recommendation) -> dict[str, Any]:
    """A recommendation as plain JSON-safe data, field for field, with nothing enumerated.

    `asdict` walks the dataclass, so this function cannot fall behind the engine. Tuples become
    lists because JSON has no tuple; that is a format conversion, not a content decision.

    D-109 is NOT applied here. Scores are rounded once, at the point the engine builds a `Pick`
    (`recommend._pick`), and rounding a second time at the boundary would be a second opinion about
    a number the engine has already published.
    """
    data = asdict(rec)
    return {key: list(value) if isinstance(value, tuple) else value for key, value in data.items()}
