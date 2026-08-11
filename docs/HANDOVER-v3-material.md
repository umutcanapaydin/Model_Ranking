# HANDOVER — Material that produced Pipeline v3

> Provenance record for the v3 cut (2026-06-26). Companion to `HANDOVER-v2.2-material.md`
> (which produced v2.2) and `HANDOVER-v2.1-material.md`. v3 is a **clean superset** of v2.2 — a
> cross-project harvest, not a rewrite. This file records WHERE v3's material came from and HOW it
> was ratified, so a future maintainer can audit the cut. Full candidate text is in
> `General_Pipeline/v3-candidate-register.md`; the council record is `General_Pipeline/v3-ratification.md`;
> the full seed text of every adopt is in `.agents/rules/playbook-seeds.md` (§ ★ v3 RATIFIED).

## Six source projects (the harvest)

Increment 1 (V3C-01..31): three projects + HCS lineage.
1. **Reimbursement-App** — Reimbursement Management System (Node/Vue), ad-hoc, 12 findings.
2. **Poyraz-Dekorasyon** — Poyraz Dekorasyon (React site), ad-hoc, 12 findings.
3. **aop-portal** (aop-portal) — Next.js AI-ops portal, *ran the defined pipeline*, 14 findings (frontier).

Increment 2 (V3C-32..60, + the Agent-Native cluster): three more.
4. **BotIm-AOP / BotIm** — BotIm AI / AOP, a multi-tenant AI customer-service platform, 14 findings.
5. **aop_growth** — aop_growth (Botim Growth Agent), 17 findings.
6. **HSC-MaaS** — HSC MaaS NewAPI Demo (Go gateway), 11 findings.

Increment 3 (V3C-61..67 + bumps): a correction that split one source into two.
7. **one-api / one-api** — a distinct mature OSS LLM API gateway (Go), 15 findings. (In Increment 2,
   `EXPERIENCE_one-api.md` was a mistaken md5-duplicate of BotIm-AOP's file; one-api re-downloaded the real
   one-api file, so BotIm-AOP (BotIm AOP) and one-api (one-api) are now two separate sources.)

> The earlier **HCS-MaaS** feedback (FB-1..FB-5) is already ACTIVE in v2.2; kept for lineage. The two
> GP-v2.2 validation runs (Reimbursement-App item-store, Poyraz-Dekorasyon project-mgmt API) closed M1 clean — evidence GP
> v2.2 is usable as written.

## The intra-ecosystem-independence caveat (load-bearing)

The single biggest weighting rule of this cut: **the Agent-Native + gateway evidence is mostly ONE
ecosystem.** Botim AOP (BotIm-AOP), aop_growth (aop_growth) and aop-portal (aop-portal) are the **same
agent-platform ecosystem**; one-api (one-api) and NewAPI (HSC-MaaS) are the **same gateway family**
(one-api is the upstream NewAPI forks). Treat their agreement as *semi-independent*. A finding is
"strongly convergent" only when it also appears **outside** one ecosystem or **re-derives GP's own
(independent) design**. This is why most of the agent-native/LLM-ops cluster is held at CANDIDATE and
only V3C-33/45, V3C-08/36, V3C-44, V3C-56 were adopted from it — each crossed a boundary or matched GP.

## How v3 was ratified

A **13-seat blind-parallel council** ran 2026-06-26 (budget §5.5 of council-design): 6 core seats +
the skeptic voted all 68 candidates; 7 domain seats voted their clusters; a non-voting chair tallied.
The chair auto-accepted only **convergent** ADOPTs (broad agreement across independent lenses) and
surfaced the genuine disagreements as splits S1–S4 for the owner. Budget: **~15 adopts, ≤3 BLOCKING
gates.**

**Owner-settled splits (2026-06-26):** S1 = V3C-02 a **gate**; S2 = V3C-12 a **guardrail** (not
cheaply per-route checkable); S3 = V3C-65 race detector a **guardrail** (Go-only evidence); S4 =
charter the Agent-Native theme as a **container** + adopt the 4 cross-ecosystem seeds + V3C-56.

