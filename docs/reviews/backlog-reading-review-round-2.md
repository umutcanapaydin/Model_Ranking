---
record_type: review
id: backlog-reading-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 2: the reading wave (#237, #222, D-196)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `origin/main..ac2387e` (3 commits: `f884bfe`, `be0b101`, `ac2387e`)
**Risk tier:** MEDIUM (routing behaviour of the wording tier; no security path)

## Verdict
MAJOR

The round-1 fixes are real for M1, N2, N3, N6 and K2: each is held by a test that fails on its mutant,
or by a run that reproduces. Two things need fixing in this wave:
- **The held-out leak gate never reads the app's `Router.swift` (M1).** It keys the files it scans by
  bare name, so a fixture of the same name replaces it. That is the file holding every example
  sentence, including the 84 Turkish ones this wave wrote. D-196 clause 4 leans on that gate.
- **The M2 fix reads more than letters (M2).** It counts an emoji's variation selector, a keycap and
  a decomposed accent as "a letter Turkish never writes". A Turkish question ending in a heart emoji
  falls back to "not measured", while the same question ending in a different emoji is answered.

The rest are records and test holes (N1 to N5).

How the review was done:
- **Reading.** I read the three commits' diff, round 1's record and its Dispositions, D-196
  (`docs/decisions.md:4981`), the research note section 1 to section 6 and the runs, `score.py`, `SimilarityRouter.route`,
  `readsTurkish`, `turkishLetters`, `withPlainSpellings`, `ExampleVectors`, `TurkishEmbeddingTests.swift`,
  the manifest, and the leak gate (`_unescaped`, `_forms`, `_held_out_leaks` and their caller).
- **Gates.** `make swift-test` in the seat: PASS, 623 tests, each named in the manifest, and SlowTierTests
  7 of 7. `make client-decls`: PASS, 21 files in 4 configurations. `pytest tests/unit/test_ios_client_contract.py
  tests/unit/test_router_hints.py tests/unit/test_client_decl_gate.py`: 221 passed.
- **Held-out reproduction (counts only).** I copied `ios/` to a scratch directory outside the seat and
  added `ReadingProbe.swift`. One `PROBE_TIER=wording` run gave right 91/147, searches right 62/89, not
  measured 0, and not-a-search caught 29/58. It is identical, row by row, to the committed
  `review-wording-1.json`. No held-out question was read or printed.
- **Own probe.** I wrote a probe test in the same scratch copy and ran 25 sentences of my own through it.
  For each it printed `readsTurkish`, `readsEnglish`, the recogniser's hypotheses, `namedSurface`,
  `generalSurface`, the wording-tier outcome, the final `TieredRouter(model: nil)` outcome, and the
  outcome with `everyday` not served.
- **Mutants.** I ran seven mutants of `Router.swift` in the copy against the whole Engine suite or
  `TurkishEmbeddingTests`, restored the file each time, and confirmed with `cmp` that it matched the
  seat's. In the copy, three tests fail for reasons of the environment, with or without a mutant: the
  copy has no `scripts/` and runs outside `scripts/offline.sb`. Those three are excluded below.

Turkish sentences below are my own, written without their letters (rule L1); each was run with its letters.

## Findings

### BLOCKING
- none

### MAJOR (fix in this wave)

- **M1** `tests/unit/test_ios_client_contract.py:198`: the held-out leak gate never reads
  `ios/ModelRanking/Engine/Router.swift`, or six other app files.
  - **Why.** `texts = {p.name: ...}` keys each source by its bare file name.
    `scripts/client_decl_fixtures/` holds files with the same names as the app's: `Router.swift`,
    `ContentView.swift`, `StandingsStore.swift`, `EngineClient.swift`, `Models.swift`, `Detail.swift`
    and `Combine.swift`. `scripts` is scanned after `ios`, so each fixture replaces the app file.
    - The gate's `Router.swift` is the 12-line fixture, not the 1443-line router.
    - The fixtures arrived in `22c3d1c` (2026-10-06), so the gate has been blind to these files since then.
  - **Measured.**
    - I used two lines that already sit in the router as stand-in "held" questions: an English example
      and a Turkish example.
    - The test's own construction returned `[]`.
    - Keyed by path, the same call found both, in `ios/ModelRanking/Engine/Router.swift` (lengths 44 and 46).
    - I re-ran the live `reading_heldout_m22` set keyed by path, counts only. It found no leak today.
  - **Failure scenario.** A later wave tunes `examplesTurkish` or `examples` with a held-out sentence of
    #237's set, or of the next fresh set. The gate stays green. The next held-out count is then a tuning
    count, which is the spoiling D-147 clause 5 and #66 describe.
  - **Why it is this wave's.** The wave rewrote `_held_out_leaks`, and D-196 clause 4 says what the gate
    finds. The file it cannot read is where this wave's 84 Turkish lines and their plain twins live.
  - **Second hole, small.** `_unescaped` matches `\N{...}` names in capitals only (`:257`). Python accepts
    `\N{latin small letter c with cedilla}`, so that form passes.
  - **Remedy.**
    - Key `texts` by path relative to the root.
    - Add a fail-closed check that the gate holds one text per scanned source (`len(texts) == len(sources)`).
    - Plant a stand-in question in a file whose name a fixture shares.
    - Make the `\N{}` match case-insensitive.

- **M2** `ios/ModelRanking/Engine/Router.swift:635-636` (`readsTurkish`): the M2 guard reads marks as
  letters, so an emoji or a decomposed accent puts a Turkish question out of the Turkish path.
  - **Why.** `CharacterSet.letters` is the categories L* and M*. Measured in the probe:
    `CharacterSet.letters.contains` is true for these, none of them in `turkishLetters`:
    - U+FE0F, the variation selector after a heart and most emoji;
    - U+20E3, the keycap;
    - U+0327, the cedilla of a decomposed letter.

    It is false for U+1F3FD (a skin tone), U+2019 and U+200D.
  - **Measured on my sentences.** All were `tr=1.00` to the recogniser. Each line below compares the same
    question with and without its addition:

    | sentence | without | with |
    |---|---|---|
    | `bana annem icin bir siir yaz` + U+2764 U+FE0F | `assistant` | manual, "not measured" |
    | the same + U+1F64F (no selector) | `assistant` | `assistant` |
    | `bu e-postayi daha kibar bir dille yeniden yaz` + U+270D U+FE0F | `agentic-coding` | manual, "not measured" |
    | `mide agrisi icin hangi ilaci almaliyim` + U+2764 U+FE0F | `assistant` | manual, "not measured" |
    | `mide agrisi icin hangi ilaci almaliyim` + U+1F914 | `assistant` | `assistant` |
    | `bana annem icin bir siir yaz`, NFD | `assistant` | manual, "not measured" |
    | `1` U+FE0F U+20E3 `numarali soruyu coz` | - | manual, "not measured" |

  - **What it contradicts.** D-196 clause 1 and the doc comment (`Router.swift:630-633`) say "a letter Turkish
    never writes". An emoji is not a letter. The outcome is the honest pre-wave decline, not a wrong
    board, so the failure is inconsistency, not a confident wrong answer.
  - **Failure scenario.** A reader on a phone without Apple Intelligence writes a Turkish request and ends it
    with a heart. They get "not measured". The same request without the heart, or with a different emoji,
    is answered. A pasted macOS string (NFD) is never Turkish.
  - **Not measured anywhere.** No set holds an emoji: 0 of the 147 held-out rows and 0 of the 80 tuning
    sentences have a character at or above U+2000.
  - **Remedy.**
    - Normalise to NFC first (`precomposedStringWithCanonicalMapping`).
    - Test only scalars whose general category is a letter (L*), not marks.
    - Pin it with a test: an invented Turkish search with a U+FE0F emoji, and its NFD form, each stays
      `readsTurkish`.

### MINOR (the author fixes each in this wave or files it as an issue)

- **N1** `Router.swift:664-665`, `docs/research/reading-wave-m22-probe.md:110-116`, `docs/decisions.md:5029`:
  round 1's N1 is held by neither a test nor a committed run (D-192).
  - **Mutant.** Using `examplesTurkish` and `unmeasuredHintsTurkish`, lettered only, survives the whole
    Engine suite (623 tests, no new failure).
  - **Missing runs.** The note's section 6 table and D-196 give 31/29, 45/37 and 44/39 on the wave's own 61
    searches, lettered and plain. The runs directory holds only `own-tuning_m22.json` and
    `own-short_m22.json`, both from the first head (10:28). It holds no plain-typed variant set, no run
    after the fixes, and `score.py` does not score them.
  - **Failure scenario.** A later edit drops the plain twins, for speed or by a merge. Nothing goes red, and
    the recorded 37-to-39 cannot be re-derived.
  - **Remedy.**
    - Commit the plain-typed variant of the wave's own sentences and the after-fix runs, and score them
      in `score.py`.
    - Or add one test where an invented plain-typed Turkish search reaches its surface only with both
      spellings.

- **N2** `ios/EngineTests/TurkishEmbeddingTests.swift:65`: M2's test holds the schwa only.
  - **Measured.** The Turkmen line `ma\u{0148}a bir hat \u{00FD}az` is read as Slovak (`sk=0.74`,
    `tr=0.08`), so it declines without the letter rule.
  - **Mutant.** A guard testing U+0259 alone survives the whole suite.
  - **A line that would hold it.** One of mine, `men\u{00E4} bir hat \u{00FD}azy\u{0148}`, is
    `tr=0.72` and is kept out only by the letter rule.
  - **Remedy.** Replace the Turkmen line with one the recogniser reads as Turkish, and assert that it does.

- **N3** `Router.swift:692-694`, `:703`, `:797-813` (`ExampleVectors`): "never anything typed" is held by
  nothing, and the key ignores the model.
  - **Typed text.** Mutant: `let query = example(text)` (the typed question through the cache) survives
    all 623 tests, and `make client-decls` cannot see it (in-memory state outside a sink). Each distinct
    question would then stay in a process-wide dictionary for the app's life.
  - **The key.** It is `language + "\n" + example`. Vectors from one embedding revision would be reused
    after another loads in the same process.
    - If the dimension differed, the centring loop (`mean[index] += v[index]`, `:719`) indexes past a
      kept vector and traps.
    - That is unlikely (an asset update mid-process), but the key costs nothing to widen.
  - **Thread safety and bound.** Both are fine. The lock is held only around dictionary access, and the
    worst case is the same example embedded twice. The keys are bounded by the example tables.
  - **Remedy.**
    - Add the embedding's `modelIdentifier` and `revision` to the key.
    - Pin "examples only" with a text pin that `example(` is applied only to `exampleSet` and
      `unmeasuredHints`, or with a count read through an internal accessor after a novel question.

- **N4** `docs/decisions.md:5002-5003`, `docs/research/reading-wave-m22-probe.md:51`, `:125-127`, #66:
  claims not held as written (D-192).
  - **"No question answered before the wave changes."**
    - The surface is unchanged. But a Turkish question that names a surface now passes the guard,
      reaches `if let named` (`Router.swift:763`) and carries two alternatives from the Turkish
      embedding. Before the wave it had none.
    - Measured: `python kodumu hizlandir` now offers `agentic-coding` and `computer-use` beside `coding`.
    - It is untested and unrecorded. It also costs an embedding run on every named Turkish question.
  - **"3 fewer searches are right" against the first head (section 6).**
    - By the committed runs (`after-wording-1` against `review-wording-1`), it is 4 lost and 1 gained.
    - One of the 4 now reads `mathematics`, not `everyday`, and was "not measured" before the wave, so
      M1's rule did not cause it. It is likely the plain twins (N1).
  - **#66's comment** says 9 lines moved from "not measured" to a ranking. After the fixes it is 10, as
    D-196 says.
  - **Section 3 (`:51`)** still states the brand-only rule, and "every other language" without the M2 caveat.
    Section 6 supersedes both, but section 3 is not marked.
  - **Remedy.**
    - Narrow the claim to "keeps its surface", and record the alternatives, or hold them with a test.
    - Correct section 6's attribution, and update #66's count.
    - Mark section 3 as superseded by section 6.

- **N5** `TurkishEmbeddingTests.swift:52`: M1's test omits the mixed sentence its disposition names.
  - The mixed line `en iyi model for writing cover letters` (`tr=0.76`) now gets `everyday`.
  - With `everyday` not served it goes to `coding`.
  - Neither outcome is in the test, though the Dispositions say "the three sentences here" are held.
  - **Remedy.** Add it to the loop.

### PASS (what looks good)
- **Numbers reproduce.** My held-out run is identical, row by row, to `review-wording-1.json`. `score.py`
  prints the note's tables. Against `before-wording-1`: 3 gained, 0 lost and 25 rows moved. 10
  not-a-search rows the reading misses moved from "not measured" to a ranking. Each of these matches D-196.
- **The English path is unchanged.** `readsTurkish` true still implies `readsEnglish` false, and the new
  guard can only turn `readsTurkish` off. That returns a question to the pre-wave decline, never to the
  English path.
- **M1 holds.** Disabling the `generalSurface` short-circuit fails 4 assertions in
  `testATurkishQuestionAboutModelsInGeneralKeepsEveryday`. By construction, a Turkish question
  `named ?? generalSurface` answered before keeps that surface.
- **N6 holds.** Returning `nil` when `everyday` is not served fails 8 assertions in the same test.
- **N3 (round 1) holds.** Using the English decline groups on the Turkish path fails
  `testATurkishRequestToChangeAnImageIsAnsweredFromVision`.
- **N7.** `requireTheEmbedding` fails rather than passes where the assets are missing. `make swift-test`
  runs only on the owner's machine (`.github/workflows/ci.yml:64`), so this cannot turn CI red.
- **K2.** The run took about 25 s for 147 rows on this Mac, and the rows are unchanged.
- **The leak gate's new decoding** passes on the real repo: no false positive, 221 passed. Each planted
  form is found.

## Round-1 dispositions, verified

| Finding | Disposition | Verified | Held by |
|---|---|---|---|
| M1 | Fixed | yes | `TurkishEmbeddingTests.swift:50`; mutant fails 4 assertions. The mixed sentence is not in it (N5) |
| M2 | Fixed | in part | `:64` holds the schwa only (N2); the guard reads marks as letters (M2) |
| N1 | Fixed and measured | no | No test (mutant survives); the plain-letter runs are not committed (N1) |
| N2 | Fixed | yes | `testTheModelsDeclineOnATurkishSearchGoesToTheTurkishPath`; note section 1 corrected |
| N3 | Fixed in part | yes | `testATurkishRequestToChangeAnImageIsAnsweredFromVision`; mutant fails |
| N4 | Fixed in part | in part | Forms planted and found; the gate does not read `Router.swift` at all (M1); lowercase `\N{}` passes |
| N5 | Fixed | yes, nearly | D-196 and note narrowed; #66 comment present, its count 9 is now 10 (N4) |
| N6 | Fixed | yes | Same test, `unserved` half; mutant fails 8 assertions |
| N7 | Fixed otherwise | yes | `requireTheEmbedding`; owner-machine leg only |
| K1 | Filed #271 | yes | #271 open |
| K2 | Fixed | yes | Rows identical, run faster; key and typed-text claim unheld (N3) |

## Acceptance criteria evidence
- **#222, a confident Turkish search reaches its surface.** `Router.swift:658-665` and
  `TurkishEmbeddingTests.swift:30-45`. Held-out searches not measured went from 8 to 0, reproduced.
- **#237, a fresh set is live and the old one retired.** `tests/unit/test_ios_client_contract.py:217-223`.
- **D-196 clause 1, "no question answered before changes".** Its surface is held
  (`TurkishEmbeddingTests.swift:50`), but its alternatives are not (N4).
- **D-196 clause 1, the letter rule.** Held for the schwa only (N2), and over-broad (M2).
- **D-196 clause 4, the leak gate.** The planted forms are held at `:292-315`, but the gate does not read
  `Router.swift` (M1).

## K.8 contract drift check
- No `/v1` field, schema or shared Swift type changed. `RoutingOutcome` is unchanged.
- `namesABrand` is removed, and nothing referenced it after the change: `make swift-test` builds and
  passes. `ExampleVectors` is new and internal. `make client-decls` PASS.
- Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- **K1** `tests/unit/test_ios_client_contract.py:192`: the leak gate scans `.swift` and `.py` under `ios`,
  `src`, `scripts` and `tests` only.
  - A held-out question quoted in `docs/` passes it: a review record, a research note or a decision.
    Those are the files the next tuner reads first.
  - Enhancement.
- **K2** `Router.swift:608-617` (`readsEnglish`): a non-English line the recogniser is unsure of takes the
  English path and gets a confident board.
  - Two Kurmanji lines of mine were read as `fr`/`nb` below 0.65. Both took the English path and went to
    `expert` with `unmeasured=false`.
  - This is older than the wave: the door `readsEnglish`'s comment describes, at low confidence.
  - Bug, for #66 or its own issue.

## Risks queued to next M
- **R1** The plain twins sit next to their lettered examples. So for a lettered question the "mean of the
  two closest" (`Router.swift:740`) often averages an example with its own twin, close to the
  single-closest rule D-147 measured as worse.
  - Net, on the wave's own set: 45 to 44 lettered, 37 to 39 plain.
  - The sign it is real: on a fresh set, lettered Turkish searches score below a lettered-only variant.
- **R2** `reading_heldout_m22` has now been run on the wording tier seven times, this review's run
  included. D-196's "Revisit when" already bars a fourth #218 attempt on it.
  - The sign it is real: a later wave cites its counts after tuning on its failures.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Fixed. The check keys what it reads by path (`_leak_scan_texts`), so the app's `Router.swift` and the fixture's are each read; `test_the_held_out_check_reads_each_same_named_file_on_its_own` holds it, and a mutant back to names fails it. A lowercase `\N{}` is decoded and planted. Read so, the live set shows no leak. | `test_ios_client_contract.py` |
| M2 | Fixed. The question is composed (NFC) and only letters by general category are tested, so marks change nothing. `testAMarkIsNotALetterTurkishNeverWrites` holds a heart emoji and a decomposed line. | `Router.swift` (`readsTurkish`, `isLetter`); D-196 clause 1 |
| N1 | Fixed both ways. `testATurkishQuestionTypedWithoutItsLettersReachesItsSurface` fails with lettered examples only (mutant checked), and the own-set runs are committed (`own-*.json`, `own_tuning_plain.json`) and scored by `score.py`: 31/29 before, 45/37 lettered examples, 44/39 both. | runs dir; `TurkishEmbeddingTests.swift` |
| N2 | Fixed. The Turkmen line is the one offered here, which the test asserts the recogniser reads as Turkish at or above 0.65; a schwa-only mutant fails it. | `TurkishEmbeddingTests.swift` |
| N3 | Fixed. The key carries the embedding's model identifier and revision; `ExampleVectors.keys` lets a test hold that only the router's examples are kept after a novel question, and the mutant that routes the question through the cache fails 13 assertions. | `Router.swift`; `TurkishEmbeddingTests.swift` |
| N4 | Fixed. D-196 says a named Turkish question keeps its surface and now offers two alternatives (held by a test); section 6 gives 4 lost and 1 gained against the first head; #66 carries a correction to 10; section 3 is marked superseded. | D-196; research note sections 3, 6, 7; #66 |
| N5 | Fixed. The mixed line is in the loop, served and with `everyday` withheld. | `TurkishEmbeddingTests.swift` |
| K1 | Filed as #272, with a measurement: scanning `docs/` found one held-out row in this wave's note (#218's own example, now removed) and three in a record that predates the set. | #272 |
| K2 | Filed as #273. | #273 |
| R1 | Accepted; the own-set runs show the trade (lettered 45 to 44, plain 37 to 39). | runs dir |
| R2 | Accepted. One more held-out run with the final code confirmed the counts; no change was made from it. | research note section 7 |
