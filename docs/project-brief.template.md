# Project Brief — `<PROJECT_NAME>`

> Fill this out before handing the agent a fresh project. ~5-10 minutes to complete; saves a 30-40 minute back-and-forth round with the agent during Stage 0.
>
> Hand this to the agent alongside the PRD when starting. The agent uses it to skip the "who / what / where" questions and go directly to drafting the Stage 1 plan.

---

## 1. Project identity

- **Project name:** `<...>`
- **Customer / owner:** `<who is asking for this software>`
- **One-line description:** `<what this project does, in plain English>`
- **Business context (≤3 sentences):** `<what problem does this solve for the customer? what does success look like for them? what are they worried about?>`

## 2. Stack and environment

- **Primary language / framework:** `<e.g., Python + FastAPI / Node + TypeScript / Go / Rust>`
- **Test framework:** `<pytest / vitest / jest / go test / cargo test>`
- **Target runtime environment:** `<e.g., Huawei Cloud CCE / AWS ECS / on-prem K8s / Vercel>`
- **Repo host:** `<GitHub / GitLab / Bitbucket>`
- **CI runners:** `<hosted (ubuntu-latest) / self-hosted — and why>`

## 3. Risk surface (what HIGH-risk paths exist?)

Mark each YES / NO. Any YES triggers `permission-matrix.md` §11 — senior human review mandatory.

- [ ] **Authentication / authorization logic** (login, tokens, RLS, ACLs)
- [ ] **Cryptography** (any hand-rolled, not just standard library)
- [ ] **Payment / financial transaction logic**
- [ ] **PII handling** (real customer data, not synthetic fixtures)
- [ ] **Irreversible migrations** (DROP TABLE class)
- [ ] **Regulated compliance** (PDPL / GDPR / HIPAA / SOC2)
- [ ] **Production deploy automation** (anything that can break prod)
- [ ] **Wraps / forks an OSS engine** (any third-party engine you run, modify, or build on) — if YES, complete `docs/license-review.md` at Stage 0 (FB-4 / F.10). AGPL/GPL/SSPL on a network service ⇒ **wrap-not-fork** + legal sign-off; an unreviewed copyleft fork is BLOCKING (permission-matrix catastrophe-class).

**If any YES:** name the senior human reviewer in §4 below.

## 4. Senior human reviewer

For BLOCKING items on HIGH-risk paths (§3) per `permission-matrix.md` §7 + §11:

- **Senior reviewer name:** `<...>`
- **Contact:** `<email / Slack / handle>`
- **SLA expectation:** `<e.g., 24h response, 48h review>`
- **Backup reviewer if primary unavailable:** `<...>`

If NO HIGH-risk paths in §3: write "N/A — no HIGH-risk paths in this project."

## 5. External dependencies

Who provides what BEFORE M1 can ship:

| Dependency | Provider | Status | ETA |
|---|---|---|---|
| `<e.g., model endpoint URL>` | `<customer / cloud team / us>` | proposed / in-flight / delivered | `<date>` |
| `<e.g., production database>` | `<...>` | `<...>` | `<...>` |
| `<e.g., customer test credentials>` | `<...>` | `<...>` | `<...>` |

If a dependency isn't delivered by its ETA, the agent must surface it as a milestone risk (per G.9 PM-friendly risk register).

## 6. Pipeline-specific overrides (v2.1 opt-in choices)

v2.1 ships with these as **opt-in**. Pick before Stage 0 dispatch:

