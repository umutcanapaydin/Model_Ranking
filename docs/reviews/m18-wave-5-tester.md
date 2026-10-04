---
record_type: review
id: m18-wave-5-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# Wave 5 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records.
It is not one of the wave's two Code-Reviewer seats.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `487dfc2..5cf9cb2`, W5's own change being `git diff 487dfc2 5cf9cb2`: 49 files,
+2142 / -178. `487dfc2` is the head of M18-W4, which W5 merged three times (`10d9e50`, `9cc26a2`,
`5cf9cb2`); W4 has its own seats. `git log --first-parent e32271a^..5cf9cb2` is 23 commits: 20 of
W5's own and those 3 merges.
1. The range holds the plan (`e32271a`), the P1 records, four red-then-fix pairs, round 1 of the
   code review (`be2434f`, BLOCKING), its red-then-fix pair (`3c584a5` → `a140265`) and round 2
   (`a52c76d`, PASS-WITH-MINORS).
2. Round 2's red-then-fix pair (`9473872` → `74e2bd1`) and the last merge (`5cf9cb2`) came after
   both reviews, so this seat is the only one that has tested them.

**Risk tier:** HIGH (`docs/plans/m18-wave-5-plan.md:11-13`; `docs/plans/m18-plan.md:106` says MED).
The diff touches `src/app/adapter/main.py` (a docstring) and the D-126 gates.
**Code-Reviewer verdict:** PASS-WITH-MINORS (`docs/reviews/m18-wave-5-review.md`, round 2, at
`a52c76d`). By D-172 there is no security seat on the wave. The fault injection below is the HIGH
tier's owed one.
**Model routing (HIGH, advisory):**
- Author family: Claude (every W5 commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from `.claude/agents/Tester.md`, `.agents/rules/practices.md` and
  `permission-matrix.md` §11, all read from `487dfc2` with `git show`. (`docs/permission-matrix.md`
  does not exist at the base; the matrix is `permission-matrix.md` at the root.) It then read both
  plans, D-174 and the D-154, D-156 and D-157 notes, the wave's issues, both review rounds and the
  diff. It has no memory of any authoring or reviewing session.

**Base-pinned policy:** `git diff --stat 487dfc2 5cf9cb2 -- .claude .agents permission-matrix.md
.github epb.html or.md Dockerfile fly.toml` is empty. `AGENTS.md` changes in §1 and §4, as P1 plans
(#80, #52). The §4 line (seats run one after another, each in its own worktree) restates D-174. It
asks nothing of this seat that the base rules and its brief did not already ask.

## Verdict
PASS-WITH-MINORS

**Nothing blocks.** I found the following:
1. Every acceptance check in the wave plan (P1 to P3) has a citing test that passes.
2. Each red commit fails where it should, and each fix passes.
3. No touched module lost coverage.
4. `make check-fast`, `make wave-check-all` and `make client-decls` all pass.
5. Every behaviour the wave promises is right at `5cf9cb2` wherever I probed it.

**Ten MINORs (T1 to T10).** Eight are faults that stayed green. T2 is a claim the SDK's own header
contradicts. T6 is a probe that a gate passed. Each comes with a test:
1. Each test was written in a scratch copy of `5cf9cb2` and is green there.
2. Each was shown red on its fault in that copy. T6's is red on `5cf9cb2` itself, and green with
   its one-line fix.
3. The author lands them in this wave, or files them.

The ten:
- **T1:** #59's tearDown check is held by nothing. Remove the assertion that fails a test whose
  requests the tripwire recorded, and all 367 Swift tests and all 1631 Python tests pass.
- **T2:** round 2's M11 fix for background sessions (`74e2bd1`, after both reviews) cannot work.
  A background session never asks custom protocol classes; the SDK header says so. The new test
  checks only the configuration's list.
- **T3:** #51's "the gate tests itself before it checks the app" is not held. With `self_test()`
  unwired from `main()`, every test and `make client-decls` pass.
- **T4:** the `_code` scanner's triple-quoted strings are held by nothing. It also has no
  fail-closed. An extended regex literal holding `/*` (`#/a/*b/#`, which builds) erases the rest of
  `Router.swift`, and the D-168 pin passes.
- **T5:** #82's "`wave-check-all` fails on a planned wave with no close" is held only on
  `missing_closes`. With its result dropped from `main()`'s exit, every test passes.
- **T6:** round 2's M9 is half closed. With `### W1` parsing, a `### **W2** — two` or
  `##### W2` heading is skipped, and nothing is reported missing.
- **T7:** #83's rule reads the whole footprint, and nothing holds that. Read only to the first
  newline, a `src/app/clients` path on the footprint's second line passes as MED. The real M18-W4
  close has its clients path on line 2.
- **T8:** #92 N2's carried date is held only by a timestamp. Truncating to ten characters, the rule
  MINOR-2 retired, passes it. And only +inf is tested; a `score == inf` check passes.
- **T9:** #92 T2 is half closed. The counts are held, but "a scratch copy the script makes, never
  the artifact" is not: `calibrate_board.main` and `survey_boards.measure` storing into the
  operator's database pass every test.
- **T10:** #92 T4 is half closed. The M17 closure Tester's E2 (`min_quality` fixed at 0.0) still
  passes every test.

**What was run.**
- `make check-fast`: rc 0. `make wave-check-all`: rc 0. `make client-decls`: rc 0.
- Every red commit in the range was replayed on `git archive` copies, with a scratch HOME.
- **91 faults were injected**: 87 in the worktree, and 4 in a scratch copy (S1, S3, S11 and S15,
  whose tests would otherwise have reached `example.invalid`).
  1. 74 were killed and 6 are equivalent (N1, N2, N3).
  2. 11 survived. They are the subject of T1, T3, T4, T5, T7, T8, T9 and T10.
- **Advisory kill rate: 74 of 85 non-equivalent faults, 87.1 %.** With the proposed tests added,
  85 of 85.

## Acceptance-criterion coverage (REQUIRED)

Every test named below is GREEN at `5cf9cb2`. Line numbers are at `5cf9cb2`. Fault ids are
defined under "Fault injection". W5 adds no REQ-ID. Its milestone criterion is "Every gate gap
filed is closed with a gate shown red, and the records drift is fixed" (`m18-plan.md:34`). The rows
below are the wave plan's checks (`m18-wave-5-plan.md:25-27`).

| criterion (plan phase, issue) | citing test (file:line) | entry | faults it kills | status |
|---|---|---|---|---|
| P1 #68: the REQ-APP-002/003/005 rows describe the combined path and cite its tests | `docs/prd.md:417`, `:418`, `:420`; `check_records.py` PASS | records | n/a | MET. Each row restates D-168's combined list and names what is still missing (#60, #67, #69). Its citations resolve (below) |
| P1 #33: `REQ-API-010` names one requirement; every id cited in tests has a PRD row; D-154 and D-157 carry their ruling's status | `prd.md:421` (REQ-API-010), `:470` (REQ-API-011); `decisions.md:2367`, `:2636` | records | n/a | MET. All 112 REQ ids cited under `tests/` and `ios/EngineTests/` have a PRD row (scripted at `5cf9cb2`). The two status lines are dated; the bodies are untouched |
| P1 #80: `docs/architecture.md` and `AGENTS.md` §1 describe the product after M18-W4 | `architecture.md:3-6`; `AGENTS.md` §1 | records | n/a | MET (read; round 2 checked seven of its numbers against the code) |
| P1 #52, #84: review seats run one after another, each in its own worktree | `AGENTS.md:77`; D-174 (`decisions.md:3469`) | records | n/a | MET |
| P2 #59: a Swift test that opens a connection fails the suite | `OfflineTestCase.swift:134`, `:143`, `:153`; `test_swift_tests_offline.py:18`, `:37`, `:44`, `:53`, `:60` | real path: the tripwire inside `swift test` | S1–S7, S11, S14, S15, P1–P5 | GREEN. S8 survives: T1. Background sessions: T2. S9, S10, S12, S13 are equivalent: N1 |
| P2 #51: a committed fixture shows `client-decls` refusing `URLSession` and `FileManager` outside their files | `test_client_decl_gate.py:57` (compiled), `:33` (canned) | real path: `swiftc -dump-ast` on `scripts/client_decl_fixtures/` | D1–D4, D6, D7 | GREEN. D5 survives: T3 |
| P2 #58: the same fixture refuses a URL decoded outside `EngineClient.swift`; the text gate refuses a URL as a type argument | `test_client_decl_gate.py:47`, `:70`, `:57`; `test_router_hints.py:600`, and the client text gate `:379` | real path: both D-126 gates | D1–D4, D7, D9, D10 (compiler gate only), TG1, TG2 | GREEN. D10 reproduces round 2's M7 on the text gate, filed on #107: N4 |
| P2 #58: `GapRegisterStore` refuses an address that is not a file | `FrontDoorTests.swift:749` | real path: the store, under the tripwire | FD1 | GREEN. FD2 is equivalent: N2 |
| P2 #98: a pin no longer passes on a line wrapped in `/* */` | `test_router_hints.py:591`, `:608`, `:619`; `test_engine_address.py:73` | unit: `_code`; and the pins that read Swift through it | C1–C4, C7, C8, R1 | GREEN. C5 and R2 survive: T4. C6 is equivalent: N3 |
| P3 #92 T1: a run-time watcher on every served reader | `test_readonly_uri.py:177` | real path: `/v1/boards`, `/v1/categories`, `/v1/recommendations`, the boot check, `fingerprint_of`, `_served_without` | W1–W9, W11 (the M17 closure's B7), W12 | GREEN. W10 (`Carry.restore`) is killed by `test_carry_forward.py:315` |
| P3 #92 T2: each named writer opens as often as it may, and only its scratch copy | `test_readonly_uri.py:158` | a scan of the tree | B16, B13 (by `test_survey_floors.py:121`) | GREEN for the counts. B11 and B12 survive: T9 |
| P3 #92 T3: every registered board's metric has a direction | `test_board_standings.py:648` | unit: the registries | M3 (C3), M4 (C4) | GREEN. M5 is killed by the suite, not by this test: N5 |
| P3 #92 T4: `floor_shipped` is the shipped rule | `test_calibrate_board.py:112` | real path: `main()` on a patched fetch | E1 | GREEN. E2 survives: T10 |
| P3 #92 N1: every `simctl` call names its device | `test_engine_service.py:523` | a scan of `ios/app.sh` | A1, A2 | GREEN |
| P3 #92 N2: carried rows meet the store's rules | `test_carry_forward.py:369` | unit: `Carry.restore` on a built artifact | CR1, CR2, CR4, CR6, CR7 | GREEN. CR3 and CR5 survive: T8 |
| P3 #92 N3: a missing score is a SourceError; so is a schema refusal | `test_stored_scores_are_bounded.py:94`, `:101` | unit: `_store_scores` | I1, I2 | GREEN |
| P3 #82: `wave-check-all` fails on a planned wave with no close | `test_wave_check_m18_rules.py:48`, `:54`, `:62`, `:102`, `:113`, `:142` | unit: `missing_closes` | MC1–MC7, MC9 | GREEN. MC8 survives: T5. Heading spellings: T6 |
| P3 #83: `wave-check` refuses a close that is not HIGH when its diff touches `src/app/clients/` | `test_wave_check_m18_rules.py:91`, `:97`, `:125`, `:157` | real path: `wave_check.py` as a subprocess | H1–H5, H7 | GREEN. H6 survives: T7. A MED close naming HIGH: N6 |
| P4 #60, #85 | n/a | n/a | n/a | Moved to W6 by `m18-plan.md:204-206`. Not in this wave |

**The PRD's evidence pointers.**
1. The PRD lines W5 adds or changes carry 155 `file:line` citations. I resolved each at `5cf9cb2`.
2. 148 land on a test or definition line.
3. The other 7 are deliberate pointers to documents or a source line:
   `docs/plans/m7-plan.md:166`, `docs/coverage-by-req.md:39`, `m10-wave-4-close.md:37`,
   `m14-wave-1-close.md:32`, `:46`, `m16-plan.md:53` and `ContentView.swift:64` (the `unlimited`
   budget).
4. The 17 citations `5cf9cb2` re-pointed are among the 148.

## Red→green on reported symptoms

How the replay was run:
- Each commit was extracted with `git archive` into a scratch tree, with the served artifact
  copied in, and run with this worktree's venv.
- `PYTHONPATH` pointed at that tree's `src`, and HOME was a scratch folder.
- The Python column runs the test files the red commit changed. The Swift column runs the classes it
  changed (`swift test --filter`), on the same copy.

| pair | Python: red / fix | Swift: red / fix | notes |
|---|---|---|---|
| `5a3b1be` → `6efede4` | 2 of 5 FAIL / 5 PASS | `OfflineGuardTests`: 1 test, 2 failures / 2 tests PASS | The Swift red lists `.default`'s and `.ephemeral`'s protocols with no tripwire |
| `93de739` → `90ead9d` | 2 of 3 FAIL / 3 PASS | `GapRegisterHardeningTests`: 1 of 7 FAIL / 7 PASS | The tripwire recorded `https://example.invalid/gap-register.json`. That is #58's read, caught without leaving the machine |
| `90ead9d` → `1d2a455` | whole suite: 1 failed, 1588 passed / 1589 passed | n/a | `test_the_gap_register_stays_on_the_device`: the register's comment spelled the read the text gate counts |
| `678a830` → `6894083` | 1 of 16 FAIL / 16 PASS | n/a | #98's block-comment case |
| `ca8b785` → `f21f658` | 6 of 130 FAIL / 130 PASS | n/a | N2, N3, three #82 tests and one #83 test are red. The T1–T4 and N1 tests pass on red: they pin code that was already right. Faults W1–W12, B16, M3, M4, E1, A1 and A2 show that each can fail |
| `3c584a5` → `a140265` | 6 of 70 FAIL / 70 PASS | `OfflineGuardTests`: 1 of 3 FAIL / 3 PASS | The stub-declined request reached the real stack (loopback port 9): `[]` against `["http://127.0.0.1:9/declined"]` |
| `9473872` → `74e2bd1` | 3 of 28 FAIL / 28 PASS | none changed | M8, M9 and M10 are red. M11's alias test passes on red ("held from now on", as the commit says). The background exchange has no red test: T2 |

**Weakened or deleted tests.** I read every line the range removes under `tests/` and
`ios/EngineTests/`.
1. Fourteen Swift files change `XCTestCase` to `OfflineTestCase` and nothing else.
2. `test_engine_address.py:80`: the regex stripper for `/* */` is replaced by `_code`, which strips
   the same and nested comments too. That is stronger, not weaker.
3. `test_swift_test_manifest.py`'s class pattern also reads `OfflineTestCase` subclasses. Without
   that, the manifest check would see no test classes.
4. The remaining removed lines are docstrings: REQ-API-010 → 011 (#33), the retired budget picker,
   and the stale "1400 floor".

No test was skipped or weakened. The one new skip is the compiled fixture CI cannot run, and the skip
budget records it (75 → 76).

## Suite result
- **`make check-fast` at `5cf9cb2`: PASS, rc 0, in 52 s.** This seat's guards were in front (see
  Safety).
  1. lint, typecheck and records: PASS.
  2. test: **1631 passed, 25 skipped**. Total coverage 91.77 %. `coverage-floor`: PASS, 42 modules.
  3. client-decls: PASS, 15 files in 4 configurations, after its self-test.
  4. swift-test (parallel): PASS, 367 tests, exactly the manifest.
- **`make wave-check-all`: PASS, rc 0.** 49 records validated, 20 pre-migration records out of
  scope.
- **`make client-decls`: PASS, rc 0.**
- **Coverage on touched code** (permission-matrix §11).
  1. Method: `pytest tests -n auto --cov=src/app --cov=scripts --cov-branch`, with
    `MODEL_RANKING_REQUIRE_ARTIFACT=1` and a scratch HOME.
  2. It ran on `git archive` copies of `487dfc2` and `5cf9cb2`, each with the same artifact (sha256
    `5c6977a9c67c…`).
  3. Base: 1600 passed, 25 skipped. Head: 1631 passed, 25 skipped.
  4. The three scripts were measured a second time with subprocess coverage on
    (`COVERAGE_PROCESS_START`). The #83 tests run `wave_check.py` as a subprocess, which in-process
    measurement cannot see.

| module | base `487dfc2` | head `5cf9cb2` | change |
|---|---|---|---|
| `src/app/adapter/main.py` | 98.04 % (399 st / 8 miss; 110 br / 2) | 98.04 % (399 / 8; 110 / 2) | 0 (a docstring) |
| `src/app/workflows/build.py` | 95.06 % (427 / 19; 120 / 8) | 95.32 % (447 / 19; 130 / 8) | +0.26 |
| `src/app/workflows/ingest.py` | 96.30 % (121 / 4; 14 / 1) | 97.78 % (121 / 2; 14 / 1) | +1.48 |
| `scripts/client_decl_gate.py` | 0.00 % (118 / 118) | 58.94 % (141 / 52; 66 / 33) | +58.94 |
| `scripts/wave_check.py` (with subprocesses) | 69.21 % (232 / 63; 148 / 54) | 69.64 % (240 / 64; 152 / 55) | +0.43 |
| `scripts/wave_check_all.py` | 85.33 % (55 / 6; 20 / 5) | 88.71 % (88 / 8; 36 / 6) | +3.38 |
| `src/app` total | 91.70 % | 91.77 % | +0.07 |

No touched module dropped. In-process only, `wave_check.py` reads 63.16 → 61.99 %. That is the
measurement, not the tests: its eight new lines run in the subprocesses its tests start.

## Mocks / contract tests
- **The Swift tripwire (#59)** is a test-only guard, not a fake of an upstream.
  1. `StubProtocol` (`EngineClientTests.swift`) stays the canonical stub. The setter exchange puts
     the tripwire after it, and S6 shows that order matters: with the tripwire first, the stub
     tests fail (25 failures).
  2. `DecliningStub` (`OfflineTestCase.swift:169`) is a fault-injection double for one case, a
     stub that answers nothing. I do not count it as a parallel mock.
- **The compiler gate's canned AST (#51, #58).** `DECODED_URL` and `DECODED_OPTIONAL_URL`
  (`test_client_decl_gate.py:25`, `:63`) stand in for the compiler's output.
  1. Their contract test is the compiled self-test (`:57`). It compiles the same two shapes,
     `JSONDecoder().decode([URL].self, …)` and a synthesised `decodeIfPresent` for `URL?`, and
     expects both refused.
  2. It runs wherever Xcode is. CI skips it, and the skip budget says so.
- **No new external integration.**

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T1** `ios/EngineTests/OfflineTestCase.swift:128`; `tests/unit/test_swift_tests_offline.py:44`. **#59's tearDown check, the one that fails a test which reached for the network, is held by nothing.**
   1. The plan's check is "A Swift test that opens a connection fails the suite". The tripwire's
      catching is held: S1–S7, S14 and S15 are killed by `OfflineGuardTests`.
   2. The last link is not held: the base's tearDown turning a recorded request into a failure.
      Fault S8 removes `XCTAssertEqual(attempts, [], …)`. `OfflineGuardTests` passed (10 of 10), and
      so did the whole Swift suite and all 1631 Python tests.
   3. `test_the_base_checks_every_test_and_calls_through` asks only for `OfflineGuard` in the
      tearDown body, and the `drain()` call that S8 leaves behind satisfies it.
   4. Swift cannot hold this in this project. The way to expect a failure is `XCTExpectFailure`,
      and `scripts/swift_xunit_gate.py:31` refuses it because the parallel run reports it as a
      pass. I wrote it that way first, and the project's own gate refused it.
   5. **The fix:** `test_the_base_fails_a_test_whose_requests_it_recorded`, below. It asserts that
      the tearDown asserts the drained list is empty. It kills S8.
- **T2** `ios/EngineTests/OfflineTestCase.swift:8-10`, `:62`, `:92-97`, `:136-137`. **Round 2's M11 fix for background sessions cannot work. Its test checks only a list that a background session never reads.**
   1. `74e2bd1` (after both reviews) exchanges `backgroundSessionConfigurationWithIdentifier:`, so a
      background configuration lists the tripwire first. `testEverySessionConfigurationAsksTheTripwireFirst`
      asserts that list.
   2. The SDK's own header says that list is not used:
      `MacOSX26.5.sdk/…/Foundation.framework/Headers/NSURLSession.h`, on `protocolClasses`:
      "Custom NSURLProtocol subclasses are not available to background sessions."
   3. Round 2 said the same: "Background sessions run out of process and ignore custom protocol
      classes, so no exchange can catch them. Only a source check can."
   4. The header (`:8-10`) now leaves background sessions off its "Not caught" list. The commit
      message says "the tripwire also covers background configurations".
   5. I did not run a background session in a test process. It runs out of process, and this seat
      runs nothing that might crash a process on the owner's Mac. The evidence is the SDK header.
   6. Nothing in the target uses one today, so nothing is exposed.
   7. **The fix:** `test_no_swift_source_builds_a_background_session`, below. It is the source check
      round 2 asked for, over `ios/EngineTests/` and the app sources, with the base exempt. The
      proposal fault BG adds one background configuration to a test file, and the check goes red.
      Also add background sessions to the header's "Not caught" list, or drop the exchange.
- **T3** `scripts/client_decl_gate.py:353`; `tests/unit/test_client_decl_gate.py`. **"`make client-decls` runs the same fixture before it checks the app" is held by nothing.**
   1. That is the reason the test file's docstring gives for the self-test: "so the gate cannot
      pass the app while it has stopped refusing" (#51).
   2. Fault D5 sets `broken = None` in `main()`. All 17 gate tests, the whole suite and
      `client_decl_gate.py` itself passed (rc 0).
   3. The tests call `gate.self_test()` directly. This is the same shape as `review_seat_problems`
      unwired from `main()`, which `test_review_seat_gate.py:142` records as a past finding.
   4. **The fix:** `test_make_client_decls_fails_when_its_self_test_does`, below. It patches
      `self_test` to report a miss and asserts `main() == 1`. A failed self-test returns before
      anything compiles, so the test also runs on CI. It kills D5.
- **T4** `tests/unit/test_router_hints.py:41`, `:79-111`. **The `_code` scanner's triple-quoted strings are held by nothing, and the scanner has no fail-closed: an extended regex literal holding `/*` erases the rest of a file.**
   1. Fault C5 reads `"""` as three single quotes (`multi = False`). The whole suite passed. Under
      it, a `/*` on a later line of a multi-line string opens a comment that runs to the end of the
      file.
   2. Fault R2 appends `func w5tPattern() -> Regex<Substring> { #/a/*b/# }` to `Router.swift`,
      above an extension that assigns `copy.refinements = extra`.
      1. `swift build` rc 0.
      2. `test_only_the_model_output_boundary_builds_an_outcome_with_refinements` passed, and so
         did the whole suite.
      3. Control R1, the same extension with no regex literal above it: the pin fails.
   3. That pin holds D-168 clause 4, the one place a refinement is checked.
   4. Round 2's M8 asked for three fixes. `74e2bd1` did the first two: raw strings and
      interpolation. It did not do the third: "Fail closed. If the scan ends inside a block comment,
      raise. Swift cannot compile an unclosed `/*`, so ending inside one means the scanner misread
      the file."
   5. **The fix:** the three-line raise at the end of `_code`, and two tests, below. With the raise,
      the whole suite stays green: no Swift file the pins read ends inside a comment. Under R2 the
      D-168 pin then fails ("a block comment never closes"). Under C5, both the new test and the
      raise fail.
- **T5** `scripts/wave_check_all.py:166`, `:172`; `tests/unit/test_wave_check_m18_rules.py`. **#82's check is that `wave-check-all` fails, and that is held only on `missing_closes`.**
   1. Fault MC8 makes the exit `if failed or dodged:`. The missing close is still printed, and the
      script exits 0. All 10 rule tests and the whole suite passed.
   2. Every #82 test calls `missing_closes(root)`. None runs `main()`, although
      `test_wave_check_versions.py:65` shows how: `ROOT` patched to a scratch tree with a stub
      `wave_check.py`.
   3. **The fix:** `test_wave_check_all_itself_fails_on_a_planned_wave_with_no_close`, below. It
      kills MC8.
- **T6** `scripts/wave_check_all.py:63`, `:66`. **Round 2's M9 is half closed: a wave heading in a spelling `LOOKS_LIKE_A_WAVE` does not know is skipped when another heading parses.**
   1. These are probes on scratch trees, each a closed M19 with `### W1 — one` closed and a second
      heading:
      1. `### **W2** — two` gives 0 findings;
      2. `##### W2 — two` gives 0 findings;
      3. `### W2 — (dropped frames) fix` gives 0 findings: `\(dropped\b` excuses it;
      4. `### Wave 2: two`, `#### M19-W2 — two` and `### W2 — two` are each reported, as designed.
   2. Round 2's own probe 3 used bold headings on both waves, so the fail-closed branch fired. With
      one wave in plain spelling, the bold one is silent.
   3. Round 2's fix 2 was "Count a heading that names a wave in any spelling (`W\d|Wave\b`). One
      that does not parse is a finding, even when its neighbours parse."
   4. **The fix:** `LOOKS_LIKE_A_WAVE = re.compile(r"^#{2,6}\s*[*_]*\s*(?:M\d+-)?(?:W\d|Wave\b).*$",
      re.M)`, a one-line change, and
      `test_a_bold_or_deep_wave_heading_is_reported_when_another_one_parses`, below.
      1. The test is red at `5cf9cb2` and green with the change.
      2. I graded every real plan from M1 to M18 with both versions, M18 as if closed: 18 findings
         each, the same 18. The change adds no false finding.
- **T7** `scripts/wave_check.py:361-363`. **#83's rule reads the footprint up to the next field, and nothing holds that.**
   1. Fault H6 reads `Touched:` to its first newline only. All 10 rule tests and the whole suite
      passed.
   2. Every test builds a one-line footprint (`_record`, `test_wave_check_m18_rules.py:68-72`).
      Real footprints run over several lines. The M18-W4 close names `src/app/clients/protocols.py`
      on its second line (`docs/plans/m18-wave-4-close.md:80`).
   3. Under H6, a MED close with that footprint passes the rule.
   4. **The fix:** `test_the_whole_footprint_is_read_not_its_first_line`, below. It kills H6.
- **T8** `src/app/workflows/build.py:382`, `:387`; `tests/unit/test_carry_forward.py:369`. **#92 N2's carried date is held only by a timestamp, and its finite check only by +inf.**
   1. Fault CR3 truncates a carried `run_date` to ten characters without validating it. That is the
      rule the M17 closure's MINOR-2 retired, which turned `<script>alert(1)</script>` into
      `<script>al`. The test carries `2026-09-01T12:00:00Z`, which truncation also makes a date, and
      it passed. So did the whole suite.
   2. Fault CR5 refuses only `score == math.inf`. The test sets +inf only, and it passed. A -inf
      score is as unservable, and SQLite stores it in `REAL NOT NULL`.
   3. D-156's note says "A carried date is stored as a calendar date … a score that is not finite
      is not carried" (`decisions.md:2607`).
   4. The code is right today: `_as_stored` calls `_calendar_date` and `math.isfinite`.
   5. **The fix:** `test_a_carried_date_is_validated_not_cut_and_no_infinity_is_carried`, below. It
      carries `<script>alert(1)</script>` and -inf. It kills CR3 and CR5.
- **T9** `tests/unit/test_readonly_uri.py:108-109`; `scripts/calibrate_board.py:210`; `scripts/survey_boards.py:250`. **#92 T2 is half closed: the counts are held, but each entry's stated reason is not.**
   1. #92's body names two holes in T2: "It never compares call counts, and nothing checks an
      entry's stated reason ('a scratch copy')". `WRITABLE_OPEN_COUNTS` closes the first, and B16 is
      killed.
   2. Fault B11 makes `calibrate_board.main` store the fetched rows into `--db` (the operator's
      artifact by default) instead of its scratch copy. Fault B12 does the same in
      `survey_boards.measure`. Each passed every test. These are the M17 closure Tester's own B11
      and B12.
   3. `measure_slices`, the third entry, is held: B13 is killed by `test_survey_floors.py:121`,
      which asserts the artifact's bytes.
   4. The M17 closure Tester's remedy was to assert the `--db` bytes unchanged in the one test that
      runs `main()`. That was not done.
   5. **The fix:** `test_main_leaves_the_db_it_reads_untouched_and_records_its_floor_candidate` and
      `test_measure_stores_into_its_copy_never_the_artifact`, below. They kill B11 and B12.
- **T10** `scripts/calibrate_board.py:88`; `tests/unit/test_calibrate_board.py:112`. **#92 T4 is half closed: the M17 closure Tester's E2 still passes.**
   1. That Tester's T4 named two faults: E1 (`floor_shipped` by the retired rule) and E2
      (`min_quality` fixed at 0.0).
   2. The new test kills E1. Fault E2 passed every test.
   3. `min_quality` is the Budget Pick floor candidate that `_self_check` compares against the
      shipped surfaces.
   4. **The fix:** the last assertion of the T9 test above. It asserts `min_quality` is
      `top_third` of the ranked population, 1320.0 on that fixture. It kills E2.

## Notes (no change required by this verdict)

- **N1** **Equivalent: S9, S10, S12 and S13**, each a defence in depth behind another layer.
   1. S9 removes tearDown's "never installed" check. It fires only when the tripwire was never
      installed. S11 shows that case is also caught by `OfflineGuardTests`, and the Python check
      (`:44`) refuses a subclass hook that skips super.
   2. S10 removes `XCTAssertNil(notInstalled)`. It matters only if a selector vanishes from
      Foundation, which no input here can produce.
   3. S12 and S13 each remove one of the two installs, and the other install covers the gap.
- **N2** **Equivalent: FD2** (`FrontDoor.swift:318`, the save's `isFileURL` guard).
   `Data.write(to:)` and `createDirectory(at:)` fail on any non-file URL. Removing the guard
   therefore writes nothing to any address. `74e2bd1` narrowed the test's comment to say it holds
   the load, which FD1 shows it does.
- **N3** **Equivalent on every pin that reads `_code` today: C6** (a block comment's newlines
  dropped).
   1. Only newlines inside a comment are lost. The newline after `*/` stays, so a declaration
      after a comment keeps its line start.
   2. The four pins that read `_code` (`test_router_hints.py:197`, `:224`, `:246`;
      `test_engine_address.py:73`) give the same result either way.
   3. The docstring's "the code after it keeps its line" is untested, but nothing depends on it yet.
- **N4** **D10 reproduces round 2's M7 on the text gate.**
   1. `struct W5TBox: Decodable { let u: Foundation.URL? }`, decoded in `ContentView.swift`, passes
      every text gate.
   2. The compiler gate refuses it in all four configurations.
   3. `74e2bd1` filed it on #107 (comment of the second review). I agree with that disposition: the
      fix is #107's "a declaration whose result type is URL".
- **N5** **M5 is killed, but not by #92 T3's test.**
   1. `test_every_registered_board_metric_has_a_direction` walks `ARENA_METRIC`, `ARENA_SLICES` and
      `EPOCH_BOARDS`. Its docstring says "The registries every board comes from are walked here".
      `REMOTE_SOURCES` and `LOCAL_BUNDLES` (aider, swebench, Epoch's SWE-bench, DeepSWE) are not.
   2. Fault M5 gives aider C4's shape (`_KIND = "% pass_rate_3"; METRIC = _KIND`). It passes this
      test and the older constant walker.
   3. The suite kills it anyway: 34 tests fail, through the engine's own refusal of a metric with no
      direction. So it is not a hole today. Correct the docstring, or walk those two registries too.
- **N6** **#83 passes a MED close whose evidence names HIGH, and round 2's suggested fix would
  refuse a real close.**
   1. Probe: the M18-W1 close built as `_record` builds it, at MED, with the evidence
      "(risk: **MED**; the HIGH globs were not touched". The rule did not fire (rc 0).
   2. Round 2's M10 fix was to read the `risk: **X**` token. The real M18-W4 close records
      `risk: **MED**` from the milestone plan, then "It is **HIGH** by the plan's security globs".
      The rule passes it today. With the token rule it would be refused.
   3. A marked token that only the close's tier uses, such as a bolded `**HIGH**` or a
      `tier: HIGH` field, would separate the two. This is a design choice, not a defect today.
- **N7** **Not done by this seat, by its rules.**
   1. #108 and round 2's R4 (the exchanges widening #108's surface) were not probed. No bare
      `URLSessionConfiguration()` was built.
   2. No background session was run (T2).
   3. Four Swift faults could have let a test's request leave loopback: S1, S3, S11 and S15. They
      ran on a scratch copy whose two remote test addresses
      (`OfflineTestCase.swift:155`, `FrontDoorTests.swift:754`) were changed to `127.0.0.1:9`. That
      copy was run unfaulted first as a control: 10 of 10 passed.

## K.9 candidates spotted outside this wave's scope
- none

## Fault injection (HIGH: mandatory)

**Harness:** scratch `w5t/mut.py`, with the faults in `w5t/faults.py`. For each fault it does the
following:
1. It checks every file it touches against `HEAD`: `git hash-object` must equal
   `git rev-parse HEAD:<file>`, and `git status --porcelain` must be empty.
2. It records each file's sha256 and saves its bytes.
3. It makes exact string edits, each required to match exactly once. All 91 were dry-run first, for
   the match count and, on Python files, for syntax.
4. It runs the targeted checks:
   1. a Swift fault runs `swift test --filter` for its classes;
   2. a compiler-gate fault runs `client_decl_gate.py` and its tests;
   3. a probe on `Router.swift` runs `swift build`.

   If nothing fails, it runs all of `tests/` with `-n auto` and `MODEL_RANKING_REQUIRE_ARTIFACT=1`.
   For a Swift fault it then runs the whole Swift suite as well.
5. It writes the original bytes back **in place**, never with `git checkout` or `restore`.
6. It asserts three things: sha256 equals the pre-edit hash, `git hash-object` equals HEAD's blob,
   and `git diff --quiet` holds with `git status --porcelain` empty.

The four scratch-copy faults (S1, S3, S11, S15) were checked by sha256 against that copy's own
bytes. All 91 rows of the log (`w5t/logs/mutants.jsonl`) say `restored: true`. The 87 worktree rows
also say `git_clean: true`.

After the run, all 680 tracked files match the sha256 baseline taken before the first fault
(`shasum -c`: 680 OK). `git status --porcelain` was empty, `git diff --quiet` held, and the
artifact's sha256 is unchanged (`5c6977a9c67c…`). Every kill is a test assertion or a gate's
refusal. No fault was killed by an import error, a collection error or a compile error. Ids D8 and
S16 were not used.

**Restore hashes** (sha256 prefix, pre = post, and the HEAD blob that `git hash-object` matched):

| file | faults | sha256 (pre = post) | HEAD blob |
|---|---|---|---|
| `ios/EngineTests/OfflineTestCase.swift` | 11 (S2, S4–S10, S12–S14) | `e7fb6e90bfe6` | `686ed67d69` |
| `ios/ModelRanking/Engine/FrontDoor.swift` | 2 (FD1, FD2) | `5a18b996ee33` | `ebc8315719` |
| `ios/EngineTests/RefinementsTests.swift` | 5 (P1–P5) | `d0bdf50eab53` | `f440ace973` |
| `scripts/client_decl_gate.py` | 7 (D1–D7) | `22ad8870c8e7` | `380541e768` |
| `ios/ModelRanking/ContentView.swift` | 2 (D9, D10) | `c2f4a3ff1d11` | `705a1170a5` |
| `tests/unit/test_router_hints.py` | 10 (TG1, TG2, C1–C8) | `7332afc8fd21` | `75bf248bcc` |
| `ios/ModelRanking/Engine/Router.swift` | 2 (R1, R2) | `c624a374bad2` | `df2e08373b` |
| `scripts/wave_check_all.py` | 9 (MC1–MC9) | `e20adb9c04fc` | `ccd93802e4` |
| `scripts/wave_check.py` | 7 (H1–H7) | `c0074a4df226` | `d3a8bbe8fd` |
| `src/app/workflows/build.py` | 8 (CR1–CR7, W10) | `01a2f7787cca` | `da867261ee` |
| `src/app/workflows/ingest.py` | 2 (I1, I2) | `f61beac04080` | `d6e6120363` |
| `src/app/adapter/main.py` | 5 (W1–W4, W11) | `dfffdf9273e8` | `1dcc123fa9` |
| `src/app/workflows/refresh.py` | 2 (W5, W6) | `227db22ab772` | `c91b92c7d8` |
| `src/app/workflows/serving_bounds.py` | 3 (W7–W9) | `03150e0c3a16` | `a401c323d7` |
| `tests/unit/test_readonly_uri.py` | 1 (W12) | `52d22d442e36` | `055af3e429` |
| `scripts/calibrate_board.py` | 4 (B16, B11, E1, E2) | `c5e094a2a6ce` | `581ab642eb` |
| `scripts/survey_boards.py` | 2 (B12, B13) | `d33e06ff5b06` | `a7208046b0` |
| `src/app/clients/arena_slices.py` | 1 (M3) | `0c75d0dbac89` | `aec8f1ff2d` |
| `src/app/clients/arena.py` | 1 (M4) | `8f8c1dd11cab` | `f74bb43359` |
| `src/app/clients/aider.py` | 1 (M5) | `0c68e8f6b5b5` | `5f178dc5df` |
| `ios/app.sh` (text only; nothing ran it) | 2 (A1, A2) | `87fbebb2c27b` | `a78263dc44` |
| scratch copy only: `w5t/trees/swiftfault/ios/EngineTests/OfflineTestCase.swift` | 4 (S1, S3, S11, S15) | `6b2ac22d9288` | not in the worktree |

**The faults.** "Whole suite" means 1631 passed and 25 skipped in Python, plus the 367 Swift tests
for a Swift fault.

| id | the fault | result | killed by |
|---|---|---|---|
| S1 | `URLProtocol.registerClass` removed (scratch copy) | KILLED | `testARequestNoStubAnswersIsCaughtWithoutLeavingTheMachine` |
| S2 | `.default` not exchanged | KILLED | `testEverySessionConfigurationAsksTheTripwireFirst` |
| S3 | `.ephemeral` not exchanged (scratch copy) | KILLED | every guarded test's tearDown, 13 failures |
| S4 | the background getter not exchanged | KILLED | `testEverySessionConfigurationAsksTheTripwireFirst` (the list only: T2) |
| S5 | the `protocolClasses` setter not exchanged | KILLED | `testARequestAStubDeclinesIsCaughtToo` |
| S6 | the setter puts the tripwire first, ahead of the stub | KILLED | the `EngineClient` stub tests, 25 failures |
| S7 | the setter appends only to an empty list | KILLED | `testARequestAStubDeclinesIsCaughtToo` |
| S8 | tearDown no longer fails a test that made a request | SURVIVED (whole suite) | T1 |
| S9 | tearDown's "never installed" check removed | SURVIVED, equivalent | N1 |
| S10 | tearDown's `notInstalled` check removed | SURVIVED, equivalent | N1 |
| S11 | both installs removed (scratch copy) | KILLED | 16 failures, the "never installed" check among them |
| S12 | the per-test install removed | SURVIVED, equivalent | N1 |
| S13 | the class install removed | SURVIVED, equivalent | N1 |
| S14 | the tripwire fails a request without recording it | KILLED | `testARequestAStubDeclinesIsCaughtToo`, `testARequestNoStubAnswers…` |
| S15 | the tripwire declines every request (scratch copy) | KILLED | the same two |
| FD1 | the register's load reads any address (#58) | KILLED | `testTheRegisterIsOnlyEverAFileOnThisDevice` |
| FD2 | the register's save writes to any address | SURVIVED, equivalent | N2 |
| P1 | a test class derives from `XCTestCase` | KILLED | `test_swift_tests_offline.py:18` |
| P2 | a subclass tearDown skips super | KILLED | `test_swift_tests_offline.py:44` |
| P3 | a subclass class setUp skips super | KILLED | `test_swift_tests_offline.py:44` |
| P4 | `import Testing` | KILLED | `test_swift_tests_offline.py:53` |
| P5 | a class reaches `XCTestCase` through a `typealias` | KILLED | `test_swift_tests_offline.py:60`; the manifest test |
| D1 | `DECODES_URL` drops `IfPresent` (round 1's B1) | KILLED | `test_client_decl_gate.py:57`, `:70`; the gate's self-test |
| D2 | a decoded URL never recorded | KILLED | `:47`, `:57`, `:70`; the self-test |
| D3 | `URL.decoded` dropped from `NETWORK` | KILLED | `:47`, `:57`; the self-test |
| D4 | only a decoded `[URL]` counts | KILLED | `:57`, `:70`; the self-test |
| D5 | `main()` no longer runs the self-test | SURVIVED (whole suite; the gate rc 0) | T3 |
| D6 | the self-test compiles the app, not its fixture | KILLED | `:57`; the self-test |
| D7 | a decode anywhere charged to every file | KILLED | `:57`; the self-test ("refused what it must allow") |
| D9 | product: the view decodes `[URL]` from text | KILLED | the client text gate (`test_router_hints.py:379`); the compiler gate |
| D10 | product: a `Foundation.URL?` decoded in the view | KILLED by the compiler gate only | N4 (#107) |
| TG1 | the type-argument pattern removed | KILLED | `test_router_hints.py:600` |
| TG2 | the pattern narrowed to `<URL` | KILLED | `test_router_hints.py:600` |
| C1 | strings read as code | KILLED | `test_router_hints.py:619` |
| C2 | a raw string's `#` count ignored | KILLED | `:619` |
| C3 | an interpolation not read | KILLED | `:619` |
| C4 | block comments do not nest | KILLED | `:608` |
| C5 | `"""` read as three single quotes | SURVIVED (whole suite) | T4 |
| C6 | a block comment's newlines dropped | SURVIVED, equivalent today | N3 |
| C7 | a `//` comment runs to the end of the file | KILLED | five pins, `:608` among them |
| C8 | block comments not stripped | KILLED | `:591`, `:608` |
| R1 | control: an outcome's refinements assigned after it is built (`swift build` rc 0) | KILLED | `test_router_hints.py:224` |
| R2 | R1 below `#/a/*b/#` (`swift build` rc 0) | SURVIVED (whole suite) | T4 |
| MC1 | any heading containing "dropped" excused (pre-M9) | KILLED | `test_wave_check_m18_rules.py:142` |
| MC2 | an unread wave heading skipped (pre-M9) | KILLED | `:142` |
| MC3 | the ledger's `wave-close` rows ignored | KILLED | `:54` |
| MC4 | the control starts at M19 | KILLED | `:48`, `:54` |
| MC5 | the control grades every milestone (GPF-001) | KILLED | `:62` |
| MC6 | a plan with no readable wave no longer fails closed | KILLED | `:102` |
| MC7 | a `(dropped` mark anywhere in the plan excuses every wave | KILLED | `:54` |
| MC8 | `wave-check-all` prints a missing close and exits 0 | SURVIVED (whole suite) | T5 |
| MC9 | only `###` wave headings read | KILLED | `:113` |
| H1 | the tier read from the check column (round 2's M10) | KILLED | `:97`, `:157` |
| H2 | the tier read from the whole row | KILLED | `:157` |
| H3 | a close dated on the rule's first day not graded | KILLED | `:91`, `:125`, `:157` |
| H4 | an undated close not graded (round 1's M4) | KILLED | `:125` |
| H5 | `src/app/clients` needs its slash (round 1's M4) | KILLED | `:125` |
| H6 | only the footprint's first line read | SURVIVED (whole suite) | T7 |
| H7 | the rule refuses nothing | KILLED | `:91`, `:125`, `:157` |
| CR1 | carried rows bypass the store's rules (pre-#92) | KILLED | `test_carry_forward.py:369` |
| CR2 | a carried date kept as stored | KILLED | `:369` |
| CR3 | a carried date truncated, not validated | SURVIVED (whole suite) | T8 |
| CR4 | a non-finite carried score accepted | KILLED | `:369` |
| CR5 | only +inf refused in a carried row | SURVIVED (whole suite) | T8 |
| CR6 | an unsound source carried anyway | KILLED | `:369` |
| CR7 | the fixed rows thrown away | KILLED | `:369` |
| I1 | a missing score raises `TypeError` (pre-#92) | KILLED | `test_stored_scores_are_bounded.py:94` |
| I2 | a schema refusal no longer a `SourceError` | KILLED | `:101` |
| W1 | the boot probe opens the artifact writable, aliased | KILLED | `test_readonly_uri.py:177` |
| W2 | `/v1/categories`' facts writable, aliased | KILLED | `:177` |
| W3 | `/v1/boards` writable, aliased (the M17 closure's B8) | KILLED | `:177` |
| W4 | `/v1/recommendations` writable, aliased | KILLED | `:177` |
| W5 | `fingerprint_of` writable, aliased | KILLED | `:177` |
| W6 | `_served_without` writable, aliased | KILLED | `:177` |
| W7 | `standings_problem` writable, aliased | KILLED | `:177` |
| W8 | `largest_surface_row_count` writable, aliased | KILLED | `:177` |
| W9 | `ranked_row_count` writable, aliased | KILLED | `:177` |
| W10 | `Carry.restore` writable, aliased | KILLED | `test_carry_forward.py:315` |
| W11 | `/v1/boards` on `schema.connect` (the M17 closure's B7) | KILLED | `test_readonly_uri.py:177` |
| W12 | the watcher never switched on | KILLED | `:177` ("it is watching nothing") |
| B16 | a second writable open inside `calibrate_board.main` | KILLED | `test_readonly_uri.py:158` |
| B11 | `calibrate_board.main` stores into `--db` (the M17 closure's B11) | SURVIVED (whole suite) | T9 |
| B12 | `survey_boards.measure` stores into `db` (the M17 closure's B12) | SURVIVED (whole suite) | T9 |
| B13 | `survey_boards.measure_slices` stores into `db` | KILLED | `test_survey_floors.py:121` |
| M3 | a dataclass field default (the M17 closure's C3) | KILLED | `test_board_standings.py:648` |
| M4 | a metric through a non-`METRIC` name (the M17 closure's C4) | KILLED | `:648` |
| M5 | C4's shape on aider | KILLED by the suite (34 tests), not by `:648` | N5 |
| E1 | `floor_shipped` by the retired D-145 rule | KILLED | `test_calibrate_board.py:112` |
| E2 | `min_quality` fixed at 0.0 | SURVIVED (whole suite) | T10 |
| A1 | an added `simctl uninstall booted` | KILLED | `test_engine_service.py:523` |
| A2 | the same, continued over two lines | KILLED | `:523` |

## Tests added/extended this review

**None in the repository.** This seat may change only this file. Each test below was written into a
scratch copy of `5cf9cb2` (scratch `w5t/trees/prop`, its own local git). The whole diff is
`w5t/logs/proposed-tests.diff`: 8 files, +195 / -1.
- **Green with the tests in place:**
  1. Each is GREEN there.
  2. The copy's whole suite passes: 1642 passed, 25 skipped.
  3. `ruff check` passes on every file touched.
  4. T4's raise and T6's one-line change are the only non-test edits. The suite stays green with
     both.
- **Red on its fault:** each was run against the fault it is written for, in that copy
  (`w5t/logs/proposals.jsonl`). Each goes red by assertion, or by T4's raise:
  1. S8 by T1;
  2. BG, one background configuration added to a test file, by T2;
  3. D5 by T3;
  4. C5 and R2 by T4;
  5. MC8 by T5;
  6. H6 by T7;
  7. CR3 and CR5 by T8;
  8. B11 and B12 by T9;
  9. E2 by T10.

  T6's test is red at `5cf9cb2` itself and green with its fix.
- **Restored:** every fault was then restored and checked by sha256 and `git status` in that copy.

**T1 and T2.** In `tests/unit/test_swift_tests_offline.py`:
```python
def test_no_swift_source_builds_a_background_session() -> None:
    """W5 Tester (round 2's M11): a background session never asks custom protocol classes. The SDK's
    own header says so (`NSURLSession.h`, on `protocolClasses`: "Custom NSURLProtocol subclasses are
    not available to background sessions"). So the tripwire listed in a background configuration
    catches nothing, and only the source can refuse one. The base's own check of the list is exempt."""
    engine = TESTS.parent / "ModelRanking"
    users = [p.name for p in sorted([*TESTS.glob("*.swift"), *engine.rglob("*.swift")]) if p.name != BASE
             and re.search(r"\bbackground\s*\(\s*withIdentifier|backgroundSessionConfiguration",
                           p.read_text(encoding="utf-8"))]
    assert users == [], users


def test_the_base_fails_a_test_whose_requests_it_recorded() -> None:
    """W5 Tester (#59): with its assertion on the drained requests removed, the base's tearDown failed
    nothing and every test passed (the check above matches `OfflineGuard` in the body, which the drain
    alone satisfies). Swift cannot hold this here: the way to expect a failure is `XCTExpectFailure`,
    which `scripts/swift_xunit_gate.py` refuses because the parallel run reports it as a pass."""
    base = (TESTS / BASE).read_text(encoding="utf-8")
    tear_down = re.search(r"override func tearDown\(\) \{(.*?)\n    \}", base, re.S)
    assert tear_down, "the base has no tearDown"
    body = tear_down.group(1)
    drained = re.search(r"let (\w+) = OfflineGuard\.drain\(\)", body)
    assert drained, "the base no longer reads what the tripwire saw"
    assert re.search(rf"XCTAssertEqual\(\s*{drained.group(1)}\s*,\s*\[\]", body), (
        "the base no longer fails a test that reached for the network")
```

**T3.** In `tests/unit/test_client_decl_gate.py`:
```python
def test_make_client_decls_fails_when_its_self_test_does(monkeypatch: pytest.MonkeyPatch) -> None:
    """W5 Tester: `main()` runs the self-test before it checks the app, so the gate cannot pass the app
    while it has stopped refusing (#51). Nothing held that: with the call unwired, every test here and
    `make client-decls` passed. A failed self-test returns before anything compiles, so this runs
    where there is no Xcode too."""
    monkeypatch.setattr(gate, "self_test", lambda: ["ContentView.swift: URL.decoded was not refused"])
    assert gate.main() == 1
```

**T4.** In `tests/unit/test_router_hints.py`: `import pytest` beside the other imports; at the end of
`_code`, before `return "".join(out)`:
```python
    if depth:  # W5 Tester: a comment Swift would refuse to build means the scan misread the file
        msg = "a block comment never closes: `_code` misread a literal, and would erase live code"
        raise ValueError(msg)
```
and:
```python
def test_the_comment_stripper_reads_a_triple_quoted_string() -> None:
    """W5 Tester: `_string_end` reads a `\"\"\"` string to its closing `\"\"\"`, and nothing held it. Read
    as three single quotes, a `/*` on a later line of the string opened a comment and erased the code
    after it, to the end of the file."""
    assert "let live = 1" in _code('let s = """\nsee /* the note\n"""\nlet live = 1\n')


def test_the_comment_stripper_fails_closed_on_a_comment_that_never_closes() -> None:
    """W5 Tester (round 2's M8, fix 3): Swift cannot build an unclosed `/*`, so a scan that ends inside
    one has misread the file. An extended regex literal holding `/*` (`#/a/*b/#`, which builds) is
    such a misreading: above a live `copy.refinements = extra` in Router.swift it erased the
    assignment, and the D-168 pin passed."""
    with pytest.raises(ValueError, match="never closes"):
        _code("let pattern = #/a/*b/#\ncopy.refinements = extra\n")
```

**T5, T6 and T7.** In `tests/unit/test_wave_check_m18_rules.py`, with `import pytest`. T6's change
to `scripts/wave_check_all.py:66` is given under T6 above.
```python
def test_wave_check_all_itself_fails_on_a_planned_wave_with_no_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """W5 Tester: the plan's check is that `wave-check-all` FAILS on a planned wave with no close. Every
    test above calls `missing_closes`; with its result dropped from `main()`'s exit, all of them, and
    `make wave-check-all`, passed."""
    check = _module("wave_check_all")
    root = _tree(tmp_path, closes=(1,))
    (root / "docs" / "plans" / "m18-wave-1-close.md").write_text(
        "---\nprocess_version: v6.6\ndate: 2026-10-04\n---\n# W1\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "wave_check.py").write_text("def main(argv):\n    return 0\n", encoding="utf-8")
    monkeypatch.setattr(check, "ROOT", root)
    assert check.main() == 1
    assert "m18 W2 is in the plan and has no close record" in capsys.readouterr().out


def test_the_whole_footprint_is_read_not_its_first_line(tmp_path: Path) -> None:
    """W5 Tester: a real footprint runs over several lines (the M18-W4 close's does). Read up to its
    first newline only, a `src/app/clients` path on the second line passed as MED."""
    record = _record(tmp_path, tier="MED", touched="src/app/workflows/rank.py ·\n                src/app/clients/epoch.py")
    assert "src/app/clients" in _wave_check(record).stdout


def test_a_bold_or_deep_wave_heading_is_reported_when_another_one_parses(tmp_path: Path) -> None:
    """W5 Tester (round 2's M9, second half): `LOOKS_LIKE_A_WAVE` reads `### W2` and `## Wave Three`, but
    not `### **W2** — two` or `##### W2 — two`. With `### W1` parsing beside either, the second wave
    was never counted and nothing was missing."""
    check = _module("wave_check_all")
    for name, heading in (("bold", "### **W2** — two"), ("deep", "##### W2 — two")):
        root = tmp_path / name
        plans = root / "docs" / "plans"
        plans.mkdir(parents=True)
        (plans / "m19-plan.md").write_text(f"# M19\n\n### W1 — one\n\n{heading}\n", encoding="utf-8")
        (plans / "m19-wave-1-close.md").write_text("a close\n", encoding="utf-8")
        (root / "docs" / "closure-report-m19.md").write_text("closed\n", encoding="utf-8")
        assert any("W2" in line for line in check.missing_closes(root)), heading
```

**T8.** In `tests/unit/test_carry_forward.py`:
```python
def test_a_carried_date_is_validated_not_cut_and_no_infinity_is_carried(tmp_path: Path) -> None:
    """W5 Tester (#92 N2): the test above carries a timestamp, which cutting to ten characters also
    makes a date, so the rule MINOR-2 retired (`<script>alert(1)</script>` became `<script>al`) passed
    it. And it carries +inf only; -inf is as unservable."""
    from app.workflows.build import Carry

    live = _live(tmp_path)
    raw = sqlite3.connect(live)
    raw.execute("UPDATE scores SET run_date = '<script>alert(1)</script>' WHERE source = 'aider'")
    raw.execute("UPDATE scores SET score = -9e999 WHERE source = 'swebench'")
    raw.commit()
    raw.close()
    conn = connect(str(tmp_path / "candidate.db"))
    carry = Carry(live=live, last_ok={"aider": _iso(1), "swebench": _iso(1)}, now=NOW)

    assert carry.restore(conn, "aider") == "carried"
    assert {d for (d,) in conn.execute("SELECT DISTINCT run_date FROM scores WHERE source = 'aider'")} == {None}
    assert carry.restore(conn, "swebench") == "absent"
```

**T9 and T10.** In `tests/unit/test_calibrate_board.py`:
```python
def test_main_leaves_the_db_it_reads_untouched_and_records_its_floor_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W5 Tester (#92 T2's second half, T4's E2): `WRITABLE_OPENS` lets `main` write because it writes "a
    scratch copy the script makes, never the artifact", and nothing held that: `main` storing the
    fetched rows into `--db` itself passed every test. Nor was `min_quality` held: fixed at 0.0, it
    passed too (the M17 closure Tester's E2)."""
    from app.clients.fakes import FakeRawSource
    from app.workflows.floors import top_third
    from app.workflows.ingest import RunContext, ingest_litellm
    from app.workflows.rank import build_price_medians
    from app.workflows.registry import reconcile
    from app.workflows.schema import connect

    from .test_api_v1 import PRICING

    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), RunContext(observed_at="2026-09-22T00:00:00Z"))
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()
    before = db.read_bytes()
    ratings = {"gpt-5": 1320.0, "gpt-5-high": 1319.0, "claude-opus-4-5": 1300.0, "deepseek-v3.2": 1250.0}
    board = json.dumps({"rows": [
        {"row": {"model_name": name, "rating": r, "rating_lower": r - 10, "rating_upper": r + 10,
                 "category": "overall", "leaderboard_publish_date": "2026-09-13"}}
        for name, r in ratings.items()]})
    script = _script()
    monkeypatch.setattr(script.ArenaClient, "fetch_raw", lambda self: board)
    out = tmp_path / "record.json"
    assert script.main(["--config", "vision", "--db", str(db), "--out", str(out)]) == 0
    assert db.read_bytes() == before, "main() wrote into the --db it was given"
    record = json.loads(out.read_text(encoding="utf-8"))
    # The ranked population is three models, each at its best rating.
    assert record["threshold_candidates"]["min_quality"] == top_third([1320.0, 1300.0, 1250.0]), record
```
In `tests/unit/test_survey_floors.py`:
```python
def test_measure_stores_into_its_copy_never_the_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W5 Tester (#92 T2's second half): `measure` is allowed a writable open because it opens "a scratch
    copy the script makes, never the artifact", and no test ran it: `measure` storing into `db` itself
    passed every test. Its sibling `measure_slices` is held by the test above."""
    from app.clients.fakes import FakeRawSource
    from app.workflows.ingest import RunContext, ingest_litellm
    from app.workflows.rank import build_price_medians
    from app.workflows.registry import reconcile

    from .test_api_v1 import PRICING

    artifact = tmp_path / "advisor.db"
    conn = connect(str(artifact))
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), RunContext(observed_at="2026-09-22T00:00:00Z"))
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()
    before = artifact.read_bytes()
    board = json.dumps({"rows": [
        {"row": {"model_name": name, "rating": r, "rating_lower": r - 10, "rating_upper": r + 10,
                 "category": "overall", "leaderboard_publish_date": "2026-09-13"}}
        for name, r in (("gpt-5", 1320.0), ("claude-opus-4-5", 1300.0))]})

    class _Board:
        name, benchmark, url = "arena_vision", "Arena vision", "https://example.invalid/board"

        def fetch_raw(self) -> str:
            return board

    script = _script()
    monkeypatch.setattr(script, "survey_client", lambda config: _Board())
    workspace = tmp_path / "work"
    workspace.mkdir()
    script.measure("vision", artifact, workspace)
    assert artifact.read_bytes() == before, "measure() wrote into the artifact it was given"
```

## Safety (this seat's rules)

- **Neither installer script was executed by this seat.**
  1. `scripts/install_engine_service.sh` and `scripts/remove_engine_service.sh` ran only inside
     `tests/unit/test_engine_service.py`, with its stubs and its scratch HOME.
  2. That happened in the gate, in the whole-suite runs of the fault harness, and in the replays.
  3. No fault touched either installer.
  4. A1 and A2 edited `ios/app.sh` as text. Nothing ran it.
- **No `launchctl`, `xcodebuild` or `simctl` ran, and nothing touched the simulator.**
  1. The provided `guard-bin` was first on PATH in every command.
  2. This seat added an `xcrun` filter in front of it that refuses `simctl`, `xcodebuild`,
     `devicectl`, `instruments` and `xctrace`. `client-decls` used `xcrun` only for
     `--show-sdk-path` and `swiftc -typecheck`.
  3. `swift test` and `swift build` ran on macOS only.
  4. Each guard was fired once, on purpose, to prove it refuses:
     1. `launchctl print` exited 97;
     2. `xcrun simctl list` exited 97;
     3. `xcodebuild -version` exited 97;
     4. `simctl list` exited 97.

     None fired otherwise.
- **Nothing that can crash a process.**
  1. No `os.abort()`, `fatalError`, `preconditionFailure` or `try!` in any probe or fault.
  2. No bare `URLSessionConfiguration()` (#108) and no background session was built.
  3. The proposed tests add no Swift.
- **Nothing bound beyond loopback, and nothing bound 8080.**
  1. A `sitecustomize` guard was on `PYTHONPATH` for every Python run.
  2. It refuses five things:
     1. a bind that is not loopback;
     2. port 8080;
     3. any port from 1 to 8100;
     4. a connect to an address that is not loopback;
     5. DNS for a real name.

     Each refusal raises and is logged. None aborts.
  3. It was fired on purpose once per rule: 0.0.0.0:8150, 127.0.0.1:8080, 127.0.0.1:8050,
     192.168.1.10, 1.1.1.1 and `example.com`. The log was then cleared.
  4. After that it logged **nothing**, across the gate, the replays, all 103 fault runs (91 in the
     worktree and its scratch copy, 12 in the proposal copy), the coverage runs and the probes.
- **The network.**
  1. No test reached it.
  2. The only requests made were the suite's own to `127.0.0.1:9`, a closed loopback port. Faults
     S5 and S7 sent `testARequestAStubDeclinesIsCaughtToo`'s request there, as did the replay of
     `3c584a5`, and S1, S3, S11 and S15 sent their copy's.
  3. The bodies of #59, #92, #107, #108 and #110 were read with `gh issue view`. That is a read, and
     nothing was written.
- **Changes.** No commit, no push, no GitHub write.
  1. The only change in the worktree is this file.
  2. Every fault was reverted in place and checked byte-identical (table above). No `git checkout`
     or `restore` was used.
  3. `epb.html`, `or.md` and `.github/**` were not touched.
  4. Scratch work is under the session scratchpad's `w5t/` folder. One stray empty file this seat
     created by mistake, `/tmp/ignore_w5t`, was deleted.
