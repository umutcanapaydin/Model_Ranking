---
record_type: review
id: m16-wave-1-rereview-2
status: ratified
seat: independent
process_version: v5.0
date: 2026-09-22
---
# M16-W1 — independent second re-review (round-3 fixes)

**Seat:** independent (Code-Reviewer + Tester; wrote none of this code). **Subject:** the author's
round-3 fixes, UNCOMMITTED in the working tree, against every finding of
`docs/reviews/m16-wave-1-rereview.md` (BLOCKING — 1/3/7/0). Reviewed file state:
`scripts/client_decl_gate.py` sha256 `8168b914ef6b1760…`,
`tests/unit/test_swift_test_manifest.py` `4771bd5be9181234…`. Every mutant ran in a copy under the
session scratchpad (`scripts/` + `ios/ModelRanking` for the decl gate; `tests/unit/<file>` +
`ios/EngineTests` for the manifest test; the `sw` copy's manifest test was synced to this working
tree before its swift-test mutants ran). The only repository file this seat wrote is this one. No
git checkout/restore/stash/commit and no `make install` were run. `note.txt` and
`docs/plans/m16-wave-1-close.md` were being edited by the author and were NOT reviewed.

## Verdict

**PASS — 0 BLOCKING, 0 MAJOR, 0 MINOR, 2 NIT.**

Every BLOCKING, MAJOR and MINOR of the re-review is closed as written or honestly recorded, and I
confirmed each by running it. The one BLOCKING (R-B1) is gone: `CoreFoundation` is now allowlisted
symbol by symbol (`CGFloat` only), and `CFSocketCreate`/`CFSocketConnectToAddress`/`CFSocketSendData`
(X01), `CFNotificationCenter…` (B11), `CFShow` (X14) and `CFStreamCreatePairWithSocketToHost` (X19)
all die on the module rule. The three MAJORs (R-M1 runtime `LocalizedStringKey` link, R-M2
credential/cookie stores, R-M3 the static manifest half) die too. The real client passes the gate
in all four configurations (1472 declarations each) and the real suite passes the manifest test.
Two NITs are latent false-positive risks that do not fire on the shipping tree.

**Real client, real suite (run by this seat):**
- `python3 scripts/client_decl_gate.py` on the repo tree: `client-decls PASS: 11 client file(s) in
  4 configuration(s) -- simulator, release: 1472; simulator, debug: 1472; device, release: 1472;
  device, debug: 1472`.
- `pytest tests/unit/test_swift_test_manifest.py tests/unit/test_router_hints.py`: 10 passed.
- `make swift-test` on a clean copy: `swift-test PASS: 262 test(s)`, manifest diff empty.

## Disposition of the re-review's findings

