---
record_type: review
id: m19-wave-3-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# Wave 3 Tester Review (m19)

**Reviewer:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records,
and it is not the wave's Code-Reviewer.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `133a525e8e77755c913e6442ed7a343563fb0a29..f47231b` (17 commits; 42 files, +1533 / -92).
It includes the Code-Reviewer's verdict (`960b2d3`), the red tests for its findings (`7e01e53`) and
the fixes (`f47231b`).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:80`, `docs/plans/m19-wave-3-plan.md:13-17`). Gate
definitions change, and the diff touches `tests/conftest.py`, a security glob (`m19-plan.md:131`). By
D-172 no security seat runs on the wave.
**Code-Reviewer verdict:** MINOR, M1 to M10, K1, K2, R1 to R3 (`docs/reviews/m19-wave-3-review.md`).
Not BLOCKING, so this seat runs.
**Model routing (HIGH, advisory):** author family: Claude (all 17 commits carry `GP-Agent:
claude-code/local-lane`) / reviewer family: Claude (Opus 5.5). Fallback reason: no second model family
is available to this seat. Fresh context: I read the base profile and rules first, then the plans,
D-183, INV-6, G-5, the skip budget and the issues, then the diff, and the commit messages last.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75d...`) on `origin/main`
and in the tree. The range does not touch it, `.agents/rules/practices.md` or the `writing-a-control`
skill. Nothing in the diff tries to change this review's policy.

## Verdict

MINOR

**Nothing blocks.** W3 has no REQ-IDs ("none new (controls)", `m19-plan.md:40`). Each phase's
acceptance check (`m19-wave-3-plan.md:44-48`) has a citing test that exercises it, and the tests pass.
Each of the six issues' tests fails on its red commit, run on that commit's own tree, and passes on the
fix. So do the review's M1, M2, M3, M6 and M8 tests at `7e01e53`. The suite passes in this seat, with
its test leg inside the offline profile.

**Fault injection: 28 of 31 code faults killed before this review (90%), 31 of 31 after.** Three
fail-open paths of `coverage_floor.py --derive` had no test: a collection that fails, an unset budget,
and a `needs` that `tests/skips.py` does not name. I wrote two tests that kill all three. One acceptance
check was held only by a stand-in: P5's "shown red on M18-W3's case as a fixture". I wrote that replay
from M18-W3's own phrases and its now-retired set. It flags exactly the review's 11 phrases, and it is
red on the matcher the wave first shipped.

**The findings are holes and records, not failures.** Five of the Code-Reviewer's findings were
closed only in part (its M1, M2, M3, M5 and M6): planted inputs or a static read still get past each.
What is left is not in D-183's "What it does not do", and only one root is filed (#183): M3 to M7
below. One test
will turn CI red the day the owner applies #122's patch (M1 below). Three records disagree on one count
(M2 below). And `make wave-check` will refuse this wave's close as things stand: the Code-Reviewer's
verdict has 47 nested bullets that the gate counts as findings with no id (M9 below).

## Acceptance-criterion coverage (REQUIRED)

The W3 criterion: "A wave sees CI's skip count, its wave and tier gates, and a child process's network
before it pushes. Each new check is shown red." By phase:

- **P1, #137** (the local skip count) → `tests/unit/test_skip_budget_local.py:27` (cites REQ-CI-001 and
  #137): on the tree the derived count is the budget (83 of 2090 in this seat). `:34`: a planted
  `needs("artifact")` test fails it. `:45`: a budget above the count fails. `:86`: a raw skip in any
  tracked test file is refused. `:100`: nine spellings are refused. Caller held at
  `tests/unit/test_offline_run.py:109`. Fail-closed paths held by this seat's `:55` and `:69`. GREEN.
