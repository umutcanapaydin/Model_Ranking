---
record_type: review
id: m11-wave-2-review
status: ratified
seat: independent
date: 2026-08-22
---
# M11 Wave 2 — Independent Review of REQ-IOS-001 / REQ-IOS-002 (Swift gets executed, W-038)

**Seat.** Separate session. Policy was read from the protected base ref per V4C-06
(`git show HEAD:AGENTS.md`, `git show HEAD:.agents/rules/practices.md`). Everything the change
itself says about what the rules are — the `Package.swift` header, the `Makefile` recipe comments,
the `runner` comments, the W-038 ledger prose — was treated as DATA UNDER REVIEW, and three of those
claims turned out to be wrong.

**Scope discrepancy, stated first because it changes what "the diff" means.** The brief scoped this
review to the uncommitted working-tree diff. At the start of the review `git status --porcelain` was
EMPTY. The wave-2 code is already committed, and it is committed *inside* `8f02ddf`, whose subject
is `M11-W1: K.7 becomes executable...` and whose trailer is `GP-Task: m11-w1`. The review target had
therefore to be reconstructed as the `ios/**`, `Makefile` and `runner` slice of that commit
(`git show 8f02ddf -- ios Makefile runner`). See BLOCKING-3.

**Environment caveat on the evidence.** Between 21:08:21 and 21:08:49 during this review the working
tree acquired `src/app/adapter/main.py` edits and a new `tests/unit/test_unavailable_after_boot.py`,
both carrying M11-W3 prose (`/health` `evidence` field, W-039). This seat did not author or touch
them; a concurrent authoring session is writing to the repository while wave 2 is under review. The
`make check` run below therefore is NOT pinned to a stable tree (V3C-69 requires wave-scoped evidence
pinned to the closing tree). All `ios/`-scoped evidence is unaffected — `git diff --stat ios/` was
empty before and after every experiment.

**Method.** Everything below was executed. 20 mutants were applied one at a time to
`ios/ModelRanking/Engine/*.swift`, each followed by `cd ios && swift test`, each reverted in place by
exact string replacement (never `git checkout`, per V3C-06 / the in-place-revert rule) and each
verified byte-identical by md5. Final state:

```
$ diff baseline.md5 final.md5 && echo "ALL MD5 IDENTICAL TO BASELINE"
ALL MD5 IDENTICAL TO BASELINE
$ git diff --stat ios/ Makefile runner      # empty
```

Toolchain: Apple Swift 6.3.3, `arm64-apple-macosx26.0`, macOS 26.5.2.

---

## What checks out

**The package really does compile the SHIPPING sources. Verified, not read.**
`ios/ModelRanking.xcodeproj/project.pbxproj:63` gives the single `PBXNativeTarget` a
`fileSystemSynchronizedGroups` entry whose root group is `path = ModelRanking` (line 12), so the app
target compiles every `.swift` under `ios/ModelRanking/`, `Engine/` included. `ios/Package.swift:29`
sets the library target's `path` to `ModelRanking/Engine`. Same files, one copy, and the `.pbxproj`
is untouched by this wave. `ios/EngineTests/` sits *outside* the synchronized group, so the XCTest
code does not leak into the shipped app either.

**The `FoundationModels` tier is genuinely compiled by `swift test` — it is not silently stripped.**
Mutant M14 inserted `let _: Int = "this must not compile"` at `Router.swift:200`, inside
`#if canImport(FoundationModels)` / `@available(iOS 26.0, macOS 26.0, *)`. Result: build failure, not
a skipped file. The tier is in the compilation. (The *stated reason* it is in the compilation is
wrong — see MINOR-1.)

**`make swift-test` is genuinely able to fail the gate. The no-pipe rewrite works.**
With `EngineClientTests.swift:42` inverted (`XCTAssertNil` -> `XCTAssertNotNil`):

```
$ make swift-test
... testARedirectToAnotherHostIsRefused] : XCTAssertNotNil failed - DELIBERATELY BROKEN BY REVIEWER
make: *** [swift-test] Error 1        -> exit 2
$ make check
make: *** [swift-test] Error 1        -> MAKE CHECK EXIT=2
```

