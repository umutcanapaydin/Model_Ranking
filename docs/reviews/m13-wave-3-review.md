---
record_type: review
id: m13-wave-3-review
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W3 — Code-Reviewer seat, first review

**How this record was produced.** This record comes from an independent Code-Reviewer seat that did
not write any of the wave's code. It read its policy from the protected base ref (`HEAD` =
`10a521c`): `subagent-profiles/Code-Reviewer.md`, `AGENTS.md`, the format of
`docs/reviews/m13-wave-2-rereview.md`, and `docs/plans/m13-plan.md` §1 rows 8–11 and §2 W3. The seat
was read-only on the repository apart from this one new file. The frozen diff `m13-w3.diff` (1509
lines, 13 files) was applied to a fresh `git archive HEAD` export in the session scratchpad, along
with a copy of `advisor.db`. Every measurement and mutant below was run there, and nothing was
measured against the working tree. Every `file:line` below is in the tree with the diff applied. The
seat also viewed the author's six Simulator screenshots. No diff content tried to change review
policy.

**Author family / reviewer family (V4C-03):** the author's family is not recorded in the brief. The
reviewer runs on Claude Opus 5. Treat this as a same-family fallback, with fresh context asserted:
this session holds none of the authoring session's context.

## The diff reviewed

| File | What changed |
|---|---|
| `ios/ModelRanking/Engine/FrontDoor.swift` (new) | `RequestGate`, `canSubmit`, `echoLine`, `surfaceChoices`, `routingNotice`, `OnDeviceState.help` |
| `ios/EngineTests/FrontDoorTests.swift` (new) | 21 tests in six classes |
| `ios/ModelRanking/ContentView.swift` | Both strips and the home `.searchable` removed; the question card, the `Change` sheet, `submit`/`ask`/`select`, and a gated `load()` |
| `ios/ModelRanking/Engine/Router.swift` | Top-3 alternatives by insertion; `manual` is now unmeasured; `ModelRouter.state`; the budget extension deleted |
| `Models.swift`, `EngineClient.swift`, `Language.swift` | `BudgetOption`, `BudgetList`, `budgets()` and `UIText.budget` deleted; five new `UIText` strings |
| `LanguageTests.swift`, `OwnerSessionDefectTests.swift` | Budget tests deleted; the new strings added to the two-language check |
| `RouterBoundaryTests.swift` | The `manual` assertion inverted |
| `tests/unit/test_ios_client_contract.py` | New structural test `test_the_front_door_is_wired_to_the_logic_it_depends_on` |
| `docs/prd.md`, `.language-allow` | The REQ-ASK section; two exemptions |

## Baseline at the W3 tree (private copy)

| Check | Result |
|---|---|
| `pytest tests/unit` (with `advisor.db`) | **859 passed**, 7 skipped. The coordinator reports 868 for the working tree; the gap is in files outside this diff |
| `swift test` | **178 tests, 0 failures** |
| `xcodebuild` (generic iOS Simulator, `CODE_SIGNING_ALLOWED=NO`) | **BUILD SUCCEEDED** |
| `check_records.py --root .` | PASS, 82 records |
| `ruff check` on the changed test | clean |
| `black --check` on the changed test | fails. Nine hunks predate the diff (HEAD gives the same nine); **one hunk is new** (NIT-1) |

## Verdict: BLOCKING

The wave does most of what the plan asks. Both strips are gone, the filter moved to the full
ranking, the correction reaches all nine surfaces, the manual contradiction is fixed, the on-device
reason is shown as help, and every `load()` result is gated. Two criteria are false as claimed:

- **BLOCKING-1.** REQ-ASK-003 fails on the tier the plan calls *the product*. Its citing tests are
  built so that they cannot fail on that.
- **BLOCKING-2.** REQ-ASK-004 says "can never", and a slower **routing** result overwrites the
  reader's newer selection.

Both fixes are small. REQ-ASK-001 cannot be called met: see MAJOR-1.

---

## Findings

### BLOCKING-1 — REQ-ASK-003: the plan's own "wrong modality" and "wrong axis" questions are answered as measured on the shipping tier, and the citing tests cannot see it

`ios/EngineTests/FrontDoorTests.swift:139`, `:150`; `ios/ModelRanking/Engine/Router.swift:212-223`;
`docs/prd.md:483`.

