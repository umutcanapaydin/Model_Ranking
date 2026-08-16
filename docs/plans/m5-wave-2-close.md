---
record_type: wave
id: m5-wave-2-close
status: ratified
date: 2026-08-16
---
# Wave-Close Checklist — M5 Wave 2

> Filled from `docs/wave-checklist.template.md`. Scope: M5 plan §3 W2 — effort-aware score
> identity, migration, registry resolution, data-owned ranking level, comparable range evidence,
> and Turkish disclosure.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded; migration and input parsing make W2 HIGH | `docs/plans/m5-plan.md` §4 records W2 HIGH | ✅ |
| 2 | Per-agent implement → test → self-review → fix loop ran | checkpoint `964a389`, blocker-fix commit `795facb`; focused 27 passed and full 241 passed / 5 expected skips in `docs/reviews/m5-wave-2-tester.md` | ✅ |
| 3 | HIGH review: separate fresh Code Reviewer and Tester; two facts countersigned | original BLOCKING `docs/reviews/m5-wave-2-review.md`, independent PASS `docs/reviews/m5-wave-2-rereview.md`, Tester PASS `docs/reviews/m5-wave-2-tester.md`; reviewer independently countersigned D-109 raw/published values and same-identity `70` versus foreign `99/98` evidence | ✅ |
| 4 | HIGH pulled-forward security/data-boundary pass | finite/range parsing, six-value effort domain, explicit-over-suffix precedence, unknown/conflict accounting, pre-wave migration, release-date isolation, and same-harness/source evidence boundaries are covered in both PASS records | ✅ |
| 5 | Fault injection on load-bearing behaviors | Tester killed 3/3 manual mutants: effort-filter merge, range-disclosure removal, harness/source widening; all RED, then in-place byte-identical SHA-256 restore; `docs/reviews/m5-wave-2-tester.md` | ✅ |
| 6 | Every touched acceptance criterion has a live-entry citing test | REQ-CAN-005: `tests/unit/test_schema.py:54-100`, `tests/unit/test_effort.py:25-77,325-398`; REQ-REC-011: model and subscription CLI `tests/unit/test_effort.py:245-300`; exact evidence in re-review and Tester records | ✅ |
| 7 | New/changed security invariants have negative tests | milestone data-boundary invariants plus `tests/unit/test_effort.py` reject unknown/defaulted effort, conflicting evidence substitution, wrong category effort, cross-harness/source range, and release-date ageing | ✅ |
| 8 | No checkout/restore on uncommitted work | Tester used only disposable exact-ref archive, in-place patches, and pre/post SHA-256; original repo remained read-only | ✅ |
| 9c | Shared security invariant producer enumeration | N/A — no auth, tenancy, or money invariant changed; effort producers (`migrate`, parser, resolver, store, rank, coverage, publish) and citing tests are enumerated in the two PASS review records | WAIVED — domain not touched |
| 9b | Scope and checkpoint | planned W2 delivered in `96ba91d..795facb`: effort schema/migration, suffix/column resolver, data-owned `high` policy, high-only model/plan/coverage selection, comparable range and disclosure; public DeepSWE ingest remains W3 as signed; checkpoint `964a389` exists | ✅ |
| 9a | Economy | 14 files, +1222/−63 exceeds the advisory ~400-line valve because the new 398-line acceptance suite, migration/parser implementation, and preserved BLOCKING + PASS audit records dominate; within signed W2 ≈80k / M5 ≈500k budget | ✅ — variance recorded |
| 9 | **RUN LINE — gates run:** exact-ref real-bundle focused 27 · full pytest 241 pass/5 skip · 90% coverage · ruff · black · mypy · 3 fault injections · Code re-review · Tester review · `make wave-check` · **gates SKIPPED:** five opt-in network contracts (existing expected skips; no network), mechanical mutation runner (not wired; HIGH advisory only), auth/tenancy/money sweep (N/A) · **tokens/cost:** within signed M5 budget · **outcome: shipped** | This row; detailed outputs and exact hashes in `docs/reviews/m5-wave-2-tester.md` | ✅ |

Escaped-blocker tripwire: the initial Code Review blocked four behaviors and one documentation
issue. All were fixed before the separate re-review PASS and Tester PASS; no blocker escaped the
wave and no MINOR remains.

Filled by: `Codex` · Date: `2026-08-16` · Wave commit range: `96ba91d..795facb`
