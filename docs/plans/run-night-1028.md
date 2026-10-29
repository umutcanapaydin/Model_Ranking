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

The run is planned and waits for the answers to its decisions message. Nothing is merged, deployed or uploaded by the run.
