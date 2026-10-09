---
record_type: review
id: m21-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 3 Code Review, round 5 (after round 4: does any record still state more than the gates hold?)

**Reviewer:** Code-Reviewer subagent (fresh eyes; wrote none of the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: I read rounds 3 and 4 first,
then the register, the gate, the four test files and the records against each other, then the round's
diff.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `0865e38..659374c`, the answer to round 4:
- `be11e1a`: the wording test, red;
- `770e00e`: the records, docstrings and test names;
- `f6dcc67`: INV-78's branch test renamed;
- `659374c`: the round-4 file's rename.

The wave as a whole is `972b55e..659374c`.
**Risk tier:** HIGH (plan §3, `docs/plans/m21-plan.md:53`, `:76-84`)

## Verdict
BLOCKING

## Summary

The scheme works where it reaches:
- **The rows.** All 15 rows that cite a client gate carry the fixed sentence. They name rules that
  `FIXTURE_RULES` has, and the gaps they name are their own "Partial:".
- **The fixture.** Every rule a row names is refused on the compiled fixture. The two shapes I planted
  in the shipping client were refused in all four configurations.
- **The wording test.** It caught all six of my plants.
- **The tests.** All four test files pass, and `make client-decls` passes on a byte-identical mirror.
- **No rule changed.** This round changes no rule: the gate's code is identical apart from docstrings.

Two records still state more than the gates hold:
- **B1. INV-78 says the privacy pins in `test_router_hints.py` read only code the compiler builds.**
  Eight of that file's pins read the raw text with only `//` comments removed. I measured it: the gap
  register's pin still passes with the line it requires moved under `#if false`. No gap names this.
  The row's cited test name, `test_the_pins_read_no_code_the_compiler_never_builds`, says the same
  thing flatly.
- **B2. REQ-DTL-001 is MET on "Nothing on the screen is computed by the client".** That is INV-76's
  property, and the row has no pointer. The pointer check never reads it, because it cites a pin test
  that no gated row cites.

The rest is MINOR:
- two gate comments still claim "any";
- older cited test names state the property flatly;
- two PRD gap lists are short;
- one `FIXTURE_RULES` phrase is carried by two rules.

**How I probed.** All probing was done in a scratch mirror (`git archive 659374c`, the worktree's
`.venv` linked, the three dependency files back-dated so `make` did not reinstall). The worktree was
never edited, and `git status` is clean apart from this file.

## Findings

### BLOCKING

- **B1** `docs/security-invariants.md:150` (INV-78), `:123` (INV-62's test cell);
  `tests/unit/test_router_hints.py:1045`, `:81`. **A row says what the privacy pins read, and most of
  them do not read that way.**
  - **The sentences.**
    - INV-78: "The privacy pins (`test_router_hints.py`) read code the compiler builds, not comments,
      strings or a branch no build compiles … Other pin files read the raw text."
    - INV-62's annotation on that test: "(what must be built is held by the pins and the Swift tests;
      this gate refuses what must not, #110)".
    - The cited test's name: `test_the_pins_read_no_code_the_compiler_never_builds`.
    - `_code`'s docstring (`:81`): "only what some build compiles".
  - **What the file does.** Eight of its pins never call `_code`. They read the file and drop only
    `//` comments, or nothing at all. Three of them hold gated rows:
    - `:413`/`:425`, INV-69's router pin;
    - `:467`/`:483`, INV-64's request pin;
    - `:541`/`:553`, the gap register pin, which INV-62, INV-67 and REQ-GAP-001 cite.

    `test_ios_client_contract.py` has a guard that every pin reads through `_swift`
    (`test_every_swift_pin_here_reads_the_code_the_compiler_builds`). `test_router_hints.py` has
    none.
  - **Measured** (mirror; `FrontDoor.swift` restored by bytes, sha256 `8ec9c9a549bb32b9…` equal to the
    worktree's).
    - I wrapped `values.isExcludedFromBackup = true` (`FrontDoor.swift:330`) in `#if false … #endif`.
      Then I ran `test_the_gap_register_code_carries_no_egress_spelling_the_pin_reads`. Result:
      **1 passed**. That is #110's own case: a pin satisfied by a line no build compiles.
    - I did the same under `#if os(watchOS)`. Both that pin and
      `test_the_pins_read_no_code_the_compiler_never_builds` passed. `_decide` returns `None` for any
      call-form condition, so `_built` keeps the branch. No target of this repo builds for watchOS
      (`ios/Package.swift:40`: macOS and iOS only).
  - **Why BLOCKING.** It is the class rounds 1 to 4 blocked on. A register row describes what a gate
    does, and a measured case contradicts it. The row's limit, G-14 ("the spellings they read"), does
    not name the residue: the residue is which pins read through `_code`, not how a line is spelled.
    A closure security seat reading INV-78 would trust a presence pin that `#if false` satisfies.
  - **Fix (records).**
    - **INV-78.** Say what holds: "`_code` drops comments, a directive inside a string, and a branch
      whose condition is the literal `false` or `!true` (or the `#else` after `true`); a condition it
      cannot decide keeps its code." Then name the pins that do not read through it: "these pins read
      the text with only `//` comments removed, so a `#if false` or `/* */` copy of a line they
      require satisfies them: <the eight names>". Name that as a gap on an issue, either in G-14's
      text or as a new G-15, and update the Partial lists and the count line.
    - **The test.** Rename `test_the_pins_read_no_code_the_compiler_never_builds` to what it holds,
      for example `test_code_drops_a_branch_whose_condition_is_literally_false`. Update INV-62's and
      INV-78's citations in the same commit.
    - **INV-62's annotation.** "(`_code` drops a literally false branch; that what must be built is
      built is held by the Swift tests)".
    - **`_code`'s docstring.** "at least what some build compiles". `_stripped`'s docstring (`:96`):
      "a branch whose condition is literally false".
    - The code change is K1.

- **B2** `docs/prd.md:570` (REQ-DTL-001); `tests/unit/test_security_invariants.py:424-433`. **A PRD
  row is MET on INV-76's property, with no pointer, and the pointer check cannot see it.**
  - **The sentence.** The criterion says "Nothing on the screen is computed by the client". The status
    is "**MET.** Evidence: DetailTests.swift::DetailFactTests …;
    test_ios_client_contract.py::test_the_detail_screen_is_reachable_and_composes_nothing_itself."
  - **Why it claims too much.**
    - The Swift tests hold the Engine's `detailFacts`. The screen itself (`ModelDetail` in
      `ContentView.swift`, which `swift test` does not compile) is held by the text pin's regexes:
      "The view renders the Engine's facts and NOTHING else" (`test_ios_client_contract.py:1239`).
    - That nothing on the phone changes a served number is INV-76, held in part (G-2, G-10, G-14).
    - This is the shape round 4's B2 blocked on for REQ-CMB-004, and round 3's B2 for REQ-RTR-004:
      MET, with no pointer and no limit.
  - **Why the check misses it.**
    - The PRD branch reads a row only when the row is a gated row's source, cites a test a gated row
      cites, or cites the compiled gate. The detail pin is cited by no register row.
    - The architecture branch keys on `GATE_NAMES`, both pin files included. The PRD branch does not.
  - **Measured.**
    - On the head, the check reads eight PRD rows: REQ-APP-002, APP-005, RTR-002, RTR-004, ASK-001,
      ASK-004, GAP-001 and CMB-004. REQ-DTL-001 is not among them.
    - Six PRD rows cite a pin test and carry no pointer: REQ-APP-001, APP-003, APP-004, RTR-005,
      DTL-001 and PRC-002. Of these, only REQ-DTL-001 states a register property.
    - When I planted a gated test's citation into REQ-DTL-001 (W2b below), the check read the row and
      failed it. So the check works once the row is in its reach.
  - **Fix.**
    - **REQ-DTL-001.** Add: "That the phone changes no number the engine sent is held in part by the
      compiled gate and the text pins: see INV-76 in `docs/security-invariants.md`." MET can stay,
      scoped to the Engine's facts.
    - **The test.** Also read a PRD row that cites any test in `PIN_FILES`, as the architecture branch
      does. Keep an explicit list, each with its reason, of the rows whose property is not on the
      register (REQ-APP-001, APP-003, APP-004, RTR-005, PRC-002), so a new one fails closed. Plant
      REQ-DTL-001 without the pointer, and watch the test fail.

### MINOR

- **M1** `scripts/client_decl_gate.py:136-137`, `:15-16`. **Two gate comments still claim "any".**
  - **The sentences.**
    - `CONTENTS_OF` (`:136-137`): "any initialiser that loads what a URL names (`NSMutableArray(contentsOf:)`,
      `NSAttributedString(url:)` and the classes the next SDK adds), whatever class declares it".
      The regex (`:138`) matches two first labels, `contentsOf:` and `url:`. This round narrowed the
      same claim in `_network_problem`'s docstring (`:1860-1861`, "an initialiser `CONTENTS_OF`
      matches"), but not here.
    - The module allowlist (`:15-16`): "refused by absence, so an API nobody has thought of yet is
      refused too". G-12 (`docs/security-invariants.md:195`) lists by-name routes the gate does not
      hold, for example `Bundle.classNamed(_:)`. A class of a module off the allowlist reached by name
      resolves no declaration in that module.
  - **Fix.**
    - `:136-137`: "an initialiser whose first label is `contentsOf:` or `url:`, whatever class
      declares it; another label is not held (G-14)".
    - `:15-16`: "so a declaration of a module nobody has listed is refused too; a class reached by name
      is G-12".

