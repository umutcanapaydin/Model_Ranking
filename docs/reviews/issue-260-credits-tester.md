---
record_type: review
id: issue-260-credits-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-12
---
# #260 Tester review: the Credits screen (D-193)

**Tester:** independent Tester seat. I wrote none of this change and did neither of its two code reviews. I read policy from `.claude/agents/Tester.md` and `.agents/rules/practices.md`. The range touches neither file.
**Independent:** yes
**Date:** 2026-10-12
**Commit range:** `origin/main..0407ab4` (12 commits)
**Risk tier:** MEDIUM

## Verdict
BLOCKING

## Suite and end-to-end runs (unmodified tree)

- `make test`: 2630 passed, 25 skipped. The module coverage floor passed (47 modules, floor 60%), and the skip budget is 83 of 83.
- `make client-decls`: PASS, 21 client files in 4 configurations.
- `swift test --disable-sandbox --filter 'CreditsTests|StandingsStoreTests|UITextLanguageTests'`: 25 tests, 0 failures. I also ran the full Swift suite once, with fault S3 planted. Only the environmental `OfflineGuardTests.testAChildTheSuiteStartsCannotNameAnOutsidePeer` failed.
- **`/v1/boards` end to end.** I used FastAPI's `TestClient` with `MODEL_RANKING_DB` set to the seat's `advisor.db` and `APP_BUILD=0407ab4`.
  - The route answered 200 with the keys `api_version, attributions, boards, credits, models`.
  - It served 12 credits, in this order: `lmarena, litellm, openrouter, swebench, aider, epoch, arc_prize, epoch_compilation, datacurve, helm, terminal_bench, arena_site`.
  - Each of the 64 boards has its citation in `attributions`, and every credit that citation owes is served. No board went uncredited.
  - Every data link is https. Every licence link is https or `null`, and no id repeats.
  - 235 of the 309 models carry accessibility, so `epoch` is credited for it as well.
  - **Size.** The payload is 560,614 bytes (43,381 gzipped), and the credits add 3,091 bytes of that. It publishes 7,848 positions against the boot bound of 25,000, and `standings_problem` returns `None`.
- **The public derivation, end to end.** I derived a public artifact from `advisor.db` with D-185's seven sources planted in `LEFT_OUT` (in-process; the code was not edited).
  - Its `/v1/boards` credits only `lmarena, litellm, aider, epoch`.
  - OpenRouter, SWE-bench, the compiled boards' publishers and `epoch_compilation` all drop out with their rows.

## Criteria and citing tests

