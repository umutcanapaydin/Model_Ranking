---
record_type: review
id: m14-wave-3-4-review
status: ratified
seat: independent
date: 2026-09-20
---
# M14-W3 and W4: Code-Reviewer and Security seat

## How this review was produced
- **Seat:** independent, fresh context. I did not write this code. I read the policy from the base repo: `subagent-profiles/Code-Reviewer.md`, `Security-Reviewer.md`, `docs/plans/m14-plan.md` (§0 rulings, §1 REQ table, W3, W4, §3), `AGENTS.md` §3/§5, and `docs/decisions.md` (D-138, D-143). The diff under review is `git diff` against `4649f10`, the same content as `/root/mr/m14-w34.diff` (12 files, +480/−11).
- **Python suite:** `PYTHONPATH=src python3 -m pytest tests … -n 2` gives **911 passed, 13 skipped**.
- **Swift parse:** every `ios/**/*.swift` file parses clean with tree-sitter-swift (no ERROR or MISSING nodes).
- **Swift compile:** checked by reading, line by line, against the package's settings. Engine is Swift 5 mode. The test target is Swift 6 mode (tools 6.2, no `swiftSettings`). The app target is `SWIFT_VERSION = 5.0`, and its synchronized root group builds ContentView and Engine as one module.
- **Mutation runs:** four mutants, each restored afterwards. `git diff --stat` still matches the original 107/79-line diffs.
- **Product figures:** served `/v1/categories` and `/v1/recommendations?budget=unlimited` in-process (FastAPI TestClient) against a copy of `/tmp/live.db`, then applied the Swift formula to every ranked row.

## (A) Code-Reviewer findings

**No compile blocker found.** The one BLOCKING item is a governance item and needs only a written record to fix.

### BLOCKING
- **B-1: `/v1` contract widened without an ADR, against an owner ruling.** `src/app/adapter/main.py:1246` adds `score_anchor` to every `/v1/categories` entry.
  - Plan §0 ruling 2 says "**No K.8 change in M14.**" The W4 plan text says "`/v1` does not move." §3 freezes `/v1` shape for W1–W3.
  - D-143 says the anchor is "pinned in `CategorySpec`". It does not authorise a new `/v1` field.
  - D-138 is the precedent: it was an owner ADR that explicitly "amends the … field freeze, for `/v1/categories` only". It covered its three fields, not future ones.
  - Code-Reviewer profile §5 lists "Public contract widened without ADR" as BLOCKING.
  - The change is additive, optional on the client, and sound. The fix is a record: a D-143 amendment or new ADR naming the field, signed by the owner. If the owner reads D-143 as already covering it, this becomes MAJOR.

### MAJOR
- **M-1: The metric name and native Elo numbers are still on every Elo card.** This breaks REQ-SCR-001 ("no card or row shows the metric's name") and the W4 plan line "The metric name leaves the card and the rows".
  - `PickRow` still renders `whySentence` / `tradeOffSentence` (`Language.swift:72,78,124`) with `unit = "Elo"` on native values.
  - Live `assistant` best-value card, reproduced: the figure line reads `Score 61.6 / 100`. The same card says "The cheapest model that is still within 30 Elo of the best one" and "25.5 Elo behind the best one". The leader's card reads `Score 65 / 100`.
  - A reader subtracts 65.0 − 61.6 = 3.4 and is told 25.5.
  - Budget pick: "it clears 1400 Elo" on the same card as "50 is at the bar".
  - No source-contract test for REQ-SCR-001 was added.
- **M-2: The leader note still gives the margin in Elo above rows read out of 100.** This is REQ-SCR-004 and D-143 clause 5.
  - `leaderSentence` (`Uncertainty.swift:115-128`, `marginUnit` → `"Elo"`) feeds the RankingList header (`ContentView.swift:164,417,836`).
  - Live: `assistant` reads "top 3 of 65 … its margin is 8 Elo" above rows `65.0 / 64.7 / 64.4`. `document` reads "margin is 8.7 Elo" above `57.0 / 56.5`.
  - Keeping rank ranges on the native scale is the correct way to preserve ties. But it is an unamended departure from the plan ("ranges are re-derived from the converted margin; property test over every margin", with `UncertaintyTests.swift` as the named verifier). No `UncertaintyTests` change exists.
  - For reference, the margin in converted units is 8 Elo ≈ 1.05–1.15 pts, 8.7 ≈ 1.23–1.25, 6.8 ≈ 0.65–0.98, 4 ≈ 0.56–0.58.
  - Fix: state the margin in converted points on anchored surfaces, or drop the unit. Record the native-range choice as a plan amendment.
