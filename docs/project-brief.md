# Project Brief — model_ranking

> Filled 2026-08-06 by the lead agent from the owner's research corpus and kickoff decisions; owner reviews and signs at the bottom. (Template: docs/project-brief.template.md.)

---

## 1. Project identity

- **Project name:** model_ranking
- **Customer / owner:** Umut Can Apaydın (ILGAR)
- **One-line description:** Data engine that aggregates free-and-legal LLM benchmark scores + API prices and produces deterministic, budget-aware "Best Quality / Best Value / Budget Pick" recommendations — the backend of a future iOS AI-advisor app.
- **Business context (≤3 sentences):** People and developers don't know which AI model or subscription fits their use case and budget; benchmark sites are web-only and developer-oriented. This engine turns public benchmark + pricing data into personal recommendations; the iOS app consuming it comes in later milestones. Success for M1 = a tested, rebuildable pipeline + recommendation engine on the coding category with clean data provenance.

## 2. Stack and environment

- **Primary language / framework:** Python 3.11 + FastAPI (adapter is /health-only in M1)
- **Test framework:** pytest
- **Target runtime environment:** local dev / CI in M1; serving target open (OQ-3: Supabase vs Cloudflare candidates)
- **Repo host:** GitHub (owner will create; private)
- **CI runners:** hosted (ubuntu-latest)

## 3. Risk surface (what HIGH-risk paths exist?)

- [ ] **Authentication / authorization logic** — NO (no users, no mutating routes in M1)
- [ ] **Cryptography** — NO
- [ ] **Payment / financial transaction logic** — NO
- [ ] **PII handling** — NO (public benchmark/pricing data only)
- [ ] **Irreversible migrations** — NO (disposable SQLite, rebuilt every run)
- [ ] **Regulated compliance** — NO in M1 (KVKK/GDPR review before any user-facing release)
- [ ] **Production deploy automation** — NO in M1
- [ ] **Builds on a modified third-party OSS engine** — NO (open-source libraries are used as unmodified pip dependencies only)

## 4. Senior human reviewer

N/A — no HIGH-risk paths in this project (M1). Owner is the sole reviewer per A0.5.

## 5. External dependencies

| Dependency | Provider | Status | ETA |
|---|---|---|---|
| LiteLLM pricing JSON (GitHub raw) | BerriAI/litellm (open source) | delivered (verified 2026-08-06) | — |
| SWE-bench leaderboard JSON (GitHub raw) | swe-bench/swe-bench.github.io | delivered (verified 2026-08-06) | — |
| Aider polyglot YAML (GitHub raw) | Aider-AI/aider (Apache-2.0) | delivered (verified 2026-08-06; source stale since ~Nov 2025 — flagged) | — |
| GitHub repo + branch protection | owner | proposed | before M1 closure commits |

## 6. Pipeline-specific overrides (opt-in choices)

- [x] **Pre-commit hook:** yes (Python default)
- [ ] **Issue-agent Layer 2:** no for M1 (revisit after first milestone)
- [ ] **MCP servers beyond GitHub default:** none
- [ ] **Additional subagent profiles:** none (mandatory Code-Reviewer + Tester + closure Security-Reviewer only)
- [ ] **Skill source overrides:** none (default A)
- [x] **CODEOWNERS / DevOps boundary:** no separate DevOps team → delete build/deploy owner lines rather than leaving a placeholder
- [x] **Version-stamped /health (L.7):** ON (starter default kept)
- [ ] **Council planning Stage-1 variant:** off

## 7. Budget and cadence

- **Token budget cap per milestone:** ~500k tokens (default upper band)
- **Token budget cap for whole project:** none set
- **Wall-clock cadence expectation:** flexible; milestone closes when waves close, capped at ~4–6 waves
- **Quarterly handover cadence:** default (M3/M6/…)
- **Retrospective frequency:** default (M≥3)
- **AGENTS.md size cap:** default (80 target / 150 hard)

## 8. Greenfield vs migration

- [x] **Greenfield** — no prior production code. (A Cowork spike exists; per D-102 it is L0 reference only, findings encoded as REQ-CAN-002/003.)

## 9. M1 (first milestone) expectations

- **Risk tier:** LOW (new-pipeline shake-out; no HIGH-risk paths)
- **Scope:** Data layer + recommendation engine for the coding category (3 sources → canonical registry → ranking → 3-answer recommender)
- **Acceptance:** REQ-ING-001..004, REQ-CAN-001..003, REQ-RANK-001..002, REQ-REC-001..004 (see docs/prd.md)
- **Estimated wave count:** 4
- **Stretch goals (deferrable):** JSON export consumed by a demo notebook; source-health report artifact

## 10. What the agent MUST deliver before any wave dispatches

Delivered with this brief (2026-08-06): filled AGENTS.md §1-2 · filled pyproject.toml · docs/prd.md with REQ-IDs · docs/architecture.md with §5 conflict table · docs/decisions.md D-100..D-104 · docs/plans/m1-plan.md (writing-plans format, token estimate, risk tier, dispatch checklist) · bootstrap-check status report · host-side admin TODO list. `make check` day-1 green to be confirmed on the owner's machine (venv lives host-side).

---

## Notes / unusual context (free text)

Owner works via Cowork (cloud agent + device bridge); agents never run git (A0.5) — owner performs all commits host-side. The build sandbox can reach GitHub but NOT huggingface.co / openrouter.ai / epoch.ai; those sources join in a milestone executed where network policy allows (owner machine or CI). Artificial Analysis integration is BANNED until a commercial agreement exists (D-101).

---

## Sign-off

**Filled by:** lead agent (Claude) from owner inputs
**Date:** 2026-08-06
**Handed to agent:** 2026-08-06

After agent delivers the items in §10, sign here to authorize Wave 1 dispatch:

**User sign-off:** PENDING
**Date:** —
