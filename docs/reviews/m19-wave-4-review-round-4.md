---
record_type: review
id: m19-wave-4-review-round-4
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# Wave 4 Code Review (m19), round 4: reading the question, a second round

**Reviewer:** Code-Reviewer subagent, a new seat with fresh eyes. I wrote none of this wave's code,
tests or records, and I sat in none of its three earlier reviews.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `3426ff3..d324669` (the whole wave, 19 commits). The answer to round 3 is `b957ec0`
(red test) and `d324669` (the slice-out, #191).
**Risk tier:** HIGH (`docs/plans/m19-wave-4-plan.md:13-15`). What the on-device model's output decides
(D-126) is touched, and `ios/ModelRanking/Engine/Router.swift` is a security glob. By D-172 no security
seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I read the profile and `.agents/rules/practices.md` from `origin/main`, then the plans,
the code at `d324669`, the tests, the records and round 3's verdict. I read no other seat's scratch
files. Every probe line below is one I made up. A script checked them against the 150 held-out
questions: none is within a 0.7 similarity ratio (the closest is 0.64). No held-out question is quoted
here, and the held-out runs were scored by count only.

**Summary.**
- **The slice-out is complete in the code.** `TieredRouter.read` overrides only a question routed to
  `vision`, with the same condition as `3426ff3` (`Router.swift:711`). `asksForANewOrOwnImage` and its
  lists are gone. On 10 made-up questions routed to `web-dev`, `document`, `assistant`, `everyday` or
  `coding`, `d324669` gives the same outcome as `3426ff3`, row for row. The red test fails at `b957ec0`
  and passes at `d324669`. #191 holds the reach and lists the three attempts.
- **A few records still describe the reach** (M1), and two live records overstate what ships for #113
  (M2).
- **New BLOCKING finding (B1).** It is on `vision`, inside what stays. The wave added the Turkish verb
  `yap` ("make", "do") to the image rule's making verbs. The rule does not check that the image is the
  verb's object. So a Turkish request to READ an image becomes "make an image" when it says "in the
  photo" or "from the picture" before `yap`.
  - 26 of my 30 such requests, routed to `vision`, are now told "not measured" and kept in the gap
    register. At `3426ff3` the number is 0.
  - One of them is a plain model search: `hangi model fotoğraftaki soruyu yapabilir` ("which model can
    do the question in the photo").
  - No set measures this phrasing, so the read guard held while the class broke.
  - A narrow fix changes 0 rows in any committed model-tier run (measured below).
- The question-of-fact signal and the other reading signals are what D-184 says. Their tests kill 16
  of 19 mutants. The measure and its record reproduce exactly.

## Verdict

BLOCKING

## Round 3's findings, one by one

Round 3 is `docs/reviews/m19-wave-4-review-round-3.md`.

| Round 3 | Fixed or filed? | Evidence |
|---|---|---|
| **B1** the image rule's reach beyond `vision` | **Fixed in code; filed as #191.** The records are mostly corrected; M1 and M2 below list what is left. | `Router.swift:711` is `3426ff3`'s condition; `git diff 3426ff3 d324669 -- Router.swift` changes only comments and the fact doubt (`:718`). `git grep -E "asksForANewOrOwnImage\|namesASiteOrADocument"` finds nothing. `ReadingTests.swift:727` fails at `b957ec0` (10 assertions, the only failure among 50 Reading tests) and passes at `d324669`. #191 (`bug`, open) lists `de8c3f8`, `671b305` and `ec5159e` with each review's count. D-169's pointer (`decisions.md:3411`), D-184 clause 3 (`:4214-4222`), REQ-IMG-003 and REQ-RTR-005 (`prd.md:550`, `:468`), record §6, and the comments at `Router.swift:706-710` and `Reading.swift:215-220` now say the rule is on `vision` only. |
| **M1** the reviewed-word comment | **Fixed.** | `tests/unit/test_ios_client_contract.py:1587`: "measured, none of them changes a row of that set". |
| **M2** untested branches of the reach | **Moot for the reach**, since the function and the coding exemption are gone. **Partly open for what stays** (M3 below). | Of the Turkish forms that stay on `vision`, the mutants on K1's folding, `degistir` and `yap` are killed. The mutants on the `fotograf` stem and the Turkish modifier heads survive the whole suite. |
| **K1** possessive "'s" on `vision` | **Neither fixed nor filed.** | It still reproduces at `d324669`: `fix my photo's ocr errors`, routed to `vision`, is told "not measured" (the same at `3426ff3`). It is carried as K1 below. |
| **R1** fact signal without the model | Carried, now measured (R1 below). | |
| **R2** spent M19 sets still live | Carried (R2 below). | Record §7 says so (`m19-w4-question-reading-probe.md:211-212`). |
| **R3** no set measures the class | Carried. It now applies on `vision` too (B1, R3). | |

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `ios/ModelRanking/Engine/Reading.swift:269-277` (the Turkish branch of `makesAnImage`) and
  `:312-315` (`yap` in `imageStemsTurkish`); `docs/decisions.md:4214-4216` (D-184 clause 3);
  `docs/prd.md:550` (REQ-IMG-003).
  **On `vision`, a Turkish request to read an image that uses `yap` is now told "not measured".**
  - **What the rule does.** It fires when a form of `yap` has an image noun within the four words
    before it, and that noun is not followed by `galeri`, `yükleme`, `sayfa` or `bölüm`. It does not
    check the noun's case. In Turkish the case says what role the image plays:
    - `fotoğraftaki` ("the one in the photo") and `resimdeki` mark where something is;
    - `fotoğraftan` ("from the photo") marks the source;
    - `fotoğrafı` ("the photo", as the object) marks the thing being made or changed.
  - **Why `yap` matters.** It is the verb of most Turkish task phrases: `özetini yap` (summarise),
    `çevirisini yap` (translate), `listesini yap` (list), `analizini yap` (analyse), `soruyu yap` (do
    the question). So "do the question in the photo", "make a list from the picture" and "translate the
    menu in the photo" all read as making an image.
  - **D-184 clause 3 claims more than the code does.** It says "make" is read "after an image that is
    its object". The code does not check that.
  - **Probe.** I wrote 30 Turkish requests to read an image, each with a form of `yap`. I also wrote 8
    requests to make or change an image with `yap`. Each went through `TieredRouter` with
    `ScriptedModelRouter` naming `vision`, as the model did for 10 and 9 of the 10 held-out reading
    requests:

    | | `3426ff3` (ships today) | `d324669` | drop `yap` | narrow fix (below) |
    |---|---:|---:|---:|---:|
    | 30 requests to READ an image, told "not measured" | 0 | **26** | 0 | 3 |
    | 8 requests to MAKE or change one, told "not measured" | 0 | 6 | 0 | 5 |

    A sample of the 26, each routed to `vision`:
    ```
    hangi model fotoğraftaki soruyu yapabilir     bu fotoğraftaki soruyu yap
    fotoğraftaki tabloyu excel yap                resimdeki faturayı tablo yap
    fotoğraftaki menünün çevirisini yap           bu görseldeki grafiğin analizini yap
    resimdeki kodun açıklamasını yap              bu resimden bir alışveriş listesi yap
    fotoğraftaki ders notlarının özetini yap      resimdeki tabloyu excel yapabilir misin
    ```
    Each one keeps `search` as its reading, so it lands in the gap register as a need for an image
    generator. On the wording tier none of these lines gets an answer, so nothing changes there.
  - **Why the measure did not see it.** Requests to read an image reaching `vision` stayed 10 and 9 of
    10 on the held-out set and 21 and 21 of 26 on tuning, at every commit. Neither set has a reading
    request built on `yap`. Round 3's R3 named this gap for the reach beyond `vision`. It applies here
    too.
  - **What `yap` buys.** It carries the whole model-tier gain that is left for #113:
    - I replayed the committed runs through a scratch copy without `yap`. Requests to make an image
      told "not measured" fall from 4 and 3 to 2 and 1 of 20 on the held-out set (the baseline), and
      from 27 and 26 to 25 and 24 of 36 on tuning.
    - On the wording tier the rule adds nothing at `d324669`: 14 of 20 held out (baseline 14), 25 of 36
      tuning (`v0w` 25). All of these are the tier's own declines.
  - **Why it blocks.** It is the same harm as the class this wave has blocked on three times: a question
    that is no request to make an image is told "not measured" and recorded as a false need. Compared
    with the code that ships, the wave makes these questions worse (0 → 26 of 30). It does so on the
    class the plan's guard protects: requests to read an image reaching `vision`, at most one lost
    (`m19-wave-4-plan.md:88`). This is a new finding, not a fourth round on #191's class: it is on
    `vision`, in the Turkish forms that round 3 said should stay.
  - **Fix.**
    1. Red first: a test that routes made-up Turkish reading requests with `yap` to `vision` and
       expects `vision` to stay. Use a locative noun (`fotoğraftaki X'i Y yap`), an ablative noun
       (`resimden … yap`) and a search (`hangi model … yapabilir`). Keep
       `testARequestToMakeAnImageAsPeopleTypeItIsRead` green.
    2. Then do one of these two:
       - **(a)** For `yap` only, skip an image noun in the locative or ablative case (`-da/-de/-ta/-te`,
         with or without `-ki`; `-dan/-den/-tan/-ten`). I tried this in a scratch copy. It changed 0
         rows in all 8 committed model-tier runs (4 held out, 4 tuning), so it keeps 4 and 3 and 27 and
         26. Every Reading test passes. 3 of the 30 reading lines are still overridden: a relative
         clause (`fotoğrafını çektiğim …`) and the dative (`fotoğrafa bakıp …`). The dative cannot be
         skipped, because `fotoğraflarıma rötuş yap` is a make request.
       - **(b)** Drop `yap`. Then the wave adds nothing to #113 on the held-out set, and the records
         must say so.
    3. Correct D-184 clause 3 and REQ-IMG-003 to say what the rule then reads. If (b) is chosen, put
       the new figures in record §6.
    4. Do not apply a case rule to M18's verbs without a measure. The M18 test at
       `ReadingTests.swift:129` holds `fotoğrafımdaki kırmızı gözleri düzelt` as a make request. That
       older class is K2.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** Four places still describe the reach, which is gone from the code.
  - `docs/decisions.md:4184`: D-184's title says "the image rule reaches every surface but code". Its
    clause 3 (`:4214`) says the rule stays on `vision`.
  - `ios/EngineTests/ReadingTests.swift:317-320`: the comment on
    `testTheImageRuleNeverOverridesAnotherSurface` says "(M19-W4, when the rule left `vision`)". It also
    says a question about a website or a photo "is no request to make one". The test checks surfaces
    only; it never calls `makesAnImage`.
  - `ios/EngineTests/ReadingTests.swift:671-674`: the class comment says "beyond `vision`, only a new
    image or the asker's own is a request to make one". That describes the removed
    `asksForANewOrOwnImage`.
  - `docs/research/m19-w4-question-reading-probe.md:104-106` (§3): "so it now stops there" (the coding
    exemption) and "(c) took the image tuning set from 25 to 33". Both describe the reach, in the present
    tense. What ships gives 25.

  **Fix.** D-184 has not merged, so retitle it to match clause 3. Put back M18's comment at `:317` ("the
  image rule overrides only a question routed to `vision`"). Say at `:671` what the class now holds:
  questions about a site's or a file's image keep their surface. Put §3's two sentences in the past
  tense, pointing to §6.
- **M2** Two live records still claim a #113 result that no longer ships.
  - `docs/plans/m19-plan.md:237` says "#113's wording-tier bar was met". That was `de8c3f8`. What ships
    gives 14 of 20 on the wording tier, the baseline, and the amendment never says so.
  - Record §5 (`m19-w4-question-reading-probe.md:153-156`) says the same in the present tense. §6
    corrects it, but §5 does not point there.
  - `docs/prd.md:532` (REQ-ASK-005) gives `de8c3f8`'s held-out figures as the row's state: 25 and 27,
    6 and 6, asked 2 and 1. What ships gives 24 and 26, 5 and 5, asked 1 and 0 on the same (spent)
    sets. REQ-IMG-003 (`:550`) gives the shipping figures, so the two rows use different rules.

  **Fix.** In each place, name the code each figure comes from (`de8c3f8`) and add what ships on the
  spent sets.
- **M3** Branches that stay are held by no test, and no test cites D-184. I planted 25 mutants in a
  scratch copy and ran the 50 Reading tests on each; I ran each survivor again on the whole suite. 20
  are killed. 5 survive the whole suite:
  - `Reading.swift:274` and `:307`, **the Turkish modifier-head check** (round 1's MJ1 fix,
    `resim galerisi yap`). Its only tests route those lines to `web-dev` (`ReadingTests.swift:617-618`). The
    rule no longer acts there, so those tests pass whatever this check does.
  - `Reading.swift:329`, the `fotograf` stem. `fotografimin arka planini degistir` takes the
    `arka plan` branch, which needs no image noun.
  - `Reading.swift:171`, the fact exclusions read under the Turkish folding (only a capital `İ` makes a
    difference now). `Reading.swift:59`, the search words before a colon under every folding (same
    reason). `Reading.swift:192`, `["what", "s"]` ("what's" is not in any test).
  - The new test classes (`ReadingTests.swift:515`, `:603`, `:671`, `:720`) cite issues and REQ-IDs but
    not D-184 (practices, seed E.2).

  **Fix.** Add direct `makesAnImage` assertions for the first two (`resim galerisi yap` is not making;
  `fotografimi karikatur yap` is), one line each for the other three, and `D-184` in the class
  comments.
- **M4** `Reading.swift:340` with `:70-77`: **"make" as an act verb before a colon reads GNU make's
  error lines as pasted content.** This contradicts the function's own comment (`:44-45`): "an error
  line pasted into a question about code … is not pasted content".
  - Probe, routed to `coding`: `make: *** No rule to make target 'install'.  Stop.`,
    `make: *** [Makefile:12: all] Error 1`, and
    `make: g++: No such file or directory, which model can debug my build`.
  - Each is a doubt at `d324669`. It is asked about when the model says "a model search", and gets the
    note with no ranking when the model says "something else". At `3426ff3` each is a search.

  **Fix.** Do not count "make" when it is the only word before the colon, and add these lines as
  tests. The reach is low: a developer pasting a build error.

### PASS (what looks good)

- **The slice-out, behaviour first.** I routed 10 made-up questions beyond `vision`. On every field,
  on both tiers, `d324669` and `3426ff3` agree. Five of them:
  - `make me a logo for my bakery` on `web-dev`;
  - `bir kedi resmi çiz` on `assistant`;
  - `remove this picture from my word document` on `document`;
  - `fotoğraflarımı buluttan sil` on `everyday`;
  - `generate an icon set for my ios app` on `coding`.
- **Red, then green.** At `b957ec0` only `testTheImageRuleOverridesOnlyAQuestionRoutedToVision` fails
  (10 assertions); the other 49 Reading tests pass. At `d324669` the whole Swift suite passes: 483 tests,
  0 failures, 110 s. The discovered list equals `test-manifest.txt` (483).
- **The record's numbers are the code's.**
  - Replaying `final-*` and `v0-*` through `d324669` gives the 8 committed `review3-*` runs with 0 rows
    different.
  - Running the wording tier fresh, in a scratch harness with no on-device model, gives the 3
    `review3w-*` runs with 0 rows different.
  - `score_w4.py` gives record §6: 4 and 3, 14, 10 and 9, 0; tuning 27 and 26, and 25; reading 24 and
    26, 5 and 5, asked 1 and 0.
  - The baseline (§2) and the §4 figures reproduce from `base-*`, `basew-*` and `final-*`. The bars
    follow the plan's rules (1 + ⌈2/3 × 19⌉ = 14; 14 + ⌈2/3 × 6⌉ = 18; 28 − 2; 9 − 1).
- **The signals are well held.** Of 19 mutants on the reading signals, 16 are killed. These include
  the fact doubt in `TieredRouter.read`, the apostrophe rule, the exclusion stems, `ne zaman` and
  `hangi yıl`, the length bound, `eline sağlık`, both colon rules, `make`, `duzelt` and `cevir`,
  `kopyala`, and `pretend ur a`.
- **#177 is delivered.** The three M18 sets are in `RETIRED_HELD_OUT`
  (`test_ios_client_contract.py:210-214`), and the swap is one commit (`5fe0793`). The fresh sets have
  the plan's composition: 20 knowledge, 10 each of the other three not-a-search classes, 40 genuine, 10
  ambiguous; 20, 10 and 20 image rows; half in Turkish (counted, not read).
- **No drive-by edits.** `git diff 3426ff3..d324669 -- src/` is empty. The model's instructions and
  schema are untouched. There is no new import and no swallowed error. All 19 commits carry the owner's
  identity, and none carries AI attribution.
- **Gates.** `pytest tests/unit/test_ios_client_contract.py`: 49 passed. `scripts/check_records.py`:
  PASS, no findings.

## Producers of hardened invariant(s)

- **"A genuine search gets the note only when a code signal and the model's doubt agree, or the text has
  no word or is only small talk"** (D-169 clause 4 as amended; D-184 clause 1).
  - Producer: `inputReading` (`Reading.swift:415-422`). Its only feeder is `TieredRouter.read`
    (`Router.swift:715-719`), on every tier. The doubt is
    `pastedContent || instructsTheApp || asksAFact`.
  - Citing tests: `ReadingTests.swift::testTheDecisionTable` (`:165`), `::testNoGenuineTuningQuestionTripsASignal`
    (`:182`), `::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote` (`:587`),
    `::testASearchThatNamesTheAskerAnAIOrATaskIsNoQuestionOfFact` (`:634`),
    `::testASearchTypedWithAColonIsNoPastedContent` (`:663`), `::testAnApostropheSuffixIsNoAsker` (`:706`).
  - Gaps: M4 (GNU make's error lines), R1 (searches that name no model).
- **"Only a request to make an image that a tier routed to `vision` is overridden to unmeasured"** (D-169
  as amended at M18-W3; D-184 clause 3).
  - Producer: `TieredRouter.read` (`Router.swift:711`) with `InputSignals.makesAnImage`
    (`Reading.swift:227-281`).
  - Citing tests: `::testTheImageRuleOverridesOnlyAQuestionRoutedToVision` (`:727`),
    `::testTheImageRuleNeverOverridesAnotherSurface` (`:321`),
    `::testARequestToMakeAnImageRoutedToVisionIsUnmeasured` (`:305`),
    `::testARequestToMakeAnImageIsRead` (`:125`), `::testTheImageRuleReadsEachOfItsForms` (`:421`),
    `::testARequestToMakeAnImageAsPeopleTypeItIsRead` (`:577`),
    `::testAQuestionAboutAnImageInASiteOrAFileKeepsItsSurface` (`:684`).
  - Gaps: B1 (a reading request on `vision` built on `yap`), M3 (two surviving branches), K1, K2.

## Acceptance criteria evidence

The W4 criterion is `docs/plans/m19-plan.md:41`. The wave plan's phases are at
`docs/plans/m19-wave-4-plan.md:96-102`.
- **P1 #177:** `5fe0793`; `tests/unit/test_ios_client_contract.py:210-214`. The held-out gates pass.
- **P2:** the probe's wording mode is at `scripts/router_probe/ReadingProbe.swift:45-53`. The baseline
  and bars were committed at `a34453b` (record §2, `:30-65`), and I reproduced them.
- **P3 #66:** `Reading.swift:164-213` and `Router.swift:718`. Tests at `ReadingTests.swift:522`, `:587`,
  `:634` and `:706`. The held-out measure at `de8c3f8` is record §4: knowledge 6 and 6 of 20 against a
  bar of 14, not met; the bounds hold.
- **P4 #113:** `Router.swift:711` and `Reading.swift:227-281`. Tests at `ReadingTests.swift:577` and
  `:727`. The reach came out (#191). **What stays is not yet correct (B1).**
- **P5:** D-184 (`docs/decisions.md:4184-4246`); REQ-ASK-005, REQ-RTR-005 and REQ-IMG-003
  (`docs/prd.md:532`, `:468`, `:550`). D-184's title and clause 3 overstate the code (M1, B1).
  REQ-ASK-005 states `de8c3f8`'s figures (M2).
- REQ-ASK-005 → `Reading.swift:164` + `ReadingTests.swift:522`, `:634`, `:706` (classes at `:515`,
  `:603`, `:671` cite it).
- REQ-IMG-003 → `Router.swift:711` + `ReadingTests.swift:577`, `:684`, `:727` (classes at `:515`,
  `:603`, `:671`, `:720`).
- REQ-RTR-005 → `Router.swift:711` + `ReadingTests.swift:727` (class at `:720`).
- The criterion "read better than M18's measure, on a fresh held-out set, measured twice, against bars"
  holds in part. Both problems improved and every bar on them was missed, so the valve applies: the pull
  request asks the owner, as the plan amendment says.

## K.8 contract drift check

The wave plan's contracts (`docs/plans/m19-wave-4-plan.md:112-123`), `grep -n` at `d324669`:

```
ios/ModelRanking/Engine/Router.swift:70:    static let byID: [String: String] = [
ios/ModelRanking/Engine/Router.swift:449:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/ModelRanking/Engine/Router.swift:553:    static let requestGuidance = "A model search, or something else: instructions to you, small talk, "
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:227:    static func makesAnImage(_ text: String) -> Bool {
ios/ModelRanking/Engine/Reading.swift:415:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
tests/unit/test_ios_client_contract.py:210:RETIRED_HELD_OUT = {"heldout_questions.json", "refinement_heldout_questions.json",
scripts/router_probe/ReadingProbe.swift:27:    func testProbe() async throws {
```

- Names and signatures are as planned. Only line numbers moved.
- There is one new internal function, `InputSignals.asksAFact` (`Reading.swift:164`), with its lists.
  Its only caller is `Router.swift:718`.
- No `/v1` field or route changed, and there is no new closed field: the plan's P4 (b) was not built.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/Reading.swift:254-268` (since M18), round 3's K1, still unfiled.
  `wordsOf` splits "photo's" into `photo` and `s`, so the image noun counts as the verb's object. At
  `d324669` and at `3426ff3`, `fix my photo's ocr errors` routed to `vision` is told "not measured".
  This is a low-reach bug. **File it** (`/close-wave` step 6).
- **K2** `ios/ModelRanking/Engine/Reading.swift:269-277` (since M18). B1's case problem is older for
  M18's own verbs. `fotoğraftaki yazım hatalarını düzelt` ("fix the typos in the photo") routed to
  `vision` is told "not measured" at both commits. A case rule for every verb would break the M18 test
  that holds `fotoğrafımdaki kırmızı gözleri düzelt` as making. So it needs a measured set of its own.
  **File it**, beside #191.

## Risks queued to next M

- **R1** `ios/ModelRanking/Engine/Router.swift:718`. **Round 3's R1, now measured.** The fact signal
  asks about searches that name no model, AI or listed task.
  - I wrote 20 such genuine searches (`who is fastest at transcribing audio`, `matematikte kim önde`,
    `what is reliable for citing sources`). All 20 are asked about at `d324669`; at `3426ff3`, none.
  - This happens on the wording tier, and on the model tier whenever the model says "a model search".
  - D-184 clause 1 records that cost, and the independent set kept it inside the bound (1 and 0 of 40
    at what ships).
  - The sign that it is real: a stranger's first-use set (#91) where more than 4 of 40 genuine searches
    are asked.
- **R2** **The M19 held-out sets are spent but still registered as live** (record §7). Four rounds of
  replays have now run on them. The sign: a later wave citing a `*_heldout_m19_*` figure as a held-out
  result.
- **R3** **No set measures the phrasings the probes break.** It applies to #191's class beyond
  `vision`, and now to B1's on `vision`. The read guard stayed at 10 and 9 of 10 and 21 and 21 of 26
  while 26 of 30 probe lines flipped. The sign: a next attempt at #113 that passes its guards on a set
  without reading requests built on `yap`, or without questions about the asker's own site or slides.

## Gates and probes run

- **Red check:** `b957ec0` extracted to scratch (`ios/` and `scripts/router_probe/`).
  `swift test --filter Reading` ran 50 tests; only the new test failed (10 assertions).
- **Whole Swift suite** at `d324669` in a scratch copy: 483 tests, 0 failures. `swift test --list-tests`
  equals `test-manifest.txt`.
- `pytest tests/unit/test_ios_client_contract.py`: 49 passed. `scripts/check_records.py`: PASS.
- **Probes:** a scratch test file (not in the repository) at `3426ff3` and `d324669`, and in two scratch
  fix copies. It routed 75 made-up lines through `TieredRouter` three ways: with `ScriptedModelRouter`
  naming a surface, with the model's "something else", and through the real `SimilarityRouter`. It
  never loaded the on-device model.
- **Replays:** `ReplayProbe.swift` for the 8 model-tier runs. The wording tier ran fresh through
  `SimilarityRouter` in the scratch harness, not through `ReadingProbe`. The held-out runs were scored
  by count only, never with `--show`.
- **Mutants:** 25, in a scratch copy, each against the Reading tests; the 5 survivors were run again
  against the whole suite. Each file was restored from saved bytes in a `finally` and checked by sha256.
  Both files match the worktree's: `Reading.swift` bacb5e94…, `Router.swift` 259909ec….
- `make check-fast` was not run, since it depends on `make install` and this seat runs no installers.
  Its legs were run directly (above).
- No `ReadingProbe` and no on-device model call were run. No installer, `launchctl`, `simctl` or
  `xcodebuild` ran, and nothing opened an app or a browser. No `os.abort()` was used. The worktree is
  unchanged except for this file, and HEAD is still `d324669`.

*Filled by: Code-Reviewer seat (independent, round 4) · Date: 2026-10-07 · Commit range: `3426ff3..d324669`*
