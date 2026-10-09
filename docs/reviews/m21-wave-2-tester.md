---
record_type: review
id: m21-wave-2-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 2 Tester Review (reading what is not a search)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `origin/closure/m20..397ca49` (base `972b55e`). W2's own commits are
`origin/closure/m20..9613a2b` (10) and `97c4059..397ca49` (20); W1 is merged in at `97c4059`. Each
commit was read with `git show`. The worktree is detached at `397ca49`.
**Risk tier:** HIGH

Routing: the author and this seat are both Claude; no second family was available. The context is fresh.
This seat read the plan's W2 rows, D-191, both review rounds and the commits. It read no `*_heldout_*`
file and no question in any run under `docs/research/`.

## Verdict
MINOR

The wave reads what its issues ask for: a ranked or served model's name with its version is a search
in both languages, a short Turkish question stays off the English embedding, and a comparison with one
plain family is answered from `everyday`. The probe rows, the held-out gates, the UI fixture and the
judgement sheet each have tests that fail when the code under them is broken. Every red commit fails only
on its own tests, and none fails to compile.

Of 22 faults planted, the wave's tests catch 18. The 6 tests this review adds (5 in Swift, 1 in Python)
catch the other 4, and they pass on the shipped code (M6, and half of M5).

Nothing blocks: each criterion has a citing test that asserts its behaviour, and no test was weakened.
Five findings remain open, each a class of sentence read wrong:
- questions of fact read as searches through a version that is an everyday token, "step 3" and "command
  a" (M1, new at this wave);
- English searches with a Turkish name or place fall to "not measured" (M2, new);
- an English question with "mu" typed twice falls to "not measured" (M3, new at `26a334a`);
- a short Turkish comparison of two ambiguous families, and a Turkish search naming a family outside the
  twelve brands, are "not measured" (M4; the second review's M2, not closed for these);
- the screen tests' wait for a search is met by the answer already on screen (M5).

## How it was checked

- **`make check-fast`, once, before anything was planted.** PASS in 90.8 s: lint, typecheck, records,
  client-decls, test and swift-test.
  - pytest: `2372 passed, 25 skipped`, total coverage 92.08%; `src/app/workflows/registry.py`, the
    wave's one touched module under coverage, 99% (its one missed line, 417, is not the wave's).
  - swift-test: 608 tests, exactly the manifest's.
