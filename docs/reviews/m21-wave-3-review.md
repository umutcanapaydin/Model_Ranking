---
record_type: review
id: m21-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 Wave 3 Code Review, round 6 (W3's own text: does any sentence or test name state more than the gates hold?)

**Reviewer:** Code-Reviewer subagent (fresh eyes; wrote none of the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: I read rounds 4 and 5 first,
then `git show 962af31 b46e976`, then the text W3's own commits wrote, found by `git blame` at
`15ebc57`, against the gate, the pins and the wording test.
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `b22859a..15ebc57`, the answer to round 5:
- `962af31`: the PRD branch of the wording test, red;
- `b46e976`: the records, docstrings, names and comments;
- `15ebc57`: the round-5 file's rename.

W3's own scope is the 46 commits of `git log --no-merges origin/closure/m20..15ebc57 ^661426c^2`. That is
`972b55e..15ebc57` without the W1 and W2 merges `97c4059` and `661426c`.
**Risk tier:** HIGH (plan §3, `docs/plans/m21-plan.md:53`)
**Scope (the lead's ruling for round 6):** W3's own diff, and the record lines, docstrings, comments and
test names that W3's commits added or changed. Older overclaiming records go to M21-W4 under #248 and
are K.9 here, never BLOCKING.

## Verdict
MINOR

## Summary

Round 5's two blockers are closed:
- **B1.** INV-78 now says what `_code` drops. G-15 (#247) names the raw-reading pins and carries
  round 5's measurement. The renamed test and the narrowed docstrings say what they hold.
- **B2.** REQ-DTL-001 points at INV-76. The PRD branch now reads every row that cites a gate test, and
  my four plants against it failed as they should.

I found no sentence in scope that states more than the gates hold for a property on the register.

Five MINOR findings remain:
- **G-15 is not exact** (M1, M2). It counts seven raw-reading pins, and the file has eight, plus one
  raw read inside a ninth. INV-78 also does not say that `_swift` keeps comments, so G-15's `/* */`
  half applies to the contract pins too; I measured it on INV-71's pin. Neither touches a row's
  property, as each finding explains.
- **The text tripwire** (M3). A W3 comment and a cited W3 test name say the text list equals the
  compiled one. They are held equal on the fixture only; measured.
- **The PRD branch** (M4). It reads a row by the gate file's name, so a bare test name is not read.
- **A stale sentence** (M5) in the "Narrowed by M21-W3" paragraph.

**How I probed.** All plants ran in a scratch mirror (`git archive 15ebc57`, the worktree's `.venv`
linked). Each planted file was restored by bytes, and its sha256 was checked equal to the worktree's.
Afterwards `diff -rq` of the mirror's `docs/` and `ios/` against the worktree is empty. The worktree was
never edited, and `git status` is clean apart from this file.

## Findings

### BLOCKING

None.

### MINOR

- **M1** `docs/security-invariants.md:198` (G-15), `:150` (INV-78's G-15 sentence);
  `tests/unit/test_router_hints.py:81-82` (`_code`), `:97` (`_stripped`). **G-15 counts seven pins that
  read the Swift without `_code`. The file has eight, and a ninth reads one file raw.**
  - **The sentences.**
    - G-15: "Seven pins in `tests/unit/test_router_hints.py` read the Swift without `_code` … and four
      more INV-78 names".
    - `_code`'s docstring: "Seven pins here read the Swift without it (G-15)".
    - INV-78's G-15 sentence names those seven.
  - **What the file does.**
    - `test_every_described_surface_has_example_questions_for_the_wording_tier` (`:267`) reads
      `Router.swift` raw, through `_example_counts` (`:258`) and `_hint_ids` (`:221`). Nothing names it.
    - `test_only_tests_hand_the_gap_register_a_writer_of_their_own` (`:878`, cited by INV-67) reads the
      app through `_code`. Its last assertion (`:897`) reads `ios/EngineTests/FrontDoorTests.swift` raw.
  - **Measured (G1).** I moved `Router.swift`'s `mathematics` examples into a `/* … */` block, so no
    build has them. The wording-tier pin gave **1 passed**. `Router.swift` was restored by bytes
    (sha256 `6e8ba539d06b41b3…`, equal).
  - **Why MINOR.**
    - No register row, PRD row or decision cites the eighth pin.
    - The ninth's raw read checks only that a test still passes a writer. That is hygiene, not
      INV-67's property.
    - So no row states more than its pins hold. But G-15 is the record of exactly this mechanism, so
      its list should match the file.
  - **Also.** `_stripped`'s docstring (`:97`) says "A branch whose condition is literally false is
    dropped too (#110, `_built`)". `_stripped` drops no branch: `_code` does, as
    `_built(_stripped(…))`. `test_ios_client_contract.py:39` calls `_stripped` on its own.
  - **Fix.**
    - Write "Eight pins" in G-15 and in `_code`'s docstring. Add the wording-tier pin to INV-78's
      G-15 sentence ("and five more INV-78 names").
    - Name `:897`'s raw read of `FrontDoorTests.swift` in G-15, or route it through `_code`.
    - Reword `_stripped`'s docstring to "`_code` then drops a branch whose condition is literally
      false (`_built`)".
    - Carry the same list to #247.

- **M2** `docs/security-invariants.md:150` (INV-78), `:198` (G-15);
  `tests/unit/test_ios_client_contract.py:34-39` (`_swift`), `:196`. **INV-78 says the contract pins read
  through `_swift`, and stops there. `_swift` keeps comments, so G-15's `/* */` half applies to them as
  well, and no gap names it.**
  - **The sentence.** INV-78: "The client contract pins (`test_ios_client_contract.py`) read every Swift
    file through `_swift`."
  - **What holds.**
    - `_swift` drops a literally false branch and keeps comments; its own docstring says so.
    - Most contract pins then cut each line at `//`, which leaves `/* */` text in place.
    - So G-15's `#if false` half does not apply to them, and its `/* */` half does. G-15 is scoped to
      `test_router_hints.py`. The rows that cite contract pins (INV-68, INV-70, INV-71, INV-72 and
      INV-76) name only G-14.
  - **Measured (G2).** In `EngineClient.swift` I replaced the read's `upTo:
    EngineClient.byteCeiling(for: path))` with `upTo: Int.max)`, and kept the original line in a
    `/* */` comment below it. INV-71's pin, `test_every_response_is_read_through_its_routes_ceiling`,
    gave **1 passed**. `EngineClient.swift` was restored by bytes (sha256 `11a583248a320995…`, equal).
  - **One more.** `:196` (`test_no_held_out_question_is_written_into_the_code_or_its_tests`) reads every
    `.swift` raw, marked `# raw:`. That is deliberate and the stricter direction for a leak check, so
    "every Swift file through `_swift`" understates that pin.
  - **Why MINOR.**
    - INV-78 says nothing false about what `_swift` drops.
    - G-14's words ("match the spellings they read") cover a spelling a pin reads inside a comment.
    - INV-71 is also held by Swift tests on the Mac.

    But the register now names the `/* */` residue for the router pins only. A closure seat could read
    that asymmetry as the contract pins being immune. The guard INV-78 cites is named
    `…reads_the_code_the_compiler_builds` (K1).
  - **Fix (records).**
    - In INV-78, write: "… read every Swift file through `_swift`, which drops a literally false branch
      and keeps comments, so a `/* */` copy of a line a contract pin requires satisfies it; the
      held-out check reads raw on purpose."
    - Either widen G-15 to say this, with the rows' Partial lists, or open it on #247. The code change
      is K1.

- **M3** `tests/unit/test_ios_client_contract.py:286-288`; `tests/unit/test_client_decl_gate.py:725`.
  The test is cited by INV-76 (`docs/security-invariants.md:142`) and REQ-APP-005 (`docs/prd.md:428`).
  **The text tripwire is said to read what the compiled gate reads. The two are held equal on the
  fixture only.**
  - **The sentences.**
    - The comment: "The compiled gate reads the same from the compiler (`served_fields`); this is its
      half for the lanes with no Xcode, so the two lists cannot say different things."
    - The test name: `test_the_text_tripwire_reads_what_the_compiled_gate_reads`.
  - **What holds.**
    - The test asserts equality on the fixture. On the shipping client it asserts only that four
      facts are in the text list (`:731-735`).
    - D-181's note says it exactly: "held equal on the fixture (#169)"
      (`docs/decisions.md:4128-4129`).
  - **Measured.** I wrote a probe file in scratch, outside the tree. It holds `struct ProbeRange:
    Decodable { let low, high: Double }` and `struct ProbeWrapped` with `: Decodable` on its own next
    line, holding `let wrapped: Double`.
    - I ran the gate's `served_fields` on its AST (`xcrun swiftc -typecheck -dump-ast`, simulator
      target). It names `ProbeRange.high`, `ProbeRange.low` and `ProbeWrapped.wrapped`.
    - `_served_numbers` names none of them.
    - On CI, where only the text half runs (G-10), arithmetic on such a field would go unwatched.
  - **Why MINOR.**
    - This is a comment and a test name. The rows' fixed sentences and D-181's note say what is held.
    - Round 3's M4 treated this wave's own test names the same way.
    - Round 1's M3 flagged this comment. The derivation was widened, but the comment stayed.
  - **Fix.**
    - Reword the comment: "… held equal on the fixture; another declaration form may differ, and on CI
      only the text list runs (G-10)".
    - Rename the test, for example to `test_the_text_tripwire_names_the_compiled_served_fields_on_the_fixture`.
      Update INV-76 and REQ-APP-005 in the same commit.

- **M4** `tests/unit/test_security_invariants.py:521-526` (the test's docstring), `:304`
  (`PRD_GATE_CITATIONS`), `:425-427` (`pointer_problems`' docstring). **The PRD branch reads a row by the
  gate file's name, not by the test's.**
  - **The sentence.** "a PRD row that cites any gate test points at the row instead, unless the PRD row
    is listed in NOT_ON_REGISTER".
  - **Measured (P5).** REQ-CMP-002 gained: "The detail pin
    (test_the_detail_screen_is_reachable_and_composes_nothing_itself) holds that nothing on the screen is
    computed." That is INV-76's property, through a gate test with no file and no pointer. The result
    was **1 passed**.
    - No row on the head cites a gate test without its file. I checked all 137 gate tests by script,
      so nothing is wrong now.
    - `pointer_problems`' docstring still lists only the three older triggers.
  - **Fix.**
    - Also match the test names that the three gate files declare (`_pin_tests()` and
      `test_client_decl_gate.py`'s), or add the limit to the section comment (`:273-274`): "a PRD row
      that names a gate test without its file is not read".
    - Update `pointer_problems`' docstring.

- **M5** `docs/security-invariants.md:213-215` ("Narrowed by M21-W3"). **A stale sentence.**
  - **The sentences.**
    - "the M21-W3 review's round-1 twins, each refused on the fixture (INV-66's and INV-76's rows list
      them)";
    - "so the rows state only the listed forms".
  - **Why it is stale.** Since `770e00e` the rows name the fixture's rules and list no forms. This
    misdirects the reader; it does not overclaim.
  - **Fix.**
    - Write "(the fixture holds them; INV-66's and INV-76's rows name its rules)".
    - Write "so the rows name the fixture's rules".

### PASS (what holds)

- **Round 5's B1 is closed in W3's text.**
  - **INV-78's first sentence is exact.**
    - `_code` removes comments and reads a directive inside a string as text.
    - `_decide` reads `false`, `!true` and `false && DEBUG` as false, and the `#else` after a true
      branch is dropped.
    - `DEBUG` and `os(watchOS)` keep their code.

    I checked each against `_decide` and `_built_mask` (`tests/unit/test_router_hints.py:133-216`).
  - **The rest matches the file.**
    - G-15's seven are each raw, as stated.
    - Its Rows column (INV-62, INV-64, INV-67, INV-69, INV-78) is the set of rows that carry the
      sentence.
    - The renamed test, the two pin docstrings and INV-62's annotation say what they hold.
    - #247 is open and matches G-15.
- **The PRD branch fails closed as stated.** I ran four plants on the mirror's `docs/prd.md`. Each was
  restored by bytes (sha256 `50ba08e476df446d…`, equal):
  - **P1.** A new row citing `test_ios_client_contract.py::test_the_client_bounds_how_long_it_will_wait`,
    with no pointer and not exempt. Result: "REQ-PRC-901 names a client gate or draws on a gated row,
    and does not point at its row".
  - **P2.** REQ-CMP-002 gains a pin citation. Result: the same message, for REQ-CMP-002.
  - **P3.** The exempt REQ-APP-004 cites INV-71's pin. Result: "listed as off the register but draws on
    INV-[71]".
  - **P4.** The exempt REQ-PRC-002 loses its gate citation. Result: "a stale entry".
- **The exempt list is honest.**
  - None of the five rows' cited tests appears in a register row's test cell.
  - None of their properties is a register row. Those properties are: no canned payload in the build,
    disclosures shown, a stated failure condition, which surface the fallback is, and a search price's
    note.
  - Disclosure is listed under "Retired ids" as a product rule (INV-13, INV-17).
  - REQ-RTR-005's pin appears in INV-78's G-15 sentence only, as a raw reader (K2).
- **The other `b46e976` changes are exact.**
  - `CONTENTS_OF`'s comment matches its regex (first labels `contentsOf:` and `url:`).
  - The module allowlist's comment points a class reached by name at G-12.
  - The phrase "not on the list of Foundation declarations" is carried by one message only
    (`scripts/client_decl_gate.py:1937`).
  - REQ-GAP-001 and REQ-RTR-004 name their rows' gaps, G-15 included.
- **The other in-scope records.** I read every line W3's commits wrote, found by blame:
  - in `docs/architecture.md` (`:272-276`, `:329-342`, `:376-377`);
  - in `docs/decisions.md` (`:4033-4039`, `:4120-4129`);
  - and in the PRD rows W3 changed (REQ-APP-002, APP-005, RTR-002, RTR-004, ASK-001, ASK-004, GAP-001,
    DTL-001 and CMB-004).

  Each one points at its rows or carries the fixed sentence. No other W3 docstring or test name I read
  in the gate or the four test files claims a form beyond its fixture or its spellings.
- **The code.** I met no defect. For example, a toolchain that writes a one-file AST to stdout leaves
  `dump_ast`'s stderr empty, and `main` fails that closed (`expected - set(found)`, `:2066-2070`).
- **Tests on the head (the worktree, `15ebc57`).**
  - pytest on `test_client_decl_gate.py`, `test_ios_client_contract.py`, `test_router_hints.py` and
    `test_security_invariants.py`: **224 passed**. The coverage floor reports a subset run, as
    expected.
  - `make client-decls`: "client-decls PASS: 21 client file(s) in 4 configuration(s) -- simulator,
    release: 2800; simulator, debug: 2805; device, release: 2800; device, debug: 2805". No reinstall
    ran.

## Acceptance criteria evidence

- **REQ-GAP-001** (`docs/prd.md:553`).
  - The status is MET, with the pointer and gaps G-1, G-10 to G-15.
  - Evidence: `ios/EngineTests/FrontDoorTests.swift:674` (`GapRegisterTests`);
    `tests/unit/test_router_hints.py:542` (G-15, M1);
    `tests/unit/test_client_decl_gate.py:157`, `:555`;
    `ios/EngineTests/StandingsStoreTests.swift:216`.
- **REQ-APP-005** (`docs/prd.md:428`).
  - The status is PARTIAL, with the pointer to INV-76.
  - Evidence: `tests/unit/test_client_decl_gate.py:368`, `:386`; `:725` (M3).
- **REQ-RTR-004** (`docs/prd.md:468`).
  - The status is MET, with the pointer and G-10, G-11, G-14 and G-15.
  - Evidence: `ios/EngineTests/EngineClientTests.swift:489`; `tests/unit/test_router_hints.py:468`.
- **REQ-DTL-001** (`docs/prd.md:570`).
  - The status is MET, with the pointer to INV-76. The criterion's own wording is round 5's K2, on #248.
  - Evidence: `ios/EngineTests/DetailTests.swift:26`; `tests/unit/test_ios_client_contract.py:1178`;
    `tests/unit/test_security_invariants.py:533` (the planted check now covers it).

## Producers of the hardened invariants

These are unchanged from round 5, since this round changed records, names and one `FIXTURE_RULES`
phrase.
- **INV-62 and INV-63.**
  - Producers: `EngineClient.fetch`; `GapRegisterStore.load` and `save` (`FrontDoor.swift`);
    `StandingsStore.swift`.
  - Gaps: G-10, G-12, G-13, G-14 and G-15 (INV-62).
- **INV-64.**
  - Producers: `ContentView.load()` → `client.recommendation(task:budget:)`.
  - Gaps: G-10, G-11, G-14, G-15.
- **INV-66.**
  - Producers: `EngineClient.swift`, `StandingsStore.swift`, `FetchedStandings.init(payload:)`.
  - Gaps: G-1, G-10, G-12, G-14.
- **INV-71.**
  - Producer: `EngineClient.read(_:declared:upTo:)`.
  - Gap: G-14, with the `/* */` residue of M2.
- **INV-76.**
  - Producers: `Uncertainty.swift`, `Combine.swift`, `priceInPages`.
  - Gaps: G-2, G-10, G-14. The text half's derivation is M3.
- **INV-78.**
  - Producers: `_code`, `_swift`, and the pins that bypass them.
  - Gaps: G-14 and G-15. M1 and M2 cover what G-15 misses.

## K.8 contract drift check

Plan §5 (`docs/plans/m21-plan.md:94-97`): "No `/v1` field changes … W3 and W4 change gates, not
contracts."

```
$ git diff --stat b22859a..15ebc57
 docs/prd.md                                        |  6 +--
 ...ve-3-review.md => m21-wave-3-review-round-5.md} |  2 +-
 docs/security-invariants.md                        | 16 +++---
 scripts/client_decl_gate.py                        |  9 ++--
 tests/unit/test_router_hints.py                    | 11 ++--
 tests/unit/test_security_invariants.py             | 62 +++++++++++++++++++---
$ git diff --name-only 661426c^2 15ebc57 -- src schemas | wc -l
       0
```

Verdict: OK. W3 as a whole touches no `src/` or schema file, and this round touches no contract
surface.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_ios_client_contract.py:1532`, `:35`. **A name and a docstring older than W3
  say more than `_swift` holds.**
  - **The text.** The test name `test_every_swift_pin_here_reads_the_code_the_compiler_builds`, and
    `_swift`'s docstring "A Swift file as the compiler builds it". INV-78 cites the test.
  - **Why it says more.** `_swift` keeps comments, so a `/* */` copy satisfies a contract pin (M2's
    measurement).
  - **Where it goes.** The name is on #248.
  - **The code change, on #247.** Make `_swift` blank block comments, keeping newlines and the `//`
    markers some pins split on. Then plant M2's G2 again and watch INV-71's pin fail.
- **K2** `docs/prd.md:469` (REQ-RTR-005, older than W3). **A row MET in part on a G-15 pin, without
  saying so.**
  - **What it rests on.** Its MET rests in part on
    `test_the_unmeasured_fallback_is_a_surface_the_engine_actually_serves`. INV-78 names that test as a
    raw reader (G-15).
  - **Why that matters.** A commented copy of `unmeasuredFallback = "…"` satisfies the pin. The row's
    property is off the register, so its exemption stands. But its evidence carries G-15 unsaid.
  - **Fix.** Name G-15 in the row, on #248.

## Risks queued to next M

- **R1** **Which pins read raw text, and which pins read comments, is recorded by hand.**
  - **Today's state.** Nothing ties a row's G-15 sentence to how its pin reads code. The wording test
    checks that the named pins exist, not that they read raw. M1 and M2 are this drift, found by
    reading.
  - **What would show the risk is real:** a new pin that reads raw, or keeps `/* */` text, cited by a
    gated row with no G-15 sentence.
  - **A cheap guard:** #247's guard in `test_router_hints.py`, with a `# raw:` escape, and a
    block-comment plant against `_swift` (K1).
- **R2** **CI's lane (G-10, #243).** This is unchanged. On CI only the text pins and the text tripwire
  run, so M2's `/* */` residue and M3's derivation gap are what CI sees.
