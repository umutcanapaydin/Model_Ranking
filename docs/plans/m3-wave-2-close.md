---
record_type: wave
id: m3-wave-2-close
status: ratified
date: 2026-08-15
---
# Wave-Close Checklist — M3 Wave 2 (staleness + verification workflow; v4.1 template)

> Wave scope: m3-plan.md §3 W2 (REQ-SUB-003/-004).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier: **LOW** (no authz/secrets/crypto/egress; CI file touched = K.10 owner-review surface, flagged) | m3-plan.md:10 | ✅ |
| 2 | Dev-test loop ran; full gate green: ruff, black, mypy (43 files), **135 passed + 5 gated-skip**, check-records | run log 2026-08-15 | ✅ |
| 3 | LOW → ONE combined fresh-eyes reviewer. Verdict **PASS**, 2 MINOR + 2 OBS, all addressed in-wave: M1 corrupt-DB date silently masked staleness → now FAILS LOUD (SourceError) + citing test; M2 local-TZ date.today() → explicit UTC; OBS-1 prd REQ-SUB-003 status wording corrected; OBS-2 pre-existing scripts/ lint noted (GP-shipped files, out of wave). Reviewer proved boundary parity (age==30 fresh / 31 stale on BOTH paths) and CI-job independence | review transcript; plans.py:216-221,265-268; test_corrupt_db_date_fails_loud_never_fresh | ✅ |
| 4 | *(plan-tag)* HIGH slice | N/A — LOW wave | ✅ |
| 5 | Fault-injection: (a) strict `>` flipped to `>=` → boundary test RED; (b) check_staleness forced empty → 2 tests RED; both restored md5-identical (cc8fbd…58), suite back to green | reviewer log | ✅ |
| 6 | Criteria → citing tests through LIVE entrypoints: REQ-SUB-003 → test_stale_plans_is_deterministic…, test_boundary…, test_window_is_read_from_data… + window-as-data test_missing_staleness_window_fails_loud; REQ-SUB-004 → test_cli_exit_codes_through_real_entrypoint (the exact CI command, exit 0/1/2) + test_shipped_seed_is_fresh_on_entry_day; CI wiring contract-tests.yml plan-staleness job | tests/unit/test_plans_staleness.py (8 tests) | ✅ |
| 7 | Security invariants: none new; cadence job is unconditional (no `if:`/`continue-on-error` — the false-pass class explicitly avoided); stale verdict fails TOWARD disclosure (corrupt dates now loud) | contract-tests.yml:31-51; review §6 | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work; in-place md5 reverts | row 5 | ✅ |
| 9c | Invariant hardening | N/A | ✅ |
| 9b | Scope row: PLANNED = window-as-data, flags in exports, cadence job, contract-style tests. DELIVERED = window-as-data (top-level staleness_days REQUIRED, plan_config table), deterministic stale_plans (same proxy doctrine as stale_notice, blind spot documented), wall-clock --check-staleness CLI + weekly CI job, 9 new tests. DEFERRED (per plan, to W3): stale flags in RECOMMENDATION OUTPUT (REQ-REC-008) — prd status corrected to say so. K.10 NOTE: contract-tests.yml diff (new plan-staleness job) → owner reviews at milestone commit | m3-plan.md §3 W2; prd.md §10 | ✅ |
| 9a | Economy: 6 files, ~230 added lines — within bounds. Token spend within plan §5 W2 ≈ 50k | git diff --stat | ✅ |
| 9 | RUN LINE — gates run: ruff · black · mypy · pytest(135+5skip) · check-records · outcome: **shipped**. SKIPPED: live contract tests (standing rule → CI/owner). Ledger: scripts/check_records.py + scripts/journey.py fail whole-repo ruff/black (PRE-EXISTING, GP-shipped, untouched; repo gate scope is src+tests) — handed to GP-upstream note in EXPERIENCE at closure (V4C-71 shape) | this row | ✅ |

**Escaped-blocker tripwire:** none.

Filled by: Claude (Cowork lead agent, D-106) · Date: 2026-08-15 · Wave commit range: `323a251..HEAD` (this commit)
