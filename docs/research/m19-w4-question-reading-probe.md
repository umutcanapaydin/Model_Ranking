---
record_type: register
id: m19-w4-question-reading-probe
status: draft
process_version: v6.6
date: 2026-10-07
---
# M19-W4: reading the question, a second round, measured (#66, #113)

**Measured 2026-10-07** on the owner's Mac, where Apple Intelligence runs, through
`scripts/router_probe/ReadingProbe.swift` in a scratch copy of `ios/`: the model tier as the app runs
it, and the wording tier (`PROBE_TIER=wording`), each followed by the signals in code. Plan:
`docs/plans/m19-wave-4-plan.md` (deleted at the close). Runs and the scorer (`score_w4.py`) are in
`docs/research/m19-w4-runs/`.

## 1. The sets (D-147 clause 5)

**Held out, unread by the author:** `notasearch_heldout_m19_questions.json` (100: 20 knowledge
questions, 10 each of instructions to the app, chit-chat and pasted content, 40 genuine searches, 10
ambiguous) and `image_heldout_m19_questions.json` (50: 20 to make or change an image, 10 to read
one, 20 that only mention images). Half of each is in Turkish. An independent seat wrote them before
reading anything in the repository (`5fe0793`). The author reads only their counts until the last
measure; `score_w4.py` refuses to list their questions.

