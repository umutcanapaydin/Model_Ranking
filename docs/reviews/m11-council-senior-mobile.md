---
record_type: review
id: m11-council-senior-mobile
status: ratified
seat: independent
date: 2026-08-24
---

# M11 council — Senior Mobile Developer

> Seat added by the owner on 2026-08-24. Policy read from the protected base ref
> (`git show HEAD:AGENTS.md`), per V4C-06. No file in the repository was modified by this seat;
> verified below.

## What I ran

| Command | Result |
|---|---|
| `swift build` (in `ios/`) | `Build complete!` |
| `swift test` (in `ios/`) | `Executed 59 tests, with 0 failures`. Target platform reported as `arm64e-apple-macos14.0`; the swift-testing runner reports `0 tests in 0 suites`. |
| `xcodebuild ... -destination 'generic/platform=iOS' -configuration Release build` | **`error: Signing for "ModelRanking" requires a development team.`** `** BUILD FAILED **` |
| `xcodebuild ... -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -configuration Release build CODE_SIGNING_ALLOWED=NO` | `** BUILD SUCCEEDED **`, one warning, no deprecations |
| `xcodebuild -showBuildSettings -configuration Release` | `DEVELOPMENT_TEAM` absent; `CODE_SIGNING_REQUIRED = YES`; `PROVISIONING_PROFILE_REQUIRED = YES` |
| `plutil -p ModelRanking.app/Info.plist` (Release product) | 20 keys. No `NSAppTransportSecurity`, no `NSLocalNetworkUsageDescription`, no `ITSAppUsesNonExemptEncryption`, no `CFBundleIcons`, no `CFBundleDisplayName`. |
| `ls ModelRanking.app` | `Info.plist`, `ModelRanking`, `PkgInfo`. No `Assets.car`, no icon. |
| `grep -rn "accessibility" ios/ModelRanking/` | 0 hits across all five source files |
| `grep -rn "AppStorage\|UserDefaults\|SceneStorage\|scenePhase" ios/ModelRanking/` | 0 hits |
| `grep -rn "#Preview\|PreviewProvider" ios/ModelRanking/` | 0 hits |
| `find ios -name "*.xcstrings" -o -name "*.strings" -o -name "*.lproj" -o -name "*.xcprivacy" -o -name "Info.plist"` | 0 hits outside `.build/` |
| `swiftc` probe of locale-sensitive string APIs (source in scratchpad, project untouched) | results quoted in L-1 |
| live engine on a spare port, `GET /v1/recommendations?task=coding&budget=unlimited` | 13 + 44 ranking rows, 21 KB, 0 duplicate model names |

**No file was modified.** `md5` of all 12 tracked files under `ios/` taken before and after this
review are identical (`diff` clean). One unrelated working-tree modification, not mine, is reported
as N-8.

---

## BLOCKS THE PHONE

### P-1 · The device build does not compile, because no development team exists

`ios/ModelRanking.xcodeproj/project.pbxproj:159` and `:181` set `CODE_SIGN_STYLE = Automatic`.
Nothing sets `DEVELOPMENT_TEAM`, and `xcodebuild -showBuildSettings` confirms it resolves to
nothing. A device build stops before it produces a binary:

```
xcodebuild -project ios/ModelRanking.xcodeproj -scheme ModelRanking \
  -configuration Release -destination 'generic/platform=iOS' build
→ error: Signing for "ModelRanking" requires a development team.
```

**Why this is a device fact and not a paperwork fact.** `ios/app.sh:113` passes
`CODE_SIGNING_ALLOWED=NO` on every build this project has ever made. Signing is not a step that has
been skipped — it is a step that has never existed here. Nothing about provisioning, entitlements
or the generated `CODE_SIGN_INJECT_BASE_ENTITLEMENTS` output has been observed once.

**Smallest change:** sign in to Xcode with the owner's Apple ID to get a free personal team, set
`DEVELOPMENT_TEAM` in both target configurations. Two consequences of the free tier he should hear
before he starts: provisioning expires after **7 days** (the app stops launching until reinstalled
from Xcode), and a personal team is limited to 3 app IDs. The $99/year account is what turns this
from a demo into something on his phone next month.

### P-2 · On a phone, `127.0.0.1` is the phone

`ios/ModelRanking/Engine/EngineClient.swift:115` —
`static let localDefault = URL(string: "http://127.0.0.1:8080")!` — and
`ios/ModelRanking/ContentView.swift:38` — `private let client = EngineClient()`, the default,
never overridden anywhere.

`EngineClient.swift:1-6` states *"the base URL is configuration, not a constant"*. Measured: it is
a constant at the only call site. There is no settings screen, no `@AppStorage`, no launch
argument, no `Info.plist` key — the grep for all persistence APIs returns zero.

