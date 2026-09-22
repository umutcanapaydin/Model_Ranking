---
record_type: review
id: m16-wave-1-review
status: ratified
seat: independent
date: 2026-09-22
---
# M16-W1 — independent review: three ADRs, two `/v1` fields, two gates and a re-measurement

**Seat:** independent (Code-Reviewer + Tester; authored none of this wave). **Base:** 059b519, all
of it uncommitted; policy read from `855b44a` only. Worked in copies under `/private/tmp`; the
repository tree was not edited except for this file. Every mutant was applied by script, reverted,
and checked byte-identical against the copy of origin.

## Scope

D-151/D-152/D-153; `src/app/adapter/main.py` `categories()`; `src/app/workflows/categories.py`;
`tests/unit/test_uncertainty_contract.py`; `ios/EngineTests/test-manifest.txt` + `Makefile`
`swift-test` + `tests/unit/test_swift_test_manifest.py`; `scripts/client_decl_gate.py` +
`make check`; `Router.swift` examples, `FrontDoorTests.swift`, `scripts/router_probe/*`,
`docs/reviews/m16-router-floor-measurement.md`; ledger rows W-111/W-118/W-122/W-123; `AGENTS.md`
K.8; `docs/plans/m16-plan.md`; `note.txt`.

## Verdict

**BLOCKING — 3 BLOCKING, 4 MAJOR, 10 MINOR, 2 NIT.**

All three BLOCKING findings are in `scripts/client_decl_gate.py`, the gate this wave shipped to
close W-122. Each is a way for the reader's typed question to leave the device from a file under
`ios/ModelRanking` with `client-decls` printing PASS, and each compiles for a target the app ships.
The rest of the wave is in good shape: the router measurement record reproduces number for number,
the `/v1` fields kill 9 of 10 mutants, and the manifest gate kills every deletion and rename I
tried.

Suite state on my copy: `pytest` 960 passed / 15 skipped; `swift test` 261 passed; `ruff`, `mypy`,
`check_records` (126 records), `wave_check_all`, `conformance_gate` all green; `client-decls` PASS
(1472 declarations in 11 files) in 2.9s.

## Findings

### BLOCKING

**B-1 — `scripts/client_decl_gate.py:141-162,238-256`: the gate prints PASS on a client that does
not compile, and never checks that it examined every file.**
`dump_ast()` returns `result.stderr` and ignores `result.returncode`; `main()` fails only when
`found` is *completely* empty. `swiftc -dump-ast` stops dumping after the file that errors, so a
single type error silently removes every later file from the check.
*Failure scenario, measured:* a type error in `Engine/Router.swift` plus
`UIPasteboard.general.string = typed` in `ModelRankingApp.swift` →
`client-decls PASS: 1336 resolved declaration(s) in 8 client file(s)` (mutants B26, B27). The
shippable form is B32: put the error inside `#if targetEnvironment(simulator)`. The gate compiles
only `arm64-apple-ios18.0-simulator`, so it truncates; `arm64-apple-ios18.0` — the device build —
compiles cleanly with the pasteboard write in it. Verified: gate rc 0, device typecheck rc 0.
*Remedy:* fail when `result.returncode != 0`, and assert
`set(found) == {p.name for p in CLIENT.rglob("*.swift")}` before judging anything.

**B-2 — `scripts/client_decl_gate.py:36`: one configuration is type-checked, so `#if`-guarded code
ships unchecked.**
*Failure scenario, measured:* `URLSession` exfiltration of the typed question inside
`#if !targetEnvironment(simulator)` → gate PASS, device target compiles (B14). The same inside
`#if DEBUG` → gate PASS, compiles with `-D DEBUG`, i.e. the Xcode Debug configuration the owner
runs on his own phone (B13). No compile error is needed; the gate simply never sees the branch.
*Remedy:* dump for both targets and both `DEBUG` states, or make an `#if` condition the gate does
not evaluate a failure in itself.

**B-3 — `scripts/client_decl_gate.py:52`: `Darwin` is allowlisted whole, so every client file has
BSD sockets and `dlopen`.**
*Failure scenario, measured, all compiling for the simulator and all surviving:* raw
`socket`/`connect`/`send` of the typed question from `Router.swift` (B01; resolves `Darwin.socket`,
`Darwin.send`), DNS exfiltration via `getaddrinfo` (B15), `dlopen`+`dlsym` calling `NSLog` by a
computed string (B16). "EngineClient.swift is the one door (D-126)" is not what this gate enforces.
The near-misses are accidental, not designed: `fputs`, `write` and `pwrite` die only because they
happen to resolve in `_DarwinFoundation2`/`_DarwinFoundation3`, which are absent from `MODULES`
while `_DarwinFoundation1` is present.
*Remedy:* delete `"Darwin"` from `MODULES`. I measured what the shipping client actually resolves
in that family: `['_DarwinFoundation1.pow']` — nothing else. The removal costs no false positives.

