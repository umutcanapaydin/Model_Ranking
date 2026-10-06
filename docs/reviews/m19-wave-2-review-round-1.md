---
record_type: review
id: m19-wave-2-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# M19-W2 Code Review: the phone's promises, held by what the code does

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `1843437..40bb4d1` (17 commits; 25 files, +1,246 / -27).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:62-64`, `docs/plans/m19-wave-2-plan.md:13-15`). The diff
touches `EngineClient.swift` and `src/app/adapter/main.py`, both security globs (`m19-plan.md:123-132`).
By D-172 no security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane` on all
17 commits) / reviewer-family: claude-opus (fallback: no second family is available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile and
`.agents/rules/practices.md` from `origin/main`, then the milestone plan (§1 W2, §2 W2, §3, the W2
amendment), the wave plan, and D-180 to D-182. Then I read the diff. I read the commit messages
last. I read issues #60, #85, #107 and #110 with `gh issue view` (read only), to learn each issue's
own scope.

**Summary.** The wave does what its planted mutants ask. Both M17 mutants (P2, P3) are now refused on
the shipping client, in all four builds, by the compiled gate and by the text half. The fixture
mutants for #60, #107 and #110 are refused. The session keeps no cookie. Each pick carries its
model's id. Every gate is green on the clean tree.

But the milestone criterion and the records claim more than that. They say "by any route the
compiler accepts", "however the value is named", "every local, parameter and loop element" and "a
URL decoded from text counts as the network". I planted ordinary Swift that gets past those claims
with `make check-fast` green. Two findings block:

1. **B1.** Arithmetic on a served number passes every gate when it goes through a reassigned `var`,
   a function's return value, a method's parameter, a loop over a literal or a tuple, `&+`, `Int32`
   or `.advanced(by:)`, or a served field the table does not list.
2. **B2.** The typed question reaches the boards request with every gate green, by two routes that
   edit no privacy sink. In the first, a generic decode returns a dictionary of URLs. In the second,
   `FrontDoor.swift` makes the URL, because both store files may make URLs. Both routes then hand
   the URL to `EngineClient(baseURL:)`, which any file can call.

There are also nine MINOR findings, two K.9 candidates and three risks. Each blocking finding can be
cleared in either of two ways: close the route (each fix with a red test made from my mutant), or
narrow the record, keep the gap open, and amend the plan. The author chooses.

## Verdict

BLOCKING

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `scripts/client_decl_gate.py:507-528` (`_flow_once`), `:299-301` (`NUMERIC_OPERATOR`),
  `:225-229` (`SERVED_NUMBERS`), `:298` (`SERVED_REF`), `:307` (`CALLEE`). **Arithmetic on a served
  number still passes every gate, through ordinary names.** Why it blocks: the W2 criterion
  (`m19-plan.md:39`) is "no arithmetic happens outside the named files, however the value is named",
  and G-2 is recorded as closed. D-181 clause 1 (`docs/decisions.md:3986-3988`) promises to follow a
  served number into "every local it is bound to, every parameter a call passes it to and every loop
  element it yields". INV-76 (`docs/security-invariants.md:143`) says "through every local,
  parameter and loop element", and REQ-APP-005 (`docs/prd.md:427`) says arithmetic "through any
  local, parameter or loop element" fails the gate. The mutants below contradict those words
  (permission-matrix §11: REQ-ID unmet).
  Evidence, planted in `ContentView.swift` on the shipping client:
  ```swift
  func probeRanksByAssignment(_ standing: Standing) -> Int {   // A1: a reassigned local
      var place = 0
      place = standing.position
      return place + 1
  }
  func probeServedPlace(_ standing: Standing) -> Int { standing.position }      // A2: a return value
  func probeRanksByReturn(_ standing: Standing) -> Int { probeServedPlace(standing) + 1 }
  struct ProbeRanker { func rank(_ place: Int) -> Int { place + 1 } }            // A12: a method's parameter
  func probeRanksByMethod(_ standing: Standing) -> Int { ProbeRanker().rank(standing.position) }
  ```
  `make check-fast` PASSED with A1 planted, and again with A2 (all six legs; `client-decls` in all
  four configurations). The other survivors passed `client-decls` and the text pins: A3 (a computed
  property on `Standing`), A5 (`standing.position &+ 1`), A6 (`.advanced(by: 1)`), A7
  (`Int32(standing.position) + 1`), A8 (`(category.scoreAnchor ?? 0) - 100`), A10
  (`for place in [standing.position]`), A11 (`for (index, place) in places.enumerated()`) and A12.
  The table under "Mutants planted" has every case. The controls were refused: a `let` alias (A0),
  a struct built inline (A4) and a free function's parameter (A13).
  The causes, in code:
  1. `_flow_once` has three steps only. It follows a binding's initialiser (`:511`). It follows a
     loop, but only when the sequence is a `declref_expr`, `member_ref_expr` or `call_expr`, and
     only into the loop's first named pattern (`:516-520`). It follows a call only when the callee's
     own line carries `function_ref=single apply` (`:521`), so it reaches free functions only: a
     method call's first child is a `dot_syntax_call_expr`. It has no step for `assign_expr`, and
     none for a function's result.
  2. `NUMERIC_OPERATOR` lists ten Swift types and the operators `[-+*/%]=?` only.
  3. `SERVED_NUMBERS` names nine fields. `Models.swift` also decodes `scoreAnchor` (`:58`),
     `closeCallMargin` (`:51`), `minQuality` (`:60`), `secondaryAgeDays` (`:55`) and
     `SourceRow.rows`/`ageDays` (`:188`, `:190`). `CloseCallFact.behindBy` is decoded in
     `Notices.swift:21`, which `SERVED_REF` cannot see.
  To clear it, either:
  - (a) follow assignments, return values and accessor bodies, method and initialiser parameters,
    every pattern of a loop over any sequence, every arithmetic operator and numeric method, and
    every numeric field the engine sends (derived from the decoded fields, not typed by hand). Each
    fix gets a red test made from these mutants. Do at least A1, A2 and A10 to A12, the shapes D-181
    clause 1 itself names.
  - (b) or write the shapes the gate does follow into D-181, INV-76 and REQ-APP-005, keep G-2 open
    for the rest, and amend the plan's W2 criterion.

- **B2** `ios/ModelRanking/Engine/EngineClient.swift:200` (`init(baseURL:session:)`),
  `scripts/client_decl_gate.py:395-396` (`MAKES_URL`), `:268` (`DECODES_URL`), `:654` (`URL.made`
  allowed in both stores). **The typed question reaches the boards request with every gate green,
  and no privacy sink is edited.** Why it blocks: the W2 criterion (`m19-plan.md:39`) is "Nothing
  derived from the question reaches a request or the standings file, by any route the compiler
  accepts", and G-3 is recorded as closed. The wave plan's P2 check (`m19-wave-2-plan.md:35`) is
  that "a URL made by ... a generic decode wrapper fails" a gate. INV-63
  (`security-invariants.md:124`) says a URL "decoded" from text "counts as the network everywhere
  but `EngineClient.swift` and the two stores". INV-66 (`:127`) says nothing derived from the
  question reaches the boards request.
  Evidence, mutant U5. It changes `Detail.swift` and adds one line to `ContentView.swift`; neither
  file is a security glob:
  ```swift
  // Detail.swift
  func probeReadLike<T: Decodable>(_ example: T, from data: Data) -> [String: T]? {
      try? JSONDecoder().decode([String: T].self, from: data)
  }
  func probeRelaysTheQuestion(_ typed: String) async -> FetchedStandings? {
      let base = EngineClient.localDefault
      let json = "{\"a\": \"" + base.absoluteString + "/" + typed + "/\"}"
      guard let address = probeReadLike(base, from: Data(json.utf8))?["a"] else { return nil }
      return try? await EngineClient(baseURL: address).boards()
  }
  // ContentView.swift
  func probeUse(_ typed: String) async -> FetchedStandings? { await probeRelaysTheQuestion(typed) }
  ```
  `make check-fast` PASSED, `client-decls` included, in all four configurations. `fetch` appends
  the route to `baseURL` (`EngineClient.swift:272`), so the boards request goes to
  `<engine>/<typed>/v1/boards`. With another string in place of `base.absoluteString`, it goes to
  any host. Mutant U3b also PASSED `make check-fast`. It puts these lines in `FrontDoor.swift`, above
  `// MARK: - The gap register` (`:203`):
  ```swift
  func probeFrontDoorRelays(_ typed: String) async -> FetchedStandings? {
      let address = EngineClient.engineURL(from: EngineClient.localDefault.absoluteString + "/" + typed)
      return try? await EngineClient(baseURL: address).boards()
  }
  ```
  The causes, in code:
  1. `EngineClient(baseURL:)` accepts any URL from any file. D-180 clause 3 (`decisions.md:3946`)
     treats a sink's "immutable configuration" as safe. But the caller sets that configuration, and
     no rule asks who the caller is. This is the "relay in `main`" that the gate's own docstring
     names (B19, `client_decl_gate.py:28-31`).
  2. So INV-63 is the only barrier, and it has two holes:
     - `MAKES_URL` matches only a call whose type is `URL`, `URL?`, `[URL]`, `[URL]?` or
       `Optional<URL>`. A `[String : URL]?`, a `Set<URL>`, a tuple or a generic struct passes.
       `DECODES_URL` looks only at a declaration named `decode(`/`decodeIfPresent(`. In U5 that
       call's substitution is `T -> [String : T]`, which names no `URL`.
     - `URL.made` is allowed in both store files. `FrontDoor.swift` is also the file that routes the
       typed question, and `EngineClient.engineURL(from:)` (`EngineClient.swift:169`) makes a URL
       from any string.
  3. The text gate refuses these lines only where it spells them out: a second `EngineClient(` in
     the view (`tests/unit/test_router_hints.py:414-416`), and `EngineClient` in the register's
     section (`:446-448`). With the same lines in `ContentView.swift` (U2), or after the MARK (U3),
     the text gate refused them. U5 and U3b sit one file away, or a few lines up.

  To clear it, either:
  - (a) stop any file but `EngineClient.swift` from building a client with a URL of its own. For
    example, a `PROVENANCE` entry for `EngineClient.init(baseURL:session:)` and `engineURL(from:)`,
    and a no-argument init for the app's one `EngineClient()` at `ContentView.swift:85`. Then widen
    `MAKES_URL` to any call whose type names `URL`, and to any generic substitution to `URL` on a
    call into the app's module. Each fix gets a red test made from U5 and U3b.
  - (b) or narrow INV-63, INV-66 and D-180 clause 3 to what the gate holds, keep G-3 open, and amend
    the plan.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `scripts/client_decl_gate.py:364-427` (`_shared_state`, `sink_facts`). **The sink rule
  refuses a `var`, not mutable state, and a read of a `var`, not a read through a function.** Two
  planted relays each passed `make check-fast`. Each needs an edit inside `EngineClient.swift`, as
  P2 did. S2b: `nonisolated(unsafe) var probeRelayTag` and `func probeRelayed() -> String` in
  `Detail.swift`, set by the screen; `fetch` (`EngineClient.swift:273`) adds
  `URLQueryItem(name: "t", value: probeRelayed())`. S3: `static let probeRelay = NSMutableString()`
  on `EngineClient`, set by the screen with `setString(typed)` and read in `fetch`. (S2, the same
  getter in `ContentView.swift`, failed `swift-test` only because the Engine package cannot see
  that file.) D-180 "What it does not do" (`decisions.md:3963`) trusts a sink's own edit, which is
  why this is MINOR. But INV-66 (`security-invariants.md:127`) and D-180 clause 2 say "neither sink
  holds or reads mutable state another file can set". S3 holds such state and S2b reads it. Narrow
  the words to the shapes the gate refuses, or refuse two more things: a sink's calls into functions
  declared outside the sinks, and a `let` that holds a mutable Foundation reference type
  (`NSMutable*`, `NSCache`) or a `@TaskLocal`.
- **M2** `tests/unit/test_router_hints.py:816` (`STORED_STATIC`). **The text half of D-180 (clause 4,
  `decisions.md:3948`: "no `static var`") misses two shapes.** Measured with `_sink_pin_problems`
  (`:820`) on edited copies of the shipping sources: `static var probeTag: String?`, which has no
  `=`, PASSED; a file-scope `var probeRelay = ""` in `EngineClient.swift` PASSED; the control
  `static var probeTag = ""` was refused. The compiled gate refuses all three, so only the lanes
  without Xcode are open.
- **M3** `tests/unit/test_ios_client_contract.py:32` (`_swift_sources`) and `test_router_hints.py:122`
  (`_built`). **The `#if false` fix reaches one pin file of two.** The contract file's pins read raw
  text. F2 wrapped `EngineClient.swift`'s two timeout lines (`:206-207`) in `#if false … #endif` and
  passed `make check-fast`, because the pin at `test_ios_client_contract.py:593` read the dead
  lines. `_built` also keeps `#if !(true)` and `#if false && DEBUG` (measured), and both are
  decidably dead. #110 itself scoped the fix to `_code`'s readers, so this is not BLOCKING. But
  INV-78 (`security-invariants.md:151`) now says "The text pins read code the compiler builds". That
  is true of `test_router_hints.py` only. Narrow INV-78, or route `_swift_sources` through `_code`.
- **M4** `scripts/client_decl_gate.py:302` (`ORDERING_CALL`). **The compiled sort rule reads Swift's
  sorts only.** `answers.sorted(using: KeyPathComparator(\Answer.eligibleCount))` (O1) passed
  `client-decls`. Only the text tripwire refused it (`test_ios_client_contract.py:436-437`). D-181
  clause 3 (`decisions.md:3994`) says any sort is keyed on the receiver the compiler resolved. Add
  Foundation's `sorted(using:)` and `sort(using:)`.
- **M5** `scripts/client_decl_gate.py:231-236` (`ARITHMETIC_PERMITTED`). **The price permission
  covers whole files.** The records say it is narrower: "permitted by name" (`decisions.md:4000`,
  `prd.md:427`). A14 put `let price = pick.blendedPerM; return price * 0.8` in `Router.swift`
  (1,030 lines). It passed `client-decls` and the text pins. The arithmetic the permission is for
  lives in one function per file, `priceInPages` (`Router.swift:928`, `Language.swift:215`). Key
  the permission to that function, or say "by file".
- **M6** `tests/unit/test_api_v1.py:793`. **The engine-side #138 test cannot see the case D-182 is
  for.** It maps ids by display name. I planted a name-keyed lookup in `recommend.py:506`
  (`by_name = {row.model: model_id ...}`) and the whole Python suite passed: 1974 passed, 25
  skipped. That is the #102/#129 defect (one display name, two ids), and the engine half of D-182
  has no test against it. Add a fixture where two ranked rows share a display name.
- **M7** **No new test cites a REQ-ID** (seed E.2, practices "Tests cite REQ-IDs and D-IDs"). The new
  tests cite D-180, D-181, D-182 and issue numbers. None cites REQ-GAP-001, REQ-APP-005 or
  REQ-API-001: `tests/unit/test_client_decl_gate.py:154-262` (0 `REQ-` in the file),
  `test_api_v1.py:779`, `ios/EngineTests/AnswerPlanTests.swift:355`, `:365`,
  `EngineClientTests.swift:840`.
- **M8** **Doc drift.** The gate's docstring (`client_decl_gate.py:42-44`) says
  `Bundle.main.url(forResource:withExtension:)` "builds no path and passes". U4 shows `URL.made` now
  refuses it outside the three files. The docstring of `pickCards` (`AnswerPlan.swift:169-172`)
  still states only the four-value rule. The INV-85 row sits between INV-72 and INV-73
  (`security-invariants.md:139`).
- **M9** `ios/EngineTests/EngineClientTests.swift:827-846`. **#144's test is not the one the plan
  names.** The plan asks for "a Swift test that a `Set-Cookie` answer is not sent back"
  (`m19-wave-2-plan.md:36`). The test reads the shipped configuration instead. The test's comment
  gives a measured reason: a `URLProtocol` stub bypasses the session's cookie handling. That is
  sound, but the W2 amendment (`m19-plan.md:198-202`) does not record the change.

### PASS (what looks good)

- **P2 and P3 are held on the shipping client.** I planted both M17 mutants myself. The compiled
  gate refused each in all four configurations ("`probeTag` is mutable stored state in a privacy
  sink"; "builds FetchedStandings"). `test_the_privacy_sinks_hold_by_text_too` refused each too.
- **Red before green, every issue.** Six reproduce/fix pairs (#85, #60, #107, #110, #144, #138). D-180 (`7395e40`) comes before P1's
  code (`a37f6a3`), and D-182 (`ad4942b`) before the field is served (`68609b3`), as the plan and
  §5 of the milestone plan require.
- **The provenance rule is a good design.** It is small, exact and file-scoped, and it refuses P3
  where the standings are built, not where they are saved.
- **The gate fails closed on its own fixture.** `FIXTURE_REFUSALS` grew one entry per new rule, and
  `self_test` refuses an unexpected refusal as well as a missed one.
- **The cookie exception is exact.** `FORBIDDEN_EXCEPT` (`:251-253`) allows one symbol in one file,
  and `test_turning_cookies_off_is_the_one_cookie_symbol_allowed_and_only_in_the_door` pins both
  directions. The Swift test reads the session as it ships, through `Mirror`, and it fails if the
  session moves.
- **D-182 is additive and keeps old engines working.** `PUBLIC_PICK_FIELDS` and `PICK_KEYS` move
  together. A pick with no id keeps the four-value rule (`AnswerPlanTests.swift:365`). The id
  follows the row by identity, the same way #102's `is` tests do. `PickCard.id` stays the label,
  so two cards that share a name do not collide in `ForEach`.
- **The valve was used as written, and recorded.** #132 left by plan amendment.
- **The gate found a real thing.** The price in pages was arithmetic on a served price that no
  table named, and D-181 names it rather than hiding it.
- Gates green on the clean tree: `make check-fast` PASS (lint, typecheck, records, test,
  client-decls, swift-test) in 61.5 s.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code; the citing test per producer; gaps.

- **INV-66 (nothing derived from the question reaches the boards request or the standings file).**
  - `EngineClient.boards()` → `fetch("v1/boards", query: [])` (`EngineClient.swift:248-249`):
    `EngineClientTests.swift:489` (`testTheBoardsRequestCarriesNothing`), `:510`;
    `test_router_hints.py:846` (the text pin on `boards()`).
  - `EngineClient.fetch`, which builds the URL from `baseURL` (`:270-282`): the sink rule
    (`test_client_decl_gate.py:154`, `:172`); the fixture (`client_decl_gate.py:275-278`).
  - `EngineClient.init(baseURL:session:)`, the boards request's destination (`:200`): **no test
    covers who may set `baseURL`**. B2.
  - The sink's stored state (`baseURL`, `session`, the `static let`s at `:165`, `:182`, `:187`): the
    sink rule. Gap: a `let` holding a mutable reference type, and reads through functions (M1).
  - `FetchedStandings.init(payload:)` (`Models.swift:412`), called at `EngineClient.swift:251` and
    `StandingsStore.swift:57`: `test_client_decl_gate.py:165`;
    `test_router_hints.py:853` (`[P3]`).
  - `StandingsStore.save(_:at:)` (`StandingsStore.swift:66`), via `currentKept(now:fetch:)` (`:85`),
    called at `ContentView.swift:981`: `StandingsStoreTests` (INV-74). Gap: the caller's date (R1).
  - `StandingsStore.init(url:)` (`:34`): INV-74's
    `testAStorePointedAnywhereButAFileReadsNothing`.
- **INV-63 (a URL made from text is the network outside the door).**
  - Named initialisers (`NETWORK`, `client_decl_gate.py:105-117`): `test_client_decl_gate.py:33`.
  - A decode whose substitution names `URL` (`DECODES_URL`, `:268`): `:47`, `:70`.
  - A call whose type is a URL (`MAKES_URL`, `:395`; `url_facts`, `:399`): `:240`; fixture.
  - `NSDataDetector` and `NSTextCheckingResult.url`: `:250`; fixture.
  - The shipping client's own URL makers: `EngineClient.engineURL(from:)` (`EngineClient.swift:169`),
    `components.url!` (`:282`), `StandingsStore.onDevice` (`StandingsStore.swift:40-46`): allowed by
    file.
  - Gaps: container results of a generic call; the `URL.made` exemption for `FrontDoor.swift` (B2).
- **INV-76 (the phone changes no served number and orders nothing itself).**
  - The served numbers: the nine fields of `SERVED_NUMBERS` (`:225`). Gap: six more decoded
    fields, and `behindBy` (B1).
  - Permitted arithmetic: `Uncertainty.swift:77`, `:79`, `:83`, `:193`, `:194`, `:361`;
    `Combine.swift:77`, `:78`, `:104`, `:106`; `Router.swift:933`; `Language.swift:218` (measured
    from the gate's facts on the shipping client): `test_client_decl_gate.py:216`.
  - Arithmetic through a binding or a free function's parameter: `:200`; fixture. Gaps:
    assignment, return value, method parameter, loop shapes, operators and types (B1);
    file-wide price permission (M5).
  - Permitted sorts: `Combine` (`common`, `placed`), `FrontDoor` (`entries` ×2), `Notices`
    (`ages`, `distinct`), `Reading` (`row`): `test_client_decl_gate.py:207`; the text tripwire.
    Gap: Foundation sorts in the compiled half (M4).
- **INV-85 (no cookie kept or sent).** The default configuration (`EngineClient.swift:205-215`):
  `EngineClientTests.swift:840`; `test_client_decl_gate.py:257`. An injected `session:` is used by
  tests only; the app builds `EngineClient()` (`ContentView.swift:85`). No gap found.
- **INV-78 (the pins read built code).** `_code` and `_built` (`test_router_hints.py:80`, `:122`):
  `:887`. Gap: `test_ios_client_contract.py` pins read raw text (M3).
- **INV-62, INV-67.** Unchanged producers. Their new test citations hold (above).

Gaps, tracked: B1, B2 (blocking); M1, M3, M4, M5 (minor); R1.

## Acceptance criteria evidence (REQUIRED for PASS verdict)

- **REQ-GAP-001 / the W2 privacy criterion** ("nothing derived from the question reaches a request
  or the standings file, by any route the compiler accepts"):
  - Code: `scripts/client_decl_gate.py:214-220` (`SINK_FILES`, `PROVENANCE`), `:364-427`, `:609-613`.
  - Tests: `tests/unit/test_client_decl_gate.py:154`, `:165`, `:172`, `:57` (fixture);
    `tests/unit/test_router_hints.py:846`, `:853`.
  - **Not met as worded:** B2 (U5, U3b). The REQ-ID is cited by no test (M7).
- **REQ-APP-005 / the W2 arithmetic criterion** ("however the value is named"):
  - Code: `client_decl_gate.py:225-247`, `:507-604`.
  - Tests: `test_client_decl_gate.py:200`, `:207`, `:216`; the fixture's
    `("ContentView.swift", "served position")` and `("Combine.swift", "sorts `common`")`.
  - **Not met as worded:** B1.
- **REQ-API-001 / "the engine's own sameness rule reaches the phone"** (D-182):
  - Code: `src/app/adapter/main.py:958`; `src/app/workflows/recommend.py:191`, `:505-506`, `:561`,
    `:576`, `:595`; `ios/ModelRanking/Engine/Models.swift:234`, `:255`; `AnswerPlan.swift:187-193`.
  - Tests: `tests/unit/test_api_v1.py:99`, `:779`; `ios/EngineTests/AnswerPlanTests.swift:355`,
    `:365`.
  - Met, with M6 (the engine-side test cannot tell a name from an id) and M7.
- **G-1 shown red on its planted mutants (P2, P3):** fixture `client_decl_fixtures/EngineClient.swift`,
  `ContentView.swift`; `test_client_decl_gate.py:154`, `:165`; replayed by me on the shipping
  client in all four configurations. Met.
- **G-2 shown red:** `test_client_decl_gate.py:200`, `:207`. Met for the named mutants; B1 for the
  criterion.
- **G-3 shown red:** `test_client_decl_gate.py:240`, `:250`; `test_router_hints.py:874`, `:887`.
  Met for the named mutants; B2 and M3 for the criterion and INV-78.
- **#144:** `EngineClient.swift:212-214`; `EngineClientTests.swift:840`;
  `test_client_decl_gate.py:257`. Met (M9).
- **#132:** left by the valve, `m19-plan.md:198-202`.

## Every file in the diff

| File | What changed | Read |
|---|---|---|
| `docs/decisions.md` | D-180, D-181, D-182 | whole; B1, B2, M1, M2, M4, M5 cite clauses |
| `docs/plans/m19-plan.md` | W2 amendment | whole |
| `docs/plans/m19-wave-2-plan.md` | the wave plan | whole; M9 |
| `docs/prd.md` | REQ-API-001, REQ-APP-005, REQ-GAP-001 rows | the three rows; B1, M5 |
| `docs/security-invariants.md` | INV-62/63/66/67/76/78 reworded, INV-85, G-1 to G-3 removed | the diff and the count (73 rows, measured) |
| `ios/EngineTests/AnswerPlanTests.swift` | two #138 tests | whole hunk; run by `swift-test` |
| `ios/EngineTests/EngineClientTests.swift` | `EngineCookieTests` | whole hunk; M9 |
| `ios/EngineTests/test-manifest.txt` | three names | the manifest diff passes |
| `ios/ModelRanking/Engine/AnswerPlan.swift` | `sameRow` by id | whole function; M8 |
| `ios/ModelRanking/Engine/EngineClient.swift` | cookies off | `init` and `fetch`; B2 |
| `ios/ModelRanking/Engine/Models.swift` | `Pick.modelId` | the struct; B1 (the unlisted fields) |
| `scripts/client_decl_fixtures/*.swift` (6) | the fixture mutants and allows | whole; compiled by `self_test` |
| `scripts/client_decl_gate.py` | sink, flow and URL rules | line by line; B1, B2, M1, M4, M5, M8 |
| `src/app/adapter/main.py` | `model_id` in `PUBLIC_PICK_FIELDS` | hunk |
| `src/app/workflows/recommend.py` | `model_id` per pick, by row identity | `recommend()`; M6 |
| `tests/unit/data/g2_fixture_ast.txt` | AST snapshot | skimmed; paths are `/x/` only |
| `tests/unit/test_api_v1.py` | `PICK_KEYS`, the id test | hunk; M6 |
| `tests/unit/test_client_decl_gate.py` | nine tests | whole hunk |
| `tests/unit/test_router_hints.py` | `_built`, EGRESS, sink pins, three tests | whole hunk; M2, M3 |
| `tests/unit/test_uncertainty_contract.py` | `model_id="m"` | hunk |

No drive-by edits: every file serves an issue the plan lists. I found no swallowed exception and no
copied block of five lines or more. One duplication smell: `pathlib.Path(line.split('"')[1]).name`
appears three times, and the dump is parsed by two walkers (`_shared_state` and `_tree`).

## K.8 contract drift check

The wave plan's contracts (`m19-wave-2-plan.md:44-57`), `grep -n` at `40bb4d1`:
```
scripts/client_decl_gate.py:118:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:134:FILESYSTEM_FILES = {
scripts/client_decl_gate.py:272:FIXTURE_REFUSALS = {
scripts/client_decl_gate.py:340:def references(ast: str) -> dict[str, set[str]]:
scripts/client_decl_gate.py:681:def problems(found: dict[str, set[str]]) -> list[str]:
ios/ModelRanking/Engine/EngineClient.swift:159:struct EngineClient {
ios/ModelRanking/Engine/EngineClient.swift:205:            let configuration = URLSessionConfiguration.ephemeral
ios/ModelRanking/Engine/EngineClient.swift:248:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/AnswerPlan.swift:173:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
tests/unit/test_router_hints.py:80:def _code(swift: str) -> str:
```
- Verdict: OK. Every symbol is present with its signature unchanged; only line numbers moved, from
  additions above them. `PUBLIC_PICK_FIELDS` gained `model_id` under D-182, written before the
  field is served (`m19-plan.md:156-157`). `HeldReading` stays in the view because #132 left.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py:122-131` (`FILESYSTEM`). **`String(contentsOf:encoding:)` is
  not on the compiled gate's lists.** Neither are `NSData(contentsOf:)` and
  `XMLParser(contentsOf:)`, and each loads an `https` URL. U7 (`try? String(contentsOf:
  EngineClient.localDefault, encoding: .utf8)` in `ContentView.swift`) passed `client-decls`; only
  the text gate's `\bcontentsOf\s*:` refused it. This is a second network door on the compiled half,
  and it predates the wave. Bug.
- **K2** `tests/unit/test_ios_client_contract.py:257-266`. **The text tripwire keeps its own
  `SERVED_NUMBERS`, beside the gate's (`client_decl_gate.py:225`).** The two lists already differ
  (`position`), and neither is derived from `Models.swift`. This is one fact in two places, the
  practices file's most reproduced finding (K.5). Enhancement: derive both from the decoded fields.

## Risks queued to next M

- **R1** `StandingsStore.save(_:at:)` (`StandingsStore.swift:66`) writes the caller's date, and
  `currentKept(now:)` (`:85`) takes `now` from the screen (`ContentView.swift:981` passes
  `Date()`). A date is a 64-bit channel from the screen into the standings file, and D-180's
  provenance rule does not see it. It becomes real when any caller passes something other than
  `Date()`.
- **R2** The flow keys parameters and loop elements by `(file, name)` (`client_decl_gate.py:520`,
  `:527`). So a later, unrelated value with the same name in that file reads as a served number.
  It shows as a refusal on a value that never came from the engine, and it pushes the author to
  rename or to widen a permission.
- **R3** The sink and flow rules parse the printed layout of `swiftc -dump-ast`: labels,
  `original_init`, `function_ref=single apply`, `writeImpl=stored`. Apple does not promise that
  layout. `self_test` runs one configuration over the fixture's shapes only. An Xcode update could
  silence a fact on the shipping client (today: 8 in `Uncertainty.swift`, 6 in `Combine.swift`)
  while the fixture stays correct. A floor on the shipping client's fact counts would show it.

## Mutants planted, and what caught each

Method: a Python harness read each file's bytes, wrote the mutant, ran the checks, then restored the
bytes in a `finally` and compared them. Every restore was byte-identical, and `git status --short`
was empty after each run. "Decl" is `client_decl_gate` on the simulator Release configuration, or
all four configurations where marked. "Text" is eight pin files (`test_router_hints`,
`test_ios_client_contract`, `test_ios_platform_drift`, `test_ios_payload_contract`,
`test_swift_tests_offline`, `test_refinements`, `test_ios_visual_contract`,
`test_uitext_sentence_rows`), stopping at the first failure. "Make" is a full `make check-fast`.

| Id | Where | Mutant | Decl | Text | Make |
|---|---|---|---|---|---|
| P2 | EngineClient + ContentView | M17 relay: `nonisolated(unsafe) static var`, read by `boards()` | refused (4/4) | refused | — |
| P3 | ContentView | M17 store: `FetchedStandings(payload:)` from typed text, saved | refused (4/4) | refused | — |
| A0 | ContentView | `let shown = pick.score; shown * 2` | refused | refused | — |
| A1 | ContentView | reassigned `var place` (B1) | passed | passed | **PASS** |
| A2 | ContentView | a function's return value (B1) | passed | passed | **PASS** |
| A3 | ContentView | computed property on `Standing` (B1) | passed | passed | — |
| A4 | ContentView | `ProbeBox(value: standing.position).value + 1` | refused | passed | — |
| A5 | ContentView | `standing.position &+ 1` (B1) | passed | passed | — |
| A6 | ContentView | `standing.position.advanced(by: 1)` (B1) | passed | passed | — |
| A7 | ContentView | `Int32(standing.position) + 1` (B1) | passed | passed | — |
| A8 | ContentView | `(category.scoreAnchor ?? 0) - 100` (B1) | passed | passed | — |
| A9 | ContentView | `Decimal(pick.score) * 2` | passed | refused (score on screen) | — |
| A10 | ContentView | loop over `[standing.position]` (B1) | passed | passed | — |
| A11 | ContentView | `for (index, place) in places.enumerated()` (B1) | passed | passed | — |
| A12 | ContentView | a method's parameter (B1) | passed | passed | — |
| A13 | ContentView | a free function's parameter | refused | passed | — |
| A14 | Router | a second price arithmetic, through a local (M5) | passed | passed | — |
| O1 | ContentView | `sorted(using: KeyPathComparator(...))` (M4) | passed | refused (ordering) | — |
| S1 | ContentView + EngineClient | class `var` through a global `let`, read in `fetch` | refused | passed | — |
| S2 | ContentView + EngineClient | getter in ContentView, read in `fetch` | passed | passed | FAIL (swift-test cannot compile) |
| S2b | Detail + ContentView + EngineClient | the same getter in `Detail.swift` (M1) | — | — | **PASS** |
| S3 | EngineClient + ContentView | `static let probeRelay = NSMutableString()` (M1) | passed | passed | **PASS** |
| U2 | ContentView | generic `[String: T]` decode, then `EngineClient(baseURL:)` | passed | refused (second client in view) | — |
| U3 | FrontDoor, end | `engineURL(from: … + typed)`, then `EngineClient(baseURL:)` | passed | refused (register reaches `EngineClient`) | — |
| U3b | FrontDoor, above the register | the same (B2) | — | — | **PASS** |
| U4 | ContentView | `Bundle.main.url(forResource:withExtension:)` (M8) | refused | passed | — |
| U5 | Detail + ContentView | U2's code in an Engine file (B2) | passed (4/4) | passed | **PASS** |
| U7 | ContentView | `String(contentsOf: EngineClient.localDefault, …)` (K1) | passed | refused (`contentsOf:`) | — |
| F1 | EngineClient | `SameHostOnly` under `#if false`, plain call under `#else` | passed | refused (second request path) | — |
| F2 | EngineClient | both timeouts under `#if false` (M3) | — | — | **PASS** |
| E1 | recommend.py | ids looked up by display name (M6) | — | — | whole Python suite 1974 passed |

## Gates and probes run

- `make check-fast` on the clean tree: PASS in 61.5 s (lint, typecheck, records, test, client-decls,
  swift-test).
- `.venv/bin/python -B scripts/client_decl_gate.py`: PASS, 19 files in 4 configurations (2,431 /
  2,436 / 2,431 / 2,436 declarations).
- The wave's new Python tests, by name: 23 passed (`test_client_decl_gate.py` whole,
  `test_api_v1.py::test_each_pick_carries_the_id_of_the_model_it_ranks`, the five new
  `test_router_hints.py` tests).
- The mutants above: 31 planted. 7 refused by the compiled gate, 6 refused by the text pins only,
  1 refused by `swift-test` only, 17 passed every check that ran on them. Seven of those 17 passed a
  full `make check-fast`, and E1 passed the whole Python suite.
- Not run: `make ui-test` (the guard stubs refuse `simctl` and `xcodebuild`). No installer, no
  launchd job, no network from a test. `gh issue view` read #60, #85, #107 and #110.
