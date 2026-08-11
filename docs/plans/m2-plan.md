# M2 Plan — New Sources + Everyday-Assistant Category

**Status:** SIGNED — owner approved 2026-08-11 ("plan ok") with TWO AMENDMENTS (owner directive, recorded):
(1) NO per-wave checkpoint commits — git happens ONCE, at the milestone boundary, by the owner
    (trust-telemetry granularity drops to milestone level; accepted consciously).
(2) Mid-milestone questions go to a 6-seat COUNCIL (Software/Quality/Security/DevOps/PM/Skeptic,
    blind-parallel) instead of halting for the owner — EXCEPT the non-waivable escalate-NOW list
    (AGENTS.md §3: suspected secret, scanner-finding suppression, security-invariant changes),
    which still interrupts the owner immediately.
**Date:** 2026-08-11 · **Risk tier:** LOW (public data only; no auth/PII/payment) · **Mode:** A0.5 (D-103, ratified at M1 closure)
**Scope decision:** owner picked "new sources + chat category" (OQ-1 answered 2026-08-11; OQ-2 → subscription table stays M3).
**Reviews per wave:** ONE combined reviewer (LOW, V3C-78); Security review at closure (BLOCKING).

---

## 0. Design notes + gap analysis (V3C-50 — before any code)

**What exists (M1):** RawSource protocol + 3 GitHub clients; scores table already benchmark-agnostic
(benchmark/metric/harness columns); registry maps any raw name; ranking + recommend are CODING-only
(hardcoded benchmark filter + `task="coding"`).

