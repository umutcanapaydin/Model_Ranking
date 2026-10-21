---
record_type: review
id: enhancement-issue-242-allowlists-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-21
---
# Security Review — enhancement #242, the client-decls compiled gate's allowlists (branch `enhancement/issue-242-allowlists`)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), the seat D-214 clause 1 requires
**Independent:** yes. I wrote none of this change's code, fixture, pin file, tests or register rows.
**Seat and method:** a fresh seat with its own `git worktree` detached at `2a75cae` in this seat's scratch directory and
its own venv (`make install`), per D-174. The main checkout and the owner's launchd service were not touched. I read
the whole diff, ran the gate (self-test and the shipping client, four configurations) and its unit tests, and
recomputed the pre-#242 refusals with the pre-#242 gate. I planted 43 twins in scratch copies of the fixture outside
the worktree and ran three staleness checks as mutants in a separate scratch copy.
**Date:** 2026-10-21
**Release range:** `0d46032..2a75cae` (17 commits, round 1); `d528020..4aa5cee` (10 commits, round 2)
**Reviewed head:** 4aa5ceeeb72bbde4201b1553770b28909f275e19
**Risk tier:** MEDIUM. The brief declares no HIGH paths (`docs/project-brief.md:110`). The change rewrites the
definition of a security gate (INV-62, INV-64, INV-66, INV-76; D-126, D-160, D-180, D-181) and touches no route, no
`src/` code, no dependency, no CI, hook, `.claude/` or `.githooks/` file. There is no auth, PII, payment or migration
path, so §11's senior-review trigger does not fire.

## Verdict
BLOCKING

### Round 2 — re-verification at `4aa5cee` (2026-10-21)

Round 2 counts: B1 still open, narrowed (round 2 of 3 on this finding) · M2 still open, narrowed · M1, M3, M4, R1 and
R2 closed · R3 left, accepted.

**Method.** The worktree was moved by the coordinator to `4aa5cee`, detached. It keeps its own venv, and the main
checkout and the service were not touched. I read `git diff d528020..4aa5cee`, ran `make client-decls` (self-test and
shipping client) and `tests/unit/test_client_decl_gate.py`, recomputed the refusals in all four configurations, and
re-planted every round-1 twin plus 21 new ones with the same harness in scratch copies outside the worktree.

**No loosening (D-214 clause 1): still holds.** At `4aa5cee` the fixture makes 281 refusals (Release) and 280
(Debug). Every one of the pre-#242 gate's 183 and 182 is still made, in all four configurations: 0 missing in each.
`make client-decls` gives `client-decls PASS: 22 client file(s) in 4 configuration(s)`, so the pin self-test is
green. `tests/unit/test_client_decl_gate.py` gives `205 passed`.

**B1, still open, narrowed.** The seven round-1 lines are now refused: `map(abs)`, `let f = abs; f(x)`, `max` held
in a value, `map(\.magnitude)`, `x[keyPath: \.magnitude]`, `map(\.words.count)` and
`map(Int.init(truncatingIfNeeded:))`. So are these new forms:
- `[x].first.map(abs)`;
- `map(abs as (Int) -> Int)`;
- `compactMap(UInt.init(exactly:))`;
- a function held in a struct's field;
- an app function passed by name.

Two by-reference forms still pass the new gate. The pre-#242 gate passed them too, so neither is a loosening:
- **A key path held in a name.** `_meets` judges a key path only when it is written at the application
  (`scripts/client_decl_gate.py:2203`, `_by_reference` at `:2160-2180`). Bound to a local first, or passed as a
  parameter, its members are never read. `_by_reference` flags a `main` reference only when its type has `->`, and
  `KeyPath<Int, UInt>` has none:
  ```swift
  func r2KPVar(_ s: Standing) -> UInt { let kp = \Int.magnitude; return s.position[keyPath: kp] }
  func r2KPVarC(_ s: Standing) -> [UInt] { let kp = \Int.magnitude; return [s.position].map { $0[keyPath: kp] } }
  func r2KPP(_ s: Standing, _ kp: KeyPath<Int, UInt>) -> UInt { s.position[keyPath: kp] }
  func r2KPPUse(_ s: Standing) -> UInt { r2KPP(s, \.magnitude) }
  ```
  This is `.magnitude`, an issue-named twin, written with its key path bound to a name first: the form #242 exists to
  end. The register overclaims at `docs/security-invariants.md:190`: "a key path applied to one
  (`x[keyPath: \.magnitude]`) meets its members". That holds only for a key path written in place.
