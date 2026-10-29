# Run — night-1028

Mode: light
Started: 2026-10-28
Ended: 2026-10-29 — all milestones closed
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

The run ended on 2026-10-29. All eleven issues are stacked on #483. Both release verdicts are current, and `make deploy-check` is PASS:
- Tester: MINOR, reviewed head `3cddbdd`.
- Security: MINOR, reviewed head `c29392c`.

Nothing was deployed or uploaded.

1. **Merge #482**, the plan. This accepts D-229.
2. **Merge #483**, the integration PR, as a **merge commit, never a squash**. It carries, in order: #485 (#481), #486 (#463), #487 (#466), #489 (#453), #490 (#477, #478, #479), #491 (#456, #457), #492 (#452) and #495 (#444), plus build 7 and the release Tester's tests.
3. **Answer the stop on #493.** The deploy gate trusts the reviewed head's trees, so a forged loose tree object hides a code change and the gate still says PASS. This was escalated; it predates the run. Until it is fixed, run `git fsck --full` before a deploy. It was clean on 2026-10-29.
4. **Run the UI test before the upload.** It is `ScreenPathTests` (the caption's label, M9). Then upload build 7 to TestFlight.
5. **Decide #484**: whether the guide gets a Settings button. That needs an exception to D-126's client-decls control.
6. **New issues, all triaged:** #484, #488 (`NSAllowsLocalNetworking` in Debug only), #493, #494 (#444's MINORs) and #496 (`RecursionError` in the status readers).