### MAJOR

**M-1 — the W-118 fix has no regression test.** `ios/ModelRanking/Engine/Router.swift:157-196` is
the only shipping-code change in this wave. I reverted the `assistant` and `vision` example lists to
059b519 in my copy (verified byte-equal to the 059b519 extraction) and ran the suite:
**261 tests, 0 failures.** The three new tests in `ios/EngineTests/FrontDoorTests.swift:344-401`
pass on both trees, so none of them is a regression test for the change. W-118's ledger row and
`docs/plans/m16-plan.md` both present those three tests as the fix's proof; they prove the m-3 and
m-4 gaps, not the fix. *Remedy:* pin two or three of the off-topic questions that moved
(`what is the capital of france` was `vision`-class before, `how do i cook rice`, `tell me a joke`)
as real-router assertions, so putting the old examples back turns `make check` red.

**M-2 — `/v1/categories` has no frozen key-set test (K.9 gap-fill).**
`tests/unit/test_api_v1.py:583-587` asserts ids only; `ENVELOPE_KEYS`/`ANSWER_KEYS`/`PICK_KEYS`
cover `/v1/recommendations`. D-152 clause 1 claims "A field is added; nothing changes shape (K.8)",
and `test_the_recommendations_route_did_not_gain_a_field` exists precisely to make that kind of
claim mechanical — but for `/v1/categories` nothing does. A fourth field could be added with no ADR
and every gate green, which is the W-112 class this ADR was written to close.

**M-3 — a test can be disabled with `make check` fully green: `XCTSkip`.**
Measured: `throw XCTSkip("disabled")` at the top of
`UncertaintyTests.testEachPositionIsTheRangeTheMarginCannotNarrow` →
`Executed 261 tests, with 1 test skipped and 0 failures`. `Makefile:161-167` reads only the
`Executed N` number, so `n = 261 >= floor 261`; `--list-tests` still lists the test, so the
`Makefile:168-175` diff matches; `test_swift_test_manifest.py` still passes. D-150 clause 1 exists
for "a test that exists and is not protected"; skip is the remaining door.
*Remedy:* fail the recipe when the Executed line reports a skip, or subtract skips from `n`.

**M-4 — in every lane without a Swift toolchain, only the static half runs, and it cannot see a
disabled test.** `.github/workflows/ci.yml` has only `ubuntu-latest` jobs, so `swift-test` and
`client-decls` both take their SKIPPED branch there and the whole privacy gate plus the real
manifest diff are owner-machine-only. Measured in that lane: wrapping a test in `#if false` (N7) or
in `/* */` (N10) leaves `test_swift_test_manifest.py` green, because `CLASS`/`FUNC` in
`tests/unit/test_swift_test_manifest.py:26-27` match declarations inside inactive and commented
regions. On macOS both die (discovered count falls to 260). This is the W-108 class again and is
worth a ledger row rather than a fix in this wave.

### MINOR

- `scripts/client_decl_gate.py:203-222` scopes by **file**, never by data, and neither the
  docstring nor the W-122 row says so. Survivors, all compiling: a `main`-module relay declared in
  `EngineClient.swift` and called from `Detail.swift` (B19 — `main` skips the capability rules at
  line 231); an App Group shared-container write and a `/tmp` write from `FrontDoor.swift`
  (B08, B31).
- `scripts/client_decl_gate.py:72-75`: `FILESYSTEM` matches `String.write`/`Data.write` but not the
  Objective-C twins or the stream APIs. Survivors from `Detail.swift`, each writing the typed
  question to an arbitrary path: `NSString.write(toFile:)` (B04), `NSData.write(toFile:)` (B28),
  `OutputStream(toFileAtPath:append:)` (B05).
- Further survivors worth a rule: `@SceneStorage` holding reader text (B23 — not `@AppStorage`, and
  state restoration writes it to disk), `fatalError("…\(typed)")` into the crash report (B09),
  `.textSelection(.enabled)` into the system pasteboard (B22).
- `docs/warnings.ledger.md` W-122 lists "a markdown link" among the 18 attempts that die in THIS
  gate. Measured: `Text("[report](https://…?q=\(typed))")` in `ContentView.swift` survives
  `client-decls` (B10) — the `AttributedString` entry at line 90 does not catch a
  `LocalizedStringKey` literal. It dies in the text gate. The row credits this gate with a kill it
  does not make.
