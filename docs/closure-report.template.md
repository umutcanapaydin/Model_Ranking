---
record_type: closure
id: closure-report-template
status: draft
process_version: v6.4
date: 2026-09-23
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run. -->
# Closure Report — M{N} (the owner's milestone review pack)

> **Written only when the owner turned the milestone Quality Gate on** (Stage 4.1,
> closure-checklist §B.1). It is the owner's review pack for the milestone session: the owner reviews
> THIS + the per-wave diffs, runs his own tests / smoke tests / checks, and signs off. Time-box:
> 60–90 min; if the pack needs more than ~15 min of reading before the owner can start his own tests,
> the milestone was too big (cap: ~4–6 waves / ~2k net lines — close early next time).
> **Copy to `docs/closure-report-m{N}.md`.** `make closes` grades it. **Hard cap: 2 pages / ~150 lines**
> — a pack too long to read defeats its purpose.
>
> **Derivation rule (anti-wallpaper):** every section except §6 is **derived from raw referents**
> (git log/diffstat, CI runs, committed checklist + review artifacts) — assemble, don't author.
> Every claim carries a referent the owner can spot-check in git. Only §6 is prose.

## 1. What shipped (from the approved plan — criteria hash-checked)

| Acceptance criterion (hash-frozen when the plan was approved) | Citing test | CI run | Status |
|---|---|---|---|
| `<criterion>` | `<file:line>` | `<run id>` | ✅/❌ |

**Criteria diffs since plan approval:** `<NONE, or highlighted diff>`

## 1a. Per-wave table (one row per wave; each cell links to committed evidence)

| Wave | Risk tier | Reviews (Code-Reviewer + Tester, + security if HIGH) | Findings opened/closed | Test Δ | Escalations | PR |
|---|---|---|---|---|---|---|
| W{1} | `<tier>` | `<review file + tester file>` | `<n>/<n>` | `<+n>` | `<none|list>` | `<#PR>` |

## 1b. Decisions made on your behalf (assumption ledger + agent judgment calls)

- `<each assumption/decision, one line, with its ledger referent — the section the owner's attention pays for>`

## 2. Git record (annotated)

- Commit range: `<start>..<closure-tag>` · diffstat: `<files/+/->` · waves: `<K>`
- Notable commits, one line each (no AI attribution in any commit — identity is the git author):
  - `<sha>` — `<what and why, one line>`

## 3. Trust telemetry (computed from git against protected refs — never asserted)

| Task type | Post-closure fix rate | Churn (N-day) | Reverts | Findings (sec separately) |
|---|---|---|---|---|
| `<type>` | `<computed>` | `<computed>` | `<computed>` | `<n> (<sec n>)` |

**Agent self-report vs telemetry:** `<agent's one-line self-assessment>` — *placed beside the numbers
so the believed-vs-actual gap is visible.*

## 4. Security & invariants

- HIGH waves' security passes on their slices: `<none | review files>` (the release security review runs once, at Stage 5.1)
- Invariants table current: every row cites its NEGATIVE test — `<referent>`
- ⛔-glob touches this milestone: `<none | list + line-by-line review referent>`

## 5. Ledgers (nothing silent)

- **Skipped/waived checks:** `<each with reason + its docs/control-events.csv row>`
- **Assumption ledger:** `<each assumption the agent made instead of asking — from m{N}-assumptions.md>`
- **Seed candidates queued:** `<list for owner approval — never adopted live>`
- **Risks queued to M{N+1}:** `<from MINOR findings>`

## 6. Architecture delta — PROSE (the comprehension-debt countermeasure)

`<The agent explains, in plain prose a stranger could follow: what structurally changed this
milestone, why this approach, what could break, and what a future maintainer must know.
If the agent cannot explain it, it does not ship — this section is a BLOCKING closure item.>`

---
*Assembled from raw referents at closure. Owner sign-off: `<initials/date>`.*
