---
record_type: review
id: issue-260-credits-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-12
---
# #260 review: the Credits screen, and D-193

**Reviewer:** independent Code-Reviewer seat. Policy was read from `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md`; the range touches neither.
**Independent:** yes
**Date:** 2026-10-12
**Commit range:** `origin/main..ceb7a69` (f7c110c red tests, 393eca0 D-193 and the Terminal-Bench record, a932d66 the feature, ceb7a69 docs)
**Risk tier:** MEDIUM

## Verdict
BLOCKING

## Findings

The derivation is sound. Credits come from the attributions a payload already owes. A citation with no credit raises, and at boot that raise becomes a `standings_problem`, so the engine refuses to serve. The order is stable: it follows the catalogue. The public-artifact path credits correctly when a source is left out, because a source that is left out has no board and so no attribution. On the real `advisor.db`, all 11 credits are served (2,781 bytes of a 612 KB payload). An older app ignores the new key. `make client-decls` passes. The Swift suite has 611 tests, and only `OfflineGuardTests` fails. That test is environmental: it asks for the `offline.sb` sandbox, and it fails on the unmodified tree too.

One credit states a licence that the record contradicts, which blocks. The other findings are smaller: what the derivation does not see, a gap in the phone's kept copy, the notice wording, the toolbar, and the tests.

### BLOCKING

- **B1** `src/app/workflows/board_tables.py:88-89`, `src/app/workflows/rank.py:118-122`. **The Epoch credit claims CC BY 4.0 for Epoch's compilations of other publishers' boards.**
  - The credit reads "Capabilities & benchmarking: its own boards, and its compilations of the boards credited to their publishers here", with licence "CC BY 4.0". `CREDITS_BY_ATTRIBUTION` attaches this credit to every external board, as `(publisher, "epoch")`.
  - Epoch says its external data "retains its original licensing" (`board_tables.py:39-44`, which quotes epoch.ai/benchmarks/use-this-data). The project's own `EPOCH_EXTERNAL_ATTRIBUTION` says: "None claims a licence: Epoch's grant does not reach them."
  - The licence review records the following for those boards:
    - ARC-AGI: ARC Prize Terms, no compilation without permission (row 3, note 3).
    - DeepSWE: no licence found (row 4).
    - Terminal-Bench: none stated (row 5).
    - WebDev: Arena's Terms of Use (row 6).
  - **Failure scenario:** a reader, an external tester or App Review opens the Credits screen. It says the ARC-AGI and DeepSWE scores, which Epoch compiled, are available under CC BY 4.0, a grant that nobody made. If an artifact carries only external Epoch boards, Epoch's only row on the screen is that CC BY claim. The project has treated a false provenance claim as BLOCKING before (W4 BLOCKING-2). This one is a false licence claim, on the one screen built to state licences correctly.
  - **Fix:** split the credit in two.
    - `epoch`: "its own boards", CC BY 4.0.
    - `epoch_compilation`: "its compilation of the boards credited above", licence "each board under its publisher's terms", `licence_url=None`.
  - Map `EPOCH_ATTRIBUTION` to `epoch`, and each external citation to `(publisher, "epoch_compilation")`.
  - Add a test: no credit that an `EPOCH_EXTERNAL_ATTRIBUTION` citation owes may carry a CC licence unless its publisher's own entry does.
  - The same class of claim with a lower stake: `helm`'s "Apache-2.0 (HELM)" is the licence of HELM's code (record note 6: no data licence found). The owner's ruling ("HELM Apache") covers it, but naming the link "HELM's code licence" would keep the screen within the record.

### MINOR

- **M1** `src/app/workflows/standings.py:129-146`, `src/app/workflows/rank.py:64-106`. **Epoch's accessibility data is served without a credit.**
  - `/v1/boards` serves `models[].accessibility`, which is Epoch's `model_metadata.csv` (`epoch_access`, licence review row 2). The phone filters on it (`AnswerPlan.swift:380-388`).
  - The attributions, and so the credits, are derived from board ids alone, and `epoch_access` is not in `SOURCE_ATTRIBUTION`.
  - **Failure scenario (reproduced):** an artifact with an `arena` board and one `access` row. It serves `accessibility: "Open weights (unrestricted)"`, and its credits are `['lmarena', 'litellm']`, with no Epoch. Today the real artifact always carries Epoch boards, so Epoch's credit is present by coincidence. If Epoch's score sources are ever left out (`LEFT_OUT`) while the access rows stay, D-193's claim that "a source cannot be served and left off the screen" fails silently.
  - **Fix:**
    - Add `"epoch_access": EPOCH_ATTRIBUTION` to `SOURCE_ATTRIBUTION`.
    - Have `board_standings` add `epoch_access` to the sources it attributes whenever any model carries an accessibility value.
    - Name "model metadata (accessibility)" in Epoch's `data` text.
    - Add the test above.

