---
record_type: ratification
id: fixture-pass-minimal
status: ratified
---
# Fixture — the id already used by conformance/pass/minimal-ratification.md (`fixture-pass-minimal`) (R3 uniqueness)

<!-- expect: R3 -->

Why it exists: the validator once keyed its record map by id, so two records sharing an id
collapsed into one entry before R3 could see them. The uniqueness check was dead code, and with no
fixture nothing showed it.