| # | Criterion | Citing test(s) | Held? |
|---|---|---|---|
| 1a | Every board, the price sources (with and without OpenRouter) and `epoch_access` are credited. Each credit has a publisher, what it publishes, an https data link, a licence or terms, and an https licence link or `null` | `tests/unit/test_credits.py:40` `test_every_citation_the_engine_can_owe_has_a_credit` (over the catalogue, `SOURCE_ATTRIBUTION` and `METADATA_ATTRIBUTION`); `:78` `test_prices_credit_openrouter_only_where_its_prices_are_served`; `:101` `test_the_boards_payload_credits_openrouter_when_it_serves_its_prices`; `:109` `test_the_accessibility_epoch_publishes_is_credited_whatever_boards_are_served`; `tests/unit/test_ios_payload_contract.py:266` | yes. P1, P2, P5, P13, P14, P15 and P20 were caught. The gap is M4 |
| 1b | A citation with no credit, or a metadata source with no attribution, is refused at boot | `test_credits.py:51` `test_an_attribution_with_no_credit_is_refused` (at `credits_for` only); `:130` `test_an_accessibility_source_nobody_credits_is_refused_by_its_own_map`; `:123` `test_a_board_is_attributed_from_the_boards_alone`; `tests/unit/test_board_standings.py:353` `test_a_payload_the_route_would_refuse_refuses_the_boot_instead` (any `ValueError` from `board_standings`) | partly. P7 and P8 were caught; P17 survived (M3) |
| 2a | SWE-bench is CC BY-NC 4.0, credited | `test_credits.py:83` `test_the_owners_ruling_is_what_the_screen_says` | yes (P11) |
| 2b | MMLU credits HELM (Apache-2.0, the repository) and the arXiv reports | `test_credits.py:83` | yes (P10) |
| 2c | Epoch's CC BY covers only its own boards and metadata; `epoch_compilation` claims no licence | `test_credits.py:68` `test_epochs_licence_is_claimed_for_its_own_boards_only` | partly. P3 was caught; P3b survived (M1) |
| 2d | Each compiled board credits its publisher first | `test_credits.py:61` `test_a_board_epoch_compiles_credits_its_publisher_and_epochs_compilation`; `:56` | yes (P4) |
| 2e | No licence is claimed that the record does not support, for the other credits | none pins Terminal-Bench, Datacurve, ARC Prize, the Arena site, OpenRouter, Aider, LiteLLM, LMArena or Epoch | **no**. P18 and P19 survived the full unit suite (M1) |
| 3a | `/v1/boards` carries `credits`, derived from `attributions`, in a stable order | `test_credits.py:93` `test_the_boards_payload_carries_the_credits_its_attributions_owe`; `:56`; `test_board_standings.py:141` `test_the_key_sets_are_frozen`; `:219` `test_the_route_publishes_the_standings` | yes (P6, P9, P9b) |
| 3b | An app that predates `credits` still decodes the payload | `test_board_standings.py:141` and `:219` freeze the envelope, so build 4's four keys are still served. `test_ios_payload_contract.py:266` keeps them non-null. That Swift's synthesized `Decodable` ignores the extra key is language behaviour, and no test names it | held indirectly |
| 3c | An app that has `credits` decodes an engine without them (`nil`) | `ios/EngineTests/CreditsTests.swift:40` `testAnEngineThatSendsNoCreditsStillGivesTheBoards` | yes |
| 4a | The phone keeps the credits in the standings it stores | `CreditsTests.swift:22` `testTheCreditsSurviveTheStandingsKeptOnThePhone`; `ios/EngineTests/StandingsStoreTests.swift:69` (asserts `load()?.standings.credits == []`); `test_ios_payload_contract.py:266` | yes (S1) |
| 4b | A copy kept without credits is fetched again once in a launch, and not again within that launch | `StandingsStoreTests.swift:69` `testACopyKeptWithoutCreditsIsFetchedAgainBeforeItsDay`; `:86` `testAnEngineThatSendsNoCreditsIsAskedOncePerLaunch` | partly. S2 and S4 were caught; S3 survived the gate's serial run (M2) |
| 4c | The sheet shows each credit with its links as selectable text, with no `Link`, `openURL` or `URL(string:)` | The negative half is held by `make client-decls` (S6 caught). Nothing tests the positive half: that each credit, its links and `.textSelection` are shown | **no**. S9 and S10 survived (B1) |
| 4d | "not loaded" only with no boards; "the server sends no credits yet" with boards that carry none | none. `UITextLanguageTests.swift:36-37` checks only that the two strings exist in both languages | **no**. S5 survived (B1) |
| 4e | The CC BY notices (the change made; no warranty) in English and Turkish | `CreditsTests.swift:47` `testTheCreditsScreenSpeaksBothLanguages` | the strings, yes (S7, S8). That the sheet shows them is B1 |
| 5 | `LEFT_OUT` stays empty; the public derivation credits only what it serves | `tests/unit/test_public_artifact.py:35` `test_the_hosted_engine_leaves_out_no_source_on_testflight`; `:40`; `:125` `test_a_public_answer_credits_only_the_prices_it_serves` (on `attributions`), with `test_credits.py:93` tying `credits` to them | yes (P12, P9) |

## Fault injection

Each fault was one exact-string replacement by `scratchpad/seatfi/harness.py`. The harness took the file's sha256 before the plant and wrote the original bytes back in a `finally` block. After each restore it compared the sha256 again; every pair matched. At the end, `git hash-object` of all nine touched files equalled their blobs at `0407ab4`, and `git status` was clean.

"5 files" means `test_credits.py`, `test_board_standings.py`, `test_attribution_terms.py`, `test_public_artifact.py` and `test_ios_payload_contract.py` (106 tests). "Full unit" means `pytest tests/unit -n 8` (2619 tests). "View files" means `test_ios_client_contract.py`, `test_ios_visual_contract.py`, `test_attribution_terms.py`, `test_router_hints.py`, `test_client_decl_gate.py` and `test_ios_payload_contract.py` (240 tests).

