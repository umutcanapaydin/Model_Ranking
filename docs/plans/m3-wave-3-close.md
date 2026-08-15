# Wave-Close Checklist — M3 Wave 3 (subscription recommender + carried debt; v4.1 template)

> Wave scope: m3-plan.md §3 W3 (REQ-REC-007/-008, REQ-CAL-001, ArenaClient cleanup, Actions SHA-pin).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier: **LOW** (no authz/secrets/crypto; CI files touched = K.10 owner-review surface, flagged; SHA-pins verified against upstream tags by the reviewer) | m3-plan.md:10 | ✅ |
| 2 | Dev-test loop ran; full `make check` green: ruff, black, mypy (45 files), **149 passed + 5 gated-skip**, check-records, selftest, install-check | run log 2026-08-15 | ✅ |
| 3 | LOW → ONE combined fresh-eyes reviewer. Verdict **PASS**, 2 MINOR, both closed in-wave: M1 budget-cap boundary mutation (`<=`→`<`) SURVIVED the suite → boundary test added ($25 plan at cap 25, through main()); mutant re-run now RED (1 failed) then restored green; M2 REQ-REC-008 not asserted through main() → stale row added to the CLI test. Reviewer also proved: tie-break determinism (both insert orders), NULL-cap impossibility (schema CHECK), old-schema DB → exit 2, model path byte-untouched, all 3 action SHAs resolve to the claimed tags (fake-pin check) | review transcript; test_plan_priced_exactly_at_cap_is_eligible_through_cli | ✅ |
| 4 | *(plan-tag)* HIGH slice | N/A — LOW wave | ✅ |
| 5 | Fault-injection: (a) _unscored forced empty → 2 tests RED (incl. real entrypoint); (b) cap `<`-mutation survived → treated as a live stay-green fault → MANDATORY new test added (V3C-72), mutant re-verified RED; all reverts in-place md5-identical (e1b92f…83) | reviewer log + this session mutant re-run | ✅ |
| 6 | Criteria → citing tests through the LIVE entrypoint: REQ-REC-007 → test_three_labeled_plan_picks…, test_budget_cap_filters…, test_cli_subscription_through_real_entrypoint (exit 0/1/2), caps-as-data test_missing_or_malformed_budget_caps_fail_loud; REQ-REC-008 → test_stale_plan_rows_disclosed_in_output + through main() in test_plan_priced_exactly_at_cap… | tests/unit/test_subscribe.py (12 tests) | ✅ |
| 7 | Security invariants: no new ⛔ surface; supply-chain HARDENED — every workflow action SHA-pinned (checkout v4.4.0, setup-python v5.6.0, gitleaks-action v2.3.9), each SHA independently resolved by the reviewer against upstream tags; one TODO remains on the DISABLED issue-agent's Claude action (Layer-2 OFF since M1 — ledgered) | ci.yml:25-57, contract-tests.yml:37-53, issue-agent.yml:40; review §4 | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work; in-place md5 reverts | rows 3/5 | ✅ |
| 9c | Invariant hardening | N/A | ✅ |
| 9b | Scope row: PLANNED = subscription recommender + stale disclosure + Elo recalibration + ArenaClient cleanup + SHA-pin. DELIVERED = all EXCEPT Elo recalibration; plus live e2e demo (real SWE-bench + seed: three plan answers; 7 plans honestly unscored — GPT-5.6*/Claude-page names have no benchmark presence yet, registry extension queued M4). **CARRIED (open criterion): REQ-CAL-001** — needs live Arena distribution; sandbox+WebFetch cannot reach the HF filter endpoint (4 attempts ledgered), owner-side fetch pending (curl command delivered twice; first had my config error, corrected). Resolution at the closure session: calibrate if data lands, else owner descopes to M4 as an acknowledged criteria diff | m3-plan.md §3 W3; this file | ✅ |
| 9a | Economy: ~14 files, ~700 added lines (module+tests+CI pins). Token spend within plan §5 W3 ≈ 70k | git diff --stat | ✅ |
| 9 | RUN LINE — gates run: ruff · black · mypy · pytest(149+5skip) · check-records · selftest · install-check · mutant-probe(cap boundary) · outcome: **shipped (REQ-CAL-001 carried)**. SKIPPED: live contract tests (standing rule → CI/owner); Arena live probe (endpoint unreachable from here — ledgered above). K.10 NOTE: ci.yml + contract-tests.yml + issue-agent.yml diffs (SHA-pins, plan-staleness job, plans in smoke) → owner reviews at milestone commit | this row | ✅ |

**Escaped-blocker tripwire:** none.

Filled by: Claude (Cowork lead agent, D-106) · Date: 2026-08-15 · Wave commit range: `4cb9da7..HEAD` (this commit)
