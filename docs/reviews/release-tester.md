---
record_type: review
id: release-tester
status: draft
seat: independent
process_version: v7.1.2
date: 2026-10-17
---
# Release Tester Review

**Reviewer:** Tester subagent (`.claude/agents/Tester.md`). I had fresh eyes and wrote none of the range's
product code or tests. The only tests I wrote are the ones this review lists under "Tests added".
**Independent:** yes
**Date:** 2026-10-17
**Commit range:** `81af5ba..9217c6cf6b110c4e04c4ce48edd3dfd545b0e059`. `81af5ba` is the head of the
last release review (`docs/reviews/release-security.md`). No light-mode Tester verdict existed before
this one. The range is 586 commits up to `ea04b05` (`integration/run-golden-night`), plus my one test
commit, `9217c6c`.
**Reviewed head:** 9217c6cf6b110c4e04c4ce48edd3dfd545b0e059
**Risk tier:** HIGH. The range carries the hosted engine's serving path, the app's engine address, a
cache of engine answers on the phone, and the DevFlow v7.1 and v7.1.2 guard and gate upgrades.
**Seat:** my own worktree on `review/release-tester`, cut from `ea04b05`, with its own `.venv`
(`make install`, `make hooks`), and a copy of `advisor.db` as the owner allowed. Scratch files were kept
in `$TMPDIR`. Cross-model routing: the authoring family and the reviewer family are the same (Claude). No
second family was available in this seat. Fresh context: this seat read the code and the tests, not the
implementers' sessions.

## Verdict
PASS WITH FINDINGS

Every acceptance criterion in scope now has a passing test that cites it. Two gaps were found and closed
by this review: #294 had no citing test, and three faults stayed green. One gate defect is filed (#325).
Nothing is BLOCKING.

## Scope

Earlier milestones in the range had their own heavy-mode Testers. I read those verdicts and did not
redo them: `docs/reviews/m19-wave-{1..5}-tester.md`, `m20-wave-{1..5}-tester.md`,
`m21-wave-{1..4}-tester.md`, `issue-260-credits-tester*.md`, `issue-265-licensed-sources-tester.md`, and
`backlog-{data,gates,hardening,reading}-tester.md`.

What this review covers:

**(a) Work merged with no milestone Tester:**
- Light mode since D-201:
  - run product-night: #296 (#288), #302 (#289), #298 (#273), #299 (#218), #300 (#66 / D-203),
    #303 (#301);
  - run golden-night: #310 (#294), #311 (#279), #312 (#304), #313 (#255), #316 (#293), #315 (#297),
    #324 (#292).
- The DevFlow upgrades: #281 (v7.1, D-200) and #306 (v7.1.2, D-205), outside `.claude/`.
- Two older merges that had a Code-Reviewer but no Tester: #259 (#258, the startup catch-up) and #207
  (the M20 hosted-boards hotfix, D-186 and D-187).

**(b) The product paths:** `src/app/` and the serving API, and `ios/ModelRanking/`.

## Suite result

| Run | Head | Result |
|---|---|---|
| `make check` | `ea04b05` | All legs green except conformance. `test-documented-paths` was red on 5 dangling references, all in my own scratch notes under the gitignored `build/`. They went green once the notes moved to `$TMPDIR`. This is filed as #325 (below). |
| `make gate` | `ea04b05` | `gate PASS: check conformance falsify secrets deps slopsquat` in 5:31. pytest: 3244 passed, 27 skipped. Every skip is an environment skip: live upstreams, the owner's Epoch bundle. swift-test: 691 tests, each named in the manifest. SlowTierTests on a one-thread pool: 7 of 7. client-decls: 22 files in 4 configurations. |
| commit-msg `make check-fast` | `9217c6c` | PASS in 158 s. All 6 legs green. |
| `make gate` | `9217c6c` | `gate PASS: check conformance falsify secrets deps slopsquat` in 6:04. pytest: 3245 passed, 27 skipped. swift-test: 694 tests, each named in the manifest. SlowTierTests: 7 of 7. client-decls: 22 files in 4 configurations. |
| Device and simulator build | `ea04b05` | `xcodebuild -scheme ModelRanking -configuration Debug -destination 'generic/platform=iOS'` and `... 'generic/platform=iOS Simulator'`, unsigned: both `** BUILD SUCCEEDED **`. The device product's Info.plist carries `EngineOnDevice = YES` and `EngineURL = http://127.0.0.1:8080`, so `EngineClient.address` gives the hosted engine there (D-202 clause 4). I did not launch the app: on loopback it would reach the owner's launchd engine (D-174). |

