# The reading wave: a Turkish question read through Turkish examples, measured on reading_heldout_m22 (#222, #237)

**Measured 2026-10-14** on the owner's Mac, where Apple Intelligence runs, through
`scripts/router_probe/ReadingProbe.swift` in scratch copies of `ios/`:
- **before:** `wave/backlog-reading` at `f884bfe` (main at `55da886` plus the new set);
- **after:** the same branch with the change below.

The runs and the scorer (`score.py`, counts only) are in `docs/research/reading-wave-m22-runs/`. A run
row names its question by its row in the set, so the runs hold no question text.

## 1. The set

`scripts/router_probe/reading_heldout_m22_questions.json` (#237) was written by an independent seat and
is unread by the author. It holds 147 questions: 89 searches and 58 that are not a search. Its labels
are a surface (or two, `a|b`) or `NOT_A_SEARCH`.
- **Measured twice before, twice after and twice after the review's fixes, on the wording tier.** The
  model tier was measured twice before. The change reaches it only where the model answers "none of
  these" on a search and the wording tier answers instead (D-187 clause 4): in the two model runs, no
  such row was "not measured" on the wording tier, so the held-out effect there is none (the review's N2).
- **Tuning for this wave:** only sentences the wave wrote itself
  (`scripts/router_probe/turkish_tuning_questions.json`, 80) and the existing tuning sets.
- **Two of the wave's own sentences equalled held-out rows.** The leak gate reported them by file and
  length only. They were removed from the tuning set unread, by a script that compared the two files
  without printing either. One of them was in the runs below and was dropped from them the same way.

## 2. Before: where the wording tier loses

| tier, run | right (147) | searches right (89) | searches not measured (89) | searches asked (89) | not a search caught (58) |
|---|---:|---:|---:|---:|---:|
| wording, before 1 and 2 | 88, 88 | 59, 59 | 8, 8 | 0, 0 | 29, 29 |
| model, before 1 and 2 | 99, 98 | 64, 64 | 0, 1 | 1, 3 | 35, 34 |

A rough split by language (a script reads Turkish letters and particles; the questions were never
printed) put the 8 searches not measured among the Turkish ones: the wording tier declines every
question the recogniser is sure is not English, and answers it only from a word that names a surface.

## 3. The change (#222)

*Superseded in part by section 6: the brand-only rule below became `generalSurface`'s, and a letter
Turkish never writes now keeps another language out.*

Apple's contextual embedding for Latin script is one multilingual model:
`NLContextualEmbedding(language: .turkish)` and `.english` return the same `modelIdentifier`, with
assets on the device.

So a question the recogniser is sure is Turkish is compared against six Turkish example questions per
surface (`CategoryHints.examplesTurkish`, written for this wave, never from a held-out set). It is
scored the same way as the English examples: centred, the mean of the two closest, the same floor and
the same image rule (`unmeasuredHintsTurkish`). The rest stays as it was:
- a word that names a surface still decides first (D-187 clause 1);
- **a Turkish question that names an AI brand** (`generalWords`: gpt, claude, gemini and the rest) keeps
  `everyday`, as before. On the tuning set, the brand names pulled the embedding off the one task
  word: "odev" (homework) went to `abstract` and "ceviri" (translation) to `factuality`;
- every other language the recogniser is sure of still declines;
- the English path is unchanged.

**On the wave's own sentences**, which are the wording tier's surface and count only searches:

| set | before | after |
|---|---:|---:|
| own Turkish searches (52) | 23, with 18 not measured | 38, with 0 not measured |
| own short questions with model names (9) | 8 | 8 |
| `probe_questions.json` (12 scored), `coding_tuning_questions.json` (24) | 12, 22 | unchanged (English path) |

**A floor does not separate Turkish searches from what is not a search.** On the wave's own sentences,
the closest surface scored 0.18 to 0.51 for 27 Turkish searches and 0.24 to 0.56 for 18 Turkish lines
that are not a search. That matches the English finding at M16-W1
(`docs/reviews/m16-router-floor-measurement.md`), so the floor stays at 0.15.

## 4. After

| tier, run | right (147) | searches right (89) | searches not measured (89) | searches asked (89) | not a search caught (58) |
|---|---:|---:|---:|---:|---:|
| wording, after 1 and 2 | **94, 94** | **65, 65** | **0, 0** | 0, 0 | 29, 29 |

Question by question, between the first run before and the first after:
- **6 rows gained and none lost.**
- **31 rows' outcomes moved.** Beside the 6 gained, 7 searches moved without changing the count: each
  is wrong before and after, or right on another surface its label allows.
- **The cost, 18 rows that are not a search:**
  - 9 of them the reading did not catch. They fell to "not measured" before, because the tier could not
    read Turkish, and now get a ranking. The review's own pairs show the reading catches less in Turkish
    than in English (small talk and an injection attempt; its N5), which #66 now records.
  - 7 of them are asked about by the reading, as before, and now carry a surface.
  - 2 moved from one surface to another.
  - Catching input that is not a search is #66's, which this wave does not change.

## 5. What stays open

- **#218.** A short Turkish question the recogniser is not sure of (the issue's own
  example, or two model versions compared with Turkish particles) still reaches the English path.
  - On the tuning set, adding the Turkish examples to the English path did not move either.
  - The signals D-191 took out are not tried again.
- **#66.** The wording tier catches 29 of 58 lines that are not a search on the fresh set, and the model
  tier 35 and 34. M19-W4's bars are not met.

## 6. After the review (`docs/reviews/backlog-reading-review-round-1.md`)

The review's verdict was MAJOR. Its numbers reproduced the runs above exactly. The fixes:
- **M1.** A Turkish question that `generalSurface` answers (a brand, "en iyi model", "hangi yapay
  zeka") keeps `everyday`, as before the wave. Only a question that had no answer before reaches the
  Turkish examples, so every question that was answered before keeps its surface. Where the engine serves no
  `everyday`, the question goes to the embedding (N6).
- **M2.** The recogniser knows no Azerbaijani or Turkmen and reads them as Turkish at 1.00. A question
  holding a letter Turkish never writes is not Turkish, so it declines as before. Since the third review
  (section 8) these are the five letters Azerbaijani and Turkmen write and Turkish never does
  (`turkicNotTurkishLetters`). Azerbaijani written without one is still read as Turkish.
- **N1.** Each Turkish example is also read in plain letters (`examplesTurkishBothSpellings`). The runs
  below are committed (`own-*.json`, `own_tuning_plain.json`) and scored by `score.py`.
- **K2.** Each example's vector is computed once per language (`ExampleVectors`). One wording-tier run
  over the 147 rows (two routes each) took 33 s, where the review measured about 1.4 s a route before.
  Every row came out the same.

**On the wave's own 61 Turkish searches** (the 52 and the 9 short ones; the wording tier's surface):

| variant | with letters | the same, plain |
|---|---:|---:|
| before the wave | 31 (22 not measured) | 29 (22 not measured) |
| after the fixes, examples with letters only | 45 | 37 |
| after the fixes, both spellings (shipped) | 44 | 39 |

**Held-out, twice, after the fixes:**

| tier, run | right (147) | searches right (89) | searches not measured (89) | not a search caught (58) |
|---|---:|---:|---:|---:|
| wording, after the review 1 and 2 | 91, 91 | 62, 62 | 0, 0 | 29, 29 |

- **Against before:** 3 rows gained and none lost; 25 rows' outcomes moved.
- **Against the first head:** 4 searches lost and 1 gained (round 2's N4). Three of the 4 are answered
  `everyday` again under M1's rule, which keeps every question answered before; the fourth was "not
  measured" before the wave and now reads another surface, likely through the plain spellings. The rule
  was chosen from the review's sentences and the rule itself, before this run.
- **A Turkish question that names its surface** keeps it, and now also offers the two closest others, as
  an English one does (round 2's N4; held by a test).
- **The cost:** 10 lines that are not a search, uncaught by the reading, moved from "not measured" to a
  ranking.
- **Not fixed:** a request for sound ("sing a song in my own voice", in Turkish) reaches `vision` through
  the Turkish image group; D-187 clause 2 sends it to the closest surface. A request to change an image
  reaches `vision` only through the Turkish groups, and a test holds that.

## 7. After the second review (`docs/reviews/backlog-reading-review-round-2.md`)

- **M1.** The held-out check keyed the files it read by name, so the fixtures' `Router.swift` replaced the
  app's, and the app's router (with this wave's Turkish examples) was never read. It is keyed by path now;
  read so, the live set shows no leak.
- **M2.** The letter rule counted marks: an emoji's variation selector or a decomposed accent sent a
  Turkish question back to "not measured". The question is composed first and only letters are tested.
- **N3.** The kept vectors are keyed by the embedding's model and revision too, and a test holds that only
  the router's examples are kept.
- **Held-out, once more with the final code:** every one of the 147 rows reads as in the first run after
  the first review's fixes. The wave's own 61 searches read 44 and 39, as in section 6.

## 8. After the third review (`docs/reviews/backlog-reading-review.md`, MINOR)

- **N1.** "Any letter Turkish does not write" also sent a Turkish question naming pi or a cafe to "not
  measured". The rule now reads only the five letters Azerbaijani and Turkmen write and Turkish never
  does (the schwa, a with diaeresis, n with caron, y with acute and z with caron), after composing; a test holds a Greek letter, an accented one, and the
  Turkmen line decomposed.
- **N3.** The held-out check itself now refuses to read two files under one key.
- **N4.** D-196's and this note's claims were narrowed to what the runs show.
- **Held-out, once with the final code** (`final-wording-1.json`): two rows carry a letter Turkish does not
  write, and neither carries one of the five, so the narrower rule could read them differently. It did
  not: all 147 rows read as in `review-wording-1.json` (91 right; searches 62 of 89, none not measured).