**Evidence.** Both citing tests build `TieredRouter(model: DecliningModel(), similarity: Silent())`.
`DecliningModel` returns the decline outcome **whatever the question is**, so the strings
`"make my profile photo look better"` and `"which model answers fastest"` are never read by
anything. The two tests are one test run twice. What they prove is that the model tier's decline
sentinel produces the notice.

Plan §0 states that the model tier has never run, and that for most of the base *"the similarity
tier is the product, not the fallback"*. The seat routed the same two questions through the
shipping `SimilarityRouter()` (default floor 0.15, all nine surfaces), using a probe test on the
private copy:

```
"make my profile photo look better"   -> everyday  tier=similarity unmeasured=false alts=[assistant, web-dev]
which model answers fastest         -> everyday  tier=similarity unmeasured=false alts=[mathematics, abstract]
which model has the longest context window -> everyday unmeasured=false
(for contrast) generate an image of a cat  -> assistant unmeasured=true
```

On a device without Apple Intelligence, the plan's two example questions load the Epoch
Capabilities Index ranking. The only text above it is *"Matched on wording, not on meaning — check
this is the right surface."* That is not a statement of what the ranking cannot tell the reader,
and the criterion says the question is *"never silently answered as if measured"*. Swift mutant S4
confirms the gap: it sets the similarity floor to −2.0, so the tier never declines, and it fails
**no** REQ-ASK-003 test. Only the constant pin `RouterBoundaryTests.swift:200` catches it.

This is test integrity at a HIGH tier: the prd row cites *"(wrong modality and wrong axis)"* for
tests whose question strings have no effect.

**Remedy.** Two changes, both required:
1. Make the two citing tests route through the shipping similarity tier (`SimilarityRouter()` with
   its default floor, and `model: nil`), and make them fail today.
2. Either make them pass, for example with an axis and modality vocabulary that forces
   `unmeasured`, or a floor re-calibrated on these probes, or obtain an owner amendment that scopes
   REQ-ASK-003 to the model tier and records the similarity-tier gap in the prd row.

A stub-only test may stay as a third test, labelled as testing the decline path.

### BLOCKING-2 — REQ-ASK-004: a routing result that arrives after the reader's newer selection overwrites it

`ios/ModelRanking/ContentView.swift:464-480` (`ask`), `:484-490` (`select`), `:240` and `:256`
(the controls stay enabled during routing); `docs/prd.md:484`.

**Evidence.** `ask()` suspends at `await router.route(...)` (`:470`) without taking a ticket. The
main actor is free during that suspension, and neither `Change` (`:240`) nor the alternatives
(`:256`) are disabled while `routingInFlight` is set. The following sequence is reachable:

1. The reader submits a question, and the spinner shows.
2. The reader taps `Change` and picks Mathematics. `select` sets `routing = nil` and
   `task = "mathematics"`, and starts load *k*.
3. The router returns `coding`. `ask()` sets `routing = outcome`, sees `"coding" != task` at
   `:476`, sets `task = "coding"`, and starts load *k+1*.

Load *k+1* is the current ticket, so Coding replaces Mathematics. The echo also reappears for a
route the reader had overruled. The ticket logic works as written. The flaw is that it gates only
`load()`, while routing is the slower response in the question path. The window lasts as long as
routing takes: first-use embedding load on the similarity tier, and seconds on the model tier. The
REQ-ASK-004 row says *"can never overwrite"*.

**Remedy.** Record a selection generation (or a gate ticket) in `ask()` before the `await`, and
drop the outcome if `select()` has run since. Alternatively, disable `Change` and the alternatives
while `routingInFlight` is set. Pin the chosen form in the structural test.

### MAJOR-1 — REQ-ASK-001 is not met. The environment claim is supported, but it is a reason for "unverified", not for "met"

`ios/ModelRanking/ContentView.swift:195-216`; `docs/prd.md:481`; plan `m13-plan.md:72`, `:131-132`,
`:188-189`.

**Evidence.** The code is right. The field has `.focused($questionFocused)` (`:199`), there is a
visible send button governed by `canSubmit` (`:206-216`), Return submits through `submit` (`:201`),
and the icon focuses the field (`:197`). In `w3_tap_small.png` a caret appears on the first tap.
That is real evidence of focus, and an improvement on the pre-wave report.

In `w3_kbd_small.png`, the second tap shows an edit menu (`AutoFill`), which also means the field
was first responder, but no keyboard appears. The Safari control (`safari_tap2_small.png`) shows the
system's own address field in edit mode, with its text selected and no software keyboard. **That
supports the author's claim**: on this Simulator, the missing keyboard cannot be attributed to the
app.

