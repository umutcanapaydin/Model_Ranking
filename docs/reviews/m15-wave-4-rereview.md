---
record_type: review
id: m15-wave-4-rereview
status: ratified
seat: independent
date: 2026-09-22
---

# M15-W4 fix round: independent re-review (Code-Reviewer + Tester)

**Scope:** only the uncommitted fix round on top of `8640202`. That means the D-126 egress gate in
`tests/unit/test_router_hints.py`, the `test_categories.py`, `test_arena_client.py` and
`test_calibrate_board.py` changes, `ELO_BAND` in `src/app/clients/arena.py`, the parametrized live
contract test, and the records D-150 (amendment), W-111, W-113, W-117..W-121, `m15-wave-3-close.md`
and `m15-category-calibration.md`. Policy was read from `855b44a:subagent-profiles/{Code-Reviewer,Tester}.md`.
The fresh-context assertion: I wrote none of this code. The author family and reviewer family are
the same (Claude). No second model family was available, so this is a fallback.

**Method:** all work ran in a private rsync copy. I tested bypasses by dropping one extra
`ios/ModelRanking/ZZMutant.swift` into the client folder and running the gate test (`-k gap_register`).
I compiled each one for the app's real platform with
`xcrun swiftc -typecheck -sdk iPhoneSimulator26.5.sdk -target arm64-apple-ios18.0-simulator`.
The Python mutants were applied by script and restored, and I checked byte identity against the
real tree after every one. I set `PYTHONDONTWRITEBYTECODE=1` and cleared `__pycache__`. Without
that, a same-size mutant written and restored within one second left a stale `.pyc`, which gave a
false red. The suites in the copy are green: pytest 956 passed / 15 skipped, `swift test` 258/0,
and the live contract tests (`RUN_CONTRACT_TESTS=1`) 5 passed.

## Verdict: **BLOCKING**: 2 BLOCKING / 3 MAJOR / 3 MINOR / 2 NIT

The Python half of the fix round is sound. All 12 mutants I aimed at W-113, W-117, the new
threshold pin, `ELO_BAND` and the floors die except one (a widened band, MINOR-3). The records match
the code. The egress gate is much stronger than before: the prior seat's N01, N04, N05, N07 and N08
re-run and die. It is still a denylist over spellings, though, and **27 bypasses compiled for iOS
and passed the gate**. Two of them are ordinary features a future wave could write without meaning
any harm.

## Findings

**BLOCKING-1: A markdown link in `Text` sends the typed question to the web, and nothing in the gate names it.**
`tests/unit/test_router_hints.py:306` (`EGRESS`). Scenario (B04, compiles, gate PASS): a
"not answered here? search the web" hint writes
`Text((try? AttributedString(markdown: "[Search the web](https://duckduckgo.com/?q=\(question…))")) ?? "")`.
SwiftUI renders the link as tappable and opens it through the default `openURL` action, so the
reader's words go in a URL to a third party. No `URL(`, `Link(`, `openURL` or `.init(` appears.
`Text("…[Search](https://…?q=\(question))")` (B23) also compiles and passes. I did not verify at
runtime whether a `LocalizedStringKey` with interpolation turns into a link. The same shape through a
`.strings` file is also unread by the gate: it checks only that `.strings` files exist, not what
they say.
*Remedy:* refuse `https?://` string literals and `markdown:` (and `AttributedString` `.link`)
outside `EngineClient.swift`, and scan `.strings`/`.json` for URL schemes. Better, see MAJOR-1's remedy.

**BLOCKING-2: System hand-off surfaces that the ban list does not name.**
The author refused `ShareLink`, `UIActivityViewController` and the pasteboard as egress. These
equivalents pass the gate and compile for iOS without importing anything off the allowlist,
because SwiftUI re-exports UIKit:
- B06: `.userActivity("…") { $0.title = question; $0.userInfo = ["q": question]; $0.isEligibleForHandoff/Search/Prediction = true }`.
  This is Handoff to other devices and a donation to Spotlight and Siri. It is a plausible
  "continue on Mac" or "Siri suggestions" feature.