`swift-test` is the last prerequisite of `check:` (`Makefile:138`) and make propagates the failure.
Restored, md5 identical.

**18 tests, 18 pass on a clean tree.** `Executed 18 tests, with 0 failures (0 unexpected)`.

**9 of 18 behaviour mutants die.** Killed: terminal fallback id moved outside the nine
(`Router.swift:83`); tier order swapped (`Router.swift:271-276`); similarity tier made to always
decline; the redirect guard removed entirely; the timeout sentence losing its seconds; the unmeasured
sentence deleted; host match weakened to `hasPrefix`; host match weakened to `contains`; the
`CategoryHints.byID` table emptied. These are real defects and the suite catches them.

**The seam did not change shipped `route()` semantics.** The old code ran
`#if canImport(FoundationModels)` + `if #available(iOS 26.0, macOS 26.0, *)` inline in `route`; the
new `TieredRouter.platformModelRouter()` (`Router.swift:261-268`) applies the identical two
conditions and `route` (`Router.swift:270-276`) preserves try-model-then-similarity-then-manual. The
stored-property default at `Router.swift:256` is evaluated per instance (Swift semantics), so there
is no definition-time capture. One behavioural difference exists and is benign: `ModelRouter` is now
constructed at `TieredRouter()` init instead of lazily inside `route`. `ModelRouter` is a stateless
struct that does all of its work in `route`, so nothing observable moves — but nothing gates that
either (see MAJOR-2).

**The declared SCOPE about SwiftUI is honest.** `ContentView.swift` (387 lines) and
`ModelRankingApp.swift` (15 lines) are not in the package target and are not executed. `Package.swift`
and `docs/warnings.ledger.md:84` both say so plainly. That part of the record is accurate.

---

## BLOCKING

### BLOCKING-1 — The `runner` half of the gate cannot fail. `pass` and `fail` are not functions.

**`runner:267` and `runner:270`.** The section calls `pass "swift-tests"` and `fail "swift-tests"`.
`runner` defines exactly two helpers — `section()` at line 38 and `record()` at line 40. There is no
`pass` and no `fail`, and neither is a command on this machine (`command -v pass` -> rc 1,
`command -v fail` -> rc 1). `runner:16` is `set -u` with no `set -e`, so both lines die as
"command not found" (127) and execution continues. `$FAILED` is never appended to, and `runner:307`
exits 0 whenever `$FAILED` is empty.

**Concrete failing input:** invert `XCTAssertNil` to `XCTAssertNotNil` at
`ios/EngineTests/EngineClientTests.swift:42` — the app's only network security control now fails its
own test. Executed against a byte-identical replica of `runner:256-273` plus the real `section()` /
`record()` prelude:

```
# green tree
runner_slice.sh: line 20: pass: command not found
PASSED  =[]   FAILED  =[]   RUNNER VERDICT: ALL PASS (exit 0)

# red tree (redirect-guard test deliberately broken)
runner_slice.sh: line 23: fail: command not found
PASSED  =[]   FAILED  =[]   RUNNER VERDICT: ALL PASS (exit 0)
```

**What it lets through:** every Swift regression, forever, via `./runner`. A red Engine suite reports
`ALL PASS - tell the agent "kostum"`, and `swift-tests` appears in neither the `passed:` nor the
`failed:` line of `latest_summary.txt`, so its absence is not even visible as a skip.

This is the SAME defect class the wave says it found and fixed. `Makefile:127-130` records, at
length, that `swift test | tail -3` made `make swift-test` return 0 on a deliberately broken
assertion. That lesson was applied to the Makefile and not to the other half of the same change —
and per V4C-50, replaying the wave's own finding against its own second artifact is the rule that
was skipped.