- False positive: `Bundle.main.bundleURL.appendingPathComponent("about.txt")` in `Detail.swift`
  fails the gate (FP3; `PATH_BUILDING`, line 81, is file-scoped), so ordinary read-only
  bundle-resource code is blocked. `NavigationLink`, `Text(verbatim:)` and date/number formatting
  all pass, so the surface is narrow but real.
- D-150 clause 1 and the W-111 row say the manifest "lists all 258 tests". It lists **261**
  (`wc -l` = 261, `swift test --list-tests | sort` = 261, byte-identical to the manifest).
- `note.txt` was edited this wave and four of its lines still contradict it: `:3` "awaits the
  owner's sign-off (D-150 clause 2)" two lines above the new line saying he signed; `:4` "Swift
  258"; `:11` "W-111..W-122" with W-123 added; `:24` M16 gives the app an **"update now"** button —
  the control D-151 clause 3, accepted in this same wave, removes.
- `docs/reviews/m16-router-floor-measurement.md:44` quotes `"describe the photo i attached"` as a
  new `vision` example; the shipped one is the unchanged `"describe this photo"`. Lines 39-42 say
  the three replaced `assistant` examples "were all 'write/rewrite this text for me'"; two were
  `"give me advice on asking for a raise"` and `"chat with me about my weekend plans"`.
- Same record, lines 29-33: "Four labels in **the tuning set** were corrected" — the table at line
  20 calls `probe_questions.json` the tuning set; the four are in `offtopic_questions.json`. All
  three new probe sets are untracked files with no before-state, so the relabelling cannot be
  verified. I checked it by sensitivity: forcing every off-topic tuning label to
  `assistant|everyday~` gives 3/16 → 7/16, so the reported 6/16 → 11/16 is not its artefact.
- `offtopic_heldout_questions.json` is not independent in shape from the set tuned against:
  `"how do i remove a coffee stain"` against the new example `"how do i get red wine out of a
  carpet"`, `"good morning"`/`"thanks"` against `"hi can you help me with something"`,
  `"who wrote the odyssey"` against `"what is the tallest mountain in the world"`. Line 24 calls it
  "the honest measure of the off-topic fix"; it is a within-distribution one. W-123 concedes the
  point for M16-W4; the record overstates it here.
- Mutant P8 survives: `price_excludes: str | None = ""` makes every non-search surface publish `""`
  where D-153 clause 2 says the field is absent; the new test filters on truthiness.

### NIT

- `scripts/client_decl_gate.py:91-96` and `111-116`: six `FORBIDDEN` entries are listed twice.
- An emptied test body survives both manifest gates (N5) — inherent to a name list; one sentence in
  the docstring, not a change.

### What looks right

- **The measurement record reproduces exactly.** I rebuilt `probe.swift`, extracted the examples at
  059b519 and at HEAD, and ran all five sets at FLOOR 0.15 and 0.20: 21/21, 18/22, 12/16,
  6/16 → 11/16, 3/16 → 8/16, identical at both floors — every cell of the table at line 53. The
  floor claim holds: lowest correct route 0.236 (record 0.232), nonsense 0.164–0.402 (record
  0.161–0.395), nothing below 0.15. W-123's four named nonsense misses reproduce within 0.006.
- **The two `/v1` fields are pinned by their own tests:** 9 of 10 mutants die, including the one
  that matters (`min_quality` served from `score_anchor`).
- **The manifest gate kills every deletion and rename I tried**, and the text gate still catches a
  second `@AppStorage` (P10), so the one survival the W-122 row accepts is covered as stated.
- **The client still decodes `/v1/categories`:** `ios/ModelRanking/Engine/Models.swift:41-71` has
  explicit `CodingKeys` and no strict unknown-key handling. `docs/plans/m16-plan.md:66` puts the
  screens in W2, so D-152/D-153 clause 3 and all of D-151 are not claims about this wave.

## Mutants and bypasses

`compiles?` = `swiftc -typecheck` for `arm64-apple-ios18.0-simulator` unless noted.

