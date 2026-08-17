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


def envelope_contract_violation(name: str, parse: object, payload: str) -> str | None:
    """Return the violation sentence if `parse` fails with anything other than SourceError.

    Extracted from the test body by the Stage-3b Tester at re-review, for the same reason the
    author extracted `unresolvable_modules` in this wave: while the check lived inline, replacing
    its `pytest.fail(...)` with a `print(...)` left the suite fully green. The wrong-exception arm
    is the entire point of the contract and no test had ever seen it fire, so it could not be
    distinguished from a check that had been switched off.

    Returning normally is acceptable and is NOT a violation: a parser may legitimately read an
    empty object as zero rows, and the build's own `minimum_rows` floor is what rejects that.
    """
    try:
        parse(payload)  # type: ignore[operator]
    except SourceError:
        return None
    except Exception as exc:  # the exception TYPE is exactly what is under test here
        return (
            f"{name} raised {type(exc).__name__} instead of SourceError; "
            "that type escapes the build's except clauses and leaves a partial artifact"
        )
    return None


@pytest.mark.parametrize("source", REMOTE_SOURCES, ids=lambda s: s.name)
@pytest.mark.parametrize("payload", HOSTILE_ENVELOPES)
def test_a_hostile_envelope_raises_source_error_and_nothing_else(source: object, payload: str) -> None:
    """SourceError is the ONLY failure a parser may produce.

    Any other exception type escapes `_ingest_sources` and `main()`, which catch specific classes.
    The type of the exception is the contract here, not merely the fact that it failed.
    """
    violation = envelope_contract_violation(
        source.name,  # type: ignore[attr-defined]
        source.parse,  # type: ignore[attr-defined]
        payload,
    )
    assert violation is None, violation


def test_the_envelope_contract_check_can_fail() -> None:
    """V3C-02: drive the REAL predicate with a parser that breaks the contract on purpose.

    This is what makes the check above falsifiable. It calls the predicate rather than restating
    it, so neutering `envelope_contract_violation` turns this red.
    """

    def _well_behaved(_raw: str) -> tuple[list[object], int]:
        msg = "not an object"
        raise SourceError(msg)

    def _leaky(_raw: str) -> tuple[list[object], int]:
        raise AttributeError("'list' object has no attribute 'items'")

    def _lenient(_raw: str) -> tuple[list[object], int]:
        return [], 0

    assert envelope_contract_violation("good", _well_behaved, "[]") is None
    assert envelope_contract_violation("lenient", _lenient, "[]") is None
    leak = envelope_contract_violation("leaky", _leaky, "[]")
    assert leak is not None
    assert "AttributeError" in leak
