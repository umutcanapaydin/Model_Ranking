---
record_type: register
id: roadmap-2026-09-29-post-m17
status: ratified
process_version: v6.6
date: 2026-09-29
---
# Roadmap snapshot — after M17 (2026-09-29)

A snapshot, never edited after it is written (seed I.1).

**Where the product is.** One application on the owner's Mac, plus an iOS app on the simulator:
- **The engine** runs as a launchd service from a deployed release (D-170). It refreshes nightly,
  derives every floor from the served board (D-159), and serves 63 boards' standings as positions on
  `/v1/boards` (D-167).
- **The app** reads the question on the device into a surface plus a declared language or domain
  (D-168). When more than one board is chosen, it shows the product's own combined list, with a
  detail naming every board.

Nothing is deployed beyond the owner's machine.

**What is next.** M18 (`docs/plans/m18-plan.md`), in the four areas the owner chose on 2026-09-29:
- reading the question better (#66, #73), through signals decided in code or a question back to the
  reader, with each bar set after a baseline;
- screen quality: the owner's UI findings (#63) and a committed UI test target (#69);
- the backlog of filed bugs and small improvements;
- first-release preparation: data licences (W-129), go-live checks (#26), the security invariants
  list (W-131), and a stranger's first use (W-123).

**After M18, not yet planned.** The first deploy beyond the owner's machine and the Stage 5 release
review.
