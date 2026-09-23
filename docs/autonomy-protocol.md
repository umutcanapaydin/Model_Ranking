# Autonomy Protocol (**active mode: A0.5**; A1/A2 = north star, NOT ACTIVE)

> ## ⛔ STATUS — A0.5 is the only active mode
> **The agent works and commits on its own branch and opens draft pull requests; a human reviews and
> merges every PR — plan, wave and fix.** Waves close agent-side: two fresh-eyes reviews
> (`/close-wave`), green checks pinned to the closing tree, a committed checklist. There are no
> checkpoint commits. The owner's milestone test session exists only when the milestone Quality Gate
> is on (`docs/closure-checklist.md` §B.1).
>
> **Bright line: the day an agent commit reaches the default branch, that is A1 — which requires an
> explicit owner-initiated ADR, never erosion.** A1/A2 are design targets, NOT active — do not
> enable, auto-approve, or skip any owner touchpoint on their basis.

## 1. The ladder

| Level | Owner signs | Inside a milestone | Milestone boundary |
|---|---|---|---|
| **A0.5** (active) | the project brief + each milestone plan (by merging its PR) | waves close agent-side; escalate-NOW events (`AGENTS.md` §3) halt to the owner; assumption ledger active (§3); a human merges every PR | Quality Gate on: the owner's session — closure report + per-wave diffs + his own tests. Off: the milestone closes on its merged waves and Capture |
| **A1** (not active) | each milestone plan, with a scope grant (§3) | zero owner touches — agents run waves, reviews, checklists, capture | the owner reads the closure report + git |
| **A2** (not active) | the PRD, once | zero owner touches | milestone plans proceed with async notification; the owner reads closure reports + git at his own pace |

Moving above A0.5 is an owner decision recorded as an ADR in `docs/decisions.md`, and only on the
evidence in §4. At A2, per-milestone plan approval is **DEFERRED, never deleted** — the owner may
reassert it at any time without cause.

## 2. ⛔ zones and halts (every level)

- **⛔ zones** (auth, payments, crypto, personal data, prod infra, migrations) are detected by
  **path/glob patterns declared in the plan** (`security-globs`), never by agent self-classification.
  A diff touching a ⛔ glob forces the wave to HIGH (a security pass on its slice) and the slice
  receives **owner/senior line-by-line review before the release deploys**. The BLOCKING release
  security review (Stage 5.1) never moves.
- **Blocked = halt-and-notify, never improvise:** on a BLOCKING security verdict or non-assumable
  missing info, the agent (1) commits on its branch — branch pushed, draft PR naming the block with
  its evidence; (2) notifies the owner; (3) continues ONLY on independent work with no dependency on
  the blocked item. It never downgrades a BLOCKING finding, never self-answers a ⛔ question, never
  "works around" the block.

## 3. What replaces a mid-loop question

- **The assumption ledger:** where a question is reversible, wave-local and outside a ⛔ zone, the
  agent takes the most conservative interpretation, logs it in `docs/plans/m{N}-assumptions.md`, and
  surfaces every assumption in the wave's PR (and in the closure report §1b when the Quality Gate is
  on). **Not assumable — HALT instead:** any question touching a ⛔ zone, or the *meaning* of an
  acceptance criterion.
- **Write confirmation → a scope grant (A1 and above only):** the approved milestone plan declares the
  writable surface (repo worktree + an explicit allowlist of external effects). **Always blocking at
  any level:** anything outside the grant, network side-effects not in the allowlist, destructive ops
  (the permission-matrix catastrophe class), and prod credentials (agents never hold them).

## 4. The evidence rule, and what promotion would need

- **Everything that gates or feeds promotion is computed from git/CI/hook artifacts against protected
  refs the agent cannot move.** Agent-asserted content (labels, severities, narratives) is context
  for the owner — never a gate input.
- **Trust telemetry** (the closure report §3), computed from git:

| Field | Source (mechanical) |
|---|---|
| Post-closure fix rate | commits after the closure tag touching the milestone's paths (path overlap, not commit message) |
| Churn | lines rewritten within N days of landing (diffstat) |
| Reverts | revert count on the milestone's range |
| Review findings | committed reviewer artifacts (BLOCKING/MINOR counts; security counted separately, weighted double) |

- **Before A1 is even proposed:** two consecutive clean milestones by that telemetry (no post-closure
  fix commits on the milestone's paths, no unacknowledged criteria diffs, no security findings), and
  a one-time audit listing every control as script/hook/CI-enforced vs markdown-only — the
  markdown-only set is treated as ABSENT above A0.5 and must be mechanized or consciously accepted in
  the ADR.
- **Anti-gaming:** the risk tier is computed from the diff's paths and recorded in the plan;
  acceptance criteria are frozen when the plan is approved, and any later edit is shown as a diff in
  the PR that makes it; a skipped check whose subject later needs a post-closure fix counts double.

## 5. Continuity is a property of FILES, not sessions

No agent "remembers" milestone 1 while running milestone 3 — sessions rot, compaction is lossy,
models drift mid-run. Every close writes what the next milestone needs into repo files
(`docs/process-log.md`, the plans, the decision log) **as if handing to a stranger** — because
operationally, it is.
