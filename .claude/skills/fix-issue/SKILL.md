---
name: fix-issue
description: Use to fix one triaged issue autonomously — triage cleared it as safe to automate. One issue, one branch, one draft PR. If the issue needs design judgment, touches a sensitive area, or its scope is not pinned down, use work-issue instead.
---

1. Read `.agents/rules/`. Confirm triage marked this safe to automate. If it did not, stop and
 say so — the verdict is the default, and a human may still choose this lane, but you may not.
2. Branch `fix/issue-<number>-<slug>`. Never `main`. Never force-push.
3. **Reproduce with a test first, and commit it alone.**
 `test: reproduce #<n> (red)` — the test cites the issue, fails, and every other test passes.
 Committing it separately is what makes the order provable later; a test that arrives with its
 fix cannot be distinguished from one written to match it.
4. Stage with `git add -u`, never `git add -A` — `-A` pulls in secrets and local junk, and
 has. Never `--amend`, never `--no-verify`.
5. Then the smallest fix that makes it green. `fix: <what>`. Touch only what the issue covers —
 no refactors, no adjacent improvements, no features beyond the acceptance criteria.
6. Run the gates **by name**, not as "the gates": `make check` (lint, types, tests),
 `make secrets`, `make deps`. All green. Never push red. If a post-edit hook is installed,
 confirm its log is clean rather than assuming it ran.
7. If the fix lands on generated files, stop and say so in the issue — an edit there is
 overwritten by the next generation run.
8. Push the branch. Open a **draft** PR: reference the issue, summarise the fix, list what is not
 covered. For a `bug`, **no closing keyword** — it closes when QA verifies, not when code
 lands. For anything else, `Closes #<n>`. No AI attribution.
9. Comment the PR link on the issue. Apply no lifecycle label — at draft-PR time neither
 `dev:done` nor `qa:ready` is true.
10. Run `/pre-merge` before handing off.
11. Never modify `.github/workflows/**`. Propose the diff and stop.
