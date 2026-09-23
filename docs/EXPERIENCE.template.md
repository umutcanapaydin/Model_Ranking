---
record_type: experience
id: experience-template
status: draft
process_version: v6.6
date: 2026-08-12
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run. -->
# Project Experience — `<PROJECT_NAME>` (living document)

> **This file is a STANDING artifact, not a campaign deliverable.** Copy to `docs/EXPERIENCE.md`
> at bootstrap; append at EVERY milestone closure (closure-checklist §B.2 line). When lessons are collected for the next DevFlow version, this
> file is collected as-is — collection, not a campaign.
>
> **Boundary (don't mirror other docs):** EXPERIENCE = generalizable lessons in seed format for
> the ORG (below). `playbook-seeds.md` = the seed index. `docs/process-log.md` =
> session state for the next agent. A lesson lives HERE when a *different* project could reuse it.
>
> **Redaction rule (BLOCKING before the file is shared or collected):** no credentials, keys, tokens, customer
> names/data, live endpoints, or internal URLs. Abstract every example.
> **Honesty rule:** every finding cites evidence (session ref, commit, test, review file) —
> findings without origins are vibes, and vibes don't survive review.

## Header (fill once, update as it changes)

- Purpose (one line): `<what the project is>`
- Stack: `<languages/frameworks/infra>`
- Duration & size: `<wall-clock, milestones closed, tests, team shape>`
- Methodology: `<DevFlow version (from .gp/installed) + what was actually followed>`
- Author / date: `<lead agent, on behalf of OWNER>` / `<YYYY-MM-DD of last update>`
- Finding count: `<N>`

---

## Findings (append per milestone; never rewrite old entries — supersede)

### F`<n>` — `<one-line principle title>`  *(added at M`<N>` closure, YYYY-MM-DD)*
- Category: incident | problem | best-practice | novel-experience | **control-bypass (a control skipped under pressure is a finding about the CONTROL — record which, why, cost, and whether the control or the pressure should change)**
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
