---
record_type: closure
id: closure-report-m7
status: ratified
process_version: v6.0
date: 2026-09-22
---
# Closure Report — M7

## 1. What shipped (from the signed plan — criteria hash-checked)

| Acceptance criterion (hash-frozen at plan-sign) | Citing test | CI run | Status |
|---|---|---|---|
| Tenant isolation holds across the gateway | `tests/contracts/test_tenancy.py:41` | 1188342 | ✅ |
| Callback retries are idempotent | `tests/integration/test_callback.py:88` | 1188342 | ✅ |

## 1a. Per-wave table

| Wave | Scope | Reviewer | Tester | Close checklist |
|---|---|---|---|---|
| W1 | gateway auth | Code-Reviewer | fault-injection RED confirmed | `docs/plans/m7-wave-1-close.md` |
| W2 | callback path | Code-Reviewer | fault-injection RED confirmed | `docs/plans/m7-wave-2-close.md` |

## 1b. Decisions made on your behalf

| Decision | Why | Reversible? |
|---|---|---|
| Retry budget set to 3 | the provider's own docs cap at 3 | yes, one constant |

## 2. Git record (annotated)

Range `a1b2c3d..e4f5a6b`, 34 commits, 2 waves. Diffstat 41 files, +1180 / -260.

## 3. Trust telemetry (mechanical — script-computed vs protected refs)

| Metric | Value | Referent |
|---|---|---|
| criteria with a citing test | 2 of 2 | `make test` run 1188342 |
| gates skipped | 0 | wave checklists, row 9 |

## 4. Security & invariants

Security review PASSED at 4.0 before deploy. Two invariants added, both with negative tests.

## 5. Ledgers (nothing silent)

Warnings ledger: 1 raised, 1 decided. Bypass ledger: none this milestone.

## 6. Architecture delta — PROSE

The gateway stopped owning retry state. It now hands the callback a token and forgets, which is
why the retry budget could drop to a constant: nothing accumulates across attempts any more. The
cost is one more round trip on the failure path, paid only when the provider is already failing.
Anyone reading `adapter/` next should know the queue is no longer the source of truth for delivery.