**Final v3 adopt set:**
- **Gates (2 of ≤3; 1 in reserve):** V3C-11 (security baseline → `bootstrap-check`), V3C-02 (tests cite each criterion → Quality Gate).
- **Template:** V3C-68 (review-loop restructure), V3C-44 (canonical mock + contract test).
- **Guardrails:** V3C-06/53, V3C-13, V3C-51, V3C-03, V3C-10, V3C-05, V3C-08/36, V3C-33/45 (paired), V3C-12, V3C-56, V3C-65.
- **Doc/confirm:** V3C-50, V3C-52, V3C-01 (confirms L.7), V3C-27.
- **Theme:** Agent-Native / LLM-Ops chartered as a CANDIDATE container (~20 cluster candidates stay candidate; promote on a 2nd independent ecosystem).
- **Rejected (single-quirk / non-generalizable):** V3C-24 (orphan upload), V3C-26 (React head-hook), V3C-28 (SEO), V3C-29 (iOS tel:), V3C-30 (locale), V3C-54 (disk/compose ops), V3C-57 (speculative routing, no data), V3C-67 (Go concurrency hygiene).

## What landed where (placement pass)

| Adopt | Landed as |
|---|---|
| V3C-11 (gate) | `scripts/bootstrap-check.sh` C7 + `docs/security-baseline.md` + permission-matrix §11 |
| V3C-02 (gate) | `docs/closure-checklist.md` §B.1 + AGENTS.md §3.3 + `subagent-profiles/Tester.md` |
| V3C-68 (template) | `pipeline-v2-design.md` Stage 2/3/4 + `subagent-profiles/Tester.md` + closure-checklist §B.0/§B.2a + permission-matrix §8 + AGENTS.md §4/§6 |
| V3C-44 (template) | design §7 (testing) + closure-checklist §A + practices.md |
| Security guardrails (V3C-12/13/51/56) | `docs/security-baseline.md` + permission-matrix + practices.md |
| Safety guardrails (V3C-06/53, 08/36, 33/45) | permission-matrix §5/§8 + practices.md + AGENTS.md §5 |
| Build guardrails (V3C-03/05/10/65) | practices.md + Makefile/CI notes |
| V3C-50 / V3C-52 (doc) | START_HERE.md + `pipeline-v2-design.md` (Stage 1 planning + §7 routing index) |
| Agent-Native theme | `pipeline-v2-design.md` §3.6 + CANDIDATE sub-block in `playbook-seeds.md` |
| All adopts | `pipeline-v2-design.md` §0 v3 changelog + one seed each in `playbook-seeds.md` (append-only) + this file |

## Retirement pass

0 disciplines retired (v3 is a superset harvest). The ~20 deferred Agent-Native candidates and the
rejected single-quirk findings are recorded in `v3-ratification.md` §3 — promote candidates on a 2nd
independent ecosystem; do not retire on this cut.

## For the v3.1 maintainer

- **Refresh the manager-facing Executive Overview as part of the cut:** update VERSION/DATE/stats +
  the file map in `docs/executive-overview.gen.py`, then re-run it to regenerate
  `docs/executive-overview.md` + `.pdf`. (Done for v3.)
- **Watch for a 2nd independent ecosystem to graduate the Agent-Native candidates.** When you build
  agent-native/LLM-ops/gateway features **outside** the Botim AOP and one-api/NewAPI ecosystems and a
  candidate (V3C-32/34/35/37/38/39/40/41/42/43/46/47/48/58/59/61/62/66) recurs, capture it in the
  milestone retrospective and bring it to the next council — that is its promotion trigger.
- **Tighten the V3C-11 `bootstrap-check` C7 heuristic** as more projects exercise it (it is a simple
  grep that can false-positive on fixtures); consider adding the cheap "an auth middleware/guard
  exists" warning for V3C-12.
- **Bundle further project feedback the same way:** capture seeds PROPOSED, ratify via a blind
  council under the budget rules, promote into design + templates + Stage checklists, run the
  retirement pass — append-only throughout.
