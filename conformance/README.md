# Conformance fixtures (V4C-32)

`pass/` — the smallest records that MUST validate clean.
`fail/` — one fixture per blocking rule; each declares its expected diagnostic on an
`<!-- expect: RULE -->` line. `check_records.py --self-test` runs the whole corpus and FAILS if a
fail fixture does not produce its declared rule.

This is our own fault-injection doctrine (V3C-72: break it → confirm RED → revert) applied to the
validator itself. It exists because Increment 11 found that `make check-templates` — a ratified
gate — had never executed once: a control nobody exercises is a control nobody has.

Adding a blocking rule to `check_records.py` REQUIRES adding its fail fixture in the same change.
