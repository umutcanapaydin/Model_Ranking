---
record_type: review
id: backlog-hardening-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Tester review: the hardening wave (#276, #271, #272, #275, #274; D-198)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `01c0fc0..108d254` (19 commits, `7e89544` to `108d254`; `origin/main` is `01c0fc0`). The seat
is a worktree detached at `108d254` with its own `.venv`. Every fault was planted outside the seat: in a
`git archive` export of `108d254`, in a scratch clone of the seat at `108d254` (for the faults that need the
git history), or in a second export that also holds this review's tests.
**Risk tier:** HIGH for #276 (the egress pin, INV-62, G-13); MEDIUM for #271, #272, #274 and #275

Inputs read: the 19 commits, D-198, the five issues (`gh issue view`), both Code-Reviewer rounds with their
dispositions, `tests/skips.py`, and `.github/workflows/ci.yml` (read only). No held-out file was read, and no
held-out question was printed: every run reported failing test ids and counts only, and every plant used a
made-up question. Known and filed elsewhere, so not findings here: #242, #243, #278, #279.

## Verdict
MINOR

75 faults were planted: 73 in Python and 2 in Swift.
- Python: 15 in L1's escape decoding, 13 in the leak check's record scan and its age test, 16 in the backlog
  rule, 5 in its wiring, 7 in the egress pin, 12 in the #275 guard, and 5 in the `git_history` need.
- Swift: 2 rebound reads, one in each store, limited to the on-device store.

The wave's own suites caught 34 of the Python faults and both Swift faults. The 39 Python survivors were each
run again against the whole Python suite, and each stayed green. They are listed below.

This review adds 14 test functions and 2 cases to an existing one: 20 Python test cases in all, and no
Swift test. They catch 32 of the 39 survivors. The other 7 are equivalent on today's tree, a belt behind
another rule, or a deleted assertion (K1). No finding is left open.

Every criterion D-198 states has a citing test that fails when its rule is broken. So the verdict is not
BLOCKING. The seven MINOR findings are rules the code holds but no test held. Each is closed by a test below.

## Suite
- **Python.** `.venv/bin/python -m pytest -q -n 6 tests` in the seat:
  - at `108d254`, outside the sandbox: **2905 passed, 29 skipped**; two of the skips are the `offline`
    need's tests, which run inside it;
  - with this review's tests, offline (`MODEL_RANKING_REQUIRE_OFFLINE=1 sandbox-exec -f
    scripts/offline.sb`): **2927 passed, 27 skipped**, the 20 added cases among them;
  - the coverage floors pass, and `coverage_floor.py --derive` finds CI's 86 skips equal to the budget;
  - offline, in the export (no `.git`, no `advisor.db`): 2847 passed, 87 skipped; in the clone: 2855
    passed, 79 skipped;
  - `ruff check src tests scripts` passes.
- **Swift.** `make swift-test` in the seat with this review's tests: **PASS, 637 tests, each named in the
  manifest**; SlowTierTests 7 of 7 on a one-thread pool.
- **Records.** `scripts/check_records.py --root .` and `--self-test` pass in the seat with this record, and
  `wave_check_all.py` passes.
- **Network.** No test reached the network. Every Python and Swift run was inside `scripts/offline.sb`.
- **Weakened tests.** None. The wave's test diff against `01c0fc0`:
  - moves pin files' reads of the app's Swift to `_code`, `_swift` with a reason, or `# raw:` with a reason;
  - changes the egress pin's two `Data(contentsOf: url)` entries into the longer guard-and-read expression;
  - deletes no assertion that still had a subject.
  - This review's own changes move two pieces of test logic into helpers (the age check, the guard's file
    list). What each test asserts is unchanged.

## Red to green
Each red test commit was exported, its tests run there, then run again on the fix after it.

