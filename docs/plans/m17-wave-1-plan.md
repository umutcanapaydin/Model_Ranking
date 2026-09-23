---
record_type: plan
id: m17-wave-1-plan
status: draft
process_version: v6.0
date: 2026-09-23
---
# M17-W1 plan — floors from the board, every build

**Working plan for the `enhancement/m17-w1-floors-every-build` pull request**, deleted before merge.
Milestone plan: `docs/plans/m17-plan.md` §2 W1. Risk: **MED**, so one combined independent review.

## Goal

D-159: every surface's floor is the top third of its board's rows (D-148 clause 1), computed from the
artifact being served, not kept by hand in `categories.py`. Closes W-128.

## What the code does today (measured 2026-09-23)

- `CategorySpec.min_quality` is a hand-kept number on each of the 14 surfaces
  (`src/app/workflows/categories.py`). The following read it:
  - `recommend()`'s Budget Pick (`recommend.py:483`);
  - the subscription answer (`subscribe.py:437`, `:575`);
  - `/v1/categories` (`adapter/main.py:1290`, D-152), whose value the detail screen shows.
- `scripts/survey_boards.py::floors` computes the same rule (`top_third` over the board's rows) to
  MEASURE the hand-kept numbers, and `tests/unit/test_floor_rule.py` compares the code with a
  research record of one day's measurement. Six floors are stale against the fresh boards (W-128).
- `recommend.MIN_QUALITY_PCT` / `MIN_QUALITY_ELO` repeat two of the hand-kept numbers.

## Decision made on the owner's behalf (implementation, not policy)

**Derived where it is read, from the served artifact's own rows**, through one function
(`app.workflows.floors`), rather than computed at build time into a new table. It is the same number
(D-148 clause 1 over the same rows), and:
- nothing is stored, so a stored floor and the rows beside it can never disagree;
- an artifact built before this wave still serves a correct floor, with no migration and no
  startup refusal;
- `survey_boards.py` and the engine call the SAME function.

D-159 clause 1 says "the artifact carries it"; its rows do. The ADR gets a one-line clarification in
this PR.

## Scope

**In:** `app/workflows/floors.py` (the rule, and the board query); `recommend()`, `subscribe`,
`/v1/categories` and `survey_boards.py` read it; `CategorySpec.min_quality` and the two constants go;
the tests that pinned numbers state the rule instead; `test_floor_rule.py` becomes a test of the
derivation; W-128 FIXED.

**Out:** the tie margins and windows (D-148 clause 2, amended; they stay calibrated numbers);
`score_anchor`, which D-146 clause 2 keeps pinned apart from the floor; the app, which already reads
`min_quality` from `/v1` and already handles a missing one.

## Phases

- **P1 — the one function.** `floors.top_third`, `floors.board_scores(conn, spec)`,
  `floors.derived_floor(conn, spec)`; `survey_boards.py` imports them. Red first: the rule on a known
  board, an empty board is `None`, and the script and the engine agree on a fixture artifact.
- **P2 — every reader uses it.** Red first:
  - a board whose rows move moves the Budget Pick, the subscription bar and `/v1/categories`'s
    `min_quality`;
  - `score_anchor` does not move with it;
  - with no artifact, the floor is `null`.

  Then `min_quality` leaves `CategorySpec`.
- **P3 — the records.** `test_floor_rule.py` rewritten; W-128 FIXED; the D-159 clarification;
  `categories.py`'s header comment states the rule and where the number comes from.

## Risks

- **Tests built on the old numbers:** about 40 references in 7 test files. Each is rewritten to
  state the rule on its own fixture, never re-pinned to a new number.
- **A tiny fixture board makes its top third its best row.** That is the rule working, and the
  tests say so.
