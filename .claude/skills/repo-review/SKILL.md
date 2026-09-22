---
name: repo-review
description: Use after finishing a slice, a phase, or a branch and before pre-merge — and whenever asked to review, check over, or sanity-check a change. Grades the diff against THIS repository's documented practices, not generic advice. A review from memory is an opinion.
---

1. **Load every file in `.agents/rules/` first.** The review is grounded in this repo's rules or
 it is grounded in best practices in general, and those are different reviews.
2. `git diff <base>...HEAD` for the full set of changes on this branch. Read the PR's real base
 rather than assuming the default branch.
3. Review that diff with the rules as context.

Flag specifically:

- violations of `practices.md`
- **missing tests for new capabilities** — in the same change, exercising the behaviour rather
 than importing it
- README and documentation drift
- **duplicated knowledge that was not updated in sync** — one fact in two artefacts with no gate
 between them is the most recurrent defect in this corpus

Under ~30 bullets. **Correctness > clarity > nits.** A review that spends its budget on style has
spent the reviewer's attention on the cheapest thing in the diff.
