---
name: fix-issue-prepare
description: Create a branch and write a failing test (red) for a triaged issue. Stops here for human/agent review before implementation. Use on issues triage marked safe-to-automate.
---

1. Read `.agents/rules/`. Confirm `/triage-issue` marked this issue safe to automate; if not, stop and ask.
2. Create a branch named `fix/issue-<number>-<slug>`. Never work on `main`. Never force-push.
3. Reproduce the failure with a test FIRST. The test must:
   - Cite the issue number in a comment (e.g., `# covers issue #<n>`).
   - Fail (red) before any implementation.
   - Use the project's test framework (`pytest`, `vitest`, etc.).
4. Run the full test suite. Confirm the new test is red and all OTHER tests are green.
5. Push the branch with the failing test only. Add a one-line comment on the issue: `Branch fix/issue-<n>-<slug> prepared with failing test at <file:line>. Ready for /fix-issue-implement.`
6. STOP. Do NOT implement the fix. That's the next skill's job. This split (Quality lens consortium decision) makes red-test failures distinguishable from implementation failures.
