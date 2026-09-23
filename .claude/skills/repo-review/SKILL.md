---
name: repo-review
description: Use at every milestone close, across the whole milestone's diff (docs/closure-checklist.md §B.0); after each phase of /work-enhancement; and whenever asked to review, check over, or sanity-check a change. Grades the diff against THIS repository's documented practices, not generic advice. A review from memory is an opinion.
---

1. **Load `.agents/rules/practices.md` and `.agents/rules/issues.md` first**, and any seed in
   `playbook-seeds.md` a rule you apply cites. The review is grounded in this repo's rules or it is
   grounded in best practices in general, and those are different reviews.
2. `git diff <base>...HEAD` for the full set of changes on this branch. Read the PR's real base
   rather than assuming the default branch. **At milestone close** the range is the whole
   milestone: from the base of its first wave to the default branch after its last merge. That
   is the one review that sees across waves — each wave was already reviewed on its own.
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

## Where the findings go

At milestone close, write the review to `docs/reviews/m{N}-repo-review.md`, each finding with an
id (`**M1**`). Then each one is fixed (a PR) or filed with `/file-issue` — a defect as `bug`, an
improvement as `enhancement` — and the file names the fix or the issue beside its id. A review
whose findings live only in the review is a list nobody queries.