Golden report (`build/golden-report.txt`): 40 of 41 asserted questions pass. The one known miss is #295,
which the run stopped for the owner. 8 questions are disputed, out of 49.

**Coverage on touched code.** `src/` modules changed in the range: base `81af5ba` measured in a detached
worktree, head from the gate run. Total: 91.8 % to 92.2 %.

| Module | Before | After |
|---|---|---|
| `adapter/main.py` | 98.0 | 98.3 |
| `adapter/nightly.py` | 99.6 | 99.7 |
| `clients/aider.py` | 89.6 | 90.1 |
| `clients/arena.py` | 92.4 | 92.5 |
| `workflows/ingest.py` | 97.6 | 97.8 |
| `workflows/public.py` | 85.5 | 86.7 |
| `workflows/rank.py` | 97.6 | 99.0 |
| `workflows/refresh.py` | 95.5 | 95.7 |
| `workflows/registry.py` | 98.8 | 99.5 |

- New modules: `arc_prize.py` 92.9, `models_dev.py` 94.0, `terminalbench.py` 90.3, `families.py` 100.
- Unchanged at 100: `access_served`, `board_tables`, `boards`, `categories`, `sources`, `standings`.
- `coverage.py` stays at 94.3.
- `clients/epoch_board.py` reads 91.8 to 91.1. No proof was lost there: the same 9 statements are missed
  before and after. M21-W1 removed 11 covered statements, which shrinks the denominator.
- The per-module floor gate is green.

## Acceptance-criterion coverage

Each line names the citing test as `file:line` and what it asserts. Every test listed is GREEN at
`9217c6c`.

**#288: the phone reaches the hosted engine, and the last answer stands in (D-202 clauses 4 and 5)**
- **Device, no override, gives the hosted engine.** `ios/EngineTests/EngineClientTests.swift:810`, and
  `:820` for an unusable address. The app's client uses the chosen address: `:852`.
- **An override gives the override.** `ios/EngineTests/EngineClientTests.swift:829`.
- **The simulator gives loopback, or what its build was given.**
  `ios/EngineTests/EngineClientTests.swift:836`. The plist key a phone build sets:
  `tests/unit/test_engine_address.py:79`.
- **Stored on success.** `ios/EngineTests/KeptAnswerTests.swift:100` checks the store's own clock and the
  surface the engine echoed. `tests/unit/test_engine_address.py:122` pins that `ContentView.load()` keeps
  a fresh answer and a fresh surfaces' list. ContentView is not executed by `swift test`, so this pin is
  the only hold on it.
- **Shown with its date when offline.** `ios/EngineTests/KeptAnswerTests.swift:351`, plus `:312`: only
  an unreachable engine is stood in for. The dated line on the home screen:
  `tests/unit/test_engine_address.py:122`.
- **Never shown for another surface.** `ios/EngineTests/KeptAnswerTests.swift:155`, `:165`.
- **An empty kept surfaces' list is nothing kept.** `ios/EngineTests/KeptAnswerTests.swift:223`, written
  by this review (fault G02).
- **Builds for a device and runs in the simulator.** Shown by the xcodebuild runs above, not by a test.
  client-decls type-checks the device configurations on every `make check`.

**#289: a golden question set routed and ranked from a pinned snapshot (D-202 clause 2)**
- **In `make check`.** `ios/EngineTests/GoldenQuestionTests.swift:142` is in
  `ios/EngineTests/test-manifest.txt` and runs in the swift-test leg. It fails rather than skips when the
  embedding assets are missing.
