# M1 Plan — Data Layer + Recommendation Engine (coding category)

**Status:** SIGNED — owner approved via kickoff channel, 2026-08-10 ("W1 e başlayabiliriz"). Wave 1 dispatched 2026-08-10.
**Date:** 2026-08-06 · **Risk tier:** LOW (no auth/PII/payment/migration paths; V3C-78) · **Mode:** A0.5 (D-103)
**Subagent profile source:** A (superpowers baseline) · **Reviews per wave:** ONE combined reviewer (LOW tier per V3C-78); Security review at closure (Stage 4.0, BLOCKING).

---

## 1. Goal (1 sentence)

A tested, rebuildable pipeline that ingests three free-and-legal sources, reconciles model aliases into a canonical registry, produces the coding ranking, and answers "Best Quality / Best Value / Budget Pick" deterministically for a budget level.

## 2. Acceptance criteria (REQ-IDs — each MUST gain a citing test, V3C-02)

- REQ-ING-001 LiteLLM pricing ingestion (≥500 aliases, no zero-price rows, provenance)
- REQ-ING-002 SWE-bench Verified ingestion (harness retained with every score)
- REQ-ING-003 Aider ingestion (+ staleness flag)
- REQ-ING-004 provenance + deterministic re-run, no scraping
- REQ-CAN-001 alias→canonical mapping; unmatched dropped with count
- REQ-CAN-002 variant-before-parent regression test (spike bug red→green)
- REQ-CAN-003 median (not min) reference price + outlier test
- REQ-RANK-001 coding ranking (≥20 models, blended price documented)
- REQ-RANK-002 CSV + JSON export, identical rows, generated_from metadata
- REQ-REC-001 three labeled deterministic picks with why/trade-off/confidence
- REQ-REC-002 budget filter as hard constraint (tested thresholds)
- REQ-REC-003 Pareto non-dominance test
- REQ-REC-004 confidence mapping + close-call disclosure (tested)

## 3. Wave decomposition (each task ≤5-min subagent scope; K.6)

**W1 — Schema + source clients (REQ-ING-001, -004 partial)**
1. SQLAlchemy-free schema module (plain sqlite3 DDL): models/pricing/scores/px_median + provenance columns
2. `clients/` Protocols: PricingSource, LeaderboardSource + fakes with fixture payloads (D-001)
3. LiteLLM client + parser (skip-no-price rule) + unit tests citing REQ-ING-001
4. Pipeline run-context (observed_at stamp, per-source counts report)

**W2 — Benchmark ingestion (REQ-ING-002, -003, -004)**
1. SWE-bench client + Verified-only parser + harness extraction + tests (REQ-ING-002)
2. Aider client + parser + staleness flag + tests (REQ-ING-003)
3. Deterministic re-run test: two runs → identical row sets (REQ-ING-004)

**W3 — Canonical registry + ranking (REQ-CAN-*, REQ-RANK-*)**
1. Alias rule table (ordered, first-match) + canonicalize() + unmatched-drop counter (REQ-CAN-001)
2. Variant-before-parent ordering test — reproduce spike bug red→green (REQ-CAN-002)
3. Median price builder + outlier test (REQ-CAN-003)
4. Coding ranking query + CSV/JSON exporter + metadata (REQ-RANK-001/002)

**W4 — Recommendation engine (REQ-REC-*)**
1. Eligibility filter (budget thresholds as named constants) (REQ-REC-002)
2. Pareto frontier + value-pick rule (within-N-of-leader, cheapest) (REQ-REC-003)
3. Three-answer assembler with confidence + close-call disclosure (REQ-REC-001/004)
4. CLI entry (`python -m app.workflows.recommend --budget …`) + end-to-end test through the real entry point (V4C-50)

## 4. Shared contracts (K.8 — grep-verified at dispatch)

Shared surface: `src/app/workflows/schema.py` (table DDL + row dataclasses) and `src/app/clients/protocols.py`. Wave dispatch prompt will paste `grep -n "class .*Source\|CREATE TABLE" src/app/…` output as the frozen contract. (Repo not yet on disk at plan time — grep output attached at dispatch, per K.8.)

## 5. Token budget estimate

W1 ≈ 60k · W2 ≈ 60k · W3 ≈ 90k · W4 ≈ 90k · reviews+tester ≈ 100k · closure (security review, quality gate, capture, closure report) ≈ 60k → **total ≈ 460k ≤ 500k cap** (brief §7).

## 6. Issue inventory

None open (greenfield). Layer-2 issue agent OFF for M1 (brief §6).

## 7. Closure tasks (Stage 4)

4.0 Security review (BLOCKING; docs/security-baseline.md walk — no creds, no scraping, deps audited) · 4.1 Quality Gate (V3C-02 criterion↔test trace, coverage, Done Evidence) · 4.2 Capture (process-log, EXPERIENCE entry, seeds, ADR status flips to accepted on owner ratification) · 4.3 no deploy in M1 · 4.4 note.txt refresh + closure report from template.

## 8. Explicit non-goals of M1

Arena/OpenRouter/Epoch sources · subscription-plan table · non-coding categories · HTTP API beyond /health · deploy · any LLM in the data path (D-104).

## 9. Risks

- Source shape drift (SWE-bench JSON layout) → fixture-pinned parsers + loud validation.
- Alias table subjectivity → unmatched-drop report keeps blind spots visible; registry reviewed at closure.
- Sandbox network limits (only GitHub reachable) → M1 sources chosen accordingly; M2 sources run host/CI-side.

---

## §13 Dispatch checklist (owner signs to release Wave 1)

- [x] PRD REQ-IDs read and accepted (docs/prd.md)
- [x] D-100..D-104 ratified (or corrections noted)
- [x] Wave decomposition + token estimate accepted
- [x] Risk tier LOW accepted (single combined reviewer per wave)
- [x] Owner host-side TODOs acknowledged (git init pending — owner will open the repo and announce; checkpoint commits owed)

**Owner sign-off:** APPROVED (owner message) · **Date:** 2026-08-10
