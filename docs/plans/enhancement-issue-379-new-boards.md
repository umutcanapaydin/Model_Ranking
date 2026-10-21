# Enhancement plan: new external boards, each licence-checked, served or skipped with its reason (#379)

**Golden Rules served:** 1 (every source used lawfully, under D-215's rule) and 3 (the richer the boards, the more correct the list).

## Goal

Each board below is either served through the issue's five steps or recorded as skipped with its reason.

- **First tier:** OSWorld / OSWorld-Verified, METR time horizons, Humanity's Last Exam, DeepResearchBench.
- **Second tier:** SciCode, LiveBench, SimpleBench, Vending-Bench 2, Video-MME, GDPval.

## Scope

**In, per board:**
1. The licence read: the publisher's stated terms for the leaderboard data, recorded under D-185's table with publisher, licence, link and the date read.
2. A declared source in `src/app/workflows/sources.py`, with a parser test on a recorded fixture and a contract test.
3. A D-148 calibration, with the board's `score_anchor` pinned if it becomes a primary.
4. Credits.
5. The unlinked-id count. A board under half linked is not served until its aliases are fixed.

**Out:**
- a board found only in a paper's tables;
- a board with fewer than 15 ranked models (D-145);
- a board behind a sign-in, a token or a click-through, since the nightly refresh holds no secret (#387);
- a board whose publisher forbids non-commercial use (D-215).

Each is skipped, with the reason recorded.

## Decisions

1. **The licence rule is D-215's,** applied board by board. It needs no new owner ruling. A board the rule does not clearly admit is skipped, and the reason is written down.
2. **Where METR's board goes:** the run's decisions message asks.
3. **A board that adds a new surface:** the run's decisions message asks.

## Phases

One phase per board, in tier order. For each:
- the licence read and the skip-or-serve record;
- for a served board, red parser tests, then the source, the calibration, Credits and the unlinked-id count.

*Acceptance per board:* `make check` green, the board served or skipped with its reason, and the nightly refresh reading it with no new secret.
