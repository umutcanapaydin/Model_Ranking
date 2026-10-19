# Owner actions — what waits for a human

<!-- The one queue of steps only the owner can take: a merge, a workflow change (`make ci-diff` prints
     DevFlow's), a guard re-pin (`make guard-pin`), a secret, a tag and a release, a deploy, a ruling.
     An agent appends a row when its work leaves such a step, and says so in the PR's "For the owner"
     section; `/start-session` reads the open rows first. The owner -- or the agent, once the owner
     says it is done -- moves a row's Status to `done`; rows are never deleted. One command per row,
     ready to paste, so nothing reaches the owner as loose text in a chat. -->

| Date | What | Why | The command | Status |
|---|---|---|---|---|
| 2026-10-17 | Commit the v7.2 owner patch (`.claude/`, `.githooks/`, `.github/workflows/`), already applied in the upgrade's work tree, onto `upgrade/devflow-v7.2` and push it | the agent may not write these files (D-207 clause 2); the security review was waived by the owner | `cd /private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/w-up-dry && git add .claude .githooks .github && git commit -m "chore(devflow): the v7.2 owner patch (D-207)" -- .claude .githooks .github && git push` | done |
| 2026-10-18 | Apply run bug-night's owner bundle: the guard, the commit-msg hook's header, the workflows and one skill (#256, #287, #305, #317, #318, #320, #344, #81), onto its red agent half (`f716219` on `owner/bug-night-bundle-v2`), then push and open its draft | the agent may not write `.claude/`, `.githooks/` or `.github/workflows/` (D-209 clause 2); reviewed PASS WITH FINDINGS in four rounds (`docs/reviews/run-bug-night-owner-bundle-security.md`, patch sha256 `e3755901`); merge it after the integration PR #335, then start a new Claude Code session (the guard pin changes) | `cd ~/Desktop/ILGAR/model_ranking && git fetch -q && git switch owner/bug-night-bundle-v2 && git apply build/owner-bug-night.patch && git add .claude .githooks .github docs/branch-protection.md && git commit -m "chore: run bug-night's owner bundle -- the guard, hooks and workflows (D-209)" && git push -u origin owner/bug-night-bundle-v2 && gh pr create --draft --base main --fill` | open |
| 2026-10-18 | Drop `governance-contract (aggregate, unconditional)` from main's required checks, after the owner bundle merges | the bundle deletes `governance-contract.yml` (#81); a required check that never reports leaves every PR waiting | `gh api -X DELETE repos/umutcanapaydin/Model_Ranking/branches/main/protection/required_status_checks/contexts -f 'contexts[]=governance-contract (aggregate, unconditional)'` | open |
