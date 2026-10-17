---
name: post-merge
description: Use immediately after a human has merged a PR, and when asked what happened to a merged change or whether it is ready to verify. Never merges anything itself.
---

Runs **only after a human merges.** `.agents/rules/issues.md` (read at `/start-session`; open it again only after a compaction or in a new session).

## 1 · Confirm the merge before deleting anything

```bash
gh pr view <pr> --json state,mergedAt
```

If it is not MERGED, **stop and delete nothing.** This check is the safety gate: it is what makes
sure unmerged work is never lost to a cleanup that ran too early.

## 2 · Clean up

```bash
git checkout <default-branch> && git pull
git branch -d <branch>
git push origin --delete <branch>
```
`-d` refuses a branch that was **squash-merged**, because its commits never reached the default
branch. Step 1 already proved the PR MERGED, so then — and only then — `git branch -D <branch>`.
A squash also drops the head a review verdict names: the milestone Tester's `**Reviewed head:**` on
the plan's last wave is now unreachable, and `make deploy-check` fails closed until the Tester
runs again. Tell the owner; `docs/branch-protection.md` asks for merge commits for this reason.

## 2b · A plan PR (`plan/m<N>`)

The owner approved the plan. Start wave 1 now: branch `wave/m<N>-w1` from the default branch, work its
container issue's tasks (the dev-test loop, AGENTS.md §4), then `/close-wave`. Nothing else starts a
wave.

## 2a · An integration PR (`integration/<name>`)

Step 1 on the integration PR. Then, for each PR its body says it carries:

```bash
gh pr view <stacked-pr> --json state,mergedAt   # MERGED once its head commit is on the default branch
```

A merge commit lands every stacked branch's commits, and GitHub marks each stacked PR MERGED by
itself. One still OPEN means the integration PR was squashed, or that branch was left out of the
stack: close it with one comment naming the integration PR and the commit that carries its change.
The stacked draft is the record of that change, open or closed; it is never deleted. Then step 2
for the integration branch and every stacked branch, and steps 3–6 once per stacked PR's issues:
the integration PR's `Closes` lines are what closed them. A PR the run file lists as `stopped`
is not left out of the stack by mistake: it stays open for the next run or `/fix-issue`, and is
not closed here.

A run's integration PR (`integration/run-<name>`, `/plan-run`): the same, and §7 already ran
inside the run, on the integration branch, for every milestone it closed — verify the records
exist (`docs/reviews/m<N>-tester.md`, the `## Across the milestone` section of the last wave's review, the Capture entries,
`docs/plans/run-<name>.md` with its `Ended:` filled and `make run-check` green) rather than
running them again. A stop row in the run file is an open question for the owner: its answer is an
ADR, and the stopped wave goes to the next run or to `/fix-issue`. The plan PR's merge is the
owner's signature on the run's rulings: they are accepted as they stand, like every ADR the default
branch carries — no status line is added.

## 3 · Route the issue by what it actually is

Read its state and labels, and the brief's `QA verification:` (`off` unless it says `on`):

- **QA off (the default)** → every issue the PR resolved is closed by the merge, a `bug` included:
  one comment on each naming the merged PR and the test that went red, then green. If one is still
  open, close it with that comment. That is the whole step.

**QA on** (`.agents/rules/issues-qa.md`):

- **`bug`** → stays open, gets `dev:done`, one comment linking the
  merged PR. **Do not set `qa:ready`** — merged is not deployed, and you have no signal for a
  deploy. Wait to be told.
- **`bug` that the merge already closed** → **this is a finding, not a tidy-up.** A bug's PR is
  not supposed to carry a closing keyword, so a closed bug means one got past `/pre-merge`.
  Reopen it, apply `dev:done`, and **report which PR carried the keyword.** Reopening quietly
  leaves the hole open for the next one.
- **non-`bug`** → the merge closing it is correct. Leave it closed.

## 4 · Later, when you are told (QA on)

- **"It is deployed"** → each `bug` with `dev:done` from that deploy swaps to `qa:ready`.
- **`qa:passed`** (the verifier's) → close the issue with one comment naming the verification.
- **`qa:failed`** → `/triage-issue` it now: it is a bug coming back, and triage has a section for
  exactly that.
- **`qa:blocked`** → `/triage-issue` too: the thing to fix is the blocker, not the bug.

`/start-session` lists open issues carrying `qa:failed` or `qa:blocked`, so one that arrives
between sessions is not missed.

## 5 · Swap labels, never accumulate

`gh issue edit <n> --remove-label "<old>" --add-label "<new>"`. Two lifecycle labels on one issue
reads as two states at once, and a label people cannot trust is worse than no label.

## 6 · Say what was left

Anything uncovered, queued or knowingly skipped goes on the issue now. This is the last moment
the context is still in anyone's head.

The lifecycle vocabulary is closed. If the state you want is not in it, the answer is not a new
label — it is that the state is not real yet.

## 7 · The plan's last wave (heavy mode)

The merged PR was a `wave/*` branch whose close says `Last wave of the plan: yes` → every wave of
the milestone has merged, and with it the milestone close (`/close-wave` step 7 ran it on that
branch): verify it arrived — the `## Across the milestone` section of the last wave's review, the
Capture entries, the closure report when the Quality Gate is on — rather than running it again. A
wave closed before `v7.2` has none of it on its branch: walk `docs/closure-checklist.md` §B now, on a
`close/m<N>` branch with its own draft PR. Nothing deploys at a milestone close.
