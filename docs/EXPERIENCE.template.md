---
record_type: experience
id: experience-template
status: draft
process_version: v5.0
date: 2026-08-12
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run,
     which is exactly what shipped in v4.3.1. -->
# Project Experience — `<PROJECT_NAME>` (living document, v4.1 · V3C-81 + V4C-13)

> **This file is a STANDING artifact, not a campaign deliverable.** Copy to `docs/EXPERIENCE.md`
> at bootstrap; append at EVERY milestone closure (closure-checklist §B.2 line); the quarterly
> handover is BLOCKED without a dated entry for the latest closed milestone (quarterly-handover
> skill, step 0). When the org harvests for the next pipeline version, this file is collected
> as-is — harvest is collection, not a campaign.
>
> **Boundary (don't mirror other docs):** EXPERIENCE = generalizable lessons in seed format for
> the ORG (below). `playbook-seeds.md` = this project's candidate rules. `HANDOVER-*` = state
> dump for the next agent. A lesson lives HERE when a *different* project could reuse it.
>
> **Redaction rule (BLOCKING before any share/harvest):** no credentials, keys, tokens, customer
> names/data, live endpoints, or internal URLs. Abstract every example.
> **Honesty rule:** every finding cites evidence (session ref, commit, test, review file) —
> findings without origins are vibes, and vibes don't survive a council.

## Header (fill once, update as it changes)

- Purpose (one line): `<what the project is>`
- Stack: `<languages/frameworks/infra>`
- Duration & size: `<wall-clock, milestones closed, tests, team shape>`
- Methodology: `<GP version + what was actually followed>`
- Author / date: `<lead agent, on behalf of OWNER>` / `<YYYY-MM-DD of last update>`
- Finding count: `<N>`

---

## Findings (append per milestone; never rewrite old entries — supersede)

### F`<n>` — `<one-line principle title>`  *(added at M`<N>` closure, YYYY-MM-DD)*
- Category: incident | problem | best-practice | novel-experience | **control-bypass (v4.0, V4C-13: a control skipped under pressure is a finding about the CONTROL — record which, why, cost, and whether the control or the pressure should change)**
- Severity / impact: catastrophic | high | medium | low
- Confidence: N=`<how many independent occurrences>`
- Principle: `<the reusable rule, one or two sentences>`
- Origin: `<what actually happened — cite session/commit/test>`
- Reusable artifact: `<the checklist line / template / test pattern another project can lift>`
- Risk if ignored: `<what breaks>`
- Tradeoff / cost of adoption: `<what it costs>`
- Proposed disposition: gate | guardrail | template-change | candidate-seed | doc-only

---

*Milestone log: M1 `<date, +k findings>` · M2 `<…>` — one line per closure so freshness is auditable.*