- **M-3: The anchor is the Budget-Pick floor, which is itself a statistic recalibrated from the board.**
  - `categories.py:90`: "RECALIBRATED … 1400 = top third, leader-108". `:215`: "`min_quality` = the top third of the WHOLE board … Reproduce with `scripts/calibrate_board.py`".
  - So every recalibration moves every Elo score on the surface with no new measurement. It also retunes the recommendation floor.
  - D-143 forbids exactly this failure ("a model's score move[s] … with no change to any measurement of it"). It is not the board maximum, but it is a board quantile, refreshed.
  - The plan says "Each `CategorySpec` carries what 100 means". A dedicated pinned, versioned `score_anchor` field was expected, not reuse of a policy knob.
  - The choice is recorded only in a code comment. There is no ADR and no plan note.
- **M-4: A client-side board-max anchor passes the entire suite.** This breaks the REQ-SCR-003 verification ("a mutant that swaps the pinned anchor for the board max must fail").
  - Mutant: replace `anchor: category(for: answer)?.scoreAnchor` with `anchor: answer.ranking.map(\.score).max()` at `ContentView.swift:402` and `:418`. It compiles (`Double?`). Result: **911 passed**.
  - Only `PickRow`'s `anchor: info?.scoreAnchor` is pinned, by `test_ios_client_contract.py:559`. The ranking preview rows and the full list are unpinned producers.
  - The server-side mutant does fail, via `test_uncertainty_contract.py:271`.

### MINOR
- **m-1: The register records router failures as gaps, and misses real declines.** This is REQ-GAP-001 ("every decline sentinel").
  - `ContentView.swift:557` records on any `outcome.unmeasured`. That includes `tier: .manual` (`Router.swift:474`), which is returned when both tiers fail. Example: `NLContextualEmbedding` assets not loaded, which makes similarity return nil at `Router.swift:170-176`.
  - On such a device, every question, including "best model for coding", enters the owner's demand list.
  - Conversely, a real decline is lost when the ticket is superseded (`:544`, `:551`) or when categories failed to load (`:540`).
  - Fix: `if outcome.unmeasured && outcome.tier != .manual`.
- **m-2: No REQ-SCR-002 property test over served boards.** The plan names "property test over every served board", but `ScoresTests.swift:168` uses a synthetic stride. I checked the live boards myself: monotone on all four Elo surfaces.
- **m-3: The `SORTING_PERMITTED` match is a line substring, not the collection being sorted.** See C5 below.
- **m-4: `@State private var gaps = GapRegisterStore.onDevice.load()` (`ContentView.swift:49`)** does synchronous disk I/O in a property initialiser. It re-runs on every `ContentView` struct init; State keeps the first result.

### NIT
- `GapEntry.id` is the fold of the *truncated* text, so two questions that differ only after character 200 merge.
- A decoded file is not re-bounded: over 200 entries, over-length text, duplicate ids, or `count == Int.max` traps on `+= 1` at `FrontDoor.swift:253`. Only reachable by local tampering; the file is excluded from backup, so it cannot arrive by restore.

### Hardened-invariant producers (V3C-101)
Invariant: "an Elo score is displayed against the pinned anchor only."

| Producer | Pinned by |
|---|---|
| `main.py:1246` | `test_uncertainty_contract.py:271` |
| `PickRow` (`ContentView.swift:158`) | `test_ios_client_contract.py:559` |
| `figuresLine` calls in PickRow / RankedRow | `test_every_score_on_screen_goes_through_the_figures_line` |
| RankedRow in the preview (`:402`) | **no test** (M-4) |
| RankingList (`:418`) | **no test** (M-4) |