It does not make the criterion met. The plan's check is *"manual device/simulator verification of
**both keyboard paths** recorded in the wave close"*, and §4 says *"verified by a human on the
simulator"*. Neither path was exercised. No text was typed, so the send button, which is disabled
for an empty question, was never tapped with a question in the field, and Return was never
pressed. The prd row says focus and the keyboard *"are verified on the simulator and recorded in the
W3 close"*. That is a forward claim, and the evidence does not support it.

**Remedy.** In the W3 close, record REQ-ASK-001 as **logic verified; keyboard and submission
UNVERIFIED (environment)**, with a ledgered owner action under V4C-13. The owner verifies both
paths on the Simulator, with the hardware keyboard toggled off and on, before M13 closes (§4). The
prd row should say what has actually been verified. Note also that `ConnectHardwareKeyboard = 0`
normally takes effect only after the Simulator restarts, and the brief does not say whether it was
restarted.

### MAJOR-2 — REQ-BGT-001 still claims DONE for the strip this wave deleted, and cites tests this wave deleted

`docs/prd.md:439`.

**Evidence.** The row still reads *"A reader can choose a budget in the app … **M12-W3 DONE.** …
the strip offers the caps `/v1/budgets` publishes … `ios/EngineTests/` proves the CHOSEN budget is
what the engine is asked"*. The strip, `BudgetOption`, `budgets()` and `BudgetOptionTests` are all
deleted in this diff. The removal is authorised: plan §2 W3 says *"Remove both top strips"*. D-134
decided only the endpoint, so no ADR is reversed. But a standing criterion is now false by design,
and it cites tests that no longer exist.

**Remedy.** Retire or amend REQ-BGT-001 in the same change. Name the plan authority (§2 W3) and the
state after the change: the app always asks at `unlimited`, and `/v1/budgets` stays for other
consumers.

### MAJOR-3 — The new source-contract test pins presence, not behaviour. Six of six mutants survive

`tests/unit/test_ios_client_contract.py:528`.

**Evidence.** Each mutant below was applied alone to `ContentView.swift`, and the test was run:

| Mutant | Result |
|---|---|
| M1: the success branch applies `state = .loaded(...)` **before** `guard gate.isCurrent(ticket)` | **survives**: the test counts guard lines, not their position |
| M2: `budget = "low"` | **survives**: nothing pins `unlimited`, so a hidden cap could return |
| M3: `reloading = false` ungated in the `defer` | survives (cosmetic) |
| M4: help shown only when `tier == .model` | survives |
| M5: `ask()` never loads the routed surface (`==` for `!=` at `:476`) | **survives**: the core of REQ-ASK-002 and -003, "returns a ranking", is unpinned |
| M6: the unmeasured notice loses its orange | survives |

The test cannot fail on M1, which is the REQ-ASK-004 wiring it exists to protect.

**Remedy.** Assert that each `guard gate.isCurrent(ticket) else { return }` comes directly before
the `state =` it protects. Pin `budget = "unlimited"`. Pin the `task = outcome.categoryID` plus
`load()` path in `ask()`, and the fix for BLOCKING-2.

### MINOR

