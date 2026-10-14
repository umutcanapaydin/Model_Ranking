---
record_type: review
id: backlog-gates-review-round-3
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 3: the gates and licences wave (#253, #247, #246, #244, #261, D-197)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `2891f15..c726fe8` (15 commits). Round 3 reads round 2's fixes, `ad648b0` (red) and
`c726fe8` (fix), against round 2 (`docs/reviews/backlog-gates-review-round-2.md`), then the whole range once more.
Round 1 is `docs/reviews/backlog-gates-review-round-1.md`.
**Risk tier:** HIGH for #244 and #246 (the compiled privacy gate, INV-62, INV-64, INV-67); MEDIUM for
the rest

## Verdict
MAJOR

Round 2's N1 is fixed. The staleness check fires on a stale entry and on a removed call, in each list, in
all four configurations, on the shipping client. Round 2's N2 is recorded as its disposition says.
`make check-fast` passes in the seat.

Round 2's M1 was narrowed, not fixed in code. INV-62, INV-67 and the process log now say what the gate
holds. But G-13's "still not held" text, which carries the narrowing, is still wrong in three ways:
- **M1.** G-13 names only the inferred form of the generic decode, and says the stores' `isFileURL` guards
  stop it. Round 2's own first probe is an explicit-type generic decode read directly, and it passes the
  compiled gate and no guard runs. A decode through a `typealias` of `URL` passes the compiled gate too.
  What refuses all three is the text pin, not the guards. #242's note repeats the same text.

Three minor findings (N1 to N3). N1 is a record problem the round-2 fix commit made: renaming round 1's
record moved about 17 citations onto the wrong findings.

How the review was done:
- **Reading.** Rounds 1 and 2 and their dispositions; the two fix commits; `unseen_permissions`, the store,
  engine-client and URL rules of `scripts/client_decl_gate.py`; INV-62, INV-67, INV-78, G-13, G-14 and the
  G-15 closure note; the process log entry; D-197; the credits table; the egress text pin; #242's comments.
- **Plants.** I exported `HEAD` to a scratch tree outside the seat (`git archive`). Each plant went into a
  scratch copy. The full gate (`scripts/client_decl_gate.py`, self-test plus four configurations) and,
  where named, the text pins ran on it. Each file was then restored, and a byte compare against the seat's
  file passed every time. The seat's tree is unchanged.
- **Gate on HEAD.** `client-decls PASS: 21 client file(s) in 4 configuration(s)`.
- **Checks.** `make check-fast` passes in the seat at `c726fe8` (110 s, six legs), and `make check-records`
  passes with this record added.
- **Network.** One read of #242's comments through `gh`. No test reached the network.
- **Held-out discipline.** I read no held-out file.

## Round 2's dispositions, re-measured

| Round 2 | Holds? | Measured |
|---|---|---|
| M1 | In part | INV-62 (`docs/security-invariants.md:123`), INV-67 (`:128`) and the process log (`docs/process-log.md:852-855`) now say "by a URL initialiser or by a decode whose type names `URL`", and that a URL decoded through a generic helper is not held. That is true of the printed type (see M1 below on a `typealias`). G-13 (`:197`) is not accurate: M1 below. The runtime guards it cites exist and are tested: `ios/ModelRanking/Engine/FrontDoor.swift:316` (held by `FrontDoorTests.testTheRegisterIsOnlyEverAFileOnThisDevice`, `ios/EngineTests/FrontDoorTests.swift:815`) and `ios/ModelRanking/Engine/StandingsStore.swift:60` (held by `StandingsStoreTests.testAStorePointedAnywhereButAFileReadsNothing`, `ios/EngineTests/StandingsStoreTests.swift:187`). But each guards only the store's own `load()` and `save()`. |
| N1 | Yes | Shipping client, four configurations. Planted `URL.standardized` on the `FrontDoor.swift` list and `EngineClient.localDefault` on the `Models.swift` list: the gate fails, one line each, per configuration (8 lines). Removed `.lowercased(with: Locale(identifier: "en_US_POSIX"))` from `FrontDoor.swift:230` and `EngineClient.maxStandingsBytes` from `Models.swift:769-771`: the gate fails on `Locale.init(identifier:`, `StringProtocol.lowercased(with:` and `EngineClient.maxStandingsBytes`, per configuration (12 lines). Restored; `scripts/client_decl_gate.py`, `FrontDoor.swift` and `Models.swift` byte-identical to the seat. Code: `scripts/client_decl_gate.py:1840-1844`. Test: `tests/unit/test_client_decl_gate.py:527`. See N3 for the test's history. |
| N2 | Yes | Recorded in round 2's table, as it says. |
| K1 | Yes | Noted on #242 (comment of 2026-10-14T11:49:50Z). |
| R1 | Accepted | G-10, #243. |

## Findings

### BLOCKING
- none

### MAJOR

- **M1** `docs/security-invariants.md:197` (G-13, "Still not held on the compiled module: ... and a URL a
  generic helper in the store's own file decodes, its type inferred (...; the stores' own `isFileURL`
  guards ... refuse to load it)"): the narrowed text names one form of three, and cites a backstop that
  does not cover two of them.
  - **Measured.** Each probe was appended to the shipping `FrontDoor.swift`. The full gate ran in the four
    configurations, then `test_router_hints.py` and `test_ios_client_contract.py` ran.

    | Probe | Compiled gate | Guard runs? | Text pin |
    |---|---|---|---|
    | P1: round 2's explicit form, `r3Decode([URL].self, encoded)?.first`, then `Data(contentsOf: target)` | PASS, 0 refusals | No | Refused by `[<\[,(]\s*URL\b` |
    | P2: inferred form, `var target = GapRegisterStore.onDevice.url; target = r3Decode(encoded) ?? target`, then `Data(contentsOf: target)` | PASS, 0 refusals | No | Refused by `\bcontentsOf\s*:` |
    | P3: `private typealias R3Place = URL`, then `JSONDecoder().decode([R3Place].self, from: encoded)`, then `GapRegisterStore(url: target).load()` | PASS, 0 refusals | Yes | Refused by `\btypealias\b` |

    In each case one test failed, `test_the_gap_register_code_carries_no_egress_spelling_the_pin_reads`;
    the other 114 passed.
  - **Why the three claims are wrong.**
    - "its type inferred". P1 passes `[URL].self` as an argument. Inside the helper the decode is still of
      `T`, so `DECODES_URL` (`scripts/client_decl_gate.py:451`) does not see it. Round 2 measured P1 too.
    - The guards. `load()` and `save()` check `url.isFileURL` on the store's own `url`. P1 and P2 read the
      decoded URL directly, with a second `Data(contentsOf:)` in the store's file. The compiled gate allows
      that, since `Data.init(contentsOf:options:` is on the store's list (`scripts/client_decl_gate.py:168`)
      and the file is a file-system file. What refuses it is the text pin: `contentsOf:` is an `EGRESS`
      spelling (`tests/unit/test_router_hints.py:681`), permitted only as `Data(contentsOf: url)`, exactly
      once (`:722`).
    - The `typealias`. `DECODES_URL` reads the type as printed, and a `typealias` prints as its own name.
      So "a decode whose type names `URL`" (INV-62, INV-67, the process log) is held for the printed
      type only. The text pin refuses `typealias` in every client file (`:689`).
  - **Also.** #242's comment of 2026-10-14T11:49:50Z repeats "its type inferred" and "The stores'
    `isFileURL` guards refuse to load it today". The allowlist work it scopes would plan from that.
  - **Failure scenario.** Someone tidies the egress pin, for example permits a second `Data(contentsOf:)`
    in the register's file, reading G-13 as saying the guards stop a decoded URL. P2 then passes every
    gate, and the register's file reads an https address the reader's words are in.
  - **Remedy.** Text only. Rewrite G-13's clause to say, roughly: "a URL a generic helper in the store's own
    file decodes, its type explicit or inferred, or a decode whose type is a `typealias` of `URL`. The
    stores' `isFileURL` guards refuse such a URL only when it reaches the store's own `load()` or `save()`.
    A second read in the store's file is refused by the egress pin's `contentsOf:` and its exact-once
    `Data(contentsOf: url)`, and a `typealias` by its `typealias` (G-14)." In INV-62 and INV-67 say "a
    decode whose printed type names `URL`". Add a correction comment on #242.

### MINOR (the author fixes each in this wave or files it as an issue)

- **N1** `docs/reviews/backlog-gates-review-round-2.md:3` (`id: backlog-gates-review`, now round 2) and the
  rename in `c726fe8`: about 17 citations of "the backlog-gates review's" a finding now point at the wrong
  finding.
  - **Measured.** At `82f08b0` the record with id `backlog-gates-review` was round 1. `c726fe8` moved round
    1 to `backlog-gates-review-round-1` and put round 2 at the bare id. Every citation written before that
    means round 1:
    - `docs/decisions.md:5073` and `:5077` (D-197: "the backlog-gates review's N2", "N1"). Round 2's N2 is
      the red test's history, and its N1 is the staleness check. Round 1's are the ARC-AGI-2 credit and the
      licence pin.
    - `scripts/client_decl_gate.py:159`, `:353`, `:464`, `:1960`; `scripts/check_records.py:1578`;
      `scripts/client_decl_fixtures/ContentView.swift:272`, `EngineClient.swift:61`, `FrontDoor.swift:11`.
    - `src/app/workflows/board_tables.py:128`; `tests/unit/test_arc_agi_2.py:122`;
      `tests/unit/test_client_decl_gate.py:913`, `:944`; `tests/unit/test_credits.py:249`, `:270`;
      `tests/unit/test_security_invariants.py:354`; `tests/unit/test_wave_check_m21_rules.py:820`.
    - #242's comment of 2026-10-14T11:14:16Z links `docs/reviews/backlog-gates-review-round-2.md` for K1. That file's
      K1 is now a different finding.
  - **Failure scenario.** A reader follows D-197's "the backlog-gates review's N2" to the record with that
    id and finds a note about a red test, not the ARC-AGI-2 licence line.
  - **Remedy.** Put round 1 back at `backlog-gates-review` and move round 2 to
    `backlog-gates-review-round-2` (two renames, ids updated). Then every existing citation is right as
    written. Or rewrite each citation to say "round 1's".

- **N2** `docs/process-log.md:850` and `docs/security-invariants.md:223-224` ("every Swift pin reads
  through `_code` or `_swift`"): the sentence claims more than the code holds.
  - **Measured.** INV-78 (`docs/security-invariants.md:150`) is accurate: it scopes the claim to the two
    pin files and says "Other pin files read the raw text". The two sentences above have no such scope.
    In `tests/unit/test_credits.py`, the file this wave added a `_swift` pin to (`:276`), two pins still
    read `ContentView.swift` raw (`:167`, `:188`). With the live
    `.sheet(isPresented: $showingCredits) { creditsSheet }` removed, `test_the_credits_button_opens_the_sheet`
    fails (control). With it removed and a copy kept inside `/* */`, it passes. With a copy kept under
    `#if false`, it passes. Restored; byte-identical. Other pin files read Swift raw too
    (`test_engine_address.py:54`, `:80`, `test_ios_visual_contract.py:10`, `:22`,
    `test_uitext_sentence_rows.py:22`, and more).
  - **Remedy.** Scope both sentences to "every pin in `test_router_hints.py` and
    `test_ios_client_contract.py`". Route `test_credits.py:167` and `:188` through `_swift` (already
    imported at `:276`), or file it.

- **N3** `tests/unit/test_client_decl_gate.py:539`: the round-2 N1 red test's last assertion could never
  pass, and the fix commit rewrote it.
  - **Measured.** `ad648b0` asserted that no unseen line names `FrontDoor.swift` or `EngineClient.` when
    both lists are fully seen. With only those files found, `unseen_permissions` also reports
    `FrontDoor.swift: sorted on entries`, `FrontDoor.swift: min on entries`, and two `EngineClient.swift`
    calls (`UIText.engineAddress`, `FetchedStandings.init`), from older tables. `c726fe8` narrowed it to
    lines ending in the two new lists' wording. The red was red for the right reason first (the first
    assertion), and the final test is sound.
  - **Why it matters.** It is round 2's N2 again: a red test that could not go green as written, changed in
    the green commit with no word in the disposition.
  - **Remedy.** No code change. Say so in the disposition, and cite `c726fe8`'s test as N1's evidence.

