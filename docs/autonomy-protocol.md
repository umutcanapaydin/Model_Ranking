# Autonomy Protocol & Ladder (V3C-82/90 — **active mode: A0.5**; A1/A2 = NORTH STAR, NOT ACTIVE)

> ## ⛔ STATUS (updated by owner directive OD-4, 2026-07-05 — binding)
> **The active operating mode is A0.5 — "milestone-cadence owner review" (PROVISIONAL,
> tripwire-protected; `General_Pipeline/v3.3-ratification.md`).** Waves close agent-side
> (fresh-eyes reviews + green pinned checks + committed checklist); the OWNER reviews, runs his
> own tests/smoke tests/checks, and performs ALL git commits at EVERY MILESTONE boundary, plus a
> ~30-second labeled checkpoint commit per wave (`wip: NOT reviewed` — commit ≠ approval).
> **Bright line: the day an agent commit reaches main, that is A1 — which requires an explicit
> owner-initiated ADR, never erosion.** A1/A2 remain NORTH-STAR design targets, NOT active —
> do not enable, auto-approve, or skip any owner touchpoint on their basis. **Auto-reversion
> tripwire:** an escaped blocker traceable to an unreviewed wave that an owner wave-pass would
> plausibly have caught → automatic fallback to wave-cadence review (rest of milestone + one full
> milestone). A0.5 stays PROVISIONAL until it survives two full milestones on the next project.
>
> **Goal state (north star):** the pipeline takes a PRD, the owner signs, the process runs autonomously, and
> the owner reviews only closure reports + git records. **This is a LADDER, not a switch** —
> autonomy is earned by telemetry, demotion is automatic, and the ⛔ carve-outs never move.
> Ratified 2026-07-03 (`General_Pipeline/v3.2-ratification.md`); external basis: progressive-trust
> ladder + harness-loop risk literature (see `research/agentic-engineering-curriculum/`).

## 1. The ladder

| Level | Owner signs | Inside a milestone | Milestone boundary |
|---|---|---|---|
| **A0** | PRD + each milestone plan | owner answers mid-loop questions, confirms writes, reviews every wave | owner walks closure with the agent |
| **A0.5** ★ ACTIVE (OD-4, v3.3) | PRD + each milestone plan | waves close AGENT-side (fresh-eyes reviews, green pinned checks, committed checklist); owner makes labeled checkpoint commits (non-approval); escalate-NOW list halts to owner; assumption ledger active | owner's deep session: closure report + per-wave diffs, runs his OWN tests/smoke tests, performs the milestone commits, signs off |
| **A1** | PRD + each milestone plan (with scope grant, §3) | **zero owner touches** — agents run waves, reviews, checklists, capture | owner reads the closure report (V3C-83) + git |
| **A2** (target) | **PRD once** | zero owner touches | milestone plans auto-proceed with async notification; owner reads closure reports + git at their own pace |

- The project's current level is recorded in `docs/decisions.md` (a `P-` ADR states the level and
  its effective date). Default for a new project: **A0**. At A2, per-milestone plan approval is
  **DEFERRED, never deleted** — the owner may reassert it at any time without cause.

## 2. Promotion & demotion (mechanical, non-negotiable)

- **A0→A1:** owner decision, any time.
- **A1→A2:** **two consecutive clean milestones** per the trust telemetry (§6). "Clean" is computed
  by script from git/CI — never agent-asserted: no post-closure fix commits on the milestone's
  paths, no tripwire, no unacked criteria diffs, no security findings (security weighted double).
- **Demotion (auto, non-waivable, asymmetric):** ONE tripwire event drops A2→A1 (or A1→A0 on a
  ⛔-zone breach): an escaped blocker on a tiered-down wave (V3C-78 tripwire), a post-closure fix
  spike, a security finding in production, or an integrity violation (§5). Re-promotion costs two
  clean milestones again.
- **A2 preconditions:** (1) the trust-telemetry section exists and is populated for ≥2 milestones;
  (2) a one-time **mechanical-controls audit**: list every pipeline control as script/hook/CI-enforced
  vs markdown-only — the markdown-only set is treated as ABSENT at A2 and must be either mechanized
  or consciously accepted by the owner in the ADR.

## 3. Re-homed owner touchpoints (what replaces the mid-loop human)

