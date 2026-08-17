"""M7-W1 — every source parser refuses a hostile envelope the same way (REQ-ING-013).

**The defect this exists because of.** `parse_pricing` annotated its payload `dict[str, Any]` and
called `.items()` on it. The annotation ASSERTED the envelope instead of checking it, so valid JSON
that happened to be a list, a string or `null` raised `AttributeError` — which is not `SourceError`,
so it escaped every caller's except clause, killed the build with an undeclared exit code, and left
a schema-valid, `px_median`-empty database at the target path. That is the exact artifact this
milestone exists to make impossible, produced by the builder written to prevent it.

Four of the five parsers were already safe. Being right four times out of five is what makes this
worth a derived test rather than one hand-written case: the parser list comes from the source
registry, so a sixth source is covered here the day it is added, without anyone remembering to.
"""

from __future__ import annotations

import pytest

from app.clients.protocols import SourceError
from app.workflows.sources import REMOTE_SOURCES

HOSTILE_ENVELOPES = [
    pytest.param("[]", id="json-array"),
    pytest.param('"hello"', id="json-string"),
    pytest.param("null", id="json-null"),
    pytest.param("123", id="json-number"),
    pytest.param("true", id="json-bool"),
    pytest.param("{}", id="empty-object"),
    pytest.param("not json at all", id="not-json"),
    pytest.param("", id="empty-body"),
]


def test_the_parser_list_is_not_empty() -> None:
    """A derivation that finds nothing would make every case below vacuously pass."""
    assert len(REMOTE_SOURCES) >= 5


@pytest.mark.parametrize("source", REMOTE_SOURCES, ids=lambda s: s.name)
@pytest.mark.parametrize("payload", HOSTILE_ENVELOPES)
def test_a_hostile_envelope_raises_source_error_and_nothing_else(source: object, payload: str) -> None:
    """SourceError is the ONLY failure a parser may produce.

    Any other exception type escapes `_ingest_sources` and `main()`, which catch specific classes.
    The type of the exception is the contract here, not merely the fact that it failed.
    """
    parse = source.parse  # type: ignore[attr-defined]
    try:
        parse(payload)
    except SourceError:
        return
    except Exception as exc:
        pytest.fail(
            f"{source.name} raised {type(exc).__name__} instead of SourceError; "  # type: ignore[attr-defined]
            "that type escapes the build's except clauses and leaves a partial artifact"
        )
    # Returning normally is acceptable: a parser may legitimately read an empty object as zero
    # rows. The build's own minimum_rows floor is what rejects that, and it is tested separately.