- B05c: `.fileExporter(isPresented:item: question, defaultFilename:)` (a `String` is `Transferable`,
  so no `UniformTypeIdentifiers` import is needed). This writes to Files or iCloud Drive. It is a
  plausible "save my question" feature.
- B07 `.draggable(question)`, B21 `UIPrintInteractionController`, B26 `UIDocumentPickerViewController(forExporting:)`.

*Remedy:* add `userActivity`, `NSUserActivity`, `fileExporter`, `fileMover`, `draggable`, `onDrag`,
`NSItemProvider`, `Transferable`, `UIPrint`, `UIDocument` and `\bUI[A-Z]` (UIKit has no business in
this client) to `EGRESS`, or move to the allowlist in MAJOR-1.

**MAJOR-1: "URL construction of any spelling is refused" (W-121) is false. URLs can be made and read without a banned token.**
`test_router_hints.py:306-315`. The patterns need a specific following character (`URL\s*\(`,
`contentsOf\s*:`, `write\s*\(`). A backtick, a comment between tokens, a type alias or an inferred
type defeats them. All of the following compile and pass:
- B01 ``Data(`contentsOf`: `URL`(string: …+t)!)``
- B02 `Data(contentsOf/**/: URL/**/(string:…))`
- B03 `typealias Address = URL`
- B13 `CFURLCreateWithString(…) as URL`
- B22b a `Decodable` struct with a `URL` field
- B27 `config.help.appending(queryItems: [URLQueryItem(…)]).lines`. `URL.lines` and `resourceBytes`
  fetch over HTTP and are not refused. B27 is the plausible one: a help link read from a bundled
  config.

With backticks, the same trick puts a second `` Data(`contentsOf`: url) `` into `FrontDoor.save()`.
That is the prior seat's N04 again, and the exact-count rule does not see it.
*Remedy:* stop matching spellings. Typecheck the client with `swiftc -dump-ast` (or read the index
store) and check the **referenced declarations** (USRs) against an allowlist of Foundation and
SwiftUI symbols. That approach is immune to backticks, comments, aliases and inference. Until then,
remove backticks and comments before matching (both are lexically trivial, unlike the old stripper),
and add `\bURL\b` itself, `\.lines\b` and `resourceBytes`.

**MAJOR-2: Crash messages carry typed text off the device.**
B08: `fatalError("could not route \(question)")` or `precondition(…, "…\(question)")` compiles and
passes. The message is written into the crash report, which is uploaded to the developer when the
reader shares analytics. The gate refuses `print`, `dump` and `NSLog` for this reason, and this is
the more natural spelling in Engine code.
*Remedy:* refuse `fatalError|precondition|preconditionFailure|assert|assertionFailure` whose message
contains `\(`, or all of them outside tests.

**MAJOR-3: W-121 is recorded FIXED, and its stated residual is narrower than what it leaves open.**
`docs/warnings.ledger.md:167` says that URL construction "of any spelling" is refused and that the
residual is "a renamed binding or a shadowed `url`". BLOCKING-1/2 and MAJOR-1 contradict both
claims. This is the project's most-recorded defect: a record stating more than the code does.
*Remedy:* reopen W-121, or split it into a new row, with this table as its evidence. Keep "FIXED"
only for the 23 prior mutants, which do die.

**MINOR-1: Deliberate bypasses. A text gate cannot stop a determined author.**
All of these compile and pass:
- B10 ``import `Network` `` (the `IMPORT` regex at `:342` does not accept a backticked module name,
  so the import is never checked; cheap to fix)