| id | attempt | target | result | compiles? |
|---|---|---|---|---|
| B01 | raw `socket`/`connect`/`send` | Router.swift | **SURVIVED** | yes |
| B04 | `NSString.write(toFile:)` | Detail.swift | **SURVIVED** | yes |
| B05 | `OutputStream(toFileAtPath:)` | Detail.swift | **SURVIVED** | yes |
| B03, B17, B06, B07, B18 | `fputs(stderr)` / raw `write(2)` (die only via `_DarwinFoundation2/3`); a second `EngineClient.swift` or `FrontDoor.swift` by basename (die on duplicate filename); leak + type error in one file | various | DIED | mixed |
| B08 | App Group container write | FrontDoor.swift | **SURVIVED** | yes |
| B09 | `fatalError("\(typed)")` | Router.swift | **SURVIVED** | yes |
| B10 | markdown link in `LocalizedStringKey` | ContentView.swift | **SURVIVED** | yes |
| B11 | `CFNotificationCenter` Darwin notify | Router.swift | **SURVIVED** | yes |
| B12a | second `@AppStorage` (known/accepted) | ContentView.swift | SURVIVED (text gate kills) | yes |
| B13 | `URLSession` inside `#if DEBUG` | Router.swift | **SURVIVED** | yes, with `-D DEBUG` |
| B14 | `URLSession` inside `#if !targetEnvironment(simulator)` | Router.swift | **SURVIVED** | yes, device target |
| B15 | `getaddrinfo` DNS exfiltration | Router.swift | **SURVIVED** | yes |
| B16 | `dlopen`+`dlsym` → `NSLog` | Router.swift | **SURVIVED** | yes |
| B19 | `main`-module relay across the file boundary | EngineClient+Detail | **SURVIVED** | yes |
| B22 | `.textSelection(.enabled)` | ContentView.swift | **SURVIVED** | yes |
| B23 | `@SceneStorage` holding reader text | ContentView.swift | **SURVIVED** | yes |
| B27 | type error + `UIPasteboard` in ModelRankingApp.swift | Router+App | **SURVIVED** (8/11 files read) | no |
| B28 | `NSData.write(toFile:)` | Detail.swift | **SURVIVED** | yes |
| B12b, B20, B21, B24, B25, B29, B30 | controls: `@AppStorage` in the wrong file, `UIPasteboard`, `import Network`, `@Environment(\.openURL)`, a leak in `Scores.swift`, POSIX `open`/`pwrite`, `NSUserDefaults` | various | all DIED | yes except B25/B30 |
| B31 | `/tmp` write from the allowed file | FrontDoor.swift | **SURVIVED** | yes |
| B32 | simulator-only error + `UIPasteboard` in App | Router+App | **SURVIVED** | **yes, device target** |
| FP1, FP2, FP4 | `.formatted(.number.attributed)`, `NavigationLink`, date formatting + `Text(verbatim:)` | ordinary SwiftUI | pass — no false positive | yes |
| FP3 | `Bundle` URL + `appendingPathComponent` | Detail.swift | **FALSE POSITIVE** | yes |
| N1-N4, N9, N11 | delete a test / delete its manifest line / rename the test / rename the owning class / `//`-comment it / duplicate a manifest line | manifest gate | all DIED | — |
| N5 | empty the test body | manifest gate | SURVIVED (name-based, inherent) | — |
| N6 | `throw XCTSkip` | manifest gate + `swift-test` | **SURVIVED BOTH** | — |
| N7, N10 | wrap the test in `#if false` / in `/* */` | manifest gate | SURVIVED static half, DIED on macOS | — |
| P1-P4 | `min_quality` from `score_anchor` / rounded / key dropped / key renamed | `/v1/categories` | all DIED | — |
| P5-P7, P9 | `price_excludes` dropped from one surface / defaulted everywhere / `"search call"` / served `None` | categories | all DIED | — |
| P8 | `price_excludes` default `""` instead of `None` | categories.py | **SURVIVED** | — |
| P10 | second `@AppStorage` vs the text gate | ContentView.swift | DIED | — |

## What I did not check

- Not `make check` end to end: its targets depend on `install`, which would have re-pointed the
  repository's virtualenv at my copy. I ran each gate directly instead (`ruff`, `mypy`, `pytest`,
  `check_records`, `wave_check_all`, `conformance_gate`, `swift test`, `client_decl_gate.py`) and
  the Makefile logic by hand.
- Not the `.xcodeproj` build: "compiles" above means `swiftc -typecheck` against the iOS SDK for the
  stated target, which is what the gate itself does.
- Not the router on a phone — only `NLContextualEmbedding` on this Mac. My scores differ from the
  record's in the third decimal; that is a toolchain difference, not a discrepancy.
- Not `@_silgen_name` or a runtime class lookup by computed string: the W-122 row already records
  those as open, and B16 makes the same point with `dlopen`.
- Not anything outside the files under Scope. My snapshot was taken before `docs/prd.md` and
  `docs/plans/m16-wave-1-close.md` appeared in the working tree; neither is reviewed here.
