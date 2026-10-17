---
name: fix-issue
description: Use to work one triaged issue on its own branch, in light and heavy mode — alone when triage says `fix-issue` (safe to automate), with a human in the loop when it says `work-issue` (design judgment, a sensitive area, or a scope not pinned down). Red test first, the smallest fix, the reviews make review-need asks for, one draft PR. In heavy mode a fix is a one-issue wave.
---

1. Read `.agents/rules/issues.md`. Confirm the issue's latest `Triage verdict:` line — in its
   body or in a comment, the last one wins — says `fix-issue` or `work-issue`
   (`gh issue view <n> --comments`).
   Neither → stop and say so: a `wave` verdict belongs to its wave (`/close-wave`), a
   `work-enhancement` one to `/work-enhancement`. `work-issue` → the steps below AND "With a human in the loop" at
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
6. **The reviews the change needs — computed, not chosen.**
   `make review-need RANGE=$(git merge-base origin/<base> HEAD)..HEAD` — the range given, so it
   measures this branch and never exits for want of a default branch; its last line goes into the
   PR body.
   - `none` → no reviewer. The red test failing before the fix and passing after, plus
     `make gate`, is the check. In the field, fixes under ~130 product lines got a ~100-line
     verdict for 6–10 changed lines, and 3 of 4 got no product change from it.
   - `code-reviewer` (**heavy mode only**; light mode runs none) → the Code-Reviewer
     (`.claude/agents/Code-Reviewer.md`) as its own subagent, the issue as its acceptance criterion;
     verdict `docs/reviews/fix-issue-<n>-review.md`.
   - `security` (**light mode**) → the Security-Reviewer on the slice; verdict
     `docs/reviews/fix-issue-<n>-security.md`. Heavy mode never routes a fix here: its security
     signals are printed for the milestone Security-Reviewer on the plan's last wave, and a fix after
     a release meets the deploy gate's security delta before it ships.
   - `code-reviewer+security` → light mode only, and light runs the Security-Reviewer alone.
   BLOCKING → fix on the same branch, commit, and send the fix diff to the same reviewer to
   re-verify its own items. Each verdict declares `**Independent:** yes`. Commit verdicts by path.
   **The third BLOCKING on the same finding ends the loop:** no fourth round, no new reviewer.
   Revert the disputed change in place, keep the PR a draft, comment the three verdicts and what
   each round changed on the issue, and hand it back to `/triage-issue` — the verdict is
   `work-issue`, and the owner's answer is an ADR (`/log-decision`) or a `docs/refusals.md` row,
   never a fourth attempt. In the field the loop ran to five and six rounds.
   **A finding the fix does not fix leaves it as an issue**, as at a wave close: each MINOR and
   queued-risk id (`**M1**`, `**R1**`) is fixed on this branch, `/file-issue`d (then
   `/triage-issue`), or refused in a sentence — the PR body lists them.
   No per-fix Tester. A fix is covered by the next milestone Tester — heavy: the open plan's, on
   its last wave; light: the one before the next release, on everything merged since its last
   verdict (`docs/closure-checklist.md` §B.0). Until then the red→green test and the gate are it.
7. Run the gate **by name**: `make gate` (lint, types, tests, records, conformance, secrets,
   deps, slopsquat). All green. Never push red. The post-edit hook runs only `make check-fast`.
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
12. Never modify `.github/workflows/**`. Propose the diff and stop.

## With a human in the loop (`Triage verdict: work-issue`)

Every step above still holds — the convention has no carve-out for interactive work. Three
additions:

1. **Plan before coding.** Write the ambiguities, the options with their trade-offs, and what is
   in and out of scope. Get direction before you write code.
2. **Pause at every decision triage flagged**, and before anything large or irreversible.
3. **Name the sensitive areas you are about to touch** and confirm before touching them.

A human may choose this lane for something triage would have let run alone.