### Acceptance evidence
| REQ | Evidence | Status |
|---|---|---|
| REQ-GAP-001 | `FrontDoorTests.swift:539,551,562,580,595`; `test_router_hints.py:198` | met, with the m-1 hole |
| REQ-GAP-002 | `FrontDoorTests.swift:569`; sheet at `ContentView.swift:337-368` | met |
| REQ-SCR-001 | — | **not met** (M-1) |
| REQ-SCR-002 | `ScoresTests.swift:168` (synthetic only) | partial (m-2) |
| REQ-SCR-003 | `test_uncertainty_contract.py:271` (server only) | partial (M-4) |
| REQ-SCR-004 | — | **not delivered as planned** (M-2) |

## (B) Security findings (pulled-forward seat)

No BLOCKING or MAJOR security finding.

### MINOR
- **S-1: File protection class not set.** `FrontDoor.swift:301` writes with `.atomic` only, so the free text gets the default `CompleteUntilFirstUserAuthentication` class. It is readable while the phone is locked after first unlock. Use `[.atomic, .completeFileProtection]`; the register is only written and read in the foreground.
- **S-2: Backup exclusion is correct but fails silently.**
  - Re-applying `isExcludedFromBackup` after *every* atomic write is correct. The rename replaces the inode and drops the attribute; `:301-305` sets it again.
  - `var target = url; try? target.setResourceValues(values)` works: `setResourceValues` is `mutating` only for URL's cache and writes to the file system.
  - Residual risk: the `try?` swallows a failed exclusion, and there is a small window between rename and flag.
  - More robust: put the file in a dedicated subdirectory and set the exclusion on the directory, which survives file replacement.
- **S-3: The size bound counts Characters, not bytes.** `prefix(Self.maxLength)` at `:249` counts grapheme clusters. `"e"` followed by 10,000 × U+0301 is one Character, so 200 "characters" can be megabytes, times 200 entries. Only the reader can do this, to their own device (pasted text). Bound on `utf8.count` or `unicodeScalars`.
- **S-4: `scoreOutOf100` checks `anchor.isFinite` only** (`Uncertainty.swift:174`), not the project's own `inRange` principle ("-1e19 is perfectly finite", `Language.swift:253`).
  - A broken engine sending `score_anchor: 1e300` makes every row read "Score 0 / 100"; `-1e300` makes every row read "100". No crash, but a whole board of false ties.
  - NaN cannot arrive as JSON. A non-numeric value fails decoding of the whole category list, which is pre-existing behaviour for every optional field.
  - Suggest rejecting an anchor more than about 2000 Elo from the score, or reusing `inRange`.

### NIT
- **S-5: Anyone holding the phone can open the register.** It sits behind an unlabeled tray icon, and it is on every reader's device, not just the owner's. Also, the owner only ever sees questions typed on his own phone. That is by design, but the M15 "input to coverage work" framing assumes more.

### Verified clean
- **Logging:** no `print`, `Logger`, `os_log` or `NSLog` anywhere in `ios/ModelRanking`.
- **Network:** no network symbol in the register code. The only network path is `EngineClient`. Engine calls are pinned to bare `task` / `budget` arguments by `test_router_hints.py:125`.
- **Display:** `Text(entry.question)` takes a String variable, so it renders verbatim with no Markdown or localisation interpretation.
- **Corrupt file:** loads as an empty register (tested at `:595`) and is overwritten on the next save.
- **Location:** Application Support inside the app container; the directory is created on first save.
- **`score_anchor` leaks nothing new.** `min_quality` is already served in prose ("clears the 1400 Elo minimum-quality bar").

## C1–C6

| Claim | Verdict | Evidence |
|---|---|---|
| C1: every Swift change compiles | **VERIFIED (by reading)** | See detail below. |
| C2: typed text never reaches the engine; the register never leaves the device | **VERIFIED** | Register code has no network symbol. Engine-argument data-flow test at `test_router_hints.py:142-165`. File excluded from backup. No logging. Caveat: the new gate at `:198` checks only the register section of FrontDoor and `client.` calls; any other egress added in ContentView (e.g. a URLSession) would not be caught. |
| C3: strictly monotonic, cannot reorder; ranges and ties unchanged | **VERIFIED** | Logistic in `score` for a fixed finite anchor. Live: monotone on all 4 Elo boards. `rankRanges` is still fed `answer.ranking.map(\.score)` and the native margin. Display caveat: at one decimal, distinct native values collapse (assistant: 13 duplicate displayed values vs 2 native). No inversion, but more visual ties. |
| C4: the anchor is pinned data, never the board maximum | **VERIFIED, narrowly** | `spec.min_quality`, a constant, never the maximum. But it is a recalibrated board-third quantile and the Budget-Pick floor (M-3), and the client-side rows are unpinned (M-4). |
| C5: `SORTING_PERMITTED` is narrow | **REFUTED** | See mutants below. |
| C6: no existing Swift test expectation broken | **VERIFIED** | See detail below. |

