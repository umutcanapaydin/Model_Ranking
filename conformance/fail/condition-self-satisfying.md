---
record_type: ratification
id: condition-self-satisfying
status: ratified
process_version: v6.3
---
# Fixture — a condition that satisfies itself (C1c)

<!-- expect: C1c -->

The condition names a file that already exists and no anchor inside it, so the row is true the day
it is written and can never fail. Naming `path#a literal string the change adds` is what makes it
checkable.

### Binding conditions

| # | Condition | Owner | Date | Closure artifact |
|---|---|---|---|---|
| 1 | a row that names a file already present | owner | 2020-01-01 | `Makefile` |
