---
record_type: wave
id: m4-wave-3-close
status: ratified
date: 2026-08-15
---
# Wave-Close Checklist — M4 Wave 3 (coverage, source health, Epoch; v4.1 template)

> Wave scope: m4-plan.md §3 W3 (REQ-SUB-005, REQ-ING-010, REQ-ING-011).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier: **LOW** (read-only derived metrics + one CI leg; no authz/secrets/crypto/egress) | m4-plan.md:6 | ✅ |
| 2 | Dev-test loop ran; full `make check` green: ruff, black, mypy (49 files), **180 passed + 5 gated**, check-records, selftest, install-check, pin-check | run log 2026-08-15 | ✅ |
| 3 | LOW → ONE combined fresh-eyes reviewer. Verdict **PASS**, 0 BLOCKING, 3 MINOR — all closed in-wave: M1 a malformed `run_date` made a stale source report "ok" (failing toward freshness — the wrong direction for a health check) → unknown age is now STALE, with `age_days: null` still saying why; M2 the "one definition of old" comment overclaimed (same window, two clocks) → both the code comment and the record now state which clock each uses; M3 dead per-category re-query + a `KeyError` path → hoisted and `.get(pid, pid)`. Reviewer also added the live-shape case the tests missed (links present but resolved to NULL) → test added | review transcript; coverage.py:29-35, :100-118; test_coverage.py | ✅ |
| 4 | *(plan-tag)* HIGH slice | N/A — LOW wave | ✅ |
| 5 | Fault-injection (reviewer, in-place, md5 467e25…9743): (a) count a plan scoreable on links alone → 2 tests RED; (b) stale comparison `>`→`>=` → boundary test RED; (c) CLI always returns 0 → CLI test RED. Restored byte-identical | reviewer log | ✅ |
| 6 | Criteria → citing tests: REQ-SUB-005 (test_coverage_counts_and_explains_every_unscoreable_plan, test_links_that_all_dropped_count_as_no_links, the CLI test through `main()`), REQ-ING-011 (test_source_health_flags_a_source_that_went_quiet, boundary test, unparseable-date test, window-parity test). **REQ-ING-010 has NO citing test because it is not implemented — see row 9b** | tests/unit/test_coverage.py (9 tests) | ✅ |
| 7 | Security invariants: no new input or network surface; the metric is provably read-only (reviewer ran it against a `mode=ro` connection); health now fails toward disclosure | review §5(c) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | rows 3/5 | ✅ |
| 9c | Invariant hardening: coverage's "scoreable" predicate was checked against what the ENGINE can actually rank (`subscribe.plan_ranking`) — identical sets, so the metric cannot drift into measuring a parallel definition of the product | review §3 | ✅ |
| 9b | Scope row: PLANNED = coverage metric, source health, Epoch ingestion, fresh-benchmark investigation. DELIVERED = coverage + health (measured, CI-wired, reported) and the investigation with evidence. **NOT DELIVERED — REQ-ING-010 (Epoch) and the fresh-benchmark ingestion: epoch.ai and huggingface.co are proxy-403 from this container (reviewer reproduced all five probes independently), and writing a parser against an unseen shape is the FP-M2-2 defect this project paid for twice.** Two owner-fetch commands delivered 2026-08-15; the criteria stay OPEN and visible in docs/reviews/m4-w3-source-health.md. If the fetch does not land this milestone they become an acknowledged criteria diff to M5 | docs/reviews/m4-w3-source-health.md §3-4 | ✅ |
| 9a | Economy: 4 files, ~380 net lines. Token spend under the plan §5 W3 ≈ 90k line (no ingestion code written) | git diff --stat | ✅ |
| 9 | RUN LINE — gates run: ruff · black · mypy · pytest(180+5skip) · check-records · selftest · install-check · pin-check · live source probes (SWE-bench all 6 boards, Epoch docs, 3 alternative-benchmark probes) · outcome: **shipped with one criterion OPEN**. SKIPPED: live contract tests (standing rule). **Findings recorded, not fixed here:** SWE-bench has published nothing since 2026-02-26 on ANY board and Aider since 2025-10-03 — the coding category rests on frozen evidence; that is now a measured number in every run, not a demo surprise. Pre-existing, out of scope: `scripts/` fails repo-wide ruff/black (the gate is scoped to `src tests`, so scripts drift is structurally invisible — GP-upstream note) | this row | ✅ |

**Escaped-blocker tripwire:** none.

Filled by: Claude (Cowork lead agent, D-106) · Date: 2026-08-15 · Wave commit range: `45dc1f9..HEAD` (this commit)
