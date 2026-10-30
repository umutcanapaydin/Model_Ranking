# Run 1030 — assumptions

Reversible, wave-local answers the run took without the owner, each with where it is recorded.

| Wave | Question | Answer taken | Recorded |
|---|---|---|---|
| issue-509 | When the protected base's brief fails its hash check, which commands does the guard judge as deploys? The brief is the only record of that, and the tree's copy is the change's own | Every command, so each is refused until the object store is repaired (`git fsck`, then re-fetch). A forged, missing or malformed object triggers it -- missing includes an offline partial clone whose base brief blob is not local, and a brief committed as a link (the #509 review's M1); a missing blob must stay in this class, since deleting it let a deploy through before. A base git cannot reach at all keeps today's reading (the tree's brief). The refusal names the repair: `git fetch origin` then `git fsck --full` in the owner's terminal | the PR of #509 |
| issue-509 | `tests/unit/test_deploy_gate_dispatch.py::test_a_base_file_git_cannot_show_makes_every_dispatch_a_deploy` injected its failure into `git show`, which the gate no longer calls | Its four assertions are unchanged; only the fault injection moved to the verified reader, where `git show` was | the PR of #509 |
