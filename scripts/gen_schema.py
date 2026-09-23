#!/usr/bin/env python3
"""Regenerate schemas/record.schema.json from the validator's own constants.

A hand-written schema once listed half the record types the validator enforced, and its only reader
was a byte-compare that asserted sameness, never correctness. One source of truth now: the
constants in scripts/check_records.py. `conformance/test-schema-sync.py` fails on drift.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_records import OPTIONAL, RECORD_TYPES, REQUIRED, STATUS_FLOW

schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$comment": ("GENERATED from scripts/check_records.py constants -- do not hand-edit. "
               "conformance/test-schema-sync.py fails on drift. "
               "Regenerate: python3 scripts/gen_schema.py"),
  "title": "Governance record frontmatter",
  "type": "object",
  "required": list(REQUIRED),
  "properties": {
    "record_type": {"enum": sorted(RECORD_TYPES)},
    "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9.\\-]{2,63}$"},
    "status": {"enum": list(STATUS_FLOW)},
    **{k: {} for k in OPTIONAL},
  },
  "additionalProperties": False,
}
out = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "record.schema.json"
out.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(RECORD_TYPES)} record types)")
