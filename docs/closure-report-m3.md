---
record_type: ratification
id: closure-report-m3
status: draft
date: 2026-08-15
---
# Closure Report — M3: Subscription-Plan Table + GP v4.3.1 Migration

> Owner's A0.5 milestone-session review pack. Generated 2026-08-15 from committed artifacts
> (4 wave commits d703a77..HEAD; wave checklists + review verdicts cited, not recalled).
> Mode notes: owner amendment (2026-08-15, recorded in m3-plan header) — no stops between waves;
> agent ran all gates per wave (D-106); owner runs out-of-sandbox tests at THIS session.

## 1. What shipped (signed plan m3-plan.md §2 — criteria diffs: TWO, both acknowledged below)

| Criterion | Citing test / gate | Status |
|---|---|---|
| REQ-GP-001 v4.3.1 install correctness | `make check` = lint+typecheck+test+check-records+selftest+install-check+pin-check, all green | ✅ (W0) |
| REQ-SUB-001 plan schema + provenance + counted drops | test_plans_ingest.py (23 tests incl. SQLite-layer CHECK, mid-transaction rollback) | ✅ |
| REQ-SUB-002 curated seed, live-verified, ≥6 plans/≥4 providers | test_seed_dataset_meets_req_sub_002 (the REAL data/plans.yaml is the fixture) | ✅ |
| REQ-SUB-003 staleness disclosed, window as data | test_plans_staleness.py (9) + output half in test_subscribe.py | ✅ |
| REQ-SUB-004 weekly re-verification gate | test_cli_exit_codes_through_real_entrypoint (the exact CI command); contract-tests.yml plan-staleness job (unconditional) | ✅* |
| REQ-REC-007 recommend --subscription, three picks, caps as data | test_subscribe.py (13) incl. cap-boundary through main() | ✅ |
| REQ-REC-008 stale-plan disclosure in output | test_stale_plan_rows_disclosed_in_output + through main() | ✅ |
| REQ-CAL-001 Elo threshold recalibration | test_assistant_budget_floor_uses_elo; method + evidence in docs/reviews/m3-elo-calibration.md | ✅ (closed at closure — owner fetched the live board 2026-08-15) |
| Criteria diff 2 (acknowledged post-sign amendment) | W0.2 deletion list 17→18 (+ the Turkish deck edition, V4C-79) | ✅ |

*Live half runs in CI — the plan-staleness job's first green run is yours to trigger (Actions tab).

## 1a. Per-wave table

| Wave | Tier | Review | Findings o/c | Test Δ | Escalations |
|---|---|---|---|---|---|
| W0 GP v4.3.1 migration | LOW | combined — FAIL→fixed | 1 BLOCKING + 4 MINOR / 5 | 0 | gitleaks FP → W-001 (same-day, this pack) |
| W1 plan schema + seed | LOW | combined — FAIL→fixed | 1 BLOCKING + 4 MINOR / 5 | +20 | none |
| W2 staleness + cadence | LOW | combined — PASS | 2 MINOR / 2 | +10 | none |
| W3 subscription rec + debts | LOW | combined — PASS | 2 MINOR / 2 | +13 | none |
| closure | — | Security-Reviewer **PASS** (0 BLOCKING) + fresh-eyes review of the calibration data edit **PASS** (arithmetic independently recomputed, 0 BLOCKING) | 2+4 MINOR + 3+5 NOTE / 6 | +3 | **stay-green fault** (close_call=8 had no test) — fixed in-session, reported to owner |

## 1b. Decisions made on your behalf (assumption ledger)

- Budget caps (subscription axis): dusuk ≤$10 / orta ≤$25 / sinirsiz — FIRST CALIBRATION, data in
  plans.yaml, one command to change. Cap boundary is INCLUSIVE (a $25 plan is "orta").
- ChatGPT Pro modeled as ONE row at the $100 "from" price (the $200 tier stated in `limits`) —
  the official page shows one Pro card; two third-party sources describe the 2026-04-09 split.
- Google AI Plus EXCLUDED: sources dispute $4.99 vs $7.99 — a disputed price does not enter the
  table (D-107 rule); re-probe queued.
