---
record_type: wave
id: m4-wave-1-close
status: ratified
date: 2026-08-15
---
# Wave-Close Checklist — M4 Wave 1 (registry expansion + authoring path; v4.1 template)

> Wave scope: m4-plan.md §3 W1 (REQ-CAN-004).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier: **LOW** (curated data table + tests; no authz/secrets/crypto/egress). Note: the registry IS the product's core IP, so the wave was reviewed as data-critical rather than cosmetic | m4-plan.md:6 | ✅ |
| 2 | Dev-test loop: probe live → write property tests → author rules → run → fix → re-run. Full `make check` green: ruff, black, mypy (45 files), **155 passed + 5 gated**, check-records, selftest, install-check, pin-check | run log 2026-08-15 | ✅ |
| 3 | LOW → ONE combined fresh-eyes reviewer. Verdict **FAIL: 4 BLOCKING + 7 MINOR** — all closed in-wave. B1 `deepseek-v4-flash` folded into the base model (own price AND own Elo) → own rule; B2 the record's coverage row was wrong (coding was 2/9 before, not 1/9) → corrected AND the drop explained as a correctness fix; B3 date stamps were BLOCKED not absorbed, losing a live Qwen3 Max score row → version-vs-date guard rewritten (`[.\-p]\d(?!\d)`); B4 `gpt-5-pro` swallowed 5.2/5.4/5.5/5.6 Pro (four generations of prices in one id) → tightened, versioned Pros now drop and are counted. MINORs: Fireworks `p` notation, `glm-5-code`, `M2.5-lightning`, image/live products, `grok-4.20-multi-agent`, an unexplained char-class edit, and the narrowness of the first two property tests — all fixed or disclosed | review transcript; 32/32 probe table green; tests/unit/test_registry.py | ✅ |
| 4 | *(plan-tag)* HIGH slice | N/A — LOW wave | ✅ |
| 5 | Fault-injection (reviewer, in-place, md5-verified 2b6892…1ca4): (a) widen+reorder the gemini rule → `test_every_rule_canonicalizes_to_itself` RED; (b) duplicate a canonical id → `test_no_duplicate_canonical_ids_or_patterns` RED. Both restored byte-identical; suite green after | reviewer log | ✅ |
| 6 | REQ-CAN-004 citing tests: `test_every_rule_canonicalizes_to_itself` (swallow property), `test_no_duplicate_canonical_ids_or_patterns`, and — added because the review proved the first two too narrow — `test_live_names_resolve_to_the_right_model`, a 41-entry corpus of strings real sources emitted, including every wrong mapping this review found | tests/unit/test_registry.py | ✅ |
| 7 | Security invariants: none new; no new input surface (the table is in-repo curated data, no network path added). Registry changes are ranking-correctness surface, covered by rows 3/5/6 | — | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work; reviewer restored from a `/tmp` byte copy | row 5 | ✅ |
| 9c | Invariant hardening: the swallow property is now enforced FROM the table itself rather than per-rule by hand — every future rule inherits the guard | tests/unit/test_registry.py | ✅ |
| 9b | Scope row: PLANNED = property test, rules from a live drop-list probe, drop-list report. DELIVERED = all three (29 rules added, 2 removed/retargeted at review, 1 swallow defect fixed), plus the live-name corpus test and a corrected record. DEFERRED = none. **Measured outcome:** models 42→71, score rows matched 190→218, plan-name drops 2→**0**, assistant plan coverage 2/9→**3/9**, coding 2/9→**1/9** (a correction — see the record) | docs/reviews/m4-w1-registry-droplist.md | ✅ |
| 9a | Economy: 5 files, ~250 net lines (mostly the rule table + corpus). Token spend within plan §5 W1 ≈ 70k line, though the review ran long (deliberate: this table is the product's IP) | git diff --stat | ✅ |
| 9 | RUN LINE — gates run: ruff · black · mypy · pytest(155+5skip) · check-records · selftest · install-check · pin-check · live drop-list probe (LiteLLM + SWE-bench + Aider live; Arena from the owner's staged pages) · outcome: **shipped**. SKIPPED: live contract tests (standing sandbox rule → CI/owner); OpenRouter aliases could not be probed from here (openrouter.ai unreachable) — its aliases enter the drop list only in CI, recorded as a known blind spot of this probe. **Control-bypass ledger: none.** **Tooling incident recorded:** a same-length mutation (`8.0`→`5.0`) inside one second poisoned Python's bytecode cache, so an earlier fault-injection read a stale module; caches are now cleared before every probe and the lesson goes to EXPERIENCE | this row | ✅ |

**Escaped-blocker tripwire:** none (all four BLOCKING were caught inside the wave, by the wave's own reviewer).

Filled by: Claude (Cowork lead agent, D-106) · Date: 2026-08-15 · Wave commit range: `0f840a9..HEAD` (this commit)
