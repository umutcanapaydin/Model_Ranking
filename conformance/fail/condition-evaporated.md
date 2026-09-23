---
record_type: ratification
id: condition-evaporated
status: ratified
process_version: v4.2
---
# Fixture — a condition whose named closure artifact does not exist (C1b)

<!-- expect: C1b -->

A condition was ratified with an owner, a date and a named artifact; the date passed; the artifact
was never filed; nothing noticed. Frozen here as a regression test. The date below is deliberately
far in the past so this fixture never depends on the clock.

### Binding conditions

| # | Condition | Owner | Date | Closure artifact |
|---|---|---|---|---|
| 1 | the instrument that measures whether our controls are real | owner | 2020-01-01 | `docs/an-artifact-that-was-never-written.md` |
