---
record_type: wave
id: m13-wave-3-close
status: draft
process_version: v5.0
date: 2026-09-15
---
# Wave-Close Checklist — M13 Wave 3 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The question is the front door.** The home screen has one input. The category strip and the
budget strip are gone. The nine surfaces sit behind a `Change` sheet, reached from the row that
echoes what the router understood (`“prove a theorem” → Mathematics`), and the wording tier's next
two surfaces appear as one-tap alternatives. An unmeasured question is answered with the chat
ranking AND with the sentence saying what that ranking cannot tell. A slower answer, whether a load
or a routing, can no longer replace the choice the reader has since made.

**The wave closed on its second review round.** Both seats returned BLOCKING on the first round,
independently and on the same two criteria:
- **REQ-ASK-003's citing tests** stubbed a model tier that declined whatever it was asked. On the
  wording tier, which plan §0 calls the product, the plan's own photo and speed questions went to
  `everyday` as MEASURED answers.
- **REQ-ASK-004 gated loads but not routing.**

Both are fixed at the root. The wording tier gained a decline exit, and routing gained its own
ticket. The tests now route the real questions through the shipping tier.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m13-plan.md` §2 — "W3 — The question is the front door (risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | `make check` exit 0 at 869 Python / 191 Swift; `xcodebuild` (iOS Simulator) exit 0; the app was run on the iPhone 17 Pro simulator against `advisor.db` (ledger L2). New files: `ios/ModelRanking/Engine/FrontDoor.swift`, `ios/EngineTests/FrontDoorTests.swift`, and two source-contract tests in `tests/unit/test_ios_client_contract.py` | ✅ |
| 3 | Review per tier: HIGH → Code-Reviewer + Tester separately | `docs/reviews/m13-wave-3-review.md` (BLOCKING: REQ-ASK-003 and -004 false as claimed), `docs/reviews/m13-wave-3-rereview.md` (PASS WITH FINDINGS: both BLOCKING and all three MAJOR discharged, all six original contract mutants and four new Swift mutants caught. It raised NEW-1 (MAJOR: the decline hints declined three measured tasks), NEW-2 (three contract mutants survive), NEW-3 (the losing model call is never cancelled) and NEW-4 (a wrong ruling citation). All four were then fixed, NEW-1 as a measured trade-off: ledger L5), `docs/reviews/m13-wave-3-rereview-2.md` (PASS WITH FINDINGS: NEW-1's one-tap decline ENDORSED as a design choice, NEW-2 to NEW-4 discharged), `docs/reviews/m13-wave-3-tester.md` (BLOCKING, 26/44 killed), `docs/reviews/m13-wave-3-tester-rerun.md` (PASS WITH FINDINGS: B1, B2 and B3 cleared, 59/72 killed, `Router.swift` line coverage 97.64% against HEAD's 96.36%). Every record is `seat: independent`, from a separate session, against the frozen diff | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | **WAIVED** — ledger L1. No auth, PII, payment, crypto or migration surface, and no server change at all. Stage 4.0 covers the milestone per `docs/plans/m13-plan.md` §2 W5 and `docs/closure-checklist.md` | WAIVED |
| 5 | Tester fault-injection: break → RED → reverted byte-identical; every stay-GREEN fault got a new test | `docs/reviews/m13-wave-3-tester.md`: 44 trials, all md5-clean. Its survivors now have tests: the contract-test pins for WF3b/5/5b/8/9/10/11/12/13/14/17, plus `EchoTests` (EL1a/c), `UnmeasuredQuestionTests` (RN1t/2t), `AlternativeSurfaceTests` (SA6) and `OnDeviceHelpTests` (B3). The re-run, `docs/reviews/m13-wave-3-tester-rerun.md`: 72 trials, all md5-clean, 59 killed, including 15 of the 17 round-1 survivors. Each survivor it named now has a test: RN2t/RN3t `testAMeasuredMatchDoesNotSayItCannotTellInTurkish`; FW2 `testAFastAnswerSurvivesTheDeadlineFiringAfterIt`; RGV3, AK1 and CE the source-contract pins; SA5d `testADeclineNeverOffersTheChatRankingItIsAlreadyShowing`. Its over-decline MAJOR is the re-review's NEW-1, answered by the one-tap design (ledger L5) and extended to its own two questions (`testTheTestersOverDeclinesStayWithinOneTapOfAReasonableSurface`). DC4 and OS1 are ledgered (L7); there was no third tester round, because every survivor it named has a test | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | **REQ-ASK-001:** `ios/EngineTests/FrontDoorTests.swift::SubmissionTests`, plus the source-contract test pinning `.focused`, `.onSubmit(submit)`, `Button(action: submit)`, the synchronous in-flight flag and its `defer`. **REQ-ASK-002:** `EchoTests`, `AlternativeSurfaceTests`, and the pinned Change → sheet → `select` path. **REQ-ASK-003:** `UnmeasuredQuestionTests`, routing the photo, speed and context-window questions through the SHIPPING `SimilarityRouter`, with the M10 probe held; also the inverted `RouterBoundaryTests.testWithNoTierAtAllTheReaderStillGetsASurface`. **REQ-ASK-004:** `RequestGateTests` (loads, plus `testASelectionMadeWhileAQuestionRoutesWins`) and the contract test's guard-position and routing-ticket pins | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None. The wave changes no server code. The client still sends `task` and `budget` alone. `tests/unit/test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine` passes, and during the wave it caught one comment in `EngineClient.swift` using the word it bans | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None run. `OwnerSessionDefectTests.swift` was trimmed by a script at a named marker, removing only `BudgetOptionTests`. `black` ran with `--line-ranges` on the new test code only | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | The invariant is REQ-ASK-003: an unmeasured question is never answered as measured. `RoutingOutcome` producers, by grep over `ios/ModelRanking`: `SimilarityRouter` (3, one of them the new decline exit), `ModelOutputBoundary.outcome` (2), and the `TieredRouter.route` manual fallback (1). Each producer is exercised by `RouterBoundaryTests` or `FrontDoorTests`. The first round's gap was the similarity measured-path producer, which had no unmeasured test | ✅ |
| 9b | Scope: planned vs delivered vs deferred | **Planned (plan §2 W3):** focus and send button, remove both strips, echo, move the model filter, fix the manual-tier contradiction, the load race, `unavailableReason` as help, the bottom overlap. **Delivered:** all eight. **Added by review:** the wording tier's decline exit, the routing ticket, the model-tier deadline (REQ-RTR-003 "slow"), the empty-surface-list state, and REQ-BGT-001 retired. **Not verified:** the software keyboard and typing (ledger L2). **Found for W4:** a price below a dollar rendered as `$0`, and the `BUDGET PICK` label | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | **VARIANCE.** Tracked files: 607 insertions and 399 deletions (the two strips and the budget code went out as the front door came in). Product churn is 741 lines, most of it `ContentView.swift`'s top half rewritten, plus `FrontDoor.swift` at 201. Tests: 242, plus `FrontDoorTests.swift` at 408. Records: 23. The second review round added the decline exit, the routing ticket, the deadline and about 170 lines of tests. Not split: the strips' removal and the sheet that replaces them are one change, and a reader sees either all of it or none | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: make check, xcodebuild (iOS Simulator, CODE_SIGNING_ALLOWED=NO), swift test, check_records, conformance-gate, simulator session · gates SKIPPED: none at the leg level; 12 conditional pytest skips · outcome: shipped` | ✅ |