- **M2** `ios/ModelRanking/Engine/StandingsStore.swift:94-96`, `ios/ModelRanking/Engine/Models.swift:452-455`, `ios/ModelRanking/ContentView.swift:751`, `ios/ModelRanking/Engine/Language.swift:400-404`. **The Credits screen is empty while the phone is online, for up to a day.**
  - `FetchedStandings` stores what the app decoded, re-encoded. Build 4's `Standings` has no `credits`, so the kept copy that build 4 wrote never has them. The same holds for any copy fetched before the engine with #260 was deployed.
  - After the update, `currentKept` serves that copy without fetching while it is younger than 86,400 s.
  - **Failure scenario:** a tester updates to build 5, an hour after build 4 fetched the boards. The Credits sheet says "The credits come with the boards. Open the app once while it is online", while the app is online and showing answers. The same happens whenever `/v1/boards` fails and `/v1/recommendations` succeeds, because the home screen ranks on publishers' data and the screen credits none of them.
  - **Fix:**
    - Have `currentKept` treat a kept copy whose `credits == nil` as due, for one fetch per launch; a failed fetch keeps the copy.
    - Reword the empty state so it does not tell an online reader to go online.
    - Add the case to the runbook's v2 step 9 note.

- **M3** `ios/ModelRanking/Engine/Language.swift:385-390`. **The CC BY notices misstate what the app does.**
  - "The data is shown as each publisher published it, without any warranty" is not true of what the app shows. Every board is re-ranked into positions over this app's own population: reconciled and priced models, at the effort policy (`standings.py:86-113`). That is a modification.
  - §3(a)(1)(B) asks the app to indicate the modification. Only the combined lists are said to be the app's own.
  - §3(a)(1)(A)(ii) asks for the copyright notice where one is supplied. The LMArena attribution carries "© LMArena", but the credit drops it. Datacurve's credit keeps its ©.
  - **Failure scenario:** the one notice meant to discharge §3(a) makes a claim of fidelity that the code contradicts.
  - **Fix:**
    - English: "Each board is re-ranked here over the models this app can price, and the lists combine those boards. The publishers provide their data without any warranty."
    - Turkish to match.
    - Carry "© LMArena" in the `lmarena` credit's licence or publisher text.
    - Extend `testTheCreditsScreenSpeaksBothLanguages` to cover the modification sentence.

- **M4** `ios/ModelRanking/ContentView.swift:139`. **The toolbar button's accessibility label does not contain its visible text.**
  - The button shows "Credits", but its label is "Sources and licences".
  - **Failure scenario:** a Voice Control user says "Tap Credits" and nothing happens (WCAG 2.5.3, Label in Name). The neighbouring gaps button passes this rule: its visible "Not measured" is inside its label, "Asked, but not measured". The Turkish credits label passes too.
  - **Fix:** make the English title contain the button's word, for example "Credits: sources and licences". Alternatively, add `.accessibilityInputLabels([UIText.creditsButton(language), UIText.creditsTitle(language)])`.

- **M5** `ios/ModelRanking/ContentView.swift:113-151`, `ios/UITests/ScreenAuditTests.swift:99-104`. **Nothing checks the toolbar's fit or the new sheet.**
  - The leading side now holds two labelled buttons, and the trailing side a 96 pt segmented picker.
  - In Turkish the two buttons are `Ölçülmeyenler` and `Kaynaklar`, each with an icon, at `.footnote`. On a 375 pt phone (iPhone SE, 13 mini) that is about 300 pt of items before margins, and Dynamic Type grows the text.
  - The screen audit captures the gaps sheet (`test05Gaps`) but not the Credits sheet or the three-item bar.
  - **Failure scenario:** at a large text size the bar truncates or drops a button, and no gate or screenshot shows it.
  - **Fix:**
    - Add a `test05bCredits` capture, in Turkish and at a large content size, beside `test05Gaps`.
    - If the bar overflows, show the icon alone, with the label kept for VoiceOver.

