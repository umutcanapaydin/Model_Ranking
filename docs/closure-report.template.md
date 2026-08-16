---
record_type: closure
id: closure-report-template
status: draft
process_version: v5.0
date: 2026-08-12
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run,
     which is exactly what shipped in v4.3.1. -->
# Closure Report — M{N} (v3.3, V3C-83/90 — the owner's milestone-session review pack)

> **Generated at every milestone closure** (Stage 4.2) — the owner's review pack for the A0.5
> milestone session (v3.3, OD-4): the owner reviews THIS + the per-wave diffs, runs his own tests /
> smoke tests / checks, and performs the milestone commits. Time-box: 60–90 min; if the pack needs
> more than ~15 min of reading before the owner can start his own tests, the milestone was too big
> (cap: ~4–6 waves / ~2k net lines — close early next time). **Copy to `docs/closure-report-m{N}.md`.**
> **Hard cap: 2 pages / ~150 lines** — a pack too long to read defeats its purpose.
>
> **Derivation rule (anti-wallpaper):** every section except §6 is **derived from raw referents**
> (git log/diffstat, CI runs, committed checklist + review artifacts) — assemble, don't author.
> Every claim carries a referent the owner can spot-check in git. Only §6 is prose.
> **This report REPLACES the old §B closure walk-through output and note.txt's milestone summary**
> (net-zero artifacts rule) — those steps now produce THIS file.

## 1. What shipped (from the signed plan — criteria hash-checked)

| Acceptance criterion (hash-frozen at plan-sign) | Citing test | CI run | Status |
|---|---|---|---|
| `<criterion>` | `<file:line>` | `<run id>` | ✅/❌ |

**Criteria diffs since plan signature:** `<NONE, or highlighted diff — A2 requires zero unacked>`

## 1a. Per-wave table (v3.3 — one row per wave; each cell links to committed evidence)

| Wave | Risk tier | Review depth applied | Findings opened/closed | Test Δ | Escalations | Checkpoint sha |
|---|---|---|---|---|---|---|
| W{1} | `<tier>` | `<combined / C-R+Tester+sec>` | `<n>/<n>` | `<+n>` | `<none|list>` | `<sha>` |

## 1b. Decisions made on your behalf (v3.3 — assumption ledger + agent judgment calls)

- `<each assumption/decision, one line, with its ledger referent — the section the owner's attention pays for>`

## 2. Git record (annotated)## 2. Git record (annotated)

- Commit range: `<start>..<closure-tag>` · diffstat: `<files/+/->` · waves: `<K>`
- Notable commits, one line each (agent-authorship trailer per convention: `Co-Authored-By: <agent> (GP-v3.2)`):
  - `<sha>` — `<what and why, one line>`

## 3. Trust telemetry (mechanical — script-computed vs protected refs; V3C-84)

| Task type | Post-closure fix rate | Churn (N-day) | Reverts | Findings (sec separately) |
|---|---|---|---|---|
| `<type>` | `<computed>` | `<computed>` | `<computed>` | `<n> (<sec n>)` |

**Agent self-report vs telemetry (METR clause):** `<agent's one-line self-assessment>` — *placed
beside the numbers so the believed-vs-actual gap is visible.*
**Mode: A0.5 (milestone-cadence owner review — PROVISIONAL, v3.3).** Fix-rate vs owner-per-wave
baseline: `<generated comparison line — the OD-4 falsifier>`. Tripwires: `<none|event → auto-fallback to wave cadence>`

## 4. Security & invariants

- Security close verdict: `<PASS/…>` (referent: review artifact)
- Invariants table current: every row cites its NEGATIVE test — `<referent>`
- ⛔-glob touches this milestone: `<none | list + line-by-line review referent>`

## 5. Ledgers (nothing silent)

- **Skipped/waived checks:** `<each with reason + referent — capped; skips-turned-fixes count double>`
- **Assumption ledger:** `<each assumption the agent made instead of asking — from m{N}-assumptions.md>`
- **Seed candidates queued (A2):** `<list for owner approval — never adopted live>`
- **Risks queued to M{N+1}:** `<from MINOR findings>`

## 6. Architecture delta — PROSE (the comprehension-debt countermeasure)

`<The agent explains, in plain prose a stranger could follow: what structurally changed this
milestone, why this approach, what could break, and what a future maintainer must know.
If the agent cannot explain it, it does not ship — this section is a BLOCKING closure item.>`

---
*Generated from raw referents at closure. Owner sign-off: `<initials/date>`.*
