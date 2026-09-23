---
name: fix-issue
description: Use to fix one triaged issue autonomously — triage cleared it as safe to automate. One issue, one branch, one draft PR. If the issue needs design judgment, touches a sensitive area, or its scope is not pinned down, use work-issue instead.
---

1. Read `.agents/rules/issues.md`. Confirm the latest triage comment ends with
   `Triage verdict: fix-issue` (`gh issue view <n> --comments`). If it does not, stop and say so
   — the verdict is the default, and a human may still choose this lane, but you may not.
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
6. **Fresh eyes: the Tester, alone.** Dispatch the Tester profile (`.claude/agents/Tester.md`) as
   a subagent that did not write the fix, on `$(git merge-base origin/main HEAD)..HEAD`, with the
   issue as its acceptance criterion. It confirms the red test fails on the pre-fix commit and
   passes after, that the issue's criteria have citing tests, and runs the suite; its verdict goes
   to `docs/reviews/fix-issue-<n>-tester.md` (`## Verdict` PASS / MINOR / BLOCKING). BLOCKING →
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
11. Run `/pre-merge` before handing off.
12. Never modify `.github/workflows/**`. Propose the diff and stop.
