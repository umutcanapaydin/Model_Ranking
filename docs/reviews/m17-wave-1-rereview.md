---
record_type: review
id: m17-wave-1-rereview
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M17-W1 fix round -- independent re-review (commits 1c4ea31..9cf2b0d)

**Seat:** independent (Code-Reviewer + Tester combined). I wrote none of this fix round and none of
the wave it answers.

**Scope:** `git diff origin/main...HEAD` on `enhancement/m17-w1-fixes` (draft PR #12). The merge base
is `e66a2b3` (PR #11's merge) and HEAD is `9cf2b0d`. There are two commits:
- `1c4ea31` adds the tests (red).
- `9cf2b0d` is the fix. It also commits the first review and deletes the W1 working plan, which
  `.path-refs-allow:81` says is the convention.

**What I read it against:**
- `docs/reviews/m17-wave-1-review.md`: BLOCKING-1, MINOR-1 to MINOR-5 and NIT-1 to NIT-3.
- D-159 with its clarification and the new correction (`docs/decisions.md:2694-2737`), D-128 and
  D-132.
- The owner's ruling in `docs/plans/m17-plan.md` §0.1.
- The refresh's publish path (`src/app/workflows/refresh.py`: `serving_summary`, `_reason_to_refuse`
  and the `EXIT_UNCHANGED` branch).

**Policy:**
- I read my policy only from `git show origin/main:subagent-profiles/Code-Reviewer.md` and
  `.../Tester.md`.
- `git diff --stat origin/main...HEAD -- subagent-profiles AGENTS.md .agents .claude
  permission-matrix.md docs/security-baseline.md` is empty.
- Nothing in the diff addresses a reviewer, so there is no injection-class finding.

**Families:** the commits are authored as Claude, and this seat is also Claude. No second family was
available to me, so this is the fallback. My context was fresh: I did not see the author's session.

**How I worked:**
- **The copy.** I made a `git clone` of the repository in a NEW subdirectory of the session scratch
  directory, checked out `9cf2b0d`, and set its `main` and `origin/main` to `e66a2b3`. It holds only
  tracked files, so the two untracked files at the owner's repository root are not in it.
- **The artifact.** I copied the owner's `advisor.db` (md5 `214139e9...`) and
  `advisor.db.refresh.json` (`d729a3f6...`) into the copy. Both were unchanged in the repository at
  the end.
- **The venv.** I built a fresh one in the copy (`make install`). Its editable `.pth` points at the
  copy's own `src`.
- **The red commit.** I replayed it from a `git archive` export.
- **No state changes.** I made no git state change in the repository and started no server. The
  only repository file I created is this one.

**Snapshot.** The md5 of each file in my copy equals `git show 9cf2b0d:<file>`, at the start and after
every mutant:

| File | md5 |
|---|---|
| `refresh.py` | `2b857d08` |
| `recommend.py` | `059ca5c1` |
| `subscribe.py` | `9d8bad54` |
| `floors.py` | `ab0a896d` |
| `adapter/main.py` | `b937b7ff` |
| `Language.swift` | `47919093` |

**The working tree moved during this review.** When I started, the repository was on
`enhancement/m17-w1-fixes` with two untracked files. Partway through, its working tree was on
`upgrade/devflow-v6.4` with an unfinished merge (about 120 staged and conflicted paths). I did not
cause it and did not touch it. The branch ref `enhancement/m17-w1-fixes` is still `9cf2b0d`, and
every result here is against that commit in my own clone. This file was written into that working
tree as an untracked file. **It belongs on the fix branch, not on the upgrade merge.**

## Verdict

**BLOCKING: 1 BLOCKING (a red merge gate, not a code defect), 1 owner ruling needed before merge,
6 MINOR, 2 NIT.**

**The code closes BLOCKING-1, and I found no new side effect:**
- **The fingerprint now sees the floor.** `refresh.py:391` hashes `derived_floor(conn, spec)` for
  every surface, inside the same loop and from the same connection that hash the ranked rows.
- **The repair runs through the real cycle.** The cycle test `test_floor_served.py:168` drives the
  real `refresh()` and `build.main`. On the pre-fix source it FAILS with exactly the review's symptom:
  `nothing a user would notice changed`, exit 1. On HEAD it passes.
- **No new churn.** On the owner's artifact, two fingerprints in a row are identical. Mutant R6 hashes
  a clock beside the floor, and it is killed by `test_refresh.py::test_two_cycles_against_an_unchanged_upstream_publish_once`
  among 30 others. So a nondeterministic floor could not slip in.
- **No persisted digest to invalidate.** No digest is compared across versions: the live fingerprint
  is recomputed each cycle (`refresh.py:945`, `:790`). The code change therefore does not turn the
  first cycle after deploy into a publish.
- **The cost is small.** The 14 derivations take 2.1 ms. A whole `fingerprint_of` on the owner's
  artifact takes 42-47 ms, and it runs at most four times per cycle.
- **A floor of `None` hashes safely.** It hashes as the text `None`, which is stable and distinct
  from any number. On a copy with `coding`'s own board deleted, the digest changed, and nothing
  raised.
- **The precision is right.** The floor is already rounded to one decimal (`floors.py:30`), so float
  noise cannot trip the digest. Mutant F1 (no rounding) is now also killed by
  `test_refresh.py::test_rounding_noise_below_the_published_precision_is_not_a_change`.

**What blocks:** CI on PR #12 is red. So is `make check-fast` on a clean copy, which the PR
description reports as PASS (BLOCKING-R1).

**What the owner must rule on:** the D-159 correction withdraws part of an owner-ruled ADR without
the owner (OWNER-R1). Its reasoning is right about the guard it withdraws. It over-reaches in two
ways and leaves a narrower hole unguarded.

## Disposition of the first review's findings

| Finding | Status | Evidence |
|---|---|---|
| **BLOCKING-1**, fingerprint half | **CLOSED** | `refresh.py:44`, `:387-391`. `test_floor_served.py:123` was RED at `1c4ea31` (digest `ec83cf0a...` equal before and after) and is GREEN at HEAD. `test_floor_served.py:168` is RED on the pre-fix source and GREEN at HEAD. Mutants R1, R2 and R3 are RED |
| **BLOCKING-1**, guard half (D-159 clause 3) | **WITHDRAWN by the correction.** The owner has not ruled | `docs/decisions.md:2726-2737`. See OWNER-R1 |
| **MINOR-1**, reason code | **CLOSED** | `recommend.py:578-587` emits `{"reason": "no_floor_measured", "unit": ...}`. `test_floor_served.py:103` and `:136` (both RED at `1c4ea31`). Mutants E1 and E2 are RED |
| **MINOR-1**, phone | **CLOSED** | `Language.swift:41-42` and `:92-97` give an English and a Turkish sentence. `LanguageTests.swift:27-29`, `:34`, `:46`, `:311`. Mutants W1, W2 and W3 are RED. Two gaps remain (MINOR-R2, MINOR-R3) |
| **MINOR-1**, plan answer (M16) | **CLOSED** | `test_subscribe.py:670`. Mutant S1 (`or 0.0`) is RED |
| **MINOR-2** (`:.0f` in `subscribe.py`) | **CLOSED** | `test_floor_served.py:150` reads both modules' sources and requires `:g`. Mutant S2 is RED |
| **MINOR-3**, rounding in CI | **CLOSED** | `test_floors.py:29`. Mutant F1 is RED WITHOUT the artifact, with 2 killers |
| **MINOR-3**, `value_window < floor` in CI | **OPEN, not recorded** | `test_categories.py:343` is still artifact-only. The fix neither moved it to a fixture nor filed it |
| **MINOR-4**, REQ-FLR-001 | **CLOSED** | `docs/prd.md:533` now cites `test_floor_served.py` and the served == derived test |
| **MINOR-4**, anchor comment | **CLOSED** | `adapter/main.py:1276-1281` |
| **MINOR-4**, W-128 "independent" | **PARTIAL** (NIT-R1) | The oracle now orders with SQLite (`test_floor_rule.py:22-34`), but its index formula `max(0, round(count / 3) - 1)` and its rounding are the same as `floors.py:30`. It shares no code. It still shares the reading of "a third of the way down", which is what the first review asked the ledger to say |
| **MINOR-5** ("50 is at the bar") | **RECORDED, left to the owner honestly** | PR #12's description has a section "Needs an owner ruling (MINOR-5)" with two options, and `adapter/main.py:1277-1281` names it. The app text is unchanged (`Language.swift:205-206`, `Uncertainty.swift:172`). Durability: see MINOR-R6 |
| **NIT-1** (`survey_boards.py:178` docstring) | **OPEN** | still "beside the two it did not choose and today's" |
| **NIT-2** (a test never shown red) | n/a | history. The same pattern recurs in this round (MINOR-R5) |
| **NIT-3** (read-write handle on the artifact) | **OPEN** | `test_categories.py:331` still calls `sqlite3.connect("advisor.db")` |

## BLOCKING

### BLOCKING-R1 -- the merge gate is red on a clean checkout and in CI; the PR says PASS

**Where:** `docs/reviews/m17-wave-1-review.md:53`, `:54`, `:453` and `:472`. That record is added
by this branch. It names the two untracked files at the owner's repository root as paths.
`conformance/test-documented-paths.py` resolves them against the delivered tree, and no row of
`.path-refs-allow` declares them.

**Evidence:**
- **Clean copy.** `make check-fast` on my clean copy gave:
  - python leg PASS;
  - client leg PASS;
  - swift leg PASS;
  - records leg FAIL, "test-documented-paths FAIL: ... 6 dangling".
- **CI.** PR #12's CI run 35860206464 fails the same way, in `install-and-governance` step
  "Conformance -- every gate rejects what it must", with the same six references.
- **The PR description.** It says "`make check-fast`: PASS". That is true only on the owner's disk,
  where those two files exist.
- **A second failure was mine, not the branch's.** `test-commit-identity` failed too until I gave my
  clone a local `main` branch. After that it passed, and CI shows it passing.

**Why blocking:** the Tester profile requires honest red and green, and the merge gate cannot pass as
committed. This is the same class the first review filed as K.9 for the M16 record, which `348fa00`
fixed on `main`. The new record reintroduced it.

**Fix:** a records change, not code. Either reword the four lines so they do not name the files as
paths, or add two exact rows to `.path-refs-allow` with a reason.

## Needs an owner ruling before merge

### OWNER-R1 -- the D-159 correction withdraws an owner-ruled clause, and one hole it leaves is real

**What the correction says** (`docs/decisions.md:2726-2737`): clause 3's guard "does not exist and
should not be built", because the floor is a label, not a filter, and a guard refusing "a floor that
empties a budget" would freeze the refresh.

**Where the reasoning is right.** I checked it against the code:
- **The floor filters nothing.** `recommend.py:500-502` takes the Budget Pick as
  `min(floor_pool or rows, ...)`, so the floor never removes a model from an answer. It only changes
  which in-budget model is named, and whether the WARNING is shown. `subscribe.py:440-442` has the
  same shape.
- **The real filter is the budget,** and D-128's `eligible` axis already guards a budget emptying
  (`refresh.py:229-236`).
- **The freeze argument holds.** Once a board legitimately rises past what a `low` budget buys, a
  refuse-guard on "nothing clears" would refuse every later candidate too. That is D-128's own
  freeze failure.
- **The guard therefore should not be built as clause 3 worded it.**

**Where it over-reaches:**
1. **The owner did not rule on it.** D-159 is "accepted -- ruled by the owner" (`:2696`). The owner's
   words were "D-128/D-132 still guard" (`docs/plans/m17-plan.md` §0.1). The first review said this
   axis was "a judgement for the lead and the owner".
   - This repository's precedent for withdrawing part of an accepted ADR is the M15-W4 amendment
     (`docs/decisions.md:2209-2216`). It was "Put to the owner again ... Ruled by the owner".
   - The correction records no ruling, and PR #12 presents the withdrawal as done rather than as a
     question. Policy (Code-Reviewer §5) treats a reversed decision without supersession as
     blocking. I record it as an owner ruling rather than a second BLOCKING only because an appended
     amendment IS this repository's accepted form. The owner merges; the owner should rule on it in
     writing first.
2. **"A guard that does not exist" is half wrong.** Clause 3 has two halves. Its second half ("or
   moves a surface's roster past the limits") exists: D-128 and D-132 still run on every candidate
   (`refresh.py:772-781`, unchanged). Only the "empties a budget" half is withdrawn, and the text
   should say so.
3. **The floor's own input is now outside every guard.** This is the real hole. D-132 exists because
   "an injected set arrives together" (a feed that a bug or an attacker controls). Its name axis reads
   RANKED names only (`ServingSummary.models`), and the floor is derived from ALL rows.
   - **Measured on a copy of the owner's artifact.** 60 unpriced rows added to `swebench` move
     `coding`'s floor from 65.4 to 71.3. The digest changes, so the candidate now publishes. Both
     `degradations` and `upward_anomalies` return `[]`.
   - **The effect.** A burst of rows nobody prices can move every surface's served `min_quality`, and
     turn its Budget Picks into WARNINGs, with nothing to object.
   - **Before M17 this could not happen.** The floor was a constant.
   - **A narrower guard need not freeze.** It could extend D-132's "a quarter of the names are new"
     test to the board's rows. D-132 measured ordinary movement at 0% new names.
   - **Not the author's call.** Whether to build that guard, or accept and record the risk, is a
     ruling. At minimum it should be a warnings-ledger row, not silence.

## MINOR

- **MINOR-R1: the fingerprint's per-surface coverage and precision are unpinned.**
  - **Mutant R5** hashes only `coding`'s floor. It stays GREEN on the full suite, because every floor
    test moves `coding`.
  - **Mutant R4** hashes the floor rounded to a whole number. It also stays GREEN. A 0.1 move is
    served (`min_quality` has one decimal) and can change the Budget Pick, yet it would read as
    unchanged.
  - **Killer tests.** I wrote two, in scratch only. K1 raises every surface's board in turn and
    asserts the digest changes while the ranked counts do not. K2 moves `coding`'s floor by 0.1
    without changing its whole-number rounding. Both pass on HEAD, and R5 and R4 are RED on them.
    The md5 matched afterwards.
- **MINOR-R2: the `no_floor_measured` fact's shape is pinned only on the Swift side.**
  - **The dependency.** `whySentence` returns `nil` without a `unit` (`Language.swift:59`). The
    Turkish screen then shows the engine's English, which is MINOR-1's own symptom.
  - **Mutant E3.** It drops `unit` from the fact, and it is GREEN on the full Python suite. The Swift
    tests use their own hand-written fixture (`LanguageTests.swift:27-29`), which carries `unit`.
  - **No contract test.** `tests/unit/test_ios_client_contract.py` pins no reason code, so nothing
    ties the engine's reason vocabulary to `PickReason`. The engine and the app each hold the literal
    separately.
  - **Killer test.** My scratch K3 asserts
    `why_fact == {"reason": "no_floor_measured", "unit": spec.score_unit}`. It passes on HEAD and is
    RED on E3.
- **MINOR-R3: `test_why_facts.py`'s reason inventory is stale, and it fails on a legitimate
  artifact.**
  - **The stale lines.** `REASONS` (`:27`) and the budget-pick subset (`:105`) still list four and two
    reasons.
  - **The failure.** On a copy of the owner's artifact with `coding`'s 173 own-board rows deleted
    (the D-156 expiry case, which the refresh can publish), 4 tests fail against a correct engine. I
    ran it with the artifact swapped in the copy and restored it by md5. Three are
    `test_every_pick_carries_a_fact_for_its_sentence[coding-*]` and one is
    `test_the_reason_distinguishes_the_two_budget_pick_cases`.
  - **Why it matters.** After such a publish, the owner's `make test` (`MODEL_RANKING_REQUIRE_ARTIFACT=1`)
    goes red for a reason that is not a defect.
- **MINOR-R4: MINOR-3's second half is neither fixed nor filed.** `value_window < floor` (CAT-10) still
  runs only where `advisor.db` exists (`test_categories.py:343`). The commit message calls MINOR-3
  handled.
- **MINOR-R5: the PR's evidence claims overstate.**
  - **"Every new test was committed red first."** Four of the new tests were not:
    - The cycle test `test_floor_served.py:168` first appears in the GREEN commit `9cf2b0d`. I
      replayed it red on the pre-fix source, so the proof exists, but it was not committed red.
    - `test_floors.py:29`, `test_subscribe.py:670` and `test_floor_served.py:150` pass at `1c4ea31`.
      They are mutant killers, which is legitimate, but they are not red-first tests.
  - **"`make check-fast`: PASS."** See BLOCKING-R1.
- **MINOR-R6: MINOR-5's owner question lives only in the PR description and a code comment.**
  - A PR description does not survive as a record, and a comment in `adapter/main.py` is not where an
    owner looks.
  - It deserves a warnings-ledger row naming the two options, so the next wave that touches
    `Language.swift` finds it.
  - The disposition itself is honest: the fix changed no app text and put both options to the owner.

## NITs

- **NIT-R1.** W-128's new wording ("sharing no code with `floors.py`") is literally true, but it still
  implies more independence than it has (see the MINOR-4 row above).
- **NIT-R2.** The cycle test (`test_floor_served.py:168-187`) asserts only `EXIT_PUBLISHED`. It does
  not assert its own precondition: that no ranked row changed and that the floor did. If a fixture
  change ever priced those nine models, it would pass for a different reason. Today the red replay
  proves the precondition holds.

## The new reason, end to end

| Reader | Empty own board | Evidence |
|---|---|---|
| Engine `recommend` (`/v1/recommendations`, CLI) | `why_fact {"reason": "no_floor_measured", "unit"}`. `why` is the WARNING "own board is empty" | `recommend.py:455-463`, `:578-587`; `test_floor_served.py:103`, `:136` |
| Plan answer (`subscribe`, CLI only; no `/v1` route) | the same WARNING through `unmet_floor_warning(None, unit, "plan")`. It has no fact, as before | `subscribe.py:439-442`, `:578-580`; `test_subscribe.py:670` |
| `/v1/categories` | `min_quality: null` | `adapter/main.py:1223`; `test_floor_served.py:71` |
| App (this build) | both languages, no number quoted | `Language.swift:92-97`; `LanguageTests.swift:34`, `:46`, `:311` |
| App (an older build) | `PickReason(rawValue:)` is `nil`, so it falls back to the engine's English. That is additive and never invents a sentence | `Language.swift:52-54` |
| Artifact-bound tests | **stale** | `test_why_facts.py:27`, `:105` (MINOR-R3) |

## Hardened-invariant producer section (Code-Reviewer §2a-bis)

**Invariant (D-159): every floor a reader or a decision sees is `derived_floor` on the artifact in
hand. Since this round, a moved floor is also a served change.**

`git grep -n "derived_floor(" -- src scripts` at `9cf2b0d`:
```
scripts/calibrate_board.py:155:        served = derived_floor(conn, spec)  # D-159: the floor the engine serves from this artifact
scripts/survey_boards.py:198:        floor_rows = derived_floor(conn, spec)  # D-159: the engine's own function
src/app/adapter/main.py:1223:        return ages, {spec.id: derived_floor(conn, spec) for spec in CATEGORIES.values()}
src/app/workflows/floors.py:42:def derived_floor(conn: sqlite3.Connection, spec: CategorySpec) -> float | None:
src/app/workflows/recommend.py:494:    floor = derived_floor(conn, spec)  # D-159: from the board this answer reads
src/app/workflows/refresh.py:391:        digest.update(f"floor:{name}:{derived_floor(conn, spec)}\n".encode())
src/app/workflows/subscribe.py:439:    floor = derived_floor(conn, spec)  # D-159: from the served board
```

| Producer | Citing test | Gap |
|---|---|---|
| Budget Pick, `recommend.py:494` | `test_floor_served.py:78`, `:103`, `:136`; `test_recommend.py:259` | the fact's shape (MINOR-R2) |
| Plan answer, `subscribe.py:439` | `test_subscribe.py:135`, `:670`; `test_floor_served.py:150` | none |
| `/v1/categories`, `main.py:1223` | `test_floor_served.py:51`, `:58`, `:71` | none |
| Refresh fingerprint, `refresh.py:391` (new) | `test_floor_served.py:123`, `:168` | per-surface coverage and precision (MINOR-R1) |
| Refresh guards | none, withdrawn | OWNER-R1, item 3 |
| `survey_boards.py:198`, `calibrate_board.py:155` | `test_floors.py`, `test_survey_floors.py`; none for calibrate | unchanged since the first review |

## Mutants

**How each mutant ran:**
- One at a time, in place, on the copy.
- The harness replaced one exact string and refused any string that did not match exactly once.
- Python mutants ran the full `tests/unit` suite (`-n auto`, `MODEL_RANKING_REQUIRE_ARTIFACT=1`).
  The F1 run moved `advisor.db` aside and cleared the flag, which is CI's view.
- Swift mutants ran `make swift-test-parallel`.
- Each change was string-replaced back, and the md5 was compared with the value taken before. All 19
  restores were byte-identical.
- At the end, the six snapshot files matched `git show 9cf2b0d:<file>`. My scratch killer file was
  deleted, and `git status --short` in the clone was empty.

| # | Mutant (load-bearing line) | Result |
|---|---|---|
| R1 | `refresh.py:391` deleted (the floor not hashed) | RED, 2 (`test_floor_served.py:123`, `:168`) |
| R2 | `:391` hashes a constant | RED, 2 |
| R3 | `:391` hashes the top third of the RANKED rows | RED, 2 |
| **R4** | **`:391` hashes the floor rounded to a whole number** | **GREEN, full suite.** RED on scratch K2 (MINOR-R1) |
| **R5** | **`:391` hashes only `coding`'s floor** | **GREEN, full suite.** RED on scratch K1 (MINOR-R1) |
| R6 | `:391` adds a clock to the hash (churn) | RED, 30 (incl. `test_refresh.py` two-cycles, `test_floor_served.py:168`) |
| E1 | `recommend.py:581` `no_floor_measured` never emitted | RED, 2 |
| E2 | `:581` `no_floor_measured` whenever the floor is unmet | RED, 6 |
| **E3** | **`:581` fact without `unit`** | **GREEN, full suite.** RED on scratch K3 (MINOR-R2) |
| E4 | `recommend.py:461` warning loses "board is empty" | RED, 2 (incl. `test_subscribe.py:670`) |
| S1 | `subscribe.py:439` `or 0.0` (first review's M16) | RED, 1 (`test_subscribe.py:670`) |
| S2 | `subscribe.py:578` `{floor:.0f}` (first review's M24) | RED, 1 (`test_floor_served.py:150`) |
| F1 | `floors.py:30` no rounding, WITHOUT the artifact (first review's M03) | RED, 2 (`test_floors.py:29`, `test_refresh.py` rounding noise) |
| W1 | `Language.swift:42` raw value `no_floor` | RED (`testEveryReasonTheEngineCanEmitHasBothSentences`, en and tr) |
| W2 | `Language.swift:96` Turkish sentence gone | RED (two `LanguageCompositionTests`) |
| W3 | `Language.swift:93` English sentence gone | RED (two `LanguageCompositionTests`) |

**Totals:** 16 mutants give 13 RED and 3 GREEN. None is equivalent. Each GREEN mutant is closed by a
scratch killer test (K1, K2, K3). Each killer passes on HEAD and is RED on its mutant; the three
re-runs are the other 3 of the 19 restores. The killers are not in the repository: this seat changes
no file but its own.

## Red to green, replayed

- **`1c4ea31` (red), from a `git archive` export.** 3 tests fail, and each failure is the claimed
  symptom:
  - `test_the_budget_pick_says_when_its_board_is_empty` gets `nothing_clears_floor`;
  - `test_a_floor_moved_by_rows_the_ranking_never_carries_is_a_served_change` gets identical digests;
  - `test_an_empty_own_board_has_its_own_reason_code`.

  The other 33 tests in `test_floor_served.py`, `test_floors.py` and `test_subscribe.py` pass
  (MINOR-R5).
- **HEAD's cycle test on the pre-fix source.** It fails with `AssertionError: nothing a user would
  notice changed`, `assert 1 == 0`.
- **HEAD.** Everything passes.

## Gates

`make check-fast` on the clean copy (tracked files plus the owner's `advisor.db`):
- **python leg PASS:**
  - ruff and mypy are clean.
  - pytest: **1187 passed, 15 skipped**, total coverage 90%.
  - Touched modules: `refresh.py` 96%, `recommend.py` 95%, `subscribe.py` 96%, `adapter/main.py`
    97%, `floors.py` 100%.
  - coverage-floor: "PASS: 36 module(s)".
- **client leg PASS.**
- **swift leg PASS:** "PASS: 268 test(s), exactly the ones named in ios/EngineTests/test-manifest.txt".
- **records leg FAIL** on `test-documented-paths` (BLOCKING-R1). Everything else in the leg passed:
  - `check_records`, its self-test and `wave-check-all` ("43 ... record(s) validated");
  - the other 13 conformance tests, once my clone had a local `main`.

**The skips.** The 7 skips in `tests/unit` are `EPOCH_DATA_DIR` contract tests. Every artifact test
ran.

## K.9 candidates outside this round's scope

- **A reason-vocabulary contract test.** It would hold the engine's `why_fact` reasons, with their
  required keys, against `PickReason` and the `number`/`label` guards in `whySentence`. It would
  close MINOR-R2 and MINOR-R3 as one class.
- **A board-level D-132 axis** (OWNER-R1, item 3), if the owner wants it.

## What I did not check

- **A live refresh against real upstreams.** The cycle test runs the real `refresh()` and
  `build.main` on the canonical fakes.
- **The app on a device.** The Turkish sentence is proven by the Swift tests, not rendered.
- **`make check`,** which is the merge gate. I ran `check-fast` as instructed. `make check` shares the
  failing `conformance` leg.
- **Security (Stage 4.0).**
