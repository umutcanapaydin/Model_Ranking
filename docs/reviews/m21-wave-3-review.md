---
record_type: review
id: m21-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 3 Code Review, round 2 (the phone's promises, held further: the answer to round 1)

**Reviewer:** Code-Reviewer subagent (fresh eyes; wrote none of the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: round 1
(`docs/reviews/m21-wave-3-review-round-1.md`) and plan §W3 (`docs/plans/m21-plan.md:53`) were read first,
then each commit with `git show`, then the register.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `6233993..7e8deaf`, the answer to round 1 (`826ab04`, `312eeac`, `08f21f0`, `39a1c86`,
`3b1fc8c`, `7e8deaf`); the wave as a whole is `972b55e..7e8deaf`.
**Risk tier:** HIGH (plan §3; `EngineClient.swift`, `StandingsStore.swift` and `ContentView.swift` are security globs)

## Verdict
BLOCKING

## Summary

The answer fixes every twin round 1 planted. Each is refused on the fixture, and I re-measured the controls
on the shipping client. The count of partial rows and open gaps now matches the register (eight partial,
seven open). The self-test runs `release_problems` in the Release configurations. The #219 and #220 pins
now fail on a planted re-ask and a non-lazy layout.

The verdict is BLOCKING because the records still claim a few properties the gate does not hold, and the
gaps naming the residue do not name these cases. Each is a one-token variant of a refused spelling that
compiles, passes `make client-decls` in all four configurations, and passes every test in the two text-pin
files (107 tests, none newly failing against a clean baseline). An honest gap that named these would not
block; a record stating the property as closed does.

All probing was done in a scratch mirror of the repository (tests, scripts and client copied; the worktree
never edited — `git status` is clean). The compiled gate was exercised by calling the module's own
`references`/`problems` on a `swiftc -dump-ast` of the mirrored client.

## Findings

### BLOCKING

- **B1** `scripts/client_decl_gate.py:662-669` (`_holds_an_object`), `:857-859` (`FOUNDATION_OBJECT`),
  `:820-823` (`FOUNDATION_SHARED`); records `docs/security-invariants.md:127` (INV-66) and `:188` (G-1),
  `docs/decisions.md:4039`. **A Foundation object held in a constant reaches a sink when the constant's
  type is widened.** `_holds_an_object` judges a constant's declared type by name (an `NS` class, a listed
  Foundation class, or an app class). The control `let box = NSMutableString()` read by a sink is refused;
  `let box: Any = NSMutableString()`, `: AnyObject`, `[NSMutableString]` and a one-field struct holding one
  all pass, in the sink's own file and in the code the sink runs (`FetchedStandings.init(payload:)`).
  Separately, `FOUNDATION_SHARED` lists `TimeZone.current` but not `Calendar.current`, which reads the same
  default zone and passes. INV-66 states "reads no constant holding a Foundation or app object" as held; G-1
  names only a `ManagedBuffer` header as residue.
  - **Failure scenario.** A later edit annotates the screen's shared box `: Any` or wraps it in a struct;
    the typed question relays into the boards request or the standings file with every gate green.
  - **Fix.** When a sink, or code it runs, reads another file's global/`static` `let`, refuse it unless the
    declared type is a value type built only from `SINK_HELD_TYPES`; add `Calendar` to `FOUNDATION_SHARED`;
    plant the variants in the fixture. Or reword INV-66, D-180's note and G-1 to "a constant whose declared
    type is a Foundation or app class", naming these as residue.

- **B2** `scripts/client_decl_gate.py:1668-1682` (`_request_source`), `:1638-1655` (`_request_call`);
  records `docs/security-invariants.md:125` (INV-64) and `:194` (G-11), `docs/decisions.md:4044-4046`, and
  #244's body ("a key-path write ... refused"). **The surface still takes the typed question through an
  indirect key-path write and through a request entry point that is not a call.** `_request_source` reads
  only an assignment/`inout` whose left side names `ContentView.task`; the direct `self[keyPath:
  \.task] = question` is refused, but binding the key path to a `let` first, or writing through a generic
  `root[keyPath:] = v` helper, passes both gates (the `@State` setter is nonmutating, so the write sticks).
  `_request_call` reads only a `call_expr`, so a `subscript` declared on `EngineClient` that forwards to
  `recommendation(task:budget:)` and is read as `client[probe: question].value` passes both gates. `task`'s
  initial value is also unchecked (only `budget`'s is), so seeding it from a `static var` the screen writes
  passes the compiled gate (the text pin at `test_router_hints.py:467` alone catches that one). G-11 names
  only the router's outcomes and `select(_:)`.
  - **Failure scenario.** A refactor that writes view state through a `(key path, value)` helper sets `task`
    from the question; the next request carries the typed text to `/v1/recommendations`, where the hosted
    engine logs it and echoes it in `unknown_task`.
  - **Fix.** Refuse any `keypath_expr` naming `ContentView.task` or its aliases; refuse a subscript on
    `EngineClient` and any `EngineClient` member read with arguments that is not a listed call; hold `task`'s
    initial value to a literal. Plant each, or name them in G-11 and #244.

- **B3** `scripts/client_decl_gate.py:232-245` (`BY_NAME`); records `docs/security-invariants.md:127` and
  `:188`, `docs/decisions.md:4040-4041`, `docs/prd.md:553` ("no file reaches a value, a class or a selector
  by name"). **K1 (#241) is matched by owner type, not by the by-name mechanism, so overrides and other
  entry points pass.** `BY_NAME` lists `NSObject`'s KVC members by prefix; `NSArray`/`NSDictionary`/`NSSet`
  override them, so `([x] as NSArray).value(forKey:)` / `.setValue(_:forKey:)` / `setValuesForKeys(_:)`
  resolve under the collection type and pass. Also unlisted: `Bundle.classNamed(_:)`, `Selector.init`,
  `responds(to:)`, and the target/selector APIs (`Timer`, `Thread(target:selector:object:)`,
  `NotificationCenter.addObserver(_:selector:…)`). A chain through `Bundle.classNamed` → an `NSArray` KVC
  box → `value(forKey: "URL")` builds a URL from typed text in a client file and passes both gates in all
  four configurations (I confirmed the mechanism compiles and runs offline on this Mac; I did not wire the
  send).
  - **Failure scenario.** An INV-62/INV-63 route: a URL built from the question outside the three files
    allowed to make one, invisible to `make client-decls`.
  - **Fix.** Refuse by argument label (`forKey`, `forKeyPath`, `forKeys`, `selector`, `aSelector`) rather
    than by owner type; add `Bundle.classNamed`, `Bundle.principalClass`, `Selector.init`. Plant the chain.
    Or reword the four records and reopen #241 naming these.

- **B4** `scripts/client_decl_gate.py:561-562` (`FREE_NUMERIC`), `:1158-1171` (`_counted`); records
  `docs/security-invariants.md:142` (INV-76) and `:189` (G-2), `docs/decisions.md:4131-4140`,
  `docs/prd.md:428`. **"A count of what a served number built" is followed only for the three listed
  builders, and a value-carrying count through text passes.** `Array(repeating:count:)`, a range's bound and
  `dropFirst(_:)` are followed; but `String(repeating:count:).count`, `Data(count:).count`,
  `Data(repeating:count:).count` and `repeatElement(_:count:).count` are not — a served number sizes the
  collection and its count is a function of it, yet each passes (text's length is explicitly skipped in
  `_counted`, and the free constructors are not treated as builders). G-2 names `abs`/`min`/`max`/
  `.magnitude`/`.rounded`/a table index as the residue, not these count-launders.
  - **Failure scenario.** A view computes a rank-like number from `Data(count: pick.position).count`; a
    second ordering value ships with every gate green while the PRD says only the listed shapes pass.
  - **Fix.** In `_counted`, follow a served number that sizes a `String`/`Data`/`repeatElement`
    construction (do not skip text when a count is taken of it); or name these builders in G-2.

### MINOR

- **M1** `scripts/client_decl_gate.py:1476-1480` (`closure`), `:1281-1290` (`_bound`). The closure-`$0`
  fix keys an anonymous parameter by its own closure range, which is correct, but the fallback for a *named*
  closure/`loop` parameter still uses a six-line look-back by name (`:1288-1289`). Round 1's M1 over-refusal
  is reduced, not removed: a named binding in one closure can still carry into an unrelated binding of the
  same name within five lines. Measured: harmless on the shipping client (no such pair), so MINOR.
  - **Fix.** Key named closure parameters by the closure's own range too, as `$0` now is.

- **M2** `docs/security-invariants.md:142` (INV-76 text). The row says the compiled rule follows a served
  number "through text, `Any` ... the parsers and boxes that carry one back", stating the box set as
  complete. `Any`-typed and `AnyObject`-typed *object* constants are the B1 hole, and plain `Any` number
  boxing is covered; the wording reads as a closed property while B1 shows a box it does not hold. Align the
  INV-76 and G-2 wording with whatever B1/B4 settle so the register does not overclaim.

## PASS (what looks good)

- **Round 1's twins are closed.** Each twin from round 1 B1/B2/B3/M1/M2/K1 is refused on the compiled
  fixture, and I re-ran the controls on the shipping client: `Thread.main.name`, `ProcessInfo.processName`,
  `OperationQueue.main.name`, `NSTimeZone.default`, the mutable-container constant and static, the `_task`
  storage, the `$task` binding, the helper-built outcome, the method-as-value, the parser/box arithmetic,
  the bitwise operators, the count-of-built shapes, `NSMutableArray(contentsOf:)`, `NSExpression`, `Mirror`
  and associated objects — all refused.
- **The author's own three (`08f21f0`/`39a1c86`).** The count-of-built laundering, `Mirror`, and associated
  objects are refused; `BY_NAME` carries its own message distinct from `FORBIDDEN`.
- **The allowed forms are not refused (false-positive check, measured on the fixture AST):** the three D-143
  functions on their own served facts, a served-rows count (`list.count`), `enumerated()` row numbers in
  for/closure/`$0` form, `positions.count`, `indices`, `Set`/`filter` counts, a key-path-mapped count, a
  closure's own `$0`, `abs`/`min`/`max`/`.magnitude`/`.rounded`/`.signum`/`.byteSwapped`, a `Date`/`Duration`
  carrier, a memberwise store, an optional map, and a ternary table — none refused.
- **B2's INV-64 controls.** `task = question` and `self[keyPath: \.task] = question` are refused by both
  gates; `apply`'s routed `outcome.categoryID` and `select(_:)`'s id are allowed.
- **The fixture and self-test.** Every rule in `FIXTURE_RULES` has a refused shape; `self_test` now adds
  `release_problems` and `FIXTURE_RELEASE_REFUSALS` for the two Release configurations. `make client-decls`
  PASS: 21 files in 4 configurations.
- **#219 and #220.** The tightened pins fail on a planted re-ask inside the `scenePhase` handler, a second
  handler that re-asks, and a `VStack` in place of `LazyVStack`; the shipping handler and layout pass.
- **G-10's issue.** Moved from #175 (fixed in the wave) to #243.
- **Records' count.** Eight partial rows, seven open gaps, matching the register's own count line and the
  per-row "Partial:" markers (INV-62/63/64/66/76 plus INV-6/82/88).
- **Test strength.** 23 faults planted in the mirror's gate and the text tripwire, each restored by bytes
  with sha256 checked equal. 20 were killed (sink Foundation list, holds-object, FOUNDATION_OBJECT narrowed,
  counted-off, offset rule, `REQUEST_ALIASES`, `_request_value`, `PROVENANCE_BY_TYPE`, source-shape widened,
  parser/box/operator drops, `CONTENTS_OF`, the Release self-test leg, the served-fact kind, served-cases,
  the text tripwire's enum derivation, and more). Three survived and each corresponds to a finding or a
  known residue: `shared_drop_new_members` and `swift_refused_empty` (the gate still refuses the plant by
  another rule); `module_rule_off` is a pre-existing coverage gap in the Swift-side pins, out of this wave's
  diff — queued as K1.
- **Swift and pytest.** `swift test` on `HeldReading`/`StandingsStore`/`EngineClient`: 20 passed, in a
  scratch copy of `ios/`. pytest on the five relevant files: 223 passed.

## Acceptance criteria evidence

- **REQ-GAP-001** (INV-64, INV-66, D-169): `tests/unit/test_client_decl_gate.py:644`
  (`test_every_route_172_names_into_a_sink_is_refused`), `:677`, `:687`, `:730`;
  `ios/EngineTests/StandingsStoreTests.swift` and `HeldReadingTests.swift` (20 Swift tests pass). The
  compiled half remains incomplete: B1 (INV-66), B2 (INV-64), B3.
- **REQ-APP-005** (INV-76): `test_client_decl_gate.py:623` (18 shapes), `:661`, `:668`, `:717`. Incomplete:
  B4, M1.
- **Producers of hardened invariant(s):**
  - **INV-64** — producers: `ContentView.load()` → `client.recommendation(task:budget:)`
    (`ContentView.swift:1051`); `task` written at `:28`, `:946` (`apply`), `:1025` (`select`); `budget` a
    literal `let` (`:89`). Citing tests: `test_client_decl_gate.py:551`, `:687`;
    `test_router_hints.py:467`. Gaps: B2, G-11.
  - **INV-66** — producers: `EngineClient.swift` (`recommendation`, `categories`, `boards`, `fetch`);
    `StandingsStore.swift` (`currentKept`, `save`); `FetchedStandings.init(payload:)` (`Models.swift:421`).
    Citing tests: `test_client_decl_gate.py:644`, `:677`. Gaps: B1, B3, G-1.
  - **INV-76** — producers: `Uncertainty.swift` (`scoreOutOf100`, `distanceOutOf100`, `anchoredFact`),
    `Combine.swift`, `priceInPages` in `Router.swift` and `Language.swift`. Citing tests:
    `test_client_decl_gate.py:623`, `:661`, `:668`, `:717`. Gaps: B4, M1, G-2.

## K.8 contract drift check

Plan §5: "No `/v1` field changes ... W3 and W4 change gates, not contracts."

```
$ git diff --stat 972b55e..7e8deaf -- src/ schemas/
(empty)
```

Verdict: OK. `src/` moved under W1/W2, which are already merged; the W3 round-2 commits touch no `src/` or
`schemas/`. `EngineError.refusalSentence` stays an internal Swift function, not a contract.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_router_hints.py` (the Swift-side text pins) — the `module_rule_off` mutant (the
  module allowlist disabled in the compiled gate) survived the pytest suite: nothing in the two text-pin
  files re-asserts the compiled module allowlist, and on CI's Linux lane the compiled gate skips (G-10/#243).
  A Linux-only PR that silenced the module allowlist would not be caught by the text pins alone. File for
  the closure security seat (D-172): add a text pin that the client imports only `CLIENT_IMPORTS`.

## Risks queued to next M

- **R1** **The list-versus-allowlist model (the recurring one).** B1 to B4 are each a twin of a listed
  refused spelling, exactly as rounds past predicted. #242 already proposes moving the sink and arithmetic
  rules to allowlists; the same should cover INV-64's surface sources (key paths, subscripts, initial
  values) and the by-name set (match by argument label, not owner type). What would show the risk is real:
  the next review plants a twin that passes. Until the rules are allowlists, each round will.
- **R2** **CI's lane (G-10/#243).** CI's Linux lane still skips the compiled gate, so only the owner's local
  `make check`/`check-fast` holds INV-62 to INV-76 on the compiled module; the text pins do not see these
  routes (and K1 shows one they miss). What would show it: a PR merged on CI green alone carrying a change
  the text pins cannot see.