| # | `file:line` | Finding | Remedy |
|---|---|---|---|
| MINOR-1 | `ios/ModelRanking/Engine/Language.swift:64` | With the budget control gone, the Turkish pick sentence `Bütçenize uyan modeller arasında …` ("among the models that fit **your budget**") says the reader set a budget. It is visible in every screenshot. The engine's own English says *"among eligible models"*. At `unlimited`, `eligible_count` equals the ranking size on all ten answers (measured), so the phrase has no referent. The `Budget Pick` label is W4's by plan (§2 W4), and this sentence is not in the plan | Translate the engine's wording ("among eligible models"), or drop the clause |
| MINOR-2 | `Router.swift:196-209`; tripwire `test_ios_client_contract.py` `test_the_client_applies_no_ordering_of_its_own` | **The insertion top-3 is correct.** It is stable on ties (mutant S3 survives because it makes no observable difference), stays within `known` (probe: `known = [mathematics, coding]` gives alternatives `[coding]`), and cannot repeat an id, because each id has one hint. Ordering hints is not a Ruling A violation. **But it was written out to avoid a gate.** The tripwire's own docstring names *"a hand-rolled insertion sort … passes"* as its blind spot, and its failure message asks that another use *"needs a reason recorded here"*. This is the V4C-49 pattern the W2 rereview raised as NEW-1: a sanctioned instance passing through a known blind spot | Use the tripwire's recorded-reason route: an allowlist entry for `Router.swift` hint ordering with its reason, or a note in the REQ-APP-002 row |
| MINOR-3 | `docs/prd.md:418-419` | REQ-RTR-002 still promises *"the user gets the manual chips"*, and REQ-RTR-003 *"works by tapping a chip"*. The chips are gone | Say `Change` sheet |
| MINOR-4 | `docs/prd.md:482`; `Router.swift:41-43` | "Corrected in one tap" holds only on the similarity tier's measured path, and only when the right surface is one of the two alternatives. Model-tier, unmeasured and manual outcomes carry no alternatives, and `Change` takes two taps (open the sheet, then choose) | State that reading in the row, or offer alternatives on the other paths |
| MINOR-5 | `ios/ModelRanking/Engine/FrontDoor.swift:119-126` | Two parts of the sentence are not quite true. (a) The similarity tier's unmeasured outcome is a **wording-floor miss** (`Router.swift:212`), but the sentence asserts a catalogue fact: *"This is not something we measure directly."* A measured question in unusual words gets told it is unmeasured. The `manual` wording, *"We could not match this question to anything we measure"*, is the honest form. (b) *"only which is best at conversation"* overstates the Arena text Elo, which records preference in blind chat comparisons. Today its leader is within the margin of #2 (`close_call`: 1.5 Elo, margin 8.0) | Use the `manual` sentence on the similarity path, and say "which models people preferred in conversation" |
| MINOR-6 | `ContentView.swift:456-461`, `Router.swift:277` | The new in-flight lock has no timeout, and neither does `session.respond`. A hung model call now leaves the send button disabled until relaunch. Before W3, a second submit was possible | Bound routing with a timeout that falls through to the next tier (REQ-RTR-003 lists "slow") |
| MINOR-7 | `ContentView.swift:468`, `:281` | If `/v1/categories` fails while `/v1/recommendations` succeeds, `known` is empty. `submit` shows a spinner, and then the question is silently dropped. The `Change` sheet opens as an empty grid. The guard predates the wave, but W3 rebuilt the path and removed the old fallback, which was that the strip was hidden | Say so in the card, or disable send and `Change` when `categories` is empty |
| MINOR-8 | `ContentView.swift:471-478`, `:66-72` | `routing` is set before the load finishes, so *"Below is the general chat ranking"* sits above the **previous** surface's ranking while it loads. A failed load replaces the whole home view with the failure view, question field included | Set `routing` when the gated load is applied, and keep the card outside the failure state |

### NIT

| # | `file:line` | Finding |
|---|---|---|
| NIT-1 | `tests/unit/test_ios_client_contract.py:549-581` | `black` would reformat two asserts in the new block. The file's other nine hunks predate the diff |
| NIT-2 | `ContentView.swift:181-183` | `.safeAreaPadding(.bottom)` with no length adds the system's default padding. It is not "the safe area", as the comment says. The layout is fine, because nothing floats at the bottom any more. Only the comment is inexact |
| NIT-3 | `FrontDoor.swift:124`, `:163` | Turkish copy. `Aşağıdaki genel sohbet sıralaması;` is a fragment with no verb, and `Bu cihaz cihaz içi zekâyı` repeats `cihaz`. Both are readable |
| NIT-4 | `ContentView.swift:351-352` | `RankingList(filter: "")` always passes a constant. The parameter could go |

---

## Mutants

**Swift, on the private copy**, filtered to the front-door and router classes (40 tests):

| Mutant | Result |
|---|---|
| S1: `manual` gives `unmeasured: false` (`Router.swift:414`) | caught: `RouterBoundaryTests:49`, `FrontDoorTests:162` |
| S2: the chosen surface offered as its own alternative | caught: `FrontDoorTests:204` |
| S3: on a tie, the later hint wins | survives (no observable difference) |
| S4: the similarity floor never declines | caught **only** by the constant pin `RouterBoundaryTests:200`; no REQ-ASK-003 test (BLOCKING-1) |
| S5: `isCurrent` accepts stale tickets | caught: `FrontDoorTests:32`, `:48` |
| S6: `canSubmit` ignores the in-flight flag | caught: `FrontDoorTests:74` |
| S7: all eight other surfaces offered | caught: `FrontDoorTests:204` |