| Fault | File | Tests run | Result |
|---|---|---|---|
| P1 Aider's licence link set to `http://` | `src/app/workflows/board_tables.py:98` | 5 files | caught: `test_every_citation_the_engine_can_owe_has_a_credit[Aider]` |
| P2 Datacurve's data link set to `http://` | `board_tables.py:105` | 5 files | caught: the same test, `[DeepSWE]` |
| P3 `epoch_compilation` claims `"CC BY 4.0"`, `_CC_BY_URL` | `board_tables.py:92-94` | 5 files | caught: `test_epochs_licence_is_claimed_for_its_own_boards_only` |
| P3b `epoch_compilation` claims `"Creative Commons Attribution 4.0 International"`, link `None` | `board_tables.py:94` | 5 files; full unit | **survived** (M1) |
| P4 a compiled board credits `epoch_compilation` before its publisher | `src/app/workflows/rank.py:127` | 5 files | caught: 3 tests |
| P5 the access sources dropped from `board_standings` (`metadata_sources=()`) | `src/app/workflows/standings.py:144` | 5 files | caught: `test_the_accessibility_epoch_publishes_...`, `test_an_accessibility_source_nobody_credits_...` |
| P6 `credits_for` returns its credits reversed | `rank.py:142` | 5 files | caught: 5 tests |
| P7 `credits_for` skips a citation with no credit | `rank.py:139-140` | 5 files | caught: `test_an_attribution_with_no_credit_is_refused` |
| P8 `attributions_for` skips an unknown metadata source | `rank.py:204-205` | 5 files | caught: `test_an_accessibility_source_nobody_credits_is_refused_by_its_own_map` |
| P9 the payload credits the whole catalogue, not its own attributions | `standings.py:149` | 5 files | caught: `test_the_boards_payload_carries_the_credits_its_attributions_owe` |
| P9b the payload's `credits` is `[]` | `standings.py:149` | 5 files | caught: 4 tests, the iOS contract among them |
| P10 HELM's licence set to `"CC BY 4.0"` | `board_tables.py:111` | 5 files | caught: `test_the_owners_ruling_is_what_the_screen_says` |
| P11 SWE-bench's licence set to CC BY 4.0 | `board_tables.py:95-96` | 5 files | caught: the same test |
| P12 `LEFT_OUT` given `openrouter` | `src/app/workflows/public.py:31` | 5 files | caught: `test_the_hosted_engine_leaves_out_no_source_on_testflight`, `:40` |
| P13 Aider's publisher set to `""` | `board_tables.py:97` | 5 files | caught: the parametrized credit test |
| P14 `epoch_access` credited to LMArena's citation | `rank.py:111` | 5 files | caught: `test_the_accessibility_epoch_publishes_...` |
| P15 `access_served.sources` keeps only the models not served | `src/app/workflows/access_served.py:18` | 5 files | caught: 2 tests |
| P16 the `©` notice dropped from LMArena's credit | `board_tables.py:85` | 5 files | caught: `test_lmarenas_credit_keeps_its_copyright_notice` |
| P17 `board_standings` drops any citation with no credit before `credits_for` | `standings.py:149` | 5 files; full unit | **survived** (M3) |
| P18 Terminal-Bench 2.0 claims `"Apache-2.0"` with Apache's link | `board_tables.py:107-108` | 5 files; full unit | **survived** (M1) |
| P19 Datacurve claims `"CC BY 4.0"`, `_CC_BY_URL` | `board_tables.py:105-106` | 5 files; full unit | **survived** (M1) |
| P20 `epoch_access`'s citation moved off the catalogue (`EPOCH_ATTRIBUTION + " "`) | `rank.py:111` | 5 files | caught: 2 tests. The general case is M4 |
| S1 `case credits` removed from `Standings.CodingKeys` | `ios/ModelRanking/Engine/Models.swift:366` | 5 files; `swift test --filter CreditsTests` | caught: `test_the_boards_payload_satisfies_every_struct_the_app_decodes`, and the Swift build fails (`Standings` does not conform to `Decodable`) |
| S2 the launch rule inverted (`fetchedAt < Self.launched`) | `ios/ModelRanking/Engine/StandingsStore.swift:104` | `--filter StandingsStoreTests` | caught |
| S3 `_ = Self.launched` removed from `init` | `StandingsStore.swift:42` | `--filter StandingsStoreTests`; the full Swift suite; that one test alone | **survived** the class run and the full serial run (only `OfflineGuardTests` failed). It is caught only when `testAnEngineThatSendsNoCreditsIsAskedOncePerLaunch` runs alone (M2) |
| S4 the `credits != nil` half of the rule replaced by `true` | `StandingsStore.swift:104` | `--filter StandingsStoreTests` | caught |
| S5 the sheet's `else if standings != nil` branch removed, so boards with no credits read "not loaded" | `ios/ModelRanking/ContentView.swift:764-766` | view files; `--filter 'CreditsTests\|UITextLanguageTests'`; `make client-decls` | **survived** (B1) |
| S6 the licence link shown as `Link(licenceUrl, destination: URL(fileURLWithPath:))` | `ContentView.swift:758` | `make client-decls`; view files | caught: `client-decls FAIL: ... SwiftUI.Link.init(_:destination:` and the URL rule; `test_router_hints.py::test_the_gap_register_code_carries_no_egress_spelling_the_pin_reads` |
| S7 the English "without any warranty" sentence dropped | `ios/ModelRanking/Engine/Language.swift:384` | `--filter CreditsTests` | caught: `CreditsTests.swift:58` |
| S8 the Turkish notice of the change dropped | `Language.swift:383` | `--filter CreditsTests` | caught: `CreditsTests.swift:59-60` |
| S9 the sheet no longer shows a credit's data link | `ContentView.swift:754` | view files; `make client-decls` | **survived** (B1) |
| S10 `.textSelection(.enabled)` removed from the sheet | `ContentView.swift:761` | view files | **survived** (B1) |

