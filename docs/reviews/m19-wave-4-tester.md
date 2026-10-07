---
record_type: review
id: m19-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# Wave 4 Tester Review (m19)

**Reviewer:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records,
and it sat in none of the wave's three code reviews.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `3426ff3..d324669` (20 commits; 90 files, +85305 / -72, most of it committed probe
runs). It holds the three Code-Reviewer verdicts and the fixes for each, the last being `b957ec0` (red)
and `d324669` (the image rule's reach beyond `vision` taken out, #191).
**Risk tier:** HIGH (`docs/plans/m19-wave-4-plan.md:13-15`). What the on-device model's output decides
(D-126) is touched, and `ios/ModelRanking/Engine/Router.swift` is a security glob. By D-172 no security
seat runs on the wave.
**Code-Reviewer verdict:** the last one in the range is round 3 (`m19-wave-4-review-round-3.md`),
BLOCKING (B1, M1, M2). `d324669` is the fix that verdict prescribed: the reach comes out, the
keep-its-surface tests stay, and a red test comes first. No review seat has read `d324669` yet. This
seat ran on the caller's dispatch. It checked B1's fix as a test question only: F17 below plants the
reach back, and three tests go red. The code verdict on `d324669` is still owed. `make wave-check` reads
`docs/reviews/m19-wave-4-review.md`, and that file does not exist yet.
**Model routing (HIGH, advisory):** author family: Claude (all 20 commits carry `GP-Agent:
claude-code/local-lane`) / reviewer family: Claude (Opus 5.5). Fallback reason: no second model family
is available to this seat. Fresh context: I read the profile and the rules first, then the plan, D-184,
the record and the three reviews, then the diff.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75dac85...`) on
`origin/main` and in the tree. The range does not touch `.claude/` or `.agents/`. Nothing in the diff
tries to change this review's policy.

## Verdict

MINOR

**Nothing blocks.** Each phase's acceptance check has a test that exercises it, and the tests pass.
Each red commit of the wave fails on its own tree and passes on its fix: `1ef5657`, `1e9a92a`,
`b2723f8` and `b957ec0`. The two tests the last fix deleted held only the reach that #191 took out.
The whole Swift suite passes in a scratch copy: 490 tests, which is exactly the manifest. So does the
Python suite inside the offline profile: 2079 passed, 25 skipped.

**Fault injection: 45 of 70 faults were killed before this review (64%), and 66 of 70 after.** In the
Swift reading, 8 of 45 faults passed the whole suite of 483 tests:
- "hangisi" read again as a fact word;
- "hangi" before any noun read as a fact word;
- a Turkish question of fact typed in capitals no longer read;
- "what's" no longer read as an opener;
- a phrase not counted toward small talk's bound;
- the Turkish modifier rule removed (since #191 its tests route to `web-dev`, where the rule no
  longer acts);
- "fotograf" (no Turkish letter) removed;
- the window after "arka plan" cut to one word.

Seven tests kill all eight. The scorer behind every figure in the record had no test: ten faults
passed the whole suite. A test file now kills all ten, and it pins the record's held-out figures to the
committed runs. Two holes in the held-out gates are closed by this seat's change to the gates (M1, M2).
Four faults in the replay harness pass every committed test. This seat's exactness replay catches all
four (M3).

**The record's numbers follow from the committed runs.** I scored every run with `score_w4.py`, counts
only. I replayed the model-tier runs through `d324669`. I re-ran the wording tier on `d324669`. Every
figure in §2, §3, §4 and §6, in D-184's "Measured" paragraph and in REQ-IMG-003 matches. The
`review3-*` and `review3w-*` runs are exactly the shipped code's output: 0 rows differ. The findings
are records that say less, or something older, than what was measured (M4, M5, M6).

## Acceptance-criterion coverage (REQUIRED)

The wave's phases (`m19-wave-4-plan.md:95-101`) and the REQ rows they update:

- **P1, #177** (fresh sets and the retirement in one commit; the held-out gates pass on it) →
  `5fe0793` holds both set files and the `RETIRED_HELD_OUT` change
  (`tests/unit/test_ios_client_contract.py:213`, with #177's outcome in the comment). The gates,
  run on `5fe0793`'s own exported tree, pass: 5 passed. On the tree, `:175`
  (`test_no_held_out_question_is_written_into_the_code_or_its_tests`) and `:1576`
  (`test_every_signal_word_only_a_live_held_out_set_holds_is_reviewed`) pass, with the 22 entries at
  `:1593`. I checked each entry's stated origin. The 17 "before" entries are all in `Reading.swift` at
  `23a81da`. The five entries added after the measure change no held-out row on either tier at
  `d324669`: I took them out of a scratch copy and replayed (V1, V2). GREEN. Two holes are closed by
  this seat's change (M1, M2).
- **P2** (the probe's wording-tier mode; the baseline twice per tier; the bars before any variant) →
  `bd355c9` adds the mode. The baseline runs and the bars are committed at `a34453b`, before every
  variant run (`ae2c528`). The two wording runs are identical row for row, as §2 says. A process
  criterion: no suite test runs a probe harness (M3). The bars are now held by this seat's
  `tests/unit/test_reading_probe_scorer.py:107` (the rule) and `:166` (each bar from the baseline's
  lower run). GREEN.
- **P3, #66** (three variants; the best built red-first, with `ReadingTests` holding each side of its
  line) → `ios/EngineTests/ReadingTests.swift:522` (`testAQuestionOfFactIsRead`: 12 questions of fact
  and 11 near-searches), `:587` (a doubt on the model tier, the note with the model's doubt, a doubt on
  the wording tier), `:634`, `:706`, `:182` (no genuine tuning question trips it, one named). The class
  at `:517` cites REQ-ASK-005. The variant runs are committed, and (a) and (c) ran once, as the record
  says. GREEN, with F7, F40, F44 and F45 now killed by this seat's `:759`, `:768` and `:773`.
- **P4, #113** (three variants; the best built red-first on both tiers; after #191, on `vision`
  only) → `:577` (the Turkish forms), `:727` (`testTheImageRuleOverridesOnlyAQuestionRoutedToVision`,
  red at `b957ec0` with 10 assertions), `:321`, `:611`, `:684` (questions about a site's or a file's
  image keep their surface), `:432` (the rule on the wording tier). GREEN, with F35, F37 and F39 now
  killed by this seat's `:788`, `:801` and `:806`.
- **P5** (the held-out measure, the record, D-184, the REQ rows) → the record and D-184 are in the
  range. Its figures are held by this seat's `tests/unit/test_reading_probe_scorer.py:166`. GREEN, with
  record drift in M4, M5 and M6.
- **REQ-ASK-005** → `ReadingTests.swift:522`, `:549`, `:557`, `:568`, `:587`, `:634`, `:650`, `:663`,
  `:706`, `:712`, and this seat's `:759` to `:779`. **REQ-IMG-003 / REQ-RTR-005** → `:577`, `:727`,
  `:305`, `:321`, `:611`, `:684`, and this seat's `:788` to `:806`.

## Red→green on reported symptoms

Each commit was exported with `git archive` into the scratchpad, and its `Reading*` classes were run on
its own tree. Nothing in the worktree was checked out.

- **#66 and #113's tuning misses** → at `1ef5657` (the `asksAFact` stub returns false): 7 tests fail,
  38 assertions, and every other Reading test passes. At `de8c3f8`: 40 passed.
- **Round 1's MJ1, MJ2, M1, M6, K2** → at `1e9a92a`: 4 tests fail, 47 assertions. At `671b305`: 44
  passed.
- **Round 2's B1, M2, M3, K1** → at `b2723f8`: 4 tests fail, 49 assertions. At `ec5159e`: 48 passed.
- **Round 3's B1 (the reach comes out)** → at `b957ec0`: only
  `testTheImageRuleOverridesOnlyAQuestionRoutedToVision` fails, 10 assertions. At `d324669`: 47 passed
  (54 with this seat's tests).

## Suite result

- **Swift**, in a scratch copy of `ios/` with `scripts/router_probe/` beside it, at `d324669` with
  this seat's tests: `swift test` → `Executed 490 tests, with 0 failures`. `swift test --list-tests |
  sort` equals `ios/EngineTests/test-manifest.txt` (490 lines). Without this seat's tests: 483.
- **Python**, as `make test` runs it:
  `MODEL_RANKING_REQUIRE_ARTIFACT=1 MODEL_RANKING_REQUIRE_OFFLINE=1 sandbox-exec -f scripts/offline.sb
  .venv/bin/python -m pytest -n auto` → `2079 passed, 25 skipped`. Then `module_coverage_floor.py`:
  `PASS: 45 module(s), floor 60%`. Then `coverage_floor.py --derive`: `CI will skip 83 of 2104 ... the
  budget is 83`. Also `ruff check src tests scripts`: all checks passed. `check_records.py`: PASS, no
  findings, with this record in the tree.
- **Coverage on touched code.** The range changes nothing under `src/`, so module coverage cannot move:
  total 91.93%. The Swift engine has no coverage tool in the gate. The fault injection below is the
  evidence for it.
- **Mutation kill rate (advisory):** no runner is wired. Hand-planted: 45 of 70 before this review,
  66 of 70 after, and 70 of 70 counting this seat's exactness replay (M3).

## Mocks / contract tests

- No new external integration. The tests drive the canonical tier fakes in
  `ios/EngineTests/TierStubs.swift` (`ScriptedModelRouter`, `SilentTier`, `AnsweringWordingTier`), and
  this seat's tests do too. The on-device model is measured only by the probes, which this seat did not
  run.

## Test integrity

- **Deleted or weakened to green:** none. `d324669` deletes
  `testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted` and
  `testANewImageOrTheAskersOwnIsUnmeasuredWhereverItWasRouted`. Each asserted only the override beyond
  `vision`, which #191 removed; round 3's fix list names them. Two inputs changed. "What is the capital
  of australia" became "a playlist for a long drive" (`:257`, `:451`), because a question of fact is now
  a doubt in code. The new behaviour is held at `:587`. No assertion was loosened.
- **Mirror tests:** the wave's tests assert readings and outcomes on inputs. They do not restate the
  lists. This seat's #117 test (`test_ios_client_contract.py:1638`) parses two declarations to name what
  the check must read. That is a statement about the check, not about the reading.

## Fault-injection protocol

How each fault ran: `w4tt/plant.py` in the scratchpad read the file's bytes and its sha256. It planted
one exact replacement, ran the check, and restored the bytes in a `finally`. Then it compared the
bytes and the sha256. Each step is one record in `w4tt/logs/faults-*.jsonl`. Every fault was restored
byte-identical. Swift faults went into the scratch copy: `Reading.swift` `bacb5e94...` and
`Router.swift` `259909ec...`, the same as the worktree's. Each ran `swift test --filter
'ModelRankingEngineTests\.Reading'`, and each survivor ran the whole suite. Python faults went in
place: `test_ios_client_contract.py` `ed82a97e...`, `score_w4.py` `a83017ef...`, and the three tuning
files. After every batch, `git status` showed only this seat's own files. The data plants used a live
held-out question that was held in memory and never printed or written to a file.

| # | Fault (file) | Before this review | After |
|---|---|---|---|
| F1 | `asksAFact`: ten-word bound raised to thirty (`Reading.swift`) | RED: `testNoGenuineTuningQuestionTripsASignal` | RED |
| F2 | exclusions read under the Turkish folding only | RED: `:634`, `:706` | RED |
| F3 | no suffix dropped after an apostrophe | RED: `:706` | RED |
| F4 | an act verb no longer excludes | RED: `:634` | RED |
| F5 | an image noun no longer excludes | RED: `:182` | RED |
| F6 | the Turkish stems no longer exclude | RED: `:634` | RED |
| F7 | "hangisi" a fact word again (the review's MJ2) | **survived** (483 tests) | RED: `:759` |
| F8 | "ne zaman" not read | RED: `:522` | RED |
| F9 | "hangi yil" without its letter not read | RED: `:522` | RED |
| F10 | an opener anywhere, not only first | RED: `:634` | RED |
| F11 | only the bare word "model" excludes | RED: `:634` | RED |
| F12 | something current no longer excludes | RED: `:182` | RED |
| F13 | the asker no longer excludes | RED: `:706` | RED |
| F14 | an AI or a model named no longer excludes | RED: `:634` | RED |
| F15 | the fact signal is no doubt (`Router.swift`) | RED: `:587` | RED |
| F16 | the fact signal only on the model tier | RED: `:587` | RED |
| F17 | the image rule on every surface but code again (#191) | RED: `:727`, `:611`, `:684` | RED |
| F18 | the image rule on the model tier only | RED: `:432` | RED |
| F19 | a doubt in code alone is the note (`inputReading`) | RED: `:165`, `:264`, `:288`, `:587` | RED |
| F20 | a doubt and the model's doubt only ask | RED: `:165`, `:248`, `:288`, `:587` | RED |
| F21 | small talk no longer decides alone | RED: `:165`, `:297` | RED |
| F22 | a phrase counted but its words kept | RED: `:549`, `:650` | RED |
| F23 | a phrase not counted toward the bound | **survived** (483) | RED: `:779` |
| F24 | "health" alone is small talk (the review's M1) | RED: `:650` | RED |
| F25 | the W4 small-talk words dropped | RED: `:549`, `:650` | RED |
| F26 | search words before a colon under the Turkish folding only (K2) | RED: `:663` | RED |
| F27 | a comparison before the colon is content | RED: `:663` | RED |
| F28 | a which-model question after the colon is content | RED: `:663` | RED |
| F29 | any "which" after the colon is a search (M3) | RED: `:712` | RED |
| F30 | the W4 Turkish act stems dropped | RED: `:557` | RED |
| F31 | "make" dropped from the act verbs | RED: `:557` | RED |
| F32 | the W4 role phrases dropped | RED: `:568` | RED |
| F33 | "kopyala" dropped | RED: `:568` | RED |
| F34 | K1's folding removed from `makesAnImage` | RED: `:684` | RED |
| F35 | the Turkish modifier rule removed (the review's MJ1) | **survived** (483) | RED: `:788` |
| F36 | "yap" dropped from the image stems | RED: `:577`, `:727` | RED |
| F37 | "fotograf" (no Turkish letter) dropped | **survived** (483) | RED: `:801` |
| F38 | "degistir" dropped after "arka plan" | RED: `:577` | RED |
| F39 | the verb after "arka plan" must follow at once | **survived** (483) | RED: `:806` |
| F40 | "what's" no longer an opener | **survived** (483) | RED: `:773` |
| F41 | K1's folding applied to the Turkish words too | RED: `:421` | RED |
| F42 | no small-talk phrase read | RED: `:549`, `:650` | RED |
| F43 | the image rule's outcome claims the model tier (`Router.swift`) | RED: `:432` | RED |
| F44 | fact openers under the default folding only | **survived** (483) | RED: `:768` |
| F45 | "hangi" before any noun is a question of fact | **survived** (483) | RED: `:759` |
| G1 | the M19 sets retired too (`test_ios_client_contract.py`) | RED: `:175`, `:1576` | RED |
| G2 | the M18 sets live again (#177 undone) | RED: `:175`, `:1576` | RED |
| G3 | a flagged entry left unreviewed | RED: `:1576` | RED |
| G4 | a stale reviewed entry kept | RED: `:1576` | RED |
| G5 | the tuning sets no longer clear an entry | RED: `:1576`, `test_m18_w3s_own_case_...` | RED |
| G6 | the tuning side reads the live sets | RED: `:1576` | RED |
| G7 | #117 reads no two-entry list | **survived** | RED: `:1638` |
| G8 | three-letter entries skipped | RED: `test_an_entry_matches_...`, `:1576` | RED |
| D1 | a live held-out question copied into `reading_tuning_w4.json` | **survived** | RED: `:175` |
| D2 | the same, into `scripts/router_probe/probe_questions.json` (control) | RED: `:175`, `:1576` | RED |
| D3 | the same, into `docs/research/m18-w3-runs/reading_tuning.json` | **survived** | RED: `:175` |
| S1 | a question back not counted as caught (`score_w4.py`) | **survived** (2073 passed) | RED: `test_reading_probe_scorer.py:57`, `:166` |
| S2 | a genuine search given the note counted on its surface | **survived** | RED: `:57` |
| S3 | a request given the note counted as told "not measured" | **survived** | RED: `:92` |
| S4 | the tier's own decline counted as an override | **survived** (2073 passed) | RED: `:92` |
| S5 | the bar rounded, not rounded up | **survived** | RED: `:107` |
| S6 | `--show` allowed on a held-out set | **survived** (2073 passed) | RED: `:120` |
| S7 | an unmeasured answer counted on its surface | **survived** | RED: `:57` |
| S8 | pasted content left out of not-a-search | **survived** | RED: `:57`, `:166` |
| S9 | a run that does not answer its set row for row is scored | **survived** | RED: `:130` |
| S10 | a read request given the note counted as reaching `vision` | **survived** | RED: `:92` |
| R1 | replay: the tier's own decline dropped (`ReplayProbe.swift`) | **survived** (no test runs it) | exactness replay: 5 and 2 rows differ |
| R2 | replay: the model's doubt dropped | **survived** | exactness replay: 14, 5 and 6 rows differ |
| R3 | replay: the outcome rebuilt on the wording tier | **survived** | exactness replay: 14, 5 and 6 rows differ |
| R4 | replay: a wording-tier run replayed, not refused | **survived** | exactness replay: the run is not refused |

A `:NNN` with no file is `ios/EngineTests/ReadingTests.swift`. Before this review the scorer faults
were checked against the whole Python suite, inside the offline profile. Three of them (S1, S4, S6)
gave `2073 passed`. No file in `tests/`, `scripts/`, `src/` or `ios/` names `score_w4`, so the other
seven pass it for the same reason. The exactness replay is `w4tt/replaycheck.sh`, and no committed
test runs it. It replays `final-notasearch_heldout_m19-1`, `final-image_heldout_m19-1` and
`v0-image_tuning_w4-1` through the copy and compares them with the committed `review3-*` runs. Then it
offers it a wording-tier run, which the harness must refuse. Unplanted, the replays give 0 rows
different and the wording run is refused.

**Checks of the record's claims, the same way (not faults):** V1 removes `galeri` and `yükleme`
from `modifierHeadsTurkish`, and V2 removes `chatbot`, `gemini` and `deepseek` from the exclusions.
Replayed and re-run on both tiers, each changes 0 rows of the held-out runs. That is what
`_AFTER_MEASURE` says.

**No on-device probe was run.** No `ReadingProbe`, no model call, no installer, `launchctl`, `simctl`
or `xcodebuild`, nothing that opens an app or a browser, no `os.abort()`, and no network but `gh issue
view`. The wording-tier runs used a scratch harness, `W4TSignalsDump.swift`, in the scratch copy only.
It does what `PROBE_TIER=wording` does: `SimilarityRouter`, then `TieredRouter(model: nil)`.

## The record's numbers

Scored with `score_w4.py`, counts only, never `--show` on a held-out set:
- **§2 baseline:** model 18 and 21 of 50 caught. Knowledge 1 and 3. Genuine searches on their surface
  30 and 28. Wording 8, 0 and 14 in both runs. By class: 0 / 1 and 0 / 3; 0 / 3 and 0 / 5; 0 / 9 and
  0 / 8; 0 / 5 and 1 / 4. Requests to make an image: 2 and 1 told "not measured", with 12 / 6 / 0 and
  12 / 7 / 0 of the misses on `vision` / `web-dev` / other. Wording: 14, with misses 0 / 3 / 3.
  Requests to read an image reaching `vision`: 10 and 9, wording 4. Questions that only mention an
  image, overridden: 0. **The bars:** 1 + ⌈2/3 × 19⌉ = 14 for knowledge and for the model tier's
  image measure; 14 + ⌈2/3 × 6⌉ = 18; 28 − 2 = 26; 14 − 2 = 12; 9 − 1 = 8; 4 − 1 = 3. All as recorded.
- **§3 variants:** reference 69 and 67, 1 and 2, asked 14 and 7, on surface 133 and 131. (a) 76, 2,
  17, 128. (b) 97 and 94, 18 and 18, 15 and 8, 133 and 131. (c) 93, 18, 17, 129. Image: reference 24
  and 23; (a) 29 and 28; (b) 35 / 15 / 7; (c) 32 and 31; wording 25 to 33. All as recorded.
- **§4 at `de8c3f8`:** 0 noted; 2 and 1 asked; 25 and 27 caught; 6 and 6 knowledge questions; 8 and 8
  image requests, wording 18 and 18; 32 and 29 on surface, wording 14; 10 and 9 reaching `vision`,
  wording 4; 0 overridden. The class split and the misses' surfaces (9 on `vision`, 3 on `web-dev`)
  are as recorded. The `final-*` runs are fresh model runs: 40 of 100 rows differ from `base-*` in the
  model's own answers.
- **§6 and D-184, the code that ships:** 24 and 26 caught; 5 and 5 knowledge questions; 1 and 0
  asked; image requests 4 and 3, wording 14; tuning 96 and 93, 17 of 22, image 27 and 26, wording 25.
  All as recorded. I replayed `final-*` and `v0-*` through a scratch copy of `d324669` with the wave's
  `ReplayProbe.swift`: 0 rows differ from `review3-*` across 8 files. A fresh wording-tier run of
  `d324669` differs from `review3w-*` in 0 rows on all three sets. It is also identical to `basew-*`:
  on these sets the shipped image rule changes no wording-tier row (K1).

## BLOCKING

- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `tests/unit/test_ios_client_contract.py:175-205` (the leak gate). **The held-out leak gate did
  not read the tuning sets this wave tuned on.** Those are `docs/research/m19-w4-runs/reading_tuning_w4.json`,
  `image_tuning_w4.json` and `docs/research/m18-w3-runs/reading_tuning.json`; the plan names them
  (`m19-wave-4-plan.md:61-65`). A live held-out question planted in either reading set passed every
  test (D1, D3), while the same plant in `scripts/router_probe/` was caught (D2). This is #119's class,
  moved to a new folder. There is no live leak: measured, none of the 150 held-out questions is in any
  of them. **Fixed in this seat's uncommitted change:** `_research_tuning_sets()` and
  `RESEARCH_TUNING_SET` (`:1656-1668`) read any set in `docs/research/*/` whose name has no run prefix.
  The gate now reads them (`:202-203`), and `:1671` holds the list. D1 and D3 are then RED. Commit it,
  or refuse it with a reason.
- **M2** `tests/unit/test_ios_client_contract.py:1621` (`STRING_LIST`); D-183 clause 5; D-184 clause 2.
  **#117's check read lists of two or more literals, so five entries this wave added were outside
  it:** `smallTalkPhrases`, and "who", "when", "where" and "whats" in `factOpeners`. A word from a live
  held-out set put into a one-entry list would not be flagged. Also, no test held that two-entry lists
  are read (G7), and `factOpeners` is made of them. There is no live miss: measured, reading one-entry
  lists flags nothing new and clears nothing. **Fixed in this seat's uncommitted change:** the bound is
  now one, with its comment. The new test at `:1638` fails on the wave's bound (G9) and on a bound of
  three (G7). Commit it, or refuse it with a reason.
- **M3** `scripts/router_probe/ReplayProbe.swift`; `scripts/router_probe/ReadingProbe.swift:43-52` (the
  wording mode). **The replay harness is held by no committed check, and every number of record §3 for
  code-only variants and all of §6 rest on it.** Four faults pass every test (R1 to R4): a decline
  dropped, the model's doubt dropped, the outcome rebuilt on another tier, and a wording run replayed.
  Each was caught only by an exactness replay run by hand: the record's ("checked on 306 rows"), round
  3's, and this seat's. The wording mode is in the same position. A suite test cannot reach either one:
  both sit outside the package's test target. **Fix:** file an issue for a check that replays one
  committed run and compares it row for row, as `w4tt/replaycheck.sh` does. Or move the rebuild of an
  outcome from a recorded row into `EngineTests/`, where the harness and a test can share it.
- **M4** `docs/decisions.md:4184` (D-184's heading). **D-184's title still says "the image rule
  reaches every surface but code".** Clause 3 of the same ADR, the code (`Router.swift:711`) and #191
  say it stays on `vision`. **Fix:** retitle, for example "... a question of fact is a doubt, and the
  image rule reads more Turkish forms on `vision`".
- **M5** `docs/prd.md:532` (REQ-ASK-005); `docs/plans/m19-plan.md:234-243` (the W4 amendment).
  **Two records give `de8c3f8`'s figures as if they were the shipped code's.** REQ-ASK-005 says "25 and
  27 of 50 ... knowledge questions 6 and 6 of 20 ... 2 and 1 of 40 were asked". The code that ships
  gives 24 and 26, 5 and 5, and 1 and 0 asked (record §6). This seat's replay through `d324669`
  matches §6 exactly. The plan's amendment says "#113's wording-tier bar was met" and stops there.
  After #191 the bar is missed, 14 of 20 against 18. D-184 and REQ-IMG-003 already say so. **Fix:**
  give the shipped figures, or name `de8c3f8` beside the ones given, and add the wording-tier miss to
  the amendment.
- **M6** `docs/decisions.md` D-184 clause 2; `ios/ModelRanking/Engine/Reading.swift:191-210`. **The
  clause names two entries that no tuning row holds whole while the app matches them whole (`nerede`,
  `öner`). Measured, five more were added before the measure:** `ben`, `hafta` and `şimdi` in
  `factExclusions`, and "far" and "high" in `factOpeners` ("how far", "how high"). Each is in a tuning
  row only at a word's start (`benim`, `haftalik`, `şimdiden`, `farklarını`, `highest`), which is how #117's check
  matches. None is whole in a held-out row (counts only), so none changed a measured row. **Fix:** name
  them in clause 2, or say only "at a word's start". Add them to #186, which holds this matching
  class.

## K.9 candidates spotted outside this wave's scope

- **K1** `docs/research/m19-w4-question-reading-probe.md` §2, §4, §6; `score_w4.py:48`. **On the
  wording tier, "told not measured" mostly counts the manual fallback, not a reading.** Of the 14
  held-out requests to make an image told "not measured" at the baseline and in what ships, 10 are rows
  no tier answered: the manual outcome is unmeasured. The other 4 are the wording tier's own decline.
  On the image tuning set it is 18 of 25 and 7. At `d324669` the image rule overrides 0 wording-tier
  rows on either set. So #113's wording bar (18) credits a fallback as if it were a read. The record's
  counts are right; what the measure means is the point for #113's next round. **Fix there:** score the
  rule's own catches (`declined == "false"`) apart from the fallback.

## Tests added/extended this review

Uncommitted in this seat's worktree, for the author to commit unedited with this verdict:

- `ios/EngineTests/ReadingTests.swift:752-809`, class `ReadingSecondRoundFaultTests` (7 tests, each in
  `ios/EngineTests/test-manifest.txt`). Each line was made up here. Its highest similarity ratio to any
  held-out question is 0.57 (`difflib`, against all 150).
  - `:759` `testWhichOneAndWhichBeforeANounOpenNoQuestionOfFact`: D-184 clause 1 and the review's MJ2.
    Kills F7 and F45.
  - `:768` `testATurkishQuestionOfFactInCapitalsIsRead`: REQ-ASK-005, the Turkish folding. Kills F44.
  - `:773` `testWhatsWithItsApostropheOpensAQuestionOfFact`: D-184 clause 1. Kills F40.
  - `:779` `testAPhraseOfSmallTalkCountsAsOneWord`: the review's M1. Kills F23.
  - `:788` `testATurkishImageThatModifiesANounIsNoImageToMake`: REQ-IMG-003 and the review's MJ1, on
    `vision` too. Kills F35.
  - `:801` `testAPhotoTypedWithoutItsTurkishLetterIsAnImage`: D-184 clause 3. Kills F37.
  - `:806` `testABackgroundRemovedAWordLaterIsMade`: REQ-IMG-003. Kills F39.
- `tests/unit/test_reading_probe_scorer.py` (new, 6 tests; cites REQ-ASK-005, REQ-IMG-003, D-184). It
  covers the scorer's measures on made-up rows (`:57`, `:92`), the plan's bar rule (`:107`), the
  `--show` refusal (`:120`) and the row-for-row refusal (`:130`). `:166` checks the record's held-out
  figures against the committed runs, and each bar against the baseline's lower run. It reads the
  held-out sets for counts only, and no question is written into it. It kills S1 to S10.
- `tests/unit/test_ios_client_contract.py`: `STRING_LIST` reads one-entry lists (`:1621`), and
  `test_every_fact_opener_and_small_talk_phrase_is_read_by_the_held_out_check` is added (`:1638`) (M2;
  kills G7 and G9). The leak gate reads the research tuning sets (`:202-203`), through
  `_research_tuning_sets()`, and `test_the_tuning_sets_kept_beside_their_runs_are_read_by_the_leak_gate`
  is added (`:1671`) (M1; kills D1 and D3). The Turkish letters are escaped (V4C-79).

*Filled by: Tester seat (independent) · Date: 2026-10-07 · Commit range: `3426ff3..d324669`*
