---
record_type: review
id: issue-260-credits-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-12
---
# #260 review, round 2: the Credits screen, after round 1's fixes

**Reviewer:** independent Code-Reviewer seat, round 2. I wrote none of the change and did not do round 1. Author and reviewer family: Claude / Claude (fallback: no second family in this lane). Policy was read from `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md`, and the range touches neither. I read round 1 and its Dispositions table, then the whole range's diff, then each fix against the code it touches.
**Independent:** yes
**Date:** 2026-10-12
**Commit range:** `origin/main..11e1cc8` (9 commits). Round 1's fixes are `81a877b` (red), `78f1bca` (fix) and `11e1cc8` (docs).
**Risk tier:** MEDIUM

## Verdict
MINOR

## Round 1, finding by finding

- **B1: fixed.** Epoch's own boards are credited as `epoch` (CC BY 4.0). Its compilation is now a separate credit, `epoch_compilation`, which claims no licence and has `licence_url=None` (`src/app/workflows/board_tables.py:88-95`). The five external boards map to `(publisher, "epoch_compilation")` (`src/app/workflows/rank.py:127-129`).
  - Plant: mapping them back to `epoch` is caught by `test_a_board_epoch_compiles_credits_its_publisher_and_epochs_compilation` and `test_each_publisher_is_credited_once_in_the_order_the_attributions_come`.
  - The real `advisor.db` credits 12 publishers: `lmarena, litellm, openrouter, swebench, aider, epoch, arc_prize, epoch_compilation, datacurve, helm, terminal_bench, arena_site`.
- **M1: fixed.** The fix adds `rank.METADATA_ATTRIBUTION` (`rank.py:109-112`) and `access_served.sources` (`src/app/workflows/access_served.py:13-18`). `board_standings` credits these sources (`src/app/workflows/standings.py:141-143`).
  - Plant: dropping `epoch_access` from the map is caught by 3 tests, because `board_standings` then raises.
  - Plant: dropping the access sources from `credited` is caught by `test_the_accessibility_epoch_publishes_is_credited_whatever_boards_are_served`, and by that test alone.
  - An unknown access source fails closed: a `ValueError` the boot check and the nightly refresh refuse (`egress_problems`), or a 503 on `/v1/boards`. That is the right direction. The widened lookup has two rough edges (M3 below).
- **M2: fixed for the copy build 4 kept.** `StandingsStore.swift:96` treats a kept copy with `credits == nil` as due.
  - Plant: removing that condition is caught by `StandingsStoreTests.testACopyKeptWithoutCreditsIsFetchedAgainBeforeItsDay`, and by that test alone.
  - The explicit `init` (`Models.swift:352`) does not change decoding: the synthesized `init(from:)` stays, and the app builds a `Standings` only by decoding it (`Models.swift:462`).
  - Equality now includes `credits`, which is what a kept copy should compare on. A `nil` is left out when the copy is encoded.
  - The new refetch has no bound, and the empty-state text is still wrong in one case (M1 below).
- **M3: fixed in the text, not held by a test.** The English and Turkish purpose texts state the change and the absence of warranty (`Language.swift:385-390`). The LMArena credit carries `©` (`board_tables.py:85`). Removing either one passes every test (M2 below).
- **M4: fixed.** The entry is a `Label` whose visible text, `UIText.creditsTitle`, is its accessibility name (`ContentView.swift:340-344`).
- **M5: fixed in substance.** The bar holds its original two items again, and the entry sits at the end of the answers (`ContentView.swift:337-344`). As the disposition says, no capture of the sheet was added.
- **M6: fixed.** `_declared_properties` now reads stored `var`s (`tests/unit/test_ios_payload_contract.py:106`), and each served credit is held against `Credit` (`:290`).
  - Plant: renaming `licence_url` to `licence_link` is caught by `test_the_boards_payload_satisfies_every_struct_the_app_decodes`.
  - Plant: dropping `case credits` is caught by the same test.
  - The unused `type: ignore` is gone.
- **M7: fixed.** The third way and the two kinds of date are in the record. Checked read-only:
  - `harbor-framework/terminal-bench`: Apache-2.0, pushed 2026-10-09, 21 submissions with `metadata.date` from 2026-05-28 to 2026-09-29.
  - `harborframework/terminal-bench-2-leaderboard`: `license:apache-2.0`, and its card says "SUBMISSIONS CLOSED".
  - One count is off: the record says 76 folders, and there are 75 (M5 below).
- **K1: filed as #261**, which is open (checked with `gh`).
- **R1: stated** in D-193's cost paragraph and in the runbook's v2 step 9 (`docs/release-testflight.md:59-62`). Carried below.

### BLOCKING
None

### MINOR

