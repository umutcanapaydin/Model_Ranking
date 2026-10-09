---
record_type: review
id: m21-wave-2-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 2 Code Review, round 2 (reading what is not a search: #194, #218, #222, #186, #180, #193, #199, #226; #66 carried)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: each commit was read with
`git show`, the code before its message.
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `97c4059..f33935e`, the round's 12 commits `0c956e0` to `f33935e`, read against the wave
`972b55e..f33935e` (39 commits). The M4/M5 red commit is `2340761`; the `0aa1ed5` named in the brief is no
object in the repository.
**Risk tier:** HIGH (plan §3: `Reading.swift` and `Router.swift` are security globs)

## Verdict
MINOR

## Summary

Round 1's M2, M3 (for its own sentences), M5 (for its own sentences), M6 and M7 (for its planted faults)
are closed. Round 1's R1 is filed as #237, which is open.
- `ModelFamilies.swift` equals `render()` byte for byte, and the test now holds it so.
- The held-out wording read covers the family words.
- The record's numbers reproduce exactly.
- Nothing typed leaves the phone.

Four first-round findings are not closed, or the narrowing opened a new door:
- The Turkish ask rule still answers non-AI questions with a measured ranking through Turkish homographs
  (M1).
- K1's comparison of two ranked families is still "not measured" or an embedding guess (M2).
- The new "cost or making" context turns questions of fact about granite, mercury, Command strips and
  solar panels into searches (M3).
- "llama3" and the Turkish twins of "who makes llama" are asked (M4).

The served names are wired in by code no test runs (M5). The two-signal Turkish rule takes "Kim" and
"MI" (M6). The key refusal can be passed by a path's case (M7). The record has four inexact sentences
(M8). Nothing blocks: no contract, boundary or privacy rule is broken. Each finding is a reading that is
wrong for a class of questions.

## Findings

### BLOCKING
None

### MINOR

- **M1** `ios/ModelRanking/Engine/Router.swift:463-466` (`askSubjects`), with `:471-476` (#222, D-191 clause 2).
  This is round 1's M4, and it is not closed.
  **Problem.** An ask is general when `askSubjects` names a task, but the stems are matched by their start
  and several are common Turkish words:
  - `yaz` is "summer", and it starts "yazıcı" ("printer") and "yazlık" ("summer house");
  - `ogren` starts "öğrenci" ("student");
  - `bot` is "boots";
  - `model` is also a model kit;
  - `hazirla`, `analiz` and `duzelt` name everyday tasks.
  **Failure scenario.** Each of these was "not measured" at `972b55e`. At `f33935e` each is a measured
  `everyday` ranking (`TieredRouter(model: nil).route`: `similarity`, `unmeasured=false`):
  - "yaz tatili için en iyisi neresi" ("where is best for a summer holiday"); "yazın tatil için en iyisi
    neresi" ("where is best for a holiday in summer"); "yazlık için en iyisi neresi" ("where is best for a
    summer house");
  - "yazıcı için hangisi iyi" ("which one is good as a printer");
  - "öğrenci için hangisi daha iyi, macbook mu dell mi" ("which is better for a student, MacBook or Dell");
  - "kışlık bot için en iyisi hangisi" ("which is best for winter boots");
  - "model uçak için en iyisi hangisi" ("which is best for a model aircraft");
  - "kahvaltı hazırlamak için en iyisi hangisi" ("which is best for preparing breakfast");
  - "kan analizi için en iyisi hangisi" ("which is best for a blood test");
  - "saç düzeltmek için en iyisi hangisi" ("which is best for straightening hair").

  The six round-1 sentences pass only because none of them holds a stem. Going the other way, the test's
  old sentence "muhasebe soruları için hangisi daha iyi" ("which is better for accounting questions") is
  no general question any more. It was rewritten to name a verb (`ReadingM21Tests.swift:114`).
  **Fix.**
  - Read a task by its verb forms, through the `isTurkishVerb` shape `Reading.swift:397` already has: `yaz` as
    "yazmak", "yazdır…" or "yazan", never bare.
  - Count `bot` and a bare `model` only beside an AI word or a model name.
  - Refuse an ask whose question word is "neresi" ("where").
  - Add the ten sentences above to `testAnAskAboutNoTaskOrModelIsNoGeneralQuestion` (`ReadingM21Tests.swift:190`).

- **M2** `Router.swift:587-589`, with `:471-476`, `:424-436` and `:405-410`; `ReadingM21Tests.swift:172-178`
  (#206, #218). This is round 1's K1, and it is not closed.
  **Problem.**
  - (a) `comparesModelsOnly` now reads every registry family. Its caller still answers through
    `generalSurface`, which names `everyday` only from `generalWords`' twelve brands. So a comparison of
    two families outside those twelve returns nil, which is "not measured".
  - (b) The new Turkish rule counts distinct words. "X mi Y mi", typed with a plain "mi" twice, is one
    signal, so it reaches the English embedding again. That is #218's own class.
  **Failure scenario.** At `f33935e`:
  - "nemotron mu glm mi" ("Nemotron or GLM?", K1's own example): `comparesModelsOnly` is true, and the
    outcome is `manual`, not measured;
  - "o3 mü o4 mü" ("o3 or o4?"): not measured;
  - "phi mi gemma mi" ("Phi or Gemma?", K1's own example): not Turkish, so the English embedding gives
    `document`, as at `972b55e`;
  - "glm mi minimax mi" ("GLM or MiniMax?"): the embedding gives `search`.

  **Planted fault.** I removed the widening line from `isModel` (`Router.swift:430`), restored it by bytes
  and checked it by sha256. The targeted suites stayed green. Each of the test's two questions holds a
  `generalWords` brand ("qwen", "claude"), and the `allSatisfy` clause reads `ModelFamilies` anyway.
  **Fix.**
  - When `comparesModelsOnly` holds, answer `everyday` directly (when it is known), not through
    `generalSurface`.
  - Count a particle between two names as a Turkish signal of its own, or count occurrences.
  - Test the route's outcome, not the predicate, for "nemotron mu glm mi", "phi mı gemma mı" and "glm mi
    minimax mi".

- **M3** `ios/ModelRanking/Engine/Reading.swift:229-246` and `:252-256` (`modelContext`);
  `ServedModelNames.swift:15-21` (#194). These are new collisions from the round's fix for round 1's M1.
  **Problem.** For an ambiguous family word, and for every first word of a served name, one context word
  anywhere in the question makes it a model. The words are `cost`, `price`, `makes`, `released`,
  `context` and the like, and they are just as common in questions about the thing the word also names.
  **Failure scenario.** These questions of fact lose the fact doubt and are read as searches, so only a
  doubting on-device model stands between them and a ranking. Each was asked at both `972b55e` and
  `9613a2b`:
  - "how much does a granite countertop cost", "what is the price of granite per square foot";
  - "what is the price of mercury", "when was mercury released as a single";
  - "how much does a command strip cost";
  - "how much does a titan watch cost", "when was the titan submarine released";
  - with the names of the served snapshot of 2026-10-08 (301 models): "how much do solar panels cost"
    ("Solar Pro"), "who makes meta quest" and "how much does a meta quest 3 cost" ("Meta Llama").

  Round 1's M3 class also survives by this road. "how much does the usmle step 1 cost", "how much does
  an o1 visa cost" and "what is the price of nvidia stock" are searches.
  **Fix.**
  - For `cost`, `price`, `makes` and `released`, count the context only when it is bound to the name
    ("o3's price", "the cost of llama 3", "who makes llama" with the name as its object).
  - Elsewhere, count only the AI-only words (`api`, `token(s)`, `parameters`, `benchmark`, `weights`,
    `llm`).
  - Never let a served-only word stand on context alone.
  - Add these sentences to `testAWordWithASecondMeaningIsNoModelUnlessItStandsAsOne` (`ReadingM21Tests.swift:144`).

- **M4** `Reading.swift:233-241`; `ReadingM21Tests.swift:33`; `src/app/workflows/registry.py:524-534` (#194).
  This is round 1's M1, and it is not closed for two spellings.
  **Problem.**
  - (a) A version written onto the word is read by its letters only when the family is not ambiguous
    (`:238-240`). So "llama3", "phi4" and "gemma3", Ollama's spelling, name no model.
  - (b) `modelContext` is English only, so the Turkish twins of the English searches are questions of
    fact.
  - (c) `family_versions` reads only the registry's curated names. They hold Phi-3 and Llama 2 and 3,
    not Phi-4 or Llama 4. Without the served names, "what is phi-4 good at" is asked. The round's red
    commit changed the existing assertion from "phi-4" to "phi-3" (`ReadingM21Tests.swift:33`) rather than
    supplying the names.
  **Failure scenario.** These are read as questions of fact at `f33935e`, even with the served names:
  - "what is llama3 good at" (a search at `972b55e` and at `9613a2b`), "what is phi4 good at" and "what
    is gemma3 good at" (searches at `9613a2b`);
  - "llama'yı kim yaptı" ("who made Llama") and "llama kaç para" ("how much is Llama"). Both were
    searches at `972b55e`, where llama was one of the eleven brands. The English "who makes llama" is a
    search, as D-191 decides;
  - "o3 kaç para" ("how much is o3"), "gemma kaç para" ("how much is Gemma") and "glm ne zaman çıktı"
    ("when did GLM come out"): searches at `9613a2b`.

  The round's commit title claims "a served model's name is a search whatever its version's spelling".
  **Fix.**
  - Read letters followed by digits for an ambiguous word when the digits are a version its names use
    ("llama3" is Llama 3).
  - Add Turkish context: "kim yap…", "kaç para", "fiyat…", "ne zaman çık…".
  - Restore "what is phi-4 good at" in the test with served names, or let `family_versions` read the
    derived identities.

- **M5** `Router.swift:1004-1020`, `Reading.swift:236` and `ContentView.swift:81-88` (#194, round 1's M2);
  `ios/UITests/ScreenPathTests.swift:46`, `:258`; `tests/unit/test_screen_paths.py:32` (#199, round 1's
  M8). Each of these fixes has a half that no test holds.
  **Failure scenario.** Faults planted, each restored by bytes and checked by sha256:
  - **The router dropping the served names.** I dropped `served: servedNames` at all four `route` calls.
    The full `swift test` (606 tests) stayed green, except one failure caused by my scratch copy's missing
    `scripts/` folder. The screen's served names reach the reading only through `route`. No test calls
    `route` with `servedNames` set, and `ContentView`'s `router` is SwiftUI, which no test runs.
  - **The served versions of a registry word.** I dropped `|| served.versions[token…]`
    (`Reading.swift:236`). That clause is what makes "what is phi-4 good at" and "when did llama 4 come
    out" searches in the app. The targeted suites stayed green.
  - **The UI fixture's reading (M8).** I changed the fixture's reading of "what is the capital of
    australia" from `notASearch` to `unsure`, and `test_screen_paths.py` stayed green. After that change
    in both the code and the fixture, `swift test` and pytest are green, and the UI test fails at `:258`
    (`XCTAssertFalse(field("askBack").exists)`) only in `make ui-test`. Also, the `search` arm waits for
    `change` (`:46`), which the note shows too (`:305`). No test waits through that arm today.
  **Fix.**
  - Add a `TieredRouter` test with `servedNames` set that routes "when did yi-34b come out" and "what is
    phi-4 good at" to `search`.
  - Derive each UI test's assertions after the wait from its fixture reading, or check them against it in
    `test_screen_paths.py`.
  - Wait for a search by an element only an answer shows.

- **M6** `Router.swift:393-410` (#218, D-191 clause 1). Round 1's M5 is closed for its five sentences.
  **Problem.** Two signals decide, and the 29 words include:
  - "kim" ("who"), which is also a common English given name;
  - "ne" ("what") and "mi", which are also the Nebraska and Michigan abbreviations;
  - "en", "ve", "var", "bir" and "ile".
  **Failure scenario.** These English questions reached the embedding at `972b55e` (`vision`, `everyday`,
  `vision`). Now they fall to "not measured" (`manual`, `unmeasured=true`):
  - "write a cover letter for Kim in Detroit, MI";
  - "plan a road trip from Detroit MI to Omaha NE";
  - "write a short bio of Björk for Kim".
  **Fix.**
  - Read the case before folding: a capitalised "Kim", "MI" or "NE" is no Turkish signal.
  - Or require one of the two signals to be a particle, `icin` or `hangi…`, or require a Turkish
    `NLLanguageRecognizer` hypothesis.
  - Add the three sentences to `testALetterOtherLanguagesShareIsNoTurkishAlone` (`ReadingM21Tests.swift:198`).

- **M7** `scripts/judgement_sheet.py:25`, `:32`; `docs/judgement-sheet.md:31`;
  `tests/unit/test_judgement_sheet.py:115-123` (#226). Round 1's M7 is closed for its four planted faults
  (each is red now). The refusal has a gap.
  **Problem.**
  - (a) `key.resolve().is_relative_to(ROOT)` compares strings. The Mac's default volume ignores case,
    and `resolve()` does not fold it.
  - (b) The documented seed is fixed (`--seed 2026`). With it, `random.Random(2026)` flips the same
    coins, so the key can be regenerated from the committed sheet and the doc.
  - (c) If the refusal regresses, the test writes a real key into the repository
    (`sheet.ROOT / "docs/research/judgement/key.json"`), as the red commit's run did.
  **Failure scenario.** I ran a scratch copy of the script, whose `ROOT` is its own folder. A key path
  that spelled that folder with different capitals was written inside it. The exact spelling and a `..`
  spelling were refused.
  **Fix.**
  - Compare by identity: `os.path.samefile` on the nearest existing parent, or
    `git -C <key's folder> rev-parse --show-toplevel`.
  - Draw the seed from `secrets` and keep it only in the key.
  - Monkeypatch `sheet.ROOT` to `tmp_path` in the test.

- **M8** The record and D-191: `docs/research/m21-w2-reading-probe.md:76`, `:95-96`;
  `docs/decisions.md:4604-4607`, `:4638-4643`; `scripts/router_probe/ReadingProbe.swift:48`.
  - **(a) The model tier.** §6 says the review's changes reach the model tier "only through the fact
    doubt's model names". When the model declines, the wording tier answers (`Router.swift:1005-1007`),
    and that path carries clauses 1 and 2. The model tier's "3 to 5 of 71 asked" is labelled as before
    the fixes, which is honest. The reason given for not running it again is not.
  - **(b) The served names.** The probes run `TieredRouter(model: nil)` and `TieredRouter.read(question,
    $0)` without `servedNames`. So the record measures the router the app runs only before the standings
    load. I re-ran the wording probe with the served snapshot's names: all 78 rows were identical to
    `review-wording-1.json`, so the wording numbers stand. The record should say the names were absent,
    and that the model tier was not measured with them.
  - **(c) A stale citation.** §6 cites `docs/reviews/m21-wave-2-review.md` for M1 to M8. That path is
    now this review; cite `m21-wave-2-review-round-1.md`.
  - **(d) The revisit statement.**
    - D-191's statement that its revisit condition is met is honest about the set: 1 of 1, which I
      verified.
    - It leaves out the second half of round 1's M4 fix, "let the reader see that the surface was not
      read". The general answer still says "Matched on wording, not on meaning — check this is the
      right surface", and D-191 does not say why.
    - Its reason, that the alternative is "not measured", is the outcome its own narrowing chose for
      three of the four held-out searches.
    - M1 shows that the narrowed clause still gives non-AI asks a measured `everyday`.
  - **(e) The word list.** Clause 1 calls `turkishQuestionWords` "the question particles, 'which',
    'for', 'the best'". It holds 29 words, "kim", "ne", "en", "ve" and "var" among them (M6). C-cedilla
    is not a German or Nordic letter.
  **Fix.** Correct §6's sentence and its citation. Say that the served names were absent. In D-191, say
  what the reader sees and why the second half of M4 was not done, and describe the word list as it is.

### PASS (what looks good)

- **The generated file.** `ModelFamilies.swift` equals `render()` byte for byte, with sha256
  `cf2efc24ceae8203…` under PYTHONHASHSEED 1, 2 and 3. A planted generator fault (`render()` writing an
  empty `ambiguous`) is now red (`tests/unit/test_model_families.py:42`).
- **The held-out gates over it.** `_wording_lists` (`tests/unit/test_ios_client_contract.py:1858-1873`)
  reads `ModelFamilies.swift` (its words, ambiguous words and versions) and `AMBIGUOUS_FAMILY_WORDS`.
  `turkishAsks`, `askSubjects` and `turkishQuestionWords` sit inside the `CategoryHints` region (lines
  66 to 519), and `modelContext` sits inside `_reading_lists`. Nothing new is flagged.
- **Round 1's M6 (a).** I printed `_lists_in`'s mode for every literal in `Reading.swift`. The eight
  lists round 1 named are now read as the app matches them: lines 66-68, 76, 126, 153 and 378 whole;
  125 by its start.
- **The record's numbers.** I checked them with a count-only scorer.
  - `review-wording-1` and `-2`: 44 of 78 right; 7 of 71 searches not measured, all Turkish; none given
    the note; none asked; 3 of 7 non-searches caught. The two runs are identical row for row.
  - From before to after the review, one row changed: Turkish, now `everyday`, which its label does not
    allow. So "1 of 1" is true.
  - From the first fix to after the review, three rows went back to "not measured".
  - Own sentences: 2 of 37 not measured.
  - My re-run at `f33935e` reproduced `review-wording-1.json` on all 78 rows.
- **The privacy rule (D-126, D-160).** The new flow runs inward: standings, then `ServedModelNames`,
  then the reading.
  - `EngineClient.swift` and `StandingsStore.swift` are unchanged in the range.
  - `refreshStandings` fetches the boards the same way whatever is typed (`ContentView.swift:1072-1078`),
    and `load()` starts it at launch (`:153`, `:1066`).
  - `tests/unit/test_client_decl_gate.py` is green.
  - The reading stays on the device.
- **Round 1's M2 in the app.** With the snapshot's 301 names, I tried three frames per name ("what is
  X", "when did X come out", "X kim yaptı" ("who made X")). 9 of the 903 stay a question of fact, all
  single-word names (Hy3, Inkling, o3), against 72 without the served names.
- **Planted faults that went red,** each restored by bytes and checked by sha256:
  - the ask rule without `askSubjects` (4 tests failed);
  - one Turkish signal deciding (5);
  - the served versions dropped (5);
  - no context (5);
  - the primary board unsorted (1);
  - the family list cut at six (1);
  - "ours" always A;
  - a tie calling the revisit;
  - "same" counted as ours;
  - a UI wait naming its element by hand.
- **Runs.**
  - pytest: 125 passed (`test_ios_client_contract.py`, `test_client_decl_gate.py`,
    `test_model_families.py`, `test_judgement_sheet.py`, `test_screen_paths.py`).
  - `ruff check src tests scripts` is clean.
  - Targeted `swift test`: 33 passed, the round's 7 new tests among them.

## Round 1's findings, one by one

| Round 1 | Closed? | Where |
|---|---|---|
| M1 | In part. "who makes llama", "how much does kimi k2 cost", "who makes command r" and "who trains aya expanse" are searches. Spellings with the version attached, and Turkish spellings, are not | M4 here |
| M2 | Yes in the app. The byte-for-byte test is present; the wiring is untested | M5 here |
| M3 | Its ten sentences are asked again; the context rule reopens the class | M3 here |
| M4 | No. D-191 states that its condition is met | M1, M8 (d) here |
| M5 | Its five sentences are closed | M6 here |
| M6 | (a), (b) and (c) are closed | PASS |
| M7 | Its four faults are red now; the key refusal has a gap | M7 here |
| M8 | The waits are closed as specified; the assertions after them are not | M5 here |
| K1 | No | M2 here |
| R1 | Filed as #237 (open) | none |

## Acceptance criteria evidence

- **REQ-ASK-005, #194:**
  - code: `Reading.swift:169`, `:226-246`, `:252-256`; `ServedModelNames.swift:15-27`; `ModelFamilies.swift`;
    `registry.py:524-546`; `Router.swift:986`, `:1004-1020`;
  - tests: `ReadingM21Tests.swift:12`, `:26`, `:136`, `:144`, `:153`; `test_model_families.py:42`, `:49`, `:56`;
  - partial: M3, M4, M5.
- **#218:** `Router.swift:393-410`, `:592`; `ReadingM21Tests.swift:51`, `:198`. Partial: M2 (b), M6.
- **#222:** `Router.swift:457-476`; `ReadingM21Tests.swift:111`, `:190`. Partial: M1.
- **#180, #186:** `test_ios_client_contract.py:1611-1630`, `:1755-1777`, `:1858-1873`; the fixtures at
  `:1719-1753`.
- **#199:** `ScreenPathTests.swift:29-51`; `test_screen_paths.py:17-37`. Partial: M5.
- **#226:** `scripts/judgement_sheet.py:29-52`; `test_judgement_sheet.py:89-123`; `JudgementRowTests.swift:55`.
  Partial: M7.

## Producers of the hardened invariants

- **"A search naming a ranked model is no question of fact."**
  - Producers: `InputSignals.asksAFact` (`Reading.swift:169`) through `namesARankedModel` (`:226`). It
    is fed by `ModelFamilies` (generated) and `ServedModelNames` (`ServedModelNames.swift:15`), which
    reach it through `TieredRouter.servedNames` (`Router.swift:986`, `:1004-1020`) and
    `ContentView.swift:84-88`.
  - Citing tests: `ReadingM21Tests.swift:12`, `:26`, `:136`, `:144`, `:153`; `test_model_families.py`.
  - Gaps: M3, M4, M5. The wiring through `route` and `ContentView` has no citing test.
- **"A Turkish question never reaches the English embedding."**
  - Producer: the one `NLContextualEmbedding` call site, behind `readsAsTurkish` (`Router.swift:592`).
  - Citing tests: `ReadingM21Tests.swift:51`, `:62`, `:198`.
  - Gaps: M2 (b), where "X mi Y mi" reaches it; and M6, where English text does not.

## K.8 contract drift check

Plan §5: no `/v1` field change. `git diff --stat 97c4059..f33935e -- src/app/adapter src/app/clients schemas
ios/ModelRanking/Engine/API.swift ios/ModelRanking/Engine/Models.swift ios/ModelRanking/Engine/EngineClient.swift
ios/ModelRanking/Engine/StandingsStore.swift` prints nothing. The new symbols:
```
src/app/workflows/registry.py:524:def family_versions() -> dict[str, frozenset[str]]:
scripts/model_family_words.py:14:from app.workflows.registry import AMBIGUOUS_FAMILY_WORDS, family_versions, family_words
tests/unit/test_model_families.py:59:    versions = registry.family_versions()
ios/ModelRanking/ContentView.swift:86:        reading.servedNames = ServedModelNames(standings)
ios/ModelRanking/Engine/Router.swift:986:    var servedNames = ServedModelNames()
```
Verdict: OK. `Standings.models[].display` was already decoded; nothing is added to the payload.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/registry.py:536-546` (`AMBIGUOUS_FAMILY_WORDS`), read by `Reading.swift:233-234`. A bug.
  **Problem.** Family words with a common second meaning are outside the ambiguous set, so they always
  name a model.
  **Failure scenario.** "who was claude monet", "when is gemini season", "what is the mistral wind" and
  "who is grok in heinlein" are read as searches, with no fact doubt. That was already so at `972b55e`,
  where all four were among the eleven brands, so it is not this round's regression. But the set that
  can decide them now exists.
  **Fix.** Decide claude, gemini, mistral and grok in `AMBIGUOUS_FAMILY_WORDS`, with the versions their
  names use.

## Risks queued to next M

- **R1** **The risk.** The fact doubt now reads the engine's served display names (`ServedModelNames`,
  from `/v1/boards`). The first word of every served name becomes a model word whenever a context word
  is present. Today that adds "meta" and "solar" (M3). The names come from upstream boards. A new model
  whose name starts with a dictionary word (Hermes, Ring, Seed, Sonar and Falcon are real model names)
  would widen the fact doubt's bypass on every phone at the next refresh, with no gate or review. Nothing
  typed leaves the phone: D-160 holds, and the flow runs inward.
  **What would show it is real:** a served display name whose first word is a dictionary word, or a
  question of fact read as a search because of one.
