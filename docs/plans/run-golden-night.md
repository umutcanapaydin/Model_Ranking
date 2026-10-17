# Run — golden-night

Mode: light
Started: 2026-10-17
Ended: open
Integration branch: `integration/run-golden-night` · PR: #308
Plan PR: #307
Rulings: D-206

The queue in order (D-206). It is built on the DevFlow v7.1.2 upgrade (`upgrade/devflow-v7.1.2`, D-205), which the owner merges first. The reading rules come first: an independent seat writes the fresh held-out set m24 before #293's rule is written, and all three rules are measured on it (D-206 clauses 1 and 2). The owner-only rows end as one patch for the owner (D-206 clause 9). The run closes with the release Tester and the release security review (clause 10).

On 2026-10-17 the owner allowed, in chat, a copy of the gitignored `advisor.db` in each of this run's worktrees, so an implementer's commit hook can run its `test` leg. The fresh set m24 (173 rows, written by an independent seat) is kept out of the repository until its rules are measured. On the shipped rule (`58e9f21`) it scores 81 of 173 right: 68 of 112 searches right and 13 of 61 non-searches caught. #293's rule scores the same on it (81 of 173; no row lost or gained, 3 moved between wrong surfaces) and fixes both its golden questions, so it ships (D-206 clause 2). #292's scores 82 (one search gained, none lost) and ships too. The record is `docs/research/reading-wave-m24-probe.md`.

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | 9c0c576 | issues | running |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-293 | fix/issue-293-maths-hub | #316 | none | stacked |
| issue-295 | fix/issue-295-turkish-general-words | none | none | stopped |
| issue-292 | fix/issue-292-agent-with-a-coding-verb | #324 | none | stacked |
| issue-294 | fix/issue-294-disputed | #310 | none | stacked |
| issue-297 | fix/issue-297-keep-provenance | #315 | none | stacked |
| issue-279 | fix/issue-279-test-observation | #311 | none | stacked |
| issue-304 | fix/issue-304-l1-ignored | #312 | none | stacked |
| issue-255 | fix/issue-255-closing-keywords | #313 | none | stacked |
| issue-252 | owner/golden-night-bundle | none | none | stopped |
| issue-254 | owner/golden-night-bundle | none | none | stopped |
| issue-278 | owner/golden-night-bundle | none | none | stopped |
| issue-122 | owner/golden-night-bundle | none | none | stopped |
| issue-283 | owner/golden-night-bundle | none | none | stopped |
| issue-284 | owner/golden-night-bundle | none | none | stopped |
| issue-285 | owner/golden-night-bundle | none | none | stopped |
| issue-286 | owner/golden-night-bundle | none | none | stopped |
| issue-287 | fix/issue-287-scoped-variables | none | none | stopped |
| issue-305 | fix/issue-305-credential-helper | none | none | stopped |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-17 | issue-295 | not-assumable | The owner's design default (the general-words rule gives way when another surface's example scores confidently) cannot fix the golden question without sending general Turkish "yapay zeka" questions off everyday: four attempts, all on #295. Choose: (a) a grammar rule (a verb clause right before "yapay zeka" names a task), to be measured on a fresh set; (b) ship attempt 3, about 1 in 6 general questions leaving everyday; (c) leave it to the on-device model tier and mark the golden question disputed | issue-292 |
| 2026-10-17 | issue-252 | control-change | Apply the owner bundle (skill text): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-254 | control-change | Apply the owner bundle (a .githooks/post-rewrite hook): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-278 | control-change | Apply the owner bundle (ci.yml fetch-depth): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-122 | control-change | Apply the owner bundle (ci.yml loopback-only pytest): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-283 | control-change | Apply the owner bundle (review-need and the deploy gate read the base's brief (agent half on the bundle branch)): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-284 | control-change | Apply the owner bundle (the guard refuses the launchd scripts): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-285 | control-change | Apply the owner bundle (the guard refuses git config --edit and writes into .git/config and hooks): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-286 | control-change | Apply the owner bundle (the guard refuses removing a dirty worktree): one line, given under For the owner | the rest of the queue |
| 2026-10-17 | issue-287 | control-change | Not in the bundle: a variable scoped in a subshell, function, pipeline or loop needs per-command depth in the guard, a larger change than tonight's | the rest of the queue |
| 2026-10-17 | issue-305 | control-change | Not in the bundle: the agent drafting the list of code-running git config keys was stopped by a safety classifier, so the list is the owner's to write or ask for | the rest of the queue |

## For the owner

The run is open. This section is rewritten with the morning's merge order when it ends.