### BLOCKING

- **B1** `ios/ModelRanking/ContentView.swift:742-775`. **Criteria 4c and 4d have no citing test, and three faults in the sheet survive every gate.**
  - The sheet's logic lives only in the view, and no package test, source-reading test or UI path reaches it. `ios/UITests` and `ScreenPaths.json` never open the sheet.
  - Faults S5, S9 and S10 pass `pytest` over the view files, `swift test` and `make client-decls`.
  - **Failure scenario.** A later edit merges the two empty branches back into one. Every phone then talks to an engine from before #260, either before the deploy or after a rollback, and says "The credits come with the boards, which have not loaded yet" while the boards are on screen. That is the round-2 review's M1, back with nothing to catch it. Likewise, dropping `Text(credit.url)` or `.textSelection(.enabled)` ships a screen that names a licence with no way to reach or copy the data. That is the whole of criterion 4c's positive half.
  - **Fix.** Move the sheet's decision out of the view and into the Engine target, where `swift test` compiles it. For example, `enum CreditsShown { case credits([Credit]), notSent, notLoaded }` with `init(standings: Standings?)`, plus a function giving the texts each credit shows (publisher, data, data link, licence, licence link). Test the three states, and test that each credit yields its two links. Then add the sheet to `ScreenPaths.json`, so `make ui-test` opens it and finds a credit's link text.

### MINOR

- **M1** `src/app/workflows/board_tables.py:92-115`, `tests/unit/test_credits.py:68-90`. **Only 3 of the 12 licences are pinned by a test, and the compilation's licence only by a substring.**
  - P3b, P18 and P19 survive the full unit suite.
  - **Failure scenario.** D-193 itself records that only Terminal-Bench 4.0 is Apache, while the served board is 2.0. A future edit that "fixes" the Terminal-Bench credit to `Apache-2.0` (P18) ships to every phone, and so would `"CC BY 4.0"` on Datacurve (P19). The Credits screen then claims a licence the record does not support, which is exactly what criterion 2 rules out. `epoch_compilation` spelled `"Creative Commons Attribution 4.0 International"` (P3b) passes `"CC BY" not in licence`.
  - **Fix.** Pin the whole table in one test: a literal mapping of id to `(licence, licence_url)` taken from D-193 and `docs/research/data-licences-2026-10-04.md`, compared for equality with `CREDITS`. Any licence change then fails until the record is changed with it.
