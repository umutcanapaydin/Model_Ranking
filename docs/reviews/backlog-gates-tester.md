---
record_type: review
id: backlog-gates-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Tester review: the gates and licences wave (#253, #247, #246, #244, #261; D-197)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `2891f15..9287c27` (17 commits, `62bf419` to `9287c27`). The seat is a worktree detached at
`9287c27` with its own `.venv`. Every fault was planted in a `git archive` export of `9287c27` outside the seat.
**Risk tier:** HIGH for #244 and #246 (the compiled privacy gate); MEDIUM for the rest

Inputs read: the 17 commits, D-197, the four Code-Reviewer rounds and their dispositions, and #242's scope.
No held-out file was read. Known and filed elsewhere, so not findings here: #242, #243, #275, #276.

## Verdict
MINOR

68 faults were planted: 10 in A1, 12 in the pins' Swift reading (`_swift`, `_code`, the raw-read guard),
10 in the store rules, 4 in the staleness check, 9 in the engine client's rules, 7 in the credits on the
engine, and 16 in the app's credits and licence texts. The wave's own suites caught 43. The 25 survivors are
listed below. This review adds 10 Python test cases (8 functions) and 2 Swift tests, which catch 17 of them. Seven are equivalent
on today's tree, or a belt behind another rule. One stays open (M4).

Each survivor was confirmed against the whole suite it could reach: the full Python suite for Python faults,
and the full Swift suite (633 tests) for Swift faults.

## Suite
- **Python.** `.venv/bin/python -m pytest -q -n 4 tests` in the seat:
  - at `9287c27`: **2856 passed, 29 skipped**;
  - with this review's tests: **2866 passed, 29 skipped**;
  - `ruff check` passes on the four touched test files.
- **Swift.**
  - At `9287c27`, in the export, offline (`MODEL_RANKING_REQUIRE_OFFLINE=1 sandbox-exec -f ../scripts/offline.sb
    swift test --disable-sandbox`): **633 tests, 0 failures**.
  - `make swift-test` in the seat with this review's tests: **PASS, 635 tests, each named in the manifest**;
    SlowTierTests 7 of 7 on a one-thread pool.
- **Compiled gate.** `scripts/client_decl_gate.py` on the export: `client-decls PASS: 21 client file(s) in 4
  configuration(s)`.
- **Records.** `scripts/check_records.py --root .` and `--self-test` pass on the export.
- **Network.** No test reached the network. The Swift runs were inside the offline sandbox.
- **Weakened tests.** None. The wave's test diff against `2891f15`:
  - raises one count (6 to 8 refusals) because the fixture gained two key paths;
  - removes the G-15 sentence checks (RAW, COMMENTED) with the gap G-15 that #247 closed;
  - widens the staleness test's control to the two new tables;
  - deletes no assertion that still had a subject.

## Acceptance-criterion coverage

| Criterion | Citing test | Red to green proven |
|---|---|---|
| #253: a pointer names an ADR whose `Amends` names it back | `tests/unit/test_wave_check_m21_rules.py:806`; added `:828` | yes (A01, A03, A04; A06 to A08 only by the added test) |
| #253: D-176 and D-179 name what they amend | `make check-records` on the real log | yes (A09, A10) |
| #247: `_swift` blanks block comments, keeps lines and `//` | `tests/unit/test_ios_client_contract.py:1666` | yes (B01, B04, B05, B12) |
| #247: `_without_block_comments` nests, skips `//` and strings, fails loud | added `tests/unit/test_router_hints.py:1202`, `:1213` | yes (B02, B03, B06, B07 only by the added tests) |
| #247: every pin read in `test_router_hints.py` goes through `_code` | `tests/unit/test_router_hints.py:1171`; added `:1181` | yes (B08; B09 only by the added test); B10 open (M4) |
| #246: a store makes no URL by an initialiser or a decode | `tests/unit/test_client_decl_gate.py:893`, `:906` | yes (C01, C03, C04) |
| #246: the register's file references only its Foundation list | `tests/unit/test_client_decl_gate.py:912`; added `:957`; the compiled gate | yes (C05, C09, C10; C06, C07 only by the added test) |
| #244: other files reach only the engine client's listed members, whole, per file | `tests/unit/test_client_decl_gate.py:941` and the fixture | yes (D01 to D04, D08, D09) |
| #244: no key path names a request's source | `tests/unit/test_client_decl_gate.py:924` (round-two twins), `:585` (the fixture count) | yes (D05, D07) |
| Round 2's N1: an entry no longer used fails the gate | `tests/unit/test_client_decl_gate.py:527`; added `:969` | yes (E01, E02, E04; E03 only by the added test) |
| D-197 clause 2: each Apache-2.0 or MIT credit carries its notice, or is in `PUBLISHES_NO_NOTICE` | `tests/unit/test_credits.py:249`; `tests/unit/test_arc_agi_2.py:113` | yes (N01 to N07) |
| D-197 clause 2: the phone decodes and keeps the notice, and an older engine's credit reads | `ios/EngineTests/CreditsTests.swift:93` | yes (S01, S02) |
| D-197 clause 3: the sheet carries each named licence's text, once, in first-named order | `CreditsTests.swift:93`; `tests/unit/test_credits.py:278`; added `CreditsTesterTests.swift:29`, `:42` | yes (S04, S06, S07, S13; S03, S08, S14 only by the added tests) |
| D-197 clauses 2 and 3: the sheet draws the notice and the texts | added `tests/unit/test_credits.py:297` | yes (S10 to S12, only by the added test) |
| D-197 clause 4: each Apache address permitted exactly once, in `Models.swift` | the egress pin, `tests/unit/test_router_hints.py:588` | yes (S15, S16) |

## Fault injection

**Method.** `plant.py` in the Tester's scratchpad made each fault as one exact string replacement in the export:
1. the file's md5 was taken, and the old string had to occur once;
2. the fault was written and the named commands run;
3. the original bytes were written back, the md5 compared, and the file compared with the seat's.

Each of the 119 recorded runs (the 68 faults, then the re-runs) restored to the md5 taken before it. A first
pass of 29 ran with the coverage floor on, which fails any partial run; it was discarded, re-run with
`--no-cov`, and restored each file too. After the last run, `diff -rq` showed the export identical to the seat
(build output aside). Test files in the export were reset to `9287c27` for the
first pass of each group and replaced by the seat's for the re-runs.

**What ran per fault.**
- A1: `test_wave_check_m21_rules.py`, `test_review_seat_gate.py`, `test_c2b_counter.py`, `check_records.py`
  on the real log and `--self-test`.
- Pin reading: `test_router_hints.py`, `test_ios_client_contract.py`, `test_credits.py`, `test_arc_agi_2.py`,
  `test_security_invariants.py`.
- Gate: `test_client_decl_gate.py`, `test_security_invariants.py`; for a list entry, also the compiled gate.
- Credits: every test whose name holds credit, arc, licence or notice.
- Swift: `swift test --filter "CreditsTests|UITextLanguageTests|CreditsTesterTests"` offline, plus the pins.
- Survivors: the full Python suite, or the full Swift suite, once more.

| Fault | Planted change (file:line at `9287c27`) | Wave's suite | With added tests |
|---|---|---|---|
| A01 | `scripts/check_records.py:1579` reverse loop reads nothing | caught | - |
| A02 | `:1581` the "log holds no" branch never runs | **survived** | equivalent: the next branch refuses the ghost pointer, with another message |
| A03 | `:1584` the "does not name" branch never runs | caught | - |
| A04 | `:1579` pointer read only at a line's start | caught | - |
| A05 | `:1568` targets declared only when in the log and not the ADR itself | **survived** | equivalent: such a target can carry no pointer that the check reads |
| A06 | `:1568` every D-n in the source's body counts as declared | **survived** | caught (T1) |
| A07 | `:1584` refused only when the source declares no amendment at all | **survived** | caught (T1) |
| A08 | `:1580` finding reported at the ADR's heading line | **survived** | caught (T1) |
| A09 | `docs/decisions.md:3783` D-176's `Amends` removed | caught (`check-records`) | - |
| A10 | `docs/decisions.md:3907` D-156 dropped from D-179's `Amends` | caught (`check-records`) | - |
| B01 | `tests/unit/test_ios_client_contract.py:42` `_swift` keeps block comments | caught | - |
| B02 | `tests/unit/test_router_hints.py:140` nesting not counted | **survived** | caught (T2) |
| B03 | `:148` `//` comment not skipped | **survived** | caught (T2) |
| B04 | `:153` strings not skipped | caught | - |
| B05 | `:144` a block comment's newlines dropped | caught | - |
| B06 | `:153` raw `#"` strings not skipped | **survived** | caught (T2) |
| B07 | `:160` an unclosed comment does not raise | **survived** | caught (T2) |
| B08 | `:258` `_hint_ids` reads Router.swift raw | caught (the guard) | - |
| B09 | `:1168` the guard's pattern matches no read | **survived** | caught (T3) |
| B10 | `:1177` exemption by `_code` or `raw` anywhere on the line | **survived** | open (M4) |
| B11 | `:600` the register pin reads all of FrontDoor.swift | **survived** | equivalent: it reads more, so refuses more |
| B12 | `ios/ModelRanking/Engine/Models.swift:659` a `/* */` copy of the MIT text above a changed live one | caught | - |
| C01 | `scripts/client_decl_gate.py:1981` `_store_url_problem` not called | caught | - |
| C02 | `:184` `NSURL` dropped from `URL_MADE_BY_NAME` | **survived** | belt: both stores' lists refuse every `NSURL` symbol first (K1) |
| C03 | `:184` `decoded` dropped | caught | - |
| C04 | `:1955` the URL rule only in the register's file | caught | - |
| C05 | `:2055` `_store_module_problem` not called | caught | - |
| C06 | `:1967` an entry's lookalike passes (`symbol.startswith(entry)`) | **survived** | caught (T4) |
| C07 | `:1965` the store list read for `Foundation` only, not `SINK_MODULES` | **survived** | caught (T4) |
| C08 | `:184` only `URL.init(string:` refused by name | **survived** | belt: the other initialisers are off both lists (K1) |
| C09 | `:169` `CharacterSet.newlines` removed from the list | caught (compiled gate only) | - |
| C10 | `:179` `URLComponents.init(string:` added to the list | caught | - |
| E01 | `:1843` store entries not checked for staleness | caught | - |
| E02 | `:1845` engine-client entries not checked | caught | - |
| E03 | `:1844` an entry seen when any reference contains it | **survived** | caught (T4) |
| E04 | `:363` `EngineClient.baseURL` added for Models.swift | caught | - |
| D01 | `:2055` `_engine_client_problem` not called | caught | - |
| D02 | `:2022` members matched by prefix | caught | - |
| D03 | `:2021` one list for every file | caught | - |
| D04 | `:2019` the engine client's own file checked too | caught | - |
| D05 | `:1739` the key-path rule never runs | caught | - |
| D06 | `:1743` the key-path rule ignores `_task` and `$task` | **survived** | equivalent: the alias rule at `:1733` refuses any non-implicit use of either |
| D07 | `:1740` the key path's own line read, not its children | caught | - |
| D08 | `:2019` members with a `(` skipped | caught | - |
| D09 | `:361` `EngineClient.subscript(asking:` listed | caught | - |
| N01 | `src/app/workflows/board_tables.py:122` LiteLLM's notice removed | caught | - |
| N02 | `board_tables.py:98` terminal_bench dropped from `PUBLISHES_NO_NOTICE` | caught | - |
| N03 | `src/app/workflows/rank.py:161` `notice` not served | caught | - |
| N04 | `rank.py:139` `arc_prize_solutions` not credited | caught | - |
| N05 | `board_tables.py:132` the solutions' notice removed | caught | - |
| N06 | `board_tables.py:141` HELM's notice altered | caught | - |
| N07 | `board_tables.py:120` Aider given a notice | caught | - |
| S01 | `ios/ModelRanking/Engine/Models.swift:403` notice decoded from another key | caught | - |
| S02 | `:699` a row's notice always `nil` | caught | - |
| S03 | `:436` a licence matched whole, not by its start | **survived** | caught (T6) |
| S04 | `:437` each licence carried once per credit | caught | - |
| S05 | `:436` a licence matched anywhere in the string | **survived** | equivalent: no served licence names Apache-2.0 or MIT past its start |
| S06 | `:450` MIT carries the Apache text | caught | - |
| S07 | `:542` one word of the Apache text changed | caught (`test_credits.py`) | - |
| S08 | `:435` every text carried when no credit names one | **survived** | caught (T6) |
| S09 | `Language.swift:397` the heading not Turkish | caught | - |
| S10 | `ContentView.swift:759` the row's notice not drawn | **survived** | caught (T5) |
| S11 | `:771` the texts' section shown only when empty | **survived** | caught (T5) |
| S12 | `:775` the section draws the name, not the text | **survived** | caught (T5) |
| S13 | `Models.swift:450` the Apache entry named "Apache" | caught | - |
| S14 | `:435` only the first two credits read | **survived** | caught (T6) |
| S15 | `Models.swift:450` the Apache address as a live string | caught (egress pin) | - |
| S16 | `:649` the Apache address a second time in the text | caught (egress pin) | - |

## Findings

1. **M1 (MINOR, closed by T1). `scripts/check_records.py:1568`, `:1580`, `:1584`: half of #253's reverse
   check was not held.**
   - The wave's test plants only a pointer whose source declares no amendment at all. #253's second case is a
     source that amends others (D-179 amended three, not D-156).
   - With the check refusing only a source with no `Amends` (A07), all tests and `check-records` passed.
   - With every D-n in the source's text counted as declared (A06), a pointer to an ADR that only "applies"
     the target passed.
   - With the finding reported at the heading, not the pointer (A08), nothing failed.
2. **M2 (MINOR, closed by T2). `tests/unit/test_router_hints.py:140`, `:148`, `:153`, `:160`: four of
   `_without_block_comments`'s stated rules were not held.**
   - Its docstring says block comments nest, and a `/*` inside a `//` comment or a string opens nothing.
   - Each, broken, passed the full suite (B02, B03, B06), and so did removing the fail-loud raise (B07).
   - Broken nesting keeps a comment's tail as live code, so a pin reads text no build compiles. The other
     three blank live code to the end of the file, or raise.
3. **M3 (MINOR, closed by T3). `tests/unit/test_router_hints.py:1168`: the raw-read guard could pass
   vacuously.** With `_READ` matching no read at all (B09), the guard found nothing and passed. AGENTS.md 3.5
   says an empty derived set is a failure. T3 asserts the guard sees the pins' `_code(` reads.
4. **M4 (MINOR, open). `tests/unit/test_router_hints.py:1177`: the guard's exemption is not held.**
   - The rule is "a raw read says why on its line", marked `# raw:`.
   - With the exemption loosened to `_code` or `raw` anywhere on the line (B10), a line such as
     `raw = path.read_text()` would pass. The full suite passed.
   - The predicate lives inside the test, so no test can plant a line for it. `test_ios_client_contract.py:1659`,
     the twin from before the range, has the same shape.
   - Remedy: move the predicate into a helper that takes lines. Then test it on a raw read, a read with `raw` in
     a name, a `_code(` read and a `# raw:` read. Or file it with #275.
5. **M5 (MINOR, closed by T4). `scripts/client_decl_gate.py:1844`, `:1965`, `:1967`: the store's list was
   held less tightly than the engine client's.**
   - C06: a prefix match let `URL.appendingPathComponent(_:conformingTo:` pass under the listed
     `URL.appendingPathComponent`. Round 1's M1 made the engine client's members match whole; the store's list
     says "any other one is refused by absence".
   - C07: the list read for the `Foundation` module alone. A `_DarwinFoundation1` symbol then passed
     `FrontDoor.swift`, and passes every other file too (`MODULES` allows that module whole).
   - E03: the staleness check by substring read `URL.appendingPathComponent` as still used while only
     `URL.appendingPathComponent(_:isDirectory:` remained.
   - Each passed the full Python suite.
6. **M6 (MINOR, closed by T5 and T6). D-197 clause 3 and the sheet were held only on the wave's one payload.**
   - The wave's Swift test names MIT and plain "Apache-2.0" in its first two credits.
   - So these passed all 633 Swift tests:
     - a whole-string match (S03), which drops HELM's "Apache-2.0 (the HELM repository, ...)";
     - reading only the first two credits (S14);
     - carrying every text when no credit names one (S08).
   - The view's notice line and the licence texts' section (`ContentView.swift:759`, `:770` to `:778`) were held
     by no pin. Removing the notice, inverting the section's guard, or drawing the name in place of the text
     (S10 to S12) passed the full Python suite.
7. **K1 (informational). The URL rule's belts.**
   - In `FrontDoor.swift` the store list refuses every URL initialiser and decode before `_store_url_problem`
     runs. Its message also says "a store makes a URL only", so `test_a_store_makes_a_url_only_from_the_file_systems_folders`
     (`tests/unit/test_client_decl_gate.py:893`) cannot tell the two rules apart there.
   - In `StandingsStore.swift` the sink list does the same, except for `URL.init(string:` and `URL.decoded`,
     which the test holds.
   - So `URL_MADE_BY_NAME`'s `NSURL` half and its other initialisers (C02, C08) fire only if a list grows. That
     is a reasonable belt; no test is added.
8. **K2 (informational).** An entry removed from the store's list (C09) is caught only by the compiled gate on
   the shipping client (`make client-decls`), not by the Python suite. That gate is a leg of `make check` and
   `make check-fast`, so this is held. A probe on the iPhoneSimulator 26.5 SDK puts `socket` and `getaddrinfo` in
   `Darwin` (refused) and `fopen` in `_DarwinFoundation2` (refused). Only `pow` was seen in `_DarwinFoundation1`.

## Tests added this review
All pass at `9287c27`, and each fails on the faults named.
- **T1:** `tests/unit/test_wave_check_m21_rules.py:828`,
  `test_a_pointer_whose_adr_amends_others_or_names_it_outside_amends_is_refused_at_its_line` (A06, A07, A08).
- **T2:** `tests/unit/test_router_hints.py:1202`, `test_without_block_comments_reads_nesting_line_comments_and_strings`,
  four cases (B02, B03, B06); `:1213`, `test_a_block_comment_that_never_closes_fails_loud` (B07).
- **T3:** `tests/unit/test_router_hints.py:1181`, `test_the_raw_read_guard_sees_the_reads_it_lets_through` (B09).
- **T4:** `tests/unit/test_client_decl_gate.py:957`,
  `test_the_gap_registers_file_matches_its_foundation_list_whole_and_in_each_foundation_module` (C06, C07);
  `:969`, `test_a_store_entry_is_seen_only_by_its_own_declaration` (E03).
- **T5:** `tests/unit/test_credits.py:297`, `test_the_credits_sheet_draws_each_notice_and_the_licence_texts`
  (S10, S11, S12).
- **T6:** `ios/EngineTests/CreditsTesterTests.swift:29`,
  `testALicenceIsCarriedForACreditWhoseLicenceBeginsWithItsNameWhereverItIsListed` (S03, S14); `:42`,
  `testCreditsThatNameNoCarriedLicenceCarryNoText` (S08).
- **Manifest:** `ios/EngineTests/test-manifest.txt` gains the 2 Swift tests, sorted; `make swift-test` finds the
  discovered tests equal to it.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Closed by T1. | `tests/unit/test_wave_check_m21_rules.py` |
| M2 | Closed by T2. | `tests/unit/test_router_hints.py` |
| M3 | Closed by T3. | same |
| M4 | Filed on #275, which widens the raw-read guard to every pin file; the helper and its planted lines belong there. | #275 |
| M5 | Closed by T4. | `tests/unit/test_client_decl_gate.py` |
| M6 | Closed by T5 and T6. | `tests/unit/test_credits.py`, `ios/EngineTests/CreditsTesterTests.swift` |
| K1 | Accepted: the module lists refuse first, and `URL_MADE_BY_NAME` stays as the backup if a list grows. | none |
| K2 | Accepted: the store list is the compiled gate's, and `make client-decls` runs in `check-fast` on a Mac (G-10, #243). | none |

