---
record_type: review
id: m19-wave-2-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# M19-W2 Code Review (third seat): the phone's promises, held by what the code does

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records,
and none of the fixes made after either earlier review.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `1843437950dda095bcb4bb6e5ac63c001b9d21bb..c327192` (the whole wave; 36 commits).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:62-64`; `docs/plans/m19-wave-2-plan.md:13-15`). The diff
touches `EngineClient.swift` and `src/app/adapter/main.py`, both security globs
(`docs/plans/m19-plan.md:123-132`). By D-172 no security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I read the profile and `.agents/rules/practices.md` from `origin/main` (including
the "three attempts, then stop" rule), then the milestone plan (§1 W2, §2 W2, §3, §5 and the three
W2 amendments), the wave plan, D-180 to D-182, the invariants diff, and the two earlier verdicts. I
read the diff before the commit messages. I then re-planted each earlier finding's own mutant on the
shipping client, and looked for routes neither review named.

**Summary.** This is the third review of a wave that was BLOCKED twice. The first two reviews each
found the records claiming more than the code held (arithmetic "however the value is named"; a client
or standings "built by any route the compiler accepts"). After each, the author either closed the
route by rule or narrowed the record and filed the remainder as an issue. As the wave now stands:

- Every blocking mutant of both earlier reviews is **refused on the shipping client**, and I planted
  each again: the M17 relays (P2, P3), the first review's B1/B2 set (A0–A14, O1, U5, U3b, S3, S2b),
  and the second review's B1/B2 set — **P3w, U8, U11 (cast out of `Any`), U9 (unsafe memory), S5
  (the question appended inside `FetchedStandings.init`'s body), U10 (a store on a path made from the
  question)** — each refused (simulator Release; the structural ones re-run across all four
  configurations).
- The records are now **scoped to what the gate holds**. D-181 clause 3 and G-2 openly list the
  arithmetic shapes the gate does *not* see (prefix `-`, shifts, an operator passed as a value,
  `pow`, other numeric methods, a subscript, an enum payload, `self` on a numeric type, a
  next-line binding, a conformance in an extension, `Any`/text). I planted that gap set (`N_set`,
  `GL_let_init`, Foundation's `Thread.threadDictionary` = S4); each passes, matching the record. So
  the records neither over- nor under-claim on the routes they enumerate.
- D-182 (#138) is additive and keyed by object identity on the engine side; the app keys cards on the
  id with a four-value fallback for an older engine.
- `make check-fast` PASS on the clean tree (all six legs). K.8 contracts intact. No drive-bys. Every
  changed file serves a wave issue or is a record. Red-before-green held for every slice (test→fix
  commit pairs).

I found **no route past a rule the records claim to hold.** The arithmetic/construction findings that
were blocked twice are not re-raised: they are now honestly scoped and their remainders filed
(#171, #172, #173) — re-blocking the same two findings would be the third attempt the practices file
stops, and there is nothing left to block because the overclaim is gone. Two MINOR record items and
a risk neither earlier seat named remain.

## Verdict

MINOR

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `docs/prd.md:427` (REQ-APP-005) vs `docs/decisions.md` D-181 clause 2. **The PRD's
  parenthetical list of the names the gate follows is shorter than D-181's, for the same rule.** The
  PRD says "the names clause 2 lists (a binding, an assignment, a result, a parameter, a loop, a
  condition, a case, `inout`, a protocol requirement)". D-181 clause 2 and the gate also follow **a
  closure handed each element** (`_Flow.closure`, `client_decl_gate.py:1036`), **a function used as a
  value** (`_Flow.carried`, `:900-901`) and **a memberwise initialiser's stored property**
  (`_Flow.call`, `:1003-1004`). I confirmed all three are enforced: `[Standing].map(\.position).map
  { $0 - 1 }`, `let f = probeServed; f(p) + 1`, and `ProbeMW(v: s.position).v * 2` are each refused
  on the shipping client. One rule written two ways drifts (K.5, the practices file's top finding).
  Fix: align the PRD list or point it at D-181 without an abridged copy. (Under-statement, not an
  overclaim, so MINOR.)

- **M2** `scripts/client_decl_gate.py:807` (`_numeric`), `:421` (`NUMERIC_TYPE`), `:1095-1111`
  (`_arithmetic` → `carried` on the whole operand). **A collection of served numbers is a served
  carrier, so count/length arithmetic over it is refused for the wrong reason.** `NUMERIC_TYPE`
  matches `Double`/`Int` inside `[Double]`/`[Int]`, so `let scores = picks.map(\.score)` is marked a
  "score" carrier; `scores.count + 1` is then refused as "`+` on a served score" — but the `+` is on
  a count of rows, not a score. I confirmed this on the shipping client. D-181 "What it does not do"
  already admits over-refusal on counts, but names only the shape where "a served field appears
  anywhere inside the operand" (`answers.filter { … }.count + 1`); this is a different shape (a
  served-typed *carrier*, no field in the operand) and the message misattributes it. Fold this shape
  into #173 / D-181's admission, or stop a collection type being a numeric carrier in `_numeric`.
  (Over-refusal pressure, the second review's R3; MINOR because it refuses too much, never too
  little.)

### PASS (what looks good)

- **Both earlier reviews' mutants are dead on the shipping client.** `_kept_types`
  (`client_decl_gate.py:584-610`) closes the protocol-requirement route for *both* kept types
  (P3w/U8/U11 refused as "conforms to … a protocol the app declares" and "extends … outside its own
  file"); `UNSAFE` (`:256-257`, enforced at `:1252-1254`) closes U9; `_SinkReach`
  (`:622-707`) closes S5/S5b by following the bodies a sink runs and the coding witnesses; the new
  `PROVENANCE` entries for `StandingsStore.init(url:)` and `.save(_:at:)` (`:241-246`) close U10.
- **The arithmetic and sort rules are honestly bounded.** The listed operators/methods/names are
  caught (A0–A14, O1, NSArray `sortedArray` all refused); the unlisted shapes pass and are each named
  in D-181 clause 3 and G-2 with a filed issue. `unseen_permissions` (`:1152-1170`) answers the first
  review's R3: a permission, listed sink call or `NOT_SERVED` type the shipping client no longer shows
  fails the gate.
- **The no-cookie door is exact.** `FORBIDDEN_EXCEPT` (`:314-316`) allows one symbol in one file;
  `EngineClientTests.swift:841` reads the shipped session through `Mirror`.
- **D-182 is safe and additive.** Picks are keyed to ids by object identity
  (`recommend.py:503-504`, `ids = {id(row): model_id …}`), not by display name; `test_recommend.py:661`
  refuses a name-keyed lookup; the app falls back to the four-value rule for an engine with no id
  (`AnswerPlan.swift:186-194`).
- **The pins now read only built code in both lanes.** `_swift` runs `_built_mask(_stripped(raw))`
  (`test_ios_client_contract.py:34-39`), so a directive hidden in a block comment or a string is no
  longer read as a branch (the second review's M3, closed).
- **The valve was used and recorded** (#132 left W2, `m19-plan.md:198-200`), and the committed AST
  snapshot is checked against the fixture as it compiles (`_snapshot_drift`, `:1321-1330`).
- **Gates green on the clean tree:** `make check-fast` PASS in 99 s (lint, typecheck, records,
  test, swift-test, client-decls); `client-decls` clean in all four configurations (2474/2479/2474/2479
  declarations). Git tree clean before and after every probe.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code; citing test per producer; gaps (tracked).

- **INV-66 — nothing from the question reaches the boards request or the standings file.**
  - `EngineClient.boards()` → `fetch("v1/boards", query: [])` (`EngineClient.swift:256-265`):
    `EngineClientTests.swift:489` (`testTheBoardsRequestCarriesNothing`);
    `test_router_hints.py:911` (`_sink_pin_problems`), run by `:942`.
  - `EngineClient.init(baseURL:session:)` (`EngineClient.swift:208`), the request's destination,
    `PROVENANCE`: `test_client_decl_gate.py:291`. Protocol-requirement and unsafe-memory routes
    closed by `_kept_types`/`UNSAFE`: `:406`, `:422`. (Replayed U8, U11, U9 — refused 4/4.)
  - `FetchedStandings.init(payload:)` (`Models.swift:412`), `PROVENANCE` + its reachable body +
    witnesses (`_SinkReach`): `test_client_decl_gate.py:166`, `:440`. (Replayed P3w, S5 — refused.)
  - `StandingsStore.init(url:)` / `.save(_:at:)` (`StandingsStore.swift:34`, `:66`), `PROVENANCE`:
    `test_client_decl_gate.py:414`. (Replayed U10 — refused.)
  - A sink's held state, its reads of another file's state, its calls out of file: `_sink_holds`,
    `_shared_state`, `_sink_calls`: `test_client_decl_gate.py:155`, `:383`, `:393`.
  - **Gaps (G-1, #172):** Foundation-held state (`Thread.threadDictionary`, confirmed S4 passes), a
    stored property's default, a global/`static` `let`'s initialiser, a closure kept in a value; and
    no proof that no other route exists. The standings file's date comes from its caller (#170).
- **INV-63 — a URL made from text is the network outside the door.** `NETWORK` + `DECODES_URL` +
  `url_facts` (`MAKES_URL`, now any call whose result *type names* `URL`, and `CASTS_URL` for a cast
  out of `Any`) + `NSDataDetector`: `test_client_decl_gate.py:242`, `:252`, `:304`, `:428`. (Replayed
  a bare `as? URL` cast — refused.) **Gap:** `contentsOf:` readers (#168, filed).
- **INV-76 — no arithmetic on a served number; the client orders nothing.** `served_fields`
  (`:770-789`) + `_Flow` (`:866-1060`) + `_arithmetic` (`OPERATOR`/`NUMERIC_METHOD`, `:1095`) +
  `_ordering` (`ORDERING_CALL` incl. `sortedArray`, `:1114`): `test_client_decl_gate.py:359`, `:369`,
  `:376`, `:450`, `:209`. (Replayed NP1–NP7, C_closure/fnvalue/memberwise, NSArray sort — refused;
  N_set gaps pass.) **Gaps (G-2, #171/#173):** prefix `-`, shifts, an operator as a value, `pow`,
  other numeric methods, `self`/enum payload/subscript, a next-line binding, a conformance in an
  extension, `Any`/text. Over-refusal: counts (M5/#173) and a collection carrier's `.count` (M2).
- **INV-85 — no cookie kept or sent.** `EngineClient.swift:220-222`: `EngineClientTests.swift:841`;
  `test_client_decl_gate.py:259`. The app builds `EngineClient()` (`ContentView.swift:85`); only tests
  inject a session, and the injecting initialiser is `PROVENANCE`-kept to its file. No gap found.
- **INV-78 — the pins read built code.** `_code`/`_built` (`test_router_hints.py:80`, `:186`) and
  `_swift` via `_built_mask(_stripped(…))` (`test_ios_client_contract.py:34`): `:980`, `:1042`;
  `test_ios_client_contract.py::test_every_swift_pin_here_reads_the_code_the_compiler_builds`,
  `::test_a_directive_inside_a_comment_hides_nothing`. No gap found now.
- **INV-62** — unchanged confinement; new pin citation holds. **INV-67** — its standings-file half now
  cites `test_client_decl_gate.py:166` (D-180).

Gaps, tracked: M2 (over-refusal → #173); declared G-1 (#172), G-2 (#171, #173); #168, #170 filed.

## Acceptance criteria evidence (REQUIRED)

- **REQ-GAP-001 / the W2 privacy criterion** ("nothing derived from the question reaches a request or
  the standings file"):
  - Code: `client_decl_gate.py:221-271` (`SINK_FILES`, `PROVENANCE`, `SINK_HELD_TYPES`,
    `SINK_CALLS_PERMITTED`, `KEPT_TYPES`, `UNSAFE`), `:449-725`; `EngineClient.swift:200-225`.
  - Tests: `test_client_decl_gate.py:155`, `:166`, `:291`, `:383`, `:393`, `:406`, `:414`, `:422`,
    `:440`; `test_router_hints.py:942`, `:946` (text half). Each cites REQ-GAP-001.
  - **Met for every planted route** (P2, P3, P3w, U8, U10, U11, U9, S5 — replayed, refused). **Not met
    "by any route the compiler accepts"**: recorded as such (`m19-plan.md:204-222`), G-1 open (#172).
- **REQ-APP-005 / the W2 arithmetic criterion** ("however the value is named"):
  - Code: `client_decl_gate.py:273-310`, `:770-1149`.
  - Tests: `test_client_decl_gate.py:359`, `:369`, `:376`, `:450`, `:209`; the fixture refusals.
  - **Met for the listed operators/methods/names** (A0–A14, O1, NSArray, NP1–NP7 — refused). **Not met
    "however the value is named"**: recorded (`m19-plan.md:219-222`), G-2 open (#171, #173). M2.
- **REQ-API-001 / "the engine's sameness rule reaches the phone"** (D-182):
  - Code: `main.py:956` (`model_id` in `PUBLIC_PICK_FIELDS`); `recommend.py:189-191`, `:500-504`,
    `:560`, `:575`, `:594`; `Models.swift:234`, `:255`; `AnswerPlan.swift:174-194`.
  - Tests: `test_api_v1.py:779`; `test_recommend.py:661`; `AnswerPlanTests.swift:355`. Each cites a
    REQ-ID. **Met.**
- **#144:** `EngineClient.swift:220-222`; `EngineClientTests.swift:841`; `test_client_decl_gate.py:259`.
  Met. **#132:** left by the valve (`m19-plan.md:198-200`).

## K.8 contract drift check

The wave plan's contracts (`m19-wave-2-plan.md:44-57`), `grep -n` at `c327192`:
```
scripts/client_decl_gate.py:125:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:141:FILESYSTEM_FILES = {
scripts/client_decl_gate.py:338:FIXTURE_REFUSALS = {
scripts/client_decl_gate.py:456:def references(ast: str) -> dict[str, set[str]]:
scripts/client_decl_gate.py:1290:def problems(found: dict[str, set[str]]) -> list[str]:
ios/ModelRanking/Engine/EngineClient.swift:159:struct EngineClient {
ios/ModelRanking/Engine/EngineClient.swift:213:            let configuration = URLSessionConfiguration.ephemeral
ios/ModelRanking/Engine/EngineClient.swift:256:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/AnswerPlan.swift:174:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
tests/unit/test_router_hints.py:80:def _code(swift: str) -> str:
```
- Verdict: OK. Every symbol present with its signature unchanged; only line numbers moved.
  `PUBLIC_PICK_FIELDS` gained `model_id` under D-182, written before the field was served
  (`m19-plan.md:156-157`). `EngineClient.init(baseURL:session:)` lost its default address and `init()`
  took the app's slot; the tests name both arguments, so no call changed.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py:42` (docstring), INV-64. **The compiled gate reads no arguments,
  so `EngineClient.recommendation(task:budget:)` can carry the typed question as `task` with the
  compiled gate silent.** This is held today by the text gate
  (`test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine`) and the Swift tests
  (INV-64), which is why it is outside W2 (W2 hardened INV-66, the boards request). But it is the same
  "hold by data, not spelling" argument this wave made for INV-66, left un-made for INV-64: a future
  seat could extend the flow to a request argument. Enhancement, not a bug.

## Risks queued to next M

- **R1** `scripts/client_decl_gate.py:1376-1378`. **`make client-decls` exits 0 ("SKIPPED
  NO-ENVIRONMENT") on any host without Xcode**, and the text pins alone cannot see the AST-only routes
  this wave exists to close. So the strong INV-62/63/66/76 guarantees hold only where the gate runs on
  an Xcode host. The docstring acknowledges "this one runs where the toolchain is", but no record pins
  the authoritative gate host, and a push validated only where `xcrun` is absent gets the weaker lane
  (practices: "Configured != working" / "one authoritative gate host"). It would show as a regression
  that merges green off-host and only fails on the owner's Mac. Neither earlier review named this.
- **R2** `recommend.py:503-504`. **Picks map to ids by object identity** (`ids[id(row)]`). A future
  refactor that copies a `RankingRow` between `ranked_with_ids` and the picks raises `KeyError` at
  serving time, not at build time. Covered by tests today; fragile by construction.
- **R3** The sink/flow/URL rules parse `swiftc -dump-ast`'s printed layout. `unseen_permissions`
  guards a permitted rule going quiet, but a layout change could still silence a refusal on an
  unlisted shape with no permission going unseen; `self_test` exercises only the fixture's shapes in
  one configuration (the second review's R1/R2, still open).

## Mutants planted, and what caught each

Method: a Python harness read each file's bytes, wrote the mutant, ran the gate (and the text pins
where marked), restored the bytes in a `finally`, and compared them. Every restore was byte-identical
and `git status --short` held only this verdict after each run. "Decl" is `client_decl_gate` on the
simulator Release configuration, or all four ("4/4") where marked.

| Id | Where | Mutant | Decl |
|---|---|---|---|
| P3w | Detail + ContentView | standings built via a protocol requirement (2nd review B1) | refused |
| U8 | Detail + FrontDoor + ContentView | a witness-built client on `<engine>/<typed>` (2nd review B1) | refused |
| U11_cast | Detail + ContentView | a URL through `Any` by a cast, a witness-built client (2nd review B1/M6) | refused |
| U9_unsafe | FrontDoor + ContentView | `withUnsafeMutablePointer` in the client (2nd review B1) | refused |
| S5 | Models + ContentView | the question appended inside `FetchedStandings.init`'s body (2nd review B2) | refused |
| U10 | FrontDoor + ContentView | a store on a path made from the question (2nd review B2) | refused |
| CAST_url | Detail | a bare `any as? URL` in a non-sink file (INV-63) | refused |
| N_set | Detail | prefix `-`, `<<`, `reduce(0,+)`, `truncatingRemainder`, a subscript (G-2 gaps) | passed (declared) |
| GL_let_init / S4 | Detail / EngineClient + ContentView | a `let`-init helper; `Thread.threadDictionary` relay (G-1/G-2 gaps) | passed (declared) |
| NP1 | Detail | served position into a memberwise property, read back, `+ 1` | refused |
| NP2 | Detail | served position as a dict value, `+ 1` | refused |
| NP4 | Detail | served position through a returned tuple, destructured, `+ 1` | refused |
| NP5 | Detail | `xs.map(\.position).first ?? 0 + 1` | refused |
| NP6 | Detail | `(picks.map(\.score) as NSArray).sortedArray(comparator:)` (clause 4) | refused |
| NP7 | Detail | served position through a computed property's result, `+ 1` | refused |
| C_closure | Detail | served through a closure handed each element, `$0 - 1` (M1) | refused |
| C_fnvalue | Detail | served-returning function held as a value, then called, `+ 1` (M1) | refused |
| C_memberwise | Detail | served into a memberwise initialiser's stored property, `* 2` (M1) | refused |
| OVR_count | Detail | `picks.map(\.score).count + 1` — refused *as a served score* (M2) | refused (wrong reason) |

## Gates and probes run

- `make check-fast` on the clean tree: PASS in 99 s (all six legs).
- `client_decl_gate.py` on the clean tree: PASS, 19 files in 4 configurations.
- `test_client_decl_gate.py`, `test_router_hints.py`, `test_ios_client_contract.py`, the #138
  `test_api_v1.py` test and `test_recommend.py`: 164 passed.
- ~20 harness runs over the rows above (the structural privacy mutants re-run across all four
  configurations). No installer was run, no launchd job touched, no test reached the network.
- Not run: `make ui-test` (the guard stubs refuse `simctl` and `xcodebuild`).