| Red commit | Failing at the red commit | Fix | At the fix |
|---|---|---|---|
| `e0700f2` (#276) | 2 of 56: both cases of the rebound-read pin | `e5cdebd` | 56 passed |
| `489d5cc` (#271) | 1 of 2: the escaped Turkish line | `92f33b8` | 2 passed |
| `15a50bb` (#272) | 1 of 70: a question quoted in a record | `a4d349d` | 69 passed, 1 skipped |
| `4981fee` (#275) | 2 of 11: the guard and its floor | `6137cfb` | 11 passed |
| `24a0aae` (#274) | 6 of 6 | `e5fc270` | 6 passed |
| `b2ece4d` (round 1) | 7 of 7 | `05ebda7` | 7 passed |
| `4c2b1b5` (round 2) | 6 of 8 | `03fad1e` | 8 passed |

The Swift half of `e0700f2` (`testTheOnDeviceStoreLoadsWithoutReachingOut`) was not run at the red commit.
S2 below shows it fail on the rebound form.

## Acceptance-criterion coverage

| Criterion | Citing test | Held against its faults |
|---|---|---|
| Clause 1: L1 decodes a JSON `\uXXXX` and a Swift `\u{...}` | `tests/unit/test_language_rule_escapes.py:29`, `:40`; `test_hardening_round_one.py:63`; the self-test's `tr-escaped.json`; added T1 | yes (A01 to A03, A05, A06, A09, A11 to A13, A15; A04, A07, A08 only by T1) |
| Clause 2: the leak check reads `docs/**/*.md`, wrapped, spaced, ticked and quoted | `tests/unit/test_ios_client_contract.py:276`; `test_hardening_round_one.py:52`; `test_hardening_round_two.py:55`; added T2 | yes (B03 to B05; B06 only by T2) |
| Clause 2: a live set's overlap with records, by file and count | `test_ios_client_contract.py:285` | yes (B01, B02, B07, B08, B12) |
| Clause 2: an overlap is excused only in an older record | `test_ios_client_contract.py:321`; added T3, T4, T15 | yes (B11; B09, B10, B13 only by T3; H04 by `test_ci_needs.py:44`; H01 to H03, H05 only by T4, T15) |
| Clause 3: a backlog ADR comes before its code, read on the branch's range | `tests/unit/test_wave_check_backlog_order.py:27` to `:57`; `test_hardening_round_one.py:73`; `test_hardening_round_two.py:45`; added T5 to T8, T14 | yes (D01, D06, D11, D13, D15; D02 to D05, D08 to D10, D12, D16 only by the added tests) |
| Clause 3: `make wave-check-all` runs it | `test_wave_check_backlog_order.py:67`; added T9 | yes (E05; E01 to E04 only by T9) |
| Clause 4: every pin file reads the app's Swift through `_code`, `_swift` with `# keeps //:`, or `# raw:` with a reason | `tests/unit/test_swift_reads.py:72`, `:78`, `:97`, `:105`; `test_hardening_round_two.py:40`; added T12, T13 | yes (G01 to G03, G06; G04, G05, G07, G09, G10, G12 only by the added tests) |
| Clause 5: a store's guard and its read are one permitted expression | `tests/unit/test_router_hints.py:660`; `test_hardening_round_one.py:83`; added T11 | yes (F01, F02, F07; F06 only by T11) |
| Clause 5 and round 2's N6: a URL typed through its module is egress | `test_hardening_round_two.py:62`; added T10 | yes (F05; F03 only by T10) |
| Clause 5: the on-device stores load without reaching out | `ios/EngineTests/FrontDoorTests.swift:830`; `ios/EngineTests/StandingsStoreTests.swift:201` | yes (S1, S2) |

## Fault injection

**Method.** `plant.py` in the Tester's scratchpad made each fault as one exact string replacement:
1. the file's md5 was taken, and the old string had to occur once;
2. the fault was written and the named tests run, offline, with `--no-cov` (the coverage floor fails any
   partial run);
3. the original bytes were written back and the md5 compared.

Every one of the 159 recorded runs restored its file to the md5 taken before it. After the last run,
each scratch tree's planted files compared equal to `108d254` (or, in the second export, to the seat's).

**What ran per fault.**
- L1: the escape tests, both hardening rounds, the seat-gate and language tests, `check_records.py --root .`
  and `--self-test`.
- Record scan: `test_ios_client_contract.py` and both hardening rounds; the age faults in the clone, where
  the git history is.
- Backlog rule and wiring: every `wave_check` and `wave_check_all` test; for the wiring, `wave_check_all.py`
  itself on the clone.
- Egress pin: `test_router_hints.py`, `test_ios_client_contract.py`, `test_board_standings.py` and both rounds.
- Guard: `test_swift_reads.py` and both rounds.
- `git_history`: `test_ci_needs.py`, `test_ios_client_contract.py`, `test_skip_budget_local.py` and
  `coverage_floor.py --derive`, in the clone.
- Swift: `swift test --filter "StandingsStoreTests|GapRegisterHardeningTests"` in the export, offline.
- Survivors: the whole Python suite once more, in the clone.
- With the added tests: the same group plus `test_hardening_tester.py` and `test_ci_needs.py`, in the second
  export. B09, B10, B13 and G10 were planted again on the helpers this review moved them into.

Lines are at `108d254`.

| Fault | Planted change | Wave's suite | With added tests |
|---|---|---|---|
| A01 | `scripts/check_records.py:1322` JSON not decoded | caught | - |
| A02 | `:1324` Swift not decoded | caught | - |
| A03 | `:1322` JSON's escaped backslash not read first | caught | - |
| A04 | `:1324` Swift's escaped backslash not read first | **survived** | caught (T1) |
| A05 | `:1324` a raw string's `\#u{...}` not read | caught | - |
| A06 | `:1324` Swift escapes of 2 to 4 digits only | caught | - |
| A07 | `:1322` JSON hex in lower case only | **survived** | caught (T1) |
| A08 | `:1324` Swift hex in upper case only | **survived** | caught (T1) |
| A09 | `:1341` the second of two escapes dropped | caught | - |
| A10 | `:1340` a surrogate pair read as `?` | **survived** | equivalent (K1) |
| A11 | `:1413` escapes decoded before the spans | caught | - |
| A12 | `:1413` every file decoded as JSON | caught | - |
| A13 | `:1413` nothing decoded | caught | - |
| A14 | `:1335` an escaped backslash kept as itself | **survived** | equivalent (K1) |
| A15 | `:1342` only code points below 256 decoded | caught | - |
| B01 | `tests/unit/test_ios_client_contract.py:251` only `docs/*.md`, not its folders | caught | - |
| B02 | `:251` only `docs/research/` | caught | - |
| B03 | `:268` the record's white space kept | caught | - |
| B04 | `:268` a backtick not read as a quote | caught | - |
| B05 | `:268` only the first blockquote mark dropped | caught | - |
| B06 | `:271` the question's white space kept | **survived** | caught (T2) |
| B07 | `:272` one match counted per record | caught | - |
| B08 | `:259` questions of 25 characters or more only | caught | - |
| B09 | `:316` the age comparison always true | **survived** | caught (T3) |
| B10 | `:311` a record's last adding commit, not its first | **survived** | caught (T3) |
| B11 | `:308` modifying commits read, not adding ones | caught | - |
| B12 | `:244` a record added to `HELD_OUT_PUBLISHED_OVERLAP` | caught | - |
| B13 | `:315` only a set's first record aged | **survived** | caught (T3) |
| D01 | `scripts/wave_check.py:477` `tests/` dropped from `BACKLOG_CODE` | caught | - |
| D02 | `:477` `runner/` dropped | **survived** | caught (T5) |
| D03 | `:477` `requirements/` dropped | **survived** | caught (T5) |
| D04 | `:477` `schemas/` dropped | **survived** | caught (T5) |
| D05 | `:478` `stack.mk` dropped | **survived** | caught (T5) |
| D06 | `:501` the backlog rule reads `CODE_DIRS` | caught | - |
| D07 | `:486` the shallow-clone check removed | **survived** | equivalent (K1) |
| D08 | `:494` any changed close leaves the range to the close, not only an added one | **survived** | caught (T6) |
| D09 | `:495` any added `.md` leaves the range to a close | **survived** | caught (T6) |
| D10 | `:463` earlier citing commits read in `CODE_DIRS` only | **survived** | caught (T7) |
| D11 | `:464` the ADR's own commit read in `CODE_DIRS` only | caught | - |
| D12 | `:468` any earlier code commit refuses a backlog ADR | **survived** | caught (T8) |
| D13 | `:469` an earlier citing commit not read | caught | - |
| D14 | `:492` the empty-range return removed | **survived** | equivalent (K1) |
| D15 | `:500` the rule returns nothing | caught | - |
| D16 | `:491` no merge base passes in silence | **survived** | caught (T14) |
| E01 | `scripts/wave_check_all.py:222` the rule's findings dropped | **survived** | caught (T9) |
| E02 | `:223` the rule's skip not printed | **survived** | caught (T9) |
| E03 | `:221` a `wave_check` without the rule passes in silence | **survived** | caught (T9) |
| E04 | `:220` the rule reads the parent folder | **survived** | caught (T9) |
| E05 | `:219` the rule looked up by another name | caught | - |
| F01 | `tests/unit/test_router_hints.py:758` FrontDoor's read permitted alone again | caught | - |
| F02 | `:769` StandingsStore's read permitted alone again | caught | - |
| F03 | `:704` `Foundation.URL` matched with no white space | **survived** | caught (T10) |
| F04 | `:704` `Foundation.NSURL` not matched | **survived** | belt (K1) |
| F05 | `:704` `Foundation.URL` matched only when called | caught | - |
| F06 | `:831` an exact entry permitted more than once | **survived** | caught (T11) |
| F07 | `:758` the read permitted without its guard | caught | - |
| G01 | `tests/unit/test_swift_reads.py:59` `_swift(` needs no reason | caught | - |
| G02 | `:57` `# raw:` needs no reason | caught | - |
| G03 | `:57` `_code(` in a comment explains | caught | - |
| G04 | `:22` a `.swift` path does not name the app | **survived** | caught (T12) |
| G05 | `:46` a local bound to a `.swift` path not read | **survived** | caught (T12, T13) |
| G06 | `:47` a loop over Swift files not read | caught | - |
| G07 | `:32` a constant bound through another not read | **survived** | caught (T12) |
| G08 | `:44` comment lines read too | **survived** | equivalent (K1) |
| G09 | `:48` module constants not read at a read | **survived** | caught (T12, T13) |
| G10 | `:92` the guard reads `test_[a-r]*.py` only | **survived** | caught (T13) |
| G11 | `:105` the raw-read floor deleted | **survived** | a deleted assertion (K1) |
| G12 | `:46` the local window one line, not three | **survived** | caught (T12) |
| H01 | `tests/skips.py:82` the probe never holds | **survived** | caught (T4) |
| H02 | `:82` the probe holds outside a repository | **survived** | caught (T4) |
| H03 | `:117` the workflow fact always false | **survived** | caught (T15) |
| H04 | `:83` CI marked as having the history | caught | - |
| H05 | `:117` any `fetch-depth` read as the whole history | **survived** | caught (T15) |
| S1 | `ios/ModelRanking/Engine/StandingsStore.swift:60` an https URL bound between the guard and the read, on the on-device store only | caught: `StandingsStoreTests.testTheOnDeviceStoreLoadsWithoutReachingOut`, alone | - |
| S2 | `ios/ModelRanking/Engine/FrontDoor.swift:316` the same, on the gap register's on-device store only | caught: `GapRegisterHardeningTests.testTheOnDeviceStoreLoadsWithoutReachingOut`, alone | - |

## Findings

1. **M1 (MINOR, closed by T1). `scripts/check_records.py:1322`, `:1324`: L1's escapes were held in one case
   of hex each.**
   - JSON and Swift both read hex digits in either case. The wave's tests wrote JSON's in lower case and
     Swift's in upper case.
   - Read in lower case only (A07), a JSON file with `\u015F` passed L1. Read in upper case only (A08), a
     Swift file with `\u{15f}` passed. Each passed the full suite and `check-records`.
   - Swift's escaped backslash was held by no test (A04), only JSON's. Without it, `"\\u{15F}"`, which is a
     backslash and text, reads as a Turkish letter. That refuses more, so it is the safer error.
2. **M2 (MINOR, closed by T2 and T3). `tests/unit/test_ios_client_contract.py:271`, `:307` to `:316`: two
   parts of the record scan were not held.**
   - Round 2's review said the collapse "is applied to both sides". No test held the question's side (B06).
     A question kept with a doubled space or a trailing newline was then not found in any record.
   - The age check's comparison lived inside the test, so no plant could show it fail. Made vacuous (B09),
     limited to a set's first record (B13), or read at a record's last add (B10), it passed in the clone,
     which has the history.
   - T3 needed the check in a helper. It is now `_records_not_older_than_their_set` (`:309` in the seat), and
     the live test calls it. What the live test asserts is unchanged.
3. **M3 (MINOR, closed by T4 and T15). `tests/skips.py:79` to `:83`, `:116` to `:117`: the `git_history` need
   was held by no test.**
   - With the probe never true (H01), the age test skipped on every machine. The full suite and
     `coverage_floor.py --derive` passed. The only sign is one more local skip, which nothing reads.
   - With the workflow fact always false (H03), or true for any `fetch-depth` (H05), `test_ci_needs.py`
     passed. With H03, #278's `fetch-depth: 0` would move no fact. Nothing would then ask for `in_ci` to
     change, and the local count of CI's skips would stay one too high.
4. **M4 (MINOR, closed by T5 to T8 and T14). `scripts/wave_check.py:463`, `:468`, `:477`, `:491`, `:494`,
   `:495`: five parts of the backlog rule were not held.**
   - Four of `BACKLOG_CODE`'s nine paths: `runner/`, `requirements/`, `schemas/` and `stack.mk` (D02 to
     D05). Round 2's test planted `Makefile`, `pyproject.toml` and `conformance/`.
   - Which range is left to a close (D08, D09). The rule skips a range that ADDS a milestone close. With
     `--diff-filter=A` dropped, a backlog wave that edits an old close skipped the rule. With the pattern
     loosened to any `.md`, every backlog wave that adds its review record would skip it. Both passed.
   - Which commits cite the ADR too early (D10). They were read in `CODE_DIRS`, not `BACKLOG_CODE`. A test
     commit that cites the ADR before it is written then passed.
   - The other direction (D12): a backlog ADR refused after any code commit, cited or not. The wave's
     tests passed. A wave that fixes two issues would then be refused for an ADR written after the other
     issue's code.
   - No merge base (D16) must say the rule read nothing (D-192 clause 2). Made silent, it passed. The
     wave's test held only the skip with no `origin/main`.
5. **M5 (MINOR, closed by T9). `scripts/wave_check_all.py:217` to `:224`: the wiring was held by a search
   for the rule's name.** `test_wave_check_backlog_order.py:67` reads the script's text. With the
   findings dropped (E01), the skip not printed (E02), a missing rule silent (E03), or the parent folder
   read (E04), the full suite passed and `wave_check_all.py` printed PASS on the clone.
6. **M6 (MINOR, closed by T10 and T11). `tests/unit/test_router_hints.py:704`, `:831`: two edges of the
   egress pin were not held.**
   - Swift compiles `Foundation .URL`, and `Foundation` with `.URL` on the next line, as a type. This review
     checked both with `swiftc -typecheck`. Round 2's test reads only `Foundation.URL`, so a pattern with no
     white space (F03) passed. A store's `var url: Foundation` then `.URL` on the next line passed every
     text pin.
   - D-198 clause 5 permits the guard and its read "only as one exact expression in each store". The pin
     says "each occurring exactly once". With `== 1` loosened to `>= 1` (F06), a second, live copy in
     another function passed. No test planted one. The rule is older than the range; this wave leans on it.
7. **M7 (MINOR, closed by T12 and T13). `tests/unit/test_swift_reads.py:22`, `:32`, `:46`, `:48`, `:92`:
   five of the #275 guard's rules were not held.**
   - The detector's planted module bound its constant two lines above its read. So the local-window rule
     found that read, and four other rules were tested by nothing:
     - a `.swift` path outside `ios/` (G04);
     - a constant bound through another constant (G07);
     - module constants at all (G09);
     - the local window (G05, G12).
   - The guard's file list lived inside its own loop. Narrowed to `test_[a-r]*.py` (G10), it passed the
     guard and its floor, and the guard no longer read `test_screen_paths.py` or
     `test_uitext_sentence_rows.py`, two files #275 named. The list is now `pin_files()` (`:91` in the
     seat), read by the guard and its floor. T13 holds that each file #275 named is in it, and that the
     detector sees a read of the app's Swift in each.
8. **K1 (informational). The seven survivors with no test.**
   - A10: a surrogate pair decoded as `?`. Equivalent: no Turkish letter is outside the Basic Multilingual
     Plane.
   - A14: an escaped backslash kept as itself. Equivalent: the pattern consumes the pair either way.
   - D07: the shallow-clone check removed. Measured on clones of a scratch branch at depths 1 to 4. At
     depths 1 and 2 the faulted rule still skips, at its "no merge base" check. At 3 and 4 the history is
     whole, and both versions report the same finding. So the check is a belt.
   - D14: the empty-range return removed. Equivalent: an empty range adds no ADR.
   - F04: `Foundation.NSURL` dropped from the module pattern. A belt: `\bNSURL\b` refuses it first.
   - G08: comment lines read as reads. It refuses more, and no such line exists today.
   - G11: the raw-read floor deleted. A deleted assertion is a test-integrity matter, found by diffing the
     tests, as this review did. No suite can catch it.
9. **K2 (informational). The Swift tests are live.**
   - S1 and S2 bind an https URL between the guard and the read, on the on-device store alone, as round 4
     of the backlog-gates review measured.
   - Of the 28 store tests, each plant failed exactly one: the store's new on-device test. The tripwire
     recorded the `example.invalid` address. With nothing planted, all 28 passed.
   - The Python pin refuses both forms too (F01, F02 and the rebound-read test).

## Tests added this review
All pass at `108d254` with this review's changes, and each fails on the faults named.
- **T1:** `tests/unit/test_hardening_tester.py:27`,
  `test_l1_reads_an_escape_in_either_case_and_an_escaped_backslash_as_text` (A04, A07, A08).
- **T2:** `:42`, `test_a_held_question_is_found_whatever_its_own_spacing` (B06).
- **T3:** `:50`, `test_a_record_first_committed_after_its_set_is_not_excused` (B09, B10, B13), on a scratch
  repository. The age check moved into `_first_added` and `_records_not_older_than_their_set`
  (`tests/unit/test_ios_client_contract.py:299`, `:309`).
- **T4:** `:68`, `test_the_git_history_need_holds_only_in_a_whole_history` (H01, H02).
- **T5:** `:91`, `test_a_backlog_adr_beside_any_backlog_code_path_is_refused`, four cases (D02 to D05).
- **T6:** `:99`, `test_a_backlog_branch_that_adds_a_record_or_edits_an_old_close_is_still_read` (D08, D09).
- **T7:** `:119`, `test_a_backlog_adr_after_a_test_commit_that_cites_it_is_refused` (D10).
- **T8:** `:129`, `test_a_backlog_adr_after_unrelated_code_passes` (D12).
- **T9:** `:153`, `test_wave_check_all_fails_on_the_backlog_rules_findings_and_prints_its_skips` (E01 to E04).
- **T10:** `:238`, `test_a_url_typed_through_its_module_across_white_space_is_refused` (F03).
- **T11:** `:249`, `test_a_second_copy_of_a_stores_one_read_is_refused`, two cases (F06).
- **T12:** `:187`, `test_the_detector_finds_a_read_through_a_chained_constant_a_far_constant_and_a_near_local`
  (G04, G05, G07, G09, G12).
- **T13:** `:207`, `test_the_guard_reads_each_pin_file_275_named_and_sees_its_reads` (G10, and G05, G09).
  The guard's file list moved into `pin_files()` (`tests/unit/test_swift_reads.py:91`).
- **T14:** `:139`, `test_a_branch_with_no_merge_base_says_the_rule_read_nothing` (D16).
- **T15:** `tests/unit/test_ci_needs.py:65`, two cases of
  `test_a_planted_change_to_the_test_job_flips_its_need_and_only_that`: `whole-history` flips
  `git_history` (H03), `two-commits` flips nothing (H05).
- No Swift test was added, so `ios/EngineTests/test-manifest.txt` is unchanged.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Closed by T1. | `tests/unit/test_hardening_tester.py` |
| M2 | Closed by T2 and T3; the age check is now the helper `_records_not_older_than_their_set`. | same, `tests/unit/test_ios_client_contract.py` |
| M3 | Closed by T4 and T15. #278's `fetch-depth: 0` now flips the `git_history` fact, so the local count of CI's skips moves with it. | `tests/unit/test_hardening_tester.py`, `tests/unit/test_ci_needs.py` |
| M4 | Closed by T5 to T8 and T14. | `tests/unit/test_hardening_tester.py` |
| M5 | Closed by T9. | same |
| M6 | Closed by T10 and T11. | same |
| M7 | Closed by T12 and T13; the guard's file list is now `pin_files()`. | same, `tests/unit/test_swift_reads.py` |
| K1 | Accepted: five are equivalent or a belt behind another rule, G08 refuses more, and G11 (a deleted assertion) is found by diffing the tests at review. | none |
| K2 | Accepted: both on-device store tests fail on the rebound read, and the Python pin refuses it too. | none |