**Ledger rows**

- **L1 — pulled-forward security pass WAIVED.** Client-only wave; no server code changed. Stage 4.0
  covers the milestone surface. *Recorded rather than skipped silently, per V4C-13.*
- **L2 — REQ-ASK-001 is PARTIAL: logic verified; keyboard and submission UNVERIFIED (environment).**
  No sentence may say they were verified.
  - **Setup:** the iPhone 17 Pro simulator (iOS 26.5), booted fresh by `./ios/app.sh up` this
    session, with `ConnectHardwareKeyboard = 0`.
  - **Measured:** a tap on the question field now shows a caret, and a second tap shows the edit
    menu. Before this wave the field gave no visible response. No software keyboard appeared.
  - **Control:** Safari's own address bar, in edit mode on the same simulator, raised no software
    keyboard either. Toggling "Software Keyboard" from the Simulator menu changed nothing, and was
    reverted.
  - **Not exercised:** synthetic keystrokes do not reach the Simulator from this environment, so
    typing, Return and the send button were never exercised.
  - **Owner action:** type a question and press both Return and the arrow, with the hardware
    keyboard off and on (plan §4).
- **L3 — tests deleted with the code they tested:** `BudgetOptionTests` (six tests) and
  `LanguageTests.testTheBudgetCapKeepsItsFigureInBothLanguages`. They went together with
  `BudgetOption`, `BudgetList`, `capLabel`, `UIText.budget` and `EngineClient.budgets()`, none of
  which a security invariant depended on. `/v1/budgets` and its server tests are untouched, and
  REQ-BGT-001 is marked RETIRED with its authority.
