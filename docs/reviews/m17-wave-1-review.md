---
record_type: review
id: m17-wave-1-review
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M17-W1 -- independent review (D-159, floors from the board; commits c794305..e65fd56)

**Seat:** independent (Code-Reviewer + Tester combined, MED tier). I wrote none of this wave.

**Scope:** `git diff origin/main...HEAD` on `enhancement/m17-w1-floors-every-build` (draft PR #11).
The merge base is `cf00ec7` and HEAD is `e65fd56`. There are seven commits:
- `c794305` adds the working plan.
- `e796a5f` and `5f77b39` are P1, red then green.
- `a6d6ea0` adds a board where a third and a quarter differ.
- `2d8bf51` and `365c833` are P2, red then green.
- `e65fd56` records W-128 FIXED and the D-159 clarification.

I read the branch against three things:
- `docs/plans/m17-wave-1-plan.md` and `docs/plans/m17-plan.md` §0.1 and §2 W1;
- D-148, D-146 clause 2, D-152 and D-159, with its clarification, in `docs/decisions.md`;
- W-128 in `docs/warnings.ledger.md`.

I also read the refresh's publish decision (`src/app/workflows/refresh.py`: `serving_summary`,
`degradations`, `upward_anomalies`) and REQ-REF-002 and REQ-REF-003 in `docs/prd.md`.

**Policy:** I read my policy only from `git show origin/main:subagent-profiles/Code-Reviewer.md`
and `.../Tester.md`. `git diff --stat origin/main...HEAD -- subagent-profiles AGENTS.md .agents
.claude permission-matrix.md docs/security-baseline.md` is empty. Nothing in the diff addresses a
reviewer, so there is no injection-class finding.

**Families:** the author is recorded as Claude, and this seat is also Claude. No second family was
available to me, so this is the fallback. My context was fresh: I did not see the author's session.

**Snapshot.** Every result below is against HEAD `e65fd56`. These md5 prefixes were identical in
the repository and in my copy at the start and at the end:

| File | md5 |
|---|---|
| `floors.py` | `ab0a896d` |
| `recommend.py` | `0b88a63a` |
| `subscribe.py` | `9d8bad54` |
| `adapter/main.py` | `6dde70b0` |
| `survey_boards.py` | `503a0913` |

The owner's `advisor.db` (`214139e9...`) and `advisor.db.refresh.json` (`d729a3f6...`) did not
change. I read them only as copies.

**How I worked:**
- **The copy.** I made an `rsync` copy of the tree in a NEW subdirectory of the session scratch
  directory. It left out `.venv`, `ios/.build` and the owner's two untracked files at the repository
  root.
- **A fresh venv in the copy** (`make install`). Its editable `.pth` points at the copy's own `src`.
- **Bytecode caches purged.** They had been copied with the repository's paths inside them. After
  purging, `app.workflows.floors.__file__` resolves inside the copy.
- **Other artifacts.** Probes of the served artifact ran on copies of `advisor.db` inside my
  subdirectory. I replayed the red commits from `git archive` exports.
- **No state changes.** I made no git state change and started no server. The only repository file
  I created is this one. `git status --short` shows the same two untracked files before and after,
  plus this record.

## Verdict

**BLOCKING: 1 BLOCKING, 0 MAJOR, 5 MINOR, 3 NIT.**

**What this wave got right.**
- **One definition, used everywhere it is read.**
  - `floors.derived_floor` (`floors.py:42-44`) is called by `recommend()` (`recommend.py:494`),
    `recommend_subscription()` (`subscribe.py:439`), `/v1/categories` (`adapter/main.py:1223`,
    served at `:1295`), `survey_boards.py:198` and `calibrate_board.py:155`.
  - `CategorySpec.min_quality` and `MIN_QUALITY_PCT`/`MIN_QUALITY_ELO` are gone.
  - A tree-wide `git grep` (src, scripts, ios, tests, docs outside records) finds no reader of any
    other floor (see "Every floor reader" below).
- **On the owner's artifact, nothing a reader sees changes today.** All 14 derived floors equal the
  hand-kept M16-W3 values exactly. For example `coding` 65.4, `assistant` 1406.7, `everyday` 149.6,
  `document` 1470.7 and `search_factuality` 1202.1.
