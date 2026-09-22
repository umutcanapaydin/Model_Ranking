---
name: triage-issue
description: Use when an issue arrives, is reopened, comes back failed from verification, or needs re-reading before anyone works it. Reads one issue, reproduces it, labels by ACTUAL root cause, posts a diagnosis, and ends with the routing decision the rest of the flow keys on. Writes no code, opens no PR, closes nothing.
---

Read `.agents/rules/issues.md` first — the vocabulary and the pipeline live there.

1. **Reproduce it.** If there is no local runtime, reproduce through the stack or in the test
 image; how you run things is a property of your machine and belongs in
 `.agents/rules/environment.md`, not in this skill.
2. **Label by actual root cause, never the reporter's guess.** One `severity:*` on a `bug`, by
 measured impact. Only labels that already exist.
3. **Post a diagnosis comment** — what is actually wrong, where, and what the reporter saw
 instead. If the answer is "wrong component", say which one; there are no area labels.
4. **End with the routing decision**, because it is what everything downstream keys on:
 **is this safe to automate?**
 - yes → `/fix-issue`
 - no, because it needs design judgment, touches a sensitive area, or its scope is not pinned
 down → `/work-issue`
 - larger than one fix → `/work-enhancement`

 The verdict is a default, not a lock: a human may take the interactive lane anyway.

## When the issue carries `qa:failed`

**This is a bug coming back, not a fresh one.** A fix already shipped and the verifier found it
still broken.

Read the verifier's comment **and the previous fix's diff** before diagnosing, and treat
*"why did the earlier fix miss this?"* as part of the diagnosis. Without that, the second attempt
fails the same way as the first.

Clear `qa:failed`, `qa:ready` and `dev:done` when the new work starts.

## When the issue carries `qa:blocked`

The verifier could not test **at all** — environment or seed data, not code. Say that plainly
instead of re-diagnosing the original bug. The thing to fix is the blocker.

## This skill writes no code

No edits, no PR, no closing. Triage only.
