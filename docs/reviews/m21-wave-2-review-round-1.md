---
record_type: review
id: m21-wave-2-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 2 Code Review (reading what is not a search: #194, #218, #222, #186, #180, #193, #199, #226; #66 carried)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: the wave's commits were read
with `git show` and the code before the commit messages.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `972b55e..9613a2b` (`origin/closure/m20..wave/m21-w2`), the wave's 11 commits
`9d89aee` to `9613a2b`
**Risk tier:** HIGH (plan §3; `Reading.swift` is a security glob)

## Verdict
MINOR

## Summary

The wave delivers plan §2 W2. The registry's family words reach the fact doubt through a generated
file, which is deterministic and equal to the registry. A Turkish question skips the English embedding.
The probe rows are shared and tested, the held-out checks read the wording tier, and the UI routing is
in one fixture. The owner gets a blinded judgement sheet. Nothing typed leaves the phone: the app-side
changes are pure functions over the question (`Reading.swift`, `Router.swift`, `ModelFamilies.swift`),
and the only network step is the owner's documented `curl` that downloads the served boards for the
judgement sheet.

The record's tables match its runs exactly. Both scorers reproduce every count in §2, and an
independent re-run of the wording probe on this tree reproduced `after-wording-1.json` on all 78 rows.
Nothing blocks. Three of the new rules reach further, or less far, than their tests show:
- The version rule loses Llama, one of the old eleven brands, and still misses Kimi K2, Command R and
  Nova Pro (M1).
- The registry is not every served model (M2).
- Vendor and second-meaning words now hide real questions of fact (M3).
- The #222 phrases answer non-AI Turkish questions as measured (M4).
- The "Turkish letter" rule catches German and Nordic letters (M5).

The held-out matcher still misreads inline lists (M6), and the judgement sheet's tests cannot see a
broken coin (M7).

## Findings

### BLOCKING
None

### MINOR

- **M1** `ios/ModelRanking/Engine/Reading.swift:231` (with `src/app/workflows/registry.py:471`).
  **Problem.** The version rule counts an ambiguous family word only when the next token starts with a
  digit.
  **Failure scenario.**
  - *Llama regresses.* "llama" moved from `factExclusions` (one of the eleven brands) into
    `AMBIGUOUS_FAMILY_WORDS`. Probed at `972b55e` and at `9613a2b`:
    - "who makes llama" and "how much does llama cost per token": `asksAFact` was false and is now
      true.
    - `TieredRouter.read` turns them from `search` into `unsure` (the reader is asked) on both the
      model and the similarity tier.
    - The comment at `Reading.swift:221` says the eleven brands "come from there now"; for Llama they
      do not. D-189 clause 3 names phi, nova, titan and kimi, not Llama.
  - *Served models whose version starts with a letter or is a tier word stay asked.* The registry's
    own display names include "Kimi K2" (to K2.6), "Command A", "Command R", "Command R+", "Nova
    Lite/Micro/Pro", "Aya Expanse 32B" and "Trinity Large Thinking". "how much does kimi k2 cost",
    "who makes command r" and "who trains aya expanse" are asked before and after. Kimi is #194's own
    named example, and its done-when says "a search naming a ranked model outside the eleven brands
    is a search on both tiers".

  **Fix.**
  - Count `next` as a version when it starts with a digit, is a letter followed by digits (`k2`, `x1`,
    `r1`), or is a word the registry's display names put after that family word ("pro", "lite",
    "micro", "r", "a", "expanse", "large"). Derive that set in `family_words`' generator, not by hand.
  - Decide Llama explicitly in D-189 clause 3.
  - Add "who makes llama" and "how much does kimi k2 cost" to `testASearchNamingARankedModelIsNoQuestionOfFact`.

