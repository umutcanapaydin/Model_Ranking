# Run — v100

Mode: light
Started: 2026-11-06
Ended: 2026-11-06 — all milestones closed
Integration branch: `integration/run-v100` · PR: #596
Plan PR: #595
Rulings: D-246
Cost: n/a

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | f2c3808 | issues | closed |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-594 | release/v1.0.0 | #597 | none | stacked |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|

## For the owner

In the morning, in this order:
1. Merge the plan PR #595, then the integration PR #596, each with a **merge commit** (never a squash). #596 carries
   `release/v1.0.0` (#597): both verdicts, the version bump, M20's fix and `docs/releases/v1.0.0.md`.
2. Tag and deploy v1.0.0 and upload TestFlight build 8: the 2026-11-06 row in `docs/owner-actions.md`. Do this
   BEFORE the bundles: the deploy gate counts an applied bundle as code after the reviewed heads.
3. Apply the two bundles (the 2026-11-05 rows): the nightly notice `9d89f61f`, then the guard `b233e259`, and start a
   new Claude Code session after the guard.
4. Tell the agent the bundles are merged. A short delta review confirms the merged bytes are the reviewed patches,
   so the nightly keeps deploying. #561 and #586 then close.

No stop: nothing in the run needed the owner beyond D-246's answers.
