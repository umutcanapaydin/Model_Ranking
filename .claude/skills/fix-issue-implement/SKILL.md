---
name: fix-issue-implement
description: On a prepared branch with a red test, implement the smallest fix to green. Run lint + tests + Stage 2 commit-gate. Push branch + open DRAFT PR linked to the issue. Never merge.
---

1. Verify we're on a `fix/issue-<n>-<slug>` branch (set up by `/fix-issue-prepare`). If not, stop and ask.
2. Verify the prepared failing test exists and is currently red.
3. Implement the SMALLEST possible fix to make the test green:
   - Touch only files relevant to the issue (per scope boundary in permission-matrix.md).
   - Do NOT refactor unrelated code.
   - Do NOT add features beyond the issue's acceptance criteria.
4. Run `make check` (lint + type + test). All must be green.
5. Run `make secrets` (gitleaks scan). Must be green.
6. Run `make deps` (pip-audit). Must be green.
7. The Stage 2 PostToolUse hook will fire `make check` automatically; verify the `.claude/last-check.log` is clean.
8. Push the branch.
9. Open a DRAFT PR with body containing:
   - `Closes #<issue-number>` (auto-link)
   - One-paragraph summary of the fix
   - List of files touched
   - Test names that cover the fix (with `file:line` references — required for PASS verdict per permission-matrix §11)
   - What is NOT covered + risks queued to next milestone
10. Post a one-line comment on the issue: `Draft PR opened: <PR-link>. Human review required.`
11. NEVER merge. NEVER `--no-verify`. NEVER force-push. The agent opens; the human merges. Branch protection on `main` enforces this.
