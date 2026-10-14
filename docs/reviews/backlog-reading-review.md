---
record_type: review
id: backlog-reading-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 3: the reading wave (#237, #222, D-196)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `origin/main..b5a08bb` (4 commits: `f884bfe`, `be0b101`, `ac2387e`, `b5a08bb`)
**Risk tier:** MEDIUM (routing behaviour of the wording tier; no security path)

## Verdict
MINOR

Every round-2 disposition is real. Each code fix is held by a test that a mutant fails, or by a run I
reproduced row by row. `make check-fast` passes in the seat. Nothing the round-2 fixes changed opens a
confident wrong answer.

Four minor findings are left:
- **N1.** The letter rule still sends some confidently Turkish questions to "not measured": one carrying
  a Greek letter (pi, theta, delta) or an accented Latin letter (`e` with acute). Its own comment says
  each such letter has one reading. These letters do not.
- **N2.** The NFC step added for round 2's M2 is not held by any test. Removing it survives the whole
  suite, and then a decomposed Turkmen line is answered as Turkish.
- **N3.** The leak gate's own call site is not held. Reverting the gate's line to name-keying survives
  both tests. The new test checks the helper, not the gate.
- **N4.** Three claims in D-196, and one in the research note, say more than the runs do (D-192).

The wave can close once the author fixes or files each of the four.

How the review was done:
- **Reading.** I read:
  - the four commits' diff, round 2's record and its Dispositions, and D-196 (`docs/decisions.md:4981`);
  - the research note's sections 3, 6 and 7, `score.py` and the runs directory;
  - `readsTurkish`, `isLetter`, `turkishLetters`, `ExampleVectors` and `SimilarityRouter.route`;
  - `TurkishEmbeddingTests.swift`, the manifest, and the leak gate (`_leak_scan_sources`,
    `_leak_scan_texts`, `_unescaped`, `_forms`, `_held_out_leaks` and their callers).
- **Gates.** `make check-fast` in the seat passed in 138 s: lint, typecheck, records, swift-test
  (parallel, against the manifest), test and client-decls.
- **Own probe.** I copied `ios/` to a scratch directory outside the seat and added a probe test. It ran 26
  sentences of my own. For each it printed `readsTurkish`, `readsEnglish`, the recogniser's hypotheses,
  `namedSurface`, the `TieredRouter(model: nil)` outcome and the `SimilarityRouter` outcome.
- **Mutants.** I ran eight mutants of `Router.swift` in that copy, A to G below and the lettered-examples
  run, each against `TurkishEmbeddingTests` or the whole Engine suite. I also ran one mutant of the
  leak gate, in memory. After each, a byte compare showed the copy's `Router.swift` equal to the seat's.
  - In the copy, two tests fail with or without a mutant, for reasons of the environment (3 assertions):
    `OfflineGuardTests` (the copy runs outside `scripts/offline.sb`) and
    `ReadingTests/testNoGenuineTuningQuestionTripsASignal` (the copy has no `scripts/`).
- **Own-set runs, reproduced.** I ran `scripts/router_probe/ReadingProbe.swift` (`PROBE_TIER=wording`) at
  `b5a08bb`. It read the wave's own 61 Turkish searches, both lettered and plain, which are tuning
  sentences.
  - Shipped code: every row equals `own-both-spellings-letters.json` and `own-both-spellings-plain.json`
    (61 of 61 each).
  - With the lettered examples only: every row equals the `own-lettered-examples-*` runs.
- **Held-out discipline.** I did not run the held-out probe.
  - I ran the committed `score.py`.
  - I compared the committed run files by row index, printing counts and surfaces only.
  - I counted characters of the set by Unicode category, printing counts only.
  - No held-out question was printed or read. Every sentence below is my own.

Turkish sentences below are written without their letters (rule L1). Each was run with its letters.

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **N1** `ios/ModelRanking/Engine/Router.swift:636-646` (`readsTurkish`), `docs/decisions.md:5005-5008`:
  the letter rule sends a confidently Turkish question with a Greek or accented Latin letter back to
  "not measured".
  - **Why.** Round 2's fix narrowed the guard from letters-and-marks to letters by general category, so
    marks are now out. A letter outside `turkishLetters` still rejects the question, whatever its script.
    The comment at `:639` says "Each such letter has one reading", meaning Azerbaijani or Turkmen. A
    Greek letter in a formula, or `e` with acute in a name, has another reading.
  - **Measured.** Each sentence is `tr=1.00` to the recogniser. Each row compares the same question with
    the letter and without it:

    | sentence | with the letter | without it |
    |---|---|---|
    | U+03C0 `sayisinin ilk on basamagini hesapla` (vs `pi ...`) | manual, "not measured" | `mathematics` |
    | U+03B8 `acisinin sinusunu nasil bulurum` (vs `teta ...`) | manual, "not measured" | `factuality` |
    | U+0394 `x sifira giderken bu ifadenin limitini bul` (vs no delta) | manual, "not measured" | `abstract` |
    | U+03BB `0.5 iken poisson olasiligini bul` | manual, "not measured" | - |
    | `pok` U+00E9 `mon kartlarim icin bir fiyat listesi hazirla` (vs `pokemon`) | manual, "not measured" | `web-dev` |
    | `caf` U+00E9 ` menum icin kisa bir slogan yaz` (vs `cafe`) | manual, "not measured" | `web-dev` |

    - The increment sign U+2206 is a math symbol, not a letter. It stays Turkish (`abstract`).
    - Superscript two (U+00B2) is a number, and stays Turkish.
    - U+02BC, the modifier-letter apostrophe, rejects the question too: `python` U+02BC `da bir siralama
      fonksiyonu yaz` keeps `coding` by its name, but loses its two alternatives. The usual U+2019 does not.
  - **The held-out set.** 2 of its 147 rows carry such a letter. I counted categories only: both are
    lowercase letters. Round 1's and round 2's rules both reject them, so they do not move between runs.
  - **Failure scenario.** A student on a phone without Apple Intelligence pastes a Turkish limit question
    with a delta, or asks about a Pokemon card with the accent. They get "not measured". The same
    question spelled without the letter is answered. The English path has no letter guard: the same
    question in English, with the letter, is answered.
  - **Remedy.** Any one of these:
    - Test only Latin-script letters (U+00C0 to U+024F, U+1E00 to U+1EFF). This lets Greek through and
      still catches the schwa, `a` with diaeresis, `n` with caron and `y` with acute.
    - Name the letters the Turkic languages the recogniser misreads write and Turkish does not: the
      schwa, `a` with diaeresis, `n` with caron, `y` with acute and `z` with caron, measured on lines
      like the existing two. Pin a Greek-letter Turkish math question as `readsTurkish`.
    - Keep the rule and record the cost in D-196 clause 1 and in the comment at `:639`. Drop the claim
      that "each such letter has one reading".

- **N2** `Router.swift:644`, `ios/EngineTests/TurkishEmbeddingTests.swift:66-87`: the NFC step is held by
  no test.
  - **Mutant A.** `let composed = text` (no composition) survives the whole Engine suite. The only
    failures are the two environment tests above.
  - **Why the test does not catch it.** `testAMarkIsNotALetterTurkishNeverWrites` holds the decomposed
    form of a Turkish line. That line passes without NFC too: a decomposed Turkish letter is an ASCII
    base plus a mark, and `isLetter` already skips marks.
  - **What NFC actually does.** It keeps a decomposed Turkmen or Azerbaijani letter out. `a` + U+0308
    composes to `a` with diaeresis, which the guard rejects. Without NFC the guard sees only `a` and a
    mark.
  - **Measured under mutant A.** The NFD form of the test's own Turkmen line (`tr=0.72`) gives
    `readsTurkish` true. `TieredRouter` then routes it to `expert`, measured, with alternatives `coding`
    and `assistant`. With the shipped code it declines, as the composed line does.
  - **Failure scenario.** A later edit drops the composition as redundant, since the test still passes. A
    Turkmen question pasted from macOS (decomposed) then gets a confident Turkish-read board, which is
    the class round 1's M2 closed.
  - **Remedy.** Add the Turkmen line's NFD form (`decomposedStringWithCanonicalMapping`) to
    `testALetterTurkishNeverWritesIsNotTurkish`. Mutant A then fails it.

- **N3** `tests/unit/test_ios_client_contract.py:221` and `:188-196`: the gate's own read is not held.
  - **Mutant.** I replaced line 221, `texts = _leak_scan_texts(root, sources)`, with the old
    name-keyed dict. Both
    `test_the_held_out_check_reads_each_same_named_file_on_its_own` and
    `test_no_held_out_question_is_written_into_the_code_or_its_tests` pass. Run in memory, the seat
    untouched.
  - **Why.** The new test calls `_leak_scan_texts` and `_leak_scan_sources` itself. It proves the helper
    is right, not that the gate uses it.
  - **What the gate would lose.** Keyed by name, 15 of the scanned files are dropped today (not 7), and
    `Router.swift` resolves to `scripts/client_decl_fixtures/Router.swift`.
  - **Round 2's remedy, not done.** It asked for:
    - a fail-closed `len(texts) == len(sources)` inside the gate;
    - a stand-in question planted in a file whose name a fixture shares, found through the gate's path.

    Neither is in the gate.
  - **Failure scenario.** A refactor inlines the read again, as it was for weeks. Both tests stay green,
    and the gate goes blind to the app's router. That file holds this wave's Turkish examples.
  - **Remedy.** In the gate, assert `len(texts) == len(sources)` before scanning. That fails closed, and
    the mutant above then fails. Or move the scan into one function that both the gate and the test call.

- **N4** `docs/decisions.md:5006-5007`, `:5028-5029`, `:5041`, and
  `docs/research/reading-wave-m22-probe.md:101-102`: claims that say more than the runs (D-192).
  - **D-196 Measured (`:5028-5029`).** It says "the 3 it loses were answered `everyday` before the wave
    and are again". The committed runs (`after-wording-1` against `review-wording-1`) show 4 lost and 1
    gained.
    - Three of the lost were `everyday` before the wave and are again.
    - The fourth was "not measured" before the wave and is now `mathematics`.

    The note's section 6 (`:129-131`) was corrected for round 2's N4. D-196 still carries the old
    attribution.
  - **D-196 Revisit when (`:5041`).** It says "run six times". The wording tier has run the set at least
    eight times: the six committed runs, round 2's reproduction, and section 7's run with the final code.
    The model tier ran it twice more. Round 2's R2 counted seven, before section 7's run.
  - **D-196 clause 1 (`:5006-5007`).** It says "an emoji or a decomposed accent changes nothing". It
    does not change whether the question is read as Turkish. It can change the answer, because the emoji
    is embedded with the question.
    - Measured on my line `aksam yemegi icin kolay bir tarif oner`: plain, it gives `everyday`.
    - With U+2764 U+FE0F it gives `search`.
    - With U+1F35D, or with the chef sequence, it stays `everyday`.

    Remedy: "does not take the question out of the Turkish path".
  - **The note, section 6 (`:101-102`).** It still says "no question that was answered before changes".
    Round 2's N4 asked to narrow that to "keeps its surface". D-196 was narrowed, and the note's `:133`
    adds the alternatives, but `:102` itself was not.
  - **Remedy.** Correct the three D-196 sentences and the note's `:102`. Nothing else is needed: each
    number above comes from the committed runs or `score.py`.

### PASS (what looks good)
- **check-fast.** `make check-fast` passes at `b5a08bb` in the seat. Its swift-test leg checks the
  suite against the manifest, which names all 10 new `TurkishEmbeddingTests`.
- **Committed runs reproduce.**
  - `score.py` prints the note's tables exactly: 88, 94 and 91 right on the held-out runs, and 31/29,
    45/37 and 44/39 on the wave's own.
  - By row index, before against after the fixes: 3 gained, 0 lost and 25 rows moved. 10 not-a-search
    rows moved from "not measured" to a ranking.
  - `own_tuning_plain.json` is exactly the plain form of the tuning set's 61 searches, labels included.
- **Section 7's held-out claim holds by construction.** No held-out row is non-NFC. The two rows with a
  non-Turkish character carry letters, which round 1's guard and round 2's both reject. The new cache
  key changes no vector. So the 147 rows cannot move between `ac2387e` and `b5a08bb`.
- **The round-2 fixes break nothing seen.**
  - The English path is unchanged.
  - A decomposed Turkish question routes exactly as its composed form: `assistant` and `everyday` on my
    two lines, with the same alternatives.
  - An all-capitals Turkish line with a dotted capital I is still Turkish. Lowercasing leaves U+0307, a
    mark.
  - `ExampleVectors` holds only example keys, and its lock is held only around dictionary access.
- **Emoji.** A heart with its selector no longer sends a Turkish question to "not measured". Nor does a
  ZWJ sequence or a plain emoji.

## Round-2 dispositions, verified

| Finding | Disposition | Verified | Held by |
|---|---|---|---|
| M1 | Fixed | yes, the helper; not the call site | `test_the_held_out_check_reads_each_same_named_file_on_its_own` (`:188`) holds `_leak_scan_texts`. Reverting the gate's line 221 survives (N3). Lowercase `\N{}` is planted at `:331-332` and decoded. Check-fast green, so no leak today |
| M2 | Fixed | yes, the emoji; the NFC step no (N2) | Mutant C (`CharacterSet.letters` again) fails `testAMarkIsNotALetterTurkishNeverWrites`. Mutant A (no NFC) survives the whole suite. Greek and accented letters still decline (N1) |
| N1 | Fixed both ways | yes | Mutant F (lettered examples only) fails `testATurkishQuestionTypedWithoutItsLettersReachesItsSurface`. The own-set runs reproduce row for row, shipped and lettered-only, and `score.py` scores them |
| N2 | Fixed | yes | Mutant E (schwa only) fails 2 assertions in `testALetterTurkishNeverWritesIsNotTurkish`. The Turkmen line is `tr=0.72`, asserted at `:70-72` |
| N3 | Fixed | yes (examples only); the key, by reading only | Mutant D (`query = example(text)`) fails 13 assertions. Mutant B (key without model and revision) survives, as expected: no test claims it. Section 7 claims only the examples half is held, and that is accurate |
| N4 | Fixed | in part | Alternatives held: mutant-free assertion `alternatives.count == 2` at `:107`. Section 6 corrected and section 3 marked; #66's correction comment present. D-196 Measured and the note's `:102` not corrected (N4) |
| N5 | Fixed | yes | The mixed line is at `:53`. Mutant G (no `generalSurface` short-circuit) fails 5 assertions, one more than round 2's 4 |
| K1 | Filed #272 | yes | #272 open |
| K2 | Filed #273 | yes | #273 open |
| R1 | Accepted | yes | The own-set runs show 45 to 44 lettered and 37 to 39 plain, reproduced |
| R2 | Accepted | yes | The count in D-196 is stale (N4) |

## Acceptance criteria evidence
- **#222, a confident Turkish search reaches its surface.**
  - Code: `Router.swift:669-679`.
  - Test: `TurkishEmbeddingTests.swift:30-45`.
  - Held-out searches not measured go from 8 to 0 (`score.py`).
- **#237, the fresh set is live and the old one retired.** `tests/unit/test_ios_client_contract.py`
  `RETIRED_HELD_OUT` holds `wording_heldout_m20_questions.json`, and the gate passes in check-fast.
- **D-196 clause 1, the letter rule.**
  - Schwa and Turkmen: `TurkishEmbeddingTests.swift:66-79` (mutant E fails).
  - Marks: `:83-87` (mutant C fails).
  - NFC is unheld (N2), and the rule is over-broad for non-Latin letters (N1).
- **D-196 clause 1, answered questions keep their surface.** `TurkishEmbeddingTests.swift:50-61` (mutant G
  fails) and `:102-107`.
- **D-196 clause 4, the leak gate.** The planted forms are held at `test_ios_client_contract.py:314-340`.
  The path keying is held for the helper at `:188-196`, not at the gate's line 221 (N3).

## K.8 contract drift check
- No `/v1` field, schema or shared Swift type changed. `RoutingOutcome` is unchanged.
- `ExampleVectors` and its `keys` accessor are internal. `turkishLetters`, `confidentLanguage` and
  `readsTurkish` are internal statics, and `isLetter` is private. `make client-decls` passes in
  check-fast.
- Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- none

## Risks queued to next M
- **R1** An emoji is embedded with the question, so it can move the surface: a heart moved my Turkish
  line from `everyday` to `search`, while a food emoji did not.
  - This is likely true of the English path too (not measured here). No set holds an emoji, so no count
    shows it.
  - The sign it is real: a set with emoji-bearing questions scores below the same set without them.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| N1 | Fixed. The rule reads only the five letters Azerbaijani and Turkmen write and Turkish never does (`turkicNotTurkishLetters`), after composing; `testAMarkIsNotALetterTurkishNeverWrites` holds a Greek letter and an accented Latin one. The held-out set, run once with the final code, reads every row as before. | `Router.swift`; D-196 clause 1; research note section 8 |
| N2 | Fixed. The Turkmen line's decomposed form is in the letter test; without the composing step it is read as Turkish, so the test fails. | `TurkishEmbeddingTests.swift` |
| N3 | Fixed. The check itself asserts one text per file read; the mutant back to a name-keyed dict fails it. | `test_ios_client_contract.py` |
| N4 | Fixed. D-196 gives 4 lost and 1 gained against the first head, "at least eight" runs, and says an emoji can move a surface; the note says "keeps its surface". | D-196; research note sections 6 and 8 |
| R1 | Accepted, queued: no set holds emoji. | -- |
