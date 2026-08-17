# M4 Plan — Make the Plan Answers Real (data depth)

**Status:** SIGNED — owner approved 2026-08-15: "I am signing the M3 closure report; if there is
no problem we can continue with M4" (owner, translated from Turkish). Waves dispatch without
stopping.
**Date:** 2026-08-15 · **Risk tier:** LOW (public data only; no auth/PII/payment) · **Mode:** A0.5 + D-106
**Process baseline:** GP v4.3.1 (D-108). Waves run without stopping; the owner runs the
out-of-sandbox verification at the milestone gate (owner amendment, M3).
**Owner decisions locked 2026-08-15:** focus = data depth (not API-first) · deploy target for M5 =
**Fly.io** (recorded here, spent in M5) · subscription table stays **USD / US** (no TR rows yet).

---

## 0. Design notes + gap analysis (V3C-50 — before any code)

**What M3 proved on live data (owner's verification run, 2026-08-15):** the subscription answer
works end-to-end but is **thin by data, not by design** — of 9 curated plans only 2 are scoreable,
and under the `orta` budget `eligible_count` is **1**, so all three "choices" are the same plan.
Two independent causes, and M4 exists to remove both:

1. **Registry gap.** Plan pages name models our registry has no rule for (`GPT-5.6`,
   `GPT-5.6 Sol Pro`); live SWE-bench also lists `Claude 4.6 Opus`, `MiniMax M2.5` and
   `Gemini 3 Flash` variants that drop for the same reason. Adding a rule must become a cheap,
   tested, reviewable act — the registry is this product's living IP.
2. **Roster gap.** Anthropic's and Perplexity's plan cards name NO model versions at all, so
   `included_models` is legitimately empty and those plans can never rank. M1 rule 4 forbids
   guessing — so the fix is not a guess but a SECOND, documented source: each provider's own
   model-availability page, ingested with its own provenance and its own `last_verified`.

**Third finding, same run: the coding category's evidence is aging.** `stale_notice` fired live —
SWE-bench Verified's newest run_date is 2026-02-26 (170 days); Aider has been dead since
2025-10-03 (316 days). The honesty control works, but a category resting on a frozen source is a
product risk, not just a disclosure. M4 investigates and, if a documented fresh source exists,
adds it; if not, it says so in the closure report rather than pretending.

**Fourth, small:** Elo scores reach the JSON as raw floats (`1481.5937567329202`). Before the API
freezes its contract in M5, scores must be rounded at the boundary with a stated precision rule.

**What M4 deliberately does NOT do:** HTTP API, deploy, TR/regional pricing, new categories.

## 1. Goal (1 sentence)

Every curated plan that a provider actually documents becomes rankable, so the subscription answer
offers real alternatives instead of one plan three times.

## 2. Acceptance criteria (each gains a citing test, V3C-02)

- REQ-CAN-004 Registry rules are cheap and safe to add: a rule-authoring path with a table-driven
  test (each new canonical id proves variant-before-parent ordering and non-collision with
  siblings), plus rules for the model families live sources currently drop
- REQ-ING-009 Provider model-roster ingestion: for a provider whose plan page names no models, the
  provider's own documented model list is ingested as a SEPARATE source with provenance +
  last_verified; a plan links to a roster model only through the registry (never guessed)
- REQ-SUB-005 **Plan coverage is a measured, reported number**: `scoreable_plans / total_plans` per
  category, emitted by the pipeline and printed in the closure report; a drop in coverage is
  visible, not silent
- REQ-REC-009 `--subscription` returns ≥3 DISTINCT plans in at least the `orta` and `sinirsiz`
  budgets on live data (the milestone's headline outcome)
- REQ-ING-010 Epoch AI ingestion (owner ruled M4): documented endpoint only, provenance mandatory,
  loud-fail per source; category placement decided by what the data actually supports
- REQ-ING-011 Source health is first-class: per-source freshness (newest run_date vs today) is
  computed, reported, and surfaced; the M4 closure states plainly whether a fresher documented
  coding benchmark exists and, if it does, ingests it
- REQ-REC-010 Score presentation rule: scores are rounded at the output boundary (Elo → 1 decimal,
  % → 1 decimal) with the raw value never leaking into the JSON contract
- REQ-SUB-006 Google AI Plus re-probe: the price dispute is re-checked; the row enters the table
  only if two independent sources agree (D-107 rule), otherwise the exclusion is re-recorded

## 3. Wave decomposition (≤5-min subagent tasks; K.6)

**W1 — Registry expansion + authoring path (REQ-CAN-004)**
1. Table-driven rule test: for every rule, assert variant-before-parent order and no sibling
   cross-match (generalizes the M1-W3 defect class instead of re-testing it by hand)
2. Add rules for families the live sources drop today (GPT-5.6 family, Claude 4.6/4.7, MiniMax
   M2.5, Gemini 3.x variants, Qwen 3.x, Kimi K3 — final list from a live drop-list probe)
3. Drop-list report: `reconcile`/`reconcile_plans` dropped names become a committed artifact the
   next milestone starts from

**W2 — Provider roster source (REQ-ING-009)**
1. Roster client + parser behind the existing `RawSource` protocol (documented pages only; no
   scraping of dashboards — D-101)
2. Roster → registry → `plan_models` linkage with its own provenance and staleness clock
3. Anthropic + Perplexity rosters seeded live-verified; OpenAI/Google rosters where documented

**W3 — Coverage, health, Epoch (REQ-SUB-005, REQ-ING-010, REQ-ING-011)**
1. Coverage metric + source-health report emitted by the pipeline and asserted by tests
2. Epoch AI ingestion (sandbox cannot reach epoch.ai → fixture-driven code, live half in CI /
   owner machine, same standing rule as HF/OpenRouter)
3. Fresh-coding-benchmark investigation: probe documented candidates, decide with evidence,
   record the verdict either way

**W4 — Presentation + data hygiene (REQ-REC-009/-010, REQ-SUB-006)**
1. Boundary rounding rule + regression tests through the real CLI entry point
2. Google AI Plus re-probe; plan table re-verification pass (all 9 rows' `last_verified` refreshed)
3. Live end-to-end proof that `--subscription` offers ≥3 distinct plans

## 4. Shared contracts (K.8)

Frozen: schema tables (`plans`, `plan_models`, `plan_config`, `scores`, `pricing`), `RawSource`
protocol, registry first-match semantics, CLI exit codes, D-105 category contract.
New shared surface: roster source name + `plan_models` provenance columns, coverage-report shape —
grep output pasted at W2/W3 dispatch.

## 5. Token budget estimate

W1 ≈ 70k · W2 ≈ 90k (live probing) · W3 ≈ 90k · W4 ≈ 60k · reviews ≈ 90k · closure ≈ 60k →
**≈ 460k ≤ 500k cap**.

## 6. Issue inventory

None open. Layer-2 issue agent stays OFF.

## 7. Closure tasks (Stage 4)

Security review (BLOCKING) · Quality Gate (V3C-02 trace, incl. the coverage metric) · Capture:
EXPERIENCE + retrospective #2 + **first mechanical trust telemetry** (M3's closure tag now exists:
post-closure fix rate, churn, reverts computed from git) · warnings ledger walk · closure-report-m4
· no deploy · commits per D-106.

## 8. Explicit non-goals

HTTP API and deploy (M5, Fly.io — decided, not spent) · TR/regional pricing (owner: USD/US stays) ·
new categories · composite scores (D-105) · Artificial Analysis (banned, D-101) · scraping
provider dashboards · iOS work.

## 9. Risks

- **The roster source may not exist in documented form for every provider.** Then the honest
  outcome is fewer scoreable plans, not invented links — the coverage metric will say so, and the
  closure report will name each provider that could not be covered.
- Registry growth raises collision risk → the table-driven ordering test is W1's first task, before
  any rule is added.
- Epoch's shape is unknown from here (no network) → fixture-driven, live half in CI, loud fail.
- A fresher coding benchmark may not exist → recorded as a finding, and the stale disclosure stays.
- Coverage could regress silently as providers change pages → REQ-SUB-005 makes it a reported
  number, and the weekly staleness job already fails on aged rows.

## 10. New ADR candidates (proposed at closure)

- D-109: provider model rosters are a second curated source class with their own provenance and
  verification clock (extends D-107 rather than widening the plan table).
- D-110: deploy target Fly.io (owner decision 2026-08-15; recorded now, spent in M5).
  **CORRECTION appended 2026-08-17, not overwritten (B.2):** this line cites the wrong ADR.
  D-110 is the plan-equivalence disclosure decision; the deploy target had no ADR at all
  until **D-116** closed OQ-3. The owner's choice recorded here was real; only its ID was
  wrong, and it read as settled for two milestones because of it.
- D-111: score presentation precision rule at the output boundary.

---

## §13 Dispatch checklist (owner signs to release Wave 1)

- [x] M4 REQ-IDs accepted (§2) — especially REQ-REC-009 as the headline outcome
- [x] Wave decomposition + ~460k token estimate accepted
- [x] Registry rule additions may be authored by the agent (data-class edit, reviewed per wave)
- [x] Roster source approach accepted: documented provider pages only, never dashboard scraping
- [x] M3 closure report signed (2026-08-15) — prerequisite met

**Owner sign-off:** APPROVED · **Date:** 2026-08-15