- **D-146 clause 2 is intact.**
  - `score_anchor` is still a pinned `CategorySpec` field, served as `spec.score_anchor`
    (`adapter/main.py:1288`).
  - `test_uncertainty_contract.py:304` moves the BOARD and asserts the anchor stays at
    `PINNED_SCORE_ANCHORS`.
  - Mutant M17 (serve the anchor as the floor) is RED, with 5 killers.
- **There is no stale state in the served artifact.** The floor is derived from the rows of the
  artifact being read, so an artifact and the floor served from it cannot disagree. An artifact
  built before M17 serves the right floor.
- **The empty-board case never crashes and never serves an invented number.**
  - `floor=None` gives `min_quality: null` on `/v1/categories`.
  - `recommend()` and `recommend_subscription()` both answer with the WARNING sentence
    (`recommend.py:455-463`), and `why_fact.floor` is JSON `null`.
  - Every `{floor:g}` sits behind `floor_met`, which implies a number.
  - My probe on the owner's artifact with `swebench` removed returned the same answer from all
    three readers.
- **The mutants mostly die.** 25 mutants on the load-bearing lines give 23 RED and 2 GREEN. The two
  GREEN mutants are both closed by killer tests I wrote in scratch (MINOR-1, MINOR-2).
- **Cost is not an issue.**
  - `/v1/categories` averaged 3.2 ms end to end over 30 calls on the owner's artifact (2,645 score
    rows).
  - The 14 derivations take about 7.5 ms on a plain connection.
  - The cost is linear in one artifact's rows, with no loop over requests or history.

**What blocks:**
- **The refresh cannot see a floor (BLOCKING-1).** A board that grows only by rows the ranking
  does not carry moves the floor, and with it the Budget Pick and `/v1/categories` `min_quality`.
  The fingerprint does not change. The refresh reports "nothing a user would notice changed" and
  does not publish.
- **D-159 clause 3 is not built.** The guards the owner's ruling relied on ("D-128/D-132 still
  guard", M17 plan §0.1) take a `ServingSummary`, which carries no floor. So "a floor that empties
  a budget ... is refused" cannot happen.

## BLOCKING

### BLOCKING-1 -- the refresh's "served content changed" decision and its guards are blind to the floor

**Where:**
- `src/app/workflows/refresh.py:336-396` (`serving_summary`). It hashes `category_ranking` rows
  only.
- `:1027-1043`. When the digests are equal, it returns `EXIT_UNCHANGED` with "nothing a user would
  notice changed".
- `:201-235` (`degradations`) and `:143-198` (`upward_anomalies`). Neither receives a floor.

