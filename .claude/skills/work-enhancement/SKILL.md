---
name: work-enhancement
description: Use in LIGHT mode for work triage routed as `work-enhancement` — a feature, a migration or a refactor spanning several slices, through one planned PR.
---

**Light mode only.** `make mode` prints `heavy` → this work is a wave: it joins a wave's container
issue (`Triage verdict: wave`), and `/close-wave` reviews it. In the field, a wave run through this
skill's plan-first draft PR was merged twice with a BLOCKING review still open.

0. Confirm the issue's latest `Triage verdict:` line says `work-enhancement` (`gh issue view <n>
   --comments`; the last one wins). Anything else → stop and name the skill it routes to.
1. Branch `enhancement/<slug>` or `enhancement/issue-<number>-<slug>`.
2. **Plan first.** Write the plan as `docs/plans/enhancement-<slug>.md`: goal, scope in and out, open decisions, and an
   ordered list of phases — each a small independently reviewable slice with its own acceptance
   check. Resolve the open decisions with the human BEFORE coding.
3. Commit the plan alone, push, open a draft PR, and render the phases as a task list in the body,
   with `Closes #<n>` on a line of its own (the merge closes the issue).
4. Land one phase at a time:
   - behavioural change → a test that goes red first, in its own commit
   - pure removal or refactor → no new test, say so
   - `make check` green after each phase (the post-edit hook already runs its legs; the push runs
     `make gate`), never push red
   - one conventional commit per phase, then tick that phase's box in the PR body
5. After the last phase: `make review-need-branch` (inside a run: `make review-need RANGE=...` from
   the integration branch, `/pre-merge` §5), the whole branch — a line naming `security` → the Security-Reviewer on it, with
   the four gate lines (`make secrets`, `deps`, `slopsquat`, `conformance`) from the last `make gate`
   (`docs/reviews/enhancement-<slug>-security.md`); light mode runs no Code-Reviewer, and no
   Tester per enhancement: the milestone Tester runs before the next release, on everything
   merged since its last verdict (`docs/closure-checklist.md` §B.0). Then `/pre-merge`. A finding this PR does not fix is filed with `/file-issue`, and
   a phase still red after three attempts stops the same way (`.agents/rules/practices.md`).
6. Ask for approval before finalising. Only then delete the plan document — **an enhancement's
   plan never lands on the default branch** (a milestone plan does; that is `/plan-milestone`'s).
   The PR stays a draft; the human marks it ready. After the merge, `/post-merge`.