- **P2, #140** (the wave gates read the plan) → `tests/unit/test_wave_check_m19_rules.py:57`, `:66`,
  `:73` (a wave named by an amendment or a table, with no heading, is refused, in an open milestone
  too); `:80` (quiet on `M17-W5` and `W-108`); `:115` (a MED close on `EngineClient.swift` is refused);
  `:122` (no glob list fails closed); `:128` (quiet on HIGH, and on MED off the globs); `:136`, `:145`,
  `:155`, `:164` (the review's M2 and M3 shapes); `:171` (the caller in `wave_check_all.main`). GREEN.
- **P3, #122** (the run offline at the OS level) → `tests/unit/test_offline_run.py:45` (`make test`
  runs inside `scripts/offline.sb` on macOS and says it must); `:52` (a run that must be offline and is
  not stops first); `:64` (a child, Python with a scrubbed environment and `curl`, is refused an outside
  peer); `:77` (a child cannot reach the resolver socket); `:88` (loopback stays open); `:116` (the
  environment's `UNAME_S` cannot remove the profile). The whole suite passes inside the profile: 2065
  passed. The CI patch is posted on #122, and G-5 is narrowed to CI (`docs/security-invariants.md:175`).
  GREEN, with M1, M3 and M7 below.
- **P4, #149** (the deadline read to its cause) → the reading is at
  `ios/EngineTests/FrontDoorTests.swift:550-555`. The relative bound is at `:525`, and the starved
  process at `:556`. After the review's M7, both are red on the review's mutant: a race that waits out
  the model. GREEN.
- **P5, #117** (signal words only a live held-out set holds) → `tests/unit/test_ios_client_contract.py:1494`,
  `:1505`, `:1515` (the matcher); `:1569` (the tree: each flagged entry is named with its origin, and a
  stale name fails too). **Partial before this review:** the committed cases were stand-ins. Only two
  of M18-W3's 27 phrases were used, with invented held-out rows, and the plan says "M18-W3's case as a
  fixture". **Completed by this seat:** `:1550`, `test_m18_w3s_own_case_is_flagged_phrase_by_phrase`.
  It uses the 27 phrases of `6a8038e`. It reads M18-W3's held-out set, retired now and pinned by its
  sha256. It uses every tuning row of `6a8038e` that any phrase matches. It asserts the review's exact
  11. Red on the pre-M8 matcher (9 of 11), GREEN now.
- **P5, #108** (the bare configuration, read not trapped) → `tests/unit/test_swift_tests_offline.py:95`
  (the two spellings refused, a comment not); `:110` (the app and its tests hold none). The reading is
  on #108, and the issue stays open. GREEN, with M8 below.

## Red→green on reported symptoms

Each red commit was exported with `git archive` into the scratchpad and run on its own tree with this
seat's venv. Nothing in the worktree was checked out.

- **#137** (the skip budget seen only after a push) → at `3f1bc30`, `test_skip_budget_local.py`: 3
  failed (no `--derive` yet, and raw skips in the tree). At `08df6f4`: 4 passed.
- **#140** (headings only, one HIGH path) → at `fff70d0`, `test_wave_check_m19_rules.py`: 6 failed, 1
  passed. At `16e3986`: 8 passed.
- **#122** (a child process reaches the network) → at `ea24722`, outside the profile: 3 failed. The
  child's UDP `connect()` reached TEST-NET-1, which sends no packet. At `b6fbc73`, inside the profile: 4
  passed.
- **#149** (the deadline test at 11.4 s against 5 s) → at `a0d58a9`, `swift test --filter
  SlowTierTests/testTheDeadlineIsHeldWhenTheProcessIsStarved` failed: `6.069 is not less than 5.0`. That
  is the reported shape: a process that is not scheduled, judged by the clock. A SIGCONT watchdog ran
  beside it; it was not needed, and no process was left stopped. At `f47231b` all 7 `SlowTierTests`
  pass.
- **#117** (no gate flags held-out-only signal words) → at `fbfc756`: 2 failed. At `03329e4`: 6 passed.
  M18-W3's real case: see P5 above.
- **#108** (a bare configuration trapped an xctest process) → at `4e39f30`: the planted-spellings test
  failed. At `f5d70cf`: 9 passed. No process was trapped.
- **The review's findings** → at `7e01e53`, inside the profile: M1, M2 (brace and folder), M3
  (spellings and wrap), M6 and M8 each failed (6 failed, 12 passed). They pass at `f47231b`. M5's test
  has no red commit of its own. Run under `f393bc4`'s profile, it fails: `AssertionError: reached`. It
  passes under the current profile. M7: see F31 below.

## Suite result

- `make check-fast` on `f47231b`, guard stubs on `PATH`: **PASS** in 73.9 s. Lint, typecheck, records
  (with `wave-check-all` and conformance), test, swift-test and client-decls all passed.
  - Test leg: `MODEL_RANKING_REQUIRE_ARTIFACT=1 MODEL_RANKING_REQUIRE_OFFLINE=1 /usr/bin/sandbox-exec
    -f scripts/offline.sb .venv/bin/python -m pytest -n auto` → `2062 passed, 25 skipped`. Every one of
    the 25 skip reasons starts `needs ...`. Then `coverage_floor --derive: CI will skip 83 of 2087
    (artifact 52, contract 18, epoch 7, macos 2, offline 2, xcode 2); the budget ... is 83`.
  - swift-test (parallel): `469 test(s), exactly the ones named in ios/EngineTests/test-manifest.txt`.
- Again with this seat's three tests: **PASS** in 77.8 s. `2065 passed, 25 skipped`; `CI will skip 83
  of 2090`.
- **Coverage on touched code.** The measured source is `src/app` (`pyproject.toml:155`). The range
  changes no file under `src/` or `ios/ModelRanking` (`git diff --stat` is empty), so module coverage
  cannot move: total 91.93%, and `coverage-floor PASS: 45 module(s), floor 60%`. The touched scripts
  and the conftest run mostly in child processes, which coverage does not see. The fault injection
  below is the evidence for them.
- **Mutation runner (advisory):** none is wired (`make falsify` runs only in the distribution
  package). Hand-planted kill rate: 28 of 31 before this review, 31 of 31 after. Three data plants and
  one replay check were also killed.

## Mocks / contract tests

- No new external integration. The wave's one new dependency is the operating system's sandbox, and
  it is tested for real, not mocked: `skips.offline()` starts a child that makes a real UDP
  `connect()`, and `test_offline_run.py` runs under the real profile.
- The four live contract tests moved from `skipif(RUN_CONTRACT_TESTS)` to `needs("contract")`. The
  condition is the same (`tests/skips.py:60`). The contract job still sets the variable, and
  `make test` never runs them (D-183: "outside `make test`, as before"). OK.

## Test integrity

- **Weakened or deleted to green:** none. I read the diff of each of the 18 converted test files.
  Each one replaces a `skipif`, an in-body `pytest.skip`, or a helper's skip with `needs(...)`,
  under the same condition. Each helper that lost its skip has every caller marked: an unmarked caller
  would raise `KeyError` on this Mac, which has no `EPOCH_DATA_DIR`, and none did. No assertion was
  removed.
- **Between the red commit and the fix (`7e01e53..f47231b`):** one test changed its expectation:
  `test_a_turkish_stem_matches_...` became `test_an_entry_matches_at_a_words_start_with_any_ending`.
  It now expects "print" to be flagged in "printer". That is the design D-183 clause 5 records
  (prefix matching on both sides, after the review's M8). It makes the control flag more, so it is not
  weakened. The three entries removed from `HELD_OUT_ONLY_REVIEWED` (`komutu`, `component`, `line`) are
  no longer flagged, because the tuning sets hold them with a suffix. The tree test fails on a stale
  name, so that list cannot drift.
- **Mirror tests:** the wave's new tests plant inputs and read exits and outputs. They do not restate the
  code. One weak point: `test_the_environment_cannot_turn_the_offline_run_off` compares two lines.
  Both would be empty if `make -n test` printed nothing, but `:45` fails in that case.

## Fault-injection protocol

How each fault ran: `m19w3-tester-logs/plant.py` in the scratchpad read the file's bytes and sha256,
planted one exact string replacement, ran the named tests, and restored the bytes in a `finally`.
Then it compared the bytes and the sha256 with the pre-plant read. Each step is one record in
`faults.jsonl`. Every fault was restored byte-identical. After every batch, `git status --porcelain`
was empty, apart from this seat's own two test files once they existed.

| # | Fault (file) | Result |
|---|---|---|
| F1 | `skips.apply` never counts a need CI lacks (`tests/skips.py`, sha `eb83b1ec`) | RED: `test_skip_budget_local.py:27` |
| F2 | `--derive` passes a count above the budget (`scripts/coverage_floor.py`, `57abc6fc`) | RED: `:34` |
| F3 | `--derive` passes a count below the budget | RED: `:45` |
| F4 | `--derive` exits 0 when collection fails | **survived**, then RED on this seat's `:55` |
| F5 | `--derive` exits 0 on an unset budget | **survived**, then RED on this seat's `:69` |
| F6 | the `artifact` marker no longer counts as `needs("artifact")` | RED: `:27` |
| F7 | `make test` without its `--derive` line (`Makefile`, `4465e235`) | RED: `test_offline_run.py:109` |
| F8 | a raw `pytest.skip` planted in `tests/unit/test_effort.py` | RED: `test_skip_budget_local.py:86` |
| F9 | an unknown need let through (`skips.needs_of`) | **survived**, then RED on this seat's `:55` |
| F10 | `headless_waves` finds nothing (`scripts/wave_check_all.py`, `39056604`) | RED: `test_wave_check_m19_rules.py:57` |
| F11 | `wave_check_all.main` without `headless_waves` | RED: `:171` |
| F12 | a plan with no globs passes (`scripts/wave_check.py`, `d58e8996`) | RED: `:122` |
| F13 | no brace expansion in the footprint | RED: `:145` |
| F14 | a folder no longer touches the globs beneath it | RED: `:145` |
| F15 | the glob rule starts a day later | RED: `:115` |
| F16 | another milestone's `M<n>-W<k>` counts as this plan's wave | RED: `:80` |
| F17 | a glob bullet that wraps ends the list | RED: `:164` |
| F18 | the HIGH rule never refuses | RED: `:115` |
| F19 | the profile leaves the resolver socket open (`scripts/offline.sb`, `96eed9d9`), run inside it | RED: `test_offline_run.py:77` |
| F20 | the profile without `(deny network-outbound)`, run inside it | RED: exit 4 before any test ("#122: this run must be offline ...") |
| F21 | the conftest no longer refuses a run that must be offline (`tests/conftest.py`, `b4939cf2`) | RED: `test_offline_run.py:52` |
| F22 | `make test` outside the profile on macOS (`OFFLINE_RUN =`) | RED: `:45` |
| F23 | `UNAME_S ?=` | RED: `:116` |
| F24 | the profile kept, the refusal's variable misspelled | RED: `:45` |
| F25 | the held-out check ignores the tuning sets (`test_ios_client_contract.py`, `e8fd5517`) | RED: `:1569` |
| F26 | matching back to whole English words (the M8 defect) | RED: `:1505`; on this seat's replay: RED, 9 of 11 (`88a28e04`) |
| F27 | no minimum length, so particles are flagged | RED: `:1505` |
| F28 | only `Reading.swift`'s first list is read | RED: `:1569` |
| F29 | the bare-configuration pattern matches nothing (`test_swift_tests_offline.py`, `ebceaacd`) | RED: `:95` |
| F30 | `skips.offline()` says offline outside any sandbox; run outside, with a refusing `curl` stub first on `PATH` | RED: `:64`, at its UDP assertion (`reached`), before `curl` |
| F31 | `firstWithin` waits the work out, then drops a late result (`Router.swift`, `f7dd224f`) | RED: `testAModelTierThatNeverAnswers...` (10.06 s against 4.20 s), `testTheDeadlineIsHeldWhenTheProcessIsStarved` (10.01 s against 8.07 s), `testTheCallThatMissesTheDeadlineIsCancelled`. After the restore: 7 passed |
| P1 | a held-out-only word planted in `Reading.swift`'s first list (`1eea49b2`) | RED: `:1569`, naming the word |
| P2 | `URLSessionConfiguration()` planted in `FrontDoorTests.swift` (not built) (`75ff3574`) | RED: `test_swift_tests_offline.py:110` |
| P3 | `URLSessionConfiguration.init()` planted in `EngineClient.swift` (not built) (`8be4f34c`) | RED: `:110` |

**Planted inputs that pass (control holes, not mutants):** four skip shapes (M4), two environment
routes (M3), four footprint shapes and one tier cell (M6), four plan layouts (M5), and one platform
(M1). Each is in its finding below.

**Network probes.** None sent a packet off this machine:
- UDP `connect()` only, to TEST-NET-1;
- unix-socket `connect()` to `/var/run/mDNSResponder`, `/private/var/run/mDNSResponder` and
  `/private/var/run/../run/mDNSResponder`, inside the profile (each refused, EPERM) and outside it
  (no query written);
- a loopback listener;
- a `curl` stub that refuses.

No name lookup ran, and no TCP connect to an address off this machine. No installer, `launchctl`,
`simctl`, `xcodebuild`, `os.abort()` or bare `URLSessionConfiguration()` build was run. The starvation
test SIGSTOPs its own process; at `f47231b` its backstop sends SIGCONT. At `a0d58a9`, which has no
backstop, a SIGCONT watchdog ran beside it and was not needed. `ps` showed no stopped process
afterwards.

## BLOCKING

- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `tests/unit/test_offline_run.py:76-85`. **The name-lookup test needs `offline` only, but it
  probes a macOS path. It will fail in CI the day the owner applies #122's patch.** In CI's Linux
  namespace `skips.offline()` is true (ENETUNREACH), so the test runs there.
  `/private/var/run/mDNSResponder` does not exist on Linux, so `connect()` raises `FileNotFoundError`.
  The probe catches only `PermissionError`, so stdout is empty and `assert ... == "refused"` fails.
  Measured with the probe's path swapped for a missing one: stdout `''`, `FileNotFoundError`. The #122
  comment tells the owner to expect "CI skips 81" and a green run.
  **Fix:** `@pytest.mark.needs("offline", "macos")`, or give the probe a Linux form. Update the #122
  comment to say what to expect.
- **M2** `docs/decisions.md:4177` (D-183, "Revisit when"); `docs/skip-budget.txt:43-46`; the #122
  comment; `docs/plans/m19-plan.md:230-231`. **Three records disagree on one count, and the plan's
  amendment is stale.** D-183 says the budget "falls by one" when the CI patch lands.
  `skip-budget.txt` says "lowers this by two". The #122 comment says "CI skips 81, not 82", but the
  budget is 83. The W3 amendment says #117's check "found five signal words" after the M18 sets; the
  tree test now names four (`debug`, `conclusion`, `conclusions`, `plot`;
  `test_ios_client_contract.py:1594-1597`), as #177's update says.
  **Fix:** after M1's fix there is one right number. Write it in all three places, and write four in
  the amendment.
- **M3** `Makefile:98-99`. **The review's M6 is closed for `UNAME_S` only. An environment variable can
  still remove the profile and its refusal.** Measured on this Mac: `MAKEFLAGS=UNAME_S=Linux make -n
  test` prints `MODEL_RANKING_REQUIRE_ARTIFACT=1  .venv/bin/python -m pytest -n auto`, with no
  `sandbox-exec` and no `MODEL_RANKING_REQUIRE_OFFLINE`. So does `MAKEFLAGS=e UNAME_S=Linux make -n
  test`. GNU make reads the variable assignments in the environment's `MAKEFLAGS` as command-line ones.
  `test_the_environment_cannot_turn_the_offline_run_off` (`:116`) tries only `UNAME_S`.
  **Fix:** the review's second option, which covers every route. On `sys.platform == "darwin"`, the
  conftest refuses a `make test` run (`MODEL_RANKING_REQUIRE_ARTIFACT=1`) that is not offline. Then
  add `MAKEFLAGS` to the test.
- **M4** `tests/unit/test_skip_budget_local.py:82-83` (`RAW_SKIP`); D-183 clause 1. **The review's M1
  is closed for its five spellings. Four more skip shapes pass the scan and `--derive`, and CI counts
  each one.** Planted outside the repository: `import pytest as pt` then `pt.skip(...)`;
  `raise pytest.skip.Exception(...)`; `_pytest.outcomes.skip(...)`; and
  `@pytest.mark.parametrize("value", [])`. The last is an empty parameter set, which pytest skips and
  which is no spelling at all. `RAW_SKIP` matched none of the four. `--derive tests <planted>` said
  "CI will skip 83 of 2091" and exited 0. A real run of the four wrote a JUnit report that
  `coverage_floor.counts()` reads as `(4, 4)`, so CI would count 87 against 83. None of these shapes is
  in the tree, and the review matched CI's real count, so this is a hole, not a live miss. But D-183
  says "A skip spelled any other way is refused in the source", and it is not.
  **Fix:** the runtime rule the review proposed: a conftest hook fails a test reported skipped or
  xfailed for a reason `skips.apply` did not set. Or narrow D-183 and file the rest.
- **M5** `scripts/wave_check_all.py:113` (`NAMED_WAVE`), `:129-135`; D-183 clause 2. **The review's M3
  is closed for three of its five layouts. The other two are neither fixed nor recorded.** Planted
  through the wave's own `_plan` helper, none of these was flagged: an `### Amendments` list
  ("2026-10-06: W3 joins" as a list item), a `| **W3** | #12 |` table cell, a `**Plan amendment
  (...)**` paragraph, and a lower-case "wave 3". The first two are in the review's own planted list.
  The control, a bold `**Amendment` with `W3`, was flagged. D-183 says "A wave an amendment or a table
  names must have its own heading". Its "What it does not do" names none of these, and no issue holds
  them.
  **Fix:** read every `W<n>` and `M<this>-W<n>` the plan names outside code (the review's fix), or
  file it.
- **M6** `scripts/wave_check.py:300-316` (`_footprint_paths`, `_touches`); D-183 clause 2 ("brace forms
  and folders read"). **Four more footprint shapes and one tier cell pass a MED close on a security
  glob.** Planted through `test_wave_check_m19_rules._close` with the plan's globs, each of these
  exited 0: `ios/ModelRanking/Engine/{Models, EngineClient}.swift` (a space after the comma),
  `ios/ModelRanking/{Engine,Other}/{EngineClient,Models}.swift` (two brace groups),
  `./tests/conftest.py`, and `ios/ModelRanking/Engine` (a folder with no trailing slash). The plain
  path, the control, was refused. A tier cell that reads "MED, not HIGH" also passes, because the rule
  reads `\bHIGH\b` anywhere in row 1's evidence. That read was #83's, and this wave extends it to
  every glob.
  **Fix:** #183 (read the commit range's diff) is the root fix. Add these shapes to #183, or make
  D-183's sentence say exactly what is read.
- **M7** `scripts/offline.sb:8`; `docs/security-invariants.md:149` (INV-6: "every child process
  included, name lookups too"). **Network.framework resolves names past the denied socket.** What
  holds: `getaddrinfo` goes through `libsystem_info` and `libsystem_dnssd`, which use the unix socket
  (`dyld_info -imports`: `socket`, `connect`, no XPC), and the profile refuses that socket in every
  spelling I tried. What does not: Network.framework resolves through `libdns_services`
  (`dnssd_getaddrinfo_create`). That library imports `xpc_connection_create_mach_service`, and
  mDNSResponder serves the mach service `com.apple.dnssd.service`, which `(allow default)` leaves open.
  So a child that resolves through Network.framework (a Swift tool, `nscurl`) still sends its query
  out; only its connection afterwards is refused. This is read, not measured: measuring would send a
  DNS query. The review's second M5 point is also neither fixed nor recorded: a child can hand a URL
  to a system service (LaunchServices) outside the sandbox.
  **Fix:** `(deny mach-lookup (global-name "com.apple.dnssd.service"))`, then measure the suite. Or
  narrow INV-6 to `getaddrinfo` and add the rest to D-183's "What it does not do".
- **M8** `tests/unit/test_swift_tests_offline.py:110-114`; INV-6 ("No Swift source writes a bare
  `URLSessionConfiguration()`"). **The scan reads two of the three Swift folders, and it keys files by
  name.** It reads `ios/EngineTests/*.swift` (top level only) and `ios/ModelRanking/**`. It does not
  read `ios/UITests` or `ios/Package.swift`. And `{p.name: ...}` keeps only one of two files with the
  same name: the later path wins, so a bare configuration in `ios/EngineTests/X.swift` is hidden by
  any `ios/ModelRanking/**/X.swift`. No live miss: no two files share a name today, and the UI tests
  install no tripwire.
  **Fix:** key by relative path and read `ios/**/*.swift`, or scope INV-6's sentence to what is read.
- **M9** `docs/reviews/m19-wave-3-review.md` (`960b2d3`); `scripts/wave_check.py:63-71`
  (`deferrable_findings`). **`make wave-check` will refuse this wave's close because of its own
  Code-Reviewer verdict.** Under a MINOR, K.9 or "Risks queued" heading, the gate counts every bullet
  line, nested ones included, as a finding, and each one needs an id. Read with the gate's own
  function, the W3 review has 15 ids and 47 sub-bullets with none. So the W3 close will fail: "has 47
  MINOR/K.9/queued finding(s) with no id". Every other M19 verdict has 0 (measured). This one is not in
  the wave's code, but it is in its range, and it stops the close.
  **Fix:** either the gate reads an indented bullet under an id'd one as part of that finding (today it
  fires on a correct verdict, which writing-a-control question 2 calls a control someone disables), or
  the review seat re-issues its verdict flat. The review is committed "as written", so this seat does
  not edit it. (This verdict keeps its own findings flat for the same reason.)

## Tests added/extended this review

Uncommitted in this seat's worktree, for the author to commit unedited with this verdict:

- `tests/unit/test_skip_budget_local.py:55`, `test_a_need_that_skips_py_does_not_name_stops_the_count`.
  It proves P1's fail-closed path (D-183 clause 1; writing-a-control question 5). A `needs("bogus")`
  test stops `--derive` with exit 2, "CANNOT RUN", and names the need. It kills F4 (collection failure
  returns 0) and F9 (an unknown need let through), which survived the wave's tests.
- `tests/unit/test_skip_budget_local.py:69`, `test_an_unset_budget_fails_the_local_check`. It proves
  that an unset budget is a failure: exit 1, "no skip budget". It kills F5, which survived.
- `tests/unit/test_ios_client_contract.py:1524-1566`, `M18_W3_INSTRUCTION_PHRASES`, `M18_W3_HELD_OUT`,
  `M18_W3_TUNING_ROWS` and `test_m18_w3s_own_case_is_flagged_phrase_by_phrase`. It proves P5's "shown
  red on M18-W3's case as a fixture" (#117's done-when). It flags exactly the 11 phrases of the M18-W3
  first review's table. It is red on the pre-M8 matcher (9 of 11) and GREEN now. The held-out rows are
  read from the retired file, never copied, so
  `test_no_held_out_question_is_written_into_the_code_or_its_tests` stays green. The Turkish letters
  are escaped (V4C-79).

*Filled by: Tester seat (independent) · Date: 2026-10-06 · Commit range: `133a525..f47231b`*