**C1 detail.** Each point below checks out:
- Memberwise order matches the declared order for PickRow (…, `secondaryAgeDays`, `anchor`), RankedRow (`row`, `rank`, `language`, `anchor`) and RankingList (`answer`, `@State filter`, `language`, `ranges`, `leaderNote`, `anchor`). `anchor` is `Double?`, so it has an implicit nil default.
- `(Int, Date) <` / `>` use the standard-library Comparable tuple operators; Date is Comparable.
- The closure in `min(by:)` inside a `mutating` method reads `entries` through `Range` indices, so there is no exclusivity overlap.
- `gaps.record(...)` in the non-mutating `ask()` works because `State.wrappedValue` has a nonmutating setter.
- `URLResourceValues` / `setResourceValues` on a `var` copy is valid.
- `(try? data.write(...)) != nil` on `()?` is valid.
- `lowercased(with:)` and `pow` come from Foundation, which FrontDoor.swift and Uncertainty.swift import.
- Public / internal access is consistent: the public `GapEntry.id` calls the internal `gapKey` from a non-inlinable body. Tests use `@testable`.
- `.nan` against `Double?` resolves through Optional.
- `scoreOutOf100` covers all four `ScoreForm` cases, so the switch is exhaustive.
- `ToolbarItem(.topBarLeading)`, `accessibilityLabel(String)` and two `.sheet` modifiers are all fine on iOS 18.
- Nothing in the new tests is Swift-6-concurrency sensitive.

**C5 mutants.** The key matches any line in `FrontDoor.swift` that contains `entries.`:
- `ranking.sorted(by: >)`: **fails the gate** (good).
- `ranking.sorted(by: >).filter { _ in !entries.isEmpty }`: **passes**.
- `extension Answer { var entries … }` followed by `a.entries.sorted { $0.score > $1.score }`: **passes**.

It is a tripwire on spellings, as the test itself admits, not a narrow exemption.

**C6 detail.** Every existing `scoreText` / `figuresLine` call (`ScoresTests.swift:11-82`) omits `anchor`. The default is nil, and the nil path is byte-identical to before. No function references are taken, so the changed signature does not matter. `Category` is never built memberwise, and it decodes `score_anchor` with `decodeIfPresent`.

## W4 product effect on the live artifact

What the leader and the picks read out of 100, all surfaces, `budget=unlimited`.

| Surface | Metric | Anchor | Leader | Best value | Budget pick | Last row |
|---|---|---|---|---|---|---|
| web-dev | Elo | 1478.9 | Claude Opus 5 1711.9 → **79.3** | 69.3 | 63.7 | 13.0 |
| assistant | Elo | 1400 | Claude Fable 5 1507.6 → **65.0** | 61.6 | 54.6 | 37.9 |
| factuality | Elo | 1450.6 | Claude Fable 5 1500.7 → **57.2** | 54.4 | 51.2 | 37.4 |
| document | Elo | 1467.5 | Claude Opus 5 1516.3 → **57.0** | 52.2 | 50.6 | 40.9 |
| mathematics | % correct | — | **100.0** | 94.4 | 94.4 | 6.4 |
| abstract | % correct | — | **98.0** | 96.5 | 88.0 | 4.5 |
| expert | % correct | — | **94.4** | 91.0 | 91.0 | 49.2 |
| computer-use | % resolved | — | **84.7** | 80.2 | 61.6 | 17.1 |
| coding | % resolved | — | **83.5** | 78.7 | 70.0 | 28.7 |
| agentic-coding | % resolved | — | **72.8** | 69.4 | 53.8 | 11.8 |
| everyday | ECI | — | rank only | rank only | rank only | rank only |

