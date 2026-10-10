---
record_type: review
id: m21-wave-3-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 Wave 3 Tester Review (the phone's promises, held further)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `origin/closure/m20..3c35ef5` (base `972b55e`). W3's own commits are the 49 first-parent,
non-merge commits of that range; W1 and W2 come in through the merges `97c4059` and `661426c` and are not
reviewed here. The worktree is detached at `3c35ef5`.
**Risk tier:** HIGH (plan §2, `docs/plans/m21-plan.md:53`)

Routing: the author and this seat are both Claude; no second family was available. The context is fresh.
This seat read the plan's W3 rows, the six review rounds, the commits and the code they touch. It read no
`*_heldout_*` file.

## Verdict
MINOR

The code does what its issues ask, and each issue has a test that fails when the code under it is broken:
- the held reading lives in the Engine and Swift tests drive it (#132);
- the six refusal codes are said in both languages (#223);
- the standings store dates what it keeps by its own clock (#170);
- the boards screen lays out its rows lazily (#219), and the device state is read again on `.active` (#220);
- the compiled gate refuses its fixture's new shapes (#168, #171 to #174, #188, #85) and fails on a Mac
  without Xcode (#175).

Every red commit fails only on its own tests, and the three Swift red commits compile.

Of 22 faults planted, the wave's tests catch 13. The 6 tests this review adds, and the one it extends,
catch 7 more, and they pass on the shipped code. The last 2 are overclaims written beside a register row's
fixed sentences or a PRD row's pointer, which the wording test says it does not read (R1).

Nothing blocks: each criterion has a citing test that asserts its behaviour, and no test was weakened to
go green. One red assertion was dropped in its fix, `5702663`, for a reason the commit gives (a privacy sink
calls no wording); what that leaves unsaid is M5.

Six MINOR findings remain, all of one kind: something the gate, the screen or the records hold today
with no test that fails when it stops. This review closes each one with a test. Two also need a comment
reworded (M3, M5), and M2 a change in the gate's self-test.

## How it was checked

- **The wave's tests.** `pytest` on `test_client_decl_gate.py`, `test_ios_client_contract.py`,
  `test_router_hints.py`, `test_security_invariants.py` and `test_error_codes.py`: **226 passed**, the
  Xcode-compiled fixture test included. With this review's tests: **232 passed**.
- **`make check-fast`, once, before anything was planted.** PASS in 99.1 s:
  - lint, typecheck and records passed;
  - test: `2432 passed, 25 skipped`, coverage-floor PASS (47 modules);
  - swift-test: 605 tests, exactly the manifest's;
  - client-decls passed.

  W3 touches no `src/` module, so the coverage floor has nothing of the wave's to measure.
- **`make client-decls`, once.** "client-decls PASS: 21 client file(s) in 4 configuration(s) --
  simulator, release: 2800; simulator, debug: 2805; device, release: 2800; device, debug: 2805".
- **The red commits.** Each of the 17 was extracted with `git archive` into its own scratch folder, given a
  git index (`git init`, `git add`; nothing committed) for the tests that read `git ls-files` (K1), and the
  worktree's `.venv` linked.
  - The whole `tests/unit` ran on each (`-n 6`); at `3c35ef5` the same set gives `2369 passed, 61 skipped`,
    0 failed.
  - The three Swift red commits ran the whole `swift test`; `scripts/router_probe/` is in each archive,
    beside `ios/`.
  - A red commit's own tests are the test functions its diff adds or changes. For a commit that changes
    the compiled gate's fixture, they also include the two self-test tests: the Xcode-compiled one and the
    committed-dump one.
- **Faults.** 22 were planted, one at a time, in a scratch mirror of `3c35ef5` (`git archive`, the
  worktree's `.venv` linked), never in the worktree.
  - Swift faults ran `swift test --filter` on the touched suites. Python faults ran the gate, pin and
    wording files (with `test_check_fast.py`, `test_error_codes.py` and `test_prd_citations.py`), and G11
    ran all of `tests/unit`.
  - Each planted file was restored by its bytes and its sha256 checked equal to the value before. All 22
    were equal.
  - Afterwards `diff -rq` of the mirror's `ios/`, `scripts/`, `docs/`, `tests/` and `Makefile` against the
    worktree shows no difference. The mirror's tests are this review's.
  - The worktree's `git status` shows only the three test files this review changed, and this file.

## Red→green on the red commits

| commit | suite | failed | all its own? |
|---|---|---|---|
| `23573d8` | pytest | 1: `test_every_code_the_engine_sends_has_a_sentence_on_the_phone` | yes |
| `23573d8` | swift (589) | 2: `testEveryKnownRefusalIsSaidInBothLanguages`, `testTheRateLimitSaysToWaitInTurkish` | yes |
| `ee47ea3` | pytest | 2: the lazy-rows and scene-phase pins | yes |
| `48eb939` | pytest | 2: the two self-test tests (#168's fixture shapes) | yes |
| `ac40b3d` | pytest | 2: the two self-test tests (#170's fixture shape) | yes |
| `ac40b3d` | swift (590) | 1: `testTheStoreDatesWhatItKeepsByItsOwnClock` | yes |
| `9f089d2` | pytest | 2: the two self-test tests (#174, #188) | yes |
| `545e7c3` | pytest | 1: `test_the_text_tripwire_reads_its_served_numbers_from_the_decoded_types` | yes |
| `b9060db` | pytest | 3: the toolchain test, the configuration test, the rule test | yes |
| `5222ecc` | swift (594) | 4: every `HeldReadingTests` test | yes |
| `1676c59` | pytest | 17: 14 new shapes, the over-refusal test, the two self-test tests | yes |
| `018c4eb` | pytest | 5: its 4 new shapes, the label-length test | yes |
| `fa2b5a7` | pytest | 4: the two self-test tests, and two older sink tests | see below |
| `826ab04` | pytest | 21: its 10 new shapes, its 6 new tests (9 cases), the two self-test tests | yes |
| `08f21f0` | pytest | 4: its 3 new shapes, the reflection test | yes |
| `5ab4077` | pytest | 2, the two it adds | yes |
| `be11e1a` | pytest | 3, the three it adds or changes | yes |
| `962af31` | pytest | 1: `test_no_record_restates_a_client_gates_property_without_its_row` | yes |
| `2d3a1e0` | pytest | 1: the same test, extended | yes |

- **`fa2b5a7`** plants five #172 routes, but two of them were already refused at the red commit: the
  stored default (`FixtureDefaulted.init`) and the kept closure (`holds `make``). The self-test there
  misses only `FixtureStatics.tag`, `threadDictionary` and `NotificationCenter`.
  - Because those two routes were already refused, two older tests fail on their "nothing else is refused"
    assertions: `test_a_sink_holds_nothing_another_file_can_change` and
    `test_a_sink_calls_nothing_another_file_declares_but_what_is_listed`.
  - `dbbc3a9` lets those two assertions accept exactly the two new plants. That is a correct update, not a
    weakening. Those two routes stand as guards, and `dbbc3a9`'s message claims only the other three.
- `826ab04` also adds `fact-nsnumber` and `served-dollar`, which pass at the red commit: they were
  already refused, and stand as guards. `5222ecc`'s five failures are four tests, one with two
  assertions.

## Faults planted

"Wave" is what the wave's own tests did; "now" is with this review's tests. Every file was restored by its
bytes, with sha256 equal (gate `1afb73dc8bd85729…`, `HeldReading.swift` `5cbbf1c5fc00a721…`, `Language.swift`
`830dda5a1c1521d2…`, `ContentView.swift` `6fbbfd8d58aa1c14…`, the register `fefa9108d8e464a2…`, the PRD
`ce88c6311fe93ed0…`, the Makefile `4465e2357f48648b…`).

| # | where | the fault | wave | now |
|---|---|---|---|---|
| G1 | `client_decl_gate.py:1722` | the request-argument rule (#174, #188) never refuses | RED, 5 tests (the six-shapes test among them) | RED |
| G2 | `client_decl_gate.py:279` | #170's `currentKept(now:fetch:)` leaves `PROVENANCE` | RED, the two self-test tests | RED |
| G3 | `client_decl_gate.py:1745` | a declared operator (#173) is not refused | RED, 3 (`custom-operator` among them) | RED |
| G4 | `client_decl_gate.py:854` | `SINK_SWIFT_REFUSED = ()` | **green** | RED, `test_a_sink_reads_none_of_the_standard_librarys_process_wide_state` (M4) |
| G5 | fixture `Imports.swift:4` | the fixture loses `import Network` | RED, the Xcode self-test | RED |
| G6 | fixture `ContentView.swift:232` | `keepAsked`'s `task = typed` (#188) becomes `_ = typed` | **green** | RED, the extended `test_the_gate_refuses_its_compiled_fixture` (M2) |
| G7 | `client_decl_gate.py:2004-2007` | the self-test's Release branch, its call and its expectation, removed | **green** | RED, `test_the_self_test_requires_the_release_rule_in_each_release_configuration` (M1) |
| G8 | `client_decl_gate.py:2006` | only the self-test's `release_problems` call removed | RED, the two self-test tests | RED |
| G9 | `client_decl_gate.py:2019` | `_host()` returns `platform.system().lower()` | **green** | RED, `test_a_mac_without_the_toolchain_fails_by_the_name_its_platform_gives` (M3) |
| G10 | `client_decl_gate.py:2058-2059` | `main` goes on past a missing toolchain | RED, `test_a_mac_without_the_toolchain_fails_the_gate_rather_than_skipping` | RED |
| G11 | `Makefile:212` | `-$(PY) -B scripts/client_decl_gate.py` (status ignored) | **green** (all of `tests/unit`) | RED, `test_make_client_decls_runs_the_gate_and_keeps_its_status` (M3) |
| I1 | `HeldReading.swift:17` | a `notASearch` reading is answered | RED, `testASearchIsAnsweredAndAnythingElseIsHeld` | RED |
| I2 | `HeldReading.swift:35` | the card asks back on anything but a search | RED, 2 tests | RED |
| I3 | `HeldReading.swift:30` | "No" keeps asking (`.unsure`) | RED, `testNoIsTheNote` | RED |
| I4 | `Language.swift:844` | `unknown_budget` says `unknown_task`'s Turkish | RED, `testEveryKnownRefusalIsSaidInBothLanguages` | RED |
| I5 | `Language.swift:810` | a known refusal is reworded in Turkish only | RED, the same test, 6 assertions | RED |
| I6 | `ContentView.swift:151` | the state is read again on `.background` | RED, `test_the_device_state_is_read_again_on_returning_to_the_foreground` | RED |
| I7 | `ContentView.swift:1555`, `:1575` | the screen's stack is a `VStack`; one row's stack is lazy | RED, `test_the_boards_screen_lays_out_its_rows_lazily` | RED |
| I8 | `ContentView.swift:882` | the failure view reads `error.errorDescription` (no language) | **green** | RED, `test_the_failure_view_says_the_error_in_the_readers_language` (M5) |
| W1 | `security-invariants.md:142` (INV-76) | "Every arithmetic on a served number is refused on the compiled module." added beside the row's fixed sentences | **green** | **green** (R1) |
| W2 | `prd.md:428` (REQ-APP-005) | "The compiled gate refuses every arithmetic on a served number." added beside the row's pointer | **green** | **green** (R1) |
| W3 | `security-invariants.md:189` (G-2) | G-2 becomes "The compiled arithmetic rule refuses every change of a served number" | **green** | RED, `test_each_gap_says_what_it_does_not_hold` (M6) |

The mirror has no `.git`, so `test_every_invariant_the_code_names_is_on_the_list` and five other tests that
read `git ls-files` fail there whatever is planted. They failed the same on the unplanted mirror, so they are
left out of the counts above (K1).

Kill rate (advisory; no mutation runner is wired): 13 of 22 with the wave's tests, 20 of 22 with this
review's.

## Acceptance-criterion coverage

- **REQ-GAP-001** (`docs/prd.md:553`) and **REQ-APP-005** (`docs/prd.md:428`), W3's rows (plan §1). Each
  issue the wave delivers:
  - **#85, #172** → `tests/unit/test_client_decl_gate.py:664` (`test_every_route_172_names_into_a_sink_is_refused`),
    `:697`; the self-test (`:59`, `:484`). Asserts each route is refused at its own file. GREEN.
  - **#168** → the self-test's `FIXTURE_REFUSALS` (`String`, `NSData`, `XMLParser` loading a URL; `:59`,
    `:484`), `:719`. GREEN.
  - **#169** → `tests/unit/test_ios_client_contract.py:2009`; `test_client_decl_gate.py:739`. GREEN. The
    text list equals the compiled one on the fixture only, as round 6's M3 records.
  - **#170** → `ios/EngineTests/StandingsStoreTests.swift:216`; the fixture's `Detail.swift` shape (the
    self-test). GREEN.
  - **#171, #173** → `test_client_decl_gate.py:643` (33 shapes, each at its own line), `:382`, and the
    allowances that follow it. GREEN.
  - **#174, #188** → `test_client_decl_gate.py:569` (six shapes, and the screen's own request allowed),
    `:708`. GREEN. Gap: M2 (a lost shape).
  - **#175** → `test_client_decl_gate.py:589`, `:600`, `:614`. GREEN. Gaps: M1, M3, M4, all closed here.
  - **#132** → `ios/EngineTests/HeldReadingTests.swift:16`, `:24`, `:30`, `:38`; the wiring pins in
    `test_ios_client_contract.py`. GREEN.
  - **#223** → `ios/EngineTests/LanguageTests.swift:550`, `:563`; `tests/unit/test_error_codes.py:30`,
    `:36`. GREEN. Gap: M5 (the screen's half), closed here.
  - **#219, #220** → `test_ios_client_contract.py:1983`, `:1997`, as round 1's M4 tightened them. GREEN.
    #220's battery half is the owner's.
  - **The records' wording** → `tests/unit/test_security_invariants.py:503`, `:523`, `:535`. GREEN. Gap: M6.

## Mocks / contract tests

No new integration. `test_error_codes.py` reads the engine's codes from `src/app/adapter/main.py`'s
`_error(status, "code", …)` calls and holds them equal to the phone's cases both ways. Every code the engine
sends goes through `_error` (`main.py:905`), so this is a source-level contract between the two sides.

## Findings

### BLOCKING
None

### MINOR

- **M1** `scripts/client_decl_gate.py:2004-2007` (the self-test's Release branch); G-10 at
  `docs/security-invariants.md:193` ("the Release configurations run their own rule on it").
  **Problem.** Only the self-test asks for the Release-only hook's refusal on the fixture. Nothing asks
  the self-test to keep asking.
  **Failure scenario.** G7: delete the four lines, the call and the expectation together. Every test, the
  Xcode self-test included, stays green. A later layout change that silences `release_problems` on the
  fixture would then pass `make client-decls`. `main` still runs the rule on the app
  (`test_main_refuses_a_release_dump_that_carries_a_ui_test_hook` holds that half).
  **Fix.** Done here: `tests/unit/test_client_decl_gate.py:769` silences the rule and requires the
  self-test to report it in the two Release configurations and in no other. It runs on the committed
  dump, so CI runs it too.

- **M2** `scripts/client_decl_gate.py:2010-2013` (one refusal per `(file, phrase)`) and `:1974-1987`
  (`DECLARED`, `_snapshot_drift`: declarations only).
  **Problem.** The fixture can lose a shape without anything noticing.
  - The self-test asks for any one refusal per pair. On the committed dump, 25 of the 66 pairs match more
    than one refusal line.
  - The dump is compared with the compile by kind, name and line only.
  - So a shape whose body changes, while another shape still carries its phrase, passes the self-test. The
    tests that count shapes (`:569`'s six, `:643`'s markers) then read a stale dump.
  **Failure scenario.** G6: `keepAsked`'s `task = typed` (fixture `ContentView.swift:232`, #188's "typed
  question kept as the surface") becomes `_ = typed`. The phrase `assigns `ContentView.task`` is still met
  by `:248`. The self-test and every test in the gate and pin files stay green, and the six-shapes test
  still counts six from the stale dump. A rule that later stopped refusing #188's own shape would go
  unseen too.
  **Fix.**
  - Done here, as a test: `test_the_gate_refuses_its_compiled_fixture` (`:59`, Xcode) now also requires
    the compiled fixture's refusals, and its Release refusals, to equal the committed dump's line for line.
  - In the gate itself: make `self_test` do the same comparison on configuration 0, so `make
    client-decls` fails as well as pytest. Then say so in G-10.

- **M3** `scripts/client_decl_gate.py:2017-2019` (`_host`); `Makefile:207-212` (`client-decls`), and
  `Makefile:211`'s comment.
  **Problem.** G-10's "fails rather than skip" is held in `main` only. Its two other links have no test.
  - `test_a_mac_without_the_toolchain_fails_the_gate_rather_than_skipping` replaces `_host` itself.
  - No test reads the recipe that `make check-fast` and `make check` run.
  - `Makefile:211` still says "SKIPPED, loudly, with no Xcode", which on a Mac is no longer true.
  **Failure scenario.**
  - G9: `_host()` returns `platform.system().lower()`. On the owner's Mac without Xcode the gate says
    SKIPPED and passes, and every test is green.
  - G11: the recipe's line becomes `-$(PY) …`. make prints "Error 1 (ignored)" and passes, and all of
    `tests/unit` is green.
  **Fix.**
  - Done here: `test_client_decl_gate.py:783` replaces only `platform.system`, and `:804` pins the recipe
    to the gate's one command, with nothing that drops its status.
  - Reword `Makefile:211`: "On a Mac without Xcode it fails (#175); on another host it says SKIPPED."

- **M4** `scripts/client_decl_gate.py:854` (`SINK_SWIFT_REFUSED`), used at `:1940-1942`.
  **Problem.** G-10 records that this rule has no fixture shape. It had no unit test either.
  **Failure scenario.** G4: `SINK_SWIFT_REFUSED = ()`. `CommandLine.arguments` read in `EngineClient.swift`
  passes the gate, and every test is green.
  **Fix.** Done here: `test_client_decl_gate.py:794` holds both sinks refused for `CommandLine`'s two
  members, and a file that is no sink allowed. G-10's sentence stays true: the rule still has no fixture
  shape.

- **M5** `ios/ModelRanking/ContentView.swift:882` (the failure view); `ios/ModelRanking/Engine/Language.swift:806-807`.
  **Problem.**
  - #223's Swift tests hold `errorDescription(_:)`. The only pin on the screen,
    `test_every_failure_the_client_names_reaches_the_screen_with_a_sentence`, asks for `.errorDescription`
    anywhere in a view.
  - `errorDescription(_:)`'s doc comment says the opposite of its code since `5702663`: "English is
    `errorDescription` itself, so the two cannot drift; the engine's own refusal is shown as it sent it, in
    either language". For the six known codes, English is the app's own sentence and the property keeps
    the engine's words. `5702663` dropped the red test's assertion for that reason, and left the comment.
  **Failure scenario.** I8: the failure view reads `error.errorDescription`. A Turkish reader then sees
    the engine's English for every refusal (`rate_limited` included), and every test is green.
  **Fix.**
  - Done here: `tests/unit/test_ios_client_contract.py:2029` pins the failure view to
    `error.errorDescription(language)`, and refuses the property there.
  - Reword the comment at `Language.swift:806-807`, for example: "What happened, in the reader's language.
    A refusal whose code this app knows is the app's own sentence, English too; for any other code, and in
    `errorDescription`, the engine's words are shown as it sent them."

- **M6** `tests/unit/test_security_invariants.py:401-416` (`table_problems`).
  **Problem.** The gaps table's words were read by no check. `table_problems` reads the Rows column and the
  count line, and `problems` reads the issue column.
  **Failure scenario.** W3: G-2 rewritten as "The compiled arithmetic rule refuses every change of a served
  number", with its catch-all gone. The whole wording test and `test_prd_citations.py` stay green.
  **Fix.** Done here: `gap_wording_problems` and `test_each_gap_says_what_it_does_not_hold`
  (`test_security_invariants.py:573`, `:588`).
  - A gap that says a rule or a list refuses something also says what is not held.
  - A gap about a compiled rule (G-1, G-2, G-11) carries its fixture's catch-all, and marks its examples
    as not a complete list.
  - Each refusal is watched failing on a planted G-2.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_security_invariants.py:30` (`tracked`); `tests/unit/test_prd_citations.py:47`;
  `tests/unit/test_security_surface.py:30`, `:230`; `tests/unit/test_skip_budget_local.py:91`.
  **Problem.** Six tests call `git ls-files` with `check=True` and carry no `needs("git")` marker.
  `test_no_tracked_links.py:19` carries it, and `tests/skips.py` defines it.
  **Failure scenario.** In a tree extracted with `git archive` (how the Testers build red commits), those
  six fail with `CalledProcessError` instead of skipping. Measured on this review's mirror, before any
  plant.
  **Fix.** Mark the six `needs("git")`. CI has a checkout, so its skip budget does not change.

## Risks queued to next M

- **R1** `tests/unit/test_security_invariants.py:273-274` (the wording test's stated limit), with M6 here.
  **The risk.** The wording test holds that a gated row carries its fixed sentences and a PRD row its
  pointer. It does not hold that nothing more is said. W1 and W2 stayed green: a flat "every arithmetic on
  a served number is refused" written beside INV-76's sentences, and beside REQ-APP-005's pointer.
  **What would show the risk is real:** a later record or PRD edit that restates a gate's property next
  to its pointer, found by a reader rather than a test. #248's sweep is the place to decide whether a
  check of a row's other sentences is worth its false alarms. This seat measured that every gated row
  carries other sentences, and some of them say "refused" of a property (INV-71) or "held on the compiled
  module by nothing" (INV-62).
- **R2** G-10 and #243. M2's line-for-line check runs only where Xcode is (M1's runs on CI too, on the
  committed dump). On CI's Linux lane a stale dump is still read as the fixture.

## Tests added/extended this review

- `tests/unit/test_client_decl_gate.py:59` `test_the_gate_refuses_its_compiled_fixture`, extended: the
  compiled fixture is refused line for line as the committed dump is (M2, G6). Xcode; no new skip, so
  the skip budget is unchanged.
- `test_client_decl_gate.py:769` `test_the_self_test_requires_the_release_rule_in_each_release_configuration`
  (M1, G7).
- `test_client_decl_gate.py:783` `test_a_mac_without_the_toolchain_fails_by_the_name_its_platform_gives`
  (M3, G9).
- `test_client_decl_gate.py:794` `test_a_sink_reads_none_of_the_standard_librarys_process_wide_state` (M4, G4).
- `test_client_decl_gate.py:804` `test_make_client_decls_runs_the_gate_and_keeps_its_status` (M3, G11).
- `tests/unit/test_ios_client_contract.py:2029` `test_the_failure_view_says_the_error_in_the_readers_language`
  (M5, I8).
- `tests/unit/test_security_invariants.py:588` `test_each_gap_says_what_it_does_not_hold`, with
  `gap_wording_problems` (`:573`) (M6, W3).

No Swift test was added (every Swift fault went red), so `ios/EngineTests/test-manifest.txt` is unchanged.

Each test passes on the shipped code, and each goes red on its fault in the mirror:
- the five wave and pin files: `232 passed`;
- all of `tests/unit` (`-n 6`): `2427 passed, 9 skipped`, 0 failed;
- `make lint` (`ruff check src tests scripts`): all checks passed.
