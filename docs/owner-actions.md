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