- **M1** `ios/ModelRanking/Engine/StandingsStore.swift:94-99`, `ios/ModelRanking/ContentView.swift:1107` and `:1118`, `ios/ModelRanking/Engine/Language.swift:400-404`, `docs/release-testflight.md:61-62`. **A copy without credits is fetched again on every load, not once per launch. Nothing bounds it or says so.**
  - **Failure scenario:**
    - A build-5 phone talks to an engine without `credits`. This happens in the window before the #260 engine is deployed, or after a rollback to an older image.
    - Each fetch is saved with `credits == nil`, so the next `load()` fetches again. `load()` runs at launch, on each surface chosen, on each question routed to another surface, and on pull-to-refresh.
    - So each of those costs one `/v1/boards`: about 612 KB decoded (about 40 KB gzipped, per the D-167 measure), a re-encode, and a re-plan through `standingsStamp`. Round 1 proposed one fetch per launch.
    - Meanwhile the Credits sheet says `The credits come with the boards, which have not loaded yet.` The boards have loaded; only the credits are missing.
    - The only test fetches once, and the code comment says "at once". Neither the comment nor the runbook says the fetch repeats.
  - **Fix:**
    - Bound the rule to once per launch with a `let`, so INV-66 holds. For example: `static let launchedAt = Date()`, with the copy due when `credits == nil && stored.fetchedAt < Self.launchedAt`.
    - Add a test: a second `current` call after a fetch without credits does not fetch again.
    - Give the empty state a sentence that is true in both cases.
    - Add one line to the runbook's step 9 note.

- **M2** `ios/EngineTests/CreditsTests.swift:46-56`, `ios/ModelRanking/Engine/Language.swift:385-390`, `src/app/workflows/board_tables.py:85`. **The notices M3 added are not held by a test.**
  - **Failure scenario (planted, restored by sha256):**
    - Deleting the English sentence on how the app changes the data ("The app changes how they are shown: ...") passes all 612 Swift tests. Only the environmental `OfflineGuardTests` fails.
    - Removing `© LMArena` from the `lmarena` credit passes 565 Python tests across the 22 files that touch credits, attributions and standings.
    - So a later wording pass can silently drop the §3(a)(1)(B) indication or the §3(a)(1)(A)(ii) notice. Round 1 asked for exactly this test, and the disposition marks M3 fixed.
  - **Fix:**
    - Assert the modification clause in both languages, for example `contains("ranks each board again")` and `contains("yeniden sıralar")`.
    - Assert `"© LMArena"` in `CREDITS["lmarena"]`.

- **M3** `src/app/workflows/rank.py:193-196`, `src/app/workflows/standings.py:108` and `:125`. **Widening `attributions_for` to metadata ids weakens the board check, and its message points to the wrong map.**
  - **Failure scenarios (both reproduced on the test fixtures):**
    - An access row from an unreviewed source raises `unattributed evidence source 'someone_else_access'; add it to SOURCE_ATTRIBUTION`. But `test_families` holds `SOURCE_ATTRIBUTION` to the declared boards, so the operator is sent to the one map the fix says it must not touch.
    - A scores board whose source id is `epoch_access` now passes the per-board check at `:108` and then raises `KeyError` at `:125`.
      - `standings_problem` catches only `ValueError`, so boot and the nightly refresh's `egress_problems` crash with a traceback instead of a named refusal.
      - The `/v1/boards` handler answers 500 instead of its 503 shape.
    - This needs an id collision, so the likelihood is low.
  - **Fix:**
    - Keep `attributions_for` board-only, and give `board_standings` a separate path for metadata sources: a `metadata_sources=` argument, or a `metadata_attributions()` helper.
    - Name `METADATA_ATTRIBUTION` in the message for an unknown access source.

- **M4** `ios/ModelRanking/ContentView.swift:751`. **The data link shares its `Text` with its label, so copying it copies `Data: https://...`.**
  - **Failure scenario:**
    - D-193 clause 4 rests on the reader copying a link into a browser. On iOS, a `Text` with `.textSelection(.enabled)` is copied whole from the long-press menu.
    - So the data link pastes as `Data: https://www.swebench.com` (Turkish: `Veri: https://...`), which a browser treats as a search.
    - The licence link (`:756`) is its own `Text` and copies cleanly. The data link should too.
  - **Fix:** put `credit.url` in its own `Text`, with the label in another `Text` or as a caption above it.

