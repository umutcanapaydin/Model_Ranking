---
record_type: wave
id: m13-wave-1-close
status: draft
process_version: v5.0
date: 2026-09-06
---
# Wave-Close Checklist — M13 Wave 1 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The instrument.** Four defects, each reproduced against the shipping code before it was
diagnosed, each with a citing test able to fail. Two independent seats returned BLOCKING; both
blockers are discharged and the discharges are verified by replaying the seats' own mutants.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m13-plan.md` §2 — "W1 — The instrument (risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first on all four: `test_pareto_dominance.py` 7 failed / 7 passed before the fix; `test_startup_schema_validation.py` 1 failed / 3 passed; `test_refresh_attribution_fingerprint.py` 2 failed / 2 passed; `test_runner_accounting.py` 10 failed | ✅ |
| 3 | Review per tier: HIGH → Code-Reviewer + Tester separately | `docs/reviews/m13-wave-1-review.md`, `docs/reviews/m13-wave-1-tester.md` — both `seat: independent`, separate sessions, frozen diff, policy read from the base ref | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | **WAIVED** — see ledger row L1. No auth/PII/payment/crypto/migration surface in this wave; Stage 4.0 covers it at closure per `docs/plans/m13-plan.md` §2 W5 and `docs/closure-checklist.md` | WAIVED |
| 5 | Tester fault-injection: break → RED → reverted byte-identical; every stay-GREEN fault got a new test | `docs/reviews/m13-wave-1-tester.md` — 42 trials, `revert-clean: True` on all, md5-verified, mutations on COPIES under the seat's own temp dir. **Kill-rate 29/39 (74%) at submission**; all ten survivors listed and each closed or recorded. Re-verified after the fixes: the seat's decisive R10 mutant now kills three tests | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-FIX-001 `test_pareto_dominance.py` (both shipping functions) · REQ-FIX-002 `test_startup_schema_validation.py` (the real `_database_unusable`) · REQ-FIX-003 `test_refresh_attribution_fingerprint.py` **plus** `test_refresh.py`'s parametrised real cycle, `("scores","source","arena")` · REQ-FIX-004 `test_runner_accounting.py`, executing `runner`'s own wrappers and exit gate | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None added. The startup probe is an availability control, and its fail direction is CLOSED at boot — asserted negatively by `test_an_artifact_that_ranks_nothing_is_refused` and positively by `test_a_servable_artifact_is_accepted`, which is the false-positive half a fail-closed control needs | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | Tester attests copies-only, in-place revert, md5-verified. **One exception by the author and it is declared, not hidden:** `make format` reformatted 33 files outside this wave's scope, and those files were restored with `git checkout --` per path **before** anything in them was hand-edited. No wave work was lost; the 11 intentional files were excluded from the restore by name | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Pareto dominance is the shared invariant. Producers enumerated by grep over `src/` and `ios/`: exactly two — `recommend.pareto_frontier`, `subscribe._pareto`. No Swift copy. Both fixed; one shared test table runs against both, and the reviewer confirmed reverting either copy alone kills only that engine's cases | ✅ |
| 9b | Scope: planned vs delivered vs deferred | **Planned:** the four defects + the owner's refresh actions. **Delivered:** all four, plus the discharge of two BLOCKING and four MAJOR review findings. **Deferred:** the owner's three actions (kickstart, D-128 ruling, M12 signature) — none is an agent action. `_largest_surface_row_count` duplication carried to W5. **Owner checkpoint commit: ABSENT** (ledger L2, `docs/plans/m13-wave-1-close.md` L2) — the owner is asleep; the tree is staged with a prepared message | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | **VARIANCE.** ~520 insertions / 96 deletions across 11 files plus 6 new files. Over the guideline, and the reason is recorded rather than excused: the four defects are independent and the review round added roughly a third of the total. Not split because splitting a wave after its review has run would invalidate the review. Variance recorded, not excused — `docs/plans/m13-plan.md` §2 W1 | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: make check (0), make lint, make typecheck, pytest 853, swift-test 132, check_records, wave-check-all, conformance-gate, install-check, ./runner · gates SKIPPED: none at the leg level; 12 conditional pytest skips (network contract tests, EPOCH_DATA_DIR) · outcome: shipped, unsigned` | ✅ |

**Ledger rows**

- **L1 — pulled-forward security pass WAIVED.** This wave touches a Pareto predicate, a startup
  probe, a fingerprint field set and a shell accounting library. None is auth, PII, payment, crypto
  or migration. Cost of running it anyway: ~30 min. Stage 4.0 at closure covers the milestone
  surface. *Recorded rather than skipped silently, per V4C-13.*
- **L2 — owner checkpoint commit absent for this wave.** A0.5 expects `wip(m13-w1): checkpoint —
  NOT reviewed` from the owner. He is asleep and instructed the work to continue. The tree is
  staged and a commit message is prepared; **no agent commit was made** (`AGENTS.md` §3: agent
  commit on main = A1 = explicit owner ADR only, and no such ADR exists).
- **L3 — `./runner` is RED on `refresh-status`, and this wave does not close it.** The refresh's
  launchd spawn fault needs `launchctl kickstart` (the owner's action by the plist's own rule) and
  the D-128 threshold needs his ruling. Measured this wave: with today's upstream **no surface
  breaches the 25% limit** (largest move web-dev +17.5%), so the refusal recorded on 2026-08-27 has
  cleared and only the spawn fault remains.

**Escaped-blocker tripwire:** two blockers were caught IN review, not after it. The tripwire is not
triggered; the reviews did their job.

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-06 · Wave commit range:
`335d844..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        src/app/adapter/main.py · src/app/workflows/{recommend,subscribe,refresh,sources}.py
                runner · scripts/runner_verdict.sh (new) · docs/prd.md · INSTALL-MANIFEST.md
                scripts/README.md
                tests/unit/{test_pareto_dominance,test_startup_schema_validation,
                test_refresh_attribution_fingerprint,test_runner_accounting}.py (new)
                tests/unit/{test_recommend,test_refresh,test_api_config,test_stage40_minors,
                test_unbuilt_evidence}.py (existing, corrected)
K.8 contracts:  pareto dominance (2 producers, both fixed) · `confidence_of` signature (W2) ·
                `UNHASHED_ROW_FIELDS` · `runner`'s exit contract (skip now yields 1)
```

## The finding this wave paid for, in one line

**Three separate test fixtures called themselves "a servable artifact" and ranked nothing.** They
passed because the probe they were written against asked only whether tables existed. Correcting
the probe exposed all three at once — and each of their docstrings had already claimed the property
the fixture did not have.