- **A method of a served number referenced without being applied.** The served number is captured as the receiver,
  and the call that follows carries no served argument, so neither `_calls_a_value` (`:2182`) nor `_application`
  (`:2114`) sees it:
  ```swift
  func r2Partial(_ s: Standing) -> Int { let g = s.position.advanced(by:); return g(1) }
  func r2Dist(_ s: Standing) -> Int { let g = s.position.distance(to:); return g(10) }
  func r2Sig(_ s: Standing) -> Int { let sg = s.position.signum; return sg() }
  ```
  `.advanced` applied directly is a fixture shape the arithmetic rule refuses. It is the same by-reference class as
  B1's `let f = abs`.

**Remedy.**
1. Refuse a `keypath_application_expr` on a served number whose key path is not a `keypath_expr` written in place,
   since the gate cannot read it. Alternatively, judge every `keypath_expr` over a numeric root wherever it stands, as
   #244 does for a request's key paths.
2. Judge a method reference whose receiver is served and which is not the callee of a call on the spot (an unapplied
   `dot_syntax_call_expr`) as the served number meeting that method as its receiver, by `_meets` and by the
   arithmetic rule's list.
3. Plant the seven lines above as `shape:` lines, and qualify G-2's sentence.

The next BLOCKING on this finding is its third, which ends the loop (`/close-wave` step 3).

**M2, still open, narrowed (MINOR).** A key path written in place in a store is now refused:
`h[keyPath: \TwHolder3.address]` gives `receives a URL, by TwHolder3.address, declared in ContentView.swift`
(`scripts/client_decl_gate.py:1132-1136`). The same key path bound to a local first passes, for the same reason as
B1's first form. Only `node.kids[1]`'s subtree is read, and a local `k` is declared in the store's own file:
```swift
// ContentView.swift
struct R2Holder6 { let address: URL }
// FrontDoor.swift
func r2KPStore6(_ h: R2Holder6) -> GapRegisterStore { let k = \R2Holder6.address; return GapRegisterStore(url: h[keyPath: k]) }
```
The G-13 row (`docs/security-invariants.md:197`) now says "through a key path" without that qualification. It stays
MINOR for the round-1 reasons: other files cannot make a URL, the runtime `isFileURL` guard and the text pin stay.
The same remedy applies: judge the `keypath_expr` in a store wherever it stands, or refuse a key-path application
whose key path is not written in place. If neither is done, name the form in G-13.

**Closed.**
- **M1:** both classes are named in G-2's "still not held" (`docs/security-invariants.md:190`: M1a, generic; M1b,
  rebuilt from comparisons). Re-planted, both still pass, as the register now says. The issue the author says will be
  filed is not yet filed: queued as R4.
- **M3:** in `Detail.swift`, away from the fixture's own copies, three forms are now refused:
  - `Thread.detachNewThreadSelector(_:toTarget:with:` and `RunLoop.perform(_:target:argument:order:modes:` give "it
    takes a `Selector`, whatever its label" (`selector_facts`, `_selector_problem`);
  - `NSSortDescriptor.init(key:ascending:` gives "a key labelled `key:` or `keyPath:`".

  `NSObject.perform(_:with:afterDelay:` is refused by the type rule too.
- **M4:** I re-ran the round-1 mutant (the three staleness checks replaced with `pass`). It now fails
  `test_242_an_unused_constant_type_folder_maker_or_store_read_fails_the_gate[SINK_CONSTANT_TYPES]`,
  `[STORE_FOLDER_MAKERS]` and `[STORE_READS]` (3 failed).
- **R1:** `Set(_:)` is scoped to `("AnswerPlan.swift", "disclosures")`, now that `_placed` names a computed property's
  getter as its place (`scripts/client_decl_gate.py:559`).
- **R2:** `String(_:)`, `ClosedRange.contains`, `Array.subscript` and `sorted` are each place-scoped
  (`:531-547`). The shipping client still passes the stale-entry check in all four configurations.

