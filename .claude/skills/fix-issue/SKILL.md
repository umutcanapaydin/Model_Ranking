---
name: fix-issue
description: Use to work one triaged issue on its own branch — alone when triage says `fix-issue` (safe to automate), with a human in the loop when it says `work-issue` (design judgment, a sensitive area, or a scope not pinned down). One issue, one branch, one draft PR.
---

1. Read `.agents/rules/issues.md`. Confirm the latest triage comment ends with
   `Triage verdict: fix-issue` or `Triage verdict: work-issue` (`gh issue view <n> --comments`).
   Neither → stop and say so. `work-issue` → the steps below AND "With a human in the loop" at
   the end; in CI there is no human, so a `work-issue` verdict stops the run there. The verdict is
   the default: a human may move an issue into the interactive lane, but you may not move one out.
2. Branch `fix/issue-<number>-<slug>`. Never `main`. Never force-push.
3. **Reproduce with a test first, and commit it alone.**
   `test: reproduce #<n> (red)` — the test cites the issue, fails, and every other test passes.
   Committing it separately is what makes the order provable later; a test that arrives with its
   fix cannot be distinguished from one written to match it.
4. Stage tracked changes with `git add -u` and each new file — the red test from step 3 is one —
   by its explicit path; never `git add -A`, which pulls in secrets and local junk, and has.
   Never `--amend`, never `--no-verify`.
5. Then the smallest fix that makes it green. `fix: <what>`. Touch only what the issue covers —
   no refactors, no adjacent improvements, no features beyond the acceptance criteria.
   **Three attempts that leave it red, then stop** (`.agents/rules/practices.md`): comment the
   three attempts on the issue — what each changed and what the test said — open no PR, and hand
   the issue back to `/triage-issue`. The autonomous lane has had its turn.
6. **Fresh eyes: the Tester, alone.** Dispatch the Tester profile (`.claude/agents/Tester.md`) as
   a subagent that did not write the fix, on `$(git merge-base origin/main HEAD)..HEAD`, with the
   issue as its acceptance criterion. It confirms the red test fails on the pre-fix commit and
   passes after, that the issue's criteria have citing tests, and runs the suite; its verdict goes
   to `docs/reviews/fix-issue-<n>-tester.md` (`## Verdict` PASS / MINOR / BLOCKING, and
   `**Independent:** yes`: the Tester wrote none of the fix). BLOCKING →
   fix on the same branch, commit, and dispatch a NEW Tester, never the same one. A fix gets no
   Code-Reviewer: it is one issue's smallest change, and the red→green proof is the check that
   matters. Commit the verdict file by its path.
7. Run the gate **by name**: `make gate` (lint, types, tests, records, conformance, secrets,
   deps, slopsquat). All green. Never push red. The post-edit hook runs only `make check-fast`.
8. If the fix lands on generated files, stop and say so in the issue — an edit there is
   overwritten by the next generation run.
9. `git push -u origin HEAD`, then `gh pr create --draft --title '<fix: what>' --body '<…>'`:
   reference the issue, summarise the fix, list what is not covered. For a `bug`, **no closing keyword** — it closes when QA verifies, not when code
   lands. For anything else, `Closes #<n>`. No AI attribution.
10. Comment the PR link on the issue. Apply no lifecycle label — at draft-PR time neither
   `dev:done` nor `qa:ready` is true.
11. Run `/pre-merge` before handing off. After a human merges it, `/post-merge`.
12. Never modify `.github/workflows/**`. Propose the diff and stop.

## With a human in the loop (`Triage verdict: work-issue`)

Every step above still holds — the convention has no carve-out for interactive work. Three
additions:

1. **Plan before coding.** Write the ambiguities, the options with their trade-offs, and what is
   in and out of scope. Get direction before you write code.
2. **Pause at every decision triage flagged**, and before anything large or irreversible.
3. **Name the sensitive areas you are about to touch** and confirm before touching them.

A human may choose this lane for something triage would have let run alone.
