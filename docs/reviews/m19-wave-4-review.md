---
record_type: review
id: m19-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# Wave 4 Code Review (m19), round 5: reading the question, a second round

**Reviewer:** Code-Reviewer subagent, a new seat with fresh eyes. I wrote none of this wave's code,
tests or records, and I sat in none of its four earlier reviews.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `3426ff3..3697d64` (the whole wave, 22 commits). Round 4's answer is `58da18c` (red
test) and `3697d64` (the fix).
**Risk tier:** HIGH (`docs/plans/m19-wave-4-plan.md:13-15`). What the on-device model's output decides
(D-126) is touched, and `ios/ModelRanking/Engine/Router.swift` is a security glob. By D-172 no security
seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I read the profile and `.agents/rules/practices.md` from `origin/main`, then the two
plans, the code at `3697d64`, the tests, the records and round 4's verdict. I read no other seat's
scratch files. Every probe line here is one I made up or a tuning row. A script checked my 63 probe
lines against the 150 held-out questions: none is within a 0.6 similarity ratio (the closest is 0.58).
No held-out question is quoted here, and held-out runs were scored by count only.

**Summary.**
- **Round 4's B1 is fixed.** `yap` is out of the image rule. None of my 12 made-up Turkish requests to
  read an image with `yap`, routed to `vision`, is told "not measured" (as at `3426ff3`). The red test
  fails at `58da18c` and passes at `3697d64`. The fix opened nothing new on `vision`.
- **The measure reproduces exactly.** Replaying the recorded model runs through `3697d64` gives the 8
  committed `review4-*` runs, with 0 rows different. Running the wording tier fresh gives the
  `review4w-*` runs, with 0 rows different.
- **The whole Swift suite passes:** 487 tests, 0 failures, and the list equals `test-manifest.txt`.
  21 of my 23 mutants on the wave's code are killed.
- **Three MINOR findings, none blocking:**
  - **M1** (new): a genuine search typed as "a task: which model" is now asked about, when the task
    uses one of the verbs the wave added ("make", `yap`, `duzelt`, `cevir`).
  - **M2**: small inaccuracies left in the records.
  - **M3**: the rest of round 4's M3 (two branches still held by no test).

## Verdict

MINOR

## Round 4's findings, one by one

Round 4 is `docs/reviews/m19-wave-4-review-round-4.md`.