- B11 `NetService` TXT-record broadcast
- B12 BSD `socket`/`connect`/`send` (Darwin, re-exported by Foundation)
- B17 `fopen`/`fputs`
- B18 `NSKeyedArchiver.archiveRootObject(toFile:)`
- B16 `` `write`(toFile:) ``
- B19 `CFPreferencesSetAppValue` (which is `UserDefaults` under another name)
- B20 `SecItemAdd` with `kSecAttrSynchronizable` (iCloud Keychain)
- B24b `NSClassFromString("NSURLSession")`
- B28 `NSMutableURLRequest` (the `\b` in `\bURLRequest\b` misses `NSMutable…`)
- B14 `typealias Remembered = AppStorage` (a second stored value; the count at `:377` misses it)
- B09 `fputs(…, stderr)`
- B15 `isExcludedFromBackup = true ? false : true` (satisfies the count at `:379`; the Swift on-disk
  test backstops this for the register's own file)

`dlopen` and `@_silgen_name` are the same class; I reasoned about them and did not run them.
*Remedy:* MAJOR-1's symbol allowlist closes all of these except the C-level ones. Also accept a
backticked module in `IMPORT`.

**MINOR-2: False positives on legitimate code and prose. Accepted in principle, but broader than the comment admits.**
Each of these fails the gate:
- F01 `self.init(a:)` (and any `super.init(`), and F02 `.padding(.init(top:…))`. `\.init\s*\(` bans
  common Swift idioms.
- F03 a doc comment ending "…its own URL."
- F04 "written (atomically) … we write (once)"
- F07 the UI string "the fine print (below)"
- F06 a comment "The views import this file", which fails with the confusing message "imports `this`".

The gate's comment names only "a comment may not name a banned API". The prose cases will cost
future authors time.
*Remedy:* the symbol-level check removes all of them. Short of that, match `import` only at the
start of a declaration (with comments stripped, per MAJOR-1), and say in the failure message that
comments and strings are scanned.

**MINOR-3: `ELO_BAND`'s bounds are not pinned.**
`src/app/clients/arena.py:100`. Widening the band to `(0.0, 1e6)` survives the whole suite (P12),
because the test at `tests/unit/test_arena_client.py:331` probes only `1e308` and `-5.0`.
*Remedy:* add a finite rating just above 5000 (for example 5001.0) to the refused list.

**NIT-1:** `src/app/workflows/categories.py:290`. The continuation line of the `value_window`
comment starts at column 0 inside the dict literal.
**NIT-2:** `tests/integration/test_arena_openrouter_contract.py:50` ends in a blank line.
K.9, which predates this round: in `arena.py:89-92` the size comments for `vision` and `search`
sit one entry below the boards they describe.

## Mutant / bypass table

| id | attempt | target file | gate | compiles (iOS) |
|---|---|---|---|---|
| C01 | control: `URLSession.shared` | ZZMutant.swift | DIED | yes |
| N01/N05/N07/N08 | prior seat's mutants re-run | ZZMutant.swift | DIED | yes |
| N04 | second `Data(contentsOf: url)` in `save()` | FrontDoor.swift | DIED (exact count) | n/a |
| B01 | ``Data(`contentsOf`: `URL`(string:)!)`` | ZZMutant.swift | **SURVIVED** | yes |
| B02 | `contentsOf/**/:` + `URL/**/(` | ZZMutant.swift | **SURVIVED** | yes |
| B03 | `typealias Address = URL` + backticked read | ZZMutant.swift | **SURVIVED** | yes |
| B04 | `AttributedString(markdown:)` link in `Text` | ZZMutant.swift | **SURVIVED** | yes |
| B05 | `.fileExporter` + `import UniformTypeIdentifiers` | ZZMutant.swift | DIED (import) | yes |
| B05c | `.fileExporter(item: question)` | ZZMutant.swift | **SURVIVED** | yes |
| B06 | `.userActivity` with the question | ZZMutant.swift | **SURVIVED** | yes |
| B07 | `.draggable(question)` | ZZMutant.swift | **SURVIVED** | yes |
| B08 | `fatalError` / `precondition` with the question | ZZMutant.swift | **SURVIVED** | yes |
| B09 | `fputs(…, stderr)`, `puts` | ZZMutant.swift | **SURVIVED** | yes |
| B10 | ``import `Network` `` | ZZMutant.swift | **SURVIVED** | yes |
| B11 | `NetService` TXT broadcast | ZZMutant.swift | **SURVIVED** | yes |
| B12 | BSD socket connect/send | ZZMutant.swift | **SURVIVED** | yes |
| B13 | `CFURLCreateWithString … as URL` | ZZMutant.swift | **SURVIVED** | yes |
| B14 | `typealias Remembered = AppStorage` | ZZMutant.swift | **SURVIVED** | yes |
| B15 | `isExcludedFromBackup = true ? false : true` | ZZMutant.swift | **SURVIVED** | yes |
| B16 | `` `write`(toFile:) `` into Documents | ZZMutant.swift | **SURVIVED** | yes |
| B17 | `fopen`/`fputs` into Documents | ZZMutant.swift | **SURVIVED** | yes |
| B18 | `NSKeyedArchiver.archiveRootObject(toFile:)` | ZZMutant.swift | **SURVIVED** | yes (deprecated) |
| B19 | `CFPreferencesSetAppValue` | ZZMutant.swift | **SURVIVED** | yes |
| B20 | `SecItemAdd`, synchronizable | ZZMutant.swift | **SURVIVED** | yes |
| B21 | `UIPrintInteractionController` | ZZMutant.swift | **SURVIVED** | yes |
| B22 | Decodable `URL` + `.init(name:value:)` | ZZMutant.swift | DIED (`.init(`) | yes |
| B22b | Decodable `URL` + `URLQueryItem(…)` + backticked read | ZZMutant.swift | **SURVIVED** | yes |
| B23 | markdown link in a `Text` literal | ZZMutant.swift | **SURVIVED** | yes |
| B24 | `NSClassFromString("NS" + "URLSession")` | ZZMutant.swift | DIED | yes |
| B24b | `NSClassFromString("NSURLSession")` | ZZMutant.swift | **SURVIVED** | yes |
| B25 | `\EnvironmentValues.openURL` key path | ZZMutant.swift | DIED | yes |
| B26 | `UIDocumentPickerViewController(forExporting:)` | ZZMutant.swift | **SURVIVED** | yes |
| B27 | Decodable `URL` `.appending(queryItems:).lines` | ZZMutant.swift | **SURVIVED** | yes |
| B28 | `NSMutableURLRequest(url:)` with a body | ZZMutant.swift | **SURVIVED** | yes |
| F01-F07 | legitimate code/prose (false-positive probes) | ZZMutant.swift | F01-04, F06, F07 FAILED; F05 passed | yes |
| P01 | `vision.primary_source = "arena"` | categories.py | DIED | n/a |
| P02 | `vision.primary_benchmark = "Arena text"` (W3 B-1) | categories.py | DIED | n/a |
| P03/P04 | vision `close_call` 8.1; s_f window 17.0 | categories.py | DIED | n/a |
| P05/P06 | `ELO_BAND` check removed; band `(-1e9, 1e300)` | arena.py | DIED | n/a |
| P07/P08 | `main()` counts names; pairs names (W4 MAJOR-3) | calibrate_board.py | DIED | n/a |
| P09 | worst name per model | calibrate_board.py | DIED | n/a |
| P10 | `vision` floor 60→20 (W3 B-2) | arena.py | DIED | n/a |
| P11 | vision source AND benchmark both moved to text | categories.py | DIED | n/a |
| P12 | `ELO_BAND = (0.0, 1e6)` | arena.py | **SURVIVED** | n/a |

## Records checked against code

- The D-150 amendment, W-111 (corrected) and the W3 close dispositions match the tree.
- W-113 and the calibration correction (41/156/7.8/31.2; 25/44/6.5/25.9; 24/39/4.9/19.5) match
  `categories.py` and `PINNED_M15_THRESHOLDS`.
- W-117's "both seat mutants re-run and die" holds (P02, P10).
- W-121 overclaims; see MAJOR-3.

## What I did not check

- Whether the bypasses behave as described at runtime on a device. I typechecked them only. The
  exception is B04, where the markdown-link behaviour is documented SwiftUI behaviour.
- `dlopen`, `@_silgen_name` and `perform(Selector)` (reasoned about, not run).
- Whether a `.swift` file inside an `.xcassets` folder, which the gate skips, would be compiled.
- A full `xcodebuild` of the app target.
- The live contract test beyond the one run.
- The D-150 clause 2 substance.
- Files outside this fix round (EXPERIENCE.md, process-log.md, m16-plan.md, the retrospective).