- **M6** `tests/unit/test_ios_payload_contract.py:100-104` and `:264-286`, `tests/unit/test_credits.py:30-31`. **The cross-language contract does not hold the credits.**
  - `_declared_properties` reads only `let`, so `var credits` is exempt from the check that the parser read everything.
  - Swift allows a property with a default value to be left out of an explicit `CodingKeys`, so dropping `case credits` compiles.
  - The `Credit` struct is never checked against the served credits.
  - **Planted, restored by sha256:**
    - Removing `case credits` from `Standings.CodingKeys` passes all 117 Python iOS-contract tests. Only `CreditsTests.testTheCreditsSurviveTheStandingsKeptOnThePhone` and `testACreditDecodesWithItsLinksAndAPublisherWithNoLicenceHasNoLicenceLink` catch it.
    - Renaming `licence_url` to `licence_link` in Swift also passes the Python tests. The same two Swift tests catch it.
  - Both Swift tests decode a hand-written fixture, so the engine and the app agree only through two fixtures that were typed separately.
  - **Fix:**
    - Match `(?:let|var)` in `_declared_properties`.
    - Assert `_assert_struct_is_satisfied("Credit", credit, ...)` for each served credit.
    - While there: `test_credits.py:30-31` wraps `rank.credits_for` behind `# type: ignore[no-any-return]`, an ignore that mypy reports as unused (seed C.8). Call `rank.credits_for` directly.

