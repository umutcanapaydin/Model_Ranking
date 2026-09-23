---
name: work-enhancement
description: Use for enhancement-labelled work that is larger than one fix — a feature, a migration, a refactor spanning several slices. Multi-phase work through ONE pull request, planned before any code is written.
---

1. Branch `enhancement/<slug>` or `enhancement/issue-<number>-<slug>`.
2. **Plan first.** Write the plan as a document: goal, scope in and out, open decisions, and an
   ordered list of phases — each a small independently reviewable slice with its own acceptance
   check. Resolve the open decisions with the human BEFORE coding.
3. Commit the plan alone, push, open a draft PR, and render the phases as a task list in the body.
4. Land one phase at a time:
   - behavioural change → a test that goes red first, in its own commit
   - pure removal or refactor → no new test, say so
   - gates green after each phase, never push red
   - one conventional commit per phase
   - `/repo-review` after each phase, then tick that phase's box in the PR body
5. After the last phase: `/repo-review` across the whole branch diff, then `/pre-merge`. A review
   finding this PR does not fix is filed with `/file-issue`, and a phase still red after three
   attempts stops the same way (`.agents/rules/practices.md`).
6. Ask for approval before finalising. Only then delete the plan document — **an enhancement's
   plan never lands on the default branch** (a milestone plan does; that is `/plan-milestone`'s).
   The PR stays a draft; the human marks it ready. After the merge, `/post-merge`.