**Why it matters on a device.** The Simulator shares the Mac's loopback, which is the entire reason
this has worked for four milestones. A phone does not. The first thing the owner will see after
P-1 is solved is `ContentUnavailableView` reading *"The engine is not answering"* over
*"Start it with `make run` in the engine repository, then try again"* (`EngineClient.swift:60`) —
advice naming a Makefile target that cannot be run on the device showing the message.

**Smallest change:** `@AppStorage("engineBaseURL")` in the view (or in the `HomeModel` of H-1),
falling back to `EngineClient.localDefault`, plus a one-field settings sheet. See N-6: the two
force-unwraps at `EngineClient.swift:162-165` and `:172` become a crash-on-typo the moment that URL
is typed by a person, so they are part of the same change.

### P-3 · Pointing it at the Mac over Wi-Fi needs two `Info.plist` keys the app does not have

Measured from the Release build product: the shipped `Info.plist` contains **no
`NSAppTransportSecurity` dictionary and no `NSLocalNetworkUsageDescription`**. The project generates
its plist (`GENERATE_INFOPLIST_FILE = YES`) from exactly three `INFOPLIST_KEY_*` settings
(pbxproj:163-165), and none of them concern networking.

The obvious next move after P-2 — point the app at the Mac's LAN address — crosses two platform
gates at once:

1. **Local-network privacy (iOS 14+).** A request to a LAN address from an app with no
   `NSLocalNetworkUsageDescription` does not prompt; it fails.
2. **ATS cleartext.** `http://` to a non-loopback host with no exception dictionary is refused.

**Why this is worse than it sounds.** Both surface in this client as `EngineError.unreachable`,
whose recovery text says *"start the engine"* — sending the owner to restart a healthy server. That
is precisely the wrong diagnosis `EngineClient.swift:24-28` was written to prevent, and the
`insecureTransport` case that prevents it (`EngineClient.swift:181`) **has never executed once**,
because the only host this app has ever contacted is loopback. A control in the path that does not
execute — the shape `docs/EXPERIENCE.md:530` names as this project's most-recorded defect, sitting
in the client's newest security case.

**Smallest change:** `INFOPLIST_KEY_NSLocalNetworkUsageDescription` with one honest sentence, and a
per-host `NSAppTransportSecurity → NSExceptionDomains → <host> → NSExceptionAllowsInsecureHTTPLoads`.
**Not `NSAllowsArbitraryLoads`** — `EngineClient.swift:65-68` already argues this correctly and the
argument holds. Prefer the Mac's Bonjour name (`<machine>.local`) over its IP: it survives DHCP, and
it is inside what `NSAllowsLocalNetworking` covers, whereas a `192.168.x.x` address is not.

### P-4 · There is no app icon, and no asset catalog at all

`ls` on the built `ModelRanking.app` returns `Info.plist`, `ModelRanking`, `PkgInfo` — no
`Assets.car`, no icon file. The Resources build phase is empty (pbxproj:106-113),
`ASSETCATALOG_COMPILER_GENERATE_ASSET_SYMBOLS = NO` (pbxproj:158, :178), and no `.xcassets`
directory exists anywhere under `ios/`.

**Why on a device specifically.** In the Simulator nobody looks at the home screen. On his phone
this is a blank placeholder tile labelled `ModelRanking` (no `CFBundleDisplayName`, so no space in
the name), sitting among real apps. It is also the first thing App Store Connect rejects on upload,
long before a human reviewer sees it — see S-1.

**Smallest change:** add `ios/ModelRanking/Assets.xcassets` with an `AppIcon` set (one 1024px
image; Xcode 26 derives the rest), set `ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon`, and add
`INFOPLIST_KEY_CFBundleDisplayName` if he wants two words. The file-system-synchronised root group
(pbxproj:10-15) picks the folder up with no project-file surgery.

---

## BLOCKS THE STORE

### S-1 · A reviewer will see the error screen, and nothing else

The app's entire content requires a server on `127.0.0.1:8080`. App Review runs the binary on their
own device on their own network. They will get *"The engine is not answering / Start it with
`make run` in the engine repository"*. That is Guideline 2.1 (App Completeness) and arguably 4.2
(Minimum Functionality), and it is an immediate rejection costing days per round.

**Nothing else on this list matters until the engine is publicly reachable over HTTPS.** D-123 is
undischarged and `docs/prd.md:403` says so plainly; D-116 names the target.

**Smallest change (client side):** P-2's configurable base URL, with an **`https://`** production
default compiled in, so the shipped build has never been pointed at loopback and the loopback value
is the developer override rather than the other way round.

### S-2 · Export compliance is undeclared

No `ITSAppUsesNonExemptEncryption` in the built plist. Every TestFlight and App Store upload halts
on the encryption question until it is answered. The app uses platform TLS only and nothing else.

