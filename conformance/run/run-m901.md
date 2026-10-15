# Run — m901

<!-- A filled run record, the positive fixture for `scripts/run_check.py` (`test-run-check.py`):
     one heavy milestone running, one wave stacked on the shipped wave-close fixture, one queued,
     one stop the run continued past. -->

Mode: heavy
Started: 2026-10-13
Ended: open
Integration branch: `integration/run-m901` · PR: #902
Plan PR: #901
Rulings: none

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | M901 | 0123456789abcdef0123456789abcdef01234567 | conformance/run/m901-plan.md | running |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| m901-w2 | wave/m901-w2 | #903 | conformance/wave/m901-wave-2-close.md | stacked |
| m901-w3 | wave/m901-w3 | #904 | docs/plans/m901-wave-3-close.md | stopped |
| m901-w4 | wave/m901-w4 | none | none | queued |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-13 23:40 | m901-w3 | zone-or-criterion | REQ-X-003 says "recent orders": the last 30 days, or since the last login? Should the sanitizer strip `<script>` tags or reject the request? | m901-w4 |

## For the owner

Merge #901 (the plans), then #902 as a merge commit; answer the m901-w3 question.
