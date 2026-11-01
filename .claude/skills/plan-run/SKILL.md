---
name: plan-run
description: Use only when the owner opens an unattended run — "plan the next N milestones, ask me everything now, then work until it is done" — in either mode; also to resume or end one.
---

**Only the owner opens a run.** Without the owner's words, nothing here applies: a milestone runs
as `/plan-milestone` says, one wave per merge. The owner's purpose: leave in the evening, find the
draft PRs open and every decision either answered up front or written down as a stop, merge in the
morning, open the next run. What a run never does: deploy, merge a pull request, mark a PR ready,
push to the default branch, downgrade a BLOCKING, self-answer a ⛔-zone question.

**The session.** A run is unattended, so its Claude Code session must not prompt: the owner starts
it in auto mode, or with `--dangerously-skip-permissions` inside a sandbox (`INSTALL.md`,
"Permission modes"), from the repository root. In that session the hooks are the only guard.

**One record.** `docs/plans/run-<name>.md`, from `docs/run.template.md` (`<name>`: lowercase
letters, digits and hyphens), `make run-check FILE=docs/plans/run-<name>.md` green at every change:
milestones in order with the sha each started from, every wave's branch, PR and status, every stop
with its question. A session, a compaction and the owner all resume from it — never from memory.
`make closes` grades every run file in the tree, so a record that drifts from the branch turns
`make check` red. Every cell of the record has a value from the first copy: `none` where nothing
exists yet (`Plan PR: none`, `PR: none`, `Base` `none`, `Rulings: none`); a placeholder left in it
is a finding.

## 1 · Plan

1. `/start-session`. A run file with `Ended: open` already exists → go to §3.4, resume.
2. **Heavy:** for each of the N milestones the owner named, in order, `/plan-milestone` steps 1–6:
   its plan file, its GitHub milestone, its container issues and children. One plan per milestone,
   each with its acceptance criteria and `security-globs:` line. **Light:** `/triage-issue` every
   open issue with no verdict; the run is the queue in its priority order, written as the one
   milestone row `queue` / `issues` in the run file. For each queued `work-enhancement` issue,
   write its plan document now (`/work-enhancement` step 2: goal, scope, open decisions, phases)
   and commit it on the plan branch; for each `work-issue` verdict, list the decisions triage
   flagged. Those decisions are §2's questions.
3. Copy `docs/run.template.md` to `docs/plans/run-<name>.md` and fill every line: `Mode:` from
   `make mode`, `Started:` today, `Ended: open`, `Integration branch: none · PR: none`,
   `Plan PR: none`, `Rulings: none`; one milestone row per milestone (`Base` `none`, `queued`);
   one wave row per wave of every plan (light: per issue, `issue-<n>`, close record `none`),
   `queued`. `make run-check FILE=…` passes on it before it is committed.
4. Branch `plan/run-<name>`, commit the plans, the enhancement plans and the run file by path,
   push, open ONE **draft** PR: the plan PR; write its number on `Plan PR:`. No AI attribution.

## 2 · Ask everything once

One message, numbered, every open question across every plan and queued issue — a choice between
two designs, a library, an acceptance criterion whose meaning is not settled, an enhancement plan's
open decisions, a `work-issue` verdict's flagged decisions, an approval a skill would ask for mid-way
(`/work-enhancement` step 6) — each with what it decides, its options and the default the agent
would take. Ask nothing the repository already answers. The owner may answer "defaults". An
unanswered question takes its default, written down as the default.

Each answer is an ADR: `/log-decision`, with the line
`**Owner ruling:** <date>, in chat, for run <name>` (`make run-check` refuses a ruling without it);
the plan PR's merge accepts it (`/post-merge` §2a). Write their ids on the run file's
`Rulings:` line (`none` when every question took its default); amend the plans where an answer
changed them, commit on the plan branch, push.

**The owner's answers are the signal to start.** The plan PR is merged in the morning — that merge
is the owner's signature on record (`docs/autonomy-protocol.md` §1), not the condition to begin.

## 3 · Run

1. `git checkout -b integration/run-<name>` from the plan branch's head; push; open its **draft**
   PR against the default branch, body: the run file's milestones, the PRs it will carry in merge
   order, and **"merge commit, never squash"** (`/pre-merge` §1a). Write the branch and PR on the
   run file's `Integration branch:` line. Write the integration head's sha as the first
   milestone's `Base` and mark it `running`.