| id | finding | disposition | evidence (run by this seat) |
|---|---|---|---|
| R-B1 (BLOCKING) | `CoreFoundation` allowlisted whole → CFSocket exfiltration | **CLOSED** | `COREFOUNDATION_ALLOWED = {"CGFloat"}`; `_module_problem` refuses any other CoreFoundation symbol. X01 (CFSocket) DIED(rule) all 4 configs; B11, X14, X19 DIED(rule). Real client still resolves only `CGFloat` there (1472 decls, PASS). |
| R-M1 (MAJOR) | runtime `LocalizedStringKey` markdown link | **CLOSED** | `LocalizedStringKey.init(_:` and `…init(stringLiteral` in `FORBIDDEN`. X15 DIED(rule) all 4 configs. No false positive: `Text("literal")`, `Text("k", comment:)`, `Section(header: Text("…"))` and a typed `let k: LocalizedStringKey = "Hello"` all SURVIVE (they bind `Text.init`/the literal, not `LocalizedStringKey.init(_:`). |
| R-M2 (MAJOR) | `URLCredentialStorage`/`.synchronizable`, `HTTPCookieStorage` | **CLOSED** | `URLCredentialStorage`, `URLCredential`, `URLProtectionSpace`, `HTTPCookieStorage`, `HTTPCookie` in `FORBIDDEN`. X04 DIED(rule), X10 DIED(rule), both all 4 configs. |
| R-M3 (= M-4, MAJOR) | static half blind to `#if` at class-member indent and to `private func test` | **CLOSED** | Rule is now content-based (`_guarded_tests` walks `#if…#endif` by brace-free directive depth, any indentation); `FUNC` drops `private`. S1 (`#if false` at 4 spaces) and S2 (`private func test`) BOTH now static FAIL(died) and `make swift-test` DIED (261<262). Nested `#if`, `#elseif`, and `#if` left open to EOF are all flagged; `#if` inside a test body, `#if` in `//` and `/* */` comments, and a `#if` token mid-line in a string are correctly NOT flagged. |
| minor 1 (B11) | Darwin notification, recorded nowhere | **CLOSED** | Dies via R-B1's CoreFoundation rule (DIED all 4 configs); recorded in the gate docstring and the W-122 row. |
| minor 2 (X05/X06) | crash-message class not closed | **CLOSED (recorded)** | `NSException` added to `FORBIDDEN`; X05 DIED(rule). X06 (`try!`) SURVIVES — it has no declaration to refuse, now written into the gate docstring. |
| minor 3 (X14) | `CFShow` passes | **CLOSED** | Dies via R-B1's CoreFoundation rule (DIED all 4 configs). |
| minor 4 (X02) | `Stream.getStreamsToHost` in FrontDoor treated as file | **CLOSED** | Moved to `NETWORK`; X02 (FrontDoor) DIED(rule) "is the network", X03 (Router) DIED(rule). The `InputStream(data:)` false positive (X18) is fixed — it now SURVIVES the decl gate (`FILESYSTEM` lists `InputStream.init(fileAtPath`/`(url`, not bare `InputStream`). |
| minor 5 (X07/X08/X09) | file-system gaps only text gate closed | **CLOSED** | `StringProtocol.write(to`, `URL.init(fileURLWithFileSystemRepresentation`, `FileWrapper` now in `FILESYSTEM`; `FileManager.url(forUbiquityContainerIdentifier` in `FORBIDDEN`. X07, X08 DIED(rule); X09 DIED(rule) all 4 configs. |
| minor 6 (note.txt) | note.txt contradictions | **NOT CHECKED** | Author editing `note.txt` per this seat's instructions. |
| minor 7 (vision count) | measurement doc "five of six" wrong | **CLOSED** | `m16-router-floor-measurement.md:47-49` now says "four of six changed; `describe this photo` and `read the text in this screenshot` did not". Diff `059b519`→working tree confirms exactly four of six changed and those two unchanged. |
| B19 / B22 / B31 (carried OPEN-RECORDED) | file-scope relay / `.textSelection` / `/tmp` write | **STILL OPEN-RECORDED (unchanged, as intended)** | B19 SURVIVED both gates, B22 SURVIVED both, B31 SURVIVED decl gate / died text gate — all as the docstring and W-122 record. |

## New findings

### NIT