- Plans whose pages name no models rank as UNSCORED and are disclosed, never guessed (7 of 9
  today — see the retrospective's carried question).
- "latest snapshot" Arena semantics, W-001 handling, and all W0 deviations are in the wave
  checklists (docs/plans/m3-wave-*-close.md), each row with its referent.

## 2. File record (git = 4 agent commits, D-106 + V4C-64 trailers)

Net M3: ~2.0k added lines (tooling sync ≈ half); new modules plans.py, subscribe.py, data/plans.yaml;
suite 107 → **152 unit + 5 gated**, coverage steady (~90% touched modules); 18 files deleted (GP-internal).

## 3. Trust telemetry

First mechanically computable milestone NEXT closure (this one creates the tag baseline). Self-report
(METR): 4/4 waves produced review findings (10 applied); most valuable: W0 `.gitignore` mitigation-clobber
(BLOCKING, would have shipped) and W3 cap-boundary stay-green mutant (test added). Tripwires: none.
Council: 0 convened (1 candidate resolved by data rule).

## 4. Security & invariants

Stage 4.0: **PASS** (docs/reviews/m3-security-review.md). INV-1..11 hold (spot-checked by execution).
NEW candidates: INV-12 curated-data atomic loud-fail, INV-13 staleness fails toward disclosure,
INV-14 workflow actions SHA-pinned (grep gate `make pin-check` shipped WITH the rule, V4C-49).
gitleaks: exactly 1 finding = W-001 (ledgered false positive, your call on the scoped allowlist).
Supply chain: every workflow action SHA-pinned incl. the dormant issue-agent's Claude action.

## 5. Ledgers (nothing silent)

- **REQ-CAL-001 CLOSED during this session (was OPEN):** you ran the corrected fetch; 389 live rows
  (one snapshot, 2026-08-12) drove a DATA edit in categories.py — floor 1300→**1400** (1300 admitted
  57% of the board), close_call 5→**8** (at 5 Elo, 100% of top-60 pairs still have overlapping 95%
  CIs — the old value under-disclosed real ties), value_window 30 kept and now justified. Method,
  distribution table and reproduce-command: docs/reviews/m3-elo-calibration.md. No criteria diff.
- **ESCALATE-NOW class, handled in-session (AGENTS.md §3):** the closure review found `close_call=8`
  was a stay-green fault — reverting it to 5 left the whole suite green, i.e. the calibration was
  undefended. Mandatory test added (`test_close_call_threshold_is_the_calibrated_elo_value`), both
  mutants re-verified RED, and the alias constants in recommend.py are now asserted against the
  category record so they cannot drift. Same review also: corrected an overstated sentence in the
  calibration record (9 also satisfies the stated rule; we ship the conservative 8), added the
  analysis script so every published figure is recomputable, and fixed three docs that still said
  REQ-CAL-001 was open.
- **Skipped:** live contract tests (sandbox rule — CI/your machine, unchanged); first CI runs of
  plan-staleness + governance-contract legs await your trigger.
- **K.10 CI diffs for your review at this commit:** contract-tests.yml (plan-staleness job, plans in
  smoke, SHA-pins), ci.yml (SHA-pins), issue-agent.yml (SHA-pins), governance-contract.yml
  (install-check leg), Makefile (`check` now 7 gates incl. pin-check).
- **Queued to M4:** registry expansion for plan-named models (GPT-5.6 family; Claude 4.6 Opus and
  MiniMax M2.5 now visible in live SWE-bench drops); Google AI Plus re-probe; Epoch (your ruling);
  retrospective's carried product question; .governed-records widening to docs/reviews/ (gate-definition
  change — yours); GP-upstream notes (wave-check target missing; scripts/ lint debt).

## 6. Architecture delta — PROSE

This milestone taught the engine to answer the question the product was always aimed at: not
"which model" but "which subscription should I buy". The answer layer is deliberately thin and
honest. A curated YAML table — the only place this data exists in machine-readable form anywhere —
is validated like code, ingested atomically like any source, and carries its own thresholds as
data: the staleness window, and the budget tiers in monthly dollars. A plan's quality is never
invented: it is the best benchmark score among the models the provider's own page explicitly
names, linked through the same registry that reconciles every other source; a page that names
nothing leaves its plan visibly unscored rather than silently ranked. Verification is a product
feature with two clocks: a deterministic one inside the engine (stale rows disclosed relative to
the ingest stamp, corrupt dates failing loud rather than fresh) and a wall clock in CI (the weekly
cron goes red when the table needs a re-probe — the failure IS the reminder). The process floor
moved with it: the repo is now a manifest-correct v4.3.1 install whose gates actually fire, in
English, with attributable agent commits and SHA-pinned CI. Break-glass points for a future
maintainer: the plan table's honesty depends on the entry discipline (probe live, record the URL
and date, exclude disputes), and the subscription answer's usefulness depends on registry coverage
of the models providers name — today that is the moat's thinnest wall, and the retrospective hands
you the question it raises.

---
*Owner sign-off: ______ / date: ______*
