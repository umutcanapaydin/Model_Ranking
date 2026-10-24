"""#413 (D-207 clause 4): `schemas/record.schema.json` says what `scripts/check_records.py` enforces.

The v7.2 apply removed `conformance/test-schema-sync.py` while D-207 clause 4 kept the schema and its generator, so
nothing would notice the two drifting apart. This is that check, as a project test: the schema's `record_type` and
`status` enums and its required fields equal the validator's constants. On drift, regenerate with
`python3 scripts/gen_schema.py`. It fails closed: an empty constant or enum is a failure, never a vacuous match.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "record.schema.json"


def _validator() -> tuple[set[str], set[str], set[str]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from check_records import RECORD_TYPES, REQUIRED, STATUS_FLOW
    finally:
        sys.path.remove(str(ROOT / "scripts"))
    return set(RECORD_TYPES), set(REQUIRED), set(STATUS_FLOW)


def drift(schema: dict[str, object]) -> list[str]:
    """Each way `schema` differs from the validator; empty when they agree."""
    types, required, statuses = _validator()
    assert types and required and statuses, "the validator's constants are empty: nothing to compare"
    properties = schema.get("properties", {})
    assert isinstance(properties, dict)
    found = []
    if set(properties.get("record_type", {}).get("enum", [])) != types:
        found.append("record_type enum")
    if set(schema.get("required", [])) != required:  # type: ignore[arg-type]
        found.append("required fields")
    if set(properties.get("status", {}).get("enum", [])) != statuses:
        found.append("status enum")
    return found


def test_the_schema_says_what_the_validator_enforces() -> None:
    assert drift(json.loads(SCHEMA.read_text(encoding="utf-8"))) == [], "regenerate: python3 scripts/gen_schema.py"


def test_a_planted_drift_is_found() -> None:
    """The check can fail: a schema missing one record type, one required field and one status is three drifts."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema["properties"]["record_type"]["enum"] = schema["properties"]["record_type"]["enum"][1:]
    schema["required"] = schema["required"][1:]
    schema["properties"]["status"]["enum"] = schema["properties"]["status"]["enum"][1:]
    assert drift(schema) == ["record_type enum", "required fields", "status enum"]
