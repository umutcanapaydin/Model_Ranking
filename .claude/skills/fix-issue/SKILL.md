---
name: fix-issue
description: Use to work one triaged issue whose verdict is `fix-issue` or `work-issue`, in either mode — red test first, the smallest fix, one draft PR.
---

1. `.agents/rules/issues.md` (read at `/start-session`; open it again only after a compaction or in a new session). Confirm the issue's latest `Triage verdict:` line — in its
   body or in a comment, the last one wins — says `fix-issue` or `work-issue`
   (`gh issue view <n> --comments`).
   No verdict line at all → run `/triage-issue` on it now, then go on if it says `fix-issue` or
   `work-issue`. Another verdict → stop and say so: a `wave` verdict waits for its wave (the plan's container, worked on `wave/m<N>-w<W>`), a
   `work-enhancement` one to `/work-enhancement`. `work-issue` → the steps below AND "With a human in the loop" at
   the end; in CI there is no human, so a `work-issue` verdict stops the run there. The verdict is
   the default: a human may move an issue into the interactive lane, but you may not move one out.
2. Branch `fix/issue-<number>-<slug>`. Never `main`. Never force-push.
3. **Reproduce with a test first, and commit it alone.**
   `test: reproduce #<n> (red)` — the test cites the issue, fails, and every other test passes.
   The separate commit makes the order provable: a test that arrives with its fix cannot be told
   from one written to match it.
4. Stage tracked changes with `git add -u` and each new file — the red test from step 3 is one —
   by its explicit path; never `git add -A`, never `--amend`, never `--no-verify`.
5. Then the smallest fix that makes it green. `fix: <what>` (no `#<n>` after fix/close/resolve: it closes the
   issue on the merge, unlinked). Touch only what the issue covers —
   no refactors, no adjacent improvements, no features beyond the acceptance criteria.
   **Three attempts that leave it red, then stop** (`.agents/rules/practices.md`): comment the
   three attempts on the issue — what each changed and what the test said — open no PR, and hand
   the issue back to `/triage-issue`.
   **Green: is this a class?** More instances: one `/file-issue` (a check for the shape: `/writing-a-control`).
   **Honest green?** Red for the reported reason, not an import error; no test, assertion, fixture, `skip`,
   `noqa` or coverage floor weakened, deleted or moved; no branch on the test's inputs; no mock of the fix.
6. **The reviews the change needs — computed, not chosen.**
   `git fetch origin`, then `make review-need-branch` — this branch since it left the default branch,
   with no argument, so it runs without a prompt (inside a run, where the branch was cut from the
   integration branch: `make review-need RANGE=$(git merge-base origin/<base> HEAD)..HEAD`, §5 of
   `/pre-merge`); its last line goes into the PR body.
   - `none` → no reviewer. The red test failing before the fix and passing after, plus
     `make gate`, is the check.
   - `code-reviewer` (**heavy mode only**; light mode runs none) → the Code-Reviewer
     (`.claude/agents/Code-Reviewer.md`) as its own subagent, the issue as its acceptance criterion;
     verdict `docs/reviews/fix-issue-<n>-review.md`.
   - `security` (**light mode**, the brief's declared HIGH paths only) → the Security-Reviewer on the
     slice, with the four gate lines (`make secrets`, `deps`, `slopsquat`, `conformance`) from the last `make gate`; verdict
     `docs/reviews/fix-issue-<n>-security.md`. Heavy mode never routes a fix here (its signals go
     to the milestone Security-Reviewer; after a release, the deploy gate's security delta).
   BLOCKING → fix on the same branch, commit, and send the fix diff to the same reviewer to
   re-verify its own items (the reviewer rewrites the file's `## Verdict` line to the new verdict and appends the round below
   it: the gates read that line). Each verdict declares `**Independent:** yes`. Commit verdicts by path.
   **The third BLOCKING on the same finding ends the loop:** no fourth round, no new reviewer.
   Revert the disputed change in place, keep the PR a draft, comment the three verdicts and what
   each round changed on the issue, and hand it back to `/triage-issue` — the verdict is
   `work-issue`, and the owner's answer is an ADR (`/log-decision`) or a `docs/refusals.md` row,
   never a fourth attempt.
   **A finding the fix does not fix leaves it as an issue**, as at a wave close: each id (`**B1**`,
   `**M1**`, `**K1**`, `**R1**`) is fixed on this branch, `/file-issue`d (then `/triage-issue`), or
   refused in a sentence — a row each in the PR body's `| finding | disposition |` table:
   `| security M1 | fixed <sha> |`, `#<n>` or `refused — <why>` (`make findings-check`).
   No per-fix Tester: the next milestone Tester covers it (`.agents/rules/issues.md`, "Two working
   modes"; `docs/closure-checklist.md` §B.0); until then the red→green test and the gate are it.
7. Commit this PR's `docs/process-log.md` entry (`/pre-merge` §8 has its format) with the fix, then
   run the gate **by name**: `make gate` (lint, types, tests, records, conformance, secrets,
   deps, slopsquat; the post-edit hook runs only `make check-fast`), on that committed, clean tree.
   All green; never push red. A green gate stamps the commit: the push in step 9 and `/pre-merge` §9 accept
   the stamp (`make gate-ok`) instead of running the gate again on the same tree.
8. If the fix lands on generated files, stop and say so in the issue — an edit there is
   overwritten by the next generation run.
9. `git push -u origin HEAD`, then `gh pr create --draft --title '<fix: what>' --body '<…>'`:
   reference the issue, summarise the fix, give the review-need line, list what is not covered,
   and on a line of its own the issues step 6 filed (`Filed: #12` — never after a closing keyword).
   `Closes #<n>` — the merge closes it, and the red→green test is its verification. Only when the
   brief says `QA verification: on` does a `bug` take `Ref #<n>` instead: it closes when QA
   verifies. No AI attribution.
10. Comment the PR link on the issue. Apply no lifecycle label at draft-PR time.
11. Run `/pre-merge` before handing off. After a human merges it, `/post-merge`.
12. Never modify `.github/workflows/**`. Propose it with `make owner-bundle` and stop.

## With a human in the loop (`Triage verdict: work-issue`)

Every step above still holds. Three additions:

1. **Plan before coding.** Write the ambiguities, the options with their trade-offs, and what is
   in and out of scope. Get direction before you write code.
2. **Pause at every decision triage flagged**, and before anything large or irreversible.
3. **Name the sensitive areas you are about to touch** and confirm before touching them.

A human may choose this lane for something triage would have let run alone.
