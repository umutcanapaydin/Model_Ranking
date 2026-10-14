---
record_type: review
id: backlog-reading-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Tester review: the reading wave (#222, #237, #194, #238; D-196)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `origin/main..387b70e` (5 commits, `f884bfe` to `387b70e`), branch `wave/backlog-reading`. The
seat is a worktree detached at `387b70e` with its own `.venv`. Faults were planted only in scratch copies outside
the seat (`ios/` twice, and the repository without `.git` and `.venv`).
**Risk tier:** MEDIUM

Inputs read: the five commits, D-196 and its two `Amended by` lines, D-192, the research note and its runs, and
the three Code-Reviewer rounds with their dispositions. The held-out set's questions were not printed, quoted or
read. Only its labels were read, as `score.py` reads them, and the held-out probe was not run. Every example
sentence in this record and in the added tests is the Tester's own.

## Verdict
MAJOR

68 faults were planted: 39 in the Swift router and 29 in the leak check, the router-hints gate and `score.py`. The
wave's own tests caught 40 of them. The 28 survivors are listed below. This review adds 13 tests, which catch 22
of the survivors. The other 6 are equivalent mutants, or changes that alter nothing on today's tree.

One finding stays open, M1. The held-out word check (#180) reads the English example sentences word by word. It
reads the wave's 116 Turkish example and decline-group sentences only as whole strings. These sentences were
written after the live set was committed. Read word by word, 7 of their words are held by the live set, by no
tuning set, and by no reviewed entry. The gate is green only because it does not look at them.

Every D-196 count reproduces from the committed runs, and a test now holds each one (M2). Two D-196 sentences
say more than any test or committed run holds (M9).

## Suite
- **Swift.** A scratch copy of `ios/` at `387b70e` ran the full suite in the offline profile
  (`MODEL_RANKING_REQUIRE_OFFLINE=1 sandbox-exec -f ../scripts/offline.sb swift test --disable-sandbox`).
  - At `387b70e`: **626 tests, 0 failures**. The 10 `TurkishEmbeddingTests` pass, and the embedding's assets load
    here.
  - With this review's `TurkishReadingTesterTests`: **632 tests, 0 failures**.
  - The manifest is regenerated with `swift test --list-tests | sort` and gains 6 lines.
- **Python.** `.venv/bin/python -m pytest -q -n 4 tests` in the seat:
  - with this review's tests: **2831 passed, 29 skipped**;
  - without them: 2824 passed;
  - `ruff check` passes on the touched test files.
- **`score.py`** prints the counts D-196 gives (see M2). The run files were checked as follows:
  - each held-out run answers the set row for row (147 rows, 0 to 146);
  - each own-set run answers the wave's 61 searches, with letters and plain.
- **Weakened tests.** None. The wave's test diff against `origin/main`:
  - swaps the reviewed held-out-only entries for the new live set's, because the old set retired;
  - generalises `_example_counts`;
  - deletes no assertion.

## Acceptance-criterion coverage

| Criterion (D-196) | Citing test | Red to green proven |
|---|---|---|
| Clause 1: a confidently Turkish question that names no surface is read against Turkish examples | `TurkishEmbeddingTests.swift:30`, `:95`, `:127`, `:137` | yes (S04, S06, S07, S09, S11, S12, S39) |
| Clause 1: a named surface decides first; a general question keeps `everyday`, the embedding answers where it is not served | `TurkishEmbeddingTests.swift:50`, `:106`; `KeywordRoutingTests` | yes (S01, S03, S24, S36) |
| Clause 1: the English path is unchanged | added `TurkishReadingTesterTests.swift:23` | yes (S02, only by the added test) |
| Clause 1: the decline groups, also in plain letters | `TurkishEmbeddingTests.swift:127`; added `TurkishReadingTesterTests.swift:38`, `:83` | yes (S09, S11, S12; S10, S35, S38 only by the added tests) |
| Clause 1: the five letters, composed first; marks and other letters keep a line Turkish | `TurkishEmbeddingTests.swift:66`, `:84`; added `TurkishReadingTesterTests.swift:50` | yes (S13 to S17; S18 to S22 only by the added test) |
| Clause 1: a confident Turkish reading (`confidentLanguage`) | `TurkishEmbeddingTests.swift:66`, `:50`; added `TurkishReadingTesterTests.swift:98` | yes (S24, S26; S23 only by the added test) |
| Clause 1 / K2 / round 2's N3: vectors kept per model, revision and language, examples only | `TurkishEmbeddingTests.swift:106`; added `TurkishReadingTesterTests.swift:62` | yes (S29 to S32; S27, S28 only by the added test) |
| Clause 1: Turkish examples cover each described surface | `test_router_hints.py` (Turkish examples test); `TurkishEmbeddingTests.swift:162` | yes (S37, P24) |
| Clause 4: the leak gate decodes escapes, composes, folds, keys by path | `test_ios_client_contract.py:188`, `:314` (at `387b70e`); added `:345`, `:355`, `:366` | yes (P01 to P06, P09, P11 to P15; P10, P17 to P19, P23 only by the added tests) |
| Clause 5: #237's set live, `wording_heldout_m20` retired | `test_ios_client_contract.py` held-out tests | yes (P20, P21) |
| "Measured": every count | added `tests/unit/test_reading_wave_scorer.py:47`, `:57`, `:72`, `:80` | yes (P26 to P29, only by the added tests) |

## Fault injection

**Method.** Each fault was one exact string replacement, made by `plant.py` in the Tester's scratchpad:
1. the target file's md5 was taken;
2. the file was rewritten with the fault and the suite run;
3. the original bytes were written back and the md5 compared.

**Restores.** Each of the 68 plants and the 31 re-runs restored to the md5 taken before it. The scratch files
were Swift `e0312980...` and `score.py` `ce308650...`; the contract test changed as the added tests went in
(`8dc4626d...` at `387b70e`).

**One interrupted run.** The first Swift run was stopped while S02 was planted. That scratch `Router.swift` was
copied back from the seat, and `diff -r` then showed the scratch `ios/` identical to the seat's.

**What was run per fault:**
- **Swift:** the full suite of 626 tests.
- **Python:** `test_router_hints.py` and `test_ios_client_contract.py`, plus `test_reading_wave_scorer.py` once it
  was added.
- **`score.py`:** nothing in the repository reads it (`grep`). Three of its faults planted together passed the
  whole Python suite (2817 passed).

**Survivors.** Each survivor was run again with the added tests.

| Fault | Planted change (file:line at `387b70e`) | Wave's suite | With added tests |
|---|---|---|---|
| S01 | `Router.swift:663` Turkish general rule without `named == nil` | caught (`KeywordRoutingTests`, 3) | - |
| S02 | `:663` general rule on every language (`turkish,` dropped) | **survived** | caught (T5) |
| S03 | `:663` general rule never runs | caught | - |
| S04 | `:669` guard without `turkish ||` | caught (27 failures) | - |
| S05 | `:666` language always `.english` | **survived** | caught by T9's key check; routing equivalent (one multilingual model) |
| S06 | `:667` English examples for a Turkish question | caught | - |
| S07 | `:667` lettered Turkish examples only | caught | - |
| S08 | `:667` Turkish examples added to the English path | caught (`UnmeasuredQuestionTests`) | - |
| S09 | `:668` English decline groups for Turkish | caught | - |
| S10 | `:668` lettered decline groups only | **survived** | caught (T6) |
| S11 | `:292` decline groups reversed | caught | - |
| S12 | `:292` image group emptied | caught | - |
| S13 | `:639` letter guard removed | caught | - |
| S14 | `:638` not composed | caught | - |
| S15 | `:639` the round-2 rule (any letter Turkish does not write) | caught | - |
| S16 | `:623` marks (U+FE0F, U+0308) added to the set | caught | - |
| S17 | `:623` schwa dropped | caught | - |
| S18 | `:623` z with caron dropped | **survived** | caught (T7) |
| S19 | `:623` a with diaeresis dropped | **survived** | caught (T7) |
| S20 | `:623` n with caron dropped | **survived** | caught (T7) |
| S21 | `:623` y with acute dropped | **survived** | caught (T7) |
| S22 | `:623` the five capitals dropped | **survived** | caught (T7) |
| S23 | `:643` threshold 0.3 | **survived** | caught (T8) |
| S24 | `:643` threshold 0.99 | caught | - |
| S25 | `:642` dominant-language guard removed | **survived** | equivalent: `languageHypotheses(withMaximum: 1)` holds the dominant language only |
| S26 | `:626` `confidentLanguage` 0.9 | caught | - |
| S27 | `:697` key without the language | **survived** | caught (T9) |
| S28 | `:697` key without model and revision | **survived** | caught (T9) |
| S29 | `:822` nothing kept | caught | - |
| S30 | `:697` key is the language alone | caught (36) | - |
| S31 | question embedded through the cache | caught (98) | - |
| S32 | a kept vector returned negated | caught (25) | - |
| S33 | `:295` no plain twins | caught | - |
| S34 | `:295` plain twins only | caught | - |
| S35 | `:295` twins kept twice (no filter) | **survived** | caught (T10) |
| S36 | named Turkish question offers no alternatives | caught | - |
| S37 | `search_factuality` Turkish key misspelt | caught | - |
| S38 | `:292` third decline group dropped from the read table | **survived** | caught (T10) |
| S39 | `factuality` dropped from the read table | caught | - |
| P01 | `test_ios_client_contract.py:278` no Swift `\u{}` decoding | caught | - |
| P02 | `:279` no `\U` | caught | - |
| P03 | `:280` no `\uXXXX` | caught | - |
| P04 | `:281` no `\xXX` | caught | - |
| P05 | `:282` no `\N{}` | caught | - |
| P06 | `:282` `\N{}` capitals only | caught | - |
| P07 | `:270` out-of-range code point not guarded | **survived** | harmless: no source holds one, and `chr` would raise, failing loud |
| P08 | `:289` no NFC | **survived** | equivalent: the plain form strips the marks NFC composes (see M9) |
| P09 | `:289` no casefold | caught | - |
| P10 | `:290` dotless i not folded | **survived** | caught (T2) |
| P11 | `:291` marks not stripped | caught | - |
| P12 | `:306` code read in the folded form only | caught | - |
| P13 | `:310` sets read in the folded form only | caught | - |
| P14 | `:303` code not unescaped | caught | - |
| P15 | `:185` texts keyed by file name | caught | - |
| P16 | `:223` the one-text-per-file assert removed | **survived** | a belt: path keying (P15) is held by its own test, and this assert fires only with it |
| P17 | `:179` `tests/` not scanned | **survived** | caught (T3) |
| P18 | `:180` `.py` not scanned | **survived** | caught (T3) |
| P19 | `:179` `src/` not scanned | **survived** | caught (T3) |
| P20 | live set added to `RETIRED_HELD_OUT` | caught | - |
| P21 | `wording_heldout_m20` made live again | caught | - |
| P22 | `:307` set strings not unescaped | **survived** | equivalent: JSON strings arrive decoded |
| P23 | `:306` the 25-character rule at 60 | **survived** | caught (T4) |
| P24 | `Router.swift` `search_factuality` Turkish key misspelt, Python gate | caught (`test_router_hints.py`) | - |
| P25 | `Router.swift` two Turkish mathematics examples removed | **survived** | no rule: two or more is the gate, and six per surface holds today |
| P26 | `score.py:19` "not a search" right only when asked | **survived** (whole suite) | caught (T1) |
| P27 | `score.py:20` a search right on its surface alone | **survived** | caught (T1) |
| P28 | `score.py:42` own-set search right on any surface | **survived** | caught (T1) |
| P29 | `score.py:20` a two-surface label read whole | **survived** | caught (T1) |

## Findings

1. **M1 (MAJOR, open). `tests/unit/test_ios_client_contract.py:2026`: the #180 word check does not read the
   wave's Turkish sentences word by word.**
   - **How it reads now.** `_wording_lists` finds the first `static let examples...` table with `re.search` and
     splits its sentences into words. That table is the English one. `examplesTurkish` (`Router.swift:235`) and
     `unmeasuredHintsTurkish` (`:152`) fall to the "every other literal" loop, which matches each sentence whole.
     A whole Turkish sentence is flagged only if a held-out question holds it verbatim.
   - **What it misses.** The method:
     1. Each of the 116 Turkish sentences was split with the module's own `[^\W\d_]+`.
     2. The words went through the module's own `_held_out_only_signals(..., plain_letters=True)`.
     3. The result: 8 words are held by `reading_heldout_m22` and by no tuning set. One of them is already
        reviewed from another list, so **7 are unreviewed**.
   - **Why it matters.** The words are not printed here. These sentences were committed in `be0b101`, after the
     set (`f884bfe`). D-196's held-out gain rests on their independence from the set ("written for this wave,
     never from a held-out set"). The control that holds this for the English examples does not read them.
   - **Remedy.**
     - Read every `static let examples*` and `unmeasuredHints*` table word by word (one `re.finditer` in place
       of the `re.search`).
     - Run `test_every_wording_entry_only_a_live_held_out_set_holds_is_reviewed`.
     - Review each word it names. The "in the app before the set was written" provenance does not fit these, so
       each needs its own reason (a common word the wave's tuning sentences also use), or replace the word.
   - **Assertion to add.** A Turkish example word that no other list holds is in `_wording_lists`'s entries.
2. **M2 (MINOR, closed by T1). `docs/research/reading-wave-m22-runs/score.py` was held by no test.**
   - P26 to P29 changed every count it prints and passed the whole suite.
   - D-196's "Measured" figures were checked against the runs, counts only:
     - 88/59/8 before, 94/65/0 at the first head, 91/62/0 after, with 29 of 58 caught throughout;
     - the model tier asked 1 and 3 times;
     - own set 31/29 before and 44/39 after;
     - 3 gained and 0 lost;
     - against the first head, 4 lost and 1 gained, three of the 4 `everyday`;
     - a cost of 10.
   - No row answered before the wave changed its surface or reading.
   - `tests/unit/test_reading_wave_scorer.py` now holds these figures, as `test_reading_probe_scorer.py` does for
     M19-W4.
3. **M3 (MINOR, closed by T5). `Router.swift:663`: "the English path is unchanged" was not held.**
   - With `turkish` dropped from the general rule (S02), English questions with a general word went to
     `everyday` before the embedding:
     - "which ai explains how volcanoes erupt" (`expert` today);
     - "claude for writing a thank you note to my boss" (`assistant`);
     - "which model can fill in this web form for me" (`computer-use`).
   - All 626 tests stayed green.
4. **M4 (MINOR, closed by T6 and T10). The decline groups' plain twins were not held (`Router.swift:292`, `:668`).**
   - **S10.** With the lettered groups only, "bu fotodaki arka plani bulaniklastir" and "portremi cizgi film gibi
     yap" read as `abstract` instead of `vision`.
   - **S38 and S35.** A group dropped from the read table, or a twin kept twice, passed. The wave's count test
     reads the lettered table.
5. **M5 (MINOR, closed by T7). `Router.swift:623`: four of the five letters and all five capitals were not held.**
   The wave's test lines hold the schwa, and the Turkmen line holds a with diaeresis, n with caron and y with acute
   together. Dropping any one letter other than the schwa, or the capitals, passed. A Turkmen line with only
   z with caron, for example, would then be read as Turkish. T7 adds each letter alone to one Turkish line.
6. **M6 (MINOR, closed by T8). `Router.swift:643`: the confidence threshold was held only from above.** A threshold
   of 0.3 passed. Under it, "html sayfasi" (Turkish at 0.46) leaves the English path, which is #218's ground and
   which D-196 leaves open.
7. **M7 (MINOR, closed by T9). `Router.swift:697`: round 2's N3 claim was not held.** N3 says the vectors are
   "keyed by the embedding's model and revision as well as the language". The wave's test reads a key's last line
   only, so a key without the model and revision (S28) or the language (S27) passed.
8. **M8 (MINOR, closed by T2, T3 and T4). The leak check's folding, scope and length rule
   (`test_ios_client_contract.py:177`, `:290`, `:306`).**
   - The planted Turkish question holds no dotless i, so dropping the dotless-i fold (P10) passed. A held-out
     question with a dotless i, typed in plain letters in a test, would then go unseen.
   - The round-2 test holds two `Router.swift` paths only, so a scan without `tests/`, `src/` or `.py` (P17 to
     P19) passed.
   - No planted question sits near 25 characters, so a rule of 60 (P23) passed.
9. **M9 (MINOR, open). Two D-196 sentences say more than any gate or committed run holds (D-192).**
   - **The floor range.** "A floor does not separate them: ... 0.18 to 0.51 and ... 0.24 to 0.56"
     (`docs/decisions.md:5039`, and the note's section 3). No committed run carries a score. The own-set runs hold
     surface and reading only. Remedy: commit that run, or say the range was measured and not kept.
   - **Clause 4.** It says the gate "compares each side composed and in plain letters ... planted tests hold each
     form". No planted test holds the composed form (P08 survives, because the plain form strips the same marks),
     and none held the dotless i until T2. Remedy: say "in plain letters, which also covers a decomposed letter",
     or drop "each form".
10. **N1 (process, open). D-196 first appears in `be0b101`, which also changes `ios/` and `scripts/`.**
    - D-192 clause 2 (#201) says to write the decision before the code it governs. `make wave-check` reads that
      rule only for an `m<N>-wave-<W>-close.md`, which a backlog wave does not have, so nothing flagged it. The
      backlog-data wave added D-195 in a docs-only commit (`7bdc928`).
    - Remedy: record it. Reordering pushed history is not on the table.
11. **R1 (risk, informational).** On the shipped code:
    - the plain spelling of the wave's own vision test line, "selfiemdeki kirmizi gozleri duzelt", reads
      `assistant`;
    - the Tester's "bu fotodaki arka plani bulaniklastir", written with its Turkish letters, reads `abstract`,
      while the plain spelling reads `vision`.

    D-187 clause 2 accepts the closest surface. This is the trade round 2's R1 names, seen from the image side.

## Tests added this review
All pass at `387b70e`, and each fails on the fault named.
- **T1:** `tests/unit/test_reading_wave_scorer.py:47`, `:57`, `:72`, `:80`. The runs answer the set row for row,
  and D-196's held-out, own-set and question-by-question figures follow from them (P26 to P29).
- **T2:** `tests/unit/test_ios_client_contract.py:345`, `test_a_held_out_question_with_a_dotless_i_is_found_in_plain_letters`
  (P10).
- **T4:** `tests/unit/test_ios_client_contract.py:355`, `test_a_held_out_question_of_twenty_five_characters_is_found_inside_a_longer_string`
  (P23).
- **T3:** `tests/unit/test_ios_client_contract.py:366`, `test_the_held_out_check_reads_each_folder_and_both_kinds_of_file`
  (P17 to P19).
- **T5:** `ios/EngineTests/TurkishReadingTesterTests.swift:23`,
  `testAnEnglishQuestionWithAGeneralWordIsStillReadByTheEmbedding` (S02).
- **T6:** `:38`, `testATurkishRequestToChangeAnImageTypedPlainReachesVision` (S10).
- **T7:** `:50`, `testEachLetterAzerbaijaniAndTurkmenWriteKeepsALineOutOfTurkishOnItsOwn` (S18 to S22).
- **T9:** `:62`, `testAKeptVectorIsKeyedByTheEmbeddingsModelRevisionAndLanguage` (S27, S28; also S05's key).
- **T10:** `:83`, `testTheTablesTheTurkishPathReadsHoldEachLineOnceAndTheThreeGroups` (S35, S38).
- **T8:** `:98`, `testTheTurkishPathNeedsTheRecognisersConfidence` (S23).
- **Manifest:** `ios/EngineTests/test-manifest.txt` gains the 6 Swift tests, regenerated with
  `swift test --list-tests | sort`.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Fixed. `_wording_lists` reads every `examples*` and `unmeasuredHints*` table word by word. The seven words it names are everyday Turkish from `examplesTurkish` as first committed (`be0b101`), by an author who has never read the set; each is reviewed by name (`_WORDING_TURKISH`). The assertion asked for is added; with the old single read planted, two tests fail. | `tests/unit/test_ios_client_contract.py` |
| M2 | Closed by T1. | `tests/unit/test_reading_wave_scorer.py` |
| M3 | Closed by T5. | `ios/EngineTests/TurkishReadingTesterTests.swift` |
| M4 | Closed by T6 and T10. | same |
| M5 | Closed by T7. | same |
| M6 | Closed by T8. | same |
| M7 | Closed by T9. | same |
| M8 | Closed by T2 to T4. | `tests/unit/test_ios_client_contract.py` |
| M9 | Fixed. D-196 and the note say the floor range was measured once and not kept; clause 4 names what its planted tests hold. | `docs/decisions.md` D-196, `docs/research/reading-wave-m22-probe.md` sections 3 and 9 |
| N1 | Recorded; pushed history is not reordered. Filed as #274: D-192 clause 2 is read only for milestone waves. | #274 |
| R1 | Accepted, as D-187 clause 2 and round 2's R1 accept the closest surface. | none |
