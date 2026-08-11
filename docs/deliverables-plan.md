# Deliverables Plan — model_ranking

> What this project produces, for whom, and when. Filled at Stage 0 close (2026-08-10); updated at every milestone closure. **Only M1 is formally planned and signed** (the pipeline plans one milestone at a time — Stage 1 per milestone); M2+ below are the agreed ROADMAP, each to be planned + signed at its own Stage 1.

---

## Milestone roadmap (owner-visible)

| M | Scope (one line) | Key deliverable | Status |
|---|---|---|---|
| **M1** | Data layer + recommendation engine, coding category (3 GitHub sources) | Tested pipeline: ingest → canonical registry → coding ranking → 3-answer recommender (CLI) | **in flight — W1 closed, W2-W4 running** |
| M2 | More sources + categories: Arena HF dataset, OpenRouter, Epoch (host/CI-side network); "everyday assistant" category | Multi-category rankings with blended sources + source-health report | roadmap (plan at M1 closure; resolves OQ-1) |
| M3 | Subscription-plan table (ChatGPT Plus / Claude Pro / Gemini…) + plan-level value advisor + curation workflow | The unique data asset: plan↔model↔price mapping with manual-verify cadence | roadmap (resolves OQ-2) |
| M4 | Read-only serving API + scheduled refresh + deploy (target per OQ-3) | `/rankings` + `/recommend` endpoints, CDN-cached JSON, journey script | roadmap (Security review BLOCKING before deploy) |
| M5 | iOS SwiftUI app (likely separate repo, consumes M4 API) | App Store-ready advisor MVP | roadmap (own brief + plan) |

## Customer-facing deliverables

| ID | Artifact | Format | Status | Notes |
|---|---|---|---|---|
| D-A | Coding ranking dataset | CSV + JSON | M1 (REQ-RANK-002) | rebuildable from sources; provenance stamped |
| D-B | 3-answer recommendation CLI | Python CLI | M1 (REQ-REC-001..004) | Best Quality / Best Value / Budget Pick |
| D-C | Multi-category rankings | JSON | M2 | adds Arena/OpenRouter/Epoch |
| D-D | Subscription value table | JSON + curation doc | M3 | no machine-readable feed exists anywhere — curated |
| D-E | Public API + refresh jobs | service | M4 | deploy gate: Stage 4.0 Security PASS |
| D-F | iOS advisor app | App Store build | M5 | separate plan/brief |

## Internal deliverables (Phase exit / handover)

| ID | Artifact | Status | Notes |
|---|---|---|---|
| I-A | `handover-to-prod-agent.md` | proposed | Operator runbook for post-build agent (created at M_final-1) |
| I-B | Quarterly handovers (`handover_q1..q4.txt`) | proposed | Generated via `/quarterly-handover` at every 3rd milestone closure |
| I-C | G.12 retrospectives (`m{N}-retrospective.md`) | proposed | Generated via `/retrospect` at M≥3 |

## Cadence

- Per-milestone closure: process-log + retrospect (M≥3) + Quality Gate output + closure report — **owner's 60-90 min review session happens HERE (A0.5)**
- Quarterly closure: `handover_q{N}.txt` (M3, M6, M9, M12 …)
- Phase exit: final roadmap snapshot + handover-to-prod-agent doc
