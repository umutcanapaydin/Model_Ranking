---
record_type: review
id: m19-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# M19-W3 Code Review: the gates see before the push

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `133a525e8e77755c913e6442ed7a343563fb0a29..f393bc4` (14 commits; 40 files, +895 / -92).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:80`, `docs/plans/m19-wave-3-plan.md:13-17`). Gate
definitions change, and the diff touches `tests/conftest.py`, a security glob (`m19-plan.md:131`). By
D-172 no security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile,
`.agents/rules/practices.md` and the `writing-a-control` skill from `origin/main`. Then I read the
milestone plan (§1 W3, §2 W3, §3, the W3 amendment), the wave plan, and the six issues with their
comments. Then I read the diff. I read the commit messages last.

**Summary.** The wave delivers all six issues. Each new check has a red test and a fix. `make
check-fast` passes in this seat, and its test leg ran inside the offline profile. The derived skip
count matches CI: 82 = CI's last 81 on `main` + the one new `needs("offline")` test, over 2078 tests
= CI's 2057 + the 21 the wave adds. The #149 reading holds up: on a one-thread cooperative pool,
`SlowTierTests` still passes. Nothing blocks.

Each control was probed with planted inputs and four code mutants. Most of the holes are the same
kind: **a check reads one spelling of the thing it guards, not the thing itself.** Ten MINORs:

1. **M1.** Three other skip spellings slip past both #137 checks. An `xfail` is one of them, and CI
   counts it as a skip.
2. **M2.** The #140 HIGH rule passes a MED close whose footprint uses the brace form this repo's
   closes already use.
3. **M3.** The #140 parsers read one shape. An own-milestone `M19-W6`, or a glob bullet that wraps,
   goes unseen.
4. **M4.** Nothing holds the two new callers. Remove `--derive` from `make test`, or
   `headless_waves` from `wave_check_all.main`, and every test still passes.
5. **M5.** INV-6 and G-5 say "every child process included". The profile leaves the system
   resolver open, so a child's name lookup still leaves the machine.
6. **M6.** A `UNAME_S` variable in the environment removes the sandbox on a Mac, and no gate
   notices.
7. **M7.** The #149 starvation test cannot fail on the defect its message names. A router that
   waits out the model passes it.
8. **M8.** #117 matches a Turkish word with its suffixes only if the word has a Turkish letter. On
   M18-W3's real tree it flags 9 of the review's 11 phrases. The committed fixture is a stand-in.
9. **M9.** The #108 guard is two spellings. INV-6 says "no Swift source builds" one. A typealias, a
   subclass or a metatype `.init()` passes.
10. **M10.** The wave's three design choices have no ADR (AGENTS.md §3.4). W2's design choices
    each got one.

## Verdict

MINOR

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `tests/unit/test_skip_budget_local.py:57` (`RAW_SKIP`), `tests/skips.py:11`. **The rule
  that keeps the derived count whole is a spelling list, and three common spellings pass it.**
  `skips.py:11` says "No test skips any other way". The scan refuses `pytest.skip(`,
  `pytest.mark.skip`/`skipif` and `pytest.importorskip(`. It does not see `@pytest.mark.xfail`,
  `pytest.xfail(`, `unittest.skip*`/`self.skipTest`, or `from pytest import mark, skip`
  (`@mark.skipif`, `skip(...)`). CI's JUnit report counts every one of them as skipped.
  - **Planted** (scratchpad files, outside the repo). Five tests: one `xfail`, one `unittest.skipIf`,
    one `skipTest`, one `@mark.skipif` and one bare `skip()` after `from pytest import`.
  - `coverage_floor.py --derive tests <planted>` said "CI will skip 82 of 2083" and exited 0.
  - A real run of the same five wrote `tests="5" skipped="5"`. The xfail was typed
    `pytest.xfail`. `coverage_floor.counts()`, CI's reader, returned `(5, 5)`. So CI would count 87
    against a budget of 82.
  - `RAW_SKIP` matched none of the five files.
  - None of these spellings is in the tree today (`grep` finds no `xfail`, `skipTest`,
    `unittest.skip` or `from pytest import`). This is a hole, not a live miss.
  - **Fix.** Make the rule runtime-derived as well as spelled. A conftest hook can fail the run when
    a test is reported skipped or xfailed for any reason that `skips.apply` did not set. At minimum,
    add `xfail` and the `unittest`/from-import forms to the scan, and write one planted case per
    spelling.
- **M2** `scripts/wave_check.py:307-308` (`_glob_problems`). **A MED close passes when its footprint
  writes a security-glob path in brace form or as a directory.** The rule splits `Touched:` on
  whitespace and `fnmatch`es each token.
  - **Planted** through the wave's own helper (`test_wave_check_m19_rules._close`, tier MED, the
    plan's globs). `ios/ModelRanking/Engine/EngineClient.swift`, `… (new)`, `…, docs/x.md` and
    `tests/conftest.py` were each refused (exit 1).
  - `ios/ModelRanking/Engine/{EngineClient,Router}.swift` passed (exit 0). So did
    `ios/ModelRanking/Engine/`.
  - The brace form is already in use: `docs/plans/m19-wave-2-close.md:101`
    (`scripts/client_decl_fixtures/{Combine,…}.swift`) and `m18-wave-1-close.md:73`.
  - The root is the rule's subject (writing-a-control question 3). It reads the footprint the closer
    typed, not the diff. The signed footer already names the commit range.
  - **Fix.** Read `git diff --name-only <range>` from the footer, or compare the footprint with it.
    Failing that, expand braces and refuse a token that holds `{`, `*` or a trailing `/`.
- **M3** `scripts/wave_check_all.py:113`, `:130`, `:133`; `scripts/wave_check.py:292-294`. **Both
  #140 parsers read one layout and fail open on others.**
  - `headless_waves` reads only paragraphs that start with `**Amendment`. In them it reads only a
    bare `W<n>`, because `(?<![\w-])` drops `M19-W6`, the plan's own wave with its prefix. Planted
    on a temp plan, these were **not flagged**: `M19-W6 joins` in an amendment, an amendment that
    is not bold, an `### Amendments` list, `Wave 6` spelled out, and a `| **W6** |` table cell. The
    plain `W6` control was flagged.
  - `plan_globs` stops at the first line that is not an indented bullet. Planted: a glob bullet that
    wraps onto a second line. The reader returned two of four globs. `EngineClient.swift` and
    `tests/conftest.py` were silently dropped, which makes the rule narrower with no error.
  - Every M18+ amendment today is a bold `**Amendment` paragraph with a bare `W<n>`, and M19's list
    reads all ten globs, so nothing is missed on the tree.
  - **Fix.** Count `M<this>-W<n>` as this milestone's wave, and read every `W<n>` the plan names, not
    only those in amendments. For the glob list, read continuation lines, or fail closed on a line
    inside the list that is neither a bullet nor blank.
- **M4** `Makefile:116`; `scripts/wave_check_all.py:196`. **The two new callers are held by no
  test.** writing-a-control says "give it a caller". The callers exist, but nothing fails if one is
  removed.
  - **Planted, removal of the `--derive` line from `make test`.** All 8 test files that name the
    Makefile or `coverage_floor`: 117 passed.
  - **Planted, `main()` without `*headless_waves(ROOT)`.** All 4 test files that name
    `wave_check_all`: 61 passed.
  - The precedent holds the same kind of wiring: `module_coverage_floor.py`'s place in `make test`
    is pinned by `tests/unit/test_check_fast.py:53` and `test_wave_check_versions.py:97`.
  - **Fix.** One test that reads the `test` recipe for `coverage_floor.py --derive`. One that runs
    `wave_check_all.py` on a planted root and sees the heading-less wave named.
- **M5** `docs/security-invariants.md:149` (INV-6), `:175` (G-5); `scripts/offline.sb:3-4`, `:10`.
  **The record says the macOS run is offline "every child process included". The profile leaves the
  system resolver open, so a child's name lookup still leaves the machine.**
  - `(allow network-outbound (remote unix-socket))` admits `/var/run/mDNSResponder`. The profile's
    own comment says so: "the resolver's".
  - **Measured inside the profile.** A child's UDP connect to TEST-NET-1 was refused. A `connect()`
    to `/var/run/mDNSResponder` succeeded (no query was made, so no packet was sent). A child's
    `getaddrinfo` reaches the network through that daemon.
  - The pytest process refuses name lookups (M18-W7). So the new child half is narrower than the
    in-process half that INV-6 already claimed.
  - The same `(allow default)` also leaves Mach services open. For example, `open <url>` hands the
    URL to LaunchServices, outside the sandbox. I did not run this; the owner's rules forbid it.
  - **Fix.** Deny the resolver socket and measure that the loopback tests still pass, or say in
    INV-6 and G-5 that connections are refused and name lookups are not.
- **M6** `Makefile:96`. **A `UNAME_S` in the environment turns the macOS sandbox off, and nothing
  fails.** `UNAME_S ?=` takes an environment value.
  - **Measured on this Mac** (`uname -s` = Darwin): `UNAME_S=Linux make -n test` prints the pytest
    line without `sandbox-exec` and without `MODEL_RANKING_REQUIRE_OFFLINE`, so the conftest
    refusal never runs.
  - The `needs("offline")` test then skips locally. `--derive` still passes, because it counts by
    CI's flags. This needs an unlikely variable, but it is a fail-open path in a HIGH gate.
  - **Fix.** `UNAME_S := $(shell uname -s)`. A command-line override, which
    `test_offline_run.py:40` uses, still works; an environment value does not. Or have the conftest
    refuse a `make test` run (`MODEL_RANKING_REQUIRE_ARTIFACT=1`) on `sys.platform == "darwin"` that
    is not offline.
- **M7** `ios/EngineTests/FrontDoorTests.swift:556-576`, `ios/EngineTests/TierStubs.swift:48`.
  **`testTheDeadlineIsHeldWhenTheProcessIsStarved` cannot fail on the defect its message names**
  ("the deadline was waited out by the call it exists to abandon").
  - It stops the process for 6 s and allows a 4 s margin. That is about `HangingTier`'s 10 s, so a
    router that waits for the model finishes inside the bound.
  - **Planted** in `Router.swift` `firstWithin`, restored byte-identical: await the work, then drop
    a late result. This is the structured-wait defect the function's own comment describes.
  - `testAModelTierThatNeverAnswers…` caught it: "10.0739… is not less than 4.2071…".
    `testTheCallThatMissesTheDeadlineIsCancelled` caught it too.
  - The starvation test **passed** (10.051 s). It was only ever red against the old absolute 5 s
    bound (`a0d58a9`). It guards the test's bound, not the router.
  - **Fix.** Give this test a hanging tier longer than stop + margin (for example 30 s; the correct
    router cancels it at once). Then watch it red on the planted mutant and still red on the old
    5 s bound.
- **M8** `tests/unit/test_ios_client_contract.py:1546`, `:1552-1563`, `:1590`, `:1494-1502`. **#117
  treats a word as Turkish only if it has a Turkish letter, or its list is named Turkish/stems or
  matched with `hasPrefix`. The fixture is not M18-W3's case.**
  - **Replayed** on M18-W3's real tree (`6a8038e`: its `Reading.swift`, its probe sets, its three
    live held-out sets). The check flags 9 of the first review's 11 phrases, plus `naber`. It misses
    `sistem komut` and `gizli ayar`. Their held-out rows carry each with a suffix (the first as
    `komut` + `unu`; the second as `ayar` + a plural and possessive suffix), and neither entry has
    one of the six letters `TURKISH_LETTER` looks for (U+00E7, U+011F, U+0131, U+00F6, U+015F,
    U+00FC). The app then matched them as substrings (`folded.contains`).
  - So the plan's "a Turkish word also matched with its suffixes" (`m19-wave-3-plan.md:37`) holds
    only for Turkish words spelled with Turkish letters.
  - The committed red case (`:1494`) is an invented two-entry list, not "M18-W3's case as a fixture"
    (P5, `m19-wave-3-plan.md:48`).
  - The check also reads lists only. The inline literals `"background"`, `"arka"`, `"plan"` and
    `"draw"` (`Reading.swift:153`, `:159`, `:165`) are signal words that no list holds.
  - **Fix.** Take each list's match mode from how the app matches it (substring or `hasPrefix` →
    stem), or treat every non-English entry as a stem. Commit M18-W3's 27 phrases and sets as the
    fixture, and read single literals compared with `==` or `hasPrefix`.
- **M9** `tests/unit/test_swift_tests_offline.py:95-118`; `docs/security-invariants.md:149`. **The
  #108 guard refuses two spellings. INV-6 says "No Swift source builds a bare
  `URLSessionConfiguration()`", and the test is named "…in any spelling".**
  - **Planted** through `_bare_configurations`. Refused: `URLSessionConfiguration()` and
    `Foundation.URLSessionConfiguration()`.
  - **Passed:** `typealias Config = URLSessionConfiguration; Config()`,
    `URLSessionConfiguration.self.init()`, `type(of: URLSessionConfiguration.default).init()`,
    `let make = URLSessionConfiguration.init; make()`, a subclass `Quiet()`, and
    `` `URLSessionConfiguration`() ``.
  - This is the W-122 lesson: six word lists were each bypassed before `client_decl_gate.py` read
    the compiler's view.
  - **Fix.** Hold it on resolved declarations (the compiled gate can refuse the base `init`), or
    narrow INV-6's sentence and the test name to the two spellings refused.
- **M10** `docs/decisions.md` (no new ADR); `docs/plans/m19-plan.md:226-232`,
  `docs/plans/m19-wave-3-plan.md:31-38`. **Three non-trivial choices are recorded only as plan
  prose.** AGENTS.md §3.4 says "Non-trivial choices → new ADR". W2's gate designs became D-180 and
  D-181. This wave chose three things:
  - `make test` runs inside `sandbox-exec` on macOS, and a run that says it must be offline refuses
    to start (#122 option B, a gate-definition change);
  - every Python skip goes through `needs`, enforced by a scan (#137);
  - #117's matching rule.
  - **Fix.** Write one ADR, `proposed`, through `/log-decision`, with the M5 and M8 limits stated.

### PASS (what looks good)

- **Each check fails closed on its own errors.**
  - **Derive**, exit 2 when the count cannot be taken (planted `needs("bogus")`:
    `UsageError` → "CANNOT RUN … exit 4"). Exit 1 on an unset budget (planted). Exit 2 when
    collection fails or collects no test (`coverage_floor.py:86-95`).
  - **Offline run.** A planted profile without its `deny` line: the run stopped before any test,
    exit 4 (`tests/conftest.py:278-284`).
  - **Glob rule.** No plan, or a plan with no glob bullet, is refused
    (`test_wave_check_m19_rules.py:118`).
- **The derived count is right today.** It is 82 of 2078, broken down as artifact 52, contract 18,
  epoch 7, macos 2, offline 1, xcode 2. This matches CI on `main` (`gh run 37511472120`: "81
  skipped of 2057", both Pythons) plus the wave's 21 new tests, one of which needs `offline`.
  - The local run's 25 skips are all `needs …` reasons (`build/check-fast/test.log`).
  - `docs/skip-budget.txt`'s breakdown sums to 82.
- **Two-sided tests.**
  - Derive: quiet on the tree (`test_skip_budget_local.py:27`), red one above (`:34`), red when the
    budget is too high (`:45`). The raw-skip scan had 23 hits at the red commit `3f1bc30` and 0 at
    `08df6f4`.
  - Glob rule: red on MED + glob (`test_wave_check_m19_rules.py:111`), quiet on HIGH + glob and
    on MED off the globs (`:124`).
  - `headless_waves`: red on amendment, table and open milestone (`:55`, `:64`, `:71`). Quiet on
    `M17-W5` and `W-108` (`:78`).
- **Real counts, not flags, for CI's skips.** `NEEDS` (`tests/skips.py:57-80`) is a named entry
  per need, each with CI's state and a reason.
  - Counting is by `in_ci`, not by what this machine has. So `RUN_CONTRACT_TESTS` or
    `EPOCH_DATA_DIR` set locally does not move the count.
  - An unknown need is a usage error, not a silent zero.
- **The #149 reading is supported by a measurement.** `firstWithin` only suspends
  (`Router.swift:739-756`).
  - `HangingTier` sleeps with `Task.sleep`.
  - `SlowTierTests` passes with `LIBDISPATCH_COOPERATIVE_POOL_STRICT=1`, a one-thread pool: 7
    tests, 0 failures. A race that blocked its thread would stall there.
  - The relative bound in `testAModelTierThatNeverAnswers…` (`FrontDoorTests.swift:525-538`) is
    still sensitive when the machine is idle (M7's mutant: 10.07 s against 4.21 s).
- **#108 was read, not trapped.** The reading is on the issue, the issue stays open for the
  measurement, and no probe trapped a process.
- **The record matches the code otherwise.**
  - The W3 amendment's five "added after" entries are the five `_AFTER` rows (`:1539-1543`).
  - #177 and #178 exist and are open.
  - #122 carries the CI patch, honestly marked "not run by the agent".
  - G-5 narrows to CI.
  - I checked every `HELD_OUT_ONLY_REVIEWED` "before"/"after" note against the commit order
    (`git merge-base --is-ancestor`). All hold.
- No drive-by edits outside the six issues. No swallowed exceptions. No new third-party import.
  The commits carry the owner's identity and the `GP-Agent` / `GP-Task` trailers, with no AI
  attribution.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code:

- **INV-6 (no test reaches the network).**
  - The pytest process: sockets, datagrams, name lookups, proxies (M18-W7). Citing tests:
    `tests/unit/test_no_network.py::test_a_planted_real_request_fails_the_test`,
    `::test_the_other_socket_doors_are_closed_too`, `::test_a_system_proxy_reaches_no_unit_test`
    and the rest of INV-6's list.
  - Child processes of a Python test, **on macOS**: `scripts/offline.sb` via `Makefile:97`, `:108`.
    Citing tests: `tests/unit/test_offline_run.py::test_a_child_process_the_suite_starts_cannot_name_an_outside_peer`
    (Python with a scrubbed environment, and `curl`); `::test_make_test_runs_the_suite_offline_on_macos`;
    `::test_a_run_that_must_be_offline_and_is_not_stops_before_any_test`; loopback kept by
    `::test_a_child_process_still_reaches_loopback`. IPv6 loopback measured open too.
  - Child processes of a Python test, **in CI**: none until the owner applies #122's patch (G-5).
  - A child's **name lookups** through the system resolver (macOS): none (M5).
  - Work a child hands to a **system service** (LaunchServices, XPC): none (M5; reasoned, not run).
  - Swift tests, in-process `URLSession`: `ios/EngineTests/OfflineTestCase.swift::testARequestNoStubAnswersIsCaughtWithoutLeavingTheMachine`,
    `::testEverySessionConfigurationAsksTheTripwireFirst`; every class on the base:
    `tests/unit/test_swift_tests_offline.py::test_every_swift_test_class_derives_from_the_offline_base`.
  - Swift bare configuration (#108): `test_swift_tests_offline.py::test_no_swift_source_builds_a_bare_session_configuration`
    (two spellings, M9). Background session: `::test_no_swift_source_builds_a_background_session`.
  - **Swift test child processes.** This wave adds the first `Process()` in the Swift bundle
    (`FrontDoorTests.swift:560`). The Swift legs run outside `offline.sb`, and the tripwire is
    in-process. Covered by neither (K1).
- **CI's skip count = the budget (#137).** Producers of a skip:
  - a `needs` / `artifact` marker, counted (`tests/skips.py:97-114`);
  - a raw `pytest.skip`/`skipif`/`importorskip`, refused by the scan
    (`test_skip_budget_local.py:60`);
  - `xfail`, `unittest` skips and from-import spellings: none (M1).
- **A close is required for every wave (#140)** comes from headings. Wave names come from headings,
  `**Amendment` paragraphs and first-column table cells (`test_wave_check_m19_rules.py:55-83`).
  Other layouts: none (M3).
- **A diff touching a glob is HIGH (#140).** It is read from the typed footprint: brace and directory
  forms, none (M2). The diff itself: none (M2's root).

Gaps: G-5 (CI), M1, M2, M3, M5, M9, K1.

## Acceptance criteria evidence (REQUIRED for PASS verdict)

W3 has no REQ-IDs ("none new (controls)", `m19-plan.md:40`). The criterion is "A wave sees CI's skip
count, its wave and tier gates, and a child process's network before it pushes. Each new check is
shown red." By phase (`m19-wave-3-plan.md:44-48`):

- **P1, #137**:
  - Markers: `tests/skips.py:57-80`, `:87-114`; `tests/conftest.py:220-226`, `:293-295`.
  - Derive: `scripts/coverage_floor.py:70-106`. Caller: `Makefile:116`.
  - Tests: `tests/unit/test_skip_budget_local.py:27` (quiet on the tree, cites REQ-CI-001), `:34`
    (planted artifact test, red), `:45`, `:60` (raw skip; red at `3f1bc30`).
  - The scan's 23 raw skips at `3f1bc30` are gone at `08df6f4`, converted to `needs` in the 18
    test files listed below and `tests/conftest.py`. Holes: M1, M4.
- **P2, #140**:
  - `scripts/wave_check_all.py:113-136`, `:196`; tests `test_wave_check_m19_rules.py:55`, `:64`,
    `:71`, `:78`.
  - `scripts/wave_check.py:277-311`, `:411-412`; tests `:111` (MED close on `EngineClient.swift`,
    red), `:118` (no globs, fail closed), `:124`, `:132`.
  - Holes: M2, M3, M4.
- **P3, #122**:
  - `scripts/offline.sb:6-10`; `Makefile:95-108`; `tests/conftest.py:278-284`.
  - Tests: `tests/unit/test_offline_run.py:45`, `:52`, `:64`, `:76`. Red at `ea24722`.
  - The CI patch is posted on #122. G-5 is narrowed at `docs/security-invariants.md:175`. Holes:
    M5, M6.
- **P4, #149**:
  - The reading is recorded at `ios/EngineTests/FrontDoorTests.swift:514-516` and `:550-555`. The relative bound
    is at `:517-538`, the starvation test at `:556-576`.
  - Red against the old bound at `a0d58a9`. Hole: M7.
- **P5, #117**:
  - `tests/unit/test_ios_client_contract.py:1494` (fixture red), `:1505` (matching), `:1515` (tree,
    exact list), `:1531-1594`. #177 is filed. Hole: M8.
- **P5, #108**: `tests/unit/test_swift_tests_offline.py:95`, `:109`, `:118`; the reading is the
  #108 comment, and the issue is open. Hole: M9.

## Every file in the diff

| File | What changed | Read |
|---|---|---|
| `Makefile` | `UNAME_S`, `OFFLINE_RUN`; `make test` runs in `offline.sb` on macOS and calls `--derive` | M4, M6 |
| `docs/plans/m19-plan.md` | the W3 amendment | M10 |
| `docs/plans/m19-wave-3-plan.md` | the wave plan (new) | ok |
| `docs/security-invariants.md` | INV-6 widened; G-5 narrowed to CI | M5, M9 |
| `docs/skip-budget.txt` | 81 → 82, the `offline` row, "checked twice" | ok (sums to 82) |
| `ios/EngineTests/FrontDoorTests.swift` | `plainTimer`, the relative bound, the SIGSTOP starvation test | M7, K1, R1, R3 |
| `ios/EngineTests/OfflineTestCase.swift` | comment: #108 refused by the source | ok |
| `ios/EngineTests/test-manifest.txt` | the new Swift test | ok |
| `scripts/coverage_floor.py` | `--derive` | M1 |
| `scripts/offline.sb` | the profile (new) | M5 |
| `scripts/wave_check.py` | `plan_globs`, `_glob_problems`, dated from 2026-10-06 | M2, M3 |
| `scripts/wave_check_all.py` | `headless_waves`, wired into `main` | M3, M4 |
| `tests/conftest.py` | `--ci-skips-report`; `needs` registered; offline refusal; collection through `skips.apply` | ok |
| `tests/skips.py` | `NEEDS`, `offline()`, `apply` (new) | M1, R2 |
| `tests/integration/test_arena_openrouter_contract.py`, `test_epoch_bundle_contract.py`, `test_litellm_contract.py`, `test_scores_contract.py` | `skipif(RUN_CONTRACT_TESTS)` → `needs("contract")` | ok |
| `tests/unit/test_api_config.py`, `test_startup_schema_validation.py` | runtime artifact skip → `needs("artifact")` | ok |
| `tests/unit/test_client_decl_gate.py` | `skipif(xcrun)` → `needs("xcode")` ×2 | ok |
| `tests/unit/test_deepswe_workflow.py`, `test_effort.py`, `test_epoch_ingest.py`, `test_epoch_workflow.py`, `test_m5_board_measurement.py` | Epoch skips → `needs("epoch")`; the helper reads the variable directly | ok |
| `tests/unit/test_health_memo.py` | root skip → `needs("not_root")` | ok |
| `tests/unit/test_no_network.py` | macOS skips → `needs("macos")` | ok |
| `tests/unit/test_no_tracked_links.py` | git skip → `needs("git")` | ok |
| `tests/unit/test_ui_test_refuses_a_real_old_artifact.py`, `test_ui_test_refuses_an_old_artifact.py`, `test_ui_test_script.py` | bash/curl skips → `needs("bash_curl")` | ok |
| `tests/unit/test_unavailable_after_boot.py`, `test_why_facts.py` | comment only | ok |
| `tests/unit/test_proxy_rule_and_workers.py` | copies `skips.py` beside the copied conftest | ok |
| `tests/unit/test_ios_client_contract.py` | `RETIRED_HELD_OUT` shared; the #117 check (3 tests) | M8, K2 |
| `tests/unit/test_offline_run.py` | #122's tests (new) | M5, M6 |
| `tests/unit/test_skip_budget_local.py` | #137's tests (new) | M1, M4 |
| `tests/unit/test_swift_tests_offline.py` | #108's source check | M9 |
| `tests/unit/test_wave_check_m19_rules.py` | #140's tests (new) | M2, M3, M4 |

## K.8 contract drift check

The wave plan's contracts (`m19-wave-3-plan.md:53-67`), `grep -n` at `f393bc4`:

```
scripts/coverage_floor.py:44:DEFAULT_BUDGET = ROOT / "docs" / "skip-budget.txt"
scripts/coverage_floor.py:47:def read_budget(path: pathlib.Path) -> int | None:
scripts/wave_check_all.py:79:def missing_closes(root: pathlib.Path) -> list[str]:
scripts/wave_check_all.py:116:def headless_waves(root: pathlib.Path) -> list[str]:
scripts/wave_check.py:280:def plan_globs(plan: pathlib.Path) -> list[str]:
scripts/wave_check.py:315:def main(argv: list[str]) -> int:
Makefile:99:test: install  ## pytest in parallel, with the served artifact required, offline on macOS (another stack: STACK_TEST)
Makefile:128:check: lint typecheck test check-records check-records-selftest install-check harvest-context-check shell-dialect wave-check-all conformance swift-test client-decls  ## the offline half of the gate, one leg after another (the post-edit hook runs check-fast)
tests/conftest.py:220:def pytest_addoption(parser: pytest.Parser) -> None:
tests/conftest.py:225:def pytest_configure(config: pytest.Config) -> None:
tests/conftest.py:293:def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
ios/ModelRanking/Engine/Router.swift:277:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/EngineTests/FrontDoorTests.swift:511:final class SlowTierTests: OfflineTestCase {
```

- Every declared symbol exists with the same name and signature.
- Line moves come from additive edits above them. `check:`'s legs are unchanged, and `test:` gains
  the offline wrapper and `--derive`, as planned.
- `git diff 133a525..f393bc4 -- src/ ios/ModelRanking` is empty. No `/v1` field or route changes,
  and `Router.swift` is untouched.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `Makefile:143-203` (`swift-test`, `swift-test-parallel`); `ios/EngineTests/FrontDoorTests.swift:560`.
  **A child process of a Swift test is under neither guard.** The tripwire is in-process. The Swift
  legs run outside `offline.sb`. This wave adds the bundle's first `Process()`; it is harmless, but
  nothing would stop the next one from running `curl`. Measured:
  - `sandbox-exec -f scripts/offline.sb swift test` fails: SwiftPM sandboxes its manifest build,
    and the two sandboxes cannot nest.
  - With `swift test --disable-sandbox` inside the profile, `SlowTierTests` ran 7 tests, 0 failures.
  - An enhancement: wrap the Swift legs that way, or add a source check that names each `Process()`
    in `ios/EngineTests`.
- **K2** `ios/ModelRanking/Engine/Router.swift:159` (`CategoryHints.examples`). **The wording tier's
  hint sentences are tuned text that the #117 check does not read.** A phrase only a live held-out
  set holds can enter them unflagged. The whole-question gate catches only verbatim questions. An
  enhancement: run `_held_out_only_signals` over the hint strings as well.

## Risks queued to next M

- **R1** `ios/EngineTests/FrontDoorTests.swift:517-538`. **The control timer shares the cooperative
  pool with the router.** A future change that blocks pool threads would make both late, and the
  relative bound would pass. "No app code blocks a thread" is held by reading. Here, the one-thread
  pool run passed, but no gate runs it. What would show the risk is real: `SlowTierTests` failing or
  hanging under `LIBDISPATCH_COOPERATIVE_POOL_STRICT=1`, or a `check-fast` deadline miss with the
  plain timer on time. (Adding that environment variable to one Swift run would hold it.)
- **R2** `tests/skips.py:57-80`. **`in_ci` is kept by hand beside `.github/workflows/ci.yml`.** When
  CI gains a need (#122's patch, a macOS runner, a fixture-built artifact), the derive and CI
  disagree until someone flips the flag. The #122 comment already plans this for `offline`. What
  would show it: `--derive` green with CI's budget step red, or the reverse.
- **R3** `ios/EngineTests/FrontDoorTests.swift:563`. **Every Swift run now SIGSTOPs its test process
  for 6 s.** If the `sh` child dies between `STOP` and `CONT`, the worker stays stopped, and the
  Swift legs have no timeout. What would show it: a hung `swift-test` leg with an `xctest` in state
  `T`.

## Gates and probes run

- `make check-fast` with the guard-bin stubs on `PATH`: **PASS** in 95.1 s.
  - Lint, typecheck, records (`wave-check-all`, conformance 16/16) and client-decls passed.
  - Test leg: run as `MODEL_RANKING_REQUIRE_OFFLINE=1 /usr/bin/sandbox-exec -f scripts/offline.sb …
    pytest -n auto`. 2053 passed, 25 skipped; the offline test ran. Then `--derive`: "CI will skip
    82 of 2078 … budget … 82".
  - swift-test-parallel: 469 tests, each in the manifest.
- The wave's six test files inside the profile: 81 passed.
- **Code mutants**, each planted with Python and restored byte-identical (checked by comparing
  bytes), with `git status` empty after each:
  1. `Router.swift` `firstWithin` waits out the work. Caught by `testAModelTierThatNeverAnswers…`
     and `testTheCallThatMissesTheDeadlineIsCancelled`. **Survived** the starvation test (M7).
  2. `scripts/offline.sb` without `(deny network-outbound)`: caught, exit 4 before any test.
  3. `Makefile` without the `--derive` line: **survived** (M4).
  4. `wave_check_all.main` without `headless_waves`: **survived** (M4).
- **Planted inputs**, all outside the repository unless stated:
  - five skip spellings (M1);
  - `needs("bogus")`: exit 2;
  - an `@pytest.mark.artifact` test: exit 1;
  - an empty budget: exit 1;
  - six plan layouts and one wrapped glob list (M3);
  - six footprint spellings (M2);
  - eight Swift spellings (M9);
  - M18-W3's tree replayed from `6a8038e` (M8).
- **Network probes**, none of which sent a packet off this machine:
  - inside the profile: a UDP `connect()` to TEST-NET-1 (refused), a unix `connect()` to the
    resolver socket (accepted, no query), and a `::1` loopback connect (ok);
  - outside the profile: only the conftest refusal (exit 4), which sends nothing.
- `make -n test` with `UNAME_S=Linux` in the environment (M6).
- `SlowTierTests` with `LIBDISPATCH_COOPERATIVE_POOL_STRICT=1` (R1), and inside the profile with
  `--disable-sandbox` (K1). Both passed. A SIGKILL guard was ready; it was not needed.
- No installer, launchd, `simctl` or `xcodebuild` was run. No `os.abort()`. No bare
  `URLSessionConfiguration()` was built in the Swift bundle.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-06 · Commit range: `133a525..f393bc4`*
