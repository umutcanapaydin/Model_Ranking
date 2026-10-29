# Run — night-1028

Mode: light
Started: 2026-10-28
Ended: open
Integration branch: `integration/run-night-1028` · PR: #483
Plan PR: #482
Rulings: D-229

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | edaf1ce | issues | closed |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-481 | fix/issue-481-intelligence-guide | #485 | none | stacked |
| issue-477 | fix/issue-477-respelling-expiry | #490 | none | stacked |
| issue-478 | fix/issue-477-respelling-expiry | #490 | none | stacked |
| issue-479 | fix/issue-477-respelling-expiry | #490 | none | stacked |
| issue-466 | fix/issue-466-status-object | #487 | none | stacked |
| issue-453 | fix/issue-453-build-child | #489 | none | stacked |
| issue-463 | fix/issue-463-bracket-bound | #486 | none | stacked |
| issue-456 | fix/issue-456-nightly-installed | #491 | none | stacked |
| issue-457 | fix/issue-456-nightly-installed | #491 | none | stacked |
| issue-452 | fix/issue-452-tester-minors | #492 | none | stacked |
| issue-444 | fix/issue-444-deploy-gate-pin | #495 | none | stacked |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-29 | issue-444 | silent-fault | #493: the deploy gate trusts the reviewed head's trees, so a forged loose tree hides a code change and the gate says PASS (found by #444's security review, predating it); how the gate verifies the reviewed head's objects | the release delta reviews and the run's close |

## For the owner

The run stopped short of its close when the session's usage limit was reached. All eleven issues are stacked on #483, and nothing was deployed or uploaded.

1. **Merge #482**, the plan, which accepts D-229.
2. **Do not merge #483 yet.** It still owes the release Security-Reviewer's delta round. After that round, `make deploy-check` must be green.
3. **The release Tester's round is in.** It is in `docs/reviews/release-tester.md`: MINOR, 0 BLOCKING, reviewed head `e00c516`. Its tests, and the fixes for its M8 and M9, landed after that head in `0f1837f`. That commit needs the Tester's re-check before `deploy-check` passes.
4. **Answer the stop on #493**, an escalated gate bypass that predates this run.
5. **Decide #484**, whether to add a Settings button.
6. **Upload build 7**, which is already numbered, once `deploy-check` is green.