- **M2** **Cited test names that still state the property flatly.** Round 4's M4 renamed its five,
  and `f6dcc67` renamed one more. These remain, and each is cited by a row whose fixed sentence
  contradicts its name:
  - `tests/unit/test_ios_client_contract.py:353`
    `test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent` (INV-76, REQ-APP-005).
    D-181's own context (`docs/decisions.md:4048-4051`) records `let place = standing.position;
    place + 1` passing it.
  - `:536` `test_the_client_applies_no_ordering_of_its_own` (INV-76, REQ-APP-002). D-181 records a
    second `common.sorted()` passing it.
  - `tests/unit/test_client_decl_gate.py:393` `test_a_sink_holds_nothing_another_file_can_change`
    (INV-66, REQ-GAP-001). The gate's own comment (`:825-826`) says "an object reached through a
    listed declaration, or held behind a widened type, is not held (G-1)".
  - `:405` `test_a_sink_calls_nothing_another_file_declares_but_what_is_listed` (INV-66,
    REQ-GAP-001).
  - `:35` `test_the_network_and_the_file_system_are_refused_outside_their_files` (INV-62). `NETWORK`
    and `FILESYSTEM` are deny-lists (G-14).
  - `:251` `test_a_url_made_by_any_call_outside_its_files_is_refused` (INV-63).
  - **Fix.** Rename each to what it holds and update its citations in the same commit; the register
    test fails closed on a stale one. Or add round 4's sentence to "How it is held": "a cited test's
    name says what it is for; the row, and its fixed sentence, say what it holds".

- **M3** `docs/prd.md:553` (REQ-GAP-001), `:468` (REQ-RTR-004). **Two PRD gap lists are shorter than
  the rows they point at.**
  - **The sentences.**
    - REQ-GAP-001: "Any other form is not held: gaps G-1 (#242), G-10 (#243), G-11 (#244), G-12 (#241)
      and G-13 (#246)". The list omits G-14. Every row the cell points at (INV-62, 63, 64, 66, 67, 68
      and 70) names G-14, and so does the pin the cell cites.
    - REQ-RTR-004: "the pin and the compiled request rule refuse listed forms only, and any other form
      is not held, gap G-11 (#244)". INV-64 names G-10, G-11 and G-14, and the pin holds spellings,
      not forms.
  - **Why MINOR.** Both cells carry the pointer, so a reader reaches the full list.
  - **Fix.** Add G-14 (#242, #243) to REQ-GAP-001. In REQ-RTR-004, write "gaps G-10, G-11 and G-14
    (see INV-64)", or drop the restatement and keep the pointer alone.

- **M4** `scripts/client_decl_gate.py:525`, `:496-497`. **One `FIXTURE_RULES` phrase is carried by
  two rules' refusals.**
  - **The sentence.** `"a sink's Foundation list": "Thread.main"`, under "the rules the fixture holds,
    each by a phrase a refusal of it carries".
  - **Measured.**
    - On the compiled fixture (simulator, release), "Thread.main" in `EngineClient.swift` is carried by
      two refusals. One is the sink list's: "is not on the list of Foundation declarations a privacy
      sink may reference". The other is `FOUNDATION_SHARED`'s: "code a privacy sink runs, uses
      `Thread.main`".
    - My plant in the shipping client gave the same pair in all four configurations.
    - Today the rule is still held, by the separate `FIXTURE_REFUSALS` entry "not on the list of
      Foundation declarations". If that entry went, the rule's named phrase would still be satisfied,
      by the other rule.
  - **Fix.** Map the rule to "not on the list of Foundation declarations". Every other rule's phrase
    matched only its own rule's message.

### PASS (what holds)

- **The rules the rows name exist and refuse.**
  - On the compiled fixture, each of the 27 rules in `FIXTURE_RULES` produced at least one refusal
    carrying its phrase in its file, checked by script.
  - The wording test holds that each rule a row names is one of them.
- **My plants in the shipping client.** Both were planted together, in two files, as written in the
  fixture:
  - **INV-66, rule `a sink's Foundation list`.** `struct … { func threadName() -> String
    { Thread.main.name ?? "" } }` was appended to `EngineClient.swift`. It was refused in all four
    configurations, as M4 describes.
  - **INV-64, rule `the router's outcomes`.** `extension RoutingOutcome { static func …(_ typed:
    String) -> RoutingOutcome { RoutingOutcome(categoryID: typed, …) } }` was appended to
    `Detail.swift`. It was refused in all four configurations: "builds RoutingOutcome", and "extends
    `RoutingOutcome` outside its own file".
  - **Restored by bytes**, with each sha256 equal to the worktree's: `EngineClient.swift`
    `11a583248a320995…`, `Detail.swift` `055acd8708445d7f…`. Afterwards `diff -rq` of the mirror's
    `ios/` against the worktree is empty.
- **The wording test is exact on what it reads.** I made six plants on the mirror's records. Each ran
  the three new tests and `test_the_list_holds_together`. Each file was restored by bytes and its
  sha256 checked equal: `security-invariants.md` `1c8a75bd5935…`, `prd.md` `7bd39d27a6d7…`. Every
  plant failed, as it should:
  - **W1.** INV-85 names a rule the fixture lacks (`the cookie jar`): "INV-85 names rules the fixture
    does not have".
  - **W2a.** I removed the pointer sentence that REQ-ASK-001 and REQ-ASK-004 share; its first
    occurrence, in REQ-ASK-001, was removed. Result: "REQ-ASK-001 … does not point at its row".
  - **W2b.** REQ-DTL-001 newly cites INV-76's pin `test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent`,
    with no pointer: "REQ-DTL-001 … does not point at its row".
  - **W2c.** REQ-APP-002's pointer names INV-64 instead of INV-76: "does not point at INV-[76], which
    it draws on".
  - **W3a.** The count line says 78 rows: "the count line says ('78', '18', '10'); the tables hold (77,
    18, 10)". `test_the_list_holds_together` failed too.
  - **W3b.** The count line says 17 partial rows: "the count line says ('77', '17', '10')".

  After the plants, `diff -rq` of the mirror's `docs/` against the worktree is empty.
- **The records outside the register.**
  - `docs/architecture.md:272-276`, `:328-342` and `:376-377` point at the rows.
  - The D-180 note (`docs/decisions.md:4033-4039`) and the D-181 note (`:4120-4129`) carry the fixed
    sentence and the pointer.
  - AGENTS.md says nothing about the client gates.
  - Round 4's B1 (the count of a built list) is now gap G-2's example, and `_counted`'s docstring
    says the bound form is not followed. Round 4's B2 (REQ-CMB-004) has its pointer.
- **This round changes no rule.** I parsed the three changed Python files with their docstrings and
  test names blanked. At `0865e38` and at `659374c` each gives the same AST.
- **Tests on the head.**
  - pytest: **224 passed**. That is `test_client_decl_gate.py` 105, `test_ios_client_contract.py` 61,
    `test_router_hints.py` 46 and `test_security_invariants.py` 12. The coverage floor reports a
    subset run, as expected.
  - `make client-decls`: "PASS: 21 client file(s) in 4 configuration(s)". This ran on the mirror
    before any plant; the mirror is byte-identical to `659374c` in `ios/`, `scripts/`, `docs/` and
    `tests/`.

## Acceptance criteria evidence

- **REQ-GAP-001.**
  - The status is MET, with the pointer. Its gap list lacks G-14 (M3), and its cited pin reads raw text
    (B1).
  - Evidence: `ios/EngineTests/FrontDoorTests.swift` (`GapRegisterTests`, `GapRegisterHardeningTests`);
    `tests/unit/test_router_hints.py:541`; `tests/unit/test_client_decl_gate.py:157`, `:393`, `:405`,
    `:454`, `:650`, `:683`.
- **REQ-APP-005.**
  - The status is PARTIAL, with the pointer to INV-76.
  - Evidence: `tests/unit/test_client_decl_gate.py:368`, `:629` (33 shapes), `:637`, `:644`, `:725`.
- **REQ-RTR-004.**
  - The status is MET, with the pointer. Its gap list is short (M3).
  - Evidence: `ios/EngineTests/EngineClientTests.swift::testNothingTheReaderTypedIsEverSent`;
    `tests/unit/test_router_hints.py:467`.
- **REQ-DTL-001.** The status is MET with no pointer (B2).

## Producers of the hardened invariants

These are unchanged from round 4, since this round changed records and names only.
- **INV-62 and INV-63.**
  - Producers: `EngineClient.fetch`; `GapRegisterStore.load` and `save` (`FrontDoor.swift`);
    `StandingsStore.swift`.
  - Gaps: G-10, G-12, G-13, G-14. B1's raw-reading pins sit here too.
- **INV-64.**
  - Producers: `ContentView.load()` → `client.recommendation(task:budget:)`.
  - Gaps: G-10, G-11, G-14. Its pin reads raw text (B1).
- **INV-66.**
  - Producers: `EngineClient.swift`, `StandingsStore.swift`, `FetchedStandings.init(payload:)`.
  - Gaps: G-1, G-10, G-12, G-14.
- **INV-76.**
  - Producers: `Uncertainty.swift`, `Combine.swift`, `priceInPages`.
  - Gaps: G-2, G-10, G-14. REQ-DTL-001 restates it (B2).
- **INV-78.**
  - Producer: `_code` and the pins that call it.
  - Gaps: G-14 only. The eight pins that bypass it are B1.

## K.8 contract drift check

Plan §5 (`docs/plans/m21-plan.md:96`): "No `/v1` field changes … W3 and W4 change gates, not
contracts."

```
$ git diff --stat 0865e38..659374c
 docs/architecture.md                               |   6 +-
 docs/decisions.md                                  |  50 ++----
 docs/prd.md                                        |  16 +-
 ...ve-3-review.md => m21-wave-3-review-round-4.md} |   2 +-
 docs/security-invariants.md                        |  49 +++---
 scripts/client_decl_gate.py                        |  76 ++++-----
 tests/unit/test_client_decl_gate.py                |  26 +--
 tests/unit/test_router_hints.py                    |  17 +-
 tests/unit/test_security_invariants.py             | 182 ++++++++++++++++-----