- **M2** `ios/ModelRanking/Engine/StandingsStore.swift:36-42`, `ios/EngineTests/StandingsStoreTests.swift:86-100`. **The `_ = Self.launched` in `init` is held only when its test runs first in the process.**
  - With S3 planted, the test fails alone but passes in `--filter StandingsStoreTests` and in the full serial run that `make swift-test` makes. An earlier test has already started the `static let` by then.
  - **Failure scenario.** A cleanup deletes the line as dead code (it reads like a no-op). In the app, `currentKept(fetch:)` then stamps the first fetch before `launched` starts. An engine without credits is then asked once more per launch, and no gate notices.
  - **Fix.** Make the launch date injectable, for example `init(url:launched:)` with a default from the process's start. The tests then build a store with a fresh launch date and do not depend on test order. Alternatively, give the test its own process: there is a pattern for this in `OfflineTestCase`'s child runs.
- **M3** `src/app/workflows/standings.py:149`, `tests/unit/test_credits.py:51`. **"A citation with no credit is refused at boot" is tested at `credits_for` only, not through `board_standings`.**
  - P17 drops uncredited citations inside `board_standings` before `credits_for` sees them, and it survives the full unit suite.
  - **Failure scenario.** A refactor that "guards" `credits_for` at the call site serves an uncredited citation silently. `test_a_payload_the_route_would_refuse_refuses_the_boot_instead` would never see the `ValueError`.
  - **Fix.** Add a `board_standings` (or `validate_startup_config`) test that monkeypatches `CREDITS_BY_ATTRIBUTION` to drop one served citation, for example `EPOCH_ATTRIBUTION` on the `_chess` fixture. It should expect `ValueError`, or `ConfigError` at boot, with "no credit".
- **M4** `src/app/workflows/rank.py:207-208` (with `METADATA_ATTRIBUTION` at `:109-112`). **A source whose citation is credited but not in `ATTRIBUTIONS` is served with no attribution and no credit, and nothing refuses it.**
  - `attributions_for` keeps only the catalogue's citations. `test_every_citation_the_engine_can_owe_has_a_credit` checks that each `METADATA_ATTRIBUTION` value has a credit, but not that it is in the catalogue. `test_attribution_terms.py:51` checks the catalogue for the external boards only.
  - **Failure scenario.** I reproduced this in-process, without editing code. Registering `openrouter_access` in `METADATA_ATTRIBUTION`, with a new citation that is credited in `CREDITS_BY_ATTRIBUTION`, made `attributions_for(..., metadata_sources=['openrouter_access'])` return `()`, and `credits_for` returned `[]`. The next metadata source added this way goes uncredited on the screen while every test passes.
  - **Fix.** Raise in `attributions_for` when a board or metadata citation is not in the catalogue. Or add a test that `set(SOURCE_ATTRIBUTION.values()) | set(METADATA_ATTRIBUTION.values()) <= set(ATTRIBUTIONS)`.

## K.9 candidates spotted outside this wave's scope

None

## Risks queued to next M

None from this seat. The round-2 review's R1 (ARC-AGI, DeepSWE and OpenRouter served before their publishers' permission) stands as that review states it. I did not re-examine it.

## Dispositions, by the author after the seat

| finding | disposition |
|---|---|
| B1 | Fixed in `08b1b08`, red in `5b492b2`. `CreditsScreen` (Engine, `Models.swift`) decides the sheet's state and lines, held by `CreditsTests`; a pin in `test_credits.py` holds that the view draws them, each link in a `Text` of its own, selectable. S5, S9 and S10 replanted: caught. `ScreenPaths.json` holds question readings, not sheets, so no row is added there. |
| M1 | Fixed in `08b1b08`. Every credit's (licence, licence link) is pinned whole. P18, P19 replanted: caught; P3b is covered by the same equality. |
| M2 | Fixed in `08b1b08`. The launch date is gone: a copy without credits is kept an hour, dated by `now` alone, so the rule holds in any order. This replaces round 2's "once a launch" with "at most hourly". |
| M3 | Fixed in `08b1b08`. A `/v1/boards` test refuses a served citation with no credit. P17 replanted: caught. |
| M4 | Fixed in `08b1b08`, red in `5b492b2`. `attributions_for` refuses a citation outside the catalogue; a test holds both maps' citations inside it. |
