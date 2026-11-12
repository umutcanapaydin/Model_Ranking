# Run — golive-1111

Mode: light
Started: 2026-11-11
Ended: 2026-11-12 — all milestones closed
Integration branch: `integration/run-golive-1111` · PR: #608
Plan PR: #607
Rulings: D-251, D-252
Cost: n/a

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | cb31a8e | issues | closed |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-605 | fix/issue-605-accept-growth | #609 | none | stacked |
| issue-606 | release/v1.1.0 | #610 | none | stacked |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|

## For the owner

The morning of 2026-11-12, in this order. The rows are in `docs/owner-actions.md`, "The go-live morning, 1-4".

1. **Merge the integration PR #608 with a merge commit** (never a squash). It carries the plan, so the plan PR #607
   is merged with it, and so are #604, #609 and #610.
   `make deploy-check` is PASS at its head. Both release verdicts are current at `946a89e`, and nothing after it is
   code.
2. **Tag v1.1.0 and run the hosted night.** On a copy of the served state, the night was measured to publish:
   - METR's removal (D-249);
   - the newest LiveBench and DeepSWE (D-250);
   - Terminal-Bench's accepted batch (D-251).

   Then check:
   - `/health` reads `1.1.0`;
   - the 2026-11-10 row: `long-tasks` count 0;
   - the 2026-11-08 row: `/privacy` returns 200.
3. **Archive and upload build 9** (`docs/release-testflight.md` §2).
4. **App Store Connect.**
   - Paste `docs/app-store-listing.md` (English) and `docs/app-store-listing.tr.md` (Turkish).
   - Set the privacy URL and answer "Data Not Collected".
   - Select build 9 and **Submit for Review**.

No stop: every decision was answered up front (D-251, D-252). After the go-live, the agent's next item is #611.
D-251's entry must be retired before 2026-11-26, or every night fails from that day.