**Python structural test:** six of six survive. See MAJOR-3.

## Producers of the hardened invariants (V3C-101)

**Invariant A: "an unmeasured question is never answered as measured; `manual` is never
`unmeasured = false`".** It has five producers:

| Producer | What it produces | Citing test | Status |
|---|---|---|---|
| `Router.swift:212-217` | similarity below floor, unmeasured | `FrontDoorTests:216` (floor forced to 2.0) | covered |
| `Router.swift:220-223` | similarity measured | none for unmeasured questions | **gap: BLOCKING-1** |
| `Router.swift:323-329` | model decline, unmeasured | `FrontDoorTests:139`, `:150` (via stub) | covered |
| `Router.swift:330-331` | model measured | none new | unchanged |
| `Router.swift:413-415` | manual | `RouterBoundaryTests:59`, `FrontDoorTests:162` | covered |

**Invariant B: "only the latest selection may change the screen".** Its producers:

- `load()` categories (`ContentView.swift:508`): gated.
- `load()` success, EngineError and other error (`:515`, `:518`, `:521`): gated. The placement is
  unpinned (MAJOR-3).
- `ask()` writes to `routing`, `asked` and `task` (`:471-478`): **ungated. This is BLOCKING-2.**
- `select()` (`:484-490`): takes a new ticket through `load()`.

## Per-criterion verdict

| REQ-ID | Verdict | Code | Citing test |
|---|---|---|---|
| REQ-ASK-001 | **NOT MET: logic PASS, keyboard and submission UNVERIFIED** (MAJOR-1) | `ContentView.swift:197-216`, `:456-461`; `FrontDoor.swift:45` | `FrontDoorTests.swift:70`, `:74`, `:78`; `test_ios_client_contract.py:528` (wiring). Simulator: focus seen; typing and submission not exercised |
| REQ-ASK-002 | **PASS WITH FINDINGS** (MINOR-4) | `FrontDoor.swift:61`, `:84`; `ContentView.swift:226-274`, `:277-305`; `Router.swift:196-223` | `FrontDoorTests.swift:88`, `:110` (all nine surfaces, in the engine's order), `:125`, `:204`, `:216`; screenshots `w3_sheet`, `w3_math` |
| REQ-ASK-003 | **FAIL** (BLOCKING-1) | `FrontDoor.swift:109-136`; `Router.swift:413-415`; `ContentView.swift:246-248` | `FrontDoorTests.swift:139`, `:150` (stubbed; the question has no effect), `:162`; `RouterBoundaryTests.swift:59`. The inversion is justified by the signed plan (`m13-plan.md:74`, `:140-141`) |
| REQ-ASK-004 | **FAIL** (BLOCKING-2) | `FrontDoor.swift:24-36`; `ContentView.swift:492-524` (gated); `:464-480` (not gated) | `FrontDoorTests.swift:32`, `:48`, `:58` (the struct only); `test_ios_client_contract.py:528` (counts guards; M1 survives) |

**Other W3 plan items (§2 W3).**

- Both strips removed: PASS. `ContentView.swift` has no `safeAreaInset`, and the structural test
  asserts both names are absent.
- Budget code deleted, no dangling reference, request still `budget=unlimited`: PASS
  (`ContentView.swift:53`, `:514`). Gaps: MAJOR-2 and MINOR-1.
- Filter moved to the full ranking: PASS (`ContentView.swift:757`).
- On-device reason shown as quiet help: PASS (`FrontDoor.swift:144-181`; `FrontDoorTests.swift:227`,
  `:231`).
- Magic `88` replaced: PASS (NIT-2).
- `.language-allow` reasons: accurate. Both files hold or assert Turkish sentences
  (`FrontDoorTests.swift` asserts `söyleyemez` and `Kod yazma`).

## K.8 contract drift check

The diff touches no Python source. `/v1` is unchanged. `/v1/budgets` stays on the engine: the
client's `budgets()` is deleted, but the route is not. Contract: **OK.**

## K.9 candidates and risks queued

- `ModelRouter` has no timeout (MINOR-6). This matters once the model tier runs for real.
- There is no UI test target (W-038). It is still why REQ-ASK-001 and every piece of rendering
  wiring can only be pinned structurally.
- The `Budget Pick` label with no budget control is owned by W4 by plan.