- **The red commits.** Each was extracted with `git archive` into a scratch folder (`ios/` with
  `scripts/router_probe/` beside it for Swift; the whole tree for Python). The Swift ones ran the full
  `swift test --parallel`; the Python ones ran their own test files with the tree's `src` first on the
  path. No red commit fails to compile.

  | commit | suite | failed | all its own? |
  |---|---|---|---|
  | `9d89aee` | swift (594) | 7: every test of the new `ReadingM21Tests.swift` | yes |
  | `9d89aee` | test_model_families | 2 of 3 | yes |
  | `ec9146e` | test_ios_client_contract | 3 of 56, the three it adds (its fourth is a gate, green) | yes |
  | `5fdf477` | swift (595) | 0; not named red, a fixture moved and its test | n/a |
  | `dd999bd` | swift (597) | 2, the two `JudgementRowTests` it adds | yes |
  | `dd999bd` | test_judgement_sheet | 4 of 4 | yes |
  | `345fd54` | swift (599) | 1 of the 2 it adds (the other is a guard) | yes |
  | `0c956e0` | swift (603) | 4, the four `ModelNameReviewTests` | yes |
  | `0c956e0` | test_model_families | 3 of 6, the three it adds | yes |
  | `2340761` | swift (605) | 2, the two it adds | yes |
  | `a41cfa0` | test_ios_client_contract | 2 of 58, the two it adds | yes |
  | `1e33aab` | swift (606) | 0 | see below |
  | `1e33aab` | test_judgement_sheet | 1 of 7 (the key's refusal) | yes |
  | `01fefb6` | test_screen_paths | 1 of 2 | yes |
  | `b8e3727` | swift (608) | 2: the cost test it adds, and the version test it extends | yes |
  | `7b025d9` | swift (608) | 3: the route test it adds, and the two it extends | yes |
  | `d7a327e` | test_judgement_sheet | 7 of 8 | yes, see below |
  | `6ed1c07` | test_screen_paths | 2 of 4, the two it adds | yes |

  - `1e33aab` names four behaviours red. Three were already right on its parent: "ours lands on both
    sides", "a tie is no revisit" and "both lists in place order and cut at five" pass there. Only the
    key's refusal was red. They stand as guards, and the round-1 review's planted faults are what they
    catch.
  - `d7a327e` changes the key's format to `{seed, sides}` in five earlier tests, as its body says. They
    fail on the parent for that reason, not for the behaviour they hold.
- **The reading, probed with sentences this seat wrote** (150: English and Turkish; searches naming
  served models with and without versions; questions of fact with words that have a second meaning;
  English with Turkish-looking words; short Turkish comparisons). Each was routed the way a phone without
  Apple Intelligence routes it (`TieredRouter(model: nil).route`), at `397ca49` with and without the
  served names of the 2026-10-08 snapshot (301 display names, `ServedModelNames(displayNames:)`). The
  first 120 were also routed at `972b55e`. The probe ran in a scratch copy and is not committed.
- **Faults.** 22 were planted, one at a time: 15 in a scratch copy of `ios/` outside the worktree, 7 in
  the worktree's scripts, registry and gates. F22 went into the worktree's own
  `ios/UITests/ScreenPathTests.swift`, because `test_screen_paths.py` reads that path. Each was restored
  by its bytes and checked by sha256, and `git status` showed no change after the Python runs. The
  Swift runs used `swift test --parallel --filter` over the 127 tests of the reading's suites; the Python
  runs used the touched test files.

## Faults planted

Each row: planted, the targeted suites run, restored by bytes, sha256 equal to the value before (all 22
were). "Wave" is what the wave's own tests did; "now" is with this review's tests.

| # | where | the fault | wave | now |
|---|---|---|---|---|
| F1 | `Reading.swift:239` | an ambiguous family word names a model alone | RED, 5 tests (`testAWordWithASecondMeaningIsNoModelUnlessItStandsAsOne` and 4 more) | RED |
| F2 | `Reading.swift:242` | a version written onto an ambiguous word ("llama3") is not read | RED, `testAFamilyWordThatIsAlsoEnglishNeedsAVersion` | RED |
| F3 | `Reading.swift:236` | the served versions of a registry word are dropped | RED, 2 tests (`ServedNamesRouteTests` among them) | RED |
| F4 | `Reading.swift:244` | a served-only word names a model alone | RED, `testAModelOnlyTheEngineServesIsASearch`, `testCostOrMakingWordsMakeNoModel` | RED |
| F5 | `Reading.swift:245` | a served version written onto the name ("starcoder2") is not read | **green** | RED, `testAServedVersionWrittenOntoTheNameReads` |
| F6 | `ServedModelNames.swift:20` | the served names keep no versions | RED, 3 tests | RED |
| F7 | `Router.swift:407` | a letter only Turkish has decides nothing | **green** | RED, `testATurkishOnlyLetterAloneReadsAsTurkish` |
| F8 | `Router.swift:409` | a capitalised "MI" or "MU" counts as a Turkish word | **green** | RED, `testACapitalisedWordIsNoTurkishSignalEvenTwice` |
| F9 | `Router.swift:410` | each word counted once, not per occurrence | RED, `testALetterOtherLanguagesShareIsNoTurkishAlone` | RED |
| F10 | `Router.swift:578` | a Turkish question reaches the English embedding | RED, `testAShortTurkishQuestionWithAnExtraWordIsAGeneralQuestion` | RED |
| F11 | `Router.swift:573` | a comparison of names is not answered from `everyday` directly | RED, `testAComparisonOfFamiliesOutsideTheTwelveBrandsIsEveryday` | RED |
| F12 | `Router.swift:431` | a comparison reads only the twelve brands | RED, the same test | RED |
| F13 | `Router.swift:998` | the router drops the served names on the wording path | RED, `testTheRouterReadsAServedModelAsASearch` | RED |
| F14 | `ProbeRows.swift:15` | a recorded model doubt is rebuilt as a search | RED, `testARecordedRowReadBackGivesItsReading` | RED |
| F15 | `ProbeRows.swift:54` | the judgement row's primary list shows ids while the family list shows names, so the sides can be told apart | RED, 3 `JudgementRowTests` | RED |
| F16 | `scripts/judgement_sheet.py:34` | the key's refusal inside the repository is gone | RED, `test_the_key_is_never_written_inside_the_repository` | RED |
| F17 | `scripts/judgement_sheet.py:48` | the seed is fixed again | RED, `test_the_seed_is_drawn_and_kept_only_in_the_key` | RED |
| F18 | `src/app/workflows/registry.py:545` | "zephyr" left out of the ambiguous words | RED, 2 `test_model_families` tests | RED |
| F19 | `scripts/model_family_words.py:34` | the generator writes no versions for "step" | RED, `test_the_written_file_is_the_generators_byte_for_byte` | RED |
| F20 | `tests/unit/test_ios_client_contract.py:1875` | the held-out gate stops reading `ModelFamilies.swift` | RED, `test_the_wording_read_holds_the_family_words_and_their_ambiguous_list` | RED |
| F21 | `tests/unit/test_ios_client_contract.py:1703` | the held-out gate reads every list by its start | RED, 2 tests | RED |
| F22 | `ios/UITests/ScreenPathTests.swift:59` | `waitForAnswer` returns on `field("change")` | **green** | RED, `test_what_a_search_waits_for_is_read_inside_its_wait_too` |

Kill rate (advisory, no mutation runner is wired): 18 of 22 with the wave's tests, 22 of 22 with this
review's.

## Acceptance-criterion coverage

REQ-ASK-005 is W2's row (plan §2): "A question of fact names no AI model the engine ranks as a doubt
(#194). The held-out checks read the wording tier's sentences, and match a list entry as the app does
(#180, #186). The replay harness and the probe's wording mode have tests (#193)." Each part, and each
other issue the wave delivers:
- **#194** → `ios/EngineTests/ReadingM21Tests.swift:12`, `:28`, `:48`, `:132`, `:142`, `:154`, `:163`,
  `:239`; `tests/unit/test_model_families.py:22` to `:56`. Asserts a ranked model's name, with its
  version written apart or onto it or served, is a search, and a second meaning is not. GREEN. Gaps: M1;
  one half closed here (M6).
- **#180, #186** → `tests/unit/test_ios_client_contract.py:1736`, `:1745`, `:1783`, `:1792`, `:1806`,
  `:1817`. Asserts the check reads the wording tier's text and the generated family words, each list in
  its own use's mode. GREEN.
- **#193** → `ReadingM21Tests.swift:79`, `:100` (`ProbeRows`). GREEN.
- **#218** → `ReadingM21Tests.swift:60`, `:71`, `:214`. GREEN. Gaps: M2, M3; the letter rule and the
  case rule closed here (M6).
- **#206** (D-191 clause 2) → `ReadingM21Tests.swift:182`, `:261`. GREEN. Gap: M4.
- **#199** → `ios/EngineTests/ScreenPathFixtureTests.swift:30`; `tests/unit/test_screen_paths.py:18` to
  `:59`. GREEN. Gap: M5.
- **#226** → `tests/unit/test_judgement_sheet.py:31` to `:136`; `ios/EngineTests/JudgementRowTests.swift:32`,
  `:44`, `:55`. GREEN.
- **#222** (carried) → `ReadingM21Tests.swift:122`, `:200` hold that the rule is out. **#66** (carried)
  is measured in the record, not tested.

## Red→green on reported symptoms

Every red test named in the table above fails on its red commit and passes at `397ca49` (the
`check-fast` run, and the targeted runs before each fault).

## Mocks / contract tests

No new integration. The model tier is scripted through `ScriptedModelRouter`, as before. The served
names come from `Standings.models[].display`, which `/v1/boards` already sends; the payload contract
(`tests/unit/test_ios_client_contract.py`) is unchanged by the wave.

## Findings

### BLOCKING
None

### MINOR

- **M1** `ios/ModelRanking/Engine/Reading.swift:238-239` (`namesARankedModel`), fed by
  `ModelFamilies.swift:25` (`"command": ["a", "r"]`), `:37` (`"nova": ["2", ...]`) and `:43`
  (`"step": ["3"]`), written from `src/app/workflows/registry.py:524` (`family_versions`) (#194, D-191
  clause 3).
  **Problem.** An ambiguous word names a model beside any token its names put after it. Some of those
  tokens are everyday words: the article "a", a bare number.
  **Failure scenario.** Each of these was a question of fact at `972b55e` (the fact doubt; the wording
  tier read it `unsure`). At `397ca49` each is a `search`, with or without the served names, so the screen
  loads a ranking:
  - "what is step 3 of the scientific method" (`expert`), "what is step 3 of cpr" (`search`), "what is
    step 3 in alcoholics anonymous";
  - "who was the first woman to command a space shuttle" (`expert`), "how long does it take to command a
    ship", "who was the first person to command a starship";
  - "when was nova 2 broadcast", "how much is a jamba 1 smoothie".

  Also searches at `397ca49` (not run at the base): "what is step 3 in the water cycle", "how long is step
  3 of the usmle", "who was the youngest captain to command a us navy ship", "how much is a granite 4 inch
  tile". "what is step 2 of cpr" is still a question of fact: only the version decides. With Apple
  Intelligence on, the model's "not a search" alone now gives the question back (`unsure`) where it gave
  the note (`notASearch`).
  **Fix.**
  - A version that is a single letter or a bare integer ("a", "r", "1" to "4") names the model only where
    the question ends at it, or where the next token is one the family's names put after it ("3.5",
    "flash", "08"). It never does before an article or a preposition ("a ship", "of cpr").
  - Add the sentences above to `testAWordWithASecondMeaningIsNoModelUnlessItStandsAsOne`
    (`ReadingM21Tests.swift:154`).

- **M2** `ios/ModelRanking/Engine/Router.swift:407` (the letter rule of `readsAsTurkish`), with `:578`
  and `:585` (#218, D-191 clause 1).
  **Problem.** A letter only Turkish has decides alone, wherever it stands. A Turkish name or place
  in an English sentence has those letters. A reader on a Turkish keyboard (the owner's) types them.
  **Failure scenario.** These English task descriptions name no surface. Read as Turkish, they get
  `generalSurface`, which is nil, and the outcome is `manual`, `unmeasured`: "not measured".
  - "draft an email to Çağla about the meeting" was `assistant` at `972b55e`, measured and right.
  - "plan a road trip from İzmir to Antalya", "plan a three day trip to İstanbul", "write a wedding toast
    for Ayşe and Mehmet" and "write a cover letter for a job at Şişecam" were measured at `972b55e` (as
    guesses: `web-dev`, `vision`).
  - Also not measured at `397ca49`: "help me plan a trip to Kuşadası", "write a toast for my sister
    Gülşen's wedding", "translate a letter for my friend Barış", "write an apology to Ece Şahin", "draft a
    speech for Doğan's retirement".

  The second review's M6 fix already reads a capitalised word as a name ("Kim"). The letter rule reads
  the raw text before it.
  **Fix.**
  - Let a Turkish-only letter decide alone only inside a word written in lower case. In a capitalised
    word, count it as one shared signal at most.
  - Add these sentences to `testALetterOtherLanguagesShareIsNoTurkishAlone` (`ReadingM21Tests.swift:214`).
  - `testATurkishOnlyLetterAloneReadsAsTurkish` (added here, `:279`) holds the lower-case half:
    "sınav hazırlığı" ("exam preparation").

- **M3** `Router.swift:409-410` (#218; the per-occurrence count from `26a334a`, the second review's M2 (b)).
  **Problem.** Before `26a334a` the Turkish words were counted once each (a `Set`). Now every occurrence
  counts. So an English "mu" (the Greek letter, the mean) or "mi" (solfège) typed twice is two Turkish
  signals.
  **Failure scenario.** At `397ca49` each is `manual`, not measured:
  - "estimate mu from the sample, then test whether mu equals zero" was `mathematics` at `972b55e`;
  - "find mu and sigma when mu is twice sigma", "if mu is 5 and sigma is 2 what is mu plus two sigma" and
    "write a song that goes do re mi do re mi" were `everyday` there;
  - also "calculate mu and sigma, then report mu to two decimals" and "what does mu mean when mu is the
    mean".

  One "mu" is still English ("explain the difference between mu and sigma" is `mathematics`; the test
  added here at `:279` holds it).
  **Fix.**
  - Count a particle once per occurrence only in the shape the change was made for: right after a model
    family word ("phi mi gemma mi", "Phi or Gemma?"). Count any other word once.
  - Add the sentences to `testALetterOtherLanguagesShareIsNoTurkishAlone`.

- **M4** `Router.swift:429-433` (`comparesModelsOnly`'s `isModel` needs a plain family), `:457-460`
  (`generalSurface` reads only `generalWords`' twelve brands, `:373-374`) and `:585` (#206, #222; D-191
  clause 2; the second review's M2).
  **Problem.** A Turkish question never reaches the embedding. The Turkish path then knows only a surface
  word, a comparison with one plain family, or the twelve brands. Any other model talk falls through.
  **Failure scenario.** None of these is a question of fact. Each is `manual`, not measured, at `397ca49`,
  with or without the served names:
  - "glm mi minimax mi" ("GLM or MiniMax?"), "phi mi gemma mi" ("Phi or Gemma?"), "kimi mi glm mi" ("Kimi
    or GLM?"), "o3 mü o4 mü" ("o3 or o4?"), "kimi k2 mi glm 4.5 mi" ("Kimi K2 or GLM 4.5?"), "minimax m2 mi
    kimi k2 mi" ("MiniMax M2 or Kimi K2?"), "phi-4 mü gemma 3 mü" ("Phi-4 or Gemma 3?"). At `972b55e` each
    but the last (not run there) was measured, as the embedding's guess (`search`, `document`,
    `mathematics`, `coding`).
  - "nemotron mu glm mi sence" ("Nemotron or GLM, what do you think?") was `everyday` at `972b55e`.
  - "kimi k2 kaç para" ("how much is Kimi K2") and "gemma 3 ne zaman çıktı" ("when did Gemma 3 come out")
    are searches now, which is right, and still not measured.

  The second review named "phi mı gemma mı" ("Phi or Gemma?") and "glm mi minimax mi" ("GLM or
  MiniMax?") and asked for the route's outcome.
  The fix tests only that they read as Turkish (`ReadingM21Tests.swift:226`). Its route test (`:261`)
  uses comparisons that hold a plain family.
  **Fix.**
  - On the Turkish path, a question that `namesARankedModel` (with the router's served names) and names
    no surface is a general question: answer `everyday`. "kimi kaç yaşında" ("how old is Kimi") still
    names no model.
  - In `comparesModelsOnly`, accept two family words of any kind when every word is a family, particle
    or tier word ("kimi mi", "is it some?", alone stays out).
  - Test the route outcome for the sentences above.

- **M5** `ios/UITests/ScreenPathTests.swift:55-62` (`waitForAnswer`), with `:86-88` (`setUp`) and
  `ios/ModelRanking/ContentView.swift:191-193`, `:917-934` (#199; the second review's M5).
  **Problem.** `setUp` waits until the engine's first answer shows "See the evidence". While a later
  question routes, `held` is nil, so the previous cards stay on screen until a search's answer is
  applied. `waitForAnswer` returns on that same button.
  **Failure scenario.** This is read from the code; this seat runs no UI test.
  - `waitForReading(of:)` for a fixture `search` returns at once.
  - `assertReadingAlone` then runs before the reading arrives, so a search re-read as `unsure` would
    pass.
  - No screen test waits through that arm today, so the hole is latent.
  - Separately, a planted `waitForAnswer` that returned on `field("change")` stayed green (F22):
    `test_screen_paths.py:50` reads only the arm's own line. The test added here
    (`test_screen_paths.py:59`) closes that half.

  **Fix.** Before the check, wait for the routing to end: the send button's progress view gone, or the
  question's echo, which appears once its answer has loaded. Or count the evidence buttons before the
  send, and wait for the count to change.

- **M6** `Router.swift:407`, `:409`; `Reading.swift:245` (#218, #194). Closed by this review's tests.
  **Problem.** Three halves of the wave's rules had no test that fails without them (F5, F7, F8):
  - the Turkish-only letter deciding alone: each wave sentence also holds two other signals, since
    "için" ("for") carries a c-cedilla;
  - the case rule: since "kim" ("who") and "ne" ("what") left the word list, no wave sentence holds two
    capitalised list words;
  - a served version written onto a served-only name ("starcoder2", "yi34b").

  **Failure scenario.** Remove any one of them and `swift test` stays green, while "sınav hazırlığı"
  ("exam preparation") no longer reads as Turkish, "plan a road trip from Detroit, MI to Grand Rapids, MI"
  reads as Turkish and falls to "not measured", or "who makes starcoder2" is asked as a question of
  fact.
  **Fix.** Done here: `ReadingM21Tests.swift:279`, `:291` and `:299`. Each is green on the shipped code
  and red under its fault.

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/ModelFamilies.swift:10` (`"gpt"` is a plain family word, from
  `src/app/workflows/registry.py`'s families). A bug of #238's class.
  **Problem.** "gpt" also names the GUID Partition Table.
  **Failure scenario.** "what is a gpt partition" is a `search` at `972b55e` and at `397ca49`, with no fact
  doubt.
  **Fix.** Add "gpt" to #238's ruling with the four core brands.

## Risks queued to next M

- **R1** `Reading.swift:235-239`, `registry.py:524` (#194, D-191 clause 3).
  **The risk.** The registry's curated names hold Llama 2 and 3 and Phi-3, so Llama 4, Phi-4 and Gemma 4
  name a model only through the served names. Those are empty until the standings are kept: a first
  launch offline, or a failed first fetch. A model newer than the last refresh is in the same state on
  every phone. In that window, "when did llama 4 come out", "how much does llama4 cost" and "llama 4 ne
  zaman çıktı" ("when did Llama 4 come out") are asked. All three were searches at `972b55e`, where llama
  was a brand.
  **What would show it is real:** a question back on a current model's name, from a phone with no kept
  standings. One direction is the second review's other option for its M4 (c): let `family_versions`
  read the derived identities.

## Tests added/extended this review

- `ios/EngineTests/ReadingM21Tests.swift:279` `testATurkishOnlyLetterAloneReadsAsTurkish`: D-191 clause 1,
  a Turkish-only letter decides alone, and one shared letter or one "mu" does not (F7; M2, M3).
- `ReadingM21Tests.swift:291` `testACapitalisedWordIsNoTurkishSignalEvenTwice`: the second review's M6, a
  capitalised "MI" or "MU" is no signal however often it occurs (F8).
- `ReadingM21Tests.swift:299` `testAServedVersionWrittenOntoTheNameReads`: #194, a served version written
  onto a served-only name (F5).
- `ReadingM21Tests.swift:311` `testAQuestionOfFactAboutTheOtherMeaningStaysOne`: D-191 clause 3, a word
  with a second meaning and no version stays a question of fact with the served names present, in
  English and Turkish.
- `ReadingM21Tests.swift:322` `testATurkishSearchNamingAServedVersionIsNoQuestionOfFact`: #194, a Turkish
  search with a served version.
- `tests/unit/test_screen_paths.py:59` `test_what_a_search_waits_for_is_read_inside_its_wait_too`: #199,
  `waitForAnswer`'s body names no Change (F22; M5).
- `ios/EngineTests/test-manifest.txt`: the five Swift tests, in ASCII order (613 names). `swift test
  --list-tests` equals it.

All six pass on the shipped code: `swift test --filter TesterM21W2ReadingTests` gives 5 passed;
`test_screen_paths.py` gives 5 passed; `ruff check` is clean.
