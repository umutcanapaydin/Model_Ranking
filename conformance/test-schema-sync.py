#!/usr/bin/env python3
"""The schema's first-ever reader (GPF-002).

For two versions `schemas/record.schema.json` declared 7 record types while the validator enforced 14,
and nothing noticed because nothing read the schema -- its sole consumer was a byte-compare that
asserts sameness, never correctness. **A contract document with no reader is not a contract; it is a
liability that looks like one.** This test IS the reader: drift between the schema's enum and the
validator's constants fails the build. Exit 0 clean · 1 drift · 2 cannot run.
"""
import json, pathlib, sys

def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "scripts"))
    try:
        from check_records import RECORD_TYPES, REQUIRED, STATUS_FLOW
    except ImportError:
        print("test-schema-sync CANNOT RUN: check_records.py not importable."); return 2
    sf = root / "schemas" / "record.schema.json"
    if not sf.is_file():
        print("test-schema-sync FAIL: schemas/record.schema.json is missing -- regenerate: "
              "python3 scripts/gen_schema.py"); return 1
    schema = json.loads(sf.read_text(encoding="utf-8"))
    bad = []
    enum = set(schema.get("properties", {}).get("record_type", {}).get("enum", []))
    if enum != set(RECORD_TYPES):
        bad.append(f"record_type enum drift: schema has {len(enum)}, validator enforces "
                   f"{len(RECORD_TYPES)} -- diff: {sorted(enum ^ set(RECORD_TYPES))}. "
                   "Regenerate: python3 scripts/gen_schema.py")
    if set(schema.get("required", [])) != set(REQUIRED):
        bad.append("required-fields drift")
    if set(schema.get("properties", {}).get("status", {}).get("enum", [])) != set(STATUS_FLOW):
        bad.append("status enum drift")
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-schema-sync {'FAIL' if bad else 'PASS'}: schema vs validator constants")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