1. **`CoreGraphics` geometry types are refused by the module allowlist, while `CGFloat` is
   allowed.** `CGRect`, `CGPoint` and `CGSize` resolve in `CoreGraphics`, which is not in `MODULES`,
   so ordinary SwiftUI layout code using them fails the gate ("resolves … in `CoreGraphics`, which
   is not a module the client may reach"), even though `CGFloat` (via `CoreFoundation`) is allowed.
   The shipping client uses none of them, so it passes today; by the gate's stated design a new
   framework is a reviewed edit, so this is defensible — but the `CGFloat`/`CGRect` asymmetry is a
   latent false positive a future benign layout change would hit.
2. **The manifest test's comment stripper does not touch string literals, so a lone `#if`-style
   token on its own indented line inside a Swift multiline string (`"""`) is misread as a real
   directive.** `COMMENT` strips `//` and `/* */`; `DIRECTIVE` is `^\s*#(if|elseif|else|endif)\b`,
   so such a line inside a `"""` block registers as an open/close directive. It errs SAFE — it can
   only flag a real test or fail the check, never let a guarded test through — and the suite's
   current `"""` blocks (`EngineClientTests.swift`, `UncertaintyTests.swift`) hold only JSON, so it
   does not fire today.

No new BLOCKING, MAJOR or MINOR.

## Mutants and bypasses

"Decl gate" is `scripts/client_decl_gate.py` on a copy of `scripts/` + `ios/ModelRanking`, all four
configurations. "Text gate" is `pytest tests/unit/test_router_hints.py` on the same copy. NULL (no
edit) passes both. The 43-mutant set is the re-review's own (re-run against round-3 files) plus
false-positive probes I added. SURVIVED in the decl gate implies it type-checks in all four
configurations.

| id | attempt (file) | decl gate (round 3) | text gate | vs round 2 |
|---|---|---|---|---|
| X01 | CFSocket connect+send (Router) | **DIED (CoreFoundation)** | survived | was SURVIVED — R-B1 closed |
| B11 | Darwin notification name (Router) | **DIED (CoreFoundation)** | survived | was SURVIVED — closed |
| X14 | `CFShow(typed)` (Router) | **DIED (CoreFoundation)** | survived | was SURVIVED — closed |
| X19 | `CFStreamCreatePairWithSocketToHost` | **DIED (CoreFoundation)** | died | was SURVIVED(decl) |
| X15 | runtime `LocalizedStringKey(_:)` link (ContentView) | **DIED (rule)** | survived | was SURVIVED — R-M1 closed |
| X04 | `URLCredential` `.synchronizable` (Router) | **DIED (rule)** | survived | was SURVIVED — R-M2 closed |
| X10 | `HTTPCookieStorage.setCookie` (Router) | **DIED (rule)** | survived | was SURVIVED — R-M2 closed |
| X05 | `NSException(reason: typed).raise()` | **DIED (rule)** | survived | was SURVIVED — closed |
| X06 | `try!` on an error carrying text | SURVIVED | survived | unchanged; documented |
| X02 | `Stream.getStreamsToHost` (FrontDoor) | **DIED (network)** | died | was SURVIVED(decl) — closed |
| X03 | `Stream.getStreamsToHost` (Router) | DIED (network) | died | now "network", not "file system" |
| X07 | `StringProtocol.write(to:)` (Detail) | **DIED (rule)** | died | was SURVIVED(decl) — closed |
| X08 | `FileWrapper.write(to:)` (Detail) | **DIED (rule)** | died | was SURVIVED(decl) — closed |
| X09 | iCloud ubiquity container write (FrontDoor) | **DIED (rule)** | died | was SURVIVED(decl) — closed |
| X18 | `InputStream(data:)` in memory (Detail) | SURVIVED (FP fixed) | died | was FALSE POSITIVE — fixed |
| B01/B04/B05/B08/B09/B13/B14/B15/B16/B23/B27/B28/B32 | original survivors | DIED (compile or rule) | — | unchanged |
| B10 | markdown link literal (ContentView) | SURVIVED, recorded | died | unchanged |
| B19 | relay in EngineClient, called from Detail | SURVIVED, recorded | survived | unchanged |
| B22 | `.textSelection(.enabled)` (ContentView) | SURVIVED, recorded | survived | unchanged |
| B31 | `/tmp` write (FrontDoor) | SURVIVED, recorded | died | unchanged |
| X11/X12/X13/X16/X17/X20/X23 | assert/precond, NSData/NSDict write, AsyncStream, NSClassFromString | as round 2 (DIED or SURVIVED-recorded) | — | unchanged |
| FP3 | `Bundle` URL + `appendingPathComponent` | false positive, recorded | passes | unchanged |
| X21/X22 | type error under `#if DEBUG` / device-only `#if` | DIED (compile) | — | unchanged |
| FP-text-plain-literal | `Text("Welcome…")` (ContentView) | SURVIVED (correct) | — | new probe — no LSK FP |
| FP-text-key/comment, Section header | `Text("k")`, `Text(_,comment:)`, `Section(header:)` | SURVIVED (correct) | — | new probe — no LSK FP |
| FP-lsk-literal | `let k: LocalizedStringKey = "Hello"` | SURVIVED (correct) | — | new probe — literal allowed |
| FP-text-interp / verbatim | `Text("Count \(n)")`, `Text(verbatim:)` | SURVIVED (correct) | — | new probe |
| FP-date/json/localized/task | `Date().formatted`, `JSONDecoder`, `String(localized:)`, `Task.sleep` | SURVIVED (correct) | — | new probe |
| FP-cg-geometry / FP-cgrect | `CGPoint`/`CGSize`/`CGRect` (ContentView/Detail) | FALSE POSITIVE (CoreGraphics) | — | new probe — NIT 1 |

**Manifest static-half probes (`_guarded_tests` / `FUNC`, run directly):**

| case | guarded lines | correct? |
|---|---|---|
| S1 `#if false` at 4-space indent around a test | [flagged] | yes |
| S2 `private func test` | not matched by `FUNC` → reads MISSING | yes |
| `#if` inside a test body (`canImport`) | [] | yes (no FP) |
| nested `#if…#if…#endif…#endif` guard | [flagged] | yes |
| `#elseif`/`#else` branch guard | [flagged] | yes |
| `#if` left open to EOF | [flagged] | yes |
| `//`- and `/* */`-commented `#if` | [] | yes (no FP) |
| test after a closed `#if` region | [] | yes (no FP) |
| `#if` token mid-line inside a string | [] | yes (no FP) |
| lone `#if` line inside a `"""` multiline string | [flagged] | over-flags, errs SAFE — NIT 2 |

**Swift-test mutants (`make swift-test` on the `sw` copy, static half synced to this tree):**

| id | static | make swift-test |
|---|---|---|
| N6 (`throw XCTSkip`) | passes | DIED (`1 test skipped`) |
| N7 (`#if false`, col 0) | DIED | DIED (261<262) |
| S1 (`#if false`, col 4) | **DIED** | DIED (261<262) |
| S2 (`private func test`) | **DIED** | DIED (261<262) |
| N10 (`/* */` around a test) | DIED | DIED (261<262) |
| M1 (`assistant`/`vision` back to 059b519) | passes | DIED (`FrontDoorTests.swift:394`) |

All swift-test mutant files were restored byte-identical to the repository (asserted by sha256).

## Record corrections checked against the facts

- W-111 (R-M3 paragraph): now says the rule is content-based — "no `func test…()` between any `#if`
  and its `#endif`, at any indentation, including an `#if` left open" and "a private test reads as
  missing; both mutants, and one with no `#endif`, re-run red." Matches my S1/S2/open-`#if` runs.
  **Correct.**
- W-122 (re-review paragraph): records R-B1 (CoreFoundation symbol by symbol, `CGFloat` only),
  R-M1, R-M2, `NSException.raise`, `Stream.getStreamsToHost`, `StringProtocol.write(to:)`,
  `FileWrapper`, the iCloud Drive container as fixed ("13 mutants re-run and all die"), notes
  `InputStream(data:)` passes again, and documents `try!` as having no declaration to refuse. Every
  claim matches a run above. **Correct.**
- `m16-router-floor-measurement.md` `vision` sentence: "four of six changed" — confirmed against the
  `059b519`→working-tree diff. **Correct** (round-2 "five of six" fixed).

## What I did not check

- Nothing on an iPhone. "Compiles" means the gate's own `swiftc -typecheck` for the four
  configurations; I did not run any exfiltration attempt on a device, did not render the R-M1 link,
  and did not repeat the round-1 seat's macOS CFSocket send (the mutant dies at the gate now, so the
  runtime behaviour is moot).
- `note.txt` and `docs/plans/m16-wave-1-close.md` — the author was editing both; excluded by
  instruction.
- Not the `.xcodeproj` build, and not the Python suite beyond the gate, the two manifest tests, the
  text gate, and `check_records` on this file. In `docs/warnings.ledger.md` I checked only the
  W-111 R-M3 sentence and the W-122 re-review paragraph against runs, and in
  `m16-router-floor-measurement.md` only the `vision` count.
- I did not construct a new CoreFoundation-free network path beyond re-running the re-review's set
  and the false-positive probes above.