- **M2** `src/app/workflows/registry.py:455-465`; `tests/unit/test_model_families.py:22-31`.
  **Problem.** `family_words` reads only the curated tables (`_FAMILY_VENDORS`, `_VENDOR_FAMILIES`,
  `MODEL_RULES`, `DISPLAY_NAMES`). It does not read the D-157 derived identities the engine also
  ranks.
  **Failure scenario.**
  - On a served `/v1/boards` snapshot of 2026-10-08 (301 models, 63 boards), the rule does not read 28
    display names as a ranked model.
  - 15 of them are families that never reach the file: Yi (3), StarCoder 2 (3), Muse Spark (3), Hy (2),
    Inkling (2), Solar Pro 4 and WizardLM-2.
  - "who makes starcoder 2", "how much does yi-34b cost" and "who makes solar pro 4" are still asked
    at `9613a2b`.

  **The gate holds sets, not the file.**
  - The file today equals `render()` byte for byte, and its sha256 is the same under PYTHONHASHSEED 1,
    2 and 3, so it is deterministic.
  - The test compares only the quoted words, never `render()`. A planted generator fault survived it:
    `render()` writing an empty `ambiguous` set.

  **Fix.**
  - Read the names from what the engine serves. The phone already holds `Standings.models` at run
    time, and reading their display names there would retire the generated file. Otherwise extend
    `family_words` to the derived identities' first words.
  - Assert `SWIFT.read_text() == render()`.

- **M3** `src/app/workflows/registry.py:471` (the ambiguous set) and `Reading.swift:231`.
  **Problem.** Several family words have a common second meaning but are not in the ambiguous set. And
  an ambiguous word followed by any number counts as a model.
  **Failure scenario.** These ten questions of fact were asked at `972b55e` and are searches at
  `9613a2b` on both tiers:
  - "who founded nvidia" (a vendor head, not a family);
  - "what is the minimax algorithm";
  - "what is o3 in chemistry" (ozone);
  - "what is mimo in wifi";
  - "what is a glm in statistics";
  - "who is gemma chan";
  - "how long does an o1 visa take";
  - "who were the mercury 7 astronauts";
  - "when is usmle step 1".

  **Fix.**
  - Add nvidia, minimax, mimo, glm and gemma to the ambiguous set.
  - For an ambiguous word, accept only the version shapes the registry's own names use ("Mercury 2",
    "Step 3.5").
  - Add these questions to `testAFamilyWordThatIsAlsoEnglishNeedsAVersion`.

- **M4** `ios/ModelRanking/Engine/Router.swift:375-378` (D-189 clause 2).
  **Problem.** The new stems ("model", "oner") and phrases ("en iyisi" = "the best one", "için
  hangisi" = "which one for", "hangisi iyi" = "which one is good") do not require any AI cue.
  **Failure scenario.** These non-AI Turkish questions moved from "not measured" (`manual`,
  `unmeasured=true`) to a measured `everyday` ranking (`similarity`, `unmeasured=false`):
  - "tatil için en iyisi neresi" ("where is best for a holiday");
  - "kahve için en iyisi hangisi" ("which is best for coffee");
  - "araba almak için hangisi daha iyi" ("which is better for buying a car");
  - "hangisi iyi, iphone mu samsung mu" ("which is good, iPhone or Samsung");
  - "model uçak yapımı" ("building model aircraft");
  - "en ünlü model kim" ("who is the most famous model").

  They are #66's class. The negative test (`ReadingM21Tests.swift:123-127`) has three questions, and
  none holds a trigger phrase.

  **On the measured set,** the scorer and a count-only variant agree:
  - All 4 rows that moved went to `everyday`, and none of their labels allows it; the right count
    stays 44.
  - D-189's revisit condition ("the general answer given to a question whose label names another
    surface on more than half of the Turkish searches it catches") is therefore already met, 4 of 4,
    by the only set it cites. Only the word "fresh" keeps it from applying.

  **Fix.**
  - Add negative tests holding the trigger phrases and no AI word.
  - Keep the general answer, which fits the owner's "no not-measured dead ends", but let the reader
    see that the surface was not read. For example, keep the general answer's sentence instead of
    presenting it as matched.
  - Have D-189 say that its condition is met on the measured set, and why it is accepted anyway.
  - Nit: the record's §2 aside "(a fix commit's message says 12; the run says 11)" should simply say
    11.