**Plainly: yes, readers will misread the surfaces against each other.**
- Percentage leaders read 73–100. Elo leaders read 57–79, and the two newest surfaces' best models read about 57, "barely above the bar".
- The same model, DeepSeek V4 Flash, reads **54.6** on chat, **63.7** on web-dev, **91.0** on expert and **94.4** on mathematics.
- A reader will conclude it is weak at chat. What the numbers actually say is "a percentage of questions answered" on one surface and "a 55% preference rate against a top-third model" on the other.
- The best document model (57.0) reads lower than coding's budget pick (70.0).
- This is exactly the cost D-143 names, and it is made worse by anchoring at the *top-third* floor. That choice compresses Elo leaders towards 50 by design, while a percentage leader's 100 is the benchmark's ceiling.
- D-143's revisit trigger ("a reader compares two surfaces' scores out loud and gets a wrong answer") is very likely to fire.
- For the owner, not necessarily a defect: consider an anchor whose 50 is not "the recommendation bar", or a visible per-surface cue on each card.

## Verdict
**BLOCKING.** The single blocker is B-1: a `/v1` field added in M14 without an ADR, against the owner's "No K.8 change in M14". It is fixed by an owner-signed record, not by code. No compile error was found in any Swift change. MAJORs M-1 to M-4 should be fixed or formally amended before the W5 closure seat. Security has no blocker, and S-1 to S-3 are cheap hardening.

## Findings and disposition (author, 2026-09-20, after the seat)

| # | Finding | Disposition |
|---|---|---|
| B-1 | `score_anchor` widens `/v1/categories` against "No K.8 change in M14", with no ADR | **FIXED by record.** D-146 names the field and amends the ruling for `/v1/categories` only; **accepted by the owner 2026-09-20** |
| M-1 | Why and trade-off sentences still print native Elo beside a /100 score | **FIXED.** `anchoredFact` restates `behind_by`, `window` (distances below the leader) and `floor` (a position) on the /100 scale, unit `points`, all or nothing. `PickRow` routes both sentences through it. The seat's own case now reads "3.4 points behind" (`OutOf100SentenceTests`) |
| M-2 | Leader note gives the margin in Elo; plan said ranges re-derive from a converted margin | **FIXED + AMENDED.** Ranges stay native (identical ties; D-146 clause 3, plan W4 amendment). The sentence states the margin in points below the leader (`testTheLeaderNoteSpeaksPointsWhenAnchored`) |
| M-3 | The anchor is `min_quality`, which each recalibration moves | **FIXED.** `CategorySpec.score_anchor`, pinned; `test_a_recalibration_cannot_move_the_anchor`; values pinned in `PINNED_SCORE_ANCHORS` |
| M-4 | A board-max anchor on the preview rows and full list passed every test | **FIXED.** `test_ios_client_contract.py` pins `anchor: category(for: answer)?.scoreAnchor` in `RankedRow(` and `RankingList(`, and refuses any `anchor:` built from `.max(`/`.min(` |
| m-1 | Router failures logged as gaps | **FIXED.** `recordsGap(outcome)` = unmeasured and not manual; `GapRegisterHardeningTests`; the view contract now requires it |
| m-2 | Monotonicity only on a synthetic stride | **FIXED.** `testTheConversionNeverReordersOnAnyPinnedAnchor`: all four pinned anchors, ±400 Elo at 0.1 |
| m-3 | `SORTING_PERMITTED` matched a line substring | **FIXED** (W-097). Each sort call is checked by its receiver |
| m-4 | Synchronous disk read in the `@State` initialiser | **ACCEPTED.** The file is bounded at 200 entries × 800 bytes; moving the load to `.task` opens a race where a question recorded before the load completes is overwritten. Revisit if the bound grows |
| S-1 | No file protection | **FIXED.** The phone's store writes `[.atomic, .completeFileProtection]` (a store parameter, because the Engine may not use `#if os`) |
| S-2 | Backup exclusion re-applied per file, failure swallowed | **FIXED.** The register lives in its own `GapRegister/` folder, excluded from backup; the file is still marked too |
| S-3 | Length counted in characters, not bytes | **FIXED.** `maxBytes = 800`; combining-mark test |
| S-4 | Any finite anchor accepted | **FIXED.** More than 2000 Elo from the score → no conversion, native scale kept |
| Product effect | Elo leaders read 57–79 against percentage leaders 73–100 | **ACCEPTED by the owner 2026-09-20 (option A)**, recorded in D-146's cost paragraph |
