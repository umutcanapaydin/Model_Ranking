# Project Implementation Prompt (the owner's kickoff meta-prompt)

> **What this is:** the paste-ready FIRST message from the OWNER to a fresh agent. It teaches
> nothing — everything lives in the repo files (the harness auto-loads `AGENTS.md`/`CLAUDE.md`
> anyway). Its only jobs: name the task, force the read order, and demand a **comprehension
> echo-back** so orientation is a checkable gate, not a hope. Anything re-typed from memory
> eventually gets typed wrong, which is why this is a file. If it grows past one page, it is
> duplicating the repo — prune it.

---

## Prompt A — NEW PROJECT (bootstrap from the starter package)

Copy, fill the `<...>`, paste as your first message:

```text
This project runs on DevFlow (this repo was copied from the starter package).
You are the project's lead agent. I am the owner.

Task: <one sentence — what we are building>
PRD: <path or "attached" — docs/prd.md>

Do, in order:
1. Read README.md, then AGENTS.md (note the operating mode), then permission-matrix.md,
   then .agents/rules/practices.md.
2. Run `/setup-project`: ask me the setup questions and record the answers in docs/project-brief.md.
   Then Stage 0 as the README lists it, ending with `make bootstrap-check` until green.
   If we wrap/fork any OSS engine: docs/license-review.md FIRST (day-0 gate).
3. BEFORE any plan or code, echo back to me in ≤10 lines:
   - the operating mode and what it means for MY touchpoints vs yours
   - the read order you actually followed
   - the gates that block, and where each fires (pipeline-schema.html)
   - what Stage 0 found (placeholders, missing pieces)
   - your proposed first milestone boundary (M1 scope, waves, risk tiers)
   - every ambiguity you found in my inputs, each with its resolution AND the resolution's
     source: "derived from doc X" vs "needs YOUR decision" (the assumption ledger starts
     HERE, at intake, not at the first wave)
4. STOP after the echo-back. I review it; then you run `/plan-milestone`, and I approve the M1
   plan by merging its draft PR. No code before that merge.

Standing rules you must never break: you work on a branch and open a DRAFT pull request -- you never push to the default branch, never mark a PR ready, never merge, never force-push, never `--no-verify`, and never touch `.github/workflows/**`. No AI attribution anywhere. I mark ready and I merge;
escalate-NOW events (AGENTS.md) interrupt me immediately; ⛔-zone globs force HIGH tier.
```

## Prompt B — MID-PROJECT (new session / replacement agent on a running project)

```text
This is a running DevFlow project. You are taking over as lead agent
with ZERO session memory — continuity lives in FILES, and you are the stranger they
were written for.

Do, in order:
1. Run `/start-session`: it reads the latest docs/process-log.md entry, the current
   docs/plans/m{N}-plan.md and the open draft PRs, and establishes what green looks like
   before anything changes. Then read AGENTS.md and the current milestone's wave-close
   checklists. If the milestone Quality Gate is on, also the latest docs/closure-report-m{N}.md.
2. BEFORE touching anything, echo back to me in ≤10 lines:
   - the operating mode and MY touchpoints vs yours
   - current milestone + wave state (what is closed, what is in flight, citing the checklists)
   - open risks / assumptions carried in the process log (and the last closure report, if any)
   - anything in the working tree that is uncommitted or unclear (list it — do NOT "clean it up")
   - your proposed next step
3. STOP after the echo-back. I confirm or correct, then you continue.

Task for this session (one task per session): <one sentence>
Standing rules: branch, draft PR, I merge -- never the default branch, never ready, never merge, never force-push; escalate-NOW events interrupt me immediately;
revert experimental edits IN PLACE (never git checkout/restore on uncommitted work).
```

---

**Usage notes (owner):** the echo-back is the point — if it comes back wrong or thin, the agent
did not actually read the files; correct it BEFORE approving anything. One task per session
(context hygiene). For a throwaway experiment, don't use these — declare a `spike-*` branch session
instead and skip the ceremony deliberately.