- **M5** `ios/ModelRanking/Engine/Router.swift:404-405` (D-189 clause 1).
  **Problem.** "A Turkish letter" includes ç, ö and ü, which are also German, French and Nordic
  letters. The question words "mi" and "mu" are also English tokens (MI, Mi, mu).
  **Failure scenario.** English questions now skip the embedding and fall to "not measured", while
  their plain-letter twins keep a surface:
  - "help me draft a toast for a wedding in Zürich": `assistant` before, not measured after; the same
    sentence with "Zurich" is still `assistant`;
  - "plan a weekend in Köln with kids";
  - "a tool to practise German words like Übung and Brötchen";
  - "plan meals for a week in Göteborg";
  - "help me study for the MI board exam".

  **Fix.**
  - Let only the Turkish-only letters (ı, ğ, ş, İ) decide alone.
  - Let ç, ö, ü, "mi" and "mu" decide only with a second Turkish signal: another Turkish word or
    letter, or a Turkish hypothesis from `NLLanguageRecognizer` above a floor.
  - Add these English sentences to `testAParticleOrATurkishLetterReadsAsTurkish`'s negatives.

- **M6** `tests/unit/test_ios_client_contract.py:1619-1631`, `:1781` (#186, #180).
  **(a) Problem.** `_reading_lists` gives an inline literal the match mode of the last `let`/`var`
  within 400 characters. Eight inline lists in `Reading.swift` get another list's mode.
  **Failure scenario.**
  - Seven lists the app matches whole are checked by their start, #186's own class, so its done-when
    is unmet for inline lists:
    - lines 66-68: `["which", "best"]`, `["hangi", "hangisi"]` ("which", "which one") and
      `["ai", "llm", "yapay"]`, all under `asks`;
    - line 76: `["make"]`;
    - line 126: `["komutu", …]` ("the command");
    - line 153: `smallTalkPhrases`, which has no `.method` use, so it falls back to by-start;
    - line 357: `["logo", …]`, under `stems`.
  - Line 125's `["talimat", "kural", "ayarlar"]` ("instruction", "rule", "settings") goes the other
    way. The app matches it by `hasPrefix`, but the check reads it whole under `orderLeadIns`. A
    held-out row holding only "talimatları" ("the instructions") is not flagged. That is the M18-W3
    injection class #117 exists for.

  **(b) Problem.** `WORDING_HELD_OUT_ONLY_REVIEWED` records "learn" as in the app at `bd273bc`.
  **Evidence.** `git grep -nw learn bd273bc` finds it only in a comment. It entered at `fb773fe`, in
  `Refinements.swift` `languageBefore`. That commit is still an ancestor of the set's commit
  `4256437`, so the conclusion holds and only the recorded origin is wrong. The other 22 claims hold:
  - 20 are present at `bd273bc` by the test's own reader;
  - "pazarlama" ("marketing") and "poetry" first appear at `7c12a7b`, by `git log -S`;
  - "yoksa" ("or else") first appears at `fb773fe`.

  **(c) Problem.** No held-out gate reads `ModelFamilies.swift` or `AMBIGUOUS_FAMILY_WORDS`, though
  both are matched against questions and the second is kept by hand.

  **Fix.**
  - Read the mode at the use site, from the call right after the literal's closing bracket; fall back
    to the declaration only for `let x = [`. Add one fixture per inline shape.
  - Set "learn" to `_WORDING_IN_W3.format(sha="fb773fe")`.
  - Add the ambiguous set to the wording read.

- **M7** `scripts/judgement_sheet.py:34,59-67`; `tests/unit/test_judgement_sheet.py:31-63`;
  `ios/EngineTests/JudgementRowTests.swift:32-42`; `docs/judgement-sheet.md:30-31` (#226).
  **The sheet is blinded today.** Its columns are n, question, surface, A and B, and it holds no raw
  ids: every board model in the served snapshot has a display name. But the tests would not see the
  blinding break.
  **Failure scenario.** These planted faults all survived, and were restored by bytes and checked by
  sha256:
  - `ours_first = True`, so our list is always A;
  - `revisit` on a tie (`>=`);
  - "same" counted as ours;
  - the primary board left unsorted, and either list not cut at five. The `JudgementRowTests` fixture
    is already in position order, with three entries.

  **Also,** step 2 of the doc writes `key.json` beside `sheet.csv` inside the repository, and the key
  is not ignored by git. If the agent who makes the sheet commits both, the owner sees the key in the
  PR before judging.

  **Fix.**
  - Give the blinding test 10 or more rows and assert that ours lands on both A and B.
  - Add a tie and a "same" row to the scorer test.
  - Use a six-row board out of position order in `JudgementRowTests`.
  - Write the key outside the repository, or ignore it, until the sheet is scored.

- **M8** `ios/UITests/ScreenPaths.json` with `ios/UITests/ScreenPathTests.swift:216,231,240,247,263,269`
  (#199).
  **Problem.** The fixture's `reading` is read only by `ScreenPathFixtureTests`. Each UI test still
  waits on an element it names in its own body (`askBack`, `notASearch`, `askBack.find`).
  **Failure scenario.** A change that updates a reading and the fixture keeps `swift test` green,
  while the UI test still waits for the old element and goes red only in `make ui-test`. That is
  #199's drift, moved one step: the reading is still written in two places. Today they agree, all
  nine.
  **Fix.**
  - Have each UI test look up its question's reading in the fixture, and wait on the element that
    reading maps to.
  - Or add a Python contract test that pairs each `ask("…")` with its next waited identifier and
    checks it against the fixture.

### PASS (what looks good)

- The fault planting showed most of the wave's tests going red, and every planted file was restored by
  bytes and checked by sha256. Red: the ambiguity rule dropped, the letters prefix dropped, the family
  check removed, the Turkish letter check removed, the particles removed, the guard removed, "en
  iyisi" removed, the stems removed, the replay ignoring the model's doubt, the wording row's
  declined default, no question of fact (the fixture test), the whole flag ignored, `_matched_whole`
  forced, the hint sentences unread, `_plain` made the identity, and the registry's display names
  unread.
- #193: `ProbeRows` is the one rebuild that both harnesses and the tests call
  (`ReplayProbe.swift:32`, `ReadingProbe.swift:50`).
- The record's tables equal both scorers' counts:
  - wording runs: 44/44 right; 8 then 4 searches not measured;
  - model runs: 44, 48, 45 and 47 right; 4, 4, 5 and 3 searches asked;
  - non-searches caught: 3/3 on the wording tier, 4, 3, 5 and 3 on the model tier.
  - All 8 searches not measured before, and all 4 after, are Turkish; the 4 rows that changed are
    Turkish.
- The 37 own sentences went from 11 not measured to 0, which matches the run, and a re-run of the
  wording probe matched on all 78 rows.
- `ruff check src tests scripts` is clean. Targeted pytest: 19 passed. Targeted `swift test`: the wave's
  13 new tests pass.

## Acceptance criteria evidence

- **REQ-ASK-005, #194:**
  - code: `Reading.swift:177`, `:222-235`; `ModelFamilies.swift:8-18`; `registry.py:455-474`;
  - tests: `ReadingM21Tests.swift:12-23` (cites REQ-ASK-005 at `:1`), `:26-35`, `:37-40`;
    `test_model_families.py:22-31`;
  - partial: see M1 to M3.
- **REQ-ASK-005, #180 and #186:** `test_ios_client_contract.py:1721-1753` (fixtures), `:1627-1631`,
  `:1755-1760` (the gate), `:1796-1842` (`_wording_lists`). Partial: see M6.
- **REQ-ASK-005, #193:** `ProbeRows.swift:12-36`; `ReadingM21Tests.swift:66-99`. The rebuild and
  wording-row faults went red.
- **REQ-ASK-005, #66:** measured and carried with its number (`docs/research/m21-w2-reading-probe.md`
  §3; `docs/prd.md` REQ-ASK-005 row), and the counts were reproduced.
- **#218:** `Router.swift:395-406`, `:563`; `ReadingM21Tests.swift:49-66`.
- **#222:** `Router.swift:375-380`; `ReadingM21Tests.swift:109-127`.
- **#199:** `ScreenPathFixtureTests.swift:30-41`; `ScreenPathTests.swift:13-26`, `:31`. A planted
  reading change went red in `swift test`.
- **#226:** `scripts/judgement_sheet.py`; `tests/unit/test_judgement_sheet.py`;
  `JudgementRowTests.swift`; D-188's revisit line (`docs/decisions.md`, D-188 "Revisit when").

## Producers of the hardened invariants

- **"A search naming a ranked model is no question of fact."**
  - Producers: `InputSignals.asksAFact` (`Reading.swift:169`) through `namesARankedModel` (`:222`),
    fed by `ModelFamilies.words` and `ambiguous` from `registry.family_words` and
    `AMBIGUOUS_FAMILY_WORDS`.
  - Citing tests: `ReadingM21Tests.swift:12`, `:26`, `:37`; `test_model_families.py:22`, `:28`, `:34`.
  - Gaps: M1, M2, M3; and K1, where a second, hand-kept list of model names decides #206's general
    question.
- **"A Turkish question never reaches the English embedding."**
  - Producer: the one `NLContextualEmbedding` call site, `Router.swift:564`, behind
    `readsAsTurkish` at `:563`.
  - Citing tests: `ReadingM21Tests.swift:49`, `:60`.
  - Gaps: M5, where the rule takes in non-Turkish text.

## K.8 contract drift check

Plan §5: no `/v1` field change. `git diff --stat 972b55e..9613a2b -- src/app/adapter src/app/clients
schemas ios/ModelRanking/Engine/API.swift ios/ModelRanking/Engine/Models.swift` prints nothing. The new
symbols, by `grep -rn "family_words\|AMBIGUOUS_FAMILY_WORDS" src scripts tests`:
```
src/app/workflows/registry.py:455:def family_words() -> frozenset[str]:
src/app/workflows/registry.py:471:AMBIGUOUS_FAMILY_WORDS: frozenset[str] = frozenset({
scripts/model_family_words.py:14:from app.workflows.registry import AMBIGUOUS_FAMILY_WORDS, family_words
tests/unit/test_model_families.py:22:def test_the_phones_family_words_are_the_registrys() -> None:
ios/ModelRanking/Engine/Reading.swift:230:                    guard ModelFamilies.words.contains(word) else { return false }
ios/ModelRanking/Engine/Reading.swift:231:                    return !ModelFamilies.ambiguous.contains(word) || token != word || next.first?.isNumber == true
```
Verdict: OK. The registry stays engine-side; the phone receives words only through a generated file.

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/Router.swift:376-377`, `:420-428` (#206, M20-W3). A bug, made
  visible by #218.
  **Problem.** `generalWords.words` is a second, hand-kept list of 12 model names, and
  `comparesModelsOnly` reads it.
  **Failure scenario.** Now that every question with a Turkish particle skips the embedding, a
  comparison of ranked models outside those 12 is "not measured":
  - "phi mi gemma mi" ("Phi or Gemma?") was `document` before;
  - "nemotron mu glm mi" ("Nemotron or GLM?") was `factuality` before;
  - "mixtral mi qwen mi" stays general only because qwen is on the list.

  **Fix.** Read `ModelFamilies.words` there too.

## Risks queued to next M

- **R1** **The risk.** `scripts/router_probe/wording_heldout_m20_questions.json` has now been measured
  twice and is spent (record §1, §5). It stays live only because the gate needs one live set, so the
  next reading change has no unspent set to be measured on.
  **What would show it is real:** a later wave's reading change measured on this set again, or a
  wording entry flagged against it and reviewed instead of the set being replaced.
