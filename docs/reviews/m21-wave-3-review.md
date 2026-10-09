---
record_type: review
id: m21-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 3 Code Review, round 3 (the records after round 2: does any still claim more than the gate holds?)

**Reviewer:** Code-Reviewer subagent (fresh eyes; wrote none of the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: rounds 1 and 2
(`docs/reviews/m21-wave-3-review-round-1.md`, `-round-2.md`) were read first, then `git show 3eee132`,
then the gate (`scripts/client_decl_gate.py`, all of it) against each record.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `0af8dbb..011f15d`, the answer to round 2 (`3eee132`, records only, and `011f15d`, the
round-2 file's rename); the wave as a whole is `972b55e..011f15d`.
**Risk tier:** HIGH (plan §3; `EngineClient.swift`, `StandingsStore.swift`, `ContentView.swift` and
`FrontDoor.swift` are security globs)

## Verdict
BLOCKING

## Summary

`3eee132` did what it set out to do for INV-64, INV-66 and INV-76. I checked each row clause by clause
against `problems()`: each lists forms the gate implements, and each ends "any other form is not held".
G-1, G-2, G-11 and G-12 name their residue by class, with examples. The D-180 and D-181 notes match the
code, and the counts agree.

Every listed form I planted was refused in all four configurations.

Two kinds of record still claim more than the gates hold:
- **B1. INV-62 is the one listed-form row that did not get the catch-all.** It names only the by-name
  class as not held. INV-63 says "only `EngineClient.swift` sends". The gate itself, by design, lets
  `FrontDoor.swift` make a URL from text and load it. Measured: `make client-decls` passes in all four
  configurations. No gap names this route.
- **B2. Two records state INV-64's property flatly.** `docs/architecture.md:339` and REQ-RTR-004 rest
  it on a text pin. G-11's own first example passes both that pin and the compiled gate. I re-measured
  this round.

The rest is MINOR:
- a PRD sentence that the gate refuses no count of served things;
- docstrings that state G-1's and G-2's examples as settled;
- G-10's claim that every rule has a fixture shape;
- three of this wave's test names.

All probing was done in a scratch mirror (`git archive 011f15d`, the worktree's `.venv` linked). The
worktree was never edited, and `git status` is clean.

## Findings

### BLOCKING

- **B1** `docs/security-invariants.md:123` (INV-62), `:124` (INV-63), `docs/architecture.md:333-334`.
  **The network row names one residue class, and the gate lets the gap register's own file load a URL
  it makes from text.**
  - **The sentences that overclaim.**
    - INV-62: "Only `EngineClient.swift` reaches the network … Held in part: the gate … refuses the
      symbols its lists name; a route by a name `BY_NAME` does not list is not held (gap G-12)."
    - INV-63: "it is inert where it lands, since only `EngineClient.swift` sends and builds a client on
      an address".
    - Architecture: "the network belongs only to `EngineClient.swift`".
  - **Why they claim too much.**
    - Inside Foundation and SwiftUI, `NETWORK`, `FILESYSTEM` and `FORBIDDEN`
      (`scripts/client_decl_gate.py:113-130`, `:138-147`, `:162-225`) are lists of refused symbols.
      They are the same kind of list that `3eee132` rewrote for INV-64, 66 and 76, yet INV-62 alone
      lacks "any other form is not held".
    - The gate also exempts the two stores on purpose:
      - `URL.made` is allowed in `FILESYSTEM_FILES` (`:1902-1904`);
      - `URL.init(_:strategy:)` is on no list;
      - `Data.init(contentsOf` is on `FILESYSTEM` and kept out of `CONTENTS_OF` ("`Data`'s for the two
        stores aside", `:1860-1867`).
    - `Data(contentsOf:)` fetches an https address as readily as a file. `FrontDoor.swift:314-315` says
      so itself.
  - **Measured** (scratch mirror of `011f15d`). I appended this to `FrontDoor.swift`, the file that
    keeps the reader's words:
    ```swift
    func reviewProbeLoad(_ typed: String) -> Data? {
        let target: URL? = try? .init("ht" + "tps://example.invalid/?q=" + typed, strategy: .url)
        guard let target else { return nil }
        return try? Data(contentsOf: target)
    }
    ```
    - `make client-decls` refused nothing in `FrontDoor.swift` in all four configurations, for this
      spelling and for `URL("https://…", strategy: .url)`.
    - The text pin `test_router_hints.py::test_the_gap_register_stays_on_the_device` refused each of
      the three spellings I tried (`http`, `URL(`, `: URL`). I stopped there.
    - So on the compiled module the route is held by nothing. It is held only by the text pin's
      spellings, by review (`FrontDoor.swift` is a security glob, `docs/plans/m21-plan.md:83`) and by
      `FrontDoorTests` on the shipping code. No gap says so.
    - `StandingsStore.swift`'s own Foundation references are held by `SINK_FOUNDATION_ALLOWED`, which
      does not list `URL.init(_:strategy:`. I read that, and did not measure it.
  - **Fix.**
    - **INV-62.** Use the wording INV-64, 66 and 76 use: name the three lists and the two symbol
      allowlists, and say "any other form is not held". Name the two stores' own loads as a gap on an
      issue: a URL their own code makes, loaded with `Data(contentsOf:)`, is held on the compiled
      module by nothing, and otherwise only by the text pin's spellings and by review. Use a new G-13,
      or widen and retitle G-12. Add it to INV-62's "Partial:" list and to the count line.
    - **INV-63.** Replace "since only `EngineClient.swift` sends" with "since no other file may send or
      load a URL; the two stores' own loads are gap G-13".
    - **Architecture.** Change `:333-334` the same way.
    - **REQ-GAP-001.** In its evidence cell (`docs/prd.md:553`), add the new gap and G-10 beside G-1,
      G-11 and G-12.
    - The gate change itself is K1.

- **B2** `docs/architecture.md:339`; `docs/prd.md:468` (REQ-RTR-004). **INV-64's property is stated as
  held by a text pin that G-11's own examples pass.**
  - **The sentences that overclaim.**
    - Architecture: "`tests/unit/test_router_hints.py`: nothing the reader types reaches an engine
      call."
    - REQ-RTR-004: "**MET.** Evidence: test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine;
      EngineClientTests.swift::testNothingTheReaderTypedIsEverSent." The cell states no limit.
  - **What G-11 says.** G-11 (`docs/security-invariants.md:194`) names a key path bound to a `let`
    before the write as not held. It says this pin catches only `task`'s initial value.
  - **Measured.** I added `let surface = \ContentView.task` and `self[keyPath: surface] = question` to
    `submit()`. Both text-pin files passed (107 tests), and `make client-decls` printed PASS, 21 files
    in 4 configurations.
  - **The rewrite missed this bullet.** The architecture's gate line two lines above was rewritten to
    listed-form wording in `3eee132`; this bullet was not.
  - **Fix.**
    - **Architecture `:339`.** "every argument of the screen's engine calls is spelled as the bare
      `task` or `budget`, and `task` is assigned only the listed spellings (INV-64; gap G-11 names forms
      that pass)".
    - **REQ-RTR-004.** Keep MET: its criterion is the shipping app's behaviour, held by
      `EngineClientTests.swift:489`. Add, as REQ-GAP-001 does: "the pin and the compiled request rule
      refuse listed forms only; any other form is not held, gap G-11 (#244)".

### MINOR

- **M1** `docs/prd.md:428` (REQ-APP-005): "it refuses no count of served things".
  - **Measured.** In a new Engine file, `[list.count].map { p in p + 1 }` two lines below
    `for p in list.map(\.position) { _ = p }` is refused as "`+` on a served position" in all four
    configurations. The same line alone, more than five lines from a served `p`, is not.
  - **Already recorded.** D-181's note (`docs/decisions.md:4141-4144`) records this over-refusal.
  - **Why MINOR.** It is the safe direction: more is refused, nothing leaks.
  - **Fix.** Add "except a count bound to the same name as a served loop or closure parameter up to
    five lines above (D-181's note)". Or key named closure parameters by their closure's range, which
    is round 2's M1 fix.

- **M2** Gate and test docstrings that state G-1's or G-2's examples as settled.
  - **The sentences.**
    - `scripts/client_decl_gate.py:247-249`: "so nothing derived from the question can reach them
      through state another file sets". G-1's first example is exactly such state: a constant typed
      `Any` holding an `NSMutableString`, read by a sink.
    - `:32-34`: "neither … reads mutable state another file can set, …, and the code a sink runs
      elsewhere reads no shared mutable state". The same.
    - `:826-827`: "what the boards request and the standings file are built from cannot widen unseen".
      Round 2's B1 constant widens it with every gate green.
    - `:1106`: "Text and bytes, whose length is no served number". `:1161-1162`: "nor is text, whose
      length is no served number". G-2 lists the counts of `String(repeating:count:)`, `Data(count:)`
      and `Data(repeating:count:)`, sized by a served number, as passing.
    - `:1141`: "unless a served number built the list". G-2 holds only three builders.
    - `tests/unit/test_client_decl_gate.py:678-680`: "a mutable container another file holds in a
      constant or a static, are refused where the sink reads them". G-1 says it is not refused when its
      declared type is widened.
  - **Fix.** Reword each to the rule's listed form and point at G-1 or G-2. For example: "a constant
    whose declared type is a class `FOUNDATION_OBJECT` lists or an app class"; "text and bytes are not
    followed into a count; a count of text a served number sized is gap G-2".
  - **Also, while there.** `:39-41` ("nor is a number through `Any` or text") and `:811-812` ("What it
    does not follow: … a global or `static` `let`'s initialiser … and what Foundation holds") are stale
    the other way, since W3 follows both. The "What this gate does NOT do" list should also name the
    two stores' own loads (B1).

- **M3** `docs/security-invariants.md:193` (G-10) and `scripts/client_decl_gate.py:496-498`.
  - **The sentence.** G-10 says "The fixture carries a refused shape for each of the gate's rules …, so
    a change in the compiler's printed layout that silences a rule fails the self-test
    (`FIXTURE_RULES`)".
  - **Two rules have no fixture shape.**
    - INV-64's budget rule, "a budget that is not a `let` given a literal" (`request_facts` `:1710-1713`,
      `_literal_let` `:1622-1635`). The fixture's budget is a literal `let`
      (`scripts/client_decl_fixtures/ContentView.swift:209`), and no unit test covers the rule.
    - `SINK_SWIFT_REFUSED` (`:853`, `:1938-1940`). `FOUNDATION_SHARED`'s `CommandLine` shadows it.
  - **Measured.** `private var budget = "unlimited"` in the shipping `ContentView.swift` is refused
    ("not a literal let") in all four configurations, so the listed form holds today.
  - **Fix.** Make the fixture's budget non-literal, and add the phrase to `FIXTURE_REFUSALS` and
    `FIXTURE_RULES`. Or narrow both sentences to "each rule `FIXTURE_RULES` names".

- **M4** Test names cited in the records that state more than they hold. All three are this wave's,
  not yet merged:
  - `test_every_twin_of_the_refused_surface_is_refused`, cited at `docs/security-invariants.md:125` and
    `docs/prd.md:553`. G-11, in the same row, lists twins it does not refuse.
  - `test_the_readers_text_reaches_no_argument_of_a_request`, at `:125` and `prd.md:553`.
  - `test_a_sink_references_only_its_listed_foundation_and_no_object_another_file_holds`, at `:127` and
    `prd.md:553`. G-1 lists object constants it does not refuse.
  - **Fix.** Rename each to what it holds, for example `test_round_one_twins_of_the_surface_are_refused`.
    Update the citing rows in the same commit: `test_security_invariants.py` fails closed on a stale
    citation.

### PASS (what holds)

- **The rewritten rows list real refusals.** Each listed form below was planted in the mirror's
  shipping client and refused in all four configurations. The first run gave 9 refusal lines per
  configuration: these forms and M1's count. The budget had a run of its own.
  - **INV-64, a mutating call.** `task.append(question)` in `submit()`: "assigns `ContentView.task`
    (inout_expr)". The fixture has no such shape.
  - **INV-64, a direct key-path write.** `self[keyPath: \.task] = question`: "(assign_expr)".
  - **INV-64, the budget.** `private var budget`: "not a literal let" (M3).
  - **INV-66, `CommandLine` in a sink.** `CommandLine.argc` in `EngineClient.boards()`, refused by both
    `SINK_SWIFT_REFUSED` and `FOUNDATION_SHARED`.
  - **INV-66, `FOUNDATION_SHARED` in code a sink runs.** `TimeZone.current` in
    `FetchedStandings.init(payload:)` (`Models.swift`).
  - **G-12's list.** `NSClassFromString`.
  - **INV-76.** `s.position ^ 1`, and `Int("\(s.position)") + 1`, a parser `PARSES_NUMBER` lists.
  - **The control.** `[list.count].map { p in p + 1 }` alone was not refused.
  - **The fixture's own shapes.** The self-test passed at the start of each run, so these held too.
- **Restored by bytes.** Each plant was restored by bytes and its sha256 checked equal:
  - `ContentView.swift` `6fbbfd8d…`;
  - `EngineClient.swift` `11a58324…`;
  - `Models.swift` `a0570e0f…`;
  - `FrontDoor.swift` `8ec9c9a5…`.

  The probe file was removed. `diff -rq` of the mirror's `ios/` and `scripts/` against the worktree
  is empty.
- **Counts.** 77 rows. Eight are partial: INV-62 (G-10, G-12), INV-63 (G-10, G-12), INV-64 (G-10,
  G-11), INV-66 (G-1, G-10, G-12), INV-76 (G-2, G-10), INV-6 (G-5), INV-82 (G-7) and INV-88 (G-9).
  Eight gaps are open: G-1, G-2, G-5, G-7, G-9, G-10, G-11 and G-12. Each gap's row list maps back to
  exactly those rows, which matches the count line (`docs/security-invariants.md:177-178`). B1 adds
  one gap.
- **The ADR notes.** D-180's note (`docs/decisions.md:4033-4046`) and D-181's note (`:4127-4145`)
  match the code:
  - `FOUNDATION_SHARED`'s members, `SINK_SWIFT_REFUSED` and `FOUNDATION_OBJECT`;
  - `PARSES_NUMBER`, `TEXTY_TYPE` and the three builders;
  - the over-refusal that M1 measures.
- **The text tripwire against the compiled gate, on the shipping client.** `served_fields` and
  `_served_numbers()` both give 20 fields, with no difference either way. So the PRD's "derives the
  served fields the compiled gate does" holds today. The test holds it on the fixture
  (`test_client_decl_gate.py:717`).
- **Commit messages.** No record cites a W3 commit by hash. Two subjects overstate, and later commits
  superseded both:
  - `98fb2c6`, "the reader's text reaches no argument of an engine request, on the compiled module";
  - `dbbc3a9`, "gaps G-1 and G-2 close".

  `3b1fc8c` and `3eee132` supersede them. The wave-close record should quote the latter two.
- **Historical records.** The closure reports, earlier wave-close records, `docs/coverage-by-req.md`
  ("read as of M9; the PRD holds the current status") and W-122's ledger row are point-in-time, say so,
  and were not judged.
- **Tests on the head.** pytest: 221 passed. That is `test_client_decl_gate.py` 105,
  `test_ios_client_contract.py` 61, `test_router_hints.py` 46 and `test_security_invariants.py` 9.
  `make client-decls`: PASS, 21 client files in 4 configurations, on a byte-identical mirror of
  `011f15d`.
- **REQ-GAP-001's MET is honest.** Its criterion is the app's behaviour. That behaviour is held by:
  - `FrontDoorTests.swift:674` (`GapRegisterTests`) and `:750` (`GapRegisterHardeningTests`, among them
    `testTheRegisterIsOnlyEverAFileOnThisDevice` and `testASaveToAnythingButAFileTriesNoWrite`);
  - `ReadingTests.swift:343`;
  - `StandingsStoreTests.swift:216`;
  - the text pin.

  The cell states the gates' limits: "enforced by a gate over spellings (the limit W-122 records)",
  the compiled forms as a list, and "Any other form is not held: gaps G-1, G-11, G-12". That first
  phrase is exactly B1's situation, stated honestly. Only the gap list needs B1's new gap and G-10.

## Acceptance criteria evidence

- **REQ-GAP-001.** `ios/EngineTests/FrontDoorTests.swift:674`, `:750`; `ReadingTests.swift:343`;
  `StandingsStoreTests.swift:216`; `tests/unit/test_router_hints.py:540`;
  `tests/unit/test_client_decl_gate.py:644`, `:677`, `:687`, `:730`. The status is MET and honest; the
  gap list is incomplete (B1).
- **REQ-APP-005.** `tests/unit/test_client_decl_gate.py:623` (33 shapes), `:631`, `:638`, `:661`,
  `:668`, `:717`. The status is PARTIAL and honest, except M1.
- **REQ-RTR-004.** `ios/EngineTests/EngineClientTests.swift:489`; `tests/unit/test_router_hints.py:467`.
  The status is MET, but the cell states no limit (B2).

## Producers of the hardened invariants

- **INV-62 and INV-63.**
  - Producers: every client file. The network door is `EngineClient.fetch` (`EngineClient.swift:282`).
    The file-system doors are `GapRegisterStore.load` and `save` (`FrontDoor.swift:313`, `:325`) and
    `StandingsStore.swift`.
  - Citing tests: `test_client_decl_gate.py:32`, `:56` and `::test_reflection_and_the_runtime_by_name_are_refused`;
    `test_router_hints.py:540`.
  - Gaps: G-10, G-12, and B1's.
- **INV-64.**
  - Producers: `ContentView.load()` → `client.recommendation(task:budget:)` (`ContentView.swift:1051`).
    `task` is written at `:28`, `:946` and `:1025`; `budget` is at `:89`.
  - Citing tests: `test_client_decl_gate.py:551`, `:687`; `test_router_hints.py:467`;
    `EngineClientTests.swift:489`.
  - Gaps: G-10, G-11 (B2, M3).
- **INV-66.**
  - Producers: `EngineClient.swift` (`recommendation` `:234`, `categories` `:252`, `boards` `:260`,
    `fetch` `:282`); `StandingsStore.swift` (`save` `:66`, `current` `:79`, `currentKept` `:86`, `:92`);
    `FetchedStandings.init(payload:)` (`Models.swift:421`).
  - Citing tests: `test_client_decl_gate.py:644`, `:677`, `:730`.
  - Gaps: G-1, G-10, G-12 (M2).
- **INV-76.**
  - Producers: `Uncertainty.swift` (`scoreOutOf100`, `distanceOutOf100`, `anchoredFact`),
    `Combine.swift`, and `priceInPages` in `Router.swift` and `Language.swift`.
  - Citing tests: `test_client_decl_gate.py:623`, `:631`, `:661`, `:668`, `:717`.
  - Gaps: G-2, G-10 (M1, M2).

## K.8 contract drift check

Plan §5: "No `/v1` field changes … W3 and W4 change gates, not contracts."

```
$ git diff --stat 0af8dbb..011f15d
 docs/architecture.md                               |  8 +--
 docs/decisions.md                                  | 64 +++++++++++-----------
 docs/prd.md                                        |  4 +-
 ...ve-3-review.md => m21-wave-3-review-round-2.md} |  2 +-
 docs/security-invariants.md                        | 37 ++++++-------
$ git log 972b55e..011f15d --no-merges --format='%h %s' -- src/ schemas/ | grep -c M21-W3
0
```

Verdict: OK. This round touches only records. No W3 commit touches `src/` or `schemas/`; the `src/`
changes in the wave's range are W1's and W2's, already merged.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py:1860-1867`, `:1902-1904`. **The gate change behind B1 is a
  security gap, and it is out of this records-only round.** The compiled gate lets `FrontDoor.swift`,
  which holds the reader's words, make a URL from text and load it.
  - **Fix.** In the two stores, admit only a URL `FileManager` or `appendingPathComponent` makes.
    Alternatively, refuse `URL.init(_:strategy:` and a cast to `URL` there. Plant B1's probe in the
    fixture.
  - **Where to file it.** On #242, or for the closure security seat (D-172).

## Risks queued to next M

- **R1** **A row can miss the catch-all.** INV-62 shows how (B1): the listed-form wording is applied by
  hand, row by row. What would show the risk is real: a later row cites `make client-decls`, is
  partial, and does not say what is not held. A check in `test_security_invariants.py` would catch it:
  every row whose tests cite `make client-decls` and that carries "Partial:" must say "any other form is
  not held". #242's allowlists remain the real fix (round 2's R1).
- **R2** **CI's lane (G-10, #243).** This is unchanged from round 2. On CI only the text pins run, and
  B1's route is held there by spelling alone. What would show the risk is real: a PR merged on CI's
  green alone that carries a change the text pins cannot see.
