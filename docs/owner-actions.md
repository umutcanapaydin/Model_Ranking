# Owner actions — what waits for a human

<!-- The one queue of steps only the owner can take: a merge, a workflow change (`make ci-diff` prints
     DevFlow's), a guard re-pin (`make guard-pin`), a secret, a tag and a release, a deploy, a ruling.
     An agent appends a row when its work leaves such a step, and says so in the PR's "For the owner"
     section; `/start-session` reads the open rows first. The owner -- or the agent, once the owner
     says it is done -- moves a row's Status to `done`; rows are never deleted. One command per row,
     ready to paste, so nothing reaches the owner as loose text in a chat. -->

| Date | What | Why | The command | Status |
|---|---|---|---|---|