- **L4 — an existing assertion was inverted.** `RouterBoundaryTests` asserted that the manual tier is
  NOT unmeasured. The signed plan's REQ-ASK-003 says the opposite in as many words. Both seats
  confirmed the inversion is justified.
- **L5 — the wording tier's decline hints trade one error for another, on purpose, and the trade was
  measured.** The re-review (NEW-1) found three measured tasks now declined: "click through a
  website and upload a photo", "a web app for streaming video" and "solve this geometry problem
  about a picture frame". A 26-question probe scored every question against every surface and every
  hint, on private copies:
  - **The shipped set.** Four false declines (the three above, plus "build a photo gallery
    website") and one miss ("compose a song for my wedding" routes to chat as measured).
  - **Two rewordings, rejected.** Task-phrased or question-phrased hints fired on "fix the slow
    response time of my API", "explain quantum entanglement to a chemist", and even "build me a
    landing page", which broke the M10 calibration.
  - **No threshold separates the groups.** "upload a photo" beats its surface by 0.248, while the
    true decline "which model answers fastest" beats its surface by only 0.041.

  So the error is chosen, not tuned away. A false decline is labelled, and it offers the closest
  surfaces as one-tap alternatives, captioned "Closest we measure:" and not "Or:", since nothing
  matched (re-review-2 R3-1). In all four false declines the right surface comes FIRST
  (`FrontDoorTests.testAMeasuredTaskIsNeverMoreThanOneTapFromItsSurface`). The seat endorsed the
  choice in `docs/reviews/m13-wave-3-rereview-2.md`.

  **What it does not achieve, stated so it is not over-read:**
  - **One error of the forbidden kind remains on the probe.** "compose a song for my wedding" is
    answered from chat as measured. The earlier claim that this error stood at zero was wrong
    (re-review-2 R3-3).
  - **The one-tap guarantee holds for the four tested questions only.** The seat found three more
    — about train speed, a sound wave and REST latency — that decline without their surface among
    the alternatives. All three were misrouted before this wave too (R3-2).
  - **The bias.** The hints and most of the probe were written by the author, which is the bias
    the M10 record names; three probe questions came from the independent seat. M14's router work
    should add questions neither of them wrote.
- **L6 — three formatting-only edits to independent seats' records, words unchanged.** The W2 review
  had two (backticks for `L1`). The W3 review had one: a fenced line beginning "make my…" was read as
  a `make` target by the conformance check, so the question was put in quotes. The gate's own
  exemption list was not used, because changing a gate definition is an escalate-now item.
- **L7 — accepted, not fixed:**
  - **MINOR-4:** one tap only where the wording tier offers alternatives; the prd row states two
    taps otherwise.
  - **MINOR-8(b):** a failed load replaces the card with the failure view. Queued to M14.
  - **OS1:** the `.notEligible` fallback of `TieredRouter.onDeviceState()` cannot run on this host.
  - **DC4:** the audio/video hint changed none of the Tester's twelve questions. It is kept because
    the probe shows it firing on "a web app for streaming video".
  - **NEW-3's remainder:** after a model call hangs, every later question waits the full eight
    seconds. The losing call is now cancelled, but a session circuit breaker needs state that
    `TieredRouter` does not hold. Queued to M14.
  - **REQ-API-010 is defined twice in `docs/prd.md`.** This predates the wave.
  - **The remaining NITs.**

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-15 · Wave commit range:
`10a521c..HEAD`

## Wave footprint — RECORD ONLY

```
Touched:        ios/ModelRanking/ContentView.swift · ios/ModelRanking/Engine/{FrontDoor,Router,
                Language,Models,EngineClient}.swift · ios/EngineTests/{FrontDoorTests,LanguageTests,
                OwnerSessionDefectTests,RouterBoundaryTests}.swift · tests/unit/test_ios_client_contract.py
                docs/prd.md · .language-allow · docs/reviews/m13-wave-3-review.md (L6)
K.8 contracts:  `RoutingOutcome` (+`alternatives`; manual is unmeasured) · `RequestGate.invalidate` ·
                `TieredRouter.modelTimeout` · `CategoryHints.unmeasuredHints` · `ModelRouter.state`
                replaces `unavailableReason` · `BudgetOption` / `EngineClient.budgets()` deleted
```