**Gate lines at `4aa5cee`:**
- `make secrets`: `INF no leaks found`
- `make deps`: `No known vulnerabilities found`
- `make slopsquat` (`DEVFLOW_FRESH=1`): `slopsquat PASS: 20 declared dependency(ies), 0 suspect`
- `make conformance`: `conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)`

**Risks queued (round 2).**
- **R3** (round 1): left, accepted.
- **R4:** the issue for M1a (generic parameters read through the call's substitution map) and M1b is to be filed.
  Until it is, the two classes live only in the register.
- **R5:** `_placed` passes a computed property's name as the place to `_arithmetic_permitted`
  (`scripts/client_decl_gate.py:2043-2048`). A computed property named like a permitted function of the same file
  would skip `_meets` there; before, such a property's place was `-`. I found no collision on the shipping client,
  where every entry is seen. This is narrow, and worth a line in `ARITHMETIC_PERMITTED`'s comment.

### Round 1 — at `2a75cae`

BLOCKING 1 · MINOR 4 · risks queued 3.

D-214 clause 1, no loosening, holds. I measured it independently: the pin file equals the pre-#242 gate's refusals
in all four configurations, and the self-test fails closed. Every twin the issue and its comments name is planted and
refused as written.

Clause 1 also says "every twin #242 names is refused". Two issue-named G-2 twins, `abs` and `.magnitude`, still pass
when the served number meets them by reference instead of by application: a function value, a key path, or the
function handed to `map`. The `map` form passes through the new by-rule admission `SERVED_PASSES_ELEMENTS`. That
admission's stated premise, "to a closure the flow follows", is not checked. The register's G-2 row says these twins
are refused, without qualification. That is B1. The remedy is small and local to `_meets`.

## Findings

### BLOCKING
- **B1** `scripts/client_decl_gate.py:2033`, `:2039-2040`, `:2047-2064`, `:2091`; `docs/security-invariants.md:190`. Two
  G-2 twins the issue names, `abs` and `.magnitude`, pass the new allowlist when the served number meets them by
  reference. This is an integrity control bypass (REQ-APP-005, D-104, D-181: a second scoring implementation). It is
  not an OWASP class. Planted at the end of `Arithmetic.swift`, simulator Release configuration. The new gate refused
  none of the following:
  ```swift
  func twMapAbs(_ s: Standing) -> Int { [s.position].map(abs).first ?? 0 }
  func twAbsValue(_ s: Standing) -> Int { let f: (Int) -> Int = abs; return f(s.position) }
  func twMaxRef(_ s: Standing) -> Int { let m: (Int, Int) -> Int = max; return m(s.position, 3) }
  func twMapMag(_ s: Standing) -> UInt { [s.position].map(\.magnitude).first ?? 0 }
  func twKP(_ s: Standing) -> UInt { s.position[keyPath: \.magnitude] }
  func twSignKP(_ s: Standing) -> [Int] { [s.position].map(\.words.count) }
  func twNegRef(_ s: Standing) -> [Int] { [s.position].map(Int.init(truncatingIfNeeded:)) }
  ```
  The closure controls are refused by `_meets`: `[s.position].map { abs($0) }` gives `` `Swift.abs` on a served
  position``, and `.map { $0.magnitude }` gives `` `Swift.Int.magnitude` ``. So the closure premise is what the gate
  relies on, and three things break it:
  - The `map(abs)` case, `:2091`. `SERVED_PASSES_ELEMENTS` admits the receiver whatever the argument is. The comment
    at `:2036-2038` says the method hands each element "to a closure the flow follows (`HANDS_ELEMENTS`,
    `_Flow.closure`)". A function reference such as `abs`, `Int.init(truncatingIfNeeded:)` or `\.magnitude` is no
    closure the flow follows. `_served_operand` drops it as a function type, and `_NOT_AN_OPERAND` drops it as a key
    path.
  - The key-path cases, `:2033` (new in #242) and `:2047-2064`. `_NOT_AN_OPERAND` excludes `keypath_expr`, and
    `_application` has no case for a key-path application (`x[keyPath:]`). So a member of another module named in a
    key path is never judged.
  - The function-value cases (`let f = abs`; `max`). The callee is a local of the module `main`, which `_meets` skips
    at `:2082`. `_operator_as_value` (#173) holds this form only for operators: `[s.position].map(-)` is a fixture
    shape, but `map(abs)` is not refused.

  None of these is a loosening; the pre-#242 gate passed them too. They are the issue's own named twins, written
  another way: the cycle #242 exists to end, and D-214's "Revisit when" case. The register states the opposite at
  `docs/security-invariants.md:190`: "So `abs`, `min`, `max`, `.magnitude`, `.rounded(_:)` … are refused". Its
  "still not held" examples do not name a function reference or a key path.
  **Remedy.**
  1. Admit `SERVED_PASSES_ELEMENTS` only when every argument is a `closure_expr` or an `autoclosure_expr`. Judge any
     other argument that names a declaration of another module as the served number meeting that declaration.
  2. Treat a key path (`keypath_expr` components, and the `x[keyPath:]` application) over a numeric root as the served
     number meeting each member it names.
  3. Treat a reference to a non-`main` function used as a value, where a served number reaches its call, the way
     `_operator_as_value` treats an operator.
  4. Plant the seven lines above as `shape:` lines, and correct the G-2 row.

### MINOR
- **M1** `docs/security-invariants.md:190`; `scripts/client_decl_gate.py:875` (`NUMERIC_TYPE`), `:2067-2072`. Two
  classes of G-2 twin pass both rules, before and after #242. The register's non-exhaustive "still not held" list
  names neither.
  - **(a) A served number inside a generic function of the app's own.** In
    `func twGenP<T: Numeric>(_ x: T) -> T { x + x }` called as `twGenP(s.position)`, both the arithmetic rule and
    `_meets` read the operand's static type, `T`, which `NUMERIC_TYPE` does not match. So any arithmetic passes,
    `abs(x)` in `twGen<T: SignedNumeric & Comparable>` included.
  - **(b) A served number rebuilt from comparisons.** `(1...100).filter { $0 <= s.position }.count + 1` and
    `((0..<100).first { $0 == s.position } ?? 0) + 1` each equal `s.position + 1`. The comparison admission
    (`SERVED_MAY_MEET_BY_RULE`) and the element-passing admission let them through. The register's example ("a
    selection written with a comparison") covers `a > b ? a : b`, not a count or a search over comparisons.

  This is MINOR rather than BLOCKING because neither class is #242's loosening or its named twin, and the register
  calls its list examples. Name both classes in G-2, and file an issue for (a): read a generic parameter through the
  call's substitution map.
- **M2** `scripts/client_decl_gate.py:1081-1090` (`_store_received`); `docs/security-invariants.md:197`. G-13 says "a
  URL-typed declaration of another file [is] refused". Read through a key path, it is not. I declared
  `struct TwHolder3 { let address: URL }` in `ContentView.swift`, and in `FrontDoor.swift`
  `func twKPStore3(_ h: TwHolder3) -> GapRegisterStore { GapRegisterStore(url: h[keyPath: \TwHolder3.address]) }`.
  The gate refused nothing. The control `GapRegisterStore(url: h.address)` is refused (`receives a URL, by
  `TwHolder4.address`, declared in ContentView.swift`). `_store_received` reads only `declref_expr` and
  `member_ref_expr`, so the "allowlist" still enumerates the forms it refuses.
  This is MINOR because three things still stand: `ContentView.swift` cannot make a URL (`URL.made` outside the
  network door and the stores), the shipping `load()` keeps its `isFileURL` guard, and the text pin stays. Refuse any
  URL-typed expression in a store whose `_named` set names a declaration of another file, plant the form, and name it
  in G-13 until then.
- **M3** `scripts/client_decl_gate.py:309-310` (`BY_NAME_LABEL`); `docs/security-invariants.md:196`. The issue names
  "the target and selector APIs" and key-value coding (round 2, B3). Matching by label misses a selector parameter
  labelled `_`, and a key labelled `key:`. These pass the new gate:
  - `Thread.detachNewThreadSelector(named, toTarget: target, with: nil)`;
  - `RunLoop.main.perform(named, target: target, argument: nil, order: 0, modes: [.default])`;
  - `NSSortDescriptor(key: typed, ascending: true).compare(a, to: b)`. This is key-value coding by a key the reader
    typed; the sort counter refuses only the `sortedArray` spelling.

  G-12's catch-all ("whose declaration takes none of these labels") is honest. This is MINOR because the client cannot
  make a `Selector` from text: `ObjectiveC` is off the module allowlist and `NSSelectorFromString` is in `BY_NAME`.
  Match a parameter whose interface type is `Selector` rather than its label, and add `key:` and `keyPath:` on
  Foundation declarations (or `NSSortDescriptor` to `BY_NAME`).
- **M4** `scripts/client_decl_gate.py:2553-2559` (`unseen_permissions`). The staleness reports for
  `SINK_CONSTANT_TYPES`, `STORE_FOLDER_MAKERS` and `STORE_READS` have no test that watches them fail. Mutant: I
  replaced all three with `pass` and ran `tests/unit/test_client_decl_gate.py`. The result was 183 passed and 1
  failed. The one failure, `test_make_client_decls_runs_the_gate_and_keeps_its_status`, reads the `Makefile`, which
  my scratch copy lacked. The only test that names these tables (`:550`, the control half) stubs them all at once.
  Add one test per table, as `test_242_each_sink_has_its_own_lists_and_a_stale_entry_fails_the_gate` (`:1104`) does
  for the sink lists.

### PASS
- **No loosening, measured independently.** I ran the pre-#242 gate (`git archive 0d46032`) on the pre-#242 fixture
  in all four configurations. It made 183 refusals in Release and 182 in Debug. The set equals
  `tests/unit/data/client_decl_refusals_before_242.txt` exactly in each configuration: 0 missing and 0 extra each way.
- **The pin check fails closed.** `pinned_refusals` (`scripts/client_decl_gate.py:2852-2866`) returns None for a
  missing, empty or malformed file, or any line of another shape. `_pin_broken` (`:2869-2877`) turns None into a
  failure. It runs in every configuration of `self_test` (`:2900`), which `main()` runs before the client. The pin is
  `ROOT/tests/unit/data/…` (`:612`), the tree the gate runs from. Watched failing:
  `test_the_self_test_fails_when_a_pinned_refusal_is_gone` (`tests/unit/test_client_decl_gate.py:1067`). The count is
  pinned at 183 and 182 (`:1054`), so deleting a line also fails.
- **The fixture is extended, not weakened.** Five files only append. The two in-place edits are in
  `StandingsStore.swift` `keep` and `keptAnswers`, made so that `Data()` is not refused by the store's narrower list.
  They keep their pinned refusals byte-identical, line numbers included, and the self-test checks this.
- **Every named twin is refused as written.** The fixture plants and refuses:
  - G-1: widened constants, `ManagedBuffer`, `Calendar.current`, the store's inherited `Bundle` reads;
  - G-2: `abs`, `min`, `max`, `.magnitude`, `.rounded(_:)`, the table, the bound count, range and drop, and the four
    count initialisers;
  - G-11: unlabelled, initialiser and subscript arguments;
  - G-12: the collections' KVC, `setValuesForKeys`, `classNamed`, `principalClass`, `Timer`, `Thread`,
    `NotificationCenter`, `Selector.init`, `responds(to:)`;
  - G-13: helper given and inferred, alias, cast, #276's shadowed read, store parameter, `GapRegisterStore` built
    outside its file.

  My own twins confirmed the refusals for `.description`, `contains` on an app list, `max()` of a list, a dictionary
  lookup, `Optional(_:)`, a string round trip, `advanced(by:)`, and lazy `let`/`static let` relays of screen state
  into a sink (`String` and `Int`). The new gate refuses each; four of these the old gate passed.
- **Every allowlist entry is seen on the shipping client.** `make client-decls` passes in all four configurations with
  `unseen_permissions` on. I listed the shipping facts: each `SERVED_MAY_MEET` entry is met where its reason says
  (`priceTag`, `number`, `wholeNumber`, `money`, `disclosures`), and so is each of `SINK_CONSTANT_TYPES` (`Int`,
  `String`), `STORE_FOLDER_MAKERS`, `STORE_READS` and `BY_NAME_ALLOWED`. The per-sink lists drop `URL.init(string:`,
  `URL.decoded` and the session from the standings store (backlog-gates round 2, K1).
- **The four changed existing tests each expect more refused, never fewer:**
  - `test_a_url_decoded_outside_the_engine_client_is_the_network` (`:49`) keeps "no network refusal" for the door, and
    tolerates the sink list's new refusal;
  - `test_a_store_makes_a_url_only_from_the_file_systems_folders` (`:954`): every maker is still refused in both
    stores. The standings store's reason is now its own list, which `_sink_module_problem` reaches first; the #246
    rule stays behind it;
  - `test_the_code_a_sink_runs_is_followed_into_computed_properties_and_protocol_witnesses` (`:623`) keeps the two
    reads, and the `SINK_RUNS_ALLOWED` lines are additional;
  - `test_a_permission_the_client_no_longer_uses_fails_the_gate` (`:550`) adds the new tables to the control only.
- **The register's other "still not held" lines are honest.** G-1 (`:189`), G-11 (`:195`), G-12 (`:196`) and G-13's
  function-value line (`:197`) match what I measured, apart from M2.
- No secret, no new import or dependency, no destructive operation, and no edit to `.github/`, `.claude/`,
  `.githooks/`, `Dockerfile` or `/deploy/` in the range.

## Gates passed
- [x] Secret scan green (`make secrets`: `INF no leaks found`)
- [x] `make deps` (pip-audit) green (`No known vulnerabilities found`)
- [x] `make slopsquat` green (`slopsquat PASS: 20 declared dependency(ies), 0 suspect`; no new import in the range)
- [x] Default-deny preserved for new external surfaces (no route, no `src/` change; the gate itself only narrows)
- [x] Permission-matrix not violated
- [x] Prompt-injection hygiene: not applicable (no untrusted-content consumer changed)
- [x] Auth/PII checks + human review trigger: not applicable (no HIGH path; the gate is D-126 privacy tooling, not an auth/PII path)
- [ ] SAST: the gate's own control fails a named twin (B1); `make client-decls` PASS: `22 client file(s) in 4 configuration(s)`; `make conformance`: `conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)`

Gate output for this verdict: `tests/unit/test_client_decl_gate.py` gave `184 passed in 84.91s` in this worktree.

## Acceptance criteria evidence
- D-214 cl. 1, no loosening → `tests/unit/data/client_decl_refusals_before_242.txt` (equal to the pre-#242 gate's
  refusals in all four configurations); `scripts/client_decl_gate.py:2852-2877`, `:2900`;
  `tests/unit/test_client_decl_gate.py:1054`, `:1067`
- D-214 cl. 1, every named twin refused → planted forms: `tests/unit/test_client_decl_gate.py:1090`, `:1128`, `:1165`,
  `:1191`, `:1219`, `:1227`, `:1251`, `:1260`. **Not met for `abs` and `.magnitude` by reference (B1).**
- Allowed lines still pass → `tests/unit/test_client_decl_gate.py:1139`, `:1174`, `:1199`, `:1241`; `make client-decls` PASS
- Each allowlist entry seen or reported → `scripts/client_decl_gate.py:2522-2570`; `tests/unit/test_client_decl_gate.py:1104`, `:1145`, `:1199`. Partly unwatched (M4).
- G-1, G-2, G-11, G-12, G-13 rewritten → `docs/security-invariants.md:189`, `:190`, `:195`, `:196`, `:197`. G-2 overclaims (B1), G-13 overclaims (M2).

## Risks queued
- **R1** `scripts/client_decl_gate.py:549`. The `Set(_:)` entry's place is `("AnswerPlan.swift", "-")`, and `-` is any
  scope that is not a `func` or an `init`. So it admits `Set(_:)` on a served number in every accessor, closure and
  initialiser expression of `AnswerPlan.swift`, not only `disclosures`. It is narrow in effect (deduplication, then a
  count by rule), but wider than its reason. If the gate learns to name accessors, scope it to `disclosures`.
- **R2** `scripts/client_decl_gate.py:524-537`. Four `None`-scoped `SERVED_MAY_MEET` entries are met at one place each
  on the shipping client: `Swift.String.init(_:`, `Swift.ClosedRange.contains`, `Swift.Array.subscript(_:` and
  `Swift.Sequence.sorted(`. They are comparison, display and pass-along by nature (and `sorted` is counted), so `None`
  is defensible. A place-scoped entry would make a new use a reviewed edit.
- **R3** `tests/unit/data/client_decl_refusals_before_242.txt`. The pin compares refusal text exactly, line numbers
  included. A later in-place fixture edit forces an edit of a pinned line, and a weakened shape could ride on it. The
  count test catches a deletion but not an edit. Reviewers of a pin-file diff should treat any changed line as a
  removal.