**Smallest change:** `INFOPLIST_KEY_ITSAppUsesNonExemptEncryption = NO` in both configurations —
answered once in the build instead of by hand on every upload.

### S-3 · No privacy manifest, and the privacy story has never been written down

No `PrivacyInfo.xcprivacy` exists under `ios/`.

Today the app uses no required-reason API and no third-party SDK, so the automated check would not
fail. **But P-2's fix is `@AppStorage`, which is `UserDefaults`, which is a required-reason API
(category CA92.1).** The manifest becomes mandatory in the same change that makes the app usable on
a phone. Ship them together.

The App Privacy questionnaire is mandatory regardless, and the truthful answers are worth writing
down now while they are still simple. Verified by reading `Router.swift` end to end: nothing typed
reaches the engine — the question goes to `NLContextualEmbedding` or `FoundationModels` on-device
and the only thing that leaves is one of nine category ids plus a budget word (REQ-RTR-004 holds in
the code, not only in the record). **That changes at deploy:** an engine on a public host writes an
access log with the caller's IP and their chosen category per request. Either the label describes
that collection or the engine stops logging it, and the decision belongs before go-live, not after.

**Smallest change:** `PrivacyInfo.xcprivacy` with `NSPrivacyTracking = false`, empty
`NSPrivacyCollectedDataTypes`, and one `NSPrivacyAccessedAPITypes` entry for `UserDefaults`; plus an
ADR fixing the engine's access-log retention.

### S-4 · Usage descriptions — checked, and the correct answer is "none, today"

Stated because the *absence* here is right and I do not want it "fixed". No camera, microphone,
location, photos, contacts, calendar, motion or tracking API appears anywhere in the target.
`NaturalLanguage` and `FoundationModels` require no usage description. The only usage description
this app will ever need is `NSLocalNetworkUsageDescription` (P-3), and only in the LAN configuration.
A plist declaring permissions the binary never exercises draws a 5.1.1 question of its own.

### S-5 · The version numbers are frozen at 1

`CURRENT_PROJECT_VERSION = 1` and `MARKETING_VERSION = 0.1.0` (pbxproj:160, :166). Every upload
needs a strictly increasing `CFBundleVersion`. Trivial, and it stops the *second* upload rather
than the first, which is when it is most annoying.

### S-6 · Mac distribution is on by default

`SUPPORTS_MAC_DESIGNED_FOR_IPHONE_IPAD = YES` (from `-showBuildSettings`). An iPhone-only app
requiring a specific server would be auto-offered on Apple Silicon Macs. Turn it off in App Store
Connect or set the build setting to `NO`.

---

## HURTS LATER

### H-1 · `ios/Package.swift` draws the line in the right place for FILES and the wrong place for LOGIC

`Package.swift:45` scopes the tested target by `path: "ModelRanking/Engine"`. Every file in that
directory is compiled and executed by the suite; `ContentView.swift` is not, by construction, and
`Package.swift:12-16` says so honestly. **As a statement about files, the line is correct and I
would not move it.**

The problem is what the line *incentivises*. Real policy lives on the untested side:

- `ContentView.swift:371-389` (`load()`) — the decision that a `/v1/categories` failure is
  non-fatal and the default surface still answers. A deliberate resilience choice with a written
  rationale (`:375-377`) and no test.
- `ContentView.swift:351-369` (`ask()`) — route first, reload only if the surface changed.
- `ContentView.swift:358` — `guard !known.isEmpty else { return }`. If categories failed, the
  reader types a question, watches the spinner appear and vanish, and gets nothing. No sentence.
  That is REQ-APP-004's "never a blank outcome" violated in a path no test can reach.

Any behaviour written into a view file is automatically exempt from the gate. That is the wrong
gradient for a codebase that is about to grow a sentence-composition layer (L-4).

**Smallest change, requiring no project-file edit:** move `load()`, `ask()` and `LoadState` into an
`@Observable final class HomeModel` at `ios/ModelRanking/Engine/HomeModel.swift`. `Package.swift`'s
`path` picks the new file up for free; `@Observable` is iOS 17 / macOS 14, inside both declared
floors; `ContentView` becomes `@State private var model = HomeModel()`. W-060 stays true — views
remain unexecuted — but the untested surface shrinks to layout, which is what W-060 says it wanted
to be about.

### H-2 · `swift test` proves things about macOS, not about iOS

Measured: `swift test` reports `Target Platform: arm64e-apple-macos14.0`. All 59 XCTest cases pass
and the swift-testing runner reports `0 tests in 0 suites`. The Engine is compiled against the
**macOS** SDK there — `NLContextualEmbedding`, every `@available` floor, and the
`#if canImport(FoundationModels)` tier are being exercised against macOS frameworks and macOS
availability.

