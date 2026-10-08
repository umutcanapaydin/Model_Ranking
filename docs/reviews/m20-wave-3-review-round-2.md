---
record_type: review
id: m20-wave-3-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 3 Code Review, round 2 (the question picks its family, #211, #206)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave or its fixes)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `4df0cfc` and `7c12a7b` (the wave), `7408af2` (red tests) and `fb773fe` (fix) answering
`docs/reviews/m20-wave-3-review.md`; read with `git show`. The worktree is detached at `fb773fe`.
**Risk tier:** HIGH (plan §2 W3: `Router.swift` is a security glob)

## Verdict
MINOR

Every first-round finding is answered, and B1 is closed the way the first review's option (b) asked:
the PRD row says PARTIAL, the plan names W4, and D-188 clause 6 records the amendment to D-168
clause 4. Nothing about the question leaves the phone. What is left is MINOR, because nothing in the
app calls `Refinements.read` yet. The new rule for language names still reads a nationality after
"in" (M1). D-188 clause 6 says two things the code does not do (M2, M3). One Turkish stem still has
a second meaning (M4). The new context-word rules are mostly untested (M5). #206 covers bare model
names only (M6). And W4's own section does not carry the wiring it now owns (M7).

## How it was checked

- Read the first-round record, `git show` of `7408af2` and `fb773fe`, D-168 clauses 1 to 4
  (`docs/decisions.md:3233-3247`) and its new note (`:3314`), D-188 clause 6 (`:4458-4466`), plan
  §1 and §2 W3 and W4 (`docs/plans/m20-plan.md:45,82-112,170-171`), the PRD row (`docs/prd.md:613`)
  and `gh issue view 206`.
- Copied `ios/` and `scripts/router_probe/` (no held-out file) to the scratchpad, outside the
  worktree. The copies of `Refinements.swift` and `Router.swift` have the worktree's sha256
  (`45aa1589…5f5a`, `ac1079a0…94bd`). `swift test --filter 'QuestionFamilyTests|KeywordRoutingTests'`:
  27 tests, 0 failures.
- Ran two scratch probe suites that call the real `Refinements.read`, `familyBoards`,
  `CategoryHints.comparesModelsOnly` and `TieredRouter(model: nil).route` on about 150 English and
  Turkish questions. Results are quoted below.
- Planted 8 faults in the new rules and re-planted 4 of the first round's, each with a Python script
  that restored the file by bytes and checked its sha256 after the run; every restore matched.
- Planted 5 second readers of `Refinements.read` in a scratch copy of the client and ran the real
  gate function against it (stubbing only the engine import the gate does not use); each restore
  matched by sha256 or the planted file was removed.
- `tests/unit/test_router_hints.py` and `tests/unit/test_refinements.py`: 53 passed.
- The worktree has no changes other than this file. Both scratch copies were deleted afterwards.

## The first round's findings, re-checked

- **B1 (nothing calls the wave's code; the record said MET): closed by option (b).** The PRD row
  says "PARTIAL: the Engine functions exist and hold; M20-W4's answer plan is what reaches them"
  (`docs/prd.md:613`). The plan has the amendment (`m20-plan.md:91-93`). D-188 clause 6 amends D-168
  clause 4 and D-168 carries the note (`decisions.md:3314,4458-4466`). The gate exists
  (`test_router_hints.py:350-363`). #206 is delivered (`Router.swift:391-402,533-536`). Residuals:
  W4's section does not carry the work (M7), and the gate reads one spelling (M3).
- **M1 (English language names have a second meaning): closed for its probes, reopened by the new
  rule.** All eight first-round probes now read nothing (`QuestionFamilyTests.swift:100-107`). But
  "in" before a nationality still reads it (M1 below).
- **M2 (`lehce` is also "dialect"): closed.** The stem is gone. `karadeniz lehçesi ile yaz` ("write
  in the Black Sea dialect") and `bu lehçeyi anlayan yapay zeka` ("an AI that understands this
  dialect") read nothing (`QuestionFamilyTests.swift:109-114`).
- **M3 (domain words with a second meaning): closed for English.** All eleven first-round probes
  read nothing (`QuestionFamilyTests.swift:117-131`), and `bilimkurgu hikayesi yaz` ("write a
  science-fiction story") reads only `writing`. The Turkish side keeps two such words (M4 below).
- **M4 (the tests missed planted faults): closed for the first round's plants.** Re-planted:
  P1 (`familyBoards` ignores the kind order), P3 (the "bilim kurgu" ("science fiction") guard
  removed), P5 (the family not deduplicated) and P6 (a refinement already in the family counts
  toward the cap) are each *caught* by one `QuestionFamilyTests` failure. P2's guard is gone with
  the word `law`, and "my sister in law wants a recipe" reads nothing.
- **M5 (copied code; an empty family dropped the primary): closed.** `familyBoards` takes the
  primary and keeps it when the family is empty (`Refinements.swift:99-101`); `boards(primary:…)`
  calls it (`:218-220`); `read` uses `CategoryHints.readings`, now internal (`Router.swift:386-389`).
  Probe: `familyBoards(primary: "arena", family: [], surface: "assistant", chosen: [german, french])`
  returns `["arena", "arena_text_german", "arena_text_french"]`.
- **M6 (the plan's Turkish example): closed.** The plan names the eight Arena languages and says
  Turkish has none (`m20-plan.md:87-90`). `türkçe metin yaz` ("write a Turkish text") reads nothing.
- **R1 (the gate read only `Router.swift`): addressed.** The new gate scans the whole client tree.
  It matches one spelling only (M3 below).

## Findings

### BLOCKING
- None

### MINOR

- **M1** `ios/ModelRanking/Engine/Refinements.swift:157` and `:186-194` (`languageBefore`, `namesLanguage`).
  **"in" before a nationality still reads it as the task's language.** "in" is the most common
  English preposition, and it often comes before an adjective that is a nationality. Probe results:
  - "best ai for investing in chinese stocks" → `chinese`
  - "what is trending in korean dramas" → `korean`
  - "recipes in french cuisine" → `french`
  - "trends in german politics" → `german`
  - "news in japanese markets" and "invest in japanese yen" → `japanese`
  - "in russian history class" → `russian`
  - `languageAfter` has the same problem with "speaker": "best chinese speaker brand" → `chinese`,
    "japanese speaker for my car" → `japanese`.

  D-188 clause 6 says a name "counts only as the task's language". The test checks the first round's
  eight probes but none of the new rule's own collisions. **Failure scenario.** Once W4 wires
  `read`, "news in chinese economy" (the first round's M1 failure, worded the other way) adds Arena's
  Chinese-prompts board to `everyday` at equal weight. That changes the list and shows a "Chinese"
  chip the reader never asked for. **Fix.** Count "in X" only when X ends the question or the next
  word is not a noun X describes: X is last, or it is followed by a function word ("please", "and",
  "or", "with", "for", "to", "only", "instead"). That keeps "answer in french please", "a reference
  letter in spanish" and "legal contracts in french". Drop "speaker"/"speakers", or read them only
  after "native". Add the probes above as negative tests.

- **M2** `ios/ModelRanking/Engine/Refinements.swift:175-184` with `:99-111`, against `Router.swift:832-837`
  and `docs/decisions.md:4459-4460`. **The words can choose two languages, which the model never can.**
  D-188 clause 6 says the words choose "the refinements it would have". The model's schema has one
  field per kind, and `ModelOutputBoundary.refinements` keeps one value per kind. `read` returns every
  language named. Probes:
  - "translate legal contracts from german to french" → `read` gives `french, german, legal`.
    `familyBoards` keeps `french, german` and drops `legal`, the domain the question plainly names.
    The model path would give one language and `legal`.
  - "translate from korean to japanese" → `japanese, korean`.

  Also, within a kind, `read` returns table (alphabetical) order, not the order in the question. So
  with three languages, the two kept are the first two alphabetically. The fix commit changed a red
  test's expected order to "the order chosen" (`QuestionFamilyTests.swift:69`). **Failure scenario.**
  The same question ranks on different boards with Apple Intelligence on and off, and the "off" path
  drops the domain the reader named. **Fix.** Either keep at most one refinement per kind from the
  words, as the boundary does (for a translation, the "to/into" language), or amend clause 6 to say
  the words may choose two languages and that a domain then gives way. Add a test either way.

- **M3** `tests/unit/test_router_hints.py:350-363`. **The one-reader gate sees one spelling.** D-188
  clause 6 rests on "a gate holds it". The gate's regex is `\bRefinements\.read\(`. Five second
  readers were planted in a scratch copy of `ios/ModelRanking/`:
  - G1, `Refinements.read(q)` in `ContentView.swift`: *caught*.
  - G2, `let reader: (String) -> [Refinement] = Refinements.read`: *survives*.
  - G3, `qs.map(Refinements.read)`: *survives*.
  - G4, a new `extension Refinements { static func fromWords(_ q: String) -> [Refinement] { read(q) } }`
    file, called from anywhere: *survives*.
  - G5, `Self.read(q)` in an extension: *survives*.

  G2, G3 and G4 compile: a scratch probe called each and got `french`, `german` and `korean`. The
  gate also names its allowed file by base name only (`path.name`), so any `AnswerPlan.swift` in
  any folder passes. **Failure scenario.** W4 (MEDIUM, `AnswerPlan.swift` is not a security glob)
  adds a helper that wraps `read`. The words' refinements then reach a second place, for example a
  chip or a log line, and the gate stays green. **Fix.** Rename `read` to a distinctive identifier
  (for example `refinementsFromWords`). Have the gate count every occurrence of
  `\brefinementsFromWords\b` outside its declaration and outside `Engine/AnswerPlan.swift`, matched
  by relative path. Plant G2 to G4 as gate self-tests.

- **M4** `ios/ModelRanking/Engine/Refinements.swift:142` and `:145`, and `:140`. **Turkish words with a
  second meaning remain.** The fix dropped the English "story"/"stories" because of "user stories",
  but kept the Turkish stem `hikaye` ("story"), which Turkish agile teams use the same way. Probes:
  - `kullanıcı hikayesi yaz` ("write a user story") → `writing`
  - `sunucu işletmek` ("to run a server") → `business`. The stem `isletme` ("business
    administration") also starts the verb `işletmek` ("to operate").
  - "doctor who episodes" → `medicine`

  **Failure scenario.** As in M1, a refinement nobody asked for joins the family. **Fix.** Block
  `hikaye*` after "kullanici" (a `notAfter` entry). Add `isletmek` to `notStarting`, or list the
  noun's forms as whole words. Block "doctor" before "who". Add the three probes as negative tests.

- **M5** `ios/EngineTests/QuestionFamilyTests.swift:75-131`. **Most of the new context-word rules are
  untested.** Each plant was restored, and its sha256 checked, before the next:
  - **S1.** "speak" and "speaking" no longer make a language name. *Survives.*
  - **S2.** "to"/"from" count with no translation word in the question. *Survives.* Nothing
    tests a question like "switching from german cars to japanese ones".
  - **S3.** Only "language" after a name counts ("translation", "translator", "speaker" dropped).
    *Survives.*
  - **S4.** `comparesModelsOnly` needs no Turkish particle, so a bare "claude" skips the embedding.
    *Survives.*
  - **S6.** The writing guard keeps only "code" ("tests", "scripts", "sql", "queries",
    "functions" dropped). *Survives.*
  - **S8.** "scientific" loses its data/computer guard. *Survives.*
  - Not counted: S5 (`read` uses only the first case folding) and S7 (the #206 shortcut without
    `named == nil`) also survive, but `CategoryHints.plain` and the all-words rule make each
    equivalent.

  So no test holds parts of `languageBefore`, `languageAfter`, `notAfter` and `notBefore`, the
  translation-word condition, or the particle rule.

  **Fix.** Add one positive test for each context word ("speak french with me", "korean
  translation", "a german speaker" if kept, "translator from chinese"). Add a negative test for "to"
  or "from" with no translation word: "switching from german cars to japanese ones" must read
  nothing. Add a negative test for each writing guard ("writing tests for my api", "writing sql").
  Add a routing test that a bare model name without a particle ("claude") still reaches the tiers
  below.

- **M6** `ios/ModelRanking/Engine/Router.swift:391-402` and `:371-378`; `ios/EngineTests/KeywordRoutingTests.swift:233-245`.
  **#206 covers bare model names only.** `comparesModelsOnly` accepts only `generalWords.words`, which
  has no tier names (pro, mini, flash, sonnet, opus, haiku, plus, turbo). With no on-device model:
  - `gemini pro mu chatgpt mi` ("Gemini Pro or ChatGPT?") → `coding`
  - `gpt 4o mini mi claude haiku mu` ("GPT-4o mini or Claude Haiku?") → `coding`
  - `claude sonnet mı gpt mi` ("Claude Sonnet or GPT?"), `claude opus mu gpt mi daha iyi` ("is Claude
    Opus or GPT better?") and `chatgpt plus mı claude pro mu` ("ChatGPT Plus or Claude Pro?") reach
    `everyday` only because the embedding happened to place them there.

  The issue's own scope is "words … mostly model or product names". The test checks only bare names.
  The fix adds no collision: English questions with no Turkish particle are untouched ("claude vs
  chatgpt", "claude or chatgpt" and "is claude good" still go to the embedding), and a question that
  names a surface keeps it (`claude mu chatgpt mi kod yazar` ("does Claude or ChatGPT write code") →
  `coding`; `claude mu chatgpt mi tıbbi` ("Claude or ChatGPT, medical") → `expert`). **Failure
  scenario.** A reader with Apple Intelligence off asks `gemini pro mu chatgpt mi`. The question
  still lands on coding, under "matched on wording": the defect #206 was filed for. **Fix.** Accept
  a tier word when it follows a model name. Add the two `coding` probes to the test.

- **M7** `docs/plans/m20-plan.md:45`, `:98-112` and `:170-171`. **W4's own section does not carry the
  wiring it now owns.** The W3 amendment (`:91-93`) says W4's answer plan calls `familyBoards` and
  `Refinements.read`. But W4's §1 row lists REQ-CMB-005, REQ-APP-007 and REQ-APP-008, not REQ-CMB-004.
  None of W4's bullets mention the wiring, and §7 lists #211 under W3 only. W4 is MEDIUM ("screen
  code and its tests"), and `AnswerPlan.swift`, where the one reader goes, is not a security glob.
  **Failure scenario.** W4's reviewer checks W4 against W4's row and bullets, and the wiring is not
  in either. REQ-CMB-004 stays PARTIAL at closure. Or #211 is closed when W3's PR merges (the
  close-on-merge practice), though no question reaches its code. **Fix.** Add REQ-CMB-004 to W4's §1
  row. Add a W4 bullet: "the answer plan builds the family with `familyBoards`; where the outcome's
  tier is not the model's, it reads the refinements from the words (D-188 clause 6)". List #211
  under W4 as well, or say in W3's PR that it stays open. Consider adding `AnswerPlan.swift` to the
  security globs while it hosts the D-168 clause 4 amendment.

## Privacy (D-126, D-160, D-167 clause 1)

Holds. `grep -nE 'URL|EngineClient|client\.|fetch|Session|print\(|os_log|Logger'
ios/ModelRanking/Engine/Refinements.swift` finds nothing. The fix's `Router.swift` additions
(`comparisonParticles`, `comparesModelsOnly`, the shortcut in `route`) also contain none of those
words. `comparesModelsOnly` reads the question's words on the phone and returns a Bool. The outcome
it builds names a surface the engine served, with no refinements. `test_nothing_typed_by_the_reader_reaches_the_engine`
and the other router-hint gates pass (53 passed).

## What looks good

- The M1 to M3 negative tests quote every first-round probe, and each reads nothing.
- `familyBoards` is now the one loop: `boards(primary:…)` is a call to it, and AnswerPlan already
  reaches it through `boards` (`AnswerPlan.swift:130`). The no-family case keeps the primary.
- The Turkish whole-word lists (`doktor`, `doktorlar`, `doktoru`, `saglik`, the forms of `fizik`)
  keep `doktora` ("PhD"), `sağlıklı` ("healthy") and `fiziksel` ("physical") out.
- `comparesModelsOnly` cannot take a question that names a surface: `named == nil` comes first, and
  every word must be a model name, a particle or a single letter.

## Hardened-invariant producers

- **"A refinement is on a routing outcome only through `ModelOutputBoundary`":** one producer,
  `ModelOutputBoundary.outcome` (`Router.swift:839`). The new #206 outcome (`Router.swift:534-535`)
  carries none. Citing test:
  `test_only_the_model_output_boundary_builds_an_outcome_with_refinements`.
- **"Refinements from the words are read only by the answer plan" (D-188 clause 6):** no producer
  yet (`grep -rn 'Refinements\.read' ios/ModelRanking` finds only the declaration). Citing test:
  `test_only_the_answer_plan_reads_refinements_from_the_words`. Gap: M3, four spellings bypass it.
- **"The family keeps only what the surface allows, at most two, languages first":** one producer,
  `familyBoards` (`Refinements.swift:99-111`). Citing tests: `QuestionFamilyTests.swift:30-72`.

## Acceptance criteria evidence

- **REQ-CMB-004, "the surface brings its family; at most two refinements, language first":**
  `Refinements.swift:99-111`, tested at `QuestionFamilyTests.swift:17-72`. Held (the re-planted
  faults are caught). PARTIAL in the PRD, as the record now says (`prd.md:613`).
- **REQ-CMB-004, "with no model, the words choose the refinement, only words with one reading":**
  `Refinements.swift:130-209`, tested at `QuestionFamilyTests.swift:75-131`. Not yet reached by any
  question (W4). The words are not all one-reading words yet (M1, M4).
- **REQ-CMB-004, "nothing leaves the phone":** held (Privacy above).
- **#206:** `Router.swift:391-402,533-536`, tested at `KeywordRoutingTests.swift:233-245`. Delivered
  for bare names (M6).

## K.8 contract drift check

The fix changes no engine field and no shared type. `familyBoards` gains `primary:`; its one caller
is `boards(primary:…)`. `CategoryHints.readings` goes from private to internal. Evidence:

```
$ grep -rn 'familyBoards\|Refinements\.read\|comparesModelsOnly\|readings(' ios/ModelRanking src scripts | grep -v '///'
ios/ModelRanking/Engine/Refinements.swift:99:    static func familyBoards(primary: String, family: [String], surface: String, chosen: [Refinement]) -> [String] {
ios/ModelRanking/Engine/Refinements.swift:176:        let readings = CategoryHints.readings(question)
ios/ModelRanking/Engine/Refinements.swift:219:        familyBoards(primary: primary, family: [primary], surface: surface, chosen: chosen)
ios/ModelRanking/Engine/Router.swift:387:    static func readings(_ question: String) -> [[String]] {
ios/ModelRanking/Engine/Router.swift:398:    static func comparesModelsOnly(_ question: String) -> Bool {
ios/ModelRanking/Engine/Router.swift:399:        readings(question).contains { words in
ios/ModelRanking/Engine/Router.swift:407:        let readings = readings(question), raw = question.lowercased()
ios/ModelRanking/Engine/Router.swift:420:        known.contains(generalWords.id) && names(generalWords, readings(question), question.lowercased())
ios/ModelRanking/Engine/Router.swift:533:        if named == nil, CategoryHints.comparesModelsOnly(question) {
```

`RoutingOutcome` and `Refinement` are unchanged. Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- **K1** `ios/ModelRanking/Engine/Router.swift:515-525` (`readsEnglish`). **A short Turkish question
  with one word beyond names and particles still reaches the English embedding.** "claude mu chatgpt
  mi almanca" ("Claude or ChatGPT, German?") → `coding`. This is the class #206 was one case of, and
  the narrow fix (M6) does not reach it. It is an existing bug, not an enhancement. **Fix:** file an
  issue. Treat a question that holds a Turkish particle ("mi", "mu", "hangisi") or a Turkish letter
  as Turkish before the embedding, so D-187's Turkish path answers it.

## Risks queued to next M
- **R1** `docs/decisions.md:4466` and `ios/ModelRanking/Engine/AnswerPlan.swift:130`. **"Where the
  model read the question, its choice stands, none included" has no test yet.** W4 must tell "the
  model read it and chose none" from "the model did not read it". A `RoutingOutcome` with tier
  `.model` and no refinements must not get the words' refinements. **What would show it is real:** a
  W4 answer plan that reads the words whenever `outcome.refinements` is empty. A model-tier question
  the model gave no refinement ("investing in chinese stocks", M1) would then gain a board the model
  declined. **Fix:** a W4 test with a `.model` outcome, no refinements and a question that names a
  language, expecting the family alone.