2. For each wave, in order (heavy: every wave of milestone 1, then 2 …; light: each issue):
   - `git checkout -b wave/m<N>-w<W>` (light: `fix/issue-<n>-<slug>` or `enhancement/<slug>`)
     **from the integration branch's head**, never from the default branch; mark the row `running`.
   - The work: the dev-test loop, red→green, `make check-fast` green. **Three failed attempts at
     one failure, then leave it:** file the bug and go on with the rest of the wave (AGENTS.md §4) —
     that is not a run stop. A question that is reversible, wave-local and outside a ⛔ zone takes
     its most conservative answer in `docs/plans/m<N>-assumptions.md` (light, which has no `<N>`:
     `docs/plans/assumptions-<name>.md`) and the wave's PR — not a
     stop either. Light: `/work-enhancement`'s approval before finalising is the owner's §2 answer,
     and its plan document is deleted before the branch is merged into the integration branch, as
     the skill says; a `work-issue`'s flagged decision not covered by §2 is a stop (`not-assumable`).
   - Heavy: `/close-wave` — every review it names, the checklist, `make wave-check`, `make gate`,
     the wave's draft PR against the default branch (its range is from the integration head,
     `/pre-merge` §5). Light: `/fix-issue` or `/work-enhancement`.
   - `git checkout integration/run-<name> && git merge --no-ff wave/m<N>-w<W>` (conflicts resolved
     here, once, never on the wave branch), `make gate`, push. Row `stacked`, PR number written.
   - The plan's last wave: the milestone closes on the integration branch — the milestone Tester's
     verdict `/close-wave` dispatched (its range from the milestone's `Base`), the last wave's
     Code-Reviewer across the milestone, Capture (`docs/closure-checklist.md` §B.2), the Quality Gate when the brief turns
     it on — then the milestone row `closed`. Nothing deploys. The next milestone's `Base` is the
     integration head now; mark it `running` and start its first wave from there. Light: `queue`
     is `closed` when every issue row is `stacked`.
3. **A stop** is one of AGENTS.md §3's Escalate-NOW events (`zone-or-criterion` among them: a ⛔
   zone, or the meaning of a criterion), a decision the owner reserved and §2 did not cover
   (`not-assumable`), or a gate leg or tool that cannot run here (`environment`: the network legs,
   a missing tool). Then: commit the wave as it stands, push, its draft PR names the block with the
   evidence; one row in the run file's Stops — the class, the question in a sentence, what the run
   continues on; the wave row `stopped`. **Continue on independent work** — the next wave with no
   dependency on the stopped one, in this milestone or the next; a milestone with a stopped wave
   and no independent wave left is `stopped`, and its Tester is not run on a partial milestone.
   Nothing independent left → `Ended: <date> — stopped at <class>, nothing independent left`,
   commit, push; the session ends with the run file as its report. A stop is never worked around:
   no downgrade, no self-answer, no "temporary" assumption in a ⛔ zone.
4. **A compaction or a new session** resumes from the run file: `/start-session` reads it; the
   `running` wave row names the branch — check it out, it exists with the commits so far; a
   reviewer that was mid-round is gone, and `/close-wave` step 3 says how a fresh one continues the
   round. Nothing is reconstructed from memory.
5. Every milestone closed → `Ended: <date> — all milestones closed`, commit, push, and the
   integration PR's body is rewritten to its final merge list: the `stacked` rows in order, the
   `stopped` ones named apart. The run file's **For the owner** section says the morning's order:
   the plan PR, the integration PR (merge commit), each stop's question. `/pre-merge` on the
   integration PR.

## 4 · The morning, and ending a run

- The owner merges the plan PR and the integration PR; `/post-merge` §2a closes the stacked
  drafts, accepts the rulings and verifies the milestone-close records the run wrote. Each stop's
  question is answered as an ADR, and the stopped wave is a new wave of the next run, or a
  `/fix-issue`.
- **The owner ends a run early** ("stop the run") → the running wave is committed and pushed, its
  row `stopped` with an `owner` row in Stops (or `stacked`, if its close had finished), any milestone
  still `running` becomes `stopped`, `Ended: <date> — owner stopped`; no new wave starts. Outside a
  run nothing changes: the next milestone is `/plan-milestone`, one wave per merge.