**The defect.** Before this wave the floor was a code constant, so a candidate artifact could not
change it and the ranked rows were the whole of the served content. Since D-159 the floor is
derived from EVERY row of the primary board. That includes rows that never reach
`category_ranking`: unpriced, unreconciled, or at another effort. On the owner's artifact the
`coding` board has 173 rows and 44 ranked; `everyday` has 521 and 58. Rows outside the ranking now
decide a served fact, and nothing in the fingerprint reads them. REQ-REF-002 ("'Changed' is decided
on the CONTENT THAT WOULD BE SERVED") no longer holds.

**Reproduced on a copy of the owner's artifact** (a scratch probe script). I added 60 unpriced rows
(`"new-agent + Unpriced i"`, 70.0-75.9) to `coding`'s own board (`swebench`):

| | live | candidate |
|---|---|---|
| derived floor (served `min_quality`) | 65.4 | 71.3 |
| Budget Pick, every budget | DeepSeek V3.2 | MiniMax M2.5 |
| `serving_summary` digest | (live's) | **identical to live's** |
| `degradations` / `upward_anomalies` | | `[]` / `[]` |

A second scratch probe added 120 unpriced rows at 79.0-80.2:
- **Effect.** The floor went to 79.2. The `low` Budget Pick became `GPT-5 nano`,
  `nothing_clears_floor`. That is a floor emptying a budget, which is D-159 clause 3's own example.
- **Guards.** The digest was again identical and both guard lists were empty. With any ranked
  change beside it the candidate would publish, and no guard can refuse it.

**Consequences:**
1. **Stale floors.** A floor-only move is never published. The live artifact keeps serving its own,
   self-consistent, older floor until some ranked row changes. D-159's "every build" does not hold
   for those builds. The outcome record also says something false: nothing a user would notice did
   not change.
2. **No guard on floor moves.** A floor move that rides along with any ranked change is published
   unjudged. D-159 clause 3 and the ruling it rests on ("D-128/D-132 still guard") are unbuilt, while
   the branch records D-159 as built and W-128 as FIXED.
3. **Expiry nights (D-156).** `_served_without` rebuilds the baseline through `serving_summary`, so
   a primary source expiring (MINOR-1's trigger) turns a surface's floor into `None` with no guard
   seeing it.

**The citing tests fail on HEAD.** Two tests I wrote in scratch (not in the repository) fail on
HEAD, which is the expected RED for a missing control:
- `test_a_floor_that_moves_the_budget_pick_changes_the_fingerprint` builds two `_seeded_db`
  artifacts and adds 300 unpriced rows above the best `coding` score to one. It asserts the Budget
  Pick's `why_fact` differs, which passes, and that the digests differ, which FAILS (identical).
- `test_a_floor_that_empties_a_budget_is_refused` builds the same pair. It asserts the reason goes
  from `cheapest_above_floor` to `nothing_clears_floor`, which passes, and that `degradations(...)`
  is non-empty, which FAILS (`[]`).

**What a fix needs:**
- **Fingerprint.** `serving_summary` should hash each surface's `derived_floor(conn, spec)` beside
  its rows. The value is already rounded to one decimal (D-109), so float noise cannot trip it.
  `ServingSummary` should carry the floor too, so `_served_without` inherits it.
- **Guard.** D-159 clause 3 needs a guard axis, which is a judgement for the lead and the owner.
  The simplest reading of the clause: a (surface, budget) whose Budget Pick cleared the floor on the
  live artifact and would clear nothing on the candidate, or whose floor becomes unmeasurable, is a
  degradation.
- **Freeze risk.** Weigh D-128's freeze warning before choosing. A floor that legitimately rises
  above everything a `low` budget can buy would be refused every night. If the owner prefers
  "publish and disclose", D-159 clause 3 needs an amendment, not silence.

## MINOR

### MINOR-1 -- the empty-board answer is honest in English, but the phone, the fact code and the subscription tests do not follow it

The case is a surface whose ranking reads another source on its benchmark while its own board is
empty. The three readers agree on it, and nothing crashes. Three gaps remain:
- **The phone.** `why_fact` is `{"reason": "nothing_clears_floor", "floor": null}`.
  `whySentence` returns `nil` when the floor is not a number (`ios/ModelRanking/Engine/Language.swift:87`),
  so the card falls back to the engine's English `why` (`ContentView.swift:755`). The Turkish screen
  shows an English sentence (D-129: the app owns its languages).
- **The fact code.** "Nothing clears the floor" and "there is no floor" are two answers wearing one
  code. That is the shape `test_why_facts.py:92` exists to prevent.
- **The trigger is realistic.** On a copy of the owner's artifact with the `swebench` rows removed
  (a D-156 expiry, or the W-129 licence replacement), `coding` still ranks from
  `epoch_swe_bench_verified`. Every `coding` Budget Pick becomes `GPT-5 mini` at 64.7, below
  yesterday's 65.4 bar, on every budget. The subscription answer becomes "the cheapest plan
  available".
- **The rule itself was not the owner's.** The clarification appended to the accepted D-159 says "A
  surface whose own board is empty has no floor, and its Budget Pick says so". That is a new rule
  about what the product recommends, not a clarification of "the artifact carries it". The plan
  calls the wave's choice "implementation, not policy". This sentence is policy, and it should go to
  the owner.
- **No subscription test.** `subscribe.py`'s empty-board branch has no test of its own. Mutant M16
  (`floor = derived_floor(...) or 0.0` in `subscribe.py:439`) stays GREEN across the full suite,
  and then the answer reads "clearing the 0 points bar". My scratch test
  `test_the_subscription_answer_says_when_its_board_is_empty` moves the `_plans_db()` board to
  another source. It asserts "board is empty" is in the `why` and "minimum-quality bar." is not. It
  passes on HEAD and is RED on M16, and the md5 check afterwards matched.

### MINOR-2 -- the W-084 guard on the printed floor was narrowed away (weakened to green)

`tests/unit/test_categories.py:347` (`test_no_surface_states_a_bar_the_engine_does_not_apply`) used
to match `{spec.(min_quality|value_window)...}` in `recommend.py` and `subscribe.py`. Now it
matches only `value_window` (`:367`), because the floor is a local variable. Nothing replaced its
floor half:
- **M24** (`{floor:g}` changed to `{floor:.0f}` at `subscribe.py:578`) stays GREEN on the full
  suite. The subscription answer can say "84" where the engine applies 84.4, which is the
  Stage 4.0 MINOR-1 defect this test was written for.
- **M23 and M25** (the same change in `recommend.py`) are RED, killed by `test_why_facts.py`.

My scratch test `test_the_subscription_answer_states_the_bar_it_applies` sets the fixture's 70.0
row to 70.4 and asserts the derived floor is 70.4. It then asserts
`f"clearing the {floor:g} points"` is in the plan answer. It passes on HEAD and is RED on M24, and
the md5 check afterwards matched.

### MINOR-3 -- the scale checks now run only where `advisor.db` exists, and CI no longer does

**What moved.** The constant checks CAT-01/02/09/10 (floor > 0, a percentage floor ≤ 100, an Elo
floor ≥ 1000, value window < floor) and D-145's two-board scale check moved into
`test_every_derived_floor_is_on_its_own_scale` (`test_categories.py:322`). That test is
`@pytest.mark.artifact`. `test_floor_rule.py:34` is too. Both are skipped where the artifact is
absent (`tests/conftest.py:24-54`), including `.github/workflows/ci.yml:54`.

**The measured cost:**
- **Without the artifact, M03 survives.** M03 drops the one-decimal rounding at `floors.py:30`.
  With `advisor.db` it is killed only by `test_floor_rule.py:34`. With `advisor.db` moved aside,
  M03 is GREEN on the full unit suite.
- **The other checked mutants still die.** M01, M02, M04-M08 and M17 stay RED without the artifact.
- **`value_window < floor` is no longer checked in CI.** CAT-10 was added after a mutant that set
  `web-dev`'s window to 1e9 survived.

**Why MINOR.** A derived floor needs a board, so some of this is inherent. A rounding case on a
fixture board would close M03 in CI, for example `top_third([65.44, 65.36, 60.0]) == 65.4`.
`value_window < floor` could run on the `test_api_v1._seeded_db` fixture's percentage boards.

### MINOR-4 -- three records now describe code that is gone

- **`docs/prd.md:533` (REQ-FLR-001).** The row still cites
  `test_uncertainty_contract.py::test_every_surface_publishes_the_floor_it_recommends_from` as the
  test "which moves one surface's FLOOR and not its anchor and is shown RED on three mutants". That
  test (`:340`) no longer moves anything; it compares served to derived. The moving halves are now
  `test_floor_served.py:58` and `test_uncertainty_contract.py:304`.
- **`src/app/adapter/main.py:1276-1288`.** The anchor comment still says the anchor is "the
  surface's own quality floor, so 50 means 'exactly at the bar this product recommends from'". It
  also says "never `spec.min_quality` -- which today holds the SAME four numbers". That field no
  longer exists, and no two anchors equal their floors on the owner's artifact except `web-dev` and
  `search`.
- **`docs/warnings.ledger.md:174` (W-128 FIXED).** The ledger calls `test_floor_rule.py`'s `_rule` "an
  independent reading of D-148 clause 1". It is the same SQL and the same formula as
  `floors.py:25-39`, line for line. It catches drift in `floors.py`, which is worth having. It
  cannot catch a misreading the two share. It should say so.

### MINOR-5 -- the phone tells readers "50 is at the bar", and the served floor no longer sits at 50 (K.9, owner ruling)

`ios/ModelRanking/Engine/Language.swift:197-198` explains the Elo /100 scale as "how often people
prefer it over a model at the bar we recommend from -- 50 is at the bar". The same claim is in
`Uncertainty.swift:170-172`. The anchor is pinned (D-146 clause 2); the floor now moves with the
board.

On the owner's artifact the detail screen already converts `assistant`'s floor (1406.7 against
anchor 1400.0) to 51.0/100 beside the sentence "50 is at the bar". `document` reads 50.5, `vision`
50.7 and `search_factuality` 49.8. The gap was born in M16-W3. D-159 makes it permanent and lets it
grow with every board. That is a number told to a reader that the engine does not apply.

Out of this wave's scope, since it touches no Swift. It needs a ruling: reword the sentence ("50 is
the reference we fixed on <date>"), or accept the drift and record it.

## NITs

- **NIT-1.** `scripts/survey_boards.py:178`'s docstring still promises "beside the two it did not
  choose and today's". The `floor_today` and `move` columns were removed.
- **NIT-2.** `test_floor_served.py:103` (`test_the_budget_pick_says_when_its_board_is_empty`) first
  appears in the green commit `365c833`, so it was never shown red. The P2 red commit `2d8bf51` has
  four tests, and all four fail there (replayed). Mutants M11, M12 and M20 are RED on this test now,
  which makes up for it.
- **NIT-3.** `test_categories.py:331` opens `sqlite3.connect("advisor.db")`: a read-write handle on
  the served artifact, by a path relative to the working directory. `test_floor_rule.py:35` uses
  `adapter.open_readonly`. Use the read-only door in both (INV-23's spirit).

## Test integrity: every changed assertion

113 test lines were removed. For each old assertion, is its intent kept?

| Test | Old assertion | Now | Intent |
|---|---|---|---|
| `test_recommend.py:259` | `MIN_QUALITY_PCT == 65.4` (a literal compared with itself; `docs/council-m11-assessment.md:44` called it theater); DeepSeek V3.2; `score >= 65.0` | derived floor 70.0 on a 12-row board; DeepSeek V3.2 exactly AT the floor; `why_fact.floor == 70.0` | **Kept and stronger**: boundary-tight, so M08 (`>=` to `>`) is RED |
| `test_recommend.py:445` | `score < MIN_QUALITY_PCT` | 3 unpriced rows (80-82) set the floor; `score < why_fact.floor`; WARNING | Kept |
| `test_recommend.py:146, :590` | whole benchmark moved to Epoch | only rows with a `model_id` move; `swebench` keeps the unpriced rows | Kept. The empty-board case moved to its own test |
| `test_recommend_assistant.py:111` | `MIN_QUALITY_ELO == 1406.7`; pick ≥ it (the docstring named kimi and gemini excluded) | floor ≥ 1000; pick ≥ floor; `why_fact.floor == floor` | **Slightly weaker**: which models the floor excludes is no longer stated. Acceptable |
| `test_recommend_assistant.py:~192, :204` | alias tuple with `MIN_QUALITY_ELO`; `score < MIN_QUALITY_ELO` | tuple without it; `score < why_fact.floor` | Kept |
| `test_subscribe.py:135, :195` | floor 65.0; all scores set to 40 | 6 unlisted rows; "clearing the 70 points"; only plan models set to 40 | Kept. Boundary-tight (M14 RED) |
| `test_categories.py:~306` CAT checks | on constants, always run | on derived floors, artifact only | **Kept in kind, lost in CI** (MINOR-3) |
| `test_categories.py:347` bar quoting | `min_quality` and `value_window` | `value_window` only | **Weakened** (MINOR-2) |
| `test_categories.py` M15 pins, two-board check | the floor was pinned | the floor is unpinned by D-159 | Intended by the ADR |
| `test_floor_rule.py` | code == research record | derived == a literal re-statement, on the artifact | Changed purpose, recorded as W-128. The "independent" wording is MINOR-4 |
| `test_uncertainty_contract.py:304, :340` | floor moved by `dataclasses.replace` | board moved by rows; served == derived | Kept (M17, M18, M19, M22 RED) |
| `test_uncertainty_contract.py:326` | `replace(min_quality)` leaves the anchor | `not hasattr(min_quality)`; anchor == pinned | Near-tautological before and after; neutral |
| `test_survey_floors.py:75` | `floor_today` == spec | removed with the column | Kept |

**Are the "filler" rows fair, or vacuous?**
- **What they vary.** The filler rows are unpriced or unlisted models placed BELOW the floor
  (30-54 in `test_recommend.py`, 30-55 in `test_subscribe.py`). They change only the COUNT, which is
  the variable D-148 clause 1 is about. Real boards carry far more unranked rows than ranked ones,
  so a board of mixed rows is the realistic shape.
- **Not vacuous.** The fixtures put the Budget Pick exactly at the derived floor, so they are
  boundary-tight: M08 and M14 die on them.
- **One shape is missing:** unranked rows ABOVE the ranked models. `test_floor_served.py:40`
  (`_raise_the_board`) covers it for the readers. No test covers it for the refresh (BLOCKING-1).

## Mutants

Every mutant was applied in place to the copy, one at a time. The harness replaced one exact
string, refusing any string that did not match exactly once. It ran the full `tests/unit` suite
(`-n auto`, `MODEL_RANKING_REQUIRE_ARTIFACT=1`). Then it string-replaced the change back and
compared the md5 with the value taken before. All 25 restores were byte-identical, and `diff -rq`
of the copy's `src`, `tests` and `scripts` against the repository was empty at the end.

| # | Mutant (load-bearing line) | Result |
|---|---|---|
| M01 | `floors.py:22` fraction 1/4 | RED, 6 (`test_floors.py:22`, `test_recommend.py:259`, ...) |
| M02 | `:29` sorted ascending | RED, 14 |
| M03 | `:30` no rounding | RED, 1 (`test_floor_rule.py:34`, artifact only). **GREEN without the artifact** (MINOR-3) |
| M04 | `:30` off by one (the row below the third) | RED, 8 |
| M05 | `:27-28` an empty board floors at 0.0 | RED, 4 |
| M06 | `:36-38` the board ignores the source | RED, 4 |
| M07 | `:36-38` the board ignores the metric | RED, 1 (`test_survey_floors.py`) |
| M08 | `recommend.py:500` `>=` to `>` | RED, 5 |
| M09 | `:494` floor from the ranked rows, not the board | RED, 107 |
| M10 | `:500` floor ignored | RED, 12 |
| M11 | `:494` `or 0.0` (an empty board clears everything) | RED, 1 (`test_floor_served.py:103`) |
| M12 | `:500` the None guard dropped | RED, 3 |
| M13 | `subscribe.py:440` floor ignored | RED, 2 |
| M14 | `:440` `>=` to `>` | RED, 1 (`test_subscribe.py:135`) |
| M15 | `:440` the None guard dropped | RED, 1 (`test_effort.py`, incidentally) |
| **M16** | **`:439` `or 0.0`** | **GREEN, full suite** (MINOR-1; killer test written) |
| M17 | `main.py:1295` serves `score_anchor` | RED, 5 |
| M18 | `:1223` floors only on surfaces with a secondary benchmark | RED, 4 |
| M19 | `:1295` always `None` | RED, 4 |
| M20 | `recommend.py:460-461` the empty-board warning loses its reason | RED, 1 |
| M21 | `survey_boards.py:198` floor over distinct models | RED, 2 |
| M22 | `main.py:1223` every surface gets `coding`'s floor | RED, 4 |
| M23 | `recommend.py:571` `{floor:.0f}` | RED, 15 (`test_why_facts.py`) |
| **M24** | **`subscribe.py:578` `{floor:.0f}`** | **GREEN, full suite** (MINOR-2; killer test written) |
| M25 | `recommend.py:462` `{floor:.0f}` in the warning | RED, 1 |

**Totals:** 25 mutants give 23 RED and 2 GREEN. None is equivalent.

**Without the artifact** (CI's view: `advisor.db` moved aside in the copy, no
`MODEL_RANKING_REQUIRE_ARTIFACT`), I re-ran M01-M08, M17 and M03. All but M03 stay RED.

**Killer tests.** Four tests, written in scratch only:
- two for MINOR-1 and MINOR-2, each passing on HEAD and RED on its mutant;
- two for BLOCKING-1, each RED on HEAD.

## Red to green, replayed

These runs used `git archive` exports of each commit, the copy's venv and a copy of `advisor.db`:
- **`e796a5f` (P1 red).** `test_floors.py` fails at collection because `app.workflows.floors` does
  not exist. That is a valid red.
- **`2d8bf51` (P2 red).** 4 of 4 tests in `test_floor_served.py` FAIL:
  - served == derived;
  - the floor moves and the anchor does not;
  - no artifact gives null;
  - the Budget Pick clears the board's floor.

  The other 92 tests in the eight touched files pass.
- **HEAD.** All of them are green.

## Every floor reader (the question "does anything still read a floor that is not the derived one?")

`git grep -n -i "min_quality|MIN_QUALITY|minQuality"` over the tracked tree, excluding review,
research, decision and ledger records, finds:
- **Engine:** `adapter/main.py:1295` serves the derived floor. `:1283` is the stale comment
  (MINOR-4).
- **Scripts:** `calibrate_board.py:74, :86, :159` are the ALTERNATIVE ranked-population method's
  own dict key, printed beside the served floor (`:155`), not served. `arena_calibration.py:12` is
  prose.
- **iOS:**
  - `Models.swift:60, :74` decode the field as `Double?`. `ContentView.swift` and `Detail.swift`
    pass it through.
  - `EngineClientTests.swift:170-181` and `LanguageTests.swift:21, :24` are payload fixtures.
  - No Swift file holds a floor constant.
- **Tests:** only the rewritten tests above.
- **Docs:** only historical records (process log, M11 council, M14 retrospective, earlier plans).

`git grep` for the fourteen old floor values in `src`, `scripts`, `ios`, `README.md` and `docs/*.md`
finds anchors (pinned, D-146), payload fixtures, and two docstrings that tell history
(`test_epoch_board.py:157`, `test_categories.py:353`). None is read as a floor. The one
reader-facing number that no longer matches is MINOR-5's "50 is at the bar".

## Hardened-invariant producer section (Code-Reviewer §2a-bis)

**Invariant (D-159): every floor a reader or a decision sees is `derived_floor` on the artifact
in hand.**

| Producer | Line | Citing test | Status |
|---|---|---|---|
| Budget Pick (`recommend`) | `recommend.py:494` | `test_floor_served.py:78`, `:103`; `test_recommend.py:259`, `:445` | covered |
| Plan answer (`subscribe`) | `subscribe.py:439` | `test_subscribe.py:135`, `:195` | **gap**: empty board, printed precision (MINOR-1, MINOR-2) |
| `/v1/categories` `min_quality` | `main.py:1223` | `test_floor_served.py:51`, `:58`, `:71`; `test_uncertainty_contract.py:304`, `:340` | covered |
| Measurement (`survey_boards --floors`) | `survey_boards.py:198` | `test_floors.py:54`; `test_survey_floors.py` | covered |
| `calibrate_board --self-check` | `calibrate_board.py:155` | none (a printing script) | gap, low |
| **Refresh decision (`serving_summary`, guards)** | `refresh.py:336` | **none; it does not read the floor** | **BLOCKING-1** |

**Symbol check.** `grep -n "derived_floor\|unmet_floor_warning"` over `src` and `scripts`:
```
src/app/workflows/recommend.py:455:def unmet_floor_warning(floor: float | None, unit: str, noun: str) -> str:
src/app/workflows/recommend.py:494:    floor = derived_floor(conn, spec)  # D-159: from the board this answer reads
src/app/workflows/subscribe.py:439:    floor = derived_floor(conn, spec)  # D-159: from the served board
src/app/adapter/main.py:1223:        return ages, {spec.id: derived_floor(conn, spec) for spec in CATEGORIES.values()}
scripts/survey_boards.py:198:        floor_rows = derived_floor(conn, spec)  # D-159: the engine's own function
scripts/calibrate_board.py:155:        served = derived_floor(conn, spec)  # D-159: the floor the engine serves from this artifact
```

## Plan compliance and K.8

**P1, P2 and P3 are delivered as written** (`docs/plans/m17-wave-1-plan.md` §Phases):
- the one function, with the script importing it;
- every reader moved to it, and `min_quality` removed;
- `test_floor_rule.py` rewritten, W-128 FIXED, the clarification written, and the `categories.py`
  header stating the rule.

**What the plan did not cover.** It never mentions D-159 clause 3 or the refresh. That is
BLOCKING-1: the plan's scope, not only its execution, missed the one consumer of served content
that decides publishing.

**Drive-bys.** `categories.py:54-58` rewrites the clause-2 header comment to the amended D-148
(W-127). That is documentation of a change already ruled, and it is harmless.

**K.8 contract.**
- **The field's shape is unchanged.** `/v1/categories` `min_quality` is still one field per
  surface, and `/v1` gained no field.
- **Its value can now be `null`.** That happens with no artifact (as before, for ages) or with an
  empty own board. D-152 does not promise non-null. The app decodes `Double?`
  (`Models.swift:60`) and says nothing on a null floor (`DetailTests`
  `testNoFloorIsInventedWhenTheEngineSendsNone`, per REQ-FLR-002). REQ-FLR-001 records the null.
- **`why_fact.floor` can now be `null`,** which is new, and the phone's handling is MINOR-1.

## K.9 candidates outside this wave's scope

- **MINOR-5** ("50 is at the bar" in the app) needs an owner ruling. It belongs to whichever wave
  next touches `Language.swift`.
- **`test-documented-paths` passes only on the owner's disk.** It resolves
  two file names in `docs/reviews/m16-closure-security-review.md:15` against two UNTRACKED files
  at the repository root. My copy left them out, and the records leg failed on exactly those two paths
  (details under Gates). A clean checkout, such as CI, would fail the same way. Add them to
  `.path-refs-allow` or reword the record. This predates the wave (the record is on `main` since
  `5a8b685`).

## Gates

`make -o install -o .venv/bin/python check-fast` on the copy, after purging bytecode caches:
- **python leg PASS:**
  - lint: ruff "All checks passed!".
  - typecheck: mypy "Success: no issues found in 36 source files".
  - test: pytest **1182 passed, 15 skipped**, total coverage 90%. Touched modules: `floors.py`
    100%, `recommend.py` 95.4%, `subscribe.py` 96.3%, `adapter/main.py` 96.7%.
  - coverage-floor: "PASS: 36 module(s)".
  - The 15 skips are network contract tests and `EPOCH_DATA_DIR` tests. Every artifact test ran.
- **client leg PASS:** client-decls.
- **swift leg PASS:** "PASS: 268 test(s), exactly the ones named in the manifest".
- **records leg FAIL, 1 of 14 conformance tests.** The failure is `test-documented-paths`, with 2
  dangling paths: the owner's two untracked root files, which I was told to leave out (see K.9).
  With two empty placeholders present, `make conformance` passes, "14 test(s) ... 0 failing".
  **Nothing else failed.**

## What I did not check

- **A real refresh cycle.** I demonstrated BLOCKING-1 on `serving_summary`, `degradations` and
  `upward_anomalies` directly, on artifact copies, not through a full `refresh()` with live
  upstreams. The `EXIT_UNCHANGED` branch it lands in is read, not run (`refresh.py:1027-1043`).
- **The app on a device.** The Turkish fallback in MINOR-1 is read from `Language.swift:87` and
  `ContentView.swift:755`, not rendered.
- **The six stale floors of the fresh Epoch bundle.** D-159 says the fresh bundle moves six floors
  (`abstract` 72.8 to 84.7). The owner's `advisor.db` still gives the M16-W3 values, so I did not
  see a moved floor on real data. Every move I show is constructed.
- **`make check` (the merge gate).** I ran `check-fast`, as instructed.
- **Security (Stage 4.0).**