`Package.swift:46-57` already makes exactly this distinction one level up, for language mode: the
same files in a different mode is a narrower guarantee than "compiles what the app ships". The same
sentence applies to the SDK, and the manifest does not make it. The iOS compilation happens only
inside `xcodebuild`, which runs no tests.

**Smallest change:** either add an iOS compile to the gate
(`swift build --triple arm64-apple-ios18.0-simulator`, so the iOS build is at least *attempted* by
something that can fail), or state the limit in the manifest the way the language-mode note does.
The second is cheaper and honest; the first catches a real class of thing.

### H-3 · Nothing the reader chooses survives a launch, and nothing survives losing the engine

Zero hits for `AppStorage`, `UserDefaults`, `SceneStorage` and `scenePhase` in the whole app.

- `task` resets to `"coding"` on every cold launch (`ContentView.swift:24`). So does the typed
  question, the routing outcome, the filter and the scroll position.
- `URLSessionConfiguration.ephemeral` with `.reloadIgnoringLocalCacheData`
  (`EngineClient.swift:129-132`) is a deliberate no-cache choice. It is right for correctness and
  wrong for a phone: with no engine there is nothing on screen at all.
- `.task { await load() }` (`ContentView.swift:58`) runs once. There is **no reload on foreground**.

**Why this is device-specific.** A Simulator session is one continuous foreground run. A phone is
suspended and resumed dozens of times a day, loses Wi-Fi in a lift, and gets opened on cellular with
Low Data Mode on. The app as built shows a full-screen error in every one of those moments, and an
app left open overnight shows yesterday's answer with no marker on it.

The engine already serves the vocabulary for showing old data honestly — `evidence_date`,
`evidence_dating_note`, `stale_notice`, `source_health`. Caching the last good payload and rendering
it under an "as of" line uses fields the product already paid review rounds for.

**Smallest change:** `@AppStorage("task")` for the surface (one line, immediate win); then, in the
`HomeModel` of H-1, persist the last decoded `Recommendation` and reload on
`scenePhase == .active` when it is older than N minutes.

### H-4 · Accessibility is at zero, and three of the gaps are load-bearing

`grep -rn "accessibility" ios/ModelRanking/` returns nothing across all five files. No
`lineLimit`, no `minimumScaleFactor`, no `ScaledMetric`, no `dynamicTypeSize`.

**a. Selection is signalled by colour alone.** `ContentView.swift:308-315` — the selected chip
differs from the other eight by a `.tint` capsule fill and white text, and by nothing else.
VoiceOver reads all nine identically and cannot say which surface is on screen. This is also the
control the owner has already reported twice (W-065, W-070).
*Smallest change:* `.accessibilityAddTraits(category.id == task ? .isSelected : [])` on the Button.