### PASS (what looks good)
- **The staleness check.** Per file, exact, in every configuration, and it names the file and the entry.
- **The narrowed invariants.** INV-62, INV-67 and the process log no longer say a store makes no URL by
  any decode.
- **The guards.** Both exist where cited, and each has a Swift test that holds it without the network.
- **The licence texts.** `LicenceText.carried` matches by prefix (`ios/ModelRanking/Engine/Models.swift:436`),
  so HELM's "Apache-2.0 (the HELM repository, D-193); ..." still gets the Apache text.

## Producers of the hardened invariants
- **INV-62 and INV-67, the stores' URLs.**
  - Producers: `FrontDoor.swift` and `StandingsStore.swift`.
  - Citing tests: `test_a_store_makes_a_url_only_from_the_file_systems_folders`,
    `test_the_stores_shipping_urls_pass`,
    `test_the_gap_registers_file_references_only_its_listed_foundation_declarations`
    (`tests/unit/test_client_decl_gate.py:912`),
    `test_an_entry_of_the_stores_or_the_engine_clients_list_the_client_no_longer_uses_fails_the_gate` (`:527`),
    the egress pin (`tests/unit/test_router_hints.py:588`), and the two Swift guard tests above.
  - Gaps: M1; G-13 (#242).
- **INV-64, the request's sources.**
  - Producers: assignments and key paths to `ContentView.task`, and the engine client's members reached
    from another file.
  - Citing tests: `test_a_file_reaches_only_the_engine_clients_listed_members` (`:941`), and `:527` for the
    list's staleness.
  - Gaps: G-11 (#242).
- **INV-78, how pins read Swift.**
  - Producers: the pins in `test_router_hints.py`, `test_ios_client_contract.py`, and `test_credits.py`'s
    licence pin.
  - Citing tests: `test_a_swift_read_in_this_file_goes_through_code`
    (`tests/unit/test_router_hints.py:1171`), and its twin in `test_ios_client_contract.py`.
  - Gaps: G-14; N2 (the records claim every pin file).

## Acceptance criteria evidence
- **Round 2 M1 (narrowed).** `docs/security-invariants.md:123`, `:128`, `:197`; `docs/process-log.md:852-855`.
  Not yet accurate in G-13: M1.
- **Round 2 N1.** Code `scripts/client_decl_gate.py:1840-1844`; test `tests/unit/test_client_decl_gate.py:527`;
  plants above.
- **Round 2 N2.** Round 2's dispositions table.
- **#253, #247, #246, #244, #261.** As round 2 measured; nothing in `ad648b0..c726fe8` changes their code.

## K.8 contract drift check
- `unseen_permissions` keeps its signature. It now reads two more tables.

  ```
  scripts/client_decl_gate.py:1822:def unseen_permissions(found: dict[str, set[str]]) -> list[str]:
  scripts/client_decl_gate.py:1841:    missing += [f"{name}: `{entry}` on the store's Foundation list" for name, allowed in STORE_FOUNDATION_ALLOWED.items()
  scripts/client_decl_gate.py:1843:    missing += [f"{name}: `{entry}` on the engine client's list" for name, allowed in ENGINE_CLIENT_REACHABLE.items()
  ```
- No engine or `/v1` change in `ad648b0..c726fe8`.
- Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- **K1** `tests/unit/test_engine_address.py:54`, `:80`, `tests/unit/test_ios_visual_contract.py:10`, `:22`,
  `tests/unit/test_uitext_sentence_rows.py:22` (and other pin files): they read the app's Swift raw, so a
  dead or commented copy of a line they require satisfies them, as N2 measured on `test_credits.py`. INV-78
  records it. A shared reader through `_swift`, with a guard like `test_a_swift_read_in_this_file_goes_through_code`,
  would close it. Enhancement.

## Risks queued to next M
- **R1** CI's Linux lane runs only the text pins (G-10). M1's three probes are refused there only by the
  egress pin's spellings. The sign it is real: a change to `EGRESS` or `EGRESS_EXACT` that lets one of
  them through passes CI.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Fixed in the records. G-13's "still not held" names the three forms (type given, type inferred, a `typealias`), says the `isFileURL` guards cover only the stores' own `load()` and `save()`, and names the egress text pin as what refuses them today. INV-62 and INV-67 say "a decode whose type prints as `URL`". #242 carries a correction. | `docs/security-invariants.md`, `docs/process-log.md`, #242 |
| N1 | Fixed. Every citation meaning round 1 now says "round 1's" (D-197, the gate, the fixtures and the tests); #242's note says which round each comment means. Round 2's record is renamed `-round-2`, and this one takes the bare id. | the files named |
| N2 | Fixed. The process log and the G-15 closure note are scoped to the two pin files; `test_credits.py`'s two reads go through `_swift`. A commented copy of the sheet line now fails `test_the_credits_button_opens_the_sheet` (planted, then restored). | `tests/unit/test_credits.py`, `docs/process-log.md`, `docs/security-invariants.md` |
| N3 | Recorded. `ad648b0`'s last assertion filtered too broadly and could not pass; `c726fe8` narrowed it to the two lists' lines. Cite `c726fe8`'s test, which round 3 re-measured, as round 2's N1 evidence. | this table |
| K1 | Filed as #275. | #275 |
| R1 | Accepted: G-10, the owner's macOS lane (#243). | none |

