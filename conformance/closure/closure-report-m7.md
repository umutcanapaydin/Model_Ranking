---
record_type: closure
id: closure-report-m7
status: ratified
process_version: v6.3
date: 2026-09-23
---
# Closure Report — M7 (the owner's milestone review pack)

## 1. What shipped (from the approved plan — criteria hash-checked)

| Acceptance criterion (hash-frozen when the plan was approved) | Citing test | CI run | Status |
|---|---|---|---|
| Tenant isolation holds across the gateway | `tests/contracts/test_tenancy.py:41` | 1188342 | ✅ |
| Callback retries are idempotent | `tests/integration/test_callback.py:88` | 1188342 | ✅ |

**Criteria diffs since plan approval:** NONE

## 1a. Per-wave table (one row per wave; each cell links to committed evidence)

| Wave | Risk tier | Reviews (Code-Reviewer + Tester, + security if HIGH) | Findings opened/closed | Test Δ | Escalations | PR |
|---|---|---|---|---|---|---|
| W1 | HIGH | `docs/reviews/m7-wave-1-review.md` + `docs/reviews/m7-wave-1-tester.md` + slice security pass | 3/3 | +14 | none | #41 |
| W2 | MED | `docs/reviews/m7-wave-2-review.md` + `docs/reviews/m7-wave-2-tester.md` | 1/1 | +6 | none | #44 |

## 1b. Decisions made on your behalf (assumption ledger + agent judgment calls)

- Retry budget set to 3: the provider's own documentation caps retries at 3; reversible, one constant (`docs/plans/m7-assumptions.md`, row 2).

## 2. Git record (annotated)

- Commit range: `a1b2c3d..e4f5a6b` · diffstat: `41 files, +1180 / -260` · waves: `2`
- Notable commits, one line each (no AI attribution in any commit — identity is the git author):
  - `3f9e2c1` — the gateway hands the callback a token instead of holding retry state

## 3. Trust telemetry (computed from git against protected refs — never asserted)

| Task type | Post-closure fix rate | Churn (N-day) | Reverts | Findings (sec separately) |
|---|---|---|---|---|
| feature | 0 of 2 | 4% (14-day) | 0 | 4 (1 sec) |

**Agent self-report vs telemetry:** "both waves converged in one review round" — the telemetry agrees:
no reverts and no post-closure fixes.

## 4. Security & invariants

- HIGH waves' security passes on their slices: `docs/reviews/m7-wave-1-review.md` (W1, gateway auth). The release security review runs once, at Stage 5.1; nothing deploys at this close.
- Invariants table current: every row cites its NEGATIVE test — `tests/contracts/test_tenancy.py:41`
- ⛔-glob touches this milestone: none

## 5. Ledgers (nothing silent)

- **Skipped/waived checks:** none — `docs/control-events.csv` has no row for M7
- **Assumption ledger:** the retry budget (`docs/plans/m7-assumptions.md`, row 2)
- **Seed candidates queued:** none
- **Risks queued to M8:** callback token expiry is not load-tested yet (MINOR, W2 review)

## 6. Architecture delta — PROSE (the comprehension-debt countermeasure)

The gateway stopped owning retry state. It now hands the callback a token and forgets, which is
why the retry budget could drop to a constant: nothing accumulates across attempts any more. The
cost is one more round trip on the failure path, paid only when the provider is already failing.
Anyone reading `adapter/` next should know the queue is no longer the source of truth for delivery.

---
*Assembled from raw referents at closure. Owner sign-off: `UA / 2026-09-23`.*