**Retired to tuning at this wave (#177):** the three M18 held-out sets, each spent at M18-W3.

**Tuning:** `reading_tuning_w4.json` (306: the M17 and M18 not-a-search sets and M18-W3's reading
tuning set, deduplicated) and `image_tuning_w4.json` (82: the three image sets).

## 2. Baseline at `3426ff3` (the code that ships) and the bars

Every row of every run had an answer from the model. The wording tier gave identical rows in both
runs, as it should: it does not depend on a model.

| set | measure | model run 1 | model run 2 | wording run 1 | wording run 2 |
|---|---|---:|---:|---:|---:|
| reading (100) | not-a-search inputs given the note or asked (50) | 18 | 21 | 8 | 8 |
| | knowledge questions given the note or asked (20) | 1 | 3 | 0 | 0 |
| | genuine searches given the note (40) | 0 | 0 | 0 | 0 |
| | genuine searches asked (40) | 0 | 0 | 0 | 0 |
| | genuine searches on their expected surface (40) | 30 | 28 | 14 | 14 |
| image (50) | requests to make an image told "not measured" (20) | 2 | 1 | 14 | 14 |
| | of the misses, on `vision` / `web-dev` / other | 12 / 6 / 0 | 12 / 7 / 0 | 0 / 3 / 3 | 0 / 3 / 3 |
| | requests to read one reaching `vision` (10) | 10 | 9 | 4 | 4 |
| | questions that only mention images, overridden to "not measured" (20) | 0 | 0 | 0 | 0 |

By class on the model tier (noted / asked), runs 1 and 2: knowledge 0 / 1 and 0 / 3; instructions to
the app 0 / 3 and 0 / 5; chit-chat 0 / 9 and 0 / 8; pasted content 0 / 5 and 1 / 4.

**The bars,** by the plan's rules, fixed here before any variant runs. Each run of the final measure
must meet each one.

| measure | tier | bar | from |
|---|---|---|---|
| genuine searches given the note | model | at most 2 | D-169 clause 6 |
| not-a-search inputs given the note or asked | model | at least 40 of 50 | D-169 clause 6 |
| genuine searches asked | model | at most 4 | M18-W3's bound |
| knowledge questions given the note or asked (#66) | model | at least 14 of 20 | 1 + ⌈2/3 × 19⌉ |
| requests to make an image told "not measured" (#113) | model | at least 14 of 20 | 1 + ⌈2/3 × 19⌉ |
| requests to make an image told "not measured" (#113) | wording | at least 18 of 20 | 14 + ⌈2/3 × 6⌉ |
| genuine searches on their expected surface | model / wording | at least 26 / 12 of 40 | the lower run, less 2 |
| requests to read an image reaching `vision` | model / wording | at least 8 / 3 of 10 | the lower run, less 1 |
| questions that only mention images, overridden | both | at most 1 of 20 | the plan |

D-169 clause 6 holds the model tier, as it says; on the wording tier the reading is reported.

## 3. Variants, on the tuning sets only

Each variant changing the model's instructions or schema ran through `ReadingProbe.swift`. Each
variant changing only the code after the model was scored with `ReplayProbe.swift`: the reference
runs' recorded model answers (`v0-*`), read again by the variant's code, which is exact for such a
variant (checked on 306 rows: none differed).

**#66, the reading tuning set (306: 109 not a search, 22 of them knowledge questions; 186 genuine).**
Runs 1 and 2.

| variant | what changed | not a search caught | knowledge | genuine noted / asked | genuine on surface |
|---|---|---:|---:|---:|---:|
| reference (`3426ff3`) | — | 69, 67 | 1, 2 | 0 / 14, 0 / 7 | 133, 131 |
| a | the model's instructions: a question of fact defined by what is asked; `assistant` no longer "answers a general question" | 76 | 2 | 0 / 17 | 128 |
| b | in code: a question of fact is a doubt; small talk, a task with its content and an order read as the tuning sets typed them | 97, 94 | 18, 18 | 0 / 15, 0 / 8 | 133, 131 |
| c | a and b | 93 | 18 | 0 / 17 | 129 |

The model's verdict hardly moves with its instructions: it called 2 of 22 knowledge questions
something else under (a), against 1 and 2 under the reference, and (a) cost surface accuracy and
asked more genuine searches. (a) and (c) ran once: their second runs were stopped when the first
showed each below (b) on every measure, to free the model for the held-out measure. (b) was built
(`de8c3f8`).

**#113, the image tuning set (82: 36 to make, 26 to read, 20 that only mention images).**

| variant | what changed | made, told "not measured" | read, reaching `vision` | others overridden |
|---|---|---:|---:|---:|
| reference | — | 24, 23 | 21, 21 | 0, 0 |
| a | the rule on every surface | 29, 28 | 21, 21 | 0, 0 |
| b | c, and a closed yes/no field asking the model whether the text makes or changes a picture | 35 | 15 | 7 |
| c | a, the Turkish forms it missed, and never on `coding` or `agentic-coding` | 32, 31 | 21, 21 | 0, 0 |

(b)'s field said yes to requests to read an image and to code that handles images: it failed both
guards in its first run, and its second was stopped. (c) was built: on the M18 reviews' B4 lines
the rule reached `coding`, so it now stops there; on the tuning sets it changes no genuine search's
surface. On the wording tier, (c) took the image tuning set from 25 to 33 of 36, overriding nothing.

## 4. The held-out measure, at `de8c3f8`

Twice on each tier, on the sets of §1, each run once through the code that was built.

| measure | tier | bar | run 1 | run 2 | baseline | met |
|---|---|---|---:|---:|---:|---|
| genuine searches given the note (40) | model | at most 2 | 0 | 0 | 0, 0 | yes |
| genuine searches asked (40) | model | at most 4 | 2 | 1 | 0, 0 | yes |
| not-a-search inputs given the note or asked (50) | model | at least 40 | 25 | 27 | 18, 21 | **no** |
| knowledge questions given the note or asked (20) | model | at least 14 | 6 | 6 | 1, 3 | **no** |
| requests to make an image told "not measured" (20) | model | at least 14 | 8 | 8 | 2, 1 | **no** |
| requests to make an image told "not measured" (20) | wording | at least 18 | 18 | 18 | 14, 14 | yes |
| genuine searches on their expected surface (40) | model | at least 26 | 32 | 29 | 30, 28 | yes |
| | wording | at least 12 | 14 | 14 | 14, 14 | yes |
| requests to read an image reaching `vision` (10) | model | at least 8 | 10 | 9 | 10, 9 | yes |
| | wording | at least 3 | 4 | 4 | 4, 4 | yes |
| questions that only mention images, overridden (20) | both | at most 1 | 0 | 0 | 0, 0 | yes |

By class on the model tier (noted / asked), runs 1 and 2: knowledge 0 / 6 and 0 / 6; instructions
to the app 0 / 4 and 1 / 5; chit-chat 0 / 7 and 0 / 7; pasted content 1 / 7 and 0 / 8. The requests to
make an image still missed went to `vision` (9) and `web-dev` (3) in both runs. On the wording tier,
6 knowledge questions were asked in each run, and 1 genuine search.

**The misses, read now that the sets are spent.**
- *Knowledge questions:* the signal's length limit (ten words) left out three; "live" in "how long do
  giant tortoises usually live" was read as something current; English "which" and "what" before a
  noun ("which river", "what country", "what instrument"), the Turkish "which" before a noun ("in
  which province", "which city's"), "where to", and "how many" typed without its Turkish letter are
  not read as questions of fact. The model called each "a model search".
- *Requests to make an image:* five are searches for a model that makes images ("which ai is best at
  generating realistic pictures of people", "a model that draws illustrations", translated from
  Turkish), which no rule reads; two
  verbs are not on the list ("erase", "upscale"); in two the image is too far from its verb.
- *Genuine searches asked* (translated from Turkish): "could you recommend a general model for my
  daily tasks" on the model's word, and "which chatbot gives information as reliable as Wikipedia" on
  the fact signal (its "which one").

## 5. What it says

- **No genuine search is denied its ranking, and few are asked about:** 0 given the note, 2 and 1
  asked of 40, inside both bounds, as at M18.
- **#66 improves and misses its bars.** Knowledge questions caught go from 1 and 3 to 6 and 6 of 20,
  and not-a-search inputs from 18 and 21 to 25 and 27 of 50, against bars of 14 and 40. The signal
  was written from the tuning sets' phrasings and reaches about a third of a stranger's. The model's
  own verdict does not move with its instructions (§3, variant a).
- **#113 meets its bar on the wording tier and misses it on the model tier.** Requests to make an
  image told "not measured": 14 to 18 of 20 without the model (bar 18), 2 and 1 to 8 and 8 with it
  (bar 14). No question that only mentions an image was overridden, and requests to read one reach
  `vision` as before.
- **Three variants were run per problem.** By the plan and D-169 clause 6, nothing more is tuned on
  these sets, and the pull request asks the owner whether to ship what holds.

## 6. State

- Shipped by the wave: the reading of a question of fact (a doubt), the second-round signals, and the
  image rule on every surface but code. #66 and #113 stay open: the knowledge and image-making gaps
  of §4 are what a next round would start from, on fresh sets.
- The two M19 sets are spent. They stay registered as live (`RETIRED_HELD_OUT` leaves them out) until
  the next fresh set lands, as the M18 sets did until #177: the held-out gates need a live set.
