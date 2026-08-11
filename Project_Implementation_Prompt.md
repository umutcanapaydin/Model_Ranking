# Project Implementation Prompt (v3.3 — the owner's kickoff meta-prompt)

> **What this is:** the paste-ready FIRST message from the OWNER to a fresh agent. It teaches
> nothing — everything lives in the repo files (the harness auto-loads `AGENTS.md`/`CLAUDE.md`
> anyway). Its only jobs: name the task, force the read order, and demand a **comprehension
> echo-back** so orientation is a checkable gate, not a hope.
> *Doc-weight addition, owner-requested 2026-07-05 (origin: the "re-typed every time" F1 class —
> anything re-typed from memory eventually gets typed wrong). If this file grows past one page,
> it is duplicating the repo — prune it.*

---

## Prompt A — NEW PROJECT (bootstrap from the starter package)

Copy, fill the `<...>`, paste as your first message:

```text
This project runs on General Pipeline v3.3 (this repo was copied from the starter package).
You are the project's lead agent. I am the owner.

Task: <one sentence — what we are building>
PRD / brief: <path or "attached" — docs/prd.md + docs/project-brief.template.md filled>

Do, in order:
1. Read START_HERE.md, then AGENTS.md, then docs/autonomy-protocol.md (note the ACTIVE mode),
   then permission-matrix.md, then .agents/rules/practices.md.
2. Run Stage 0: fill the placeholders, then `make bootstrap-check` until green.
   If we wrap/fork any OSS engine: docs/license-review.md FIRST (day-0 gate).
3. BEFORE any plan or code, echo back to me in ≤10 lines:
   - the operating mode and what it means for MY touchpoints vs yours
   - the read order you actually followed
   - the 2 BLOCKING gates and where they fire
   - what Stage 0 found (placeholders, missing pieces)
   - your proposed first milestone boundary (M1 scope, waves, risk tiers)
   - every ambiguity you found in my inputs, each with its resolution AND the resolution's
     source: "derived from doc X" vs "needs YOUR decision" (v4.0 — the assumption ledger
     starts HERE, at intake, not at the first wave)
4. STOP after the echo-back. I review it, then sign the M1 plan. No code before my signature.

Standing rules you must never break: you never run git (I make all commits);
escalate-NOW events (AGENTS.md §3) interrupt me immediately; ⛔-zone globs force HIGH tier.
```

## Prompt B — MID-PROJECT (new session / replacement agent on a running project)

```text
This is a running General Pipeline v3.3 project. You are taking over as lead agent
with ZERO session memory — continuity lives in FILES, and you are the stranger they
were written for.

Do, in order:
1. Read note.txt, then START_HERE.md, then AGENTS.md, then docs/autonomy-protocol.md
   (note the ACTIVE mode), then the latest docs/closure-report-m{N}.md, then
   docs/plans/<current milestone plan> and its wave-close checklists, then
   docs/process-log.md (last 3 entries).
2. BEFORE touching anything, echo back to me in ≤10 lines:
   - the operating mode and MY touchpoints vs yours
   - current milestone + wave state (what is closed, what is in flight, citing the checklists)
   - open risks / assumptions carried from the last closure report
   - anything in the working tree that is uncommitted or unclear (list it — do NOT "clean it up")
   - your proposed next step
3. STOP after the echo-back. I confirm or correct, then you continue.

Task for this session (one task per session): <one sentence>
Standing rules: you never run git; escalate-NOW events interrupt me immediately;
revert experimental edits IN PLACE (never git checkout/restore on uncommitted work).
```

---

**Usage notes (owner):** the echo-back is the point — if it comes back wrong or thin, the agent
did not actually read the files; correct it BEFORE signing anything. One task per session
(context hygiene). For a throwaway experiment, don't use these — declare a `spike-*` L0 lane
session instead and skip the ceremony deliberately.
