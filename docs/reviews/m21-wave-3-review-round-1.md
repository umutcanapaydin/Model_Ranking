---
record_type: review
id: m21-wave-3-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 3 Code Review (the phone's promises, held further: #223, #219, #220, #168 to #175, #188, #132, #85)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: the plan was read first, then the
code with `git show`, then the commit messages.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `972b55e..6882d89` (`origin/closure/m20..6882d89`), the wave's 23 commits `23573d8` to
`6882d89`; integration read at the merge `661426c` (W1 and W2 merged in)
**Risk tier:** HIGH (plan §3; `EngineClient.swift`, `StandingsStore.swift` and, since this wave, `ContentView.swift` are security globs)

## Verdict
BLOCKING

## Summary

The wave delivers what plan §2 W3 lists. Each route the earlier reviews named is refused on the fixture.
Twelve gate and wording mutants were each killed by the wave's tests, and each was restored byte for byte
(sha256 checked). `HeldReading` behaves as before. Every engine error code has both languages. The boards
screen is lazy, and only the device state is re-read in the foreground. `make client-decls` passes on the
merge commit, W2's `ModelFamilies.swift` included.

The verdict is BLOCKING for one reason. The wave's records say gap G-1 and gap G-2 are **closed**
(`docs/security-invariants.md:203`, `docs/decisions.md:4040` and `:4129`, `docs/prd.md:428`). They also add
a compiled-module claim to INV-64 (`docs/security-invariants.md:125`). One-line twins of the refused
spellings defeat all three claims.

I planted each twin in a scratch copy of the client. Each one compiles, `make client-decls` refuses nothing,
and every zero-argument test in `test_router_hints.py` and `test_ios_client_contract.py` passes on it. That
was checked against a baseline run on the unplanted copy. The plan says these gaps "narrow"; the records say
they are closed.

The fix is to refuse the cheap twins, or to keep G-1 and G-2 open with the twins named and filed. INV-64's
new compiled claim needs the same treatment.

## Findings

### BLOCKING

- **B1** `scripts/client_decl_gate.py:717-720` and `:773-785`; records at `docs/security-invariants.md:127`
  and `:203`, and `docs/decisions.md:4033-4040`. **G-1 is not closed: Foundation's shared state and another
  file's constants reach a sink unrefused.**
  - **Why the gate misses it.** `FOUNDATION_SHARED` names six members. `_SinkReach.variable` counts as
    mutable only an app-declared stored `var`, or a closure.
  - **Planted, each in `EngineClient.swift`.** The sink sends the value as a query item on the boards
    request, and `ContentView.swift` sets it from the question. The compiled gate refuses none of these:
    - `Thread.main.name`, a twin of the refused `Thread.main.threadDictionary` on the same object;
    - `ProcessInfo.processInfo.processName`;
    - `OperationQueue.main.name`;
    - `TimeZone.current.identifier`, set through `NSTimeZone.default`;
    - `let probeBox = NSMutableString()` declared in `ContentView.swift` and read by the sink. A twin of the
      fixture's refused `holds relay`, which is the same object held in the sink's own file.
    - `enum ProbeShelf { static let box = NSMutableDictionary() }`, the same shape as a static.
  - **Controls.** `threadDictionary` and an app `var` read by the sink are both refused.
  - **Failure scenario.** A later edit adds `URLQueryItem(name: "t", value: Thread.main.name ?? "")` to the
    boards request, and `submit()` sets `Thread.main.name = question`. INV-66 says nothing derived from the
    question reaches that request. Every gate stays green and the question leaves the phone.
  - **Fix.** Choose one:
    - Turn the sink rule into an allowlist, as UIKit's is. Name the Foundation symbols that the two sinks,
      and the code they run, may reference; everything else is refused by absence.
    - At minimum, refuse `Thread`, `ProcessInfo` (but `processInfo` reads the sinks need),
      `OperationQueue`, `NSTimeZone`/`TimeZone.current` and `Locale.current`-style mutable singletons in a
      sink. Also apply `SINK_HELD_TYPES` to what a sink *reads* from another file's global or `static`
      `let`, not only to what it holds.
  - **Either way.** Plant each twin in the fixture, or reopen G-1 with these routes named.

- **B2** `scripts/client_decl_gate.py:1446-1463` (`_request_call`), `:1466-1480` (`_request_source`) and
  `:279-282`; records at `docs/security-invariants.md:125`. **INV-64's new compiled claim has four twins
  that pass both gates.** The claim is that each argument names only its declared source and the surface
  is assigned only a routed outcome's id. Planted in `ContentView.swift`:
  - `_task.wrappedValue = question` in `submit()`. The wrapper's storage `ContentView._task` is not
    `ContentView.task`. The text pin's `task\s*=` (`tests/unit/test_router_hints.py:494`) does not match it.
  - `let bound = _task.projectedValue; bound.wrappedValue = question`. This is a binding, which is refused
    only when spelled `$task`.
  - `let outcome = RoutingOutcome.probeEcho(question); task = outcome.categoryID`. The helper is declared in
    `Engine/HeldReading.swift`. The rule reads only the top node's member name, so any `RoutingOutcome`
    passes. The text pin refuses only the literal `RoutingOutcome(` in the view.
  - `let ask = client.recommendation; ... try await ask(question, budget)`. `_request_call` reads only a
    direct call whose callee is a `dot_syntax_call_expr`.

  The control, `task = question`, is refused by both gates.
  - **Failure scenario.** The first twin is one token away from the refused line. The next `load()` sends
    the typed question as `task` to `/v1/recommendations`. It lands in the hosted engine's request log, and
    the engine echoes it back in its `unknown_task` message.
  - **Fix.**
    - Treat `ContentView._task` and anything reached through it as `ContentView.task`.
    - Refuse any reference to an `EngineClient` request method that is not the direct callee of a call.
    - Name the allowed sources as exact declarations (`ContentView.apply(_:typed:ticket:).outcome`,
      `ContentView.select(_:).id`). Put `RoutingOutcome.init` under `PROVENANCE`, limited to the router's
      files.
    - Plant the four twins in the fixture. Otherwise, write INV-64's compiled half as a gap.

- **B3** `scripts/client_decl_gate.py:466`, `:962`, `:965-967` and `:325-329`; records at
  `docs/decisions.md:4121-4129`, `docs/prd.md:428`, `docs/security-invariants.md:142` and `:203`. **G-2 is
  not closed: a served number through text, through `Any`, and by bitwise operators.** G-2's own words
  were "through `Any` or text".
  - **Planted in a new Engine file, compiler-checked and unrefused:**
    - `(text as NSString).integerValue + 1`, `NumberFormatter().number(from: text)` and
      `Scanner(string: text).scanInt()`, where `text = "\(s.position)"`;
    - `AnyHashable(s.position).base as? Int`, `s.position as AnyObject` and `NSNumber(value: s.position).intValue`;
    - a `JSONEncoder` → `Data` → `JSONDecoder` round trip;
    - `s.position ^ 1`, `~s.position` and `s.position & 0xFF`;
    - `NSNumber(value: n).doubleValue * 2` on a served fact's `JSONValue.number`.
  - **Controls refused:** `Int(text)`, `String(describing:)`, `[Any]`, a key path and `reduce(0) { $0 + $1 }`.
  - **One widening.** The three D-143 permissions are keyed on the generic kind `number`, so they now
    admit any served count. `scoreOutOf100(Double(answer.eligibleCount), …)` passes, and before this wave no
    `number` arithmetic was permitted anywhere.
  - **Failure scenario.** A view computes a "rank" from `(String(pick.score) as NSString).doubleValue * 2`.
    That is a second scoring implementation with every gate green, while the PRD row says G-2 is closed.
  - **Fix.**
    - Treat as carriers `AnyHashable`, `AnyObject`, `NSNumber`/`NSValue`, `NSString` and `Data`.
    - Count as parsers `NSString.*Value`, `NumberFormatter.number(from:)`, `Scanner.scan*`,
      `Decimal(string:)` and `JSONDecoder.decode`.
    - Add `&`, `|`, `^` and `~` (and their `=` forms) to `OPERATOR`.
    - Give `JSONValue.number` a kind of its own (`fact`) and permit only that kind in the three D-143
      functions.
  - **Or** reopen G-2 with these twins named.

### MINOR

- **M1** `scripts/client_decl_gate.py:1092-1095`, and how `_reach` treats `.count`. **Over-refusals remain.**
  - **The look-back window.** The six-line look-back added for `for`/`p in` on two lines keys a binding by
    name only. A served `$0` bound by one closure therefore taints an unrelated closure's `$0` up to five
    lines below.
    - Measured: `list.enumerated().map { $0.offset + 1 }` is refused one line below
      `list.map(\.position).map { $0 }`.
    - The identical line eight lines below passes, and it passes alone too.
  - **Counts and row numbers.** A count of a list of served numbers is still refused, and so is a row
    number over one:
    - `let positions = list.map(\.position); positions.count + 1`;
    - `[s.position].indices.count - 1`;
    - `list.map(\.position).enumerated().map { $0.offset + 1 }`.

    The D-181 note says a count of served things is no longer refused; only the closure spelling is fixed.
  - **Failure scenario.** A legitimate "N of M boards" or row-number change fails `make client-decls`. It
    fails, or not, depending on which lines sit above it.
  - **Fix.**
    - Key anonymous closure parameters by the closure's own range (line and column).
    - Apply the look-back only to `for_each_stmt` patterns.
    - Stop the operand walk at `count`, `indices`, `isEmpty` and `enumerated().offset` on a collection.
    - Add each of these as an `allowed:` line in `Arithmetic.swift`.

- **M2** `scripts/client_decl_gate.py:126-130`. **#168 has twins.** `NSMutableArray(contentsOf:)`,
  `NSMutableDictionary(contentsOf:)` and `NSMutableString(contentsOf:encoding:)` in `ContentView.swift` are
  not refused. The mutable subclasses declare their own initialisers, and `NETWORK` matches by class
  prefix. The control, `String(contentsOf:encoding:)`, is refused.
  - **Failure scenario.** The screen fetches `client.baseURL` from outside `EngineClient.swift` (INV-62).
    The impact is bounded: no file but the three can build a URL from text.
  - **Fix.** Refuse any Foundation initialiser labelled `contentsOf:` or `url:` that takes a `URL`, outside
    the network file. Keep `Data.init(contentsOf:)` for the two stores, and plant `NSMutableArray` in the
    fixture.

- **M3** `tests/unit/test_ios_client_contract.py:294-311` (`_served_numbers`). **The #169 text tripwire is
  narrower than the compiled list it claims to equal.** Measured on the shipping client, the compiled
  `served_fields` has four names the text derivation lacks: `whyFact`, `tradeOffFact`, `number` and
  `number(_:)`.
  - **Why.** The regexes read only `struct`/`class` declarations whose protocol list sits on the opening
    line, and fields at exactly four spaces. A decoded enum's payload, a field typed as one, a nested
    decoded type and an `extension X: Decodable` are all missed.
  - **Failure scenario.** On CI, where the compiled gate skips (G-10), arithmetic on a served fact is
    unwatched. Meanwhile the docstring says the two lists "cannot say different things".
  - **Fix.** Derive enum payloads and fields typed as them, as `_served_cases` does, and assert the
    equality on the snapshot. Or reword the docstring and INV-76 to say what the text half misses.

- **M4** Two of the wave's new tests hold less than they say.
  - **(a) The fixture misses five rules.** `scripts/client_decl_gate.py:431-449` and `:1736-1754` (#175 R3,
    G-10) claim the fixture carries "a refused shape for each of the gate's rules". It has none for the
    UIKit symbol allowlist, the CoreFoundation symbol allowlist, `URL.appending` outside its files, a
    second `@AppStorage`, or the Release-only UI-test hook. `self_test` never calls `release_problems`. A
    layout change that silences one of these passes the self-test.
  - **(b) The #220 test is loose.** `tests/unit/test_ios_client_contract.py:1955-1962` matches
    `.onChange(of: scenePhase).*?onDevice = …` with DOTALL. It passed a plant whose foreground handler also
    sets `question` and calls `ask()`. The #219 test (`:1946`) passes with `LazyVStack` anywhere in
    `CombinedDetail`.
  - **Failure scenario.** A foreground handler that re-sends what was typed, or a layout change that
    silences the pasteboard rule, stays green.
  - **Fix.**
    - Add one fixture shape per missing rule: `UIPasteboard`, `CFSocketCreate`, `URL.appending` in
      `Detail.swift`, a second `@AppStorage`, and `ProcessInfo.processInfo.arguments` judged by
      `release_problems` in the Release configurations. Give each a `FIXTURE_RULES` entry.
    - Capture the `onChange` closure body and assert it is the one assignment.
    - Assert that the entries' `ForEach` is a direct child of the `LazyVStack`.

- **M5** Records.
  - **(a) G-10's rows.** `docs/security-invariants.md:191` names INV-62, 63, 64, 66 and 76. None of those
    rows says "Partial: gap G-10", and `:177` counts three partial rows. Either the rows are partial or G-10
    is not a gap of theirs.
  - **(b) G-10's issue.** G-10 cites #175, which this wave fixes. Under the close-on-merge rule, #175
    closes and the open gap then points at a closed issue. Give G-10 an issue of its own.
  - **(c) REQ-GAP-001.** `docs/prd.md:553` still says "Routes no rule names are gap G-1 (#172); the date the
    standings file keeps comes from its caller (#170)", then appends "Since M21-W3 … held too". The row
    contradicts itself; rewrite it in place, since PRD rows are live documents.
  - **(d) REQ-APP-005.** `docs/prd.md:428` carries two evidence parentheses back to back.
  - **Failure scenario.** The closure security seat starts from this register (its own header) and counts
    the wrong partial rows and open gaps.
  - **Fix.** Edit these four places. Make the closure paragraph (`:203`) and the D-180 and D-181 notes match
    whatever B1 to B3 settle.

### PASS (what looks good)

- **HeldReading (#132).** It is equivalent to the code it replaced. `holding` is nil exactly for `.search`;
  `confirmed`, `declined` and `asksBack` are the old three lines each (`ios/ModelRanking/Engine/HeldReading.swift:16-35`;
  `ContentView.swift:929`, `:969`, `:979`, `:987`).
  - Four mutants in a scratch copy were all killed by `HeldReadingTests.swift:16-42`. They were: unsure
    answered, `asksBack` widened, declined left unsure, and confirmed left unsure.
  - D-169's `ReadingTests.swift:343` still passes, and the wiring pins at
    `test_ios_client_contract.py:895` were updated to the new names.
- **#223 error sentences.**
  - The six codes the engine sends (`src/app/adapter/main.py:838`, `:854`, `:880`, `:1590`, `:1636`,
    `:1642`) each have English and Turkish in `Language.swift:827-849`, `rate_limited` included.
  - `test_error_codes.py:30` and `:36` hold the set equal in both directions. Removing the `rate_limited`
    case is killed.
  - `EngineClient` stays a sink: its only change, `EngineClient.swift:106`, interpolates its own case
    values and calls nothing. `make client-decls` passes. The Turkish sentences say what the English ones
    say.
- **#219.** The entries' `ForEach` is a direct child of the `LazyVStack` (`ContentView.swift:1555`), so the
  rows are laid out lazily.
- **#220.** The `scenePhase` handler assigns `onDevice` and nothing else (`ContentView.swift:150-152`).
  Nothing typed is read again.
- **#170.** `currentKept(fetch:)` dates by the store's own clock (`StandingsStore.swift:86-88`), and
  `PROVENANCE` (`client_decl_gate.py:255-260`) refuses the dated forms elsewhere. Its test is at
  `StandingsStoreTests.swift:216`.
- **G-10.** On Darwin with no toolchain the gate prints a FAIL line naming #175 and exits 1; elsewhere it
  prints SKIPPED and exits 0 (`client_decl_gate.py:1774-1783`).
  - CI runs it on ubuntu (`.github/workflows/ci.yml:71`), so it still skips there. `check-fast` runs it as
    its own leg (`stack.mk:7`).
  - On this Mac, `make client-decls` printed PASS for 21 files in 4 configurations in 47 s.
  - A nit: the message says "no Xcode toolchain (xcrun)" even when `xcrun` exists and only the iOS SDK
    lookup failed, for example when `xcode-select` points at the Command Line Tools.
- **Test strength on the named routes.** Twelve mutants were run, each restored by bytes with its sha256
  checked, and all twelve were killed:
  - two dropping `FOUNDATION_SHARED` members;
  - the static initialiser no longer followed;
  - text not parsed;
  - `Any` not text;
  - served-fact cases dropped;
  - the Mac skipping;
  - the self-test on one configuration;
  - request sources matching any name;
  - shifts dropped;
  - closures read in operands;
  - `rate_limited` removed.
- **Merge with W1 and W2.** `make client-decls` passes on `661426c`. W2's `ModelFamilies.swift` is a
  `static let` of `Set<String>` that no sink reads. `test_error_codes.py` passes after W1's merge.
- **Runs.**
  - pytest on `test_client_decl_gate.py`, `test_error_codes.py`, `test_ios_client_contract.py`,
    `test_security_invariants.py` and `test_router_hints.py`: 196 passed.
  - Swift, in a scratch copy of `ios/`: 604 of the manifest's 605 pass. The one left,
    `ReadingTests::testNoGenuineTuningQuestionTripsASignal`, reads a held-out file this seat may not read.

## Acceptance criteria evidence

- **REQ-GAP-001** (INV-64, INV-66, D-169):
  - `tests/unit/test_client_decl_gate.py:637` (`test_every_route_172_names_into_a_sink_is_refused`), `:551`
    and `:561`;
  - `ios/EngineTests/StandingsStoreTests.swift:216`;
  - `ios/EngineTests/HeldReadingTests.swift:16-42`;
  - `ios/EngineTests/ReadingTests.swift:343`.

  The compiled half is incomplete (B1, B2).
- **REQ-APP-005** (INV-76): `tests/unit/test_client_decl_gate.py:616` (18 shapes), `:624` and `:631`, and
  `tests/unit/test_ios_client_contract.py:1965`. Incomplete (B3, M1, M3).
- **The plan's issues:**
  - #168: `FIXTURE_REFUSALS` at `client_decl_gate.py:425-426`.
  - #169: `test_ios_client_contract.py:1965`.
  - #170: `client_decl_gate.py:255-260` and `StandingsStoreTests.swift:216`.
  - #171 and #173: `test_client_decl_gate.py:616-635`.
  - #172: `test_client_decl_gate.py:637`.
  - #174 and #188: `test_client_decl_gate.py:551` and `:561`.
  - #175: `test_client_decl_gate.py:568`, `:579` and `:593`.
  - #132: `HeldReadingTests.swift`.
  - #223: `test_error_codes.py:30` and `:36`, and `LanguageTests.swift:550` and `:563`.
  - #219 and #220: `test_ios_client_contract.py:1946` and `:1955`.
  - #85: through #172.

## Producers of the hardened invariants

- **INV-64.**
  - Producers: `ContentView.load()` → `client.recommendation(task:budget:)` (`ContentView.swift:1051`);
    `task` written at `:28` (literal), `:946` (`apply`) and `:1025` (`select`); `budget` at `:89`.
  - Citing tests: `test_client_decl_gate.py:551` and `:561`; `test_router_hints.py:467`.
  - Gaps: B2.
- **INV-66.**
  - Producers: `EngineClient.swift` (`recommendation`, `categories`, `boards`, `fetch`);
    `StandingsStore.swift` (`currentKept(fetch:)` at `:86`, `save` at `:66`); the caller
    `ContentView.refreshStandings` (`ContentView.swift:1074`).
  - Citing tests: `test_client_decl_gate.py:637`; `StandingsStoreTests.swift:216`.
  - Gaps: B1 and K1.
- **INV-76.**
  - Producers: `Uncertainty.swift` (`scoreOutOf100` at `:184`, `distanceOutOf100` at `:356`, `anchoredFact`
    at `:372`); `Combine.swift`; `priceInPages` in `Router.swift` and `Language.swift`.
  - Citing tests: `test_client_decl_gate.py:616`, `:624` and `:631`; `test_ios_client_contract.py:1965`.
  - Gaps: B3, M1 and M3.
- **INV-62 and INV-63 (#168).**
  - Producers: any client file.
  - Citing test: `test_client_decl_gate.py::test_the_gate_refuses_its_compiled_fixture`.
  - Gaps: M2 and K1.
- **D-169 (INV-68).**
  - Producers: `HeldReading.holding`, `confirmed`, `declined` and `asksBack` (`HeldReading.swift:16-35`).
  - Citing tests: `HeldReadingTests.swift:16-42`; `test_ios_client_contract.py:895`.
  - Gaps: none.

## K.8 contract drift check

Plan §5 says "No `/v1` field changes … W3 and W4 change gates, not contracts."

```
$ git diff --stat origin/closure/m20..6882d89 -- src/ schemas/
(empty)
```

Verdict: OK. `EngineError.refusalSentence(_:_:)` is a new internal Swift function, not a contract.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py:79-92`. Foundation is allowlisted whole, and `NSExpression` invokes
  any class and selector by name. That bypasses every declaration rule and the text gate.
  - **Measured on this Mac, with no network.**
    `NSExpression(format: "FUNCTION(CAST(%@, 'Class'), %@, %@)", "NS"+"UR"+"L", "UR"+"LWithString:", "ht"+"tps://…?q="+typed).expressionValue(with: nil, context: nil)`
    returns an `NSURL` built from the typed text.
  - **Planted in `ContentView.swift`.** `make client-decls` refuses nothing, and the text gate's egress
    check (`test_the_gap_register_stays_on_the_device`) passes. The same mechanism reaches
    `NSURLSession.sharedSession`, so it is an INV-62 and INV-63 route. The client uses neither
    `NSExpression` nor `NSPredicate` (none in the compiled tree), so refusing them costs nothing.
  - **A security bug.** File it for the closure security seat (D-172). Fix: add `NSExpression`,
    `NSPredicate`, and KVC and `perform` on `NSObject` to `FORBIDDEN`, with a fixture shape.

## Risks queued to next M

- **R1** **The model behind the twins.** The compiled sink and arithmetic rules are lists of what is
  refused: member names, operators, parsers and boxes. Each review so far has found twins of the listed
  spellings (B1 to B3 here). What would show the risk is real: the next review plants a twin that passes.
  An allowlist would end the cycle: what a sink may reference, and what a served number may meet
  (comparison and display).
- **R2** **CI's lane (G-10).** CI's Linux lane still skips the compiled gate, so only the owner's local
  `make check` or `check-fast` holds INV-62 to INV-76 on the compiled module. What would show the risk is
  real: a PR merged with only CI's green, carrying a change the text pins cannot see.
