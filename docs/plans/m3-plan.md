# M3 Plan — Subscription-Plan Table (the moat) + GP v4.3.1 Migration

**Status:** SIGNED — owner approved 2026-08-15 with ONE AMENDMENT (owner directive, recorded):
waves run WITHOUT stopping; the agent runs its own test gates per wave; the OWNER runs the
out-of-sandbox/live tests after the milestone (carries forward the M2 no-per-wave-owner-touch shape).
**Q1-Q4 locked 2026-08-15:** Q1 = core four (OpenAI, Anthropic, Google, Perplexity) · Q2 = USD/US-first
(TR price noted only where a page states it; NO currency conversion) · Q3 = 30-day staleness window
(as data) · Q4 = weekly CI staleness check riding the existing cron.
**Date:** 2026-08-15 · **Risk tier:** LOW (public data only; no auth/PII/payment) · **Mode:** A0.5 + D-106 (agent runs gates + commits at green boundaries)
**Process baseline:** General Pipeline **v4.3.1** (replaces v4.2 — owner directive, 2026-08-15). New committed files are ENGLISH (V4C-79); agent commits carry the agent trailer (V4C-64, per D-106).
**Scope decisions:** Epoch AI ingestion → **M4** (owner answered 2026-08-15; option "defer to M4"). Subscription table is the whole milestone.
**Reviews per wave:** ONE combined reviewer (LOW, V3C-78); Security review at closure (BLOCKING). Mid-milestone questions → council-instead-of-owner (M2 amendment carried forward), except the escalate-NOW list.

---

## 0. Design notes + gap analysis (V3C-50 — before any code)

**What exists (M2):** 5 live sources, canonical registry, per-category ranking (coding/assistant),
budget-aware recommend CLI with honesty disclosures. All benchmark/pricing data is *per-model,
per-token* — the engine can say "use Claude 4.5 Opus" but cannot answer the question real users ask:
**"which $20/month subscription should I buy?"**

**Gap to close:** a curated **subscription-plan table** — provider, plan name, monthly price,
currency, included models, usage limits, region availability, source URL, **last_verified date** —
plus the plan↔canonical-model mapping. Both M0 research reports converged: **no machine-readable
feed for this exists anywhere**; the curated mapping is the defensible asset. Because prices are
volatile (several changed within 90 days), *verification is part of the product*: every row carries
provenance + last_verified, stale rows are disclosed exactly like stale benchmarks (M2 doctrine),
and a re-check cadence is wired into CI as a scheduled reminder job.

**Data entry rule (fixture lesson, paid for twice in M2):** every value in the seed dataset is
probed against the provider's live pricing page (WebFetch) on the day it is entered — no invented
values. The owner spot-checks at the milestone gate (out-of-sandbox).

**Process gap (v4.3.1 install-check, run 2026-08-15 against the repo at 805718b):** the v4.2
install is incomplete in both directions — **6 PROJECT paths missing (M1)**, **17 GP-INTERNAL files
leaked (M2)**. Fixed as W0 before any product code.

## 1. Goal (1 sentence)

Given a budget and a use case, the engine answers "which subscription plan should I buy" from a
curated, provenance-carrying, staleness-honest plan table — and the repo becomes a correct
GP v4.3.1 installation.

## 2. Acceptance criteria (each gains a citing test, V3C-02)

