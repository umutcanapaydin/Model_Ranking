---
name: post-merge
description: Use immediately after a human has merged a PR — to clean up the branch, move the issue to the right lifecycle state, and hand off to verification. Also when asked what happened to a merged change or whether something is ready to verify. Never merges anything itself.
---

Runs **only after a human merges.** Read `.agents/rules/issues.md` first.

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

## 3 · Route the issue by what it actually is

Read its state and labels, then:

- **`bug`** → stays open, gets `dev:done`, one comment linking the
  merged PR. **Do not set `qa:ready`** — merged is not deployed, and you have no signal for a
  deploy. Wait to be told.
- **`bug` that the merge already closed** → **this is a finding, not a tidy-up.** A bug's PR is
  not supposed to carry a closing keyword, so a closed bug means one got past `/pre-merge`.
  Reopen it, apply `dev:done`, and **report which PR carried the keyword.** Reopening quietly
  leaves the hole open for the next one.
- **non-`bug`** → the merge closing it is correct. Leave it closed.

## 4 · Later, when you are told

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