| Round 4 | Fixed or filed? | Evidence | Did the fix open anything? |
|---|---|---|---|
| **B1** `yap` read Turkish requests to read an image on `vision` as making one | **Fixed** (round 4's option b: drop `yap`). | `Reading.swift:315-318` no longer holds `yap`. `ReadingTests.swift:757` (`58da18c`) fails at `58da18c`: 16 assertions, the only failure among 49 Reading tests. It passes at `3697d64`. My 12 made-up reading lines (e.g. `resimden ocr yap`, `görseldeki grafiğin yorumunu yap`, `hangi yapay zeka fotoğraftaki ödevi yapabilir`) keep `vision` with `unmeasured = false`, as at `3426ff3`. Putting `yap` back (mutant w) is killed by that test. D-184 clause 3 (`decisions.md:4214-4218`), REQ-IMG-003 (`prd.md:550`) and record §6 now say what ships. | **Nothing new on `vision`.** The cost is stated: requests to make an image built on `yap` (`fotoğrafımı anime yap`) are ranked as measured again, as at `3426ff3`. Held out, what ships gives 2 and 1 of 20, the baseline. Two small record slips came with it (M2: a, b). The fix's new test pins a locative edit as making, which #192's proposed change would break (K1). |
| **M1** the reach still described in four places | **Mostly fixed.** | D-184's title (`decisions.md:4184`); `ReadingTests.swift:317-319` and `:672-675`. Record §3 got a pointer to §6, but `:106` still says the coding exemption "now stops there", in the present tense. | No. What is left is M2 (c). |
| **M2** live records claiming a #113 result that no longer ships | **Fixed.** | `m19-plan.md:237` names `de8c3f8`; record §5 (`:154-156`) points to §6; REQ-ASK-005 (`prd.md:532`) gives what ships (24 and 26, 5 and 5, asked 1 and 0). I scored `review4-*` and got these figures. | One slip in the new §6/§7 text: M2 (a). |
| **M3** untested branches of what stays | **Partly fixed.** 3 of 5 now held. Four classes cite D-184 (`ReadingTests.swift:514`, `:672`, `:753`, `:773`), but two that round 4 named still do not (`:604`, `:721`). | Mutants on the Turkish modifier heads (f), the `fotograf` stem (g) and `what's` (h) are killed by `ReadingTests.swift:777` and `:789`. The two folding branches still survive the whole suite (M3 below). | No. |
| **M4** GNU make's error line read as pasted content | **Fixed.** | `Reading.swift:74`; `ReadingTests.swift:794-797`. Mutant e is killed. `make[1]: *** [Makefile:30: build] Error 2` is a search, as at `3426ff3`. The test landed with the fix, not red first; mutant e shows it fails on the code without the fix. | No. The class around it (other verbs before a colon) is M1. |
| **K1** possessive "'s" on `vision` | **Filed:** #192 (open, `bug`, `severity:low`). | | K1 |
| **K2** M18's verbs with a locative or ablative image noun | **Filed:** #192, the same issue. | Still reproduces, as filed: `fotoğraftaki tablodan excel dosyası oluştur` on `vision` is told "not measured" at both commits. | K1 |
| **R1–R3** | Carried (below). | | |

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/Engine/Reading.swift:64-69` (the "question for a model after the colon"
  exemption), with the act verbs the wave added at `:343` (`make`) and `:347` (`duzelt`, `yap`,
  `cevir`). **A genuine search typed as "a task: which model" is asked about, and with the model's
  doubt it gets the note and no ranking.**
  - **How it happens.**
    - `pastedContent` reads "verb + colon + content" as a task with its content. That is a doubt.
    - The wave added four verbs to that list.
    - It also added one way out: the text after the colon opens with "which", `hangi` or `hangisi` and
      names a model. That rule reads only the first word.
    - Turkish puts the question word last. The code's own comment says so (`:199-201`: "X for which
      one" is how a Turkish reader asks for a model). English often opens with "best" or "what".
  - **Probe.** Each line was routed to `coding`, with the model saying "a model search":

    | made-up line | `3426ff3` | `3697d64` |
    |---|---|---|
    | `bir mobil oyun yap: en iyi model hangisi` | search | asked |
    | `make a flutter app: best model for it?` | search | asked |
    | `make a chrome extension: what model writes the cleanest js` | search | asked |
    | `make a 2d platformer in godot: which tool is best` | search | asked |
    | `kodumu duzelt: en iyi model hangisi` | search | asked |
    | `make a chrome extension: what model writes the cleanest js`, model says "something else" | asked | **the note, no ranking** |

    The same lines on the wording tier are asked at `3697d64` and are searches at `3426ff3`.
  - **Reach.** It is low and inside the plan's bound. Held out, what ships asks 1 and 0 of 40 genuine
    searches, against at most 4. The form is older for M18's verbs: the fifth line spelled with
    its Turkish letters was already asked at `3426ff3`.
  - **Fix.**
    - Red first: a test with the first, second and fifth lines above.
    - Then let the exemption accept `hangi` or `hangisi` anywhere after the colon, and "best" as its
      first word, when a model, AI or LLM is named there. I tried exactly that in a scratch copy:
      - all 52 Reading tests pass, including `testContentAfterAColonMayAskOrNameAI`
        (`ReadingTests.swift:713`);
      - it changes 0 rows in the 8 committed model-tier runs;
      - those three lines become searches again. The "what model" and "which tool" lines stay doubts.
- **M2** **Records still say a few things the code or the runs do not.**
  - **(a)** `docs/research/m19-w4-question-reading-probe.md:209-210` and `:214-216` say the image tuning
    set gives "25 and 24 of 36 (model) … the baseline", and that the Turkish forms "move no measured
    count". The baseline is 24 and 23 (record §3, `:98`; `v0-image_tuning_w4-1/2`). What ships
    catches one more tuning row per run.
  - **(b)** Record §6, `:195`, names `review3-*` beside a table whose "code that ships" column (`:199`)
    now holds `review4-*`'s 2 and 1. `review3-*` gives 4 and 3.
  - **(c)** Record §3, `:106`: "so it now stops there" describes the coding exemption, which is gone.
  - **(d)** D-184 "The cost" (`docs/decisions.md:4242-4244`): "on the held-out set, 2 and 1 of 40, from
    0" are `de8c3f8`'s figures, not labelled as such. What ships asks 1 and 0.
  - **(e)** D-184 clause 3 (`decisions.md:4216-4218`) says `yap` "came out", but does not say it is
    still a pasted-content verb (`Reading.swift:347`, clause 2). A reader can take it as gone entirely.
  - **(f)** Two comments in the code:
    - `Reading.swift:272-273` says "The image must be the verb's object". That is the claim round 4's B1
      took out of D-184; the code checks only the modifier heads. Its example `resim galerisi yap` uses
      a verb the rule no longer reads.
    - `ReadingTests.swift:515` says every line of its class is a tuning row, but
      `fotografimdaki lekeleri sil` (`:581`) is in no tuning set.

  **Fix.** Correct each sentence in place:
  - (a) say "the baseline held out; one tuning row more";
  - (b) name `review4-*` beside the table;
  - (c) use the past tense;
  - (d) label `de8c3f8` and add what ships;
  - (e) add "from the image rule";
  - (f) say "an image before a gallery, upload, page or section word is a modifier", use
    `resim galerisi oluştur`, and move or relabel the line.
- **M3** `ios/ModelRanking/Engine/Reading.swift:174` and `:59`. **Two branches of round 4's M3 are still
  held by no test.** Each mutant below survives the whole suite (487 tests):
  - **(a)** the fact exclusions read only under the default folding;
  - **(c)** the colon's search words read only under the default folding.

  Neither is equivalent to the code. A Turkish search in capitals with a dotted capital `İ` tells them
  apart. I ran `MATEMATİKTE EN İYİ KİM` ("who is best at maths") under mutant (a) in a scratch copy:
  it is asked about on both tiers, because the default folding turns `İYİ` into `i̇yi̇` and the
  exclusion `iyi` is missed. At `3697d64` it is a search. The reach is small.

  Also, two of the four classes round 4 named still cite no D-184 (practices, seed E.2):
  `ReadingSecondRoundReviewTests` (`ReadingTests.swift:604`) and `ReadingImageRuleOnVisionOnlyTests`
  (`:721`).

  **Fix.** Add the two assertions round 4 asked for, e.g.
  `XCTAssertFalse(InputSignals.asksAFact("MATEMATİKTE EN İYİ KİM"))`, and one colon line whose search
  word only the Turkish folding finds. Or file it. Add `D-184` to the two class comments.

### PASS (what looks good)

- **B1's fix is the narrow, measured option.** It changes nothing beyond `vision`. Each of these gives
  the same outcome at `3697d64` as at `3426ff3`:
  - the 12 made-up reading lines with `yap` (kept on `vision`);
  - the 4 made-up make-lines with `yap` (ranked as measured);
  - the 5 made-up lines with M18's verbs (#192's class, told "not measured" at both). The exception is
    `fotograftaki yazilari sil`, an edit the new `fotograf` stem now reads.
- **The K1 folding fix works where it should.** `TURN THIS PHOTO INTO TEXT` on `vision` is told "not
  measured" at `3426ff3` and keeps `vision` at `3697d64`.
- **The record's numbers are the code's.**
  - `ReplayProbe` through `3697d64`, over `final-*` and `v0-*`, gives `review4-*` (8 runs, 0 rows
    different).
  - A fresh wording-tier run (a scratch copy of `ReadingProbe`'s wording branch, never `ReadingProbe`
    itself) gives `review4w-*` (2 runs, 0 rows different) and 25 of 36 on the image tuning set.
  - `score_w4.py` gives record §6 held out: 2 and 1, 14, 10 and 9, 0; reading 24 and 26, 5 and 5,
    asked 1 and 0.
- **The held-out-only words are as reviewed.** `HELD_OUT_ONLY_REVIEWED`
  (`tests/unit/test_ios_client_contract.py:1589-1613`) says the five words added after the measure
  (`galeri`, `yükleme`, `chatbot`, `deepseek`, `gemini`) change no row of their set. I removed all
  five in a scratch copy and replayed the 4 held-out model runs and 2 wording runs: 0 rows different.
- **The signals are well held.** 21 of 23 mutants are killed. They cover the fact doubt in
  `TieredRouter.read`, the apostrophe rule, `kaç`, the length bound, `eline sağlık`, the `vs` and
  `which` colon rules, the `make` exemption, each act verb the wave added, `kopyala`, `degistir`, the
  dotless-i mapping and the Turkish modifier heads.
- **The ADR discipline holds.** D-169 is not edited; it only gains an "Amended by D-184" pointer
  (`decisions.md:3411`). D-184 carries the decision, the measure, the cost and a revisit trigger.
- **No drive-by edits.** `git diff 3426ff3..3697d64 -- src/` is empty. The model's instructions and
  schema are untouched. There is no new import and no swallowed error.
- **Commit hygiene.** All 22 commits carry the owner's identity, none carries AI attribution, and none
  uses a closing keyword: #66 and #113 stay open, as the valve says.

## Producers of hardened invariant(s)

- **"A genuine search gets the note only when a doubt in code and the model's 'something else'
  agree, or the text has no word or is only small talk"** (D-169 clause 4 as amended; D-184 clause 1).
  - Producer: `inputReading` (`Reading.swift:418-425`). Its only feeder is `TieredRouter.read`
    (`Router.swift:715-719`), on every tier. The doubt is `pastedContent || instructsTheApp ||
    asksAFact`.
  - Citing tests (all in `ReadingTests.swift`): `::testTheDecisionTable` (`:165`),
    `::testNoGenuineTuningQuestionTripsASignal` (`:182`),
    `::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote` (`:588`),
    `::testASearchThatNamesTheAskerAnAIOrATaskIsNoQuestionOfFact` (`:635`),
    `::testASearchTypedWithAColonIsNoPastedContent` (`:664`), `::testAMakeErrorLineIsNoPastedContent`
    (`:794`).
  - Gaps: M1 (a colon-form search in Turkish word order), M3 (a capital `İ`), R1 (searches naming no
    listed model).
- **"Only a request to make an image that a tier routed to `vision` is overridden to unmeasured"**
  (D-169 as amended at M18-W3; D-184 clause 3).
  - Producer: `TieredRouter.read` (`Router.swift:711`) with `InputSignals.makesAnImage`
    (`Reading.swift:230-284`).
  - Citing tests: `::testTheImageRuleOverridesOnlyAQuestionRoutedToVision` (`:728`),
    `::testTheImageRuleNeverOverridesAnotherSurface` (`:320`),
    `::testARequestToMakeAnImageRoutedToVisionIsUnmeasured` (`:305`),
    `::testATurkishRequestToReadAnImageWithYapKeepsVision` (`:757`),
    `::testTheTurkishImageFormsThatStayOnVision` (`:777`),
    `::testAQuestionAboutAnImageInASiteOrAFileKeepsItsSurface` (`:685`).
  - Gaps: #192 (the possessive and M18's verbs with a case-marked image), K1.
- **"No held-out question is in code, a test or a tuning set; every word only a live held-out set
  holds is reviewed"** (D-147 clause 5; #117).
  - Producer: the held-out gates over `RETIRED_HELD_OUT` and `HELD_OUT_ONLY_REVIEWED`
    (`test_ios_client_contract.py:210-214`, `:1590`).
  - Citing tests: `::test_no_held_out_question_is_written_into_the_code_or_its_tests` (`:175`),
    `::test_a_held_out_question_copied_into_a_tuning_set_is_found` (`:244`),
    `::test_every_signal_word_only_a_live_held_out_set_holds_is_reviewed` (`:1573`).
  - Gaps: R2.

## Acceptance criteria evidence

The W4 criterion is `docs/plans/m19-plan.md:41`; the wave plan's phases are at
`docs/plans/m19-wave-4-plan.md:96-102`.

- **P1 #177:** `5fe0793`; `tests/unit/test_ios_client_contract.py:210-214`. The held-out gates pass
  (`pytest tests/unit/test_ios_client_contract.py`: 49 passed).
- **P2:** the probe's wording mode is at `scripts/router_probe/ReadingProbe.swift:29`, `:45-53`. The
  baseline and bars were committed at `a34453b` (record §2, `:30-65`). The bars follow the plan's rules:
  - 1 + ⌈2/3 × 19⌉ = 14;
  - 14 + ⌈2/3 × 6⌉ = 18;
  - 28 − 2 = 26;
  - 9 − 1 = 8.
- **P3 #66:** `Reading.swift:167-216` and `Router.swift:718`. Tests at `ReadingTests.swift:521`, `:588`,
  `:635`, `:707` and `:789`. The held-out measure at `de8c3f8` is record §4: knowledge 6 and 6 of 20,
  against a bar of 14, not met. What ships gives 5 and 5 (from 1 and 3).
- **P4 #113:** `Router.swift:711` and `Reading.swift:230-284`. Tests at `ReadingTests.swift:576`, `:728`,
  `:757` and `:777`. The reach came out (#191) and `yap` came out (round 4's B1). What ships is the
  baseline held out: 2 and 1 with the model, 14 without it.
- **P5:** D-184 (`docs/decisions.md:4184-4247`); REQ-RTR-005, REQ-ASK-005 and REQ-IMG-003
  (`docs/prd.md:468`, `:532`, `:550`). Their figures are the shipping code's, except M2's slips.
- **REQ-ASK-005** → `Reading.swift:167` + `ReadingTests.swift:521`, `:588`, `:635`, `:707` (classes at
  `:514`, `:604`, `:672` cite it).
- **REQ-IMG-003** → `Router.swift:711` + `ReadingTests.swift:576`, `:685`, `:728`, `:757` (classes at
  `:514`, `:672`, `:721`, `:753` cite it).
- **REQ-RTR-005** → `Router.swift:711` + `ReadingTests.swift:728` (class at `:721`).
- **"Read better than M18's measure, on a fresh held-out set, measured twice, against bars"** holds in
  part. #66 improves and misses its bar; #113 is back at the baseline; D-169 clause 6's catch bar is
  missed. So the valve applies: the pull request asks the owner (`m19-plan.md:234-243`).

## K.8 contract drift check

The wave plan's contracts (`docs/plans/m19-wave-4-plan.md:112-123`), `grep -n` at `3697d64`:

```
ios/ModelRanking/Engine/Router.swift:70:    static let byID: [String: String] = [
ios/ModelRanking/Engine/Router.swift:449:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/ModelRanking/Engine/Router.swift:553:    static let requestGuidance = "A model search, or something else: instructions to you, small talk, "
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:230:    static func makesAnImage(_ text: String) -> Bool {
ios/ModelRanking/Engine/Reading.swift:418:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
tests/unit/test_ios_client_contract.py:210:RETIRED_HELD_OUT = {"heldout_questions.json", "refinement_heldout_questions.json",
scripts/router_probe/ReadingProbe.swift:27:    func testProbe() async throws {
```

- Names and signatures are as planned; only line numbers moved.
- There is one new internal function, `InputSignals.asksAFact` (`Reading.swift:167`). Its only caller is
  `Router.swift:718`.
- No `/v1` field or route changed, and there is no new closed field in the model's schema (P4's
  variant b was not built).
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** #192 (round 4's K1 and K2). **The issue's proposed change conflicts with two tests, and it does
  not say so.**
  - #192 proposes that the rule skip an image noun in a locative case "for the editing verbs".
  - Two tests hold a locative edit on the asker's own photo as making:
    - `ReadingTests.swift:129` (M18): `fotoğrafımdaki kırmızı gözleri düzelt`;
    - this wave's new `:581` and `:779`: `fotografimdaki lekeleri sil`.
  - Whoever takes #192 will meet red tests the issue never mentions.
  - **Fix:** add a comment on #192 that names both tests. Note the line they suggest: the asker's own
    photo plus the locative (`fotoğrafımdaki`, "in my photo") is usually an edit, while a bare
    locative (`fotoğraftaki`, "in the photo") is usually a reading.

## Risks queued to next M

- **R1** `ios/ModelRanking/Engine/Reading.swift:206-213` (carried from rounds 3 and 4).
  - **What happens.** The fact doubt asks about genuine searches that name no listed model. The list
    names eleven brands. Any other model name passes, such as qwen, kimi, phi, o3, mixtral or whisper.
  - **Probe.** I wrote 7 searches that name only such a model. All 7 are asked about at `3697d64`, and
    none at `3426ff3`. Examples: `what is cheaper, qwen or kimi`, `how much does o3 cost per million tokens`,
    `qwen ile kimi arasında kim önde`.
  - **Status.** D-184 clause 1 states this cost, and the fresh set kept it inside the bound.
  - **Possible remedy.** A list of model families taken from the engine's registry would cover the
    names the app itself ranks.
  - **The sign it is real:** a stranger's first-use set (#91) where more than 4 of 40 genuine searches
    are asked.
- **R2** **The M19 held-out sets are spent but still registered as live** (record §7). Five review
  rounds of replays have now run on them. The sign: a later wave citing a `*_heldout_m19_*` figure as a
  held-out result.
- **R3** **No set measures the phrasings the probes break.**
  - It applies to the image rule's case-marked nouns (#192), and now to M1's colon form.
  - The read guard stayed at 10 and 9 of 10 at every commit, and the genuine-asked bound held, while
    each probe class flipped.
  - The sign: a next attempt at #66 or #113 that passes its guards on a set with no such phrasing.

## Gates and probes run

- **Red check:** `58da18c` extracted to scratch. `swift test --filter Reading`: 49 tests, only
  `testATurkishRequestToReadAnImageWithYapKeepsVision` fails (16 assertions).
- **Whole Swift suite** at `3697d64` in a scratch copy: 487 tests, 0 failures, 61 s.
  `swift test list` equals `test-manifest.txt` (487).
- **Python gates:**
  - `pytest --no-cov` over `test_ios_client_contract.py`, `test_router_hints.py`,
    `test_swift_tests_offline.py`, `test_ios_platform_drift.py` and `test_client_decl_gate.py`: 157
    passed.
  - Over `test_language_of_shipped_strings.py`, `test_swift_test_manifest.py`,
    `test_ios_payload_contract.py`, `test_ios_visual_contract.py` and `test_swift_xunit_gate.py`: 26
    passed.
  - `scripts/check_records.py`: PASS, no findings.
- **Probes:** a scratch test file (not in the repository) at `3426ff3` and `3697d64`. It routed 63
  made-up lines through `TieredRouter`, with `ScriptedModelRouter` naming a surface and a verdict and
  with no model at all, and recorded every signal.
- **Replays and wording runs:**
  - `ReplayProbe.swift` for the 8 model-tier runs.
  - The wording tier ran fresh through `SimilarityRouter` in a scratch harness, never through
    `ReadingProbe`.
  - Held-out runs were scored by count only, never with `--show`.
- **Mutants:** 23, in a scratch copy with `scripts/router_probe/` beside `ios/`, against the Reading
  tests. The 2 survivors were run again against the whole suite. Each file was restored from saved
  bytes in a `finally` and checked by sha256: `Reading.swift` ed044176…, `Router.swift` 259909ec…, as in
  the worktree.
- **M1's candidate fix:** tried in a separate scratch copy. 52 Reading tests passed, and the 8 replays
  showed 0 rows different.
- **Not run:**
  - `make check-fast`, since it depends on `make install`, and this seat runs no installers. Its legs
    were run directly, above.
  - No `ReadingProbe` and no on-device model call. No installer, `launchctl`, `simctl` or
    `xcodebuild` ran, and nothing opened an app or a browser. No `os.abort()` was used.
- The worktree is unchanged except for this file, and HEAD is still `3697d64`.

*Filled by: Code-Reviewer seat (independent, round 5) · Date: 2026-10-07 · Commit range: `3426ff3..3697d64`*
