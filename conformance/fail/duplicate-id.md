---
record_type: ratification
id: fixture-pass-minimal
status: ratified
---
# Fixture — the id already used by conformance/pass/minimal-ratification.md (`fixture-pass-minimal`) (R3 uniqueness)

<!-- expect: R3 -->

R3's uniqueness branch was DEAD CODE in v4.1: `collect()` keyed its record map by id, so two
records sharing an id collapsed into one entry before the check could ever see them. V4C-32's
adopted text named "duplicate ID" explicitly. Both the bug and the missing fixture were found by
the Quality seat at Increment 12.