- **30 to 50 questions, both languages, each disputed one says why.**
  `ios/EngineTests/GoldenQuestionTests.swift:114`.
- **The top 3 is derived, never hand-written.** `tests/unit/test_golden_questions.py:112`, and the
  derivation's own tests from `:38`. The Swift family list agrees with the script:
  `ios/EngineTests/GoldenQuestionTests.swift:132`.
- **One reviewable file.** `ios/EngineTests/Golden/golden-questions.json`.
- **Every miss fixed or filed.** `known_miss` carries its issue number. A known miss that starts passing
  fails the test: `ios/EngineTests/GoldenQuestionTests.swift:177`.
- **Apart from the held-out sets.** `tests/unit/test_golden_questions.py:161`.
- **Bundled in the test target only (REQ-APP-001).** `tests/unit/test_golden_questions.py:180`.

**#273: a language the recogniser is unsure of is not read as English**
- `ios/EngineTests/UnsureLanguageTests.swift:38`: not read as English.
- `:48`: answered "not measured".
- `:66`: a short English line of names and versions stays on the English path.

**#218: a short Turkish question that names a model is read as Turkish**
- `ios/EngineTests/UnsureLanguageTests.swift:91`: read as Turkish.
- `:107`: answered from everyday.
- `:126`: an English question with a Turkish-looking word is not read as Turkish.

**#66 and D-203: small talk, text with no meaning, a dictated answer**
- `ios/EngineTests/ReadingTests.swift:924`: greetings and feelings.
- `:933`: placeholder text and one word repeated.
- `:941`: a dictated answer.
- `:956`: a search that shares their words stays a search.

**#301: quantum physics reads as expert**
- `ios/EngineTests/KeywordRoutingTests.swift:79`, English and Turkish. It cited only #289 until this
  review added #301 to its comment.

**#293: example sentences give a plain request a better place than maths**
- `ios/EngineTests/TurkishEmbeddingTests.swift:201`: an English request for sources.
- `:208`: Turkish polite sentences.
- `:220`: maths stays maths.
- Both golden questions are now asserted in `GoldenQuestionTests.swift:142`. Their `known_miss` marks
  are gone.

**#292: an agent with its own coding verb reads as agentic coding**
- `ios/EngineTests/KeywordRoutingTests.swift:172`: the positive cases.
- `:186`: the negatives, including code written for an agent and an agent in another sentence.
- `:206`: zip and promo codes. Written by this review (fault G06).
- `:216`: a user agent or travel agent. Written by this review (fault G06b).

**#294: the 10-percent-brain question is disputed (D-206 clause 3)**
- `tests/unit/test_golden_questions.py:209`, written by this review. Before it, no test cited #294.
- The test checks that the question is disputed, that its reason names both `factuality` and `expert`,
  and that it is no known miss.
- Red on the set as it stood before #310 (`9dd9a77^1`): all four problems are reported. Green at head.

**#297: `keep` only in the load path, and INV-73 reworded (D-206 clause 4)**
- `tests/unit/test_kept_answer_provenance.py:39`: a planted `keep` elsewhere is refused.
- `:151`: the same on a compiled client.
- INV-73's wording: `tests/unit/test_engine_address.py:171`.

**#279: an XCTestObservation fails a test that reached for the network (D-206 clause 7)**
- `ios/EngineTests/OfflineTestCase.swift:201`: a planted subclass whose `tearDown` skips `super` is
  still failed.
- `tests/unit/test_swift_tests_offline.py:97`: the observer's registration.
- The `tearDown` check stays as it was: `tests/unit/test_swift_tests_offline.py:82`.

**#304: L1 skips what git ignores and does not track (D-206 clause 5)**
- `tests/unit/test_language_rule_gitignored.py:47`: an untracked ignored file is not read.
- `:52`: a tracked file under an ignored path is still read.
- `:94`: the `ios/.build/` entry has left `.language-allow`.