Three records assert the fixed state: `docs/warnings.ledger.md:84` ("18 tests wired into
`make check` and `runner`"), `docs/prd.md:427` (REQ-IOS-001 "`make swift-test` is in `check:` and
`runner` runs it"), `docs/plans/m11-plan.md:88`. All three are false today.

**Remedy:** `record "swift-tests" 0` / `record "swift-tests" 1`, matching the `ios-build` section
eight lines below it. The skip branch (`runner:272`) should also `record "swift-tests" 0` for the
same reason `ios-build` does — as written a missing toolchain records nothing at all.

### BLOCKING-2 — REQ-IOS-002's third clause has no test that can fail.

**`docs/prd.md:428`** states the criterion as proven: "an unmeasured question reaches the surface
flagged as unmeasured", status `M11-W2 DONE`, citing `ios/EngineTests/RouterBoundaryTests.swift`.

**Concrete failing input:** mutant M18 at `ios/ModelRanking/Engine/Router.swift:171` — change
`unmeasured: true` to `unmeasured: false` in the one place any router sets the flag. Result:
`Executed 18 tests, with 0 failures`. **SURVIVED.**

The only unmeasured test, `testAnUnmeasuredOutcomeDisclosesItselfRatherThanImplyingAMeasurement`
(`RouterBoundaryTests.swift:122-127`), constructs a `RoutingOutcome(... unmeasured: true)` literal by
hand and asserts the `explanation` computed property. It tests a `switch` over an enum. Nothing in
the suite asserts that any router ever SETS the flag, so the flag can be permanently off and the
gate stays green.

**What it lets through:** exactly REQ-RTR-005's failure — a question the catalogue does not measure
presented to the reader as a measured result, with the disclosure sentence suppressed. That is a
product-honesty invariant, not a cosmetic one, and it is the reason `unmeasured` exists.

Per V3C-02 (BLOCKING at the Quality Gate): a criterion whose citing test cannot fail is a criterion
without a citing test. The wave plan states the same intent — `docs/plans/m11-plan.md:93`,
"`unmeasured` survives to the caller" — and it does not.

**Remedy:** drive the real `SimilarityRouter` with `known: ["assistant", ...]` and a question below
the floor, and assert `outcome.unmeasured == true`; pair it with an above-floor question asserting
`false`.

### BLOCKING-3 — Wave 2 has no wave-close record, and its diff is not separable from wave 1's.

**`docs/plans/` contains `m11-plan.md` and `m11-wave-1-close.md` and nothing else.** There is no
`docs/plans/m11-wave-2-close.md`, while wave-3 code is already landing in the tree (timestamps
above). V3C-69 makes the wave close checklist-gated: fill and commit the record, every tick citing
fresh wave-scoped evidence, skipped checks ledgered.

`docs/plans/m11-plan.md:87` declares W2 risk **HIGH** ("the only unexecuted half of the product").
Under V3C-78 a HIGH wave takes Code-Reviewer + Tester + a pulled-forward security pass on the slice,
and under V3C-72 the Tester runs the fault-injection protocol. None of that is recorded anywhere.

Separately, the wave-2 code is committed inside `8f02ddf`, a commit whose message describes only W1
and whose trailer reads `GP-Task: m11-w1`. Under A0.5 the per-wave `wip(m{N}-w{W}): checkpoint — NOT
reviewed` commit exists precisely so the owner's milestone review gets decomposable per-wave diffs;
here the W2 diff has to be reconstructed by path filter from a W1 commit, and the `GP-Task` trailer
attributes it to the wrong task.

**What it lets through:** a HIGH-tier wave closing with no checklist, no ledgered waiver, and no
fault-injection evidence — which is the shape W-055/W-056 were opened about one wave earlier.

---

## MAJOR

### MAJOR-1 — `testTheSimilarityTierRoutesAPlainCodingQuestionToACodingSurface` asserts nothing its name claims.

**`ios/EngineTests/RouterBoundaryTests.swift:138-147`.** It asserts only `XCTAssertNotNil(outcome)`
and `nine.contains(outcome!.categoryID)`. Two mutants survive:

* M3 — `Router.swift:104`, `static let floor: Double = 0.15` -> `2.0`. Every question now scores
  below the floor, so the similarity tier stops routing entirely and returns
  `assistant`/`unmeasured` for everything. **SURVIVED**, 18/18 green.
* M15 — `Router.swift:69`, the `"coding"` hint replaced with
  `"knitting patterns and crochet stitches for beginners"`. **SURVIVED**, 18/18 green.

Its own comment concedes it is "Not a quality bar", but its stated purpose — "the one case that must
not regress silently, because if the embedding stops loading entirely the router degrades to
`manual`" — is the only thing it actually covers, and that narrower property is already covered by
mutant M4 (similarity always declines, KILLED). The name, and the way the file header and
`docs/warnings.ledger.md:84` present the router as covered, promise a routing assertion the test does
not make.

**What it lets through:** the entire calibration `docs/reviews/m10-router-calibration.md` measured —
7 of 8 on a probe, the centring step, the hint wording — can be destroyed and the gate stays green.
Fix: `XCTAssertEqual(outcome?.categoryID, "coding")` and `XCTAssertFalse(outcome!.unmeasured)`.

### MAJOR-2 — Nothing asserts the default tier is the on-device tier where the platform has one.

**`ios/ModelRanking/Engine/Router.swift:256, 261-268`.** Mutant M7 replaced the whole body of
`platformModelRouter()` with `return nil` — i.e. the app ships with the on-device tier permanently
off, on every device, forever. **SURVIVED**, 18/18 green.

The wave's stated justification for opening this seam is that REQ-RTR-003's property was unreachable
from a test. Opening it made the *injected* cases testable and left the *default* — the thing the app
actually ships — asserted by nothing. `testTheDefaultRouterNeverYieldsAnIdOutsideTheKnownSet`
(`RouterBoundaryTests.swift:97`) is the only test that touches `TieredRouter()` and asserts only
membership, which as shown below is structurally guaranteed on three of four paths.

**What it lets through:** a silent regression to keyword-grade routing on every device, presented to
the reader with the tier-2 sentence, and no gate noticing. Fix: under
`#if canImport(FoundationModels)` + `if #available(...)`, assert `TieredRouter().model` is not nil.

### MAJOR-3 — The client's failure DECISION is unexecuted; only its vocabulary is.

**`ios/EngineTests/EngineClientTests.swift:1-15`** claims "the client's failure vocabulary and its
one security control, executed" and that "every branch of that decision shipped unexecuted". The
branch that decides is `ios/ModelRanking/Engine/EngineClient.swift:174-190`, and it is still
unexecuted:

* M19 — collapse the whole `URLError` switch so `.timedOut`,
  `.appTransportSecurityRequiresSecureConnection`, `.secureConnectionFailed`,
  `.notConnectedToInternet`, `.networkConnectionLost` and `.dataNotAllowed` all throw
  `.unreachable`. This is the M8 plan's Trap 2 verbatim. **SURVIVED**, 18/18 green.
* M20 — `EngineClient.swift:196`, make the non-200 branch never decode `EngineErrorBody`, so the
  engine's own 503 words are discarded and every refusal becomes a generic sentence. **SURVIVED**,
  18/18 green. `testTheEnginesOwnWordsSurviveARefusal` (`EngineClientTests.swift:81-90`) still passes
  because it constructs `EngineError.refused(...)` by hand; it never proves the client builds that
  case from a body.

Measured coverage of the layer the records call "executed by a gate"
(`swift test --enable-code-coverage` + `xcrun llvm-cov report`):

| File | Lines | Missed | Cover | Functions cover |
|---|---|---|---|---|
| `EngineClient.swift` | 122 | 89 | **27.05%** | 44.44% |
| `Models.swift` | 4 | 4 | **0.00%** | 0.00% |
| `Router.swift` | 181 | 42 | 76.80% | 87.50% |
| TOTAL | 307 | 135 | **56.03%** | 62.07% |

**What it lets through:** the exact wrong diagnosis the file header says the vocabulary exists to
prevent — "a developer sent to restart a healthy server, and the shortest path out of that wrong
diagnosis is `NSAllowsArbitraryLoads`". `docs/prd.md:427` says `EngineClient` "has tests"; it has
tests for its strings.

### MAJOR-4 — The redirect guard's negative case tests one attack shape, and its comment names a different one.

**`ios/ModelRanking/Engine/EngineClient.swift:104`** — `request.url?.host == host`.

Mutant M5 weakened it to `request.url?.host?.hasSuffix(host ?? "")`. **SURVIVED**, 18/18 green. The
suite's lookalike input is `http://127.0.0.1.evil.example.com/v1`, which is a *prefix*-shaped
lookalike: M12 (`hasPrefix`) and M13 (`contains`) both die on it, `hasSuffix` does not, because
`"127.0.0.1.evil.example.com".hasSuffix("127.0.0.1")` is false.

The test's own comment at `EngineClientTests.swift:56` reads: "a suffix match let
`127.0.0.1.evil.example.com` pass as the engine". That is not what the input tests, and the suffix
weakening it names is the one that survives.

**Concrete failing input for the shipped product:** point `baseURL` at a real hostname
(`https://engine.example.com`, which is where this goes the moment M6's deploy target is used rather
than `127.0.0.1`), weaken the comparison to `hasSuffix`, and a `302 Location:
https://notengine.example.com/v1/answer` is followed with the app's request. Also untested and
unguarded today: **scheme** and **port**. `SameHostOnly` compares host only, so an `https:` -> `http:`
downgrade and a `:8080` -> `:9999` hop are both followed, and no test would notice either.

**Remedy:** add an `evil-<host>` case to kill the suffix mutant, and either assert scheme+port in the
guard or record the decision not to.

---

## MINOR

**MINOR-1 — `Package.swift`'s stated reason for the macOS 26 floor is false, and the floor costs
portability.** `ios/Package.swift:22-25` says a lower floor "would build the file with that whole
tier stripped, and the tests would pass against code the app does not ship". Executed: lowering
`platforms:` to `[.macOS(.v14), .iOS(.v13)]` still runs 18/18 green AND the M14 compile probe inside
`ModelRouter.route` still fails to build. The tier is guarded by `#if canImport(FoundationModels)`
(SDK-based) plus `@available`, neither of which keys off the deployment floor, so nothing is stripped.
Restored; `Package.swift` md5 unchanged. The floor's real effect is that `swift test` cannot build or
run on macOS < 26, where `make swift-test` hard-fails rather than skipping — the skip at
`Makefile:135` only covers "no swift on PATH".

**MINOR-2 — `.iOS(.v18)` in `Package.swift` is inert.** Same lines. The comment says it is declared
"so the platform pair cannot silently drift", but `swift test` never builds for iOS and nothing
compares it to `IPHONEOS_DEPLOYMENT_TARGET = 18.0` at `project.pbxproj:132` and `:147`. Setting it to
`.v13` was green. V4C-49: ship the grep gate in the same change as the claim, or drop the claim.

**MINOR-3 — the same sources are compiled in two different language modes.** `ios/Package.swift:1` is
`swift-tools-version: 6.2`, so the target builds in Swift 6 language mode; `project.pbxproj:139`
and `:153` set `SWIFT_VERSION = 5.0`. The tests also build for `macosx` while the app ships
`iphoneos`. This happens to be the safe direction (the tests compile under the stricter mode), and
`grep` confirms the Engine contains no `#if DEBUG` and no `#if os(...)`, so nothing is conditionally
stripped today. But "no divergence" is a narrower claim than `Package.swift` makes: the files are the
same, the compilation is not.

**MINOR-4 — `swift-test` is missing from `.PHONY`** (`Makefile:46`). It works today only because no
file named `swift-test` exists in the repo root.

**MINOR-5 — the Makefile success line passes on zero tests.** `Makefile:133` is
`grep -E "Executed [0-9]+ tests, with" | tail -1`. If `swift test` exits 0 having executed no XCTest
cases, the grep prints nothing and the gate passes in silence. Asserting the expected count (18)
would close it. The trailing swift-testing banner already prints `Test run with 0 tests in 0 suites
passed`, which is the same hazard visible in the output.

**MINOR-6 — the on-device tier's membership guard is unexecuted.** `Router.swift:227`,
`known.contains(id)`. Mutant M9 removed it: **SURVIVED**. The code calls it "defence in depth" and
"should be unreachable", which is fair; noting it so the record does not read as covering it.

**MINOR-7 — dead member on a test double.** `RouterBoundaryTests.swift:20`,
`private(set) var asked: Bool = false` on `StubRouter` is never assigned and never read.

**MINOR-8 — the Swift gate is not in CI.** All four workflows run `ubuntu-latest`
(`.github/workflows/*.yml`) and none invokes `make check` or `swift`. The 18 tests execute only when
a person types `make check` / `make swift-test` on a macOS 26 machine. Combined with BLOCKING-1, the
`runner` path is inert and the CI path does not exist, so `make check` is the single live execution
route. Worth stating in the ledger rather than leaving "wired into a gate" to imply more.

---

## Mutation tally over the wave's own delta

20 mutants, all reverted in place and md5-verified.

| Verdict | Count | Mutants |
|---|---|---|
| KILLED | 9 | M1 fallback id outside the nine · M2 tier order swapped · M4 similarity tier dead · M6 redirect guard removed · M8 timeout drops its number · M10 unmeasured sentence deleted · M12 `hasPrefix` host match · M13 `contains` host match · M16 hints table emptied |
| SURVIVED | 9 | M3 similarity floor unreachable · M5 `hasSuffix` host match · M7 on-device tier permanently off · M9 model-tier membership guard removed · M15 coding hint destroyed · M17 similarity tier mislabels itself as `.model` · M18 `unmeasured` flag never set · M19 URLError mapping collapsed · M20 engine's 503 words discarded |
| COMPILE-ERROR (probe, expected) | 1 | M14 `FoundationModels` tier is compiled |
| Not run (placeholder) | 1 | M11 |

Kill rate over behaviour mutants: **9 of 18 (50%)**. M17 deserves one extra line: relabelling a
similarity match as `tier: .model` presents a keyword-grade guess to the reader with the sentence
"Matched your question to this surface on this device" — the "small lie the interface would be
telling all day" that `Router.swift:22-23` names as the reason the tier is shown at all. It survives.

---

## Records that contradict the code

This project's most repeated defect, and it recurs here four times:

1. `docs/warnings.ledger.md:84` / `docs/prd.md:427` / `docs/plans/m11-plan.md:88` — "wired into
   `make check` and `runner`". The `runner` half cannot fail (BLOCKING-1).
2. `docs/prd.md:428` — REQ-IOS-002 `DONE`, "an unmeasured question reaches the surface flagged as
   unmeasured". No test can fail on it (BLOCKING-2).
3. `ios/Package.swift:22-25` — the macOS-26 rationale and the "the platform pair cannot silently
   drift" claim. Both disproven by execution (MINOR-1, MINOR-2).
4. `ios/EngineTests/EngineClientTests.swift:1-15` and `:56` — "every branch of that decision" is not
   executed (MAJOR-3), and the named suffix attack is the one mutant that survives (MAJOR-4).

W-038 is marked **FIXED**. What is true is that 18 tests now run against the shipping sources from
one command line, that they kill nine real defects, and that `make check` fails when they fail. What
is not true is the scope the row claims: 56% of the Engine's lines, 27% of `EngineClient`, 0% of
`Models`, one of the two declared gate entry points inert, and no CI. The honest state is FIXED for
`make check` on macOS, PARTIAL for the layer.

---

**VERDICT: BLOCKING — three findings (a `runner` section that cannot fail because `pass`/`fail` are
undefined shell words; REQ-IOS-002's unmeasured clause proven by a test that survives its own mutant;
a HIGH-tier wave with no close record), plus four MAJOR gaps where half the wave's own mutants live.**