**b. The numbers read as gibberish aloud.** `Format.scoreAndPrice` (`ContentView.swift:539`)
produces `83.5 % resolved  ·  $2.06/1M`. VoiceOver reads the separator dot and the `/1M` literally.
*Smallest change:* an `.accessibilityLabel` spelling it out — and note this is the **same sentence**
the CFO feedback asks for in print (`docs/plans/m12-inputs.md`, item 4: *"about $1 for 1,500 pages
of text"*). The accessible label and the plain-language line are one piece of work, not two.

**c. Dynamic Type is unhandled, and one hardcoded number will break at exactly the wrong size.**
`RankedRow` (`ContentView.swift:482-492`) is an `HStack` of name, `Spacer()`, score, with no
`lineLimit` — at large accessibility sizes the score is squeezed or truncated. Worse,
`ContentView.swift:153` is `.padding(.bottom, 88)`, a hardcoded number for the search bar's height,
added because the last card sat under it (`:148-152`). The search bar **grows with Dynamic Type**,
so that fix silently stops working at large text — which is precisely when a 60-year-old reader has
it turned up.
*Smallest change:* `@ScaledMetric private var bottomInset = 88.0`, used in place of the literal.
One line, and it tracks the setting it was measured against.

### H-5 · Error states a person cannot act on — including one blank screen

**a. `RankingList` has no empty state.** `ContentView.swift:501-525`: filter the full ranking to
something that matches nothing and you get a completely blank `List`. The home screen handles this
(*"No model here matches …"*, `:219`); the detail screen does not. A blank screen is what
REQ-APP-004 exists to forbid.
*Smallest change:* `if rows.isEmpty { ContentUnavailableView.search(text: filter) }`.

**b. `ask()` dead-ends silently** — `ContentView.swift:358`, described in H-1.
*Smallest change:* set `routing` to a `.manual` outcome carrying an explanation; the UI at `:93`
already renders it.

**c. The `.manual` tier says one thing and does another, and this is a device-only path.**
`Router.swift:371-373` returns `categoryID: "assistant"`, `tier: .manual`, `unmeasured: false`.
`ContentView.ask()` then sets `task = "assistant"` and reloads (`:365-368`) — while the sentence on
screen reads *"Pick a surface below."* (`Router.swift:50`). The app changes the surface for the
reader and simultaneously tells them it did not. And because `unmeasured` is `false`, the
"we do not measure this" disclosure does **not** appear — the exact disclosure W-063 was raised to
install.

Reaching this state needs both tiers absent: a device without Apple Intelligence whose
`NLContextualEmbedding` assets have not downloaded yet. That is a real phone on first launch, and it
is essentially unreachable in the Simulator the app has always been tested in.
*Smallest change:* in the `.manual` case either do not change `task`, or return `unmeasured: true`.
One or the other — the current pair contradicts itself.

### H-6 · Localisation mechanics: what the client needs for the M12 decision to work

The decision at `docs/plans/m12-inputs.md:29` — engine returns structured facts, client composes the
sentence — is the right call from an iOS point of view, and I would not revisit it. It is the only
shape where the third language does not cost what the second one cost. What follows is what stands
in its way today.

#### L-1 · Turkish case folding silently breaks the model filter — measured

`ios/ModelRanking/Engine/Router.swift:396` uses `localizedCaseInsensitiveContains`, which folds case
using the **current locale**. Measured with a `swiftc` probe (source written to the scratchpad; the
project was not touched), searching four model names for a single letter:

| Locale | Needle | Matches |
|---|---|---|
| `en_US` | lowercase i | `GPT-5.1 Instruct`, `Mistral Large` |
| `tr_TR` | lowercase i | `Mistral Large` **only — `GPT-5.1 Instruct` disappears** |
| `tr_TR` | uppercase I | `GPT-5.1 Instruct` only |
| `en_TR` | lowercase i | both |

The Turkish alphabet separates the dotted and undotted forms of this letter in both cases, so
Turkish case folding does not map uppercase I to lowercase i the way English does.

**Why it is dormant today, and exactly when it fires.** Case folding follows the *language*, not the
region. The owner's device is `en_TR` — `ContentView.swift:534` says so — and the table shows
`en_TR` is safe. It breaks the day the language becomes Turkish, which is M12's first item.

**Why this one matters more than its size.** The owner has already reported this screen once, as
*"I press C and it filters by category, not by model name"* (W-069). The fix that shipped was the
scroll-to-top, the predicate was extracted to `filterRanking`, and six tests now pin it — **and all
six run under the test process's locale, so not one of them can see this.** The same symptom returns
in Turkish with the guarding tests green.

*Smallest change:* fold with a fixed locale. Model names and vendors are ASCII identifiers the
engine owns, not the reader's prose:
`name($0).range(of: needle, options: [.caseInsensitive, .diacriticInsensitive], range: nil, locale: Locale(identifier: "en_US_POSIX"))`.
Plus one test that sets the locale to `tr_TR` and asserts the lowercase letter still matches
`Instruct` — the seventh test, and the only one on the side that fails.

**Checked and NOT a bug — stated so it is not "fixed" wrongly.** `String.uppercased()`
(`ContentView.swift:433`) and `String.lowercased()` (`Router.swift:117`) are locale-*independent* in
Swift. Measured: `"budget_pick".uppercased()` gives `BUDGET_PICK`, while
`.uppercased(with: Locale(identifier: "tr_TR"))` gives the dotted-capital form the pick badge would
then render. Leave both call sites exactly as they are; do not migrate them to the `with:` variants.

#### L-2 · Nothing is localisable today, and `SWIFT_EMIT_LOC_STRINGS` will not save the sentences that matter

`knownRegions = (en, Base)` (pbxproj:89-92). No String Catalog, no `.strings`, no `.lproj` anywhere
under `ios/`.

`SWIFT_EMIT_LOC_STRINGS = YES` is set (pbxproj:169, :189) and does extract `Text("literal")`. It
cannot extract any of these:

- `EngineError.errorDescription` and `.recovery` — `EngineClient.swift:39-78`, plain `String`
  returns assembled with `+`.
- `RoutingOutcome.explanation` — `Router.swift:41-51`, the same.
- The composed ranking line — `ContentView.swift:133-139`.
- *"See all N — M fit your budget"* — `ContentView.swift:199-204`.

Those are precisely the sentences a reader sees when something is wrong or when a disclosure fires:
the ones this product's honesty claim rests on.

*Smallest change, and it should land **before** any Turkish work:* return `LocalizedStringResource`
(or `String(localized:)`) with explicit keys from those four places. Then the catalog Xcode emits
actually contains them.

#### L-3 · `+` and inline interpolation are the wrong shape for Turkish specifically

`"\(answer.ranking.count) models ranked on \(answer.primaryBenchmark), at \($0) effort"`
(`ContentView.swift:134-138`) is not a reordering problem in Turkish. Turkish is verb-final, and the
grammatical suffix attached to the benchmark's name depends on that name's own final vowel and final
letter (vowel harmony) — the correct suffix for `SWE-bench Verified` and for a name ending in a back
vowel are different strings. A translator handed fragments cannot produce either.

Plurals compound it: Turkish does not pluralise a noun after a numeral. `44 model`, never the
pluralised form. No `if count == 1` in Swift expresses that; a String Catalog plural variation does.

*Smallest change:* one format string per sentence with positional arguments (`%1$d`, `%2$@`), held
in a String Catalog with plural variations declared there. Never assemble a user-visible sentence
with `+`.

#### L-4 · The composer needs a home and an explicit `Locale`, decided now rather than retrofitted

Three requirements the client does not currently satisfy:

1. **The composition layer must not live in a view file.** Otherwise every new sentence is written
   on the untested side of `Package.swift` (H-1) — and the composer is about to become the single
   largest body of user-visible logic in the app.
2. **A `Locale` must be threaded explicitly from day one.** The owner asked for a *flag switch in
   the top-right*, not the system language. `.environment(\.locale, chosen)` localises SwiftUI
   `Text` and does nothing for a `String` composed inside `EngineError` or handed to a formatter.
   Every composition entry point needs a `Locale` parameter at the start; retrofitting one through
   fifty call sites afterwards is the expensive version of the same change. (Flipping
   `AppleLanguages` in `UserDefaults` is the shortcut, requires a relaunch, and is a known App Store
   smell — avoid it.)
3. **Currency needs the platform's formatter, not a pinned POSIX locale.** `Format.trim`
   (`ContentView.swift:543-549`) pins `en_US_POSIX`, and the rationale at `:534-537` is *right about
   the failure it observed*: a comma-decimal price beside a `$` is genuinely ambiguous. But the fix
   generalises badly — in a Turkish build, prices become the one number on screen that ignores the
   reader's locale. The platform already solves exactly this:
   `price.formatted(.currency(code: "USD").locale(chosen))` renders the reader's separators **and**
   an unambiguous currency marker, which is the property the comment wanted. The CFO line
   (*"about $1 for 1,500 pages"*) is a currency inside a composed sentence, so it needs this anyway.

#### L-5 · The router will quietly stop working in Turkish, and its threshold has no meaning there

`Router.swift:119` constructs `NLContextualEmbedding(language: .english)` and `:134` requests
`embeddingResult(for:language: .english)`. `CategoryHints.byID` (`:68-80`) is English prose. A
Turkish question embedded by an English model against English hints is noise.

Measured on this machine: `NLContextualEmbedding(language: .turkish)` constructs successfully,
`hasAvailableAssets = true`, `dimension = 512`, `revision = 1`. The platform can do it. The client
never asks.

`SimilarityRouter.defaultFloor = 0.15` (`Router.swift:114`) is documented as **measured** on an
English probe of nine questions (`docs/reviews/m10-router-calibration.md`). Under a different
embedding it is an unvalidated constant — and it is the only thing standing between an unmeasured
question and a confident wrong answer (REQ-RTR-005; W-063 is what happens when that fails). A
Turkish build reusing 0.15 ships the W-063 defect again in a language nobody probed.

Tier 1 (`FoundationModels`) handles Turkish, but only on iOS 26 with Apple Intelligence enabled — so
on any older phone, Turkish routing falls to the tier that cannot read Turkish.

*Smallest change:* select the embedding language from the chosen locale, localise `CategoryHints`,
and **re-run the M10 calibration probe in Turkish before the switch ships**. The floor is a
per-language measurement, not a constant.

#### L-6 · Turkish is longer than English, and this layout has no give — and no way to look at it

Turkish runs roughly 15-30% longer than English for the same content. Combined with H-4c (no
`lineLimit`, no `ScaledMetric`, a hardcoded 88pt inset) and the fixed capsule padding at `:306-314`
and `:436-437`, Turkish will overflow layouts that English fits.

There are **zero `#Preview` blocks** in the app, despite `ENABLE_PREVIEWS = YES` (pbxproj:161, :182).
So today, seeing a long-string layout, a stale-notice state, an empty answer or a dark-mode
regression requires making a live engine produce it — which is exactly why W-066 could record
"half of this design was verified by looking at it and half was not".

*Smallest change, and the cheapest single item on this entire list:* one `#Preview` per component
(`Card`, `PickBadge`, `PickRow`, `RankedRow`, the failure view) with a decoded fixture, plus a
second preview carrying `.environment(\.locale, Locale(identifier: "tr"))` and
`.environment(\.dynamicTypeSize, .accessibility3)`. It pays for itself in the first design
iteration and it is the only tool that makes L-6 visible before a user finds it.

### H-7 · `Router.swift:94` justifies the design by naming a different API

The comment reads *"`NLEmbedding` is iOS 13+, so this covers every device the app runs on"*. The
code uses `NLContextualEmbedding` (`:119`), which is **iOS 17+** and — unlike `NLEmbedding` —
requires an **asset download**, which is why `hasAvailableAssets` and `load()` exist at `:120-121`.
Both floors sit below the 18.0 target, so nothing breaks. But the sentence justifying the choice
describes an API with different runtime behaviour, and that behaviour is what produces H-5c.

*Smallest change:* correct the comment to name `NLContextualEmbedding`, iOS 17, and the asset
download that can be absent on a device.

### H-8 · The filter does locale-aware work per row, twice, on every keystroke

`ContentView.swift:167-168` calls `filtered(answer.ranking)` **twice inside one expression**, and
`filterRanking` runs a locale-aware comparison per row. On `coding` that is roughly 44 rows x 2
surfaces x 2 calls per keystroke. `RankingList.rows` (`:527-529`) is a computed property
re-evaluated on every body pass of a 44-row `List` and again inside `.onChange` (`:518-521`).

Measured payload today: 57 ranking rows, 21 KB total — genuinely small. This is invisible on the
Mac's CPU, which is what the Simulator runs on, and will show as keystroke lag on the A12-class
phone a 60-year-old CFO is likely holding.

*Smallest change:* bind `let visible = filtered(answer.ranking)` once and pass it to both uses;
hold `rows` in `@State`, updated in the existing `onChange`, rather than recomputing it per body.

---

## NOTED

**N-1 · Every availability floor checks out, and there are no deprecations.** Walked each API against
`IPHONEOS_DEPLOYMENT_TARGET = 18.0` (pbxproj:132, :147): `ContentUnavailableView` (17),
`NLContextualEmbedding` (17), two-parameter `onChange` (17), `foregroundStyle(.tertiary)` (17),
`.tracking` (16), `.searchable` / `.safeAreaInset` / `.refreshable` / `.submitLabel` /
`.background(.bar)` / `AnyShapeStyle` / `.controlSize` (15), `LazyVStack` / `ScrollViewReader` (14).
The iOS 26 surface (`SystemLanguageModel`, `LanguageModelSession`, `GenerationSchema`) is correctly
double-gated by `#if canImport(FoundationModels)` plus `@available(iOS 26.0, macOS 26.0, *)`
(`Router.swift:190-191`, `:356-359`) and is reachable only through
`TieredRouter.platformModelRouter()`. A clean Release build against the iOS 26.5 SDK emitted exactly
one warning, and it is not a deprecation: *"Traditional headermap style is no longer supported;
please migrate ... set `ALWAYS_SEARCH_USER_PATHS` to NO."* It will become an error in a future
Xcode. *Smallest change:* `ALWAYS_SEARCH_USER_PATHS = NO` in both project-level configurations.

**N-2 · The Release configuration builds, and had never been built.** `ios/app.sh:113` only ever
builds `-configuration Debug`, so `SWIFT_COMPILATION_MODE = wholemodule` (pbxproj:149) and
`VALIDATE_PRODUCT = YES` (pbxproj:151) had never been exercised. I ran a Release simulator build
from a clean derived-data path: `** BUILD SUCCEEDED **`. They are fine — which is worth recording,
because the first time anyone finds out otherwise is normally during an archive.

**N-3 · Nothing in the app has ever been compiled in Swift 6 language mode.** `Package.swift:58`
pins the Engine target to `.v5` to match `SWIFT_VERSION = 5.0` (pbxproj:137, :150, :170, :190), and
`tests/unit/test_ios_platform_drift.py` guards the pin. That is the right call and it is well
recorded. The consequence to carry forward: no strict-concurrency checking has ever run over this
code. The `@State`-mutating `async` methods on a `View` struct (`ContentView.swift:351-389`) are the
first thing needing an audit when the mode flips, and the `HomeModel` refactor in H-1 makes that
audit trivial because the isolation becomes explicit instead of inferred.

**N-4 · Two `ForEach` id choices assume uniqueness the contract does not promise.**
`RankedModel.id` is the bare model name (`Models.swift:131`), and `disclosures` iterates notice
strings with `id: \.self` (`ContentView.swift:246-254`). `PUBLIC_RANKING_FIELDS`
(`src/app/adapter/main.py:775`) publishes `effort` and `harness`, so a surface ranking one model at
two effort levels is expressible in the payload. `ForEach` with duplicate ids gives undefined
rendering. **Measured against a live engine today** (`task=coding`): 13 + 44 rows, zero duplicate
model names, and both answers' notices distinct. So this is a latent assumption, not a live defect.
*Smallest change:* `id` composed from model, harness and effort.

**N-5 · `SameHostOnly` compares host only — not scheme, not port.** `EngineClient.swift:90-106`.
Today both sides are `http://127.0.0.1:8080` and nothing is at risk. Once the engine is `https://`
on a public host (S-1), a `302` to `http://<same-host>` is a protocol downgrade this delegate would
follow. Flagged because M8's security review installed this delegate specifically to close the
redirect hole, and the property it protects changes meaning at the exact moment the deploy happens.
*Smallest change:* compare scheme, host and port together.

**N-6 · Two force-unwraps become a crash vector at the moment P-2 is fixed.**
`URLComponents(url:resolvingAgainstBaseURL:)!` (`EngineClient.swift:162-165`) and
`components.url!` (`:172`) are safe for a compile-time-constant base URL and unsafe for one a person
types. Fix them in the same change as the settings field, not after it.

**N-7 · Disclosure-grade fields decoded and never shown.** `Pick.confidence`,
`Pick.confidenceBasis`, `Pick.effortNote`, `Pick.higherEffort`, `Pick.higherEffortScore` and
`Answer.evidenceDating` exist in `Models.swift` and appear nowhere in `ContentView.swift`.
REQ-APP-003's citing test derives its field set from `Models.swift` and passes because the decoder
references them — which is a weaker claim than "the reader sees it". Not raised as a defect: screen
space is a product decision and the picks already carry `why` and `trade_off`. Recorded because
`effort_note` is specifically the sentence saying a score came from a different effort level, and it
is the same class of gap the requirement exists to close.

**N-8 · Not my seat, recorded because my own evidence passed through it.** Partway through this
review `src/app/workflows/recommend.py:320` was modified in the working tree — `if gap <= close_pts:`
had become `if gap <= 0.0:`. A mutation, not a commit; my first `git status` was clean, and a
parallel council seat was evidently running mutation testing. I did not touch it, and by the end of
this session it had been reverted by whoever made it; the tree is clean on that file now.

Recorded anyway for one reason: **the live payload measurement quoted in N-4 ran against an engine
carrying that mutant.** It affects `close_call` only, and neither answer emitted a `close_call`, so
it changed nothing I measured — but a reader of this record is entitled to know that, rather than to
find it out. The general point stands for the next parallel session: a mutant living in the shared
working tree is indistinguishable from a defect to any other seat that starts the engine, and
mutation runs should happen on a branch or in a worktree.

---

## What I could NOT check without a physical device or an Apple Developer account

Stated explicitly, because "it builds and the Simulator runs it" is not evidence about a device.

1. **That the app installs and launches on a phone at all.** Signing has never been attempted
   (P-1); `xcodebuild` fails before producing a binary. The provisioning profile, the generated
   entitlements (`CODE_SIGN_INJECT_BASE_ENTITLEMENTS = YES` produces them and I have never seen the
   result), and whether the free-team 7-day expiry is acceptable to the owner are all unknown.
2. **Whether ATS actually refuses a LAN host, and which error code arrives.** I could not point the
   client at anything but loopback without editing `EngineClient.swift`, which I was told not to do.
   I tried `nscurl --ats-diagnostics`; it rewrites `http://` to `https://` and therefore answers a
   different question, so I discarded the result rather than report it as evidence. The
   `insecureTransport` branch (`EngineClient.swift:181`) has never executed on any run.
3. **Whether the local-network permission prompt appears, and what the app does when it is denied.**
   iOS 14+ behaviour, device-only; no such prompt exists in the Simulator.
4. **On-device model behaviour on his actual phone.** Which of the three
   `SystemLanguageModel.default.availability` cases it reports (`Router.swift:196-206`). W-067 was
   closed by the owner's own run in a Simulator on an M-series Mac; a phone is a different device
   class with different eligibility.
5. **Whether `NLContextualEmbedding` assets are present on a fresh phone**, how long the download
   takes, and therefore how often a real first launch lands in the `.manual` tier — which is the
   state H-5c is broken in.
6. **VoiceOver.** Rotor navigation, the reading order through the cards, and whether the category
   strip is reachable at all. The Accessibility Inspector against a Simulator is an approximation;
   the phone with the screen curtain on is the instrument.
7. **Dynamic Type at accessibility sizes on a real screen**, and specifically whether the hardcoded
   88pt inset (`ContentView.swift:153`) still clears the search bar at the largest sizes.
8. **Performance on older hardware.** H-8 is arithmetic, not a measurement. Keystroke latency,
   scroll frame drops through the 44-row list, cold-launch time and memory growth need Instruments
   on an A12/A13-class phone. The Simulator runs on the Mac's CPU and tells you nothing about any of
   them.
9. **Anything about App Review.** Every item under BLOCKS THE STORE is read off the Guidelines and
   the built `Info.plist`. No Apple account exists, nothing has been uploaded, and App Store
   Connect's own upload validation — which catches the missing icon and the missing encryption
   declaration before a human reviewer ever sees the build — has never run.
