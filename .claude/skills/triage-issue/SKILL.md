---
name: triage-issue
description: Use when an issue arrives or is filed — /file-issue and /close-wave hand every new issue here — is reopened, comes back failed from verification, or needs re-reading before anyone works it. Reads one issue, reproduces it, labels by ACTUAL root cause, posts a diagnosis, and ends with the routing decision the rest of the flow keys on. Writes no code, opens no PR, closes nothing.
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
     down → `/fix-issue` with a human in the loop (verdict `work-issue`)
   - larger than one fix → `/work-enhancement`

   Write it as the diagnosis comment's **last line, exactly**:
   `Triage verdict: fix-issue` · `Triage verdict: work-issue` · `Triage verdict: work-enhancement`.
   That line is what `/fix-issue` checks; a verdict in prose is one nobody can find.
   The verdict is a default, not a lock: a human may take the interactive lane anyway.

## When the issue is an `enhancement`

There is nothing to reproduce. Step 1 becomes **pin the scope**: what changes, what stays as it
is, and how anyone would know it is done — in the diagnosis comment, three lines. Then the same
routing: one small change → `fix-issue`; several slices → `work-enhancement`; an owner decision
first → `work-issue`. An enhancement nobody takes up now stays open: `/plan-milestone` reads the
open queue and either plans it or names it as left out.

## When the issue records three failed attempts

It was filed by the rule in `.agents/rules/practices.md` ("Three attempts, then stop"). Read the
three attempts before diagnosing: they are what did not work, and why. **Never `fix-issue`**: the
autonomous lane is what already failed three times. The verdict is `work-issue` unless the
diagnosis shows the scope is larger than one fix.

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
