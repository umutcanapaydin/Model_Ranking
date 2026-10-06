---
record_type: review
id: m19-wave-2-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# Wave 2 Tester Review (m19)

**Reviewer:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records,
and it is none of the wave's three Code-Reviewers.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `1843437950dda095bcb4bb6e5ac63c001b9d21bb..fc369d5` (38 commits; 31 files, +7093 / -60).
It includes both BLOCKING reviews, the author's fixes after each, the third review (MINOR) and
`fc369d5`, which answers that review's M1 and M2 in the records.
**Risk tier:** HIGH (`docs/plans/m19-plan.md:62`, `docs/plans/m19-wave-2-plan.md:13-15`). The diff
touches `EngineClient.swift` and `src/app/adapter/main.py`, both security globs (`m19-plan.md:123-132`).
By D-172 no security seat runs on the wave.
**Code-Reviewer verdict:** MINOR, M1 and M2, K1, R1 to R3 (`docs/reviews/m19-wave-2-review.md`). Not
BLOCKING, so this seat runs.
**Model routing (HIGH, advisory):** author family: Claude (all 38 commits carry `GP-Agent:
claude-code/local-lane`) / reviewer family: Claude (Opus 5.5). Fallback reason: no second model family
is available to this seat. Fresh context: I started from the base profile and rules, then read the
plans, the six issues and the five filed after them (#171 to #175), the three reviews, D-180 to D-182
and the diff. I have no memory of any authoring or reviewing session.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75d...`) on `origin/main`
and in the worktree. `git diff --stat 1843437 fc369d5 -- .claude .agents permission-matrix.md .github
epb.html or.md tests/conftest.py` is empty. No commit message in the range carries `Co-Authored-By` or
"Generated with".

## Verdict
MINOR

**Nothing blocks.** Each W2 criterion (REQ-GAP-001, REQ-APP-005, REQ-API-001) has citing tests that
exercise what the records now claim, and they pass. Each of the six issues' tests fails on the
pre-fix code with assertions. Five red commits were run on their own trees. #144, and #138's Swift
half, were shown red by removing each fix line in place. Each gate symptom, planted in the shipping
client, is refused at `fc369d5`. Both `make check-fast` runs were green. No test was weakened, skipped
or deleted to get there.

**Fault injection: 71 of 78 faults killed before this review (91%), 77 of 78 after.** Six faults in
the wave's code stayed green (M1, M2, M3, M5). I wrote a test for each, and each test fails on its
fault. One more (M4) was caught by another test but not by the test that cites the symptom; I extended
that test. The one shape still unrefused, a URL made from text and returned through a computed
property (M6), is a gap between the gate and INV-63's wording, not a missing test. It needs an edit
in one of the three security-glob files allowed to make a URL.

**The criterion as frozen is not met as worded, and the records say so.** "By any route the compiler
accepts" and "however the value is named" are not provable by a check over declarations. The plan
amendment (`m19-plan.md:214-224`) narrows the claim to the routes and shapes D-180 and D-181 name, and
files the rest (#171, #172, #173). I tested the narrowed claim. Eight fresh mutants of my own,
planted in the shipping client inside the named routes (S7 to S14), were each refused. The owner
accepts the narrowing when he merges the amendment.

## Acceptance-criterion coverage (REQUIRED)

- **REQ-GAP-001** (the W2 privacy half: nothing derived from the question reaches a request or the
  standings file, by the routes D-180 names; G-3 closed). GREEN for the claimed routes.
  - `tests/unit/test_client_decl_gate.py:155` (a sink's own `var`, a read of another file's), `:166`
    (standings built outside the sinks), `:173` (what must pass), `:298` (only the door builds a
    client on an address), `:390` (a sink holds only values), `:400` (a sink calls only what is
    listed), `:413` (a kept type extended or conformed elsewhere), `:421` (only the store builds or
    saves to a store), `:429` (unsafe memory), `:447` (the code a sink runs reads no shared state:
    a function, a coding witness). Each cites `REQ-GAP-001`.
  - Added here: `:529` (the same, through a computed property and a protocol requirement's other
    members, compiled: M2), and `:475` (a listed sink call the client no longer makes fails the
    gate: M1).
  - G-3 (#107, #110): `:249`, `:259`, `:311`, `:324`, `:435`;
    `tests/unit/test_router_hints.py:967`, `:980`, `:1023`, `:1031`, `:1037`, `:1042`;
    `tests/unit/test_ios_client_contract.py:1450`, `:1461`, and `:1470` (added here: M3).
  - The text half (D-180 clause 4, lanes with no Xcode): `test_router_hints.py:939`, `:946`, `:1001`.
  - #144 (INV-85): `ios/EngineTests/EngineClientTests.swift:841`; `test_client_decl_gate.py:266`.
  - Not met as worded: routes no rule names (G-1, #172); the date the store writes (#170); a URL
    returned through a door file's computed property (M6).
- **REQ-APP-005** (the W2 arithmetic half: no arithmetic on a served number outside the named places,
  by the operators, methods and names D-181 lists). GREEN for the listed shapes.
  - `test_client_decl_gate.py:366` (20 shapes, each asserted on its own declaration's lines), `:202`
    (#60's R4, now on its own lines: M4), `:225`, `:383` (the price in pages, `priceInPages` only),
    `:475` (a permission the client no longer uses fails the gate: M1). Sorts (REQ-APP-002, Ruling A):
    `:216`, `:376`, `:457`.
  - Not met as worded: `Any` and text (#171); prefix `-`, shifts, an operator as a value and the rest
    D-181 clause 3 names (#173).
- **REQ-API-001** ("the engine's own sameness rule reaches the phone", D-182). GREEN.
  - `tests/unit/test_api_v1.py:779` (each pick carries the id of its model, through `/v1`);
    `tests/unit/test_recommend.py:661` (two models that share a name keep their own ids), `:678`
    (each of the three picks, the budget pick included: added here, M5);
    `ios/EngineTests/AnswerPlanTests.swift:355` (two models that share every shown value are two
    cards), `:366` (an engine with no id keeps the four-value rule);
    `tests/unit/test_ios_payload_contract.py:151` (the app's key is a key the engine serves).
- **#132** left the wave by the valve (`m19-plan.md:198-202`). Nothing of it is in the range.

## Red→green on reported symptoms

Each Python red commit was extracted with `git archive` into a scratch folder, and its tests were run
there with this worktree's `.venv`. Each fails with assertions, not only import errors. The Swift
halves were shown red in place: each fix line was removed, the test was run, and the bytes were
restored.

| Symptom | Red commit: what failed | Fix | On the shipping client at `fc369d5` |
|---|---|---|---|
| #85: M17's P2 relay and P3 pass the gate | `7f0dd29`: 3 failed (self-test, `test_a_sink_holding...`, `test_standings_built_outside...`) | `a37f6a3` | S1 (P2) and S2 (P3) refused in all four configurations, and by the text pins |
| #60: an aliased position, a second same-named sort | `74f0a60`: 3 failed (self-test, the R4 test, the sort test) | `dc68029` | S3 and S4 refused in all four configurations |
| #107: `URL(_:strategy:)`, a decode wrapper, `NSDataDetector`, an unapplied `.init` | `250a03c`: 4 failed (self-test, `:249`, `:259`, `test_router_hints.py:967`) | `1ba65c0` | S5 refused by the gate and the pins; S12 (`GapRegisterStore.init` unapplied) by three pins |
| #110: pins read code under `#if false` | `d2dd6b9`: 1 failed (`test_the_pins_read_no_code...`) | `40ec649` | S6 (both timeouts under `#if false`, the first review's F2) fails `test_the_client_bounds_how_long_it_will_wait` |
| #144: the session keeps and sends cookies | `c79444c` (Swift). Shown red in place instead: each of the fix's three lines removed alone fails the test, at `EngineClientTests.swift:843`, `:844`, `:845` (W1 to W3) | `89f724d` | the test reads the shipped session's configuration, not a `Set-Cookie` exchange; the amendment records why (a `URLProtocol` stub bypasses cookie handling, measured) |
| #138: picks carry no model id | `41c300a`: 2 failed in `test_api_v1.py` | `68609b3` | W4 (the id rule removed) and W5 (the id decoded from no key) fail `AnswerPlanTests.swift:358` |

The review rounds' red commits fail the same way: `9a5785f` 3 failed, `22c3d1c` 13, `90bfbd7` 8,
`72ead87` 11, `ce03842` 1, `4fa43cc` 13.

## Suite result

- `make check-fast` on the clean tree at `fc369d5`: **PASS** in 219.8 s. Lint, types, records; `test`
  2028 passed, 25 skipped, coverage floor PASS; `swift-test` 468 tests, exactly the manifest's;
  `client-decls` PASS, 19 files in four configurations (2474 / 2479 / 2474 / 2479).
- `make check-fast` with this review's tests in place: **PASS** in 97.2 s. `test` 2032 passed, 25
  skipped; swift and client-decls unchanged.
- Coverage on touched code, statements and branches, measured on the same three test files before
  (`1843437`) and after (`fc369d5`): `scripts/client_decl_gate.py` 79% to 93%;
  `src/app/adapter/main.py` 70% to 70%; `src/app/workflows/recommend.py` 82% to 82%. No drop. The
  gate's uncovered new lines were `unseen_permissions` (1152-1170) and `_SinkReach.reached`'s two
  branches (681-682, 686-687). This review's tests cover both (M1, M2).
- Not run: `make ui-test` (the guard stubs refuse `simctl` and `xcodebuild`; the author runs it), and
  `make check` (it runs the same legs one after another).
- Mutation runner (advisory): none is wired for the stack. The manual kill rate is above.

## Mocks / contract tests

- **The app and `/v1`:** Swift tests use the canonical `URLProtocol` stub behind `OfflineTestCase`.
  `test_ios_payload_contract.py:151` checks every key the app decodes against the payload the engine
  serves. With the app's key changed to `modelID` it failed (E5). OK.
- **Cookies (#144):** the stub cannot observe them, and the suite may not open a socket, so the test
  reads the shipped `URLSessionConfiguration` through `Mirror`. It restates the three settings the
  fix writes. That is the contract `URLSession` documents, so I accept it, but it shows no cookie
  refused on the wire. OK, as recorded.
- **The compiler:** the flow tests read the committed dump (`tests/unit/data/g2_fixture_ast.txt`), a
  stand-in for `swiftc -dump-ast`. Its contract test, `test_client_decl_gate.py:463`, fails when the
  dump's declarations differ from a fresh compile (G26 red). It compares declarations, not
  expressions, so a layout change inside a body is unseen (#175, R3, filed). The fixture's compiled
  self-test checks (file, phrase) pairs. A shape lost among several that share a phrase is invisible
  to it, but the per-declaration tests on the dump catch each one (G10b to G15 below).

## Test integrity

- **Weakened or deleted to green:** none. `git diff 1843437..fc369d5 -- tests ios/EngineTests` removes
  no assertion and no test. The one skip added (`test_client_decl_gate.py:463`, no Xcode) matches the
  existing self-test's skip. The pins moved from raw reads to `_swift`/`_code`, which drop only what no
  build compiles. A pin that requires code now requires live code, and one that refuses code now
  ignores dead code. Neither is weaker on what ships.
- **Mirror-implementation:** the wave's gate tests plant shapes in a compiled fixture and assert on
  the refusals, which is behaviour. The one restating test is the cookie test, explained above.
- **A test passing for the wrong reason:** the R4 test (`:202`) passed on any `ContentView.swift`
  "served position" refusal (M4). Extended here.

## Fault-injection protocol

Method: a Python harness (`m19w2_fault.py`, in the seat's scratchpad) read each touched file's bytes
and sha256. Then, as one atomic sequence per fault: it wrote the fault (each edit matching exactly
once), ran the command, restored the bytes in a `finally`, and compared sha256. Every fault was
restored byte-identical: all 78, the re-runs with this review's tests, and two discarded plants.
Afterwards `git diff --quiet HEAD -- scripts ios src` held, and the gate's sha256 is `bccda698...`
before and after. The commands: the three gate and pin
test files for G, T and C; `client_decl_gate.py` (self-test plus four configurations) and the two pin
files for S; four engine test files for E; `swift test --filter 'EngineCookieTests|PickCardTests'`
for W.

| Id | Fault | Result |
|---|---|---|
| G1 | `_SinkReach` facts dropped | RED: self-test, `:447` |
| G2a, G2b | the `<conforms>`, `<extends>` problems off | RED: `:413` each |
| G3a/b/c | `StandingsStore.save`, `FetchedStandings.init`, `EngineClient.init(baseURL:)` provenance widened | RED: `:421`, `:166`, `:298` |
| G4 | the `UNSAFE` rule off | RED: `:429` |
| G5 | `NSMutableString` a held type | RED: `:390` |
| G6 | `_sink_calls` off | RED: `:400` |
| G7, G8 | a sink's own `var`; its read of another file's `var` | RED: `:155` each |
| **G9** | `unseen_permissions` returns `[]` | **GREEN as delivered** (136 passed). RED with `:475` (M1) |
| **G9b** | `main()` stops calling it | **GREEN as delivered**. RED with `:475` (M1) |
| G10a | `_Flow.binding` off | RED: 3 shapes and the self-test, but **not the R4 test** (M4). RED on `:202` once extended |
| G10b to G10j | assignment, loop, condition, cases, call, inout, result, closure, dispatch off | RED: each on its own fixture shape (`:366`) |
| G11, G12 | memberwise property; a function as a value | RED: `fixtureThroughABox`, `fixtureAsAValue` |
| G13 to G16 | `&` operators; `advanced`; `Int32` not a number; served fields listed by hand | RED: A5, A6, A7, A8 and the three condition shapes |
| G17, G18 | price permitted file-wide; a second `common` sort permitted | RED: `fixtureRouterDiscounts`; `:216` |
| G19, G20 | `sortedArray` off; Foundation's sorts off | RED: `:457`; `:376` and `:457` |
| G28 | `Standing` named not served | RED: 21 tests |
| G21 to G24 | a call-made URL; a cast-made URL; the last-arrow rule; `NSDataDetector` off | RED: `:249`/`:311`/`:324`; `:435`; `:324`; `:259` |
| G25 | the cookie exception keyed by symbol only | RED: `:266` |
| G26 | snapshot drift check off | RED: `:463` |
| **G29** | `_SinkReach.reached`: the computed-property branch off (`:681-682`) | **GREEN as delivered**. RED with `:529` (M2) |
| **G30** | `_SinkReach.reached`: the protocol branch off (`:686-687`) | **GREEN as delivered**. RED with `:529` (M2) |
| T1 to T8 | `_code` keeps dead branches; a directive in a string read; the sink pins' builds, boards, stored-static and file-`var` checks off; the text gate's `NSDataDetector` off; `_decide` decides nothing | RED, each (T4's first plant was a no-op through operator precedence; re-planted, RED on `P2b`) |
| **C1** | `_swift` returns the raw text | **GREEN as delivered**. RED with `test_ios_client_contract.py:1470` (M3) |
| C2 | `_swift` reads directives in comments | RED: `:1461` |
| S1 to S6 | shipping client: P2, P3, R4, M7's second sort, `URL(_:strategy:)`, timeouts under `#if false` | refused, each (S6 by the pins only, as designed) |
| S7 to S14 | fresh, shipping client: a sink reads a class instance's `var` through a `let`; a listed call's body (`UIText.engineAddress`) reads the screen's global; arithmetic through a written initialiser's parameter, `while let` and `if case let`; a sink calls another file's computed global; an unapplied `.init`; a kept type conforming in its own file | refused, each, in all four configurations (S12 by the pins) |
| **S15b** | fresh: `extension String { var probeAsAddress: URL? { URL(string: self) } }` in `EngineClient.swift`, read as `typed.probeAsAddress` in `ContentView.swift` | **passes the gate and the pins** (M6). The same getter in `Detail.swift` is refused (S16) |
| E1 to E3 | `model_id` withheld; the value pick given the leader's id; ids keyed by display name | RED, each |
| **E4** | the budget pick given the leader's id | **GREEN as delivered**, in all 13 test files that read picks or ids. RED with `test_recommend.py:678` (M5) |
| E5 | the app decodes the id under `modelID` | RED: `test_ios_payload_contract.py:151` |
| W1 to W5 | each cookie line removed; the id rule removed; the id's coding key changed | RED, each |

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `scripts/client_decl_gate.py:1152` (`unseen_permissions`) and `:1393` (its call in `main()`).
  D-181 clause 5 says a permission the shipping client no longer uses fails the gate, and D-180 clause
  2 says a listed sink call it no longer makes does too. No test held either. With the function
  returning `[]`, or `main()` not calling it, every test passed (G9, G9b). Fixed by the test added at
  `tests/unit/test_client_decl_gate.py:475`. It reads the compiled fixture's facts (seen where the
  fixture uses a permission, reported where it does not, for all four kinds), and `main()` fails a
  client that shows none of them. Commit it.
- **M2** `scripts/client_decl_gate.py:681-682`, `:686-687` (`_SinkReach.reached`). D-180 clause 2 and
  INV-66 say the code a sink runs elsewhere is followed through computed properties and through every
  member a protocol requirement may dispatch to. Only the function and coding-witness routes were
  planted. With either branch removed every test passed (G29, G30). Fixed by the test added at
  `tests/unit/test_client_decl_gate.py:529`. It compiles a three-file probe (a computed property
  read inside `FetchedStandings.init`, and a protocol declared in the sink and answered in another
  file, each reading the screen's global) and asserts both refusals. Like the self-test, it needs
  Xcode. Commit it.
- **M3** `tests/unit/test_ios_client_contract.py:34-39` (`_swift`). INV-78 says the contract pins read
  every Swift file without a branch no build compiles. The wave's two tests held that no pin reads
  around `_swift` and that a directive in a comment hides nothing. Neither held that `_swift` drops a
  `#if false` branch: with `_swift` returning the raw text every test passed (C1). Fixed by the test
  added at `tests/unit/test_ios_client_contract.py:1470`. Commit it.
- **M4** `tests/unit/test_client_decl_gate.py:202` (#60's R4 symptom test). It asserted only that some
  `ContentView.swift` line refuses a served position, and the fixture refuses one on 15 other lines of
  that file. With the binding rule off, R4's own `let place = standing.position; place + 1` passed the
  gate and this test stayed green (G10a; other shapes caught the loss). Extended here (`:207-213`) to
  require the refusal on `fixtureViewRanksByHand`'s own lines. Commit it.
- **M5** `src/app/workflows/recommend.py:595` (`ids[id(cheap)]`). D-182 clause 1 says each pick carries
  its model's id. The budget pick's was never read: given the leader's id, it passed every test file
  that mentions `model_id` and five more that read picks (E4). Fixed by the test added at
  `tests/unit/test_recommend.py:678`. The fixture's three picks are three models, and each carries the
  id the surface's own ranking gives its row. Commit it.
- **M6** `scripts/client_decl_gate.py:514`, `:521-532` (`url_facts` reads `call_expr`,
  `constructor_ref_call_expr` and casts) against `docs/security-invariants.md:124` (INV-63: a URL
  "returned by any call whatever it is named") and G-3, recorded as closed. A computed property is a
  call by another syntax, and the rule does not read it. A getter declared in `EngineClient.swift`
  that makes a URL from its `String` receiver, read as `typed.probeAsAddress` in `ContentView.swift`,
  passed `client-decls` in all four configurations and the text pins (S15b, restored byte-identical).
  Low risk: it needs an edit to a security-glob file, and the URL is inert where it lands, since only
  `EngineClient.swift` sends and only it builds a client on an address (PROVENANCE). But the record
  claims more than the rule holds. Fix: count a reference to a computed property whose type names
  `URL`, outside the three files, as `URL.made`, with a fixture shape. Or narrow INV-63 to calls and
  write the three files' own getters in as trusted, as D-180 trusts a sink's own code. Or file it with
  #175's gate work.

## Tests added/extended this review

All uncommitted in the seat's worktree, for the author to commit with this verdict:
- `tests/unit/test_client_decl_gate.py:207-213`: the R4 test now requires the refusal on R4's own
  lines. REQ-APP-005, D-181 clause 2 (M4).
- `tests/unit/test_client_decl_gate.py:475`: `test_a_permission_the_client_no_longer_uses_fails_the_gate`.
  REQ-APP-005, REQ-GAP-001, D-180, D-181 clause 5 (M1).
- `tests/unit/test_client_decl_gate.py:504-544`: `SINK_REACH_PROBE` and
  `test_the_code_a_sink_runs_is_followed_into_computed_properties_and_protocol_witnesses`. REQ-GAP-001,
  D-180 clause 2, INV-66 (M2).
- `tests/unit/test_ios_client_contract.py:1470`: `test_a_pin_here_never_reads_a_branch_no_build_compiles`.
  REQ-GAP-001, INV-78, #110 (M3).
- `tests/unit/test_recommend.py:678`: `test_each_pick_carries_its_own_models_id_the_budget_pick_included`.
  REQ-API-001, D-182 (M5).

Each was red on the fault it names and green on the clean tree. `ruff check` passes on all three files.