$ git diff --name-only 0865e38..659374c -- src schemas ios | wc -l
       0
```

Verdict: OK. This round touches no contract surface.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_router_hints.py:413`, `:467`, `:541` and five more (`:229`, `:284`, `:703`,
  `:845`, `:861`). **The code change behind B1.**
  - Eight pins in this file, written before W3, read Swift without `_code`.
  - Route each through `_code`. Then add the guard `test_ios_client_contract.py` already has
    (`test_every_swift_pin_here_reads_the_code_the_compiler_builds`), with a `# raw:` escape for a
    deliberate raw read.
  - Plant the backup-exclusion line under `#if false` and watch the gap register pin fail.
  - This is pin code, not records, so it can go on #243 or a new issue.
- **K2** `docs/prd.md:570` (REQ-DTL-001's criterion). **The criterion contradicts itself.** It
  requires the per-pages price, which `priceInPages` computes on the phone (REQ-CMP-002, D-181
  clause 3), and then says "Nothing on the screen is computed by the client". Reword it to "nothing
  beyond what a ruling names".

## Risks queued to next M

- **R1** **An invariant clause that describes a gate's own mechanism sits outside the fixed sentence.**
  INV-78 says how the pins read, not what the app does, so "any other spelling is not held" does not
  limit it (B1).
  - **What would show the risk is real:** another row whose clause says how a gate or a pin reads the
    code, measured false. The wording test checks the fixed sentences, not such clauses.
  - **A cheap guard:** each such clause cites the test that holds it for every pin or file it names,
    as `test_every_swift_pin_here_reads_the_code_the_compiler_builds` does for one file.
- **R2** **CI's lane (G-10, #243).** This is unchanged. On CI only the text pins run, and B1 shows
  that some of them read dead code.
