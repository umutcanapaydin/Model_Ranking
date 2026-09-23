---
record_type: review
id: issue-15-review
status: draft
process_version: v6.6
date: 2026-09-24
seat: independent
---
# #15 review: the out-of-100 anchor follows the derived floor

**Reviewer:** independent seat, Code-Reviewer then Tester (policy read from `main:.claude/agents/Code-Reviewer.md` and `main:.claude/agents/Tester.md`)
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** `main..40f22b2` (ce92d20 plan, 6845c48 red, 40f22b2 feat)
**Risk tier:** MED (from `docs/plans/issue-15-plan.md`)
**Author-family / reviewer-family:** unknown / Claude (fallback: no second family available; fresh context, no authoring history)

## Verdict

**PASS WITH FINDINGS.** The behaviour is right end to end: on the owner's artifact every Elo surface serves `score_anchor == min_quality == the answer's own floor fact`, null elsewhere and without an artifact, and the app turns that floor into exactly 50. The red commit fails for the stated reasons. The plan's before/after table reproduces to the digit. Both gates are green. What remains: one surviving mutant (the off-Elo null is never checked on a surface that has a floor, **M3**), and live text that still says the anchor is pinned or independent of the floor (**M1**, **M2**, **M4**). None of them breaks what is served today. M1 to M3 are one-line or few-line fixes, and I would do them on this branch.

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR (fix on this branch or file an issue)

- **M1** `docs/decisions.md:2008-2010` (D-146 status line). D-162 (`docs/decisions.md:2914`) says it supersedes D-146 clause 2, but D-146's own `**Status:**` still reads plain "accepted", and clause 2 (`:2029-2033`) still says the anchor "moves only by a reviewed edit to `PINNED_SCORE_ANCHORS` in `tests/unit/test_uncertainty_contract.py`", a table this change deletes. The log's own rule (`docs/decisions.md:17`, "To reverse: mark the old one `superseded by D-NNN`") and the reviewer policy's B.2 row ask for the back-pointer. This repo has done it before: `docs/decisions.md:85`, "superseded in part by P-004". D-143's "pinned in `CategorySpec`" is in the same position (D-162 "Amends" it). Graded MINOR, not BLOCKING, because the reversal IS recorded (D-162 names it, nothing was edited in place), and earlier supersessions (D-106, D-149) also left the old status unmarked. **Failure scenario:** an agent searching the log for "score_anchor" lands on D-146, reads "accepted", and restores a pinned field to "honour" it. Fix: add "clause 2 superseded by D-162" to D-146's status line, and "amended by D-162" to D-143's.

- **M2** `docs/prd.md:533` (REQ-FLR-001, live PRD). This row still says the floor is "never derived from `score_anchor`, which holds the same value on every Elo surface today and moves for a different reason (D-152, D-146 clause 2)". It also describes `test_floor_served.py` as proving "the floor moves with its board, the anchor does not". Since 40f22b2 both statements are false: the two fields are one number by rule, and that test (renamed `test_the_published_floor_moves_with_the_board`, `tests/unit/test_floor_served.py:57`) no longer asserts anything about the anchor. **Failure scenario:** a reader treats the PRD as the contract, sees "the anchor does not move with the board" listed as covered, and files the D-162 behaviour as a regression. Fix: rewrite the clause as "the floor; on Elo surfaces `score_anchor` is this same number (D-162)", and correct the test description.

- **M3** `tests/unit/test_floor_served.py:396-403`, surviving mutant **X7** (table below). The null-off-Elo branch of `test_every_elo_surface_anchors_its_score_at_its_served_floor` is only checked where the fixture has a floor. The seeded fixture has no ECI board, so `everyday` has `min_quality = None` (measured: "fixture everyday floor: None"), and `served["everyday"]["score_anchor"] is None` passes whether or not the endpoint guards ECI. Mutant `if spec.metric in ("elo", "ECI")` stays GREEN across `test_floor_served`, `test_uncertainty_contract`, `test_api_v1` and `test_ios_client_contract` (97 passed). **Failure scenario:** on the owner's artifact, `/v1/categories` then serves `score_anchor: 149.6` on `everyday`. Today's app ignores it (`scoreForm` treats ECI as `.rankOnly`, and `anchoredScaleExplanation` is Elo-only). But the `/v1` contract (D-143, D-162 clause 2: "ECI stays rank-only") is broken for any other consumer, and no test goes red. **Proof the fix works:** a temporary probe (`_raise_the_board(seeded, "everyday", above=140.0, rows=30)`, then assert `min_quality is not None` and `score_anchor is None`) passes at HEAD and goes RED under X7 (`assert 161.0 is None`). The probe was deleted afterwards and `main.py`'s md5 was restored. Fix: raise the `everyday` board, and one percentage board, inside that test before asserting, and assert both have a non-null floor.

- **M4** Live comments, a test and PRD rows that still say "pinned":
  - `ios/EngineTests/ScoresTests.swift:206-210`: "every anchor the engine pins today … Kept in step with `PINNED_SCORE_ANCHORS` in `test_uncertainty_contract.py`". That table no longer exists, and the loop still walks only the four 2026-09-20 values (`[1400.0, 1478.9, 1467.5, 1450.6]`). The served anchors now include 1202.1 to 1253.3 (vision/search), which it never covers. The conversion is monotone for any anchor, so nothing is wrong today. But REQ-SCR-002's evidence (`docs/prd.md:504`, "every pinned anchor") now points at a set of values that has no meaning. Fix: reword the comment and test name, and add the ~1200 band, or loop over a span.
  - `ios/ModelRanking/ContentView.swift:743` ("the surface's pinned anchor") and `ios/ModelRanking/Engine/Detail.swift:42` ("the surface's pinned `score_anchor`").
  - `docs/prd.md:493` (REQ-CMP-004: "against the surface's pinned anchor").
  - `src/app/adapter/main.py:1200-1204` (`_artifact_facts` docstring): "The one field on `/v1/categories` that is not a policy constant". `score_anchor` is now also artifact-derived.

  **Failure scenario:** the next person to change the conversion trusts these comments and keeps a fixed-anchor assumption, for example a cache keyed on "pinned" anchors.

### NIT
- **NIT-1** `tests/unit/test_ios_client_contract.py:579,584`: the assertion messages still say "anchored on the surface's pinned anchor".
- **NIT-2** `docs/plans/issue-15-plan.md` says it is "deleted before merge". It is still in the tree at HEAD, so remember to delete it (a `/pre-merge` item, not a defect yet).

## K.9 candidates outside this change's scope
- **K1** `docs/coverage-by-req.md:128-129` (a ratified register). The REQ-SCR-002 and REQ-SCR-003 rows cite `CategorySpec.score_anchor`, `test_every_elo_surface_publishes_its_pinned_score_anchor` and `test_the_served_anchor_does_not_follow_a_moved_floor`, and all three are gone. It is a milestone snapshot, so it is arguably history. But it is a register, and `test-documented-paths` checks only paths, not symbols, so nothing will flag it. Enhancement: re-point it at the next coverage pass.
- **K2** `src/app/adapter/main.py:1206-1226`. `/v1/categories` now serves a null anchor whenever the artifact is missing, cannot be opened, or is mid-republish (`return {}, {}`). D-162 clause 2 names "no artifact, or an empty board", but not an unreadable one. Before this change the pinned anchor survived a transient read failure. Now a card can switch from "64 / 100" to "1507.6 Elo" for one load if `/v1/categories` hits the republish window and `/v1/recommendations` does not (`ContentView.swift:637` keeps the old list only when the request FAILS, not when it returns nulls). This is behaviour, not a bug, and it is honest (D-146 clause 1). Worth one sentence in D-162, or an issue if the owner wants the app to keep the last anchor.

## Risks queued
- **R1** The anchor and the answer's `floor` fact come from two separate reads of the artifact (`/v1/categories`, then `/v1/recommendations`). Across a publish that moves the floor, the Budget Pick's sentence would read "clears 50.3 points" rather than 50. It would show up as a reader report or a screenshot with a non-50 floor on an anchored card.

## Evidence

### 1. End to end
- Server: `src/app/adapter/main.py:1283`, `"score_anchor": floors.get(spec.id) if spec.metric == "elo" else None`. `floors` is `derived_floor` per spec (`:1223`). That is the same function `recommend` uses for the answer's floor fact (`src/app/workflows/recommend.py:494,583`) and the refresh hashes (`src/app/workflows/refresh.py:429`). The floor is `None` on an empty board (`src/app/workflows/floors.py` `top_third` returns None on `[]`), so the anchor is null there. Without a file it is `{}`, so the anchor is null.
- On the copied owner artifact (`MODEL_RANKING_DB=advisor.db`, `.venv/bin/python ../r15-seat/e2e.py`), anchor = the answer's floor fact on all seven Elo surfaces:
  ```
  assistant anchor 1406.7 answer floor facts {1406.7}
  web-dev anchor 1478.9 answer floor facts {1478.9}
  document anchor 1470.7 answer floor facts {1470.7}
  factuality anchor 1451.5 answer floor facts {1451.5}
  vision anchor 1253.3 answer floor facts {1253.3}
  search anchor 1206.9 answer floor facts {1206.9}
  search_factuality anchor 1202.1 answer floor facts {1202.1}
  ```
  Every non-Elo surface serves `score_anchor=None` (coding, agentic-coding, everyday/ECI, expert, mathematics, computer-use, abstract).
- iOS:
  - `ContentView.swift:161` sets `anchored: info?.scoreAnchor != nil`. Null means the engine's scale, a number means /100 (`:172,186,434,459`).
  - `Uncertainty.swift:185-199` has the 2000 Elo guard (`anchorReach`). The anchor is now drawn from the same board as the scores, so it sits within the board's spread (under 500 Elo on today's boards), and the guard stays a guard against broken data only. Untouched.
  - `anchoredFact` (`Uncertainty.swift:357-381`) converts the answer's floor against the anchor. With anchor == floor this is exactly 50, pinned by `ScoresTests.swift::testTheFloorIsRestatedAsAPosition` ("at the anchor it is exactly 50").
  - `Language.swift:205-209` (`"50 is at the bar"` / `"50 tam çıtada demek"`) is now literally true, in EN and TR.
  - Swift fixture `ios/EngineTests/EngineClientTests.swift:174` already has `score_anchor == min_quality` (1206.9), consistent with the new rule.
  - The only Swift test still built on pinned numbers is `ScoresTests.swift:209` (M4).
- Scripts: `scripts/calibrate_board.py` and `scripts/survey_boards.py` say nothing about the anchor being pinned (`git grep -n -i anchor -- scripts`: only `survey_boards.py:123`, "no anchor, no conversion, identity", which is correct).
- Stale live text: M1, M2, M4, NIT-1. Records (closure reports, retrospectives, EXPERIENCE, older plans, reviews) are history and not graded.

### 2. Red replay (6845c48, from `git archive 6845c48 | tar -x`, `PYTHONPATH=src`)
```
>               assert served[surface]["score_anchor"] == served[surface]["min_quality"], surface
E               AssertionError: assistant
E               assert 1400.0 == 1421.0
>       assert after["score_anchor"] > before
E       assert 1467.5 > 1467.5
>       assert {entry["score_anchor"] for entry in _served().values()} == {None}
E       AssertionError: assert {None, 1248.2..., 1206.9, ...} == {None}
FAILED tests/unit/test_floor_served.py::test_every_elo_surface_anchors_its_score_at_its_served_floor
FAILED tests/unit/test_floor_served.py::test_the_anchor_moves_with_the_board
FAILED tests/unit/test_floor_served.py::test_with_no_artifact_no_anchor_is_invented
3 failed, 51 passed
```
Each fails for the stated reason: the pinned value is served instead of the floor; the anchor does not move; a pinned number is served without an artifact. At HEAD: `test_floor_served.py test_uncertainty_contract.py test_ios_client_contract.py`, **71 passed**.

Test deletions in 40f22b2 (`test_uncertainty_contract.py`: `test_every_elo_surface_publishes_its_pinned_score_anchor`, `test_the_served_anchor_does_not_follow_a_moved_floor`, `test_a_recalibration_cannot_move_the_anchor`, and the assertion removed at `test_floor_served.py:67`) asserted the superseded rule (D-146 clause 2). Their inverses replace them (`test_floor_served.py:391-424`). This is a ruled restatement, not weakening to reach green.

### 3. D-162 / plan table, reproduced on the copied artifact
`cp` of the owner's `advisor.db`, md5 `214139e91c691e0273c21673e71d2ba4` before, after the copy, and at the end of the review. Leader = `category_ranking(...)[0].score`; /100 = `100/(1+10^((a-s)/400))`.
```
assistant          pinned= 1400.0 anchor=1406.7 floor=1406.7 eq=True before=65.0 after=64.1
web-dev            pinned= 1478.9 anchor=1478.9 floor=1478.9 eq=True before=79.3 after=79.3
document           pinned= 1467.5 anchor=1470.7 floor=1470.7 eq=True before=57.0 after=56.5
factuality         pinned= 1450.6 anchor=1451.5 floor=1451.5 eq=True before=57.2 after=57.0
vision             pinned= 1248.2 anchor=1253.3 floor=1253.3 eq=True before=61.0 after=60.3
search             pinned= 1206.9 anchor=1206.9 floor=1206.9 eq=True before=57.2 after=57.2
search_factuality  pinned= 1203.7 anchor=1202.1 floor=1202.1 eq=True before=56.3 after=56.5
```
All seven rows match `docs/plans/issue-15-plan.md` and D-162 exactly. The largest move is 0.9 (assistant), as D-162 states.

### 4. Refresh fingerprint
`src/app/workflows/refresh.py:429` hashes `floor:{name}:{derived_floor(conn, spec)}` for every surface. The served anchor is a pure function of that floor (plus the static `metric`), so any anchor change is also a floor change, which changes the fingerprint and publishes. No new field needs hashing. The existing "a floor moved by unranked rows is a served change" coverage in `test_floor_served.py` covers it. Other readers of `score_anchor`: `git grep` finds only `main.py:1283`, tests, and the Swift client (`Models.swift:58,73`, `ContentView.swift`, `Detail.swift`). Nothing in `src/` or `scripts/` read `CategorySpec.score_anchor`, so removing it breaks no caller. `make typecheck` is green.

## Mutant table (in place on `src/app/adapter/main.py:1283`; each restored and md5-checked `4854e56160386a043299a3f930196479`)
Suite per mutant: `pytest --no-cov -x tests/unit/test_floor_served.py test_uncertainty_contract.py test_api_v1.py test_ios_client_contract.py`.

| id | mutant | result | killed by |
|---|---|---|---|
| X1 | drop the Elo guard (`floors.get(spec.id)` everywhere) | RED | `test_every_elo_surface_anchors_its_score_at_its_served_floor` |
| X2 | always `None` | RED | same |
| X3 | anchor rounded to a whole Elo | RED | same (the decimal-floor guard works) |
| X4 | another surface's floor (`floors.get("assistant")`) | RED | same |
| X5 | the old pinned table restored | RED | same |
| X6 | pinned fallback `or 1400.0` when there is no floor | RED | same |
| X7 | ECI also anchored (`metric in ("elo", "ECI")`) | **GREEN** (97 passed) | none: **M3**. A probe test kills it (`assert 161.0 is None`) |
| X8 | anchor = floor + 0.1 | RED | same as X1 |

Kill rate 7/8. Every mutant is killed by the first new test. The other two new tests are the second line of defence Re-run without `-x`: X5 fails all three new tests (3 failed, 94 passed), and X6 fails the first test plus `test_with_no_artifact_no_anchor_is_invented` (2 failed, 95 passed).

## Gates (in the clone, `make install` venv, owner artifact copied in)
- `make check-fast`: **exit 0**. lint, typecheck, records, test (1222 passed, 15 skipped), client-decls, and swift-test (268 tests, exactly the manifest's) all PASS, in 75.1 s.
- `make check`: **exit 0**. pytest **1222 passed, 15 skipped** (`MODEL_RANKING_REQUIRE_ARTIFACT=1`). coverage-floor PASS (36 modules). check_records PASS. wave-check-all PASS (43 records). conformance PASS (16 tests). swift-test PASS (268). client-decls PASS (1488 in each of the 4 configurations).

## Acceptance criteria evidence
- REQ-SCR-003 (as amended) → `tests/unit/test_floor_served.py:391` (anchor == served floor on every Elo surface, null off Elo), `:407` (it moves with the board), `:420` (null without an artifact). Implementation `src/app/adapter/main.py:1283`. GREEN.
- #15 done-when 1 ("a board that moves its floor moves `score_anchor` by the same amount") → `test_floor_served.py:407-417` (`after["score_anchor"] > before` and `== after["min_quality"]`). GREEN.
- #15 done-when 2 ("the app's 'at the bar' sentence names the served floor") → the server serves anchor == floor (above), plus `ios/EngineTests/ScoresTests.swift::testTheFloorIsRestatedAsAPosition` (floor at the anchor reads 50), plus `Language.swift:205-209`. GREEN.