**#255: `make closing-keywords` (D-206 clause 6)**
- `tests/unit/test_closing_keywords.py:85`: the `fix: #N` colon form, which is the incident.
- `:160`: a merge commit's own message is read.
- `:174`: an empty range is an error, never a pass.
- `:221`: the target is advisory, not a leg of `check`.
- Run on `origin/main..ea04b05`: `closing-keywords: none`.

**#258 (#259): new release data is caught up at startup**
- `tests/unit/test_nightly_refresh.py:168`, four cases.
- `:184`: the build comes from `APP_BUILD`.

**#207 (D-186 and D-187)**
- `tests/unit/test_public_artifact.py:35`: no source is left out on TestFlight.
- The routing half: `KeywordRoutingTests` and `FrontDoorTests`, each citing D-187.

**The DevFlow upgrades, #281 and #306 (D-200, D-205)**
- D-200 clause 2: `tests/unit/test_wave_check_m21_rules.py:317`.
- `make secrets` fails closed on an empty set: `tests/unit/test_secrets_scan.py:72`.
- D-205 clause 3, the project's guard rules ported: `tests/unit/test_bash_guard_bounds.py`, and
  `conformance/test-bash-guard.py` (543 calls, 0 wrong verdicts).
- Six tests left `test_wave_check_m21_rules.py` in #281. They were replaced in the same change by their
  v7.1 forms, as D-200 clause 1 rules. They were not deleted to get to green.

