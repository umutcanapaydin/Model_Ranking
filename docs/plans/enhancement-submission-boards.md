# Enhancement plan: a board that grows by submissions publishes its arrivals without a ruling per batch (#613)

**Golden Rules served:** 3 (the most correct list for every question: `computer-use`'s list has been frozen at
the night of 2026-11-12 while 13 measured models arrived) and 1 (the data is the publisher's own, as it publishes it).

## Goal

The hosted night publishes Terminal-Bench 4.0's merged submissions as they arrive. The growth guards (D-132,
D-159) still refuse what they exist to refuse: a served row lost, a flood of rows under one name, a board that
more than doubles between two publishes, and a price change on the models already served.

## Scope

**In:**
- A named, code-held set of submission boards. One entry, `terminalbench_4`, with a written reason. Each entry
  must be a surface's own board, and a test fails closed on an entry that names none.
- Their arrivals are taken as D-251's additions are, computed instead of listed. The conditions:
  - every served row of that board is still on it;
  - one row is excused per new name (M26);
  - the arrivals are at most half of the candidate board.
- The arrivals the guards set aside are listed in the night's record (`admitted`).
- The median-price guard leaves out the arrivals an addition sets aside, listed or computed. The median then
  compares the models served on both nights.
- D-251's inert entry is retired: the night of 2026-11-12 (run 43179964312) published its names. This closes #611.

**Out:**
- The quarter itself, for every other board.
- The loss guards.
- `data/accepted-cuts.yaml`'s schema (the `additions:` list stays for a board that is not a submission board).
- METR (#615), the listing doc (#614).

## Decisions (defaults taken; the owner approves before the merge, `/work-enhancement` step 6)

1. **A doubling cap, 50%.** Measured growth is 21 rows (2026-09-29), 32 (2026-11-11), 46 (2026-11-15). The
   worst gap against a served artifact was 11 of 32 (34%), so 50% leaves headroom for a few refused nights,
   and a board that more than doubles is still published by hand.
2. **No served row lost, or no computed arrivals.** An append-only board keeps its rows. A parser or alias break
   turns served rows into "new" ones and loses the old ones, and then the guard judges the night as before.
3. **The median leaves out what the roster guard set aside.** A newcomer's price is not a price change. A feed
   that moves the served models' prices still trips.

## Phases

1. **Red.** Tests for computed arrivals:
   - one whose served rows are intact and under the cap passes;
   - a lost served row, a second row under one name, or arrivals over half the board count as before;
   - a set-aside arrival leaves the median alone;
   - the night's record lists the admitted names;
   - the submission set names only surfaces' own boards.
   *Acceptance:* the commit is red on exactly these tests.
2. **The change** in `src/app/workflows/refresh.py`, under D-253 (committed before it); D-251's entry retired in `data/accepted-cuts.yaml`.
   *Acceptance:* the tests green; `make check` green; the real refresh on a copy of the served state of
   2026-11-12 publishes.
3. **Security review** (`make review-need-branch`), then `/pre-merge`.
