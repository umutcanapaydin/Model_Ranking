---
record_type: review
id: m19-wave-2-rereview
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# M19-W2 Code Re-review: the phone's promises, held by what the code does

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records,
and none of the fixes made after the first review.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `1843437..4e737ea` (31 commits; 29 files, +5,562 / -58). The commits after `40bb4d1`
answer the first review (`docs/reviews/m19-wave-2-review.md`, BLOCKING).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:62-64`; `docs/plans/m19-wave-2-plan.md:13-15`). The diff
touches `EngineClient.swift` and `src/app/adapter/main.py`, both security globs (`m19-plan.md:123-132`).
By D-172 no security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane` on all 31
commits) / reviewer-family: claude-opus (fallback: no second family is available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile and
`.agents/rules/practices.md` from `origin/main`. Then I read the milestone plan (§1 W2, §2 W2, §3, §5 and
both W2 amendments), the wave plan, D-180 to D-182, the invariants diff and the first review. Then I
read the diff, and the commit messages last.

**Summary.** Every mutant of the first review is now refused where it was planted, and I replayed each
one. The privacy-sink rules, the provenance rule and the flow of served numbers are real work, and the
gate's self-checks (`unseen_permissions`) answer the first review's R3 well.

But the records still claim more than the code holds. The milestone criterion says nothing derived
from the question reaches a request or the standings file "by any route the compiler accepts". D-180
and INV-66 say "only `EngineClient.swift` builds a client on an address of its own". The plan amendment
says the client's address is kept in `EngineClient.swift`, and the invariants say gap G-1 is closed.
D-181 says "any operator on a number". I planted ordinary Swift. For P3w, U11, S5 and the arithmetic
set I edited no privacy sink and no security glob, and `make check-fast` passed with all six legs green
each time:

1. **B1.** The M17 closure's own P3 mutant: the typed question is saved as the standings, through a
   protocol requirement that `FetchedStandings.init(payload:)` satisfies (P3w). A client is built on
   `<engine>/<typed>` the same way (U8). With a URL made through `Any`, the client can point at any
   host (U11).
2. **B2.** The typed question is written into the standings file through the body of a call the sink
   is permitted to make, `FetchedStandings.init(payload:)` in `Models.swift` (S5). It also gets there
   through a `Decodable` witness in `Models.swift` (S5b). A store built on a path made from the
   question also passed every compiled configuration and the text pins (U10).
3. **B3.** Arithmetic on a served number passes through shapes that D-181 clauses 1 to 3 say are
   refused: prefix `-`, `<<`, `reduce(0, +)`, `pow`, `truncatingRemainder`, `quotientAndRemainder`, a
   method on `Int` (`self`), an enum payload, a subscript, a tuple assignment, a closure or loop whose
   name is on the next line, and a type that conforms to `Decodable` in an extension.

B1 and B3 are the second BLOCKING verdict on the first review's B2 and B1, in that order. Under the practices file's
"three attempts" rule (`/close-wave` step 3), a third would stop the slice. So for each I name a
structural fix where one exists, and the narrowing that would close it honestly where none does. There
are also six MINOR findings, one K.9 candidate and three risks.

## Verdict

BLOCKING

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `scripts/client_decl_gate.py:227-237` (`PROVENANCE`), `:561-562` (the `<builds>` fact, keyed on
  the referenced symbol), `:483-496` (`MAKES_URL`, `url_facts`: call expressions only).
  **Construction is guarded by the name of the initialiser, so a protocol requirement it satisfies
  builds standings and clients from any file.** Why it blocks: the W2 criterion (`m19-plan.md:39`) is
  "Nothing derived from the question reaches a request or the standings file, by any route the
  compiler accepts". G-1 is recorded closed (`security-invariants.md:162`). D-180 clause 2
  (`decisions.md:3944-3948`) and INV-66 (`security-invariants.md:127`) say "only the engine's answer
  and the store's file build standings; and only `EngineClient.swift` builds a client on an address
  of its own". The W2-review amendment (`m19-plan.md:204-209`) says B2 was fixed "by keeping the
  client's address in `EngineClient.swift`". P3w is the M17 mutant the wave exists to close.
  Evidence, all on the shipping client, with the bytes restored and compared after each run:
  ```swift
  // P3w. Detail.swift (an Engine file, not a security glob)
  protocol ProbeMadeFromBytes { init(payload: Data) throws }
  extension FetchedStandings: ProbeMadeFromBytes {}
  func probeMake<S: ProbeMadeFromBytes>(_ kind: S.Type, _ bytes: Data) -> S? { try? S(payload: bytes) }
  func probeKeep(_ typed: String) {
      let kept = "{\"api_" + "version\": \"" + typed + "\", \"attributions\": [], \"boards\": [], \"models\": []}"
      if let made = probeMake(FetchedStandings.self, Data(kept.utf8)) { StandingsStore.onDevice.save(made, at: Date()) }
  }
  // ContentView.swift, in ask(), after `let typed = ...`
  probeKeep(typed)
  ```
  ```swift
  // U11. Detail.swift: the URL is made through `Any`, and the client through the same kind of requirement
  protocol ProbeAddressed { associatedtype Address; associatedtype Session; init(baseURL: Address, session: Session?) }
  extension EngineClient: ProbeAddressed {}
  func probeBuild<C: ProbeAddressed>(_ kind: C.Type, _ address: C.Address) -> C { C(baseURL: address, session: nil) }
  func probeHoldAny<T: Decodable>(_ example: T, _ data: Data) -> Any? { try? JSONDecoder().decode(T.self, from: data) }
  func probeRelaysTheQuestion(_ typed: String) async -> FetchedStandings? {
      let json = "\"htt" + "ps:/" + "/elsewhere.invalid/" + typed + "\""
      guard let address = probeHoldAny(EngineClient.localDefault, Data(json.utf8)) as? EngineClient.Address else { return nil }
      return try? await probeBuild(EngineClient.self, address).boards()
  }
  // ContentView.swift
  func probeUse(_ typed: String) async -> FetchedStandings? { await probeRelaysTheQuestion(typed) }
  ```
  `make check-fast` PASSED with P3w, with U11, and with U8 (U11's requirement, with the address
  `EngineClient.localDefault.appendingPathComponent(typed)` made in `FrontDoor.swift` above the register's
  MARK). That makes the boards request to `<engine>/<typed>/v1/boards`. U8b, the same with any host,
  passed all four configurations and the text pins. U9 rewrites the app's own client's `baseURL` in
  place, through `withUnsafeMutablePointer` and `withMemoryRebound`, in `FrontDoor.swift`. It passed all
  four configurations and the text pins.
  The causes, in code:
  1. `sink_facts` records `<builds>` only for a reference whose symbol is a `PROVENANCE` key
     (`:561`). A call through a protocol requirement resolves to `main.(file).ProbeAddressed.init(...)`.
     The conformance prints as `(extension_decl ... "EngineClient" inherits="ProbeAddressed"`, with no
     witness reference (measured in the dump with U8 planted).
  2. `StandingsStore.save(_:at:)` (`StandingsStore.swift:66`) can be called from any file. The app
     calls it only through `currentKept` (`:92`).
  3. `url_facts` reads only `call_expr` and `constructor_ref_call_expr` types. A URL that comes out of
     an `as?` cast from `Any` is made by no call.
  4. Nothing refuses unsafe memory. The shipping client resolves no `Unsafe*`, `withUnsafe*` or
     `unsafeBitCast` declaration: 0 in the simulator Release dump, so refusing them costs nothing.

  To clear it, either:
  - (a) refuse any conformance of a `PROVENANCE` type to a protocol the app declares, wherever it is
    declared (an `extension_decl` of the type, and the `inherits=` of its own declaration:
    `FetchedStandings` is declared in `Models.swift`, which is not a sink). Give
    `StandingsStore.save(_:at:)` a `PROVENANCE` entry for `StandingsStore.swift`. Refuse the unsafe
    family in the client, and refuse a cast to a type naming `URL` outside the three files (or narrow
    INV-63, M6). Each fix gets a red test made from P3w, U8, U11 and U9.
  - (b) or narrow D-180 clause 2, INV-66, the REQ-GAP-001 row and the amendment to "by a reference to
    the initialiser". Reopen G-1 for conformances and unsafe memory.

- **B2** `scripts/client_decl_gate.py:247-251` (`SINK_CALLS_PERMITTED`), `:522-545` (`_sink_calls`),
  `ios/ModelRanking/Engine/Models.swift:408-421` (`FetchedStandings`), `StandingsStore.swift:34`
  (`public init(url:)`). **What a sink keeps is decided by code outside the sinks that no rule
  reads.** Why it blocks: INV-66 (`security-invariants.md:127`) says nothing derived from the question
  reaches the standings file. D-180 clause 3 (`decisions.md:3956-3957`) says "a sink sends or keeps
  only what its parameters, its own configuration and the engine's answer give it". D-180's "What it
  does not do" (`:3978-3981`) says "The gate holds the routes an edit elsewhere can take". INV-67
  (`:128`) says the question is kept only in the gap register. These mutants edit `Models.swift`,
  `FrontDoor.swift` and `ContentView.swift`, and no sink.
  Evidence:
  ```swift
  // S5. Models.swift, inside FetchedStandings.init(payload:) (:420), and a global beside it
  payload = try encoder.encode(standings) + Data(probeKeptNote.utf8)
  var probeKeptNote = ""
  // ContentView.swift, in ask()
  probeKeptNote = typed
  ```
  `make check-fast` PASSED. `boards()` (`EngineClient.swift:259`) and `load()`
  (`StandingsStore.swift:57`) both call the listed `FetchedStandings.init(payload:)`. `save`
  (`StandingsStore.swift:73`) writes its `payload` to the caches folder. INV-74's test of the stored
  fields passes, because it runs with the global empty.
  S5b puts the same relay in a custom `init(from:)` on `StandingModel` in `Models.swift`, which
  `FetchedStandings.init` reaches through `JSONDecoder` and then encodes again. It passed all four
  configurations and the text pins. U10 is `StandingsStore(url: GapRegisterStore.onDevice.url
  .deletingLastPathComponent().appendingPathComponent(typed))` in `FrontDoor.swift`, which the screen
  uses for its `currentKept` call. It passed all four configurations and the text pins: the standings
  are kept in a file named by the question. That is the first review's B2 cause (the caller sets the
  sink's configuration), on the second sink.
  To clear it, either:
  - (a) apply the sink rules to the bodies a sink is permitted to reach, and to the `Codable`
    conformances of every type a sink encodes or decodes. Or move `FetchedStandings` and the coding of
    what it stores into a sink file. Give `StandingsStore.init(url:)` a `PROVENANCE` entry: only
    `StandingsStore.swift` calls it today (`onDevice`, `:43`). Add red tests made from S5, S5b and U10.
  - (b) or write into D-180 and INV-66 that `FetchedStandings.init(payload:)`, `UIText.engineAddress`
    and the standings types' coding in `Models.swift` are trusted as sink code. Add `Models.swift` to
    the security globs (`m19-plan.md:123-132`). Keep G-1 open for the store's address.

- **B3** `scripts/client_decl_gate.py:358` (`OPERATOR`: `[-+*/%]` only), `:366-368`
  (`NUMERIC_METHOD`: a list, and extension members only), `:933-949` (`_arithmetic`: `binary_expr`
  only), `:353` (`DECODED_TYPE`: the type's own declaration only), `:790-810` and `:874-889` (`loop`,
  `condition`, `closure`: keyed on the line the `for`, the value or the `{` starts), `:769-772`
  (`_target`: the first name of a tuple). **Arithmetic on a served number still passes, through
  operators and names the records say are refused.** Why it blocks: the W2 criterion
  (`m19-plan.md:39`), as amended (`:209-211`: "holds except through `Any` or text"). D-181 clause 1
  (`decisions.md:4002`: a served number is "found on the compiled module, never listed by hand"),
  clause 2 (`:4007-4014`: a loop, a condition, a case, a closure, an assignment, a method's
  parameter) and clause 3 (`:4015`: "Any operator on a number ... or a numeric method"). INV-76
  (`security-invariants.md:142`). REQ-APP-005 (`prd.md:427`). None of these shapes goes through `Any`
  or text.
  Evidence: all of these, planted at once in `Detail.swift`, passed `make check-fast`. The same set
  passed all four configurations and the 13 pin files with Swift:
  ```swift
  func probeN1(_ standing: Standing) -> Int { -standing.position }                       // prefix `-`
  func probeN2(_ standing: Standing) -> Int { standing.position << 1 }                   // `<<` (and `<<=`, N14)
  func probeN3(_ standings: [Standing]) -> Int { standings.map(\.position).reduce(0, +) } // an operator as a value (and `.map(-)`, N17)
  func probeN4(_ pick: Pick) -> Double { pow(pick.score, 2) }                            // `pow`
  func probeN5(_ pick: Pick) -> Double { pick.score.truncatingRemainder(dividingBy: 10) } // a numeric method off the list
  func probeN6(_ standing: Standing) -> Int { standing.position.quotientAndRemainder(dividingBy: 2).quotient }
  func probeN16(_ standing: Standing) -> Int { standing.position.dividedReportingOverflow(by: 2).partialValue }
  enum ProbeWrap { case place(Int) }                                                     // a case's binding, from an enum payload
  func probeN8(_ standing: Standing) -> Int { let wrapped = ProbeWrap.place(standing.position); switch wrapped { case let .place(p): return p + 1 } }
  extension Int { func probeBumped() -> Int { self + 1 } }                               // a method's `self`
  func probeN10(_ standing: Standing) -> Int { standing.position.probeBumped() }
  extension Double { var probeHalved: Double { self / 2 } }                              // a computed property's `self`
  func probeN11(_ pick: Pick) -> Double { pick.score.probeHalved }
  struct ProbeGrid { subscript(place: Int) -> Int { place * 2 } }                        // a subscript's parameter
  func probeN13(_ standing: Standing) -> Int { ProbeGrid()[standing.position] }
  ```
  These passed all four configurations and the text pins too:
  ```swift
  standings.map(\.position).map {
      place in place - 1                       // N18: a closure's name on the line after its `{`
  }
  if let place =
      Optional(standing.position) { return place + 1 }  // N19: an `if let` whose value starts on the next line
  (spare, place) = (0, standing.position); return place + 1  // N20: the served value in a tuple's second place
  for
      place in standings.map(\.position) { total = place * 2 }  // N21: a loop's name on the line after `for`
  struct ProbeServed { let level: Int }; extension ProbeServed: Decodable {}  // N22: conformance in an extension
  func probeN22b(_ served: ProbeServed) -> Int { served.level * 2 }
  ```
  Controls, which were refused: the first review's A0 to A13 and O1 (all four configurations), and
  `category.scoreAnchor.map { $0 - 100 }` (N9). `standing.position + ProbeTag()`, through a custom `+`,
  passed the compiled gate. The position tripwire refused it by its spelling (N12).
  I leave `rounded()` and `magnitude` out of this finding. D-181 says rounding is not arithmetic here,
  and `money()` (`Router.swift:923`) rounds a served price to format it.
  To clear it, either:
  - (a) widen each piece: every operator on a numeric type, prefix ones included, and an operator used
    as a function value; every method of a numeric type; `self` in a member of a numeric type; enum
    payloads and subscripts; every name of a tuple; carriers keyed by the name's own declaration, not
    the line its statement starts; conformances in extensions. Each with a red test from these
    mutants. This is the third denylist the gate would grow, and each review has found more.
  - (b) **recommended, given the three-attempts rule:** say in D-181 clauses 1 to 3, INV-76,
    REQ-APP-005 and the amendment which operators, methods and shapes the gate refuses, as written
    today. Keep G-2 open for the rest: widen #171, or file one issue, citing these mutants.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `scripts/client_decl_gate.py:449-476` (`_shared_state` reads only the app's own `var`s).
  **A sink can read shared state that Foundation holds.** S4: the screen sets
  `Thread.main.threadDictionary["t"] = typed`, and `fetch` adds a query item from it. It passed all four
  configurations and the text pins. It needs an edit inside `EngineClient.swift`, which D-180 trusts
  (`decisions.md:3978`), so this is MINOR, as the first review's M1 was. But INV-66 and D-180 clause 2
  say a sink "reads [no] mutable state another file can set". Narrow that to "state the app
  declares", or list the Foundation stores (`threadDictionary`, `NotificationCenter`, `URLCache.shared`)
  and refuse them in a sink.
- **M2** `tests/unit/test_router_hints.py:871-875` (`STORED_STATIC`, `FILE_VAR`), `:176` (`_built`).
  **The text half of D-180 (clause 4, `decisions.md:3958-3961`) misses four shapes.** I measured
  `_sink_pin_problems` on edited copies of the shipping sources. All four PASSED:
  `static var (probeTag, probeOther) = ("", "")`; `var (probeRelay, probeOther) = ("", "")` at file
  scope; `var probeRelay = ""` indented under `#if DEBUG`; and a `static var` placed after a
  multi-line string literal whose content is the line `#if false` (`_code` keeps strings, and `_built`
  then drops live code up to a string holding `#endif`). The compiled gate refused the tuple
  `static var` and the indented `var` in every configuration that builds them (I did not compile the
  tuple file-scope form). The first review's two forms (`static var probeTag: String?` and a
  file-scope `var`) are now refused.
- **M3** `tests/unit/test_ios_client_contract.py:34-37` (`_swift`). **The contract pins now drop live
  code that the pre-wave pins read.** `_swift` runs `_built` on raw text, comments included. So a
  `#if false` and an `#endif`, each inside a block comment, hide everything between them. F3 put
  `answers.sorted(using: KeyPathComparator(\Answer.eligibleCount))` and `standing.position + 1` there
  in `ContentView.swift`. The 13 pin files passed. The pre-wave `test_ios_client_contract.py`
  (`git show 1843437:...`), run against the same mutant, refused both (the position tripwire and the
  ordering tripwire). The compiled gate refused both. So only the lanes without Xcode lose this. INV-78
  (`security-invariants.md:150`) says the privacy pins read "not comments, strings" and the contract
  pins read "every Swift file without such a branch". F3 and M2's string form contradict that. Strip
  comments before `_built` here, and ignore directives inside string literals in `_built`, or narrow
  INV-78. The first review's F2 (both timeouts under `#if false`) is now refused.
- **M4** `scripts/client_decl_gate.py:373-374` (`ORDERING_CALL`). **Foundation's `NSArray` sorts are
  not counted.** `(answers.map(\.eligibleCount) as NSArray).sortedArray(comparator: ...)` (O2) and
  `.sortedArray(using: [NSSortDescriptor(...)])` (O4) passed all four configurations and the text
  tripwire. D-181 clause 4 (`decisions.md:4021`) says the gate counts Foundation's sorts.
  `NSMutableArray.sort(using:)` (O5) was refused by both. The first review's O1 is now refused.
- **M5** `scripts/client_decl_gate.py:722-742` (`carried` walks the whole operand subtree), `:756-767`
  (`binding`). **A refusal for the wrong reason.** `answers.filter { $0.eligibleCount > 0 }.count + 1`
  (FP1) is refused in all four configurations as "`+` on a served number, a second scoring
  implementation". The `+` is on a count of rows. `let n = <that count>; return n + 1` is refused the
  same way (FP2). D-181 clause 2 says a value carries a served number "only if its compiled type can hold one",
  but the walk does not apply that to sub-expressions: a closure argument inside the operand is
  enough. This is the false-refusal pressure the first review's R2 named. It pushes an author to
  restructure code, or to widen a permission. Stop the walk at a call whose result is not a carrier,
  or say in D-181 that it over-refuses.
- **M6** `docs/security-invariants.md:124` (INV-63). **"Returned by any call whatever it is named or
  whatever type holds it" is not what `url_facts` checks.** A URL that comes out of `Any` by a cast
  (`probeHoldAny(...) as? EngineClient.Address`, U11) is made in `Detail.swift`, and no rule refuses
  it. B1's fix covers the use. This finding is about the record: narrow it to "returned by a call
  whose result type names `URL`", or refuse casts to `URL` outside the three files (B1 (a)).

### PASS (what looks good)

- **Every mutant of the first review is now refused where it was planted**, and I planted each one
  again. A0 to A13, O1 and `behindBy` (16 refusals), A14, U5, U3b, S3 and S2b: the compiled gate, in all
  four configurations. M2's two forms: the text half. F2: the timeout pin. E1: the new
  `test_recommend.py:661`. The original P2 and P3 are still refused, in all four configurations and by
  the text pins.
- **The first review's M7, M8 and M9 are done.** 17 `REQ-` citations in `test_client_decl_gate.py`. The
  gate's docstring and `pickCards`'s doc are corrected. INV-85 now follows INV-84. The amendment
  (`m19-plan.md:211-212`) records why the cookie test reads the configuration.
- **`unseen_permissions` (`client_decl_gate.py:990-1008`) answers R3.** A permission, a listed sink call
  or a `NOT_SERVED` type that the shipping client no longer shows fails the gate. So a change in the
  compiler's printed layout cannot silence a permitted rule quietly.
- **Carriers are keyed by declaration location**, not by bare names, apart from the bound names in R1.
  That removes most of R2's false refusals.
- **The no-argument `EngineClient()` (`EngineClient.swift:201-203`) is a clean design.** The app's one
  client (`ContentView.swift:85`) carries no address, and the tests keep `init(baseURL:session:)`.
- **D-182 is complete and additive.** The id follows the row by identity (`recommend.py:503-506`).
  `test_two_models_that_share_a_name_keep_their_own_ids` now refuses the name-keyed lookup. An old
  engine keeps the four-value rule (`AnswerPlanTests.swift:366`). `category_ranking` is still
  `ranked_with_ids` without the ids (`rank.py:282-288`), so recommending is unchanged.
- **Red before green for every review fix:** `9a5785f`→`28fd9df`, `22c3d1c`→`ef2f4fc`,
  `90bfbd7`→`14087b4`, `72ead87`→`6752538`, `ce03842`→`e05b6fc`.
- **The records count is right.** 73 live rows (72 at the base, plus INV-85), and four hold in part
  (INV-6, INV-76, INV-81, INV-82), measured.
- **The committed AST snapshot matches the fixture.** 106 declarations in
  `tests/unit/data/g2_fixture_ast.txt` sit on the fixture lines they name; the only exceptions are
  memberwise initialisers, which sit on their struct's line.
- No AI attribution in the 31 commits. No drive-by edit: every file serves a listed issue or a review
  finding. No swallowed exception: `_decide` returns "unknown" on a parse error, and that keeps code.
- Gates green on the clean tree: `make check-fast` PASS in 61.0 s.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code; the citing test per producer; gaps.

- **INV-66: the boards request.**
  - `EngineClient.boards()` → `fetch("v1/boards", query: [])` (`EngineClient.swift:256-265`):
    `EngineClientTests.swift::testTheBoardsRequestCarriesNothing`; the text pin in
    `test_router_hints.py:878` (`_sink_pin_problems`), run by `:905`.
  - `fetch` builds the URL from `baseURL` (`:278-291`). The sink rules cover what it holds, reads and
    calls: `test_client_decl_gate.py:155`, `:383`, `:393`. Gap: Foundation-held state (M1).
  - The destination is `EngineClient.init(baseURL:session:)` (`:208`). `PROVENANCE`:
    `test_client_decl_gate.py:291`. **Gaps: a protocol requirement (U8, U11) and unsafe memory (U9). B1.**
  - `EngineClient.init()` (`:201`), used at `ContentView.swift:85`; `localDefault` (`:165`) and
    `engineURL(from:)` (`:169`, `PROVENANCE`): `test_client_decl_gate.py:291`.
- **INV-66 and INV-67: the standings file.**
  - `FetchedStandings.init(payload:)` (`Models.swift:412`) is `PROVENANCE`:
    `test_client_decl_gate.py:166`; `test_router_hints.py:912` (`[P3]`). **Gaps: a protocol requirement
    (P3w, B1), its own body (S5, B2), and the `Decodable` witnesses it reaches (S5b, B2).**
  - `StandingsStore.save(_:at:)` (`StandingsStore.swift:66`): `StandingsStoreTests` (INV-74). **Gap:
    any file may call it (P3w, B1).** The caller's date: #170.
  - `StandingsStore.init(url:)` (`:34`): INV-74's `testAStorePointedAnywhereButAFileReadsNothing`.
    **Gap: any file may build a store on a path made from text (U10, B2).**
  - `StandingsStore.currentKept(now:fetch:)` (`:85`), called at `ContentView.swift:981`.
- **INV-63: a URL made from text.** The named initialisers (`NETWORK`, `client_decl_gate.py:110-122`):
  `test_client_decl_gate.py:33`. Decodes: `:47`, `:70`. Calls whose type names `URL` (`url_facts`,
  `:486`): `:242`, `:304`, `:317`. A link detector: `:252`. **Gaps: a cast out of `Any` (U11, M6);
  `contentsOf:` readers (#168, filed).**
- **INV-76: served numbers and orderings.** Served fields (`served_fields`, `:608-627`): fixture A8,
  `test_client_decl_gate.py:359`. **Gap: a conformance in an extension (N22).** The flow (`_Flow`,
  `:704-898`): `:202`, `:359` (20 shapes). **Gaps: N8, N10, N11, N13, N18 to N21 (B3).** Operators and
  methods (`_arithmetic`, `:933-949`): `:359`. **Gaps: N1 to N6, N14, N16, N17 (B3).** Permissions
  (`ARITHMETIC_PERMITTED`, `:265-274`): `:218`, `:376`, and `unseen_permissions`. Sorts (`_ordering`,
  `:952-961`; `SORTS_PERMITTED`, `:282-290`): `:209`, `:369`. **Gap: `NSArray` sorts (M4).**
  Over-refusal: FP1, FP2 (M5).
- **INV-78: what the pins read.** `_code` + `_built` (`test_router_hints.py:80`, `:176`): `:946`, `:981`,
  `:989`, `:995`. `_swift` (`test_ios_client_contract.py:34`): `test_every_swift_pin_here_reads_the_code_the_compiler_builds`.
  **Gaps: a directive inside a comment (F3, M3) or a string (M2).**
- **INV-85: no cookie.** `EngineClient.swift:220-222`: `EngineClientTests.swift:841`;
  `test_client_decl_gate.py:259`. Only tests inject a session, and `PROVENANCE` keeps the injecting
  initialiser in its own file. No gap found (U8 and U11 pass `session: nil`, which builds the cookieless
  default).

Gaps, tracked: B1, B2, B3 (blocking); M1 to M6 (minor); R1. Already filed: #168, #169, #170, #171.

## Acceptance criteria evidence (REQUIRED for PASS verdict)

- **REQ-GAP-001 / the W2 privacy criterion** ("nothing derived from the question reaches a request or
  the standings file, by any route the compiler accepts"):
  - Code: `client_decl_gate.py:219-251` (`SINK_FILES`, `PROVENANCE`, `SINK_HELD_TYPES`,
    `SINK_CALLS_PERMITTED`), `:449-563`; `EngineClient.swift:200-225`.
  - Tests: `test_client_decl_gate.py:155`, `:166`, `:173`, `:291`, `:383`, `:393`, `:57` (fixture);
    `test_router_hints.py:905`, `:912`, `:966` (the text half). Each cites REQ-GAP-001.
  - **Not met as worded:** B1 (P3w, U8, U11, U9), B2 (S5, S5b, U10).
- **REQ-APP-005 / the W2 arithmetic criterion** ("however the value is named", as amended):
  - Code: `client_decl_gate.py:253-290`, `:566-987`.
  - Tests: `test_client_decl_gate.py:202`, `:209`, `:218`, `:359`, `:369`, `:376`.
  - **Not met as worded:** B3. The ordering half: M4.
- **REQ-API-001 / "the engine's own sameness rule reaches the phone"** (D-182):
  - Code: `src/app/adapter/main.py:958`; `src/app/workflows/recommend.py:191`, `:503-506`, `:561`,
    `:576`, `:595`; `ios/ModelRanking/Engine/Models.swift:234`, `:255`; `AnswerPlan.swift:188-194`.
  - Tests: `tests/unit/test_api_v1.py:99`, `:779`; `tests/unit/test_recommend.py:661`;
    `ios/EngineTests/AnswerPlanTests.swift:355`, `:366`. Each cites REQ-API-001.
  - **Met.**
- **G-1 shown red on its planted mutants (P2, P3):** met for the two named mutants (fixture,
  `test_client_decl_gate.py:155`, `:166`; replayed in all four configurations). The gap is not closed
  as recorded (`security-invariants.md:162`): P3w is P3 through a protocol requirement (B1).
- **G-2 shown red:** met for the named mutants and the first review's 16. Open beyond `Any` and text:
  B3, M4.
- **G-3 shown red:** `URL(_:strategy:)`, `NSDataDetector` and the decode wrapper are refused
  (`test_client_decl_gate.py:242`, `:252`, fixture). `#if false` is refused (`test_router_hints.py:946`,
  `:981`, `:995`; the contract pins, F2 replayed). Records overclaim: M3, M6.
- **#144:** `EngineClient.swift:220-222`; `EngineClientTests.swift:841`; `test_client_decl_gate.py:259`.
  Met.
- **#132:** left by the valve, `m19-plan.md:198-202`.

## The first review's findings, checked again by their own mutants

| Id | Its mutant, planted again | Now |
|---|---|---|
| B1 | A0 to A13, O1, `behindBy` in `ContentView.swift`; A14 in `Router.swift` | refused, all four configurations; the class recurs (B3) |
| B2 | U5 (`Detail.swift` + `ContentView.swift`), U3b (`FrontDoor.swift`) | refused, all four configurations; the class recurs (B1) |
| M1 | S3 (`NSMutableString` on the client), S2b (a getter in `Detail.swift`) | refused, all four configurations; Foundation state passes (M1 here) |
| M2 | `static var probeTag: String?`; a file-scope `var` | refused by `_sink_pin_problems`; four more shapes pass (M2 here) |
| M3 | F2: both timeouts under `#if false` | refused by `test_the_client_bounds_how_long_it_will_wait` |
| M4 | O1: `sorted(using: KeyPathComparator(...))` | refused, all four configurations; `NSArray` passes (M4 here) |
| M5 | A14: `let price = pick.blendedPerM; return price * 0.8` in `Router.swift` | refused, all four configurations |
| M6 | E1: ids looked up by display name in `recommend.py` | refused by `test_recommend.py:661` (`test_api_v1.py` still passes it) |
| M7 | REQ-IDs in the new tests | done |
| M8 | docstring, `pickCards`, INV-85's place | done |
| M9 | the cookie test's change, recorded | done (`m19-plan.md:211-212`) |
| K1, K2, R1 | filed | #168, #169, #170 (open) |
| R2, R3 | keyed by location; `unseen_permissions` | done, apart from R1 here |

## Every file in the diff

| File | What changed | Read |
|---|---|---|
| `docs/decisions.md` | D-180, D-181, D-182 | whole; B1, B2, B3, M1, M4, M5 cite clauses |
| `docs/plans/m19-plan.md` | two W2 amendments | whole; B1, B3 |
| `docs/plans/m19-wave-2-plan.md` | the wave plan | whole |
| `docs/prd.md` | REQ-API-001, REQ-APP-005, REQ-GAP-001 rows | the three rows |
| `docs/reviews/m19-wave-2-review.md` | the first verdict | whole; every finding replayed |
| `docs/security-invariants.md` | INV-62/63/66/67/76/78 reworded, INV-85, G-1 and G-3 removed, G-2 narrowed | the diff and the count (73 rows, measured) |
| `ios/EngineTests/AnswerPlanTests.swift` | two #138 tests | whole hunk |
| `ios/EngineTests/EngineClientTests.swift` | `EngineCookieTests` | whole hunk |
| `ios/EngineTests/test-manifest.txt` | three names | the manifest diff passes |
| `ios/ModelRanking/Engine/AnswerPlan.swift` | `sameRow` by id | whole function |
| `ios/ModelRanking/Engine/EngineClient.swift` | `init()`, cookies off | whole file; B1 |
| `ios/ModelRanking/Engine/Models.swift` | `Pick.modelId` | the struct, and `FetchedStandings` (B2) |
| `scripts/client_decl_fixtures/*.swift` (7) | the fixture mutants and allows | whole |
| `scripts/client_decl_gate.py` | sink, provenance, flow, URL rules, `unseen_permissions` | line by line; B1, B2, B3, M1, M4, M5, M6 |
| `src/app/adapter/main.py` | `model_id` in `PUBLIC_PICK_FIELDS` | hunk |
| `src/app/workflows/recommend.py` | `model_id` per pick, by row identity | `recommend()`, `_pick` |
| `tests/unit/data/g2_fixture_ast.txt` | the fixture's AST, trimmed, paths `/x/` | checked against the fixture (106 declarations) |
| `tests/unit/test_api_v1.py` | `PICK_KEYS`, the id test | hunk |
| `tests/unit/test_client_decl_gate.py` | 17 tests | whole hunk; run |
| `tests/unit/test_ios_client_contract.py` | `_swift` through every pin, the read lint | whole hunk; M3 |
| `tests/unit/test_recommend.py` | the shared-name test | hunk; E1 replayed |
| `tests/unit/test_router_hints.py` | `_decide`, `_built`, EGRESS, sink pins, eight tests | whole hunk; M2 |
| `tests/unit/test_uncertainty_contract.py` | `model_id="m"` | hunk |

One duplication smell, as in the first review: `pathlib.Path(line.split('"')[1]).name` now appears in
five walkers (`_shared_state`, `_sink_holds`, `_sink_calls`, `url_facts`, `_file_of`). Each of them
reads the 124 MB dump line by line again. `client-decls` took 58 to 61 s in each `make check-fast`
run here.

## K.8 contract drift check

The wave plan's contracts (`m19-wave-2-plan.md:44-57`), `grep -n` at `4e737ea`:
```
scripts/client_decl_gate.py:123:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:139:FILESYSTEM_FILES = {
scripts/client_decl_gate.py:315:FIXTURE_REFUSALS = {
scripts/client_decl_gate.py:425:def references(ast: str) -> dict[str, set[str]]:
scripts/client_decl_gate.py:1105:def problems(found: dict[str, set[str]]) -> list[str]:
ios/ModelRanking/Engine/EngineClient.swift:159:struct EngineClient {
ios/ModelRanking/Engine/EngineClient.swift:213:            let configuration = URLSessionConfiguration.ephemeral
ios/ModelRanking/Engine/EngineClient.swift:256:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/AnswerPlan.swift:174:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
tests/unit/test_router_hints.py:80:def _code(swift: str) -> str:
```
- Verdict: OK. Every symbol is present with its signature unchanged; only line numbers moved.
  `PUBLIC_PICK_FIELDS` gained `model_id` under D-182, written before the field was served
  (`m19-plan.md:156-157`). `EngineClient.init(baseURL:session:)` lost its default address, and
  `init()` took its place for the app. The tests' calls name both arguments, so none changed.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/data/g2_fixture_ast.txt` and `scripts/client_decl_fixtures/`. **The compiled
  fixture's AST is kept twice, and nothing compares the two copies where Xcode runs.** It matches
  today (measured). But a fixture edit that keeps line numbers and changes a shape would leave the
  lanes without Xcode testing the old AST. This is one fact in two places (K.5). Enhancement: in
  `self_test`, or in a test that runs when `xcrun` exists, compare the snapshot's declarations with a
  fresh dump.

## Risks queued to next M

- **R1** `scripts/client_decl_gate.py:790-810`, `:874-889`. **The bound carriers are keyed by the
  line their statement starts on, so a reformat can silence the flow.** N18, N19 and N21 differ from
  refused shapes only by a line break. A formatter that moves a closure's parameters to the next line
  would drop names from the flow, and the gate would say nothing, because no permission goes unseen.
  It would show as a refused fixture shape that passes after `swift-format`.
- **R2** **The arithmetic and construction rules are lists over the dump's printed shapes.** The first
  review found 17 survivors, and this one found more than 20. Each answer has grown the lists, and
  the records have claimed completeness each time. A third BLOCKING on the same finding stops the
  slice. The risk is real if the next seat finds a shape beside each fix. Narrowing the records (B3
  (b)) removes the risk; growing the lists does not.
- **R3** **Over-refusal grows with the flow** (M5). Each new carrier makes more sub-expressions look
  served. It shows as an author renaming or restructuring code to get past the gate, or widening a
  permission. Count the permission edits and the `FIXTURE_REFUSALS` edits that are not new rules.

## Mutants planted, and what caught each

Method: a Python harness read each file's bytes, wrote the mutant, ran the checks, then restored the
bytes in a `finally` and compared them. Every restore was byte-identical, and `git status --short` was
empty after each run. "Decl" is `client_decl_gate` (`dump_ast`, `references`, `problems`,
`unseen_permissions`) on the simulator Release configuration, or on all four ("4/4"). "Text" is the 13
pin files that read Swift (`test_router_hints`, `test_ios_client_contract`, `test_ios_platform_drift`,
`test_ios_payload_contract`, `test_swift_tests_offline`, `test_refinements`, `test_ios_visual_contract`,
`test_uitext_sentence_rows`, `test_security_surface`, `test_engine_address`, `test_tier_stubs_shared`,
`test_pareto_dominance`, `test_attribution_terms`), stopping at the first failure. "Make" is a full
`make check-fast`.

| Id | Where | Mutant | Decl | Text | Make |
|---|---|---|---|---|---|
| P2+P3 | EngineClient + ContentView | the M17 relay and standings, as first written | refused 4/4 | refused | — |
| A0–A13, O1 | ContentView | the first review's B1 set, one per line | each refused 4/4 | (stopped at A3) | — |
| A14 | Router | a second price arithmetic, through a local | refused 4/4 | — | — |
| U5 | Detail + ContentView | the first review's B2, `[String: T]` decode | refused 4/4 | passed | — |
| U3b | FrontDoor | `engineURL(from:)` + `EngineClient(baseURL:)` | refused 4/4 | passed | — |
| S3 | EngineClient + ContentView | `static let probeRelay = NSMutableString()` | refused 4/4 | passed | — |
| S2b | Detail + EngineClient + ContentView | a getter in Detail read by `fetch` | refused 4/4 | passed | — |
| F2 | EngineClient | both timeouts under `#if false` | — | refused | — |
| E1 | recommend.py | ids by display name | — | `test_recommend.py` refused; `test_api_v1.py` passed | — |
| **P3w** | Detail + ContentView | P3 through a protocol requirement (B1) | passed 4/4 | passed | **PASS** |
| **U8** | Detail + FrontDoor + ContentView | a witness-built client on `<engine>/<typed>` (B1) | passed 4/4 | passed | **PASS** |
| U8b | Detail + FrontDoor + ContentView | U8, any host, decoded in FrontDoor (B1) | passed 4/4 | passed | — |
| **U11** | Detail + ContentView | a URL through `Any`, a witness-built client, any host (B1, M6) | passed 4/4 | passed | **PASS** |
| U9 | FrontDoor | the app's client's `baseURL` rewritten through an unsafe pointer (B1) | passed 4/4 | passed | — |
| **S5** | Models + ContentView | the question appended in `FetchedStandings.init`'s body (B2) | passed 4/4 | passed | **PASS** |
| S5b | Models + ContentView | a custom `init(from:)` on `StandingModel` (B2) | passed 4/4 | passed | — |
| U10 | FrontDoor + ContentView | a standings store on a path made from the question (B2) | passed 4/4 | passed | — |
| **N1–N17** | Detail | 15 arithmetic shapes, planted at once (B3) | passed 4/4 | passed | **PASS** |
| N9 | Detail | `scoreAnchor.map { $0 - 100 }` | refused | — | — |
| N12 | Detail | a custom `+` taking a served `Int` | passed | refused (position tripwire) | — |
| N18–N21 | Detail | the next-line closure, `if let` and `for`; a tuple assignment (B3) | passed 4/4 | passed | — |
| N22 | Detail | `Decodable` conformance in an extension (B3) | passed 4/4 | passed | — |
| FP1 | Detail | `filter { ... }.count + 1` (M5) | **refused 4/4, wrongly** | passed | — |
| FP2 | Detail | the same count bound to `let n`, then `n + 1` (M5) | **refused, wrongly** | — | — |
| O2, O4 | Detail | `NSArray.sortedArray(comparator:)`, `sortedArray(using:)` (M4) | passed 4/4 | passed | — |
| O5 | Detail | `NSMutableArray.sort(using:)` | refused | refused | — |
| S4 | EngineClient + ContentView | `Thread.main.threadDictionary` relay (M1) | passed 4/4 | passed | — |
| T1–T4 | EngineClient (copies) | tuple `static var`, tuple file `var`, indented `var` under `#if DEBUG`, string-literal `#if false` (M2) | T1 and T3 refused where built (T2, T4 not compiled) | passed `_sink_pin_problems` | — |
| F3 | ContentView | `#if false`/`#endif` in block comments around a sort and `position + 1` (M3) | refused | passed (the pre-wave pins refused it) | — |

## Gates and probes run

- `make check-fast` on the clean tree: PASS in 61.0 s (lint, typecheck, records, test, client-decls,
  swift-test).
- `make check-fast` with a mutant planted: PASS with P3w, U8, U11, S5 and the N-set (five runs, about
  60 s each).
- The wave's new Python tests, by name: 45 passed (`test_client_decl_gate.py` whole, the M6 and #138
  tests, the contract read lint), and 19 passed (the new `test_router_hints.py` tests).
- The probes above: about 50 harness runs over the 29 rows of the table, and one run of
  `_sink_pin_problems` on six edited copies (M2). No installer was run and no launchd job was touched. No
  test reached the network. `gh issue view` read #60, #85, #107, #110, #132, #138, #144 and #168 to
  #171.
- Not run: `make ui-test`, because the guard stubs refuse `simctl` and `xcodebuild`.
