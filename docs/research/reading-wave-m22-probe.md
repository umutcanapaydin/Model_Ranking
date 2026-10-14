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
- **Measured twice before and twice after, on the wording tier.** The model tier was measured twice
  before; the change does not touch it.
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
    read Turkish, and now get a ranking, as the same input in English already does.
  - 7 of them are asked about by the reading, as before, and now carry a surface.
  - 2 moved from one surface to another.
  - Catching input that is not a search is #66's, which this wave does not change.

## 5. What stays open

- **#218.** A short Turkish question the recogniser is not sure of ("claude mu chatgpt mi almanca",
  the issue's own example, or "o3 mu o4 mu" typed with its letters) still reaches the English path.
  - On the tuning set, adding the Turkish examples to the English path did not move either.
  - The signals D-191 took out are not tried again.
- **#66.** The wording tier catches 29 of 58 lines that are not a search on the fresh set, and the model
  tier 35 and 34. M19-W4's bars are not met.
