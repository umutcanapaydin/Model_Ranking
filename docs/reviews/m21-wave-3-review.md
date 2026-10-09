---
record_type: review
id: m21-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 3 Code Review, round 4 (after round 3: does any record still claim more than the gates hold?)

**Reviewer:** Code-Reviewer subagent (fresh eyes; wrote none of the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: I read rounds 1 to 3 first,
then `git show 5ab4077 45a2c68`, then the register, the gate and the records against each other.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `138ec0b..929e97a`, the answer to round 3:
- `5ab4077`: the wording test, red;
- `45a2c68`: the records, docstrings and test names;
- `929e97a`: the round-3 file's rename.

The wave as a whole is `972b55e..929e97a`.
**Risk tier:** HIGH (plan §3, `docs/plans/m21-plan.md:53`, `:76-84`)

## Verdict
BLOCKING

## Summary

The catch-all scheme mostly works:
- **The register's catch-alls.** All 15 rows that cite a client gate say "Held in part". Each ends with
  the catch-all, naming exactly its own "Partial:" gaps.
- **The counts.** 18 partial rows and 10 open gaps. Each gap's Rows column matches the rows that name
  it.
- **G-14** is honest.
- **The forms I planted.** Three listed forms were refused as the rows say.
- **The tests.** All four test files pass, and `make client-decls` passes on a byte-identical mirror.

Two records still state more than the gates hold:
- **B1.** INV-76 and D-181's note list "a count of what a served number built" for three builders.
  The gate refuses it only when the count is read directly off the builder's call. Bind the list to a
  name first, and all three builders pass in all four configurations.
- **B2.** REQ-CMB-004 is MET on "the question's text, its refinements and the reader's removals never
  leave the phone". It has no pointer and no limit, the shape round 3's B2 blocked on. The new pointer
  check never reads a PRD row that cites only a text pin.

The rest is MINOR:
- the wording test does not hold three of the plants it should;
- G-13 overstates the gap for `StandingsStore.swift`;
- some gate and test comments still claim every rule;
- older cited test names state their property flatly.

**How I probed.** All probing was done in a scratch mirror (`git archive 929e97a`, the worktree's
`.venv` linked, the three dependency files back-dated so `make` did not reinstall). The worktree was
never edited, and `git status` is clean apart from this file.

## Findings

### BLOCKING

- **B1** `docs/security-invariants.md:142` (INV-76); `docs/decisions.md:4138-4139` (D-181's M21-W3
  note). **A "Held in part" row lists a form the gate refuses only when it is written inline.**
  - **The sentences.**
    - INV-76: "… and a count of what a served number built, for the builders the fixture holds
      (`Array(repeating:count:)`, a range's bound, `dropFirst(_:)`)."
    - D-181's note: "A count of what a served number built is followed for the builders the fixture
      holds (`Array(repeating:count:)`, a range's bound, `dropFirst(_:)`)".
  - **Measured.** In the mirror I appended these to `Engine/Reading.swift` and ran `make client-decls`:
    ```swift
    func reviewR4Inline(_ s: Standing) -> Int { Array(repeating: 0, count: s.position).count + 1 }
    func reviewR4BoundArray(_ s: Standing) -> Int {
        let built = Array(repeating: 0, count: s.position)
        return built.count + 1
    }
    func reviewR4BoundRange(_ s: Standing) -> Int {
        let range = 0..<s.position
        return range.count * 2
    }
    func reviewR4BoundDrop(_ s: Standing) -> Int {
        let rest = [1, 2, 3].dropFirst(s.position)
        return rest.count + 1
    }
    ```
    - **The control.** The inline line (the fixture's own shape, `Arithmetic.swift:103`) was refused
      at `Reading.swift:429` in all four configurations: "`+` on a served position".
    - **The bound forms.** None of the three was refused in any configuration. The run's only other
      refusals were B2's probe in `StandingsStore.swift` (M2).
  - **Why.** `_counted` (`scripts/client_decl_gate.py:1167-1177`) reads the arguments of the call the
    count is taken off. A name bound to the built list carries no served number, so `built.count` reads
    nothing. D-181's own flow follows a served number through a binding (clause 2), so "is followed"
    reads as including this form.
  - **Fix (records).** State the form as the gate holds it. In INV-76: "a count read directly off the
    call that builds the list from a served number, written inline (`Array(repeating:count:)`, a range,
    `dropFirst(_:)`); the same list bound to a name first is not held (G-2)". Say the same in D-181's
    note, and add the bound form to G-2's examples. The gate change itself is K1.

- **B2** `docs/prd.md:615` (REQ-CMB-004); `tests/unit/test_security_invariants.py:357`. **A PRD row
  states an egress property as MET, without pointer or limit. The pointer check cannot see it.**
  - **The sentence.** The criterion: "The question's text, its refinements and the reader's removals
    never leave the phone; the surface does, as `task`". The status: "**MET: M20-W4's answer plan reads
    the family and the refinements (D-188 clause 6).**"
  - **Why it claims too much.**
    - The cell's only evidence that touches egress is
      `test_router_hints.py::test_only_the_answer_plan_reads_refinements_from_the_words`. That is a
      text pin INV-89 cites, and INV-89 is "Held in part" (G-10, G-14).
    - What reaches the sinks is INV-66, held in part (G-1). Round 2's B1 constant carried
      question-derived state to a sink with every gate green.
    - This is the shape round 3's B2 blocked on for REQ-RTR-004: MET, with no limit in the cell.
  - **Why the new test misses it.**
    - The PRD branch (`:357`) reads a row only if a gated register row names it in its Source column,
      or if it cites `test_client_decl_gate.py` or `client-decls`. INV-89's Source column names
      "D-188 clause 6", not REQ-CMB-004.
    - The architecture branch keys on `GATE_NAMES`, which includes both text-pin files. The PRD branch
      does not.
  - **Measured.** Running the test's own functions on the head:
    - the check reads exactly three PRD rows (REQ-APP-005, REQ-RTR-004, REQ-GAP-001);
    - 11 rows cite a text-pin file and are never read;
    - five of them cite a test that a gated register row cites, and carry no pointer: REQ-APP-002
      (INV-76's test), REQ-RTR-002 (INV-69's), REQ-ASK-001 and REQ-ASK-004 (INV-68's and INV-70's),
      and REQ-CMB-004 (INV-89's).
  - **Fix.**
    - **REQ-CMB-004.** Add "That nothing derived from the question leaves the phone is held in part by
      the compiled gate and the text pins: see INV-64, INV-66 and INV-89 in
      `docs/security-invariants.md`." MET can stay, scoped to the reading.
    - **The test.** Also read a PRD row that cites a test a gated register row cites, derived from the
      register as `sources` is. Then give the other four rows the pointer: REQ-APP-002 already states
      "a tripwire on spellings", but not in the pointer's words. Plant a REQ-CMB-004 without the
      pointer, and watch the test fail.

### MINOR

- **M1** `tests/unit/test_security_invariants.py:285-321` (`gate_row_problems`), `:324-363`
  (`pointer_problems`). **The wording test is exact on the catch-all, but not on the gap table, the
  count line, or a restatement.**
  - **The method.** Seven plants were made on the mirror's records. Each run was
    `test_the_list_holds_together` plus the two new tests. Each file was restored by bytes, and its
    sha256 checked equal: `security-invariants.md` `b9657441…`, `architecture.md` `b433cb3e…`.
  - **Plants that fail, as they should.**
    - P1: INV-70 without its catch-all ("does not end with the catch-all").
    - P2: INV-67's catch-all naming `(G-10, G-14)` against its Partial's G-10, G-13, G-14.
    - P4: a gate-naming architecture bullet with no pointer ("the network belongs only to
      `EngineClient.swift`").
  - **Plants that pass.**
    - **P3.** G-13's Rows column drops INV-67, while INV-67 still names G-13 in its Partial and its
      catch-all. No test compares a gap's Rows column with the rows that name it.
    - **P3b.** The count line reads "Twelve hold only in part … Four gaps are open". The words are
      not checked. Only "77 rows" is.
    - **P5.** I added this §8 bullet: "**Only `EngineClient.swift` reaches the network**, and nothing
      typed reaches a request: the compiled module refuses every other route." It names no gate, so
      the check never reads it.
    - **P6.** I added a gate-naming bullet that has the pointer and also says "nothing typed reaches a
      request, on the compiled module". The check requires the pointer to be present. It does not
      check that the claim is absent.
  - **The head itself.** On the head, the gap table and the count line are right; I checked every gap
    by script. So P3 and P3b leave nothing wrong now: they are drift the test would not catch. P5 and
    P6 are the limits round 3's R1 predicted.
  - **Cosmetic, the P5 class in the tree.** `docs/architecture.md:272-273` says "`Refinements.read`, …
    the one reader a gate holds (INV-89)" of a row that is held in part.
  - **Fix.**
    - Check that each gap's Rows column equals the set of rows whose Partial names it.
    - Compare the count line's two numbers with the tables. Write them as numerals, or map the words.
    - State P5 and P6 as the check's limits in its docstring: a restatement that names no gate, or that
      sits beside a pointer, is not read.
    - Reword `:272-273` to "the one reader, held in part by the text pins (INV-89)".

- **M2** `docs/security-invariants.md:196` (G-13), `:123` (INV-62), `:128` (INV-67);
  `scripts/client_decl_gate.py:43-45`. **G-13 says the two stores' own URL loads are held "by nothing".
  For `StandingsStore.swift` they are not.**
  - **Measured.** I appended round 3's probe to the mirror's `StandingsStore.swift`:
    `try? .init("ht" + "tps://example.invalid/?q=" + typed, strategy: .url)`, then
    `Data(contentsOf:)`. `make client-decls` refused it in all four configurations, twice:
    "`Foundation.URL.init(_:strategy:` is not on the list of Foundation declarations a privacy sink may
    reference", and the same for `ParseStrategy.url`.
  - **Where nothing holds it.** The store is a privacy sink, and `SINK_FOUNDATION_ALLOWED` is an
    allowlist. Only `FrontDoor.swift`, which is not a sink, has the route round 3 measured as held by
    nothing.
  - **Why MINOR.** This is the safe direction: the record understates the gate.
  - **Fix.** G-13: "In `FrontDoor.swift`, a URL its own code makes … loaded with `Data(contentsOf:)`,
    is held on the compiled module by nothing. In `StandingsStore.swift`, a privacy sink, a Foundation
    declaration off `SINK_FOUNDATION_ALLOWED` is refused (`URL.init(_:strategy:)` among them,
    measured), and any other form is not held (G-1)." Apply the same wording to the gate's docstring,
    and to "the two stores' own URL loads" in INV-62 and INV-67.

- **M3** Gate and test comments that still claim every rule, or no route.
  - **The sentences.**
    - `tests/unit/test_client_decl_gate.py:9-10` (the module docstring) and `:79-80`: "so the gate
      cannot pass the app while it has stopped refusing". G-10 (`docs/security-invariants.md:193`) and
      the gate's own comment (`scripts/client_decl_gate.py:500-503`) now say two rules have no fixture
      shape: the budget's literal `let` and `SINK_SWIFT_REFUSED`. Either can go quiet with the gate
      passing.
    - `:599-601`: the name `test_every_rule_has_a_refused_shape_in_the_fixture`, and "each rule the gate
      applies has at least one refusal". The test iterates `FIXTURE_RULES` only. `:586-587` says the
      same ("a refused shape per rule").
    - `scripts/client_decl_gate.py:292-294`: a routed outcome "is built only by the router and the
      answer plan, so no file can make one from what was typed". Those two files build outcomes from
      what was typed, by design. What they put in the surface is held on the compiled module by nothing
      (G-11, INV-64's row).
    - `:318-320`: "and `select` refuses anything else". That is INV-70, a text pin only (G-14).
  - **Fix.**
    - "while a rule `FIXTURE_RULES` names has stopped refusing (G-10)".
    - Rename the test to `test_each_rule_fixture_rules_names_has_a_refused_shape`.
    - "so no other file builds one (`PROVENANCE_BY_TYPE`); what those two put in its surface is gap
      G-11".
    - "(`select`'s guard is INV-70, a text pin)".

- **M4** **Test names, cited by rows this round rewrote, that state the property flatly.** Round 3's M4
  renamed this wave's three. These are older, and each row's catch-all now contradicts them:
  - `tests/unit/test_client_decl_gate.py::test_arithmetic_on_a_served_number_is_refused_whatever_carries_it`
    (INV-76, REQ-APP-005). G-2 names carriers that pass.
  - `tests/unit/test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine` (INV-64,
    G-11, REQ-RTR-004). Round 3 measured G-11's bound key path passing it.
  - `test_client_decl_gate.py::test_the_code_a_sink_runs_reads_no_shared_mutable_state` (INV-66,
    REQ-GAP-001). G-1 names `Calendar.current`.
  - `test_router_hints.py::test_the_sink_pins_refuse_shared_state_however_it_is_declared` (INV-66). A
    text pin; G-14.
  - `test_router_hints.py::test_the_gap_register_stays_on_the_device` (INV-62, INV-67, REQ-GAP-001).
    G-13.
  - **Fix.** The cheaper fix is one sentence in the register's "How it is held": "a cited test's name
    says what it is for; the row, and its catch-all, say what it holds". The other fix is to rename
    each test and update its citations in the same commit.

### PASS (what holds)

- **The listed forms I planted were refused.** Each was planted alone in the mirror, in a non-door
  file:
  - **INV-63.** `value as? URL` in `Notices.swift`: "makes a URL", in all four configurations.
  - **INV-75.** `ProcessInfo.processInfo.environment` in `Language.swift`: "a Debug-only UI test hook",
    in the two Release configurations only, as the row says.
  - **INV-76.** The inline count-of-built form, as above (B1's control).
- **Restored by bytes.** Every plant was restored by bytes, and its sha256 checked equal:
  - `Notices.swift` `300532cb…`;
  - `Language.swift` `830dda5a…`;
  - `Reading.swift` `ad872a6e…`;
  - `StandingsStore.swift` `7745bfa2…`.

  Afterwards `diff -rq` of the mirror's `ios/`, `scripts/`, `docs/` and `tests/` against the worktree
  is empty.
- **The catch-all and the counts.**
  - 77 rows; 15 say "Held in part", each with the catch-all naming exactly its Partial.
  - 18 rows are partial: those 15, and INV-6, INV-82 and INV-88.
  - 10 gaps: G-1, G-2, G-5, G-7, G-9, G-10, G-11, G-12, G-13 and G-14.
  - Every gap's Rows column equals the set of rows that name it, computed by script. No other record
    counts gaps.
- **G-14 is honest.** It lists the deny-lists (`NETWORK`, `FILESYSTEM`, `FORBIDDEN`, `DEBUG_ONLY`,
  `PROVENANCE`) and not the allowlists (modules, UIKit, CoreFoundation, sink Foundation, held types,
  calls). The text-pin-only rows INV-68 to INV-72 and INV-78 carry it. **G-13 is honest for
  `FrontDoor.swift`** (round 3's measurement) and overstated for the store (M2).
- **The records outside the register.**
  - `docs/architecture.md:329-342` and `:376-377` point at the rows.
  - REQ-APP-005, REQ-RTR-004 and REQ-GAP-001 point at the rows. REQ-RTR-004 also states G-11, and
    REQ-GAP-001's gap list now has G-10 and G-13.
  - The D-180 note (`docs/decisions.md:4033-4046`) and the D-181 note (`:4127-4145`) say "any other
    form is not held". The exception is B1's sentence.
  - AGENTS.md says nothing about the client gates.
  - D-181's "refuses no count of served things" is gone from REQ-APP-005, which was round 3's M1.
- **`45a2c68` changes no rule.** Every changed line of `scripts/client_decl_gate.py` is a comment or
  a docstring.
- **Tests on the head.**
  - pytest: 223 passed. That is `test_client_decl_gate.py` 105, `test_ios_client_contract.py` 61,
    `test_router_hints.py` 46 and `test_security_invariants.py` 11. The coverage floor reports a
    subset run, as expected.
  - `make client-decls`: "PASS: 21 client file(s) in 4 configuration(s)", on the mirror before any
    plant. The mirror is byte-identical to `929e97a` in `ios/` and `scripts/`.

## Acceptance criteria evidence

- **REQ-GAP-001.**
  - The status is MET and the cell points at INV-62 to INV-67 with its gaps. That is honest, with
    M2's nuance.
  - Evidence: `ios/EngineTests/FrontDoorTests.swift` (`GapRegisterTests`,
    `GapRegisterHardeningTests`); `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device`;
    `tests/unit/test_client_decl_gate.py:157`, `:648`, `:681`, `:692`, `:736`.
- **REQ-APP-005.**
  - The status is PARTIAL and points at INV-76, whose listed count form is B1.
  - Evidence: `tests/unit/test_client_decl_gate.py:368`, `:627` (33 shapes), `:635`, `:665`, `:723`.
- **REQ-RTR-004.**
  - The status is MET, with the pointer and G-11.
  - Evidence: `ios/EngineTests/EngineClientTests.swift::testNothingTheReaderTypedIsEverSent`;
    `tests/unit/test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine` (M4).

## Producers of the hardened invariants

These are unchanged from round 3, since this round changed records only.
- **INV-62 and INV-63.**
  - Producers: `EngineClient.fetch`; `GapRegisterStore.load` and `save` (`FrontDoor.swift`);
    `StandingsStore.swift`.
  - Gaps: G-10, G-12, G-13 (M2), G-14.
- **INV-64.**
  - Producers: `ContentView.load()` → `client.recommendation(task:budget:)`.
  - Gaps: G-10, G-11, G-14.
- **INV-66.**
  - Producers: `EngineClient.swift`, `StandingsStore.swift`, `FetchedStandings.init(payload:)`.
  - Gaps: G-1, G-10, G-12, G-14.
- **INV-76.**
  - Producers: `Uncertainty.swift`, `Combine.swift`, `priceInPages`.
  - Gaps: G-2 (B1 belongs here), G-10, G-14.

## K.8 contract drift check

Plan §5 (`docs/plans/m21-plan.md:96`): "No `/v1` field changes … W3 and W4 change gates, not
contracts."

```
$ git diff --stat 138ec0b..929e97a
 docs/architecture.md                               |  29 +++--
 docs/prd.md                                        |   6 +-
 ...ve-3-review.md => m21-wave-3-review-round-3.md} |   2 +-
 docs/security-invariants.md                        |  43 ++++---
 scripts/client_decl_gate.py                        |  77 ++++++------
 tests/unit/test_client_decl_gate.py                |  30 +++--
 tests/unit/test_security_invariants.py             | 132 +++++++++++++++++++++
$ git diff --name-only 138ec0b..929e97a -- src schemas ios | wc -l
       0
```

Verdict: OK. This round touches no contract surface.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py:1149`, `:1167-1177` (`_reach`, `_counted`). **The gate change
  behind B1.** A count is followed only into the call written as its receiver. Mark a name bound to a
  list a listed builder made from a served number as carrying its count. Plant B1's three bound forms in
  `scripts/client_decl_fixtures/Arithmetic.swift`. On #242, the allowlist work, since the records
  answer B1 for now.

## Risks queued to next M

- **R1** **The listed forms are written from the fixture's shapes, not from the gate's mechanism.**
  B1's form names what the builders build, while `_counted` matches only the inline call. That is the
  fourth round in which a record says more than the code does.
  - **What would show the risk is real:** another listed form in a "Held in part" row passes once it is
    written over two lines, or through a binding.
  - **A cheap guard:** each listed form in INV-63, INV-64, INV-66 and INV-76 gets a two-line variant in
    the fixture, refused or named as a gap.
  - **The real fix** remains #242's allowlists.
