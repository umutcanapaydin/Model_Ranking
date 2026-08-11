# HANDOVER — Material that produced Pipeline v2.2

> Provenance record for the v2.2 cut (2026-06-19). Companion to `HANDOVER-v2.1-material.md`
> (which produced v2.1). v2.2 is an increment over v2.1; this file records WHERE v2.2's
> material came from and HOW it was ratified, so a future maintainer can audit the cut.
> Full text of every seed is in `.agents/rules/playbook-seeds.md` (§ ★ v2.2 RATIFIED).

## Two source projects

1. **HCS-MaaS bootstrap** (a real project started from the v2.1 starter) — produced FB-1..FB-5.
   Evidence: `~/Desktop/Company/HCS/hcs_maas_vib/docs/pipeline-feedback.md`,
   `.../docs/process-log.md` S1–S2, `.../docs/decisions.md`, `.../docs/research/newapi-legal-note.md`.
2. **EF-AI S35 prod bring-up** (the EF-AI reference project, continued) — produced L.8, L.9, K.11, E.6.
   Evidence: `~/Desktop/ef_ai_vibe/docs/process-log.md` S35.

## What changed in v2.2 (verdict per finding)

| Finding | Sev | Verdict | Landed as |
|---|---|---|---|
| FB-1 self-enforcing Stage-0 gate | High | ADOPT | seed C.11 · `scripts/bootstrap-check.sh` + `make bootstrap-check` · starter `/health` fixed to L.7 |
| FB-2 ADR-ID collision | Med | ADOPT | seed B.6 · ADR P-001 (`P-00x` process / `D-100` projects) + reconciliation recipe |
| FB-3 Cowork git-in-mount | Med | ADOPT | seed C.12 · START_HERE caveat |
| FB-4 OSS-engine license gate | High | ADOPT | seed F.10 · Stage-0 gate · `docs/license-review.template.md` · permission-matrix catastrophe-class |
| FB-5 council planning 2nd payoff | + | ADOPT | graduated to a standing OPTIONAL Stage-1 variant (§15.8 closed); blind-parallel ballot recipe captured |
| L.8 configured != working | — | ADOPT | Theme L · Stage 4.3 go-live · `make smoke-deps` |
| L.9 config reaches the process | — | ADOPT | Theme L · Stage 4.3 go-live |
| E.6 pipe attribution via run-log | — | ADOPT | Theme E/L · Stage 4.3 go-live |
| K.11 agent-driven prod UI | — | ADOPT (split) | capability CANDIDATE (N=1); guardrails ACTIVE now (permission-matrix §12) |

## How it was ratified

A **7-role blind planning council** (Senior SW, Senior Data, PM, QM, Security, DevOps, Cloud
Architect) voted in parallel (none saw the others). Result: **7/7 YES** to cut v2.2; the
through-line, named independently by 6 of 7 roles, was *"documented discipline is not
self-enforcing — make it an executable gate."* The only split was K.11 (5 ADOPT / 2 DEFER on
anti-bloat); resolved by the synthesis above (guardrails now, capability later). This council was
itself the 2nd/3rd payoff that graduated FB-5.

## Retirement pass

0 disciplines retired (deliberate sweep). K.11's *capability* held at CANDIDATE rather than
promoted on N=1 — the same anti-bloat discipline that FB-5 just cleared.

## For the v2.3 maintainer

- Watch K.11 for a 2nd independent payoff before promoting the capability.
- Tighten `bootstrap-check` heuristic detectors (template-doc / license-review presence) as more projects exercise them (§15.10).
- Bundle further project feedback the same way: capture seeds PROPOSED, ratify via a blind council, promote into design + templates + Stage checklists, run the retirement pass.
- Refresh the manager-facing Executive Overview as part of the cut: update VERSION/DATE/stats and the file map in `docs/executive-overview.gen.py`, then re-run it to regenerate `docs/executive-overview.md` + `.pdf`.
