---
name: repo-review
description: Review the current branch's changes against this repo's documented practices. Loads .agents/rules/ before reviewing. Use before opening a PR.
---

1. Read every file in `.agents/rules/` so the review is grounded in this repo's standards, not generic best practices.
2. Read `subagent-profiles/Code-Reviewer.md` to align with the K.7 fresh-eyes review pattern.
3. Run `git diff <base-branch>...HEAD` to see the full set of changes on this branch.
4. Run the built-in `/review` workflow on the diff, with the rules loaded in Step 1-2 as additional context.
5. In the report, flag specifically:
   - Violations of `.agents/rules/practices.md`
   - Missing tests for new capabilities (with `file:line` evidence of REQ-ID citations per seed E.2)
   - README / CLAUDE.md / AGENTS.md drift
   - K.8 contract drift (run `grep -n` to verify shared symbol names)
   - PASS verdicts WITHOUT `file:line` evidence (automatically BLOCKING per permission-matrix §11)
6. Keep the review under ~30 bullet points. Prioritize correctness > clarity > nits.
7. Output verdict as PASS / MINOR / BLOCKING.