- **M7** `docs/research/terminalbench-4-feasibility-2026-10-12.md:10`, `:27`, `:43`. **The feasibility record leaves out the licensed 2.0 option, and blurs two dates.**
  - The table gives TB 2.0's licence as "none stated". The licence review's note 5 and option B4 record a first-hand Terminal-Bench 2.0 submissions dataset, `harborframework/terminal-bench-2-leaderboard`, tagged Apache-2.0. Its cost is effort L, because the scores are computed from the per-trial results.
  - The owner's premise that "only 4.0 is Apache" goes unanswered. So the owner chooses between 17 licensed models and 42 unlicensed ones, without a third option: 42 licensed models on a frozen board.
  - Spot-checked with read-only `gh api`. The repository is Apache-2.0 and was pushed 2026-10-09, `leaderboard.yaml` defines `4-0-0`, and there are 21 submissions with `metrics.accuracy` over 330 trials, Opus 5.5 at 64.85. All of that matches the record.
  - The record's "dated 2026-08-26 to 2026-10-06" are the file names. The run date is `metadata.date`, which differs: the 2026-09-30 Opus 5.5 file has `date: 2026-09-22`. The board's `evidence_date` should be named as one of the two.
  - **Fix:**
    - Add option (c), TB 2.0 from its Apache-2.0 dataset, with its cost.
    - Say which date is the run date.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/board_tables.py:92-95`. **The licence notices that Apache-2.0 and MIT ask for are not on the screen.**
  - Aider, and HELM by the owner's ruling, are Apache-2.0. Apache-2.0 §4(a) asks for a copy of the licence.
  - LiteLLM is MIT, and MIT asks for its copyright and permission notice.
  - The screen gives only the licence's name and link. The licence review already marks both rows "Partly" (rows 9-10), and D-193 does not rule on it.
  - This is an enhancement: file it as an issue, so the owner rules whether a link is enough for medians derived from those files.

## Risks queued to next M

- **R1** D-193, the cost paragraph. **The hosted engine serves ARC-AGI, DeepSWE and OpenRouter data before their publishers have given permission.**
  - The Credits screen names their terms, which shows the gap rather than closing it.
  - **What would show the risk is real:** an App Review question under guideline 5.2.2 when the app goes to external testers, or a publisher's objection.
  - **The trigger to act:** the first external-tester submission, before which the permissions are to be in hand (runbook v2 step 9).

## Evidence

**Tests run (unmodified tree):**
- `pytest tests/unit/test_credits.py tests/unit/test_board_standings.py`: 62 passed.
- The iOS text and contract suites, with `test_public_artifact` and `test_api_v1`: 183 passed.
- `make client-decls`: PASS, 21 files in 4 configurations.
- `swift test --disable-sandbox`: 611 tests, and only `OfflineGuardTests.testAChildTheSuiteStartsCannotNameAnOutsidePeer` fails, because it asks for the `offline.sb` sandbox. The unmodified tree fails it too.
- `mypy src`: clean.

**Planted faults.** Each file was restored byte for byte, and its sha256 checked: `rank.py` 50422be01d0e, `standings.py` f9ae4cf9ffc2, `Models.swift` 6497b017b371.

| fault | caught by |
|---|---|
| drop `AIDER_ATTRIBUTION` from `CREDITS_BY_ATTRIBUTION` | `test_every_citation_the_engine_can_owe_has_a_credit[Aider…]` |
| credits sorted by id (reordered) | `test_a_board_epoch_compiles_credits_its_publisher_and_epoch`, `test_the_boards_payload_carries_the_credits_its_attributions_owe`, `test_the_owners_ruling_is_what_the_screen_says` |
| Epoch before its publisher | `test_a_board_epoch_compiles…`, `test_each_publisher_is_credited_once_in_the_order_the_attributions_come`, `test_the_owners_ruling…` |
| Epoch dropped from external boards | `test_a_board_epoch_compiles…` |
| pricing credits LiteLLM only | `test_each_publisher_is_credited_once…`, `test_prices_credit_openrouter_only…`, `test_the_boards_payload_credits_openrouter…` |
| whole catalogue credited on `/v1/boards` | `test_the_boards_payload_carries_the_credits_its_attributions_owe` |
| drop `credits` from the payload | `test_the_key_sets_are_frozen`, `test_the_route_publishes_the_standings`, both payload tests in `test_credits.py`, `test_the_boards_payload_satisfies_every_struct_the_app_decodes` |
| drop `case credits` from `Standings.CodingKeys` | Swift `CreditsTests` (2 tests) only; no Python test (M6) |
| rename Swift `licence_url` key | Swift `CreditsTests` (2 tests) only; no Python test (M6) |

**Records:**
- D-193's Amends pointers sit under D-185 (after D-190's) and under D-186, and both say what changed.
- D-193 is the next free number after D-192.
- The architecture, README and runbook text matches the code.
- The credit links were checked with `gh api`:
  - Aider's `LICENSE.txt`, LiteLLM's `LICENSE` and HELM's `LICENSE` exist.
  - HELM's repository is Apache-2.0.
  - LiteLLM's repository reads `NOASSERTION` because of its `enterprise/` directory. The record covers that.

## Dispositions, by the author after the review

| finding | disposition |
|---|---|
| B1 | Fixed in `78f1bca`, red in `81a877b`. Epoch's CC BY credit names the boards it runs and its model metadata; its compilation is a credit of its own, `epoch_compilation`, which claims no licence. HELM's licence says it is the repository's (D-193). |
| M1 | Fixed in `78f1bca`, red in `81a877b`. `/v1/boards` credits the accessibility's source through `rank.METADATA_ATTRIBUTION`; `SOURCE_ATTRIBUTION` stays the boards (`test_families`). |
| M2 | Fixed in `78f1bca`, red in `81a877b`. A kept copy without credits is fetched again at once. `Standings.credits` is a `let`: `client-decls` refused the privacy sink reading a `var` (INV-66). The text for no credits no longer tells an online reader to go online. |
| M3 | Fixed in `78f1bca`. The screen states the change (each board ranked again among the priced models, boards combined) and the absence of warranty; LMArena's credit keeps its notice. |
| M4 | Fixed in `78f1bca`. The entry's accessibility name is its visible text. |
| M5 | Fixed in `78f1bca`. The entry is a button at the end of the answers, not a third item in the bar. No screenshot test covers the sheet; `make ui-test` is not in the gate, and the owner sees the screen on the next build. |
| M6 | Fixed in `78f1bca`. The contract test reads stored `var`s and holds each credit against `Credit`; renaming `licence_url` or dropping `case credits` now fails it (measured, restored by sha256). The unused `type: ignore` is gone. |
| M7 | Fixed in this commit. The record adds TB 2.0's Apache-2.0 submissions as a third way, and separates the files' added dates from the runs' dates. |
| K1 | Filed as #261. |
| R1 | Stated in D-193's cost, and in the runbook's v2 step 9: the permissions before external testers. |
