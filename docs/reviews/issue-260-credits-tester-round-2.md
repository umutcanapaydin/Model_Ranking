---
record_type: review
id: issue-260-credits-tester-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-12
---
# #260 Tester review, round 2: the Credits screen (D-193)

**Tester:** independent Tester seat, round 2. I wrote none of this change, and I did neither the first Tester round nor either code review. I read policy from `.claude/agents/Tester.md` and `.agents/rules/practices.md`; the range touches neither.
**Independent:** yes
**Date:** 2026-10-12
**Commit range:** `origin/main..91a6e2f` (round 1's fixes: red `5b492b2`, fix `08b1b08`, docs `91a6e2f`)
**Risk tier:** MEDIUM

## Verdict
BLOCKING

## Suite runs (unmodified tree, `91a6e2f`)

- `make test`: 2635 passed, 25 skipped. `coverage-floor PASS: 47 module(s), floor 60%`; the skip budget is 83 of 83.
- `make client-decls`: exit 0, `client-decls PASS: 21 client file(s) in 4 configuration(s)`.
- `swift test --disable-sandbox --filter 'CreditsTests|StandingsStoreTests|UITextLanguageTests'`: 27 tests, 0 failures. The same filter with `--parallel` passed all 27.

## Round 1, finding by finding

| Round 1 | Status | Evidence |
|---|---|---|
| B1 (the sheet had no citing test) | **Partly closed** | `CreditsScreen` and `CreditRow` (`ios/ModelRanking/Engine/Models.swift:394-429`) decide the state and the lines. `CreditsTests.swift:48` and `:57` hold them, and `test_credits.py:161` pins the view to them. The Engine form of S5 (F3), S9, S10, F4a, F4b and F4c are caught. Three view faults still pass every gate: S11 (the CC BY notices dropped), S5v and S10b. Round 1's table had put "that the sheet shows them" (4e) under B1, so B1 below and M1 below remain |
| M1 (only 3 of 12 licences pinned) | Closed | `test_credits.py:176` pins all 12 `(licence, licence_url)` pairs by equality. P3b, P18 and P19 are caught in the 5 files and in the full unit suite |
| M2 (the launch rule depended on test order) | Closed by design change | The launch date is gone, and the rule is dated by `now` alone (`StandingsStore.swift:103-104`). F1, F2 and F9 are caught both serially and with `--parallel`, by the same tests. No static state is left to order |
| M3 (an uncredited citation refused only in `credits_for`) | Closed | `test_credits.py:200` goes through `board_standings`. P17 is caught in the 5 files and in the full unit suite |
| M4 (a citation outside the catalogue dropped silently) | Closed | `rank.py:208-211` raises. `test_credits.py:151` catches F5, and `test_credits.py:209` catches F6b even with the check removed (F7). F6a (round 1's P20) is caught by 4 tests |

## Criteria and citing tests

| # | Criterion | Citing test(s) | Held? |
|---|---|---|---|
| 1a | Every board, the price sources with and without OpenRouter, and `epoch_access` are credited. Each credit has a publisher, what it publishes, an https data link, a licence or terms, and an https licence link or `null` | `tests/unit/test_credits.py:40` `test_every_citation_the_engine_can_owe_has_a_credit`; `:78` `test_prices_credit_openrouter_only_where_its_prices_are_served`; `:101` `test_the_boards_payload_credits_openrouter_when_it_serves_its_prices`; `:109` `test_the_accessibility_epoch_publishes_is_credited_whatever_boards_are_served`; `:209` `test_every_citation_a_source_can_owe_is_in_the_catalogue`; `tests/unit/test_ios_payload_contract.py:266` | yes (F6a, F6b, F7) |
| 1b | An uncredited citation, or an unattributed metadata source, is refused rather than served | `test_credits.py:51` `test_an_attribution_with_no_credit_is_refused`; `:200` `test_the_boards_payload_refuses_a_served_citation_with_no_credit`; `:130` `test_an_accessibility_source_nobody_credits_is_refused_by_its_own_map`; `:151` `test_a_citation_outside_the_catalogue_is_refused_not_dropped`; `:123`; `tests/unit/test_board_standings.py:353` | yes (P17, F5) |
| 2 | No licence beyond D-193 and the licence record: SWE-bench CC BY-NC 4.0; MMLU is HELM (Apache-2.0) plus arXiv; Epoch's CC BY only for its own boards, `epoch_compilation` claiming none | `test_credits.py:176` `test_every_publishers_licence_is_the_one_the_ruling_and_the_record_give` (all 12, by equality); `:83` `test_the_owners_ruling_is_what_the_screen_says` (arXiv in HELM's data); `:68` `test_epochs_licence_is_claimed_for_its_own_boards_only`; `:61` | yes (P3b, P18, P19) |
| 3a | `/v1/boards` carries `credits`, derived from `attributions`, in a stable order | `test_credits.py:93` `test_the_boards_payload_carries_the_credits_its_attributions_owe`; `:56`; `test_board_standings.py:141` `test_the_key_sets_are_frozen`; `:219` `test_the_route_publishes_the_standings` | yes |
| 3b | Older apps decode it | `test_board_standings.py:141` and `:219` freeze the envelope, so the four older keys are still served. Swift's synthesized `Decodable` ignores the extra key | held indirectly, as in round 1 |
| 3c | The app decodes an older engine's payload, with `credits` → `nil` | `ios/EngineTests/CreditsTests.swift:40` `testAnEngineThatSendsNoCreditsStillGivesTheBoards` | yes |
| 4a | The phone keeps the credits it stores | `CreditsTests.swift:22` `testTheCreditsSurviveTheStandingsKeptOnThePhone`; `StandingsStoreTests.swift:69` | yes |
| 4b | A copy without credits is fetched again within the hour and at most hourly (`maxAgeWithoutCredits`), dated by `now` alone | `ios/EngineTests/StandingsStoreTests.swift:69` `testACopyKeptWithoutCreditsIsFetchedAgainBeforeItsDay`; `:85` `testAnEngineThatSendsNoCreditsIsAskedAtMostHourly` | yes (F1, F2, F9; serial and `--parallel` agree) |
| 4c | `CreditsScreen` decides the sheet: no boards → not loaded; boards with no credits → not sent; otherwise each credit's lines, each link on a line of its own | `CreditsTests.swift:48` `testTheSheetSaysNotLoadedWithNoBoardsAndNotSentWithBoardsThatCarryNone`; `:57` `testEachCreditIsListedWithItsLinksOnLinesOfTheirOwn` | yes (F3, F4a, F4b) |
| 4d | The view draws `CreditsScreen` selectably; `make client-decls` holds no `Link` | `test_credits.py:161` `test_the_credits_sheet_shows_what_the_engine_layer_decides`; `make client-decls` | mostly (S9, S10, F4c caught). S5v and S10b survive the substring pin (M1) |
| 4e | The CC BY notices appear in both languages | `CreditsTests.swift:76` `testTheCreditsScreenSpeaksBothLanguages` holds the strings in both languages | **no** for "appear": nothing holds that the sheet draws them. S11 survives (B1) |
| 5 | `LEFT_OUT` stays empty; the public derivation credits only what it serves | `tests/unit/test_public_artifact.py:35` `test_the_hosted_engine_leaves_out_no_source_on_testflight`; `:40`; `:125` `test_a_public_answer_credits_only_the_prices_it_serves`, with `test_credits.py:93` tying `credits` to `attributions` | yes (round 1's P12 and P9; nothing in this range touches it) |

## Fault injection

Each fault was one or more exact-string replacements, made by `scratchpad/seatfi2/harness.py`. The harness checked that each old string occurred exactly once, and took the sha256 of each file before the plant. It wrote the original bytes back in a `finally` block and compared the sha256 again; every pair matched. At the end, `git hash-object` of all six touched files equalled their blobs at `91a6e2f`, and `git status --short` was empty.

These are the test sets:

- **"5 files"** is `test_credits.py`, `test_board_standings.py`, `test_attribution_terms.py`, `test_public_artifact.py` and `test_ios_payload_contract.py` (111 tests).
- **"Full unit"** is `pytest -n 8 tests/unit`.
- **"View files"** is `test_credits.py`, `test_ios_client_contract.py`, `test_ios_visual_contract.py`, `test_attribution_terms.py`, `test_router_hints.py`, `test_client_decl_gate.py` and `test_ios_payload_contract.py` (268 tests).
- **"Swift"** is `swift test --disable-sandbox --filter 'CreditsTests|StandingsStoreTests|UITextLanguageTests'` (27 tests), run serially and again with `--parallel`.

| Fault | File | Tests run | Result |
|---|---|---|---|
| P3b `epoch_compilation` claims `"Creative Commons Attribution 4.0 International"`, link `None` | `src/app/workflows/board_tables.py:94` | 5 files; full unit | caught: `test_every_publishers_licence_is_the_one_the_ruling_and_the_record_give` |
| P17 `board_standings` drops any citation with no credit before `credits_for` | `src/app/workflows/standings.py:149` | 5 files; full unit | caught: `test_the_boards_payload_refuses_a_served_citation_with_no_credit` |
| P18 Terminal-Bench 2.0 claims `"Apache-2.0"` with Apache's link | `board_tables.py:107-108` | 5 files; full unit | caught: the licence pin |
| P19 Datacurve claims `"CC BY 4.0"`, `_CC_BY_URL` | `board_tables.py:105-106` | 5 files; full unit | caught: the licence pin |
| S5 (Engine form) / F3 `CreditsScreen.state` returns `.notLoaded` for boards with no credits | `ios/ModelRanking/Engine/Models.swift:403-405` | Swift, serial and `--parallel` | caught: `testTheSheetSaysNotLoadedWithNoBoardsAndNotSentWithBoardsThatCarryNone` |
| S5v (view form) both empty cases drawn as `Text(UIText.creditsUnavailable(language))`, ignoring the text `CreditsScreen` decided | `ios/ModelRanking/ContentView.swift:763-764` | view files; `make client-decls` | **survived** (M1) |
| S9 the sheet no longer draws `row.dataLink` | `ContentView.swift:754` | view files; `make client-decls` | caught: `test_the_credits_sheet_shows_what_the_engine_layer_decides` |
| S10 `.textSelection(.enabled)` removed from the credit rows | `ContentView.swift:760` | view files; `make client-decls` | caught: the same pin |
| S10b `.textSelection(.enabled)` moved from the credit rows to the purpose line | `ContentView.swift:745`, `:760` | view files; `make client-decls` | **survived** (M1) |
| S11 the purpose line, which carries the CC BY notices, dropped from the sheet | `ContentView.swift:745` | view files; `make client-decls` | **survived** (B1) |
| S12 `.sheet(isPresented: $showingCredits) { creditsSheet }` removed, so the Credits button opens nothing | `ContentView.swift:151` | view files; `make client-decls` | **survived** (M2) |
| F1 `maxAgeWithoutCredits` set to the day (`86_400`) | `ios/ModelRanking/Engine/StandingsStore.swift:34` | Swift, serial and `--parallel` | caught: `testACopyKeptWithoutCreditsIsFetchedAgainBeforeItsDay`, `testAnEngineThatSendsNoCreditsIsAskedAtMostHourly` |
| F2 the credits condition inverted (`credits != nil ?`) | `StandingsStore.swift:103` | Swift, serial and `--parallel` | caught: 5 `StandingsStoreTests` |
| F9 the age read from `Date()` rather than `now` | `StandingsStore.swift:104` | Swift, serial and `--parallel` | caught: 4 `StandingsStoreTests` |
| F4a `CreditRow.dataLink` is the data label and the link joined into one string | `Models.swift:425` | Swift, serial and `--parallel` | caught: `testEachCreditIsListedWithItsLinksOnLinesOfTheirOwn` |
| F4b `CreditRow.dataLabel` is the data label and the link joined into one string | `Models.swift:424` | Swift, serial and `--parallel` | caught: the same test |
| F4c the view joins `row.dataLabel` and `row.dataLink` in one `Text` | `ContentView.swift:753-754` | view files; `make client-decls` | caught: `test_the_credits_sheet_shows_what_the_engine_layer_decides` |
| F5 the catalogue check in `attributions_for` removed | `src/app/workflows/rank.py:208-211` | 5 files; full unit | caught: `test_a_citation_outside_the_catalogue_is_refused_not_dropped` |
| F6a `epoch_access`'s citation moved off the catalogue (`EPOCH_ATTRIBUTION + " "`; round 1's P20) | `rank.py:111` | 5 files | caught: 4 tests, `test_every_citation_a_source_can_owe_is_in_the_catalogue` among them |
| F6b a `METADATA_ATTRIBUTION` entry (`openrouter_access`) with a credited citation outside the catalogue | `rank.py:111`, `:124` | 5 files; full unit | caught: `test_every_citation_a_source_can_owe_is_in_the_catalogue` |
| F7 F5 and F6b together | `rank.py` | 5 files; full unit | caught: both M4 tests |
| F8 `!credits.isEmpty` dropped, so `credits: []` lists nothing instead of saying "not sent" | `Models.swift:403` | Swift, serial and `--parallel` | survived. **Not a finding:** `board_standings` always owes a price citation (`priced=True`), so this engine never sends an empty `credits` |

Serial and `--parallel` Swift runs gave the same result for every Swift fault. No result depends on test order.

### BLOCKING

- **B1** `ios/ModelRanking/ContentView.swift:745`, `tests/unit/test_credits.py:161-173`. **Criterion 4e has no citing test for the CC BY notices appearing on the sheet, and dropping them passes every gate (S11).**
  - `CreditsTests.swift:76` proves that the notice of modification and the warranty disclaimer exist in both languages. The sheet draws them only through `Text(UIText.creditsPurpose(language))`, which sits outside `CreditsScreen`. The view pin checks the state call, the row `Text`s and `.textSelection` only.
  - Round 1 classed this as part of B1 ("That the sheet shows them is B1"). The disposition marks B1 fixed, but S11 survives the view files, `make client-decls` and `swift test`.
  - **Failure scenario.** A later edit reworks the sheet's header, for example to put the purpose in a section footer or behind a disclosure, and loses the line. The app then shows LMArena's and Epoch's CC BY 4.0 data on a Credits screen that omits the notice of modification and the disclaimer that section 3(a)(1) asks for. That is the obligation the screen exists to meet, and no gate notices.
  - **Fix.** Let `CreditsScreen` own the notice, for example a `static func notice(_ language: Language) -> String` or a `notice` carried with the state. Assert in `CreditsTests` that it is the CC BY text in both languages. Then extend `test_credits.py:161` to require that the sheet draws it, for example `Text(CreditsScreen.notice(language))` or `Text(UIText.creditsPurpose(language))` inside `creditsSheet`, ahead of the `switch`.

### MINOR

- **M1** `tests/unit/test_credits.py:170-173`, `ios/ModelRanking/ContentView.swift:760` and `:763-764`. **The view pin is a substring check, so two forms of round 1's survivors still pass.**
  - **S5v.** The view draws `UIText.creditsUnavailable(language)` for both empty cases and ignores the text that `CreditsScreen` decided. The view files and `make client-decls` pass.
  - **S10b.** `.textSelection(.enabled)` moves off the credit rows onto the purpose line. The pin finds the substring anywhere in the sheet, so it passes.
  - **Failure scenario.** A tidy-up that writes `case .notSent, .notLoaded: Text(UIText.creditsUnavailable(language))` brings back the round-2 review's M1 at the view layer. Every phone on an engine from before #260 says the boards have not loaded while they are on screen. Likewise, a modifier moved during a layout change leaves the links unselectable, and so uncopyable, which is criterion 4d's whole point now that `Link` is refused.
  - **Fix.** In `test_credits.py:161`:
    - Assert that the sheet names neither `UIText.creditsUnavailable` nor `UIText.creditsNotSent`, and that the empty case draws its bound value. A regex such as `case let \.notSent\((\w+)\), let \.notLoaded\(\1\):\s*Text\(\1\)` does both.
    - Assert `.textSelection(.enabled)` within the slice from `ForEach(rows)` to `case let .notSent`, not anywhere in the sheet.
- **M2** `ios/ModelRanking/ContentView.swift:151` and `:340`. **Nothing holds that the Credits button opens the sheet (S12).**
  - Removing `.sheet(isPresented: $showingCredits) { creditsSheet }` passes the view files and `make client-decls`. The unused `private var` compiles without error.
  - The disposition of round 1's B1 declined a `ScreenPaths.json` row, so no UI path reaches the sheet either.
  - **Failure scenario.** A refactor of `body`'s modifier chain drops the `.sheet` line. The Credits button then does nothing, every publisher goes uncredited on the phone, and all gates stay green. The owner would see this only on a phone test.
  - **Fix.** Add two source pins to `test_credits.py`: one for `.sheet(isPresented: $showingCredits) { creditsSheet }`, and one for a `Button { showingCredits = true }` carrying `.accessibilityIdentifier("credits")`. Or, if the owner allows it, add a UI path that taps `credits` and finds a credit's link text.

## K.9 candidates spotted outside this wave's scope

None

## Risks queued to next M

None from this seat. The round-2 review's R1 (ARC-AGI, DeepSWE and OpenRouter served before their publishers' permission) stands as that review states it; I did not re-examine it.

## Dispositions, by the author after the seat

| finding | disposition |
|---|---|
| B1 | Fixed in `3582409`, red in `182b976`. The CC BY notice is `CreditsScreen.notice`, held in both languages by `CreditsTests`; the sheet draws it (pinned in `test_credits.py`). S11 replanted: caught. |
| M1 | Fixed in `182b976`. The selection is looked for inside `ForEach(rows)`, the sheet may not name the empty texts, and its empty case draws the text `CreditsScreen` chose. S5v and S10b replanted: caught. |
| M2 | Fixed in `182b976`. The `.sheet` on `showingCredits` and the button that sets it are pinned. S12 replanted: caught. |
| F8 | Held in `3582409`: an empty credits list is "not sent", tested. |