**Red to green on reported symptoms.** Each light-mode fix in the range landed as a red test commit
before its fix (for example `9cad8f5` for #292, then `ab82d5c`). My fault injections below each re-create
the defect, and each one now turns its test red.

## Fault-injection table

Protocol:
1. Take the md5 of the file.
2. Break it with an exact string, found once.
3. Run the named tests.
4. Revert in place by string replacement at the injected offset.
5. Check the md5 again.

Each row is one atomic sequence, logged by the runner (`$TMPDIR/rt-scratch/faults.py`, not committed).
Every file was restored byte-identical. `git status` was clean after each batch, apart from this review's
own test edits.

| # | Behaviour broken | File | Tests run | Result |
|---|---|---|---|---|
| F01 | a phone with loopback keeps loopback | `Engine/EngineClient.swift` | DeviceAddressTests | RED (3 tests) |
| F02 | a kept answer for another surface is shown | `Engine/KeptAnswers.swift` | KeptAnswerTests | RED |
| F02b | the engine's echo is not checked | `Engine/KeptAnswers.swift` | KeptAnswerTests | RED |
| F03 | an engine refusal is stood in for | `Engine/KeptAnswers.swift` | KeptAnswerTests | RED |
| G01 | a kept answer dated ahead is shown | `Engine/KeptAnswers.swift` | KeptAnswerTests | RED |
| G02 | an empty kept surfaces' list stands in | `Engine/KeptAnswers.swift` | KeptAnswerTests | **GREEN**, then RED with the new test |
| G03 | eviction drops the newest | `Engine/StandingsStore.swift` | KeptAnswerTests | RED |
| F04 | `keep` allowed anywhere (#297) | `scripts/client_decl_gate.py` | test_kept_answer_provenance | RED |
| G10 | a kept answer's type decoded anywhere | `scripts/client_decl_gate.py` | test_kept_answer_provenance | RED |
| F21 | the typed question is sent as `q` (REQ-RTR-004) | `Engine/EngineClient.swift` | BudgetIsSentTests | RED (2 tests) |
| F05 | an unsure language reads as English (#273) | `Engine/Router.swift` | UnsureLanguageTests | RED |
| G07 | word floor 3 to 1 (#273) | `Engine/Router.swift` | UnsureLanguageTests | RED |
| F06 | Turkish beside model names off (#218) | `Engine/Router.swift` | UnsureLanguageTests | RED |
| G08 | threshold 0.9 to 0.5 (#218) | `Engine/Router.swift` | UnsureLanguageTests | RED |
| F07 | no-meaning rule off (D-203) | `Engine/Reading.swift` | GuidingNoteTests | RED |
| F07b | dictated-answer phrases removed (D-203) | `Engine/Reading.swift` | GuidingNoteTests | RED |
| F08 | quantum stems removed (#301) | `Engine/Router.swift` | KeywordRoutingTests | RED |
| F09 | family coverage rounds down (#289) | `Engine/Combine.swift` | GoldenQuestionTests | RED (both golden tests) |
| F09b | the script's coverage rounds down (#289) | `scripts/golden_questions.py` | test_golden_questions | RED |
| F10 | agent-with-coding-verb rule off (#292) | `Engine/Router.swift` | KeywordRoutingTests | RED |
| F10b | the sentence split is off (#292) | `Engine/Router.swift` | KeywordRoutingTests | RED |
| G05 | a verb before the agent counts (#292) | `Engine/Router.swift` | KeywordRoutingTests | RED |
| G06 | zip or promo code counts as code (#292) | `Engine/Router.swift` | KeywordRoutingTests | **GREEN**, then RED with the new test |
| G06b | a user or travel agent counts (#292) | `Engine/Router.swift` | KeywordRoutingTests | **GREEN**, then RED with the new test |
| F11 | #293's English search examples removed | `Engine/Router.swift` | PlainRequestReadingTests, GoldenQuestionTests | RED (both) |
| F12 | the observer's block asserts nothing (#279) | `EngineTests/OfflineTestCase.swift` | OfflineGuardTests | RED |
| F13 | L1 reads ignored files (#304) | `scripts/check_records.py` | test_language_rule_gitignored | RED |
| F13b | the ignored set loses `--others` (#304) | `scripts/check_records.py` | test_language_rule_gitignored | RED |
| F14 | the `fix: #N` colon form is missed (#255) | `scripts/closing_keywords.py` | test_closing_keywords | RED |
| F14b | an empty range passes (#255) | `scripts/closing_keywords.py` | test_closing_keywords | RED |
| F15 | no startup catch-up for a new release (#258) | `src/app/adapter/nightly.py` | test_nightly_refresh | RED; revert note below |
| G09 | an `unknown` build catches up (#258) | `src/app/adapter/nightly.py` | test_nightly_refresh | RED |
| F16 | a source left out of the public artifact (D-186) | `src/app/workflows/public.py` | test_public_artifact | RED |
| F17 | the budget cap becomes exclusive (REQ-REC-002) | `src/app/workflows/recommend.py` | tests/ | RED (`test_budgets_endpoint.py:55`) |
| F18 | the rate limiter fails closed (#187) | `src/app/adapter/main.py` | tests/unit | RED (`test_rate_limit.py:67`) |
| G13 | `/health` is rate-limited | `src/app/adapter/main.py` | tests/unit | RED |
| F22 | a mutating method on `/v1/budgets` (INV-30) | `src/app/adapter/main.py` | test_api_v1, test_api_config | RED (`test_api_v1.py:517`) |
| F19 | the deploy gate ignores code changed after the reviewed head (#306) | `scripts/deploy_gate.py` | pytest `-k deploy`: GREEN; `conformance/test-bash-guard.py`: RED | RED in `make check` |
| G12 | `scripts/*.md` counted as a record (#306) | `scripts/deploy_gate.py` | pytest and conformance | RED |
| F20 | `make secrets` passes an empty set (#281) | `scripts/secrets_scan.py` | test_secrets_scan | RED |

Notes on the table:
- **F19.** No pytest test holds the deploy gate's head comparison. `conformance/test-bash-guard.py` does,
  through the deploy-gate cases, and it runs in `make check`. No test was needed.
- **F15's first revert.** The runner first reverted by replacing the first occurrence of the injected
  text. A twin line at `nightly.py:361` matched first, so the md5 differed. I repaired it in place by
  string replacement: the md5 is back to `78ed5840839c0d94b2bfb014c79a14c8`, as before the injection.
  `git checkout` was never used. The runner then changed to revert at the injected offset. The red result
  was not affected: the injection hit the right line.
- **F01, F07 and F07b, first run.** They first ran under a filter that matched no test, or the wrong
  class, so they showed green with 0 or unrelated tests. I re-ran them under the right class, and all
  three went red. That was the runner's error, not a hole in the suite.
- **Not injected:** `.claude/hooks/bash_guard.py`. It is the owner's file, and this seat may not write
  into `.claude/`. The v7.1.2 upgrade's four security rounds fault-tested it
  (`docs/reviews/devflow-v7.1.2-upgrade-security.md`), and conformance runs 543 cases against it.

**Mutation kill-rate (advisory).** No mutation runner is wired for this stack. Of the 40 hand-made
faults, 37 were killed by the suite as it stood at `ea04b05`. All 40 are killed at `9217c6c`.

## Test-integrity checks
- **Mirror-implementation tests.** Two pins read the code rather than run it:
  `tests/unit/test_engine_address.py:122` (ContentView, which `swift test` cannot run) and
  `tests/unit/test_swift_tests_offline.py:97`. Both say so. The behaviour behind the second is also
  proven by an executed test (`OfflineTestCase.swift:201`, F12 red).
- **Golden test against a mirror.** The golden top 3 is derived by a Python script and computed by Swift
  `combineFamily`, two separate implementations held equal at `GoldenQuestionTests.swift:132`. F09 and
  F09b each turn red alone.
- **Weakened or deleted to green.** I checked from `e588910` (run product-night's base) to `ea04b05`: no
  test deleted, no manifest line removed, no skip or xfail added. Across the whole range the six removals
  in #281 are D-200 replacements (above). The manifest's 6 removed lines sit inside heavy-mode waves
  that had their own Testers.
- **Security-invariant tests.** None was weakened. INV-73's test was reworded with its invariant (#297,
  D-206 clause 4, owner-approved).

## Mocks / contract tests
- **No new external integration in (a).** The phone reaches the hosted engine through the same
  `EngineClient`, with the same URLProtocol stubs (`OfflineTestCase`, `DecliningStub`).
- **Live contract tests.** The engine's upstream clients added in the range (`arc_prize`,
  `models_dev`, `terminalbench`) have live contract tests in `tests/integration/test_scores_contract.py`.
  They are skipped without `RUN_CONTRACT_TESTS=1` and run in CI's contract job (`docs/skip-budget.txt`).
  Those heavy-mode waves' Testers covered them.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `conformance/lib_record.py:187` (`documents()`), read by `conformance/test-documented-paths.py`.
  - What is wrong: the gate grades untracked, gitignored Markdown under `build/`, the directory the rules
    name for a seat's scratch. Its PASS line says "files seen via git".
  - What happened here: `make check` went red on this seat's scratch notes.
  - Filed as **#325**: `bug`, `severity:low`, `Triage verdict: work-issue`. It is a gate change, so it
    is the owner's to approve.

## Tests added this review

- `tests/unit/test_golden_questions.py:209`
  - Proves: #294 (D-206 clause 3).
  - Red to green: red on the set as it stood before #310, green at head.
- `ios/EngineTests/KeptAnswerTests.swift:223`
  - Proves: #288, that an empty kept surfaces' list is nothing kept.
  - Red to green: red on G02, green at head.
- `ios/EngineTests/KeywordRoutingTests.swift:206`
  - Proves: #292, that a zip, promo or postal code is no coding object.
  - Red to green: red on G06, green at head.
- `ios/EngineTests/KeywordRoutingTests.swift:216`
  - Proves: #292, that a user agent or travel agent is no coding agent.
  - Red to green: red on G06b, green at head.
- `ios/EngineTests/KeywordRoutingTests.swift:76`
  - Proves: #301, now cited by its existing test (comment only).
- `ios/EngineTests/test-manifest.txt`
  - The three new Swift tests, regenerated with `swift test --list-tests | sort`.
  - The diff is exactly those three lines.

## Issues filed
- **#325**: test-documented-paths grades gitignored documents under `build/`, so a scratch note turns
  `make check` red. Labels `bug`, `severity:low`. `Triage verdict: work-issue`.
