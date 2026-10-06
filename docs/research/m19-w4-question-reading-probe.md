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