**Gap to close:** (a) two new source clients whose endpoints my build sandbox CANNOT reach
(huggingface.co, openrouter.ai) — code + tests are fixture-driven as always (default suite is
network-free by rule); LIVE contract tests run on YOUR machine / GitHub CI (`RUN_CONTRACT_TESTS=1`),
which becomes the standard verification path from M2 on (also closes the M1 friction item: CI now
runs what the sandbox can't). (b) a CATEGORY layer: benchmark→category mapping so ranking/recommend
take a task parameter instead of hardcoding coding. (c) Arena Elo is a DIFFERENT SCALE than % —
research rule: never average raw scales. M2 keeps it honest: each category ranks on its PRIMARY
benchmark (assistant = Arena text Elo; coding = SWE-bench Verified), secondary benchmarks display
as evidence. Cross-benchmark normalization is deliberately deferred (M3+ with more sources).
(d) CC-BY-4.0 attribution: Arena dataset requires attribution — exports must carry it (D-101 extension).
(e) M1 carried risk: median counts every alias row equally → with a second price source this skews;
fix = median-of-per-source-medians.

**Source shape risk:** Arena's HF dataset layout will be pinned from its dataset card at W2 dispatch;
the parser is written against a committed fixture + validated by the live contract test in CI. If the
live shape diverges, the parser fails LOUD (M1 doctrine) and the fix is a normal red-test intake.

## 1. Goal (1 sentence)

The engine answers "which AI for everyday chat/assistant use, at my budget" from Arena human-preference
data, with OpenRouter as a second pricing source — and the whole pipeline verifies itself in CI.

## 2. Acceptance criteria (each gains a citing test, V3C-02)

- REQ-ING-005 OpenRouter `/api/v1/models` pricing ingestion (no auth; input/output $/1M; provenance; skip-unpriced)
- REQ-ING-006 median price = median of per-source medians (M1 risk fix; outlier-source test)
- REQ-ING-007 Arena leaderboard dataset ingestion (text/chat board → Elo score rows; harness="arena-crowd"; dataset version recorded)
- REQ-ING-008 CC-BY attribution: every export names Arena (CC-BY-4.0) + all sources with observed_at (D-101)
- REQ-CAT-001 benchmark→category map (coding, everyday_assistant) as data, not code branches
- REQ-CAT-002 assistant ranking (Arena Elo primary; ≥20 models when live)
- REQ-CAT-003 no cross-scale averaging: a category ranks ONLY on its primary benchmark's scale (structural test)
- REQ-REC-005 `recommend --task assistant|coding` — three answers per category; coding behavior unchanged (regression)
- REQ-REC-006 stale-source disclosure: if a category's primary source is stale-flagged, the output says so
- REQ-CI-001 GitHub Actions job runs unit suite on every push; contract tests as manual/scheduled job with RUN_CONTRACT_TESTS=1

## 3. Wave decomposition (≤5-min subagent tasks; K.6)

**W1 — OpenRouter pricing + median fix (REQ-ING-005/-006)**
1. OpenRouter client + parser (models endpoint → PricingRow; $/token→$/1M; skip free/unpriced)
2. Per-source-median then cross-source median in build_price_medians + outlier-source regression test
3. Multi-source pricing determinism test (re-run replaces per source independently)

**W2 — Arena ingestion (REQ-ING-007)**
1. Arena client (HF dataset file URL, pinned at dispatch) + parser → ScoreRow(benchmark="Arena text", metric="elo", harness="arena-crowd")
2. Dataset-version + license fields into provenance; registry rules extended for chat-model display names
3. Env-gated live contract test (runs in CI/owner machine)

**W3 — Category layer (REQ-CAT-001/-002/-003)**
1. categories.py: category→primary benchmark map (data table)
2. rank.py generalized: `category_ranking(conn, category)`; coding path regression-locked
3. Assistant ranking + export with attribution block (REQ-ING-008)

**W4 — Recommender per task + CI (REQ-REC-005/-006, REQ-CI-001)**
1. recommend --task parametresi; Elo-scale trade-off wording (puan farkı Elo cinsinden)
2. Stale-source disclosure line; coding regression e2e
3. .github/workflows: unit gate on push + gated contract job (uses starter ci.yml as base — CODEOWNERS/K.10 dikkat: CI dosyası değişikliği owner onayı ile merge edilir)

**W5 (STRETCH, deferrable) — Epoch CSV ingestion** — only if W1-W4 close early within budget.

## 4. Shared contracts (K.8)

Frozen from M1: schema.py tables, RawSource protocol, registry first-match rules, RankingRow.
New shared surface this milestone: `categories.py` map + `category_ranking` signature — grep output pasted at W3 dispatch.

## 5. Token budget estimate

W1 ≈ 60k · W2 ≈ 80k (shape risk) · W3 ≈ 70k · W4 ≈ 70k · reviews ≈ 90k · closure ≈ 60k → **≈ 430k ≤ 500k cap**.

## 6. Issue inventory

None open. Layer-2 issue agent stays OFF.

## 7. Closure tasks (Stage 4)

Security review (BLOCKING; new: CI workflow hardening walk) · Quality Gate (V3C-02 trace) · Capture
(EXPERIENCE, seeds; M≥3 değil — retrospect M3'te) · no deploy · closure-report-m2.md · trust telemetry
İLK KEZ gerçek git verisiyle (checkpoint commits per wave — owner, `wip(m2-wN): checkpoint — NOT reviewed`).

## 8. Explicit non-goals

Subscription-plan table (M3) · cross-benchmark normalization/composite scores · image/writing categories ·
HTTP API · deploy · Artificial Analysis (banned, D-101) · Arena SITE scraping (dataset only).

## 9. Risks

- Arena dataset shape unknown until CI run → fixture-pinned parser + loud fail + shape-discovery task at W2 dispatch.
- OpenRouter prices are per-provider routing prices; may diverge from LiteLLM → per-source median (REQ-ING-006) absorbs this; divergence >2x logged as source-health flag.
- Elo trade-off wording can mislead (Elo puanı ≠ yüzde) → REQ-REC-005 wording test.
- CI file changes are a K.10 surface → owner reviews workflow diff explicitly at milestone commit.

---

## §13 Dispatch checklist (owner signs to release Wave 1)

- [x] M2 REQ-IDs accepted (bu dosya §2)
- [x] "Primary-benchmark-per-category, normalizasyon yok" kararı kabul (D-105 adayı)
- [x] CI'da contract-test yolu kabul (REQ-CI-001; CI dosyası diff'ini milestone commit'inde sen onaylarsın)
- [x] Wave dekompozisyonu + ~430k token tahmini kabul
- [x] ~~Checkpoint commit per wave~~ — OWNER WAIVER: milestone-boundary git only (amendment 1)

**Owner sign-off:** APPROVED with amendments (owner message) · **Date:** 2026-08-11