- REQ-SUB-001 `plans` + `plan_models` schema: provider, plan, monthly price (>0 CHECK), currency, region, limits text, source_url, last_verified; plan→canonical-model links via the registry
- REQ-SUB-002 curated seed dataset (YAML in repo, data-not-code) ingested transactionally like any source; ≥6 plans across ≥4 providers (initial scope: OpenAI, Anthropic, Google, Perplexity — Q1)
- REQ-SUB-003 every ingested plan row carries source_url + last_verified; rows older than the staleness window (Q3) are flagged, never hidden
- REQ-REC-007 `recommend --subscription --budget dusuk|orta|sinirsiz --task coding|assistant` → three labeled plan picks reusing the existing budget/quality logic where the plan's included models carry the category scores
- REQ-REC-008 stale-plan disclosure in output (same honesty contract as stale_notice); a plan whose last_verified exceeds the window says so
- REQ-SUB-004 re-check cadence: scheduled CI job (or documented owner routine — Q4) that fails/reminds when any plan row exceeds the staleness window
- REQ-GP-001 (W0) `make install-check` green against this repo: 6 missing PROJECT paths added, 18 GP-INTERNAL files removed *(post-sign amendment 2026-08-15: +`GP-v4.1-presentation-TR.html`, removed under V4C-79 alongside the manifest's 17 — acknowledged as a criteria diff in the closure report)*, v4.3.1 tooling (check_records.py, Makefile gate targets, warnings ledger) in place and WIRED (a control that warns into a void has not run)
- REQ-CAL-001 (carried debt) Elo thresholds recalibrated against live CI data (data edit in categories.py; rationale recorded)

## 3. Wave decomposition (≤5-min subagent tasks; K.6)

**W0 — GP v4.3.1 migration (REQ-GP-001; process, no product code)**
1. Add missing PROJECT paths: `.governed-records` (project record names filled), `.language-allow`, `INSTALL-MANIFEST.md`, `docs/retrospectives/`, `docs/warnings.ledger.md` + template
2. DELETE leaked GP-INTERNAL files (explicit list, permission-matrix §4): 11 `docs/HANDOVER-v*-material.md`, `GP-v4.1-presentation.html` + `GP-v4.1-presentation-TR.html` (V4C-79), `docs/executive-overview.{md,pdf,gen.py}`, `pipeline-architecture.html`, `pipeline-design.md` — 18 files
3. Upgrade tooling to v4.3.1: `scripts/check_records.py`, Makefile (`make check` now calls check-records + install-check), `.pre-commit-config.yaml`; AGENTS.md universal section refresh (V4C-79/64/71) — K.10 note: CI workflow diffs called out separately at the milestone commit

**W1 — Plan schema + seed dataset (REQ-SUB-001/-002)**
1. Schema migration + `plans.yaml` format; parser with the same skip-and-count discipline as price parsers
2. Seed dataset researched live (WebFetch per provider pricing page; every row: source_url + last_verified = probe date)
3. Registry linkage: plan included-model names → canonical IDs; unmatched names DROP and count (M1 rule 4)

**W2 — Staleness + verification workflow (REQ-SUB-003/-004)**
1. Staleness window as data (not code branch — M2-W4 lesson); flagged rows in exports
2. CI scheduled job / checklist row for re-verification cadence (Q4)
3. Contract-style test: schema of plans.yaml validated; a row missing last_verified fails loud

**W3 — Subscription recommender + carried debt (REQ-REC-007/-008, REQ-CAL-001)**
1. `recommend --subscription`: three picks, close_call + stale disclosures; per-model path regression-locked
2. Elo threshold recalibration from live CI data (data edit + rationale); ArenaClient url-param cleanup; GitHub Actions SHA-pin (before the weekly cron matters)

## 4. Shared contracts (K.8)

Frozen: schema.py existing tables, RawSource protocol, registry rules, RankingRow/Pick (D-105 shape),
CLI exit codes (0/1/2). New shared surface: `plans.yaml` format + `plan_ranking` signature —
grep output pasted at W1 dispatch.

## 5. Token budget estimate

W0 ≈ 40k · W1 ≈ 80k (live probing) · W2 ≈ 50k · W3 ≈ 70k · reviews ≈ 80k · closure ≈ 70k
(first `/retrospect`, M≥3) → **≈ 390k ≤ 500k cap**.

## 6. Issue inventory

None open. Layer-2 issue agent stays OFF.

## 7. Closure tasks (Stage 4)

Security review (BLOCKING) · Quality Gate (V3C-02 trace) · Capture: EXPERIENCE entry + **first
retrospect (M≥3, V3C-79)** + first REAL trust telemetry (git history exists since M2) · warnings
ledger walked (C2a/b/c — new in v4.3.1) · closure-report-m3.md · no deploy · commits per D-106
(green gates, agent trailer, bundle-or-push per session capability).

## 8. Explicit non-goals

Epoch AI (→ M4, owner decision 2026-08-15) · HTTP API · iOS app · composite/normalized scores ·
Artificial Analysis (banned, D-101) · scraping provider dashboards (documented pricing pages only,
read manually/WebFetch — no automated scraping pipeline) · historical price trends.

## 9. Risks

- **Curated data rot** is the product's core risk → last_verified mandatory per row (REQ-SUB-003), cadence job (REQ-SUB-004), owner spot-check at gate.
- Provider pricing pages are marketing HTML, not APIs → values are transcribed with source_url + date, never scraped programmatically; ambiguous limits recorded as the page states them (verbatim quote in `limits`).
- Plan "included models" are often vague ("latest models") → map only what is explicitly named; vague claims stored as text, not links (no guessed mappings — M1 rule 4).
- Currency/region variance (Q2) → start narrow, widen by data not code.
- W0 deletes files → exact list in §3 W0.2; nothing outside it; deletions reviewed in the milestone diff.

## 10. New ADR candidates (proposed at closure via /log-decision)

- D-107: subscription plans are curated in-repo data (YAML) with mandatory per-row provenance + last_verified; no plan feed exists, so verification cadence is a product feature.
- D-108: GP process baseline moves v4.2 → v4.3.1; install-check + warnings ledger become standing gates in `make check`.

---

## §13 Dispatch checklist (owner signs to release Wave 0)

- [ ] **Q1 — Provider scope:** OpenAI, Anthropic, Google, Perplexity for M3 (add/remove?)
- [ ] **Q2 — Region/currency scope:** USD + US region first, TR noted where pages state it (or TR-first?)
- [ ] **Q3 — Staleness window:** 30 days for plan rows (stricter/looser?)
- [ ] **Q4 — Re-check cadence:** weekly scheduled CI reminder job (vs owner manual routine)
- [ ] M3 REQ-IDs accepted (§2) · wave decomposition + ~390k token estimate accepted
- [ ] W0 deletion list (§3 W0.2) explicitly approved
- [ ] Commit/push path: repo added to session sources, or bundle handoff (D-106 stays within scope limits either way)

**Owner sign-off:** ______ · **Date:** ______