- **M5** `docs/decisions.md:4795`, `ios/ModelRanking/Engine/Language.swift:375`, `docs/research/terminalbench-4-feasibility-2026-10-12.md:65`. **Three records still describe things as they were before round 1's fixes.**
  - **Failure scenarios:**
    - D-193 clause 3 says the app shows the credits "from its toolbar". The M5 fix moved the entry to the end of the answers. A later reviewer who checks the ADR against the code will find the toolbar empty of it.
    - `UIText.creditsButton` (`Credits` / `Kaynaklar`) is no longer used by the app. Only `CreditsTests` and `UITextLanguageTests` use it, so two tests keep a string nobody sees.
    - The feasibility record counts 76 TB 2.0 folders. The Hugging Face tree lists 75 folders and a `.gitkeep`.
  - **Fix:**
    - D-193 is not merged yet, so correct clause 3 in place: "from a button at the end of the answers".
    - Delete `creditsButton` and its two test rows.
    - Change 76 to 75.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/rank.py:145-161` (`secondary_evidence_sources`), `src/app/workflows/standings.py:101-103`. **Nothing holds that a recommendation's sources are among the sources `/v1/boards` credits.**
  - The Credits screen reads only `/v1/boards`, while `/v1/recommendations` cites its own `sources`.
  - On the real `advisor.db`, every source across all 14 surfaces × 3 budgets is among the boards' attributions. I measured this.
  - But nothing holds it structurally. `secondary_evidence_sources` reads every source with rows for the secondary benchmark, without the effort policy that `board_standings` applies.
  - **Failure scenario:** a source whose secondary-benchmark rows are all at a non-policy effort is cited on an answer but has no board, so it is missing from the Credits screen. D-193's claim fails silently.
  - **Fix:** this is an enhancement. Add a test over the seeded artifact, or a boot check, that the union of `recommend(...).sources` is a subset of `board_standings(conn)["attributions"]`.

## Risks queued to next M

- **R1** (carried from round 1 unchanged) D-193's cost paragraph, `docs/release-testflight.md:61-62`. **The hosted engine serves ARC-AGI, DeepSWE and OpenRouter data before their publishers have given permission.**
  - **What would show the risk is real:** an App Review question under guideline 5.2.2, or a publisher's objection.
  - **The trigger to act:** the first external-tester submission.

## Evidence

**Unmodified tree:**
- `pytest tests/unit`: 2616 passed, 9 skipped.
- `swift test --disable-sandbox`: 612 tests. Only `OfflineGuardTests.testAChildTheSuiteStartsCannotNameAnOutsidePeer` fails, and it fails without the `offline.sb` sandbox on unmodified code too.
- `make client-decls`: PASS, 21 client files in 4 configurations.

**Planted faults.** Each was a byte replacement by a Python script, restored from its backup and checked by sha256. At the end, all seven touched files matched their original sha256 and `git status` was clean. The Python plants ran against the 22 test files that touch credits, attributions, standings and the iOS contract (565 tests). The Swift plants ran against the full suite.

| fault | caught by |
|---|---|
| compiled boards mapped back to `epoch` (`rank.py:127`) | `test_a_board_epoch_compiles_credits_its_publisher_and_epochs_compilation`, `test_each_publisher_is_credited_once_in_the_order_the_attributions_come` |
| `epoch_access` dropped from `METADATA_ATTRIBUTION` | `test_the_accessibility_epoch_publishes_is_credited_whatever_boards_are_served`, `test_models_carry_the_served_blend_and_their_accessibility`, `test_refinements::test_every_board_a_question_can_select_is_served` |
| the access sources dropped from `credited` (`standings.py:142`) | `test_the_accessibility_epoch_publishes_is_credited_whatever_boards_are_served` only |
| the store's `credits != nil` removed (`StandingsStore.swift:96`) | `StandingsStoreTests.testACopyKeptWithoutCreditsIsFetchedAgainBeforeItsDay` only |
| Swift `licence_url` renamed `licence_link` | `test_the_boards_payload_satisfies_every_struct_the_app_decodes` |
| `case credits` dropped from `Standings.CodingKeys` | `test_the_boards_payload_satisfies_every_struct_the_app_decodes` |
| the English modification sentence deleted (`Language.swift:388`) | nothing (M2) |
| `© LMArena` dropped from the `lmarena` credit | nothing (M2) |

**Read-only network checks:**
- `gh api repos/harbor-framework/terminal-bench`: Apache-2.0, pushed 2026-10-09T01:08:09Z. Its 21 `leaderboard/submissions` files, read through the contents API, carry `metadata.date` from 2026-05-28 to 2026-09-29.
- `huggingface.co/api/datasets/harborframework/terminal-bench-2-leaderboard`: `license:apache-2.0`. The tree under `submissions/terminal-bench/2.0` holds 75 directories and a `.gitkeep`, and the README says "SUBMISSIONS CLOSED".
- `gh issue view 261`: open.

## Dispositions, by the author after the review

| finding | disposition |
|---|---|
| M1 | Fixed in `2a4bb34`, red in `0cfa146`. A kept copy without credits is fetched again once in a launch (`StandingsStore.launched`, dated when a store is made); a copy fetched since is kept. The first try read the launch only in the check, and `--parallel` measured two fetches: a `static let` starts on first use, after the fetch's own time. The empty sheet's text: with boards that carry no credits it says the server sends none yet, and it says "not loaded" only when no boards are loaded (`b5e1adf`). |
| M2 | Fixed in `2a4bb34`. The modification and warranty sentences are asserted in both languages, and LMArena's copyright notice in Python. `CreditsTests.swift` is in `.language-allow` for its Turkish assertions, as `LanguageTests.swift` is. |
| M3 | Fixed in `2a4bb34`, red in `0cfa146`. `attributions_for` checks boards against `SOURCE_ATTRIBUTION` alone and metadata against `METADATA_ATTRIBUTION`; an unknown metadata source is named there. |
| M4 | Fixed in `2a4bb34`. The data link is a `Text` of its own. |
| M5 | Fixed. D-193 clause 3 names the button at the end of the answers and the change the screen states; `UIText.creditsButton` is gone (`2a4bb34`); the feasibility record counts 75 folders. |
| K1 | Filed as #262. |
| R1 | Carried, as in round 1: D-193's cost and the runbook's v2 step 9. |