- [ ] **Pre-commit hook** (lint + format at the keyboard): yes / no  *(default: opt-in for Python; reasoning per `pipeline-design.md` §11)*
- [ ] **Issue-agent Layer 2** (headless Claude in CI on labeled issues): yes / no  *(default: ship in shadow-mode for M1, graduate to draft-PR mode after one successful milestone)*
- [ ] **MCP servers beyond GitHub default:** `<list any: Linear / Slack / Notion / ...>` *(default: GitHub MCP only; add only if team uses tool daily)*
- [ ] **Additional subagent profiles beyond mandatory Code-Reviewer + Security-Reviewer:** `<list any candidate, e.g., Architect, Migration-Specialist, Docs-Writer>` *(default: only the mandatory 2; others CANDIDATE per playbook-seeds L'; graduate after ≥2 milestones of PULLED-WEIGHT)*
- [ ] **Skill source overrides:** `<list any milestone where Code-Reviewer or Security-Reviewer profile source is NOT "A — superpowers baseline">` *(default: A; B/C/D require regeneration before dispatch)*
- [ ] **CODEOWNERS / DevOps boundary (K.10):** does app + DevOps share this repo? yes / no  *(default: yes -> fill `<DEVOPS_HANDLE>` in `.github/CODEOWNERS` + enable "Require review from Code Owners". If no DevOps team, delete the build/deploy lines rather than leaving a placeholder owner.)*
- [ ] **Version-stamped `/health` (L.7):** Day-1 baseline ON by default *(set `APP_BUILD` in the Dockerfile / deploy env so the deployed build is verifiable via `curl /health | jq .build` at Stage 4.3. Defaults to `"unknown"`; only opt OUT for a service that genuinely never deploys.)*
- [ ] **Council planning Stage-1 variant (NEW v2.1):** use for this project's contested/MEDIUM+ milestones? yes / no  *(default: off; turn on per-milestone when the milestone SCOPE — not just its code — is in doubt. PULLED-WEIGHT but N=1, so opt-in.)*

## 7. Budget and cadence

- **Token budget cap per milestone:** `<e.g., $5 / 500k tokens / no cap>` *(default per `pipeline-design.md` §13: 50k-500k tokens per milestone)*
- **Token budget cap for whole project:** `<...>` *(optional)*
- **Wall-clock cadence expectation:** `<e.g., 2-week milestones / 1-week milestones / flexible>`
- **Quarterly handover cadence:** `<v2.0 default is M3/M6/M9/M12; deviate?>`
- **Retrospective frequency:** `<v2.0 default is M≥3 G.12; deviate?>`
- **AGENTS.md size cap:** `<v2.0 default is 80 target / 150 hard cap; deviate?>`

## 8. Greenfield vs migration

- [ ] **Greenfield** — no prior code; skip `docs/codex-audit.md`.
- [ ] **Migration from existing codebase** — see `docs/codex-audit.md` template; agent must complete the audit during Stage 0 before any wave dispatches.
- [ ] **Hybrid** — some greenfield modules, some migrated from `<source>`. List which: `<...>`

## 9. M1 (first milestone) expectations

- **Risk tier:** `<LOW recommended for new-pipeline shake-out / MEDIUM / HIGH>`
- **Scope:** `<one-line — e.g., "auth endpoint + DB migration", "health check + first feature">`
- **Acceptance:** `<which REQ-IDs M1 closes; agent will number these per seed A.1>`
- **Estimated wave count:** `<typically 1-4 waves per milestone>`
- **Stretch goals (deferrable):** `<...>`

## 10. What the agent MUST deliver before any wave dispatches

This is the contract. Agent reads §1-9 above + the PRD, then produces:

1. **Filled AGENTS.md** §1-2 (PROJECT section)
2. **Filled `pyproject.toml`** name + initial deps
3. **`docs/prd.md`** numbered with REQ-IDs (per seed A.1 + A.3 separate passes)
4. **`docs/architecture.md`** §5 conflict table populated (seed A.2)
5. **`docs/decisions.md`** first project ADRs **D-100..D-NNN** (covering stack, target env, risk-surface acknowledgments, any §6 pipeline overrides). Process ADRs use `P-00x`; if inheriting a project with low D-ids, run the P-001 reconciliation recipe (seed B.6).
6. **`docs/plans/m1-plan.md`** in writing-plans format — including:
   - Goal (1 sentence)
   - REQ-ID acceptance criteria
   - Wave decomposition (each task ≤5 min subagent scope)
   - K.8 shared contracts grep-verified (paste `grep -n` output)
   - **Token budget estimate per wave + total milestone**
   - **Risk tier (LOW/MEDIUM/HIGH)**
   - Subagent profile source (default A)
   - Issue inventory (Layer 2 vs K.4 routing)
   - Closure tasks
   - §13 dispatch checklist
7. **Day-1 green baseline confirmed** (`make check` GREEN) **and `make bootstrap-check` GREEN** (FB-1 Stage-0 gate — no placeholders, L.7 `/health`, filled core docs, universal ADRs present)
8. **`docs/license-review.md`** completed if §3 "wraps/forks an OSS engine" is YES (FB-4)
9. **Host-side admin TODOs surfaced** (branch protection, ANTHROPIC_API_KEY secret, label creation, 90-day rotation calendar)

After producing all items, the agent presents them to you and **waits for §13 sign-off**. Wave 1 only dispatches after sign-off.

**You will see the plan AND the workload estimate before any token is spent on implementation.**

---

## Notes / unusual context (free text)

`<anything that doesn't fit elsewhere — e.g., "the customer is on holiday until Nov 15", "we've tried this with a different vendor and failed because X", "Senior reviewer is on parental leave M3-M5">`

---

## Sign-off

**Filled by:** `<name>`
**Date:** `<YYYY-MM-DD>`
**Handed to agent:** `<YYYY-MM-DD HH:MM>`

After agent delivers the 8 items in §10, sign here to authorize Wave 1 dispatch:

**User sign-off:** `<pending>`
**Date:** `<YYYY-MM-DD HH:MM>`
