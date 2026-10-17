# Run — golden-night

Mode: light
Started: 2026-10-17
Ended: open
Integration branch: `integration/run-golden-night` · PR: #308
Plan PR: #307
Rulings: D-206

The queue in order (D-206). It is built on the DevFlow v7.1.2 upgrade (`upgrade/devflow-v7.1.2`, D-205), which the owner merges first. The reading rules come first: an independent seat writes the fresh held-out set m24 before #293's rule is written, and all three rules are measured on it (D-206 clauses 1 and 2). The owner-only rows end as one patch for the owner (D-206 clause 9). The run closes with the release Tester and the release security review (clause 10).

On 2026-10-17 the owner allowed, in chat, a copy of the gitignored `advisor.db` in each of this run's worktrees, so an implementer's commit hook can run its `test` leg. The fresh set m24 (173 rows, written by an independent seat) is kept out of the repository until its rules are measured. On the shipped rule (`58e9f21`) it scores 81 of 173 right: 68 of 112 searches right and 13 of 61 non-searches caught.

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | 9c0c576 | issues | running |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-293 | fix/issue-293-maths-hub | none | none | running |
| issue-295 | fix/issue-295-turkish-general-words | none | none | queued |
| issue-292 | fix/issue-292-agent-with-a-coding-verb | none | none | queued |
| issue-294 | fix/issue-294-disputed | #310 | none | stacked |
| issue-297 | fix/issue-297-keep-provenance | none | none | running |
| issue-279 | fix/issue-279-test-observation | #311 | none | stacked |
| issue-304 | fix/issue-304-l1-ignored | #312 | none | stacked |
| issue-255 | fix/issue-255-closing-keywords | #313 | none | stacked |
| issue-252 | fix/issue-252-found-in | none | none | queued |
| issue-254 | fix/issue-254-amend-gate | none | none | queued |
| issue-278 | fix/issue-278-ci-history | none | none | queued |
| issue-122 | fix/issue-122-ci-offline | none | none | queued |
| issue-283 | fix/issue-283-base-policy | none | none | queued |
| issue-284 | fix/issue-284-launchd-deploy | none | none | queued |
| issue-285 | fix/issue-285-git-config | none | none | queued |
| issue-286 | fix/issue-286-dirty-worktree | none | none | queued |
| issue-287 | fix/issue-287-scoped-variables | none | none | queued |
| issue-305 | fix/issue-305-credential-helper | none | none | queued |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|

## For the owner

The run is open. This section is rewritten with the morning's merge order when it ends.