1. **Write confirmation (V3C-08/36)** → a **per-plan scope grant**: the signed milestone plan
   declares the writable surface (repo worktree + an explicit allowlist of external effects).
   Inside the grant, writes auto-approve at A1/A2. **Always blocking regardless of level:**
   anything outside the grant, network side-effects not in the allowlist, destructive ops
   (the permission-matrix catastrophe class), and prod credentials (agents never hold them).
2. **Seed approval** → seeds ride the signed plan at A1; at A2 mid-milestone seed candidates are
   **queued in the closure report** and adopted only after owner review. Never adopted live.
3. **Mid-loop questions** → the **assumption ledger**: the agent takes the most conservative
   interpretation, logs it (`docs/plans/m{N}-assumptions.md`), and surfaces every assumption in the
   closure report. **Not assumable — HALT instead:** any question touching a ⛔ zone, or the
   *meaning* of an acceptance criterion.

## 4. ⛔ zones and halts

- **⛔ zones** (auth, payments, crypto, personal data, prod infra, migrations) are detected by
  **path/glob patterns declared in the plan** (`security-globs`), never by agent self-classification.
  Any diff touching a ⛔ glob forces the wave to HIGH tier (V3C-78 auto-escalation) and the slice
  receives **owner/senior line-by-line review before deploy** — at EVERY autonomy level. The
  BLOCKING security close (Stage 4.0) never moves.
- **Blocked at A1/A2 = halt-and-notify, never improvise:** on a BLOCKING security verdict, a
  tripwire, or non-assumable missing info, the controller (1) checkpoints — branch pushed, draft
  closure report naming the block with its evidence referent; (2) notifies the owner async;
  (3) may continue ONLY on independent workstreams with no dependency on the blocked item.
  It never downgrades a BLOCKING finding, never self-answers a ⛔ question, never "works around"
  the block.

## 5. Anti-gaming (integrity rules — violation = demotion)

- **Tier-shopping:** the risk tier is computed from the diff's paths/globs, recorded at plan-sign,
  audited at closure. A post-closure fix landing on a LOW-tiered wave's paths is itself a
  demotion input.
- **Criteria-softening:** acceptance criteria are **hash-frozen at plan signature**. Any post-sign
  edit renders as a mandatory highlighted diff in the closure report; A2 requires zero
  unacknowledged criteria diffs.
- **Skip-stuffing:** the skip/waiver ledger is capped per milestone; each skip needs a mechanical
  referent; a skipped check whose subject later becomes a post-closure fix counts DOUBLE against
  promotion.
- **Evidence rule (the batch's central finding, 9/9 seats):** everything feeding promotion,
  demotion, or a gate is computed from git/CI/hook artifacts against **protected refs/closure tags
  the agent cannot move**. Agent-asserted content (labels, severities, narratives) is context for
  the owner — never a gate input.

## 6. Trust telemetry (V3C-84 — feeds §2)

Appended per task type at every closure (script-computed; a section of `docs/cost-log.md`):

| Field | Source (mechanical) |
|---|---|
| Post-closure fix rate | commits after the closure TAG touching the milestone's paths (path overlap, not commit message) |
| Churn | lines rewritten within N days of landing (diffstat) |
| Reverts | revert count on the milestone's range |
| Review findings | committed reviewer artifacts (BLOCKING/MINOR counts; security counted separately, weighted double) |

Thresholds are crude and conservative: **any regression blocks promotion**. Agent-asserted fields
(task-type labels, root-cause notes) may annotate rows but never gate.

## 7. Operational clauses

- **Continuity is a property of FILES, not sessions.** No agent "remembers" milestone 1 while
  running milestone 3 — sessions rot, compaction is lossy, models drift mid-run. Every closure
  writes everything the next milestone needs into repo files (process-log, plans, cost-log,
  closure report) **as if handing to a stranger** — because operationally, it is.
- **Backpressure:** at A2, if closure reports sit unreviewed past the owner's declared threshold
  (default: 2 unreviewed milestones), the pipeline auto-pauses new milestone starts. Loop
  throughput must never outrun review capacity; if the owner can't keep up, the loop throttles —
  reviews are never skimmed to keep pace.
- **Felt vs earned trust (METR clause):** the closure report displays mechanical telemetry BESIDE
  the agent's self-report so the believed-vs-actual gap stays visible. A2 retention ties to the
  post-closure fix rate, not to report delivery.

*Weight: guardrail + template. Owner directive OD-3; safety shape per the v3.2 council. Supersedes
nothing — extends V3C-68/78 and the permission matrix; P-006 records the adoption.*
