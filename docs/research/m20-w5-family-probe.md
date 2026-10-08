---
record_type: register
id: m20-w5-family-probe
status: draft
process_version: v6.6
date: 2026-10-08
---
# M20-W5: the question reading and our own list, measured on a fresh set (#195)

**Measured on 2026-10-08** on the owner's Mac, where Apple Intelligence runs. The probes ran in
scratch copies of `ios/`:
- **before:** `main` at `bd273bc`, the code TestFlight build 1 carries;
- **after:** `wave/m20-w5` with W1 to W4 merged.

Each copy ran two harnesses:
- `scripts/router_probe/ReadingProbe.swift`, on two tiers:
  - the model tier: the on-device model, then the signals in code, as the app runs it;
  - the wording tier (`PROBE_TIER=wording`): a device without the model.
- `docs/research/m20-w5-runs/FamilyProbe.swift` (after only), with the wording tier. For each question
  it records:
  - the refinements the words name (`Refinements.read`, D-188 clause 6);
  - the family list the app would build (`familyBoards`, then `combineFamily`);
  - beside it, the primary board's own order.

Inputs for the family probe: the served `/v1/boards` (2026-10-08) and the families of
`app.workflows.families` (`families-served.json`). Every run and the scorer are in
`docs/research/m20-w5-runs/`. The scorer prints counts only, never a question.

## 1. The set (D-147 clause 5, #195)

**Held out, unread by the author:** `scripts/router_probe/wording_heldout_m20_questions.json`.
- An independent seat wrote it before reading any code. It read only the surfaces' descriptions in
  `categories.py` and a brief.
- **Labels:** each question carries its surface (several where a fair reader could pick either, `none`
  for not a model search), the task's language and the domain.
- **Kinds:** general "which AI" questions (8), one per surface (16), words with a second meaning (12),
  real language tasks (9), real domain questions (9), image requests (9), the "task: question" colon
  form (8), and questions that are not a model search (7).
- It holds the phrasings the M19 probes broke (#195): case-marked image nouns, and the colon form.

80 were written; 2 matched questions already in the app's tests and tuning sets. The held-out gate
found them, and they were dropped, so the scores below are on **78**: 39 English and 39 Turkish, of
which 71 are searches.

**Retired to tuning at this wave (#195):** the two M19 held-out sets. M19-W4 measured them, and five
review rounds replayed them. `RETIRED_HELD_OUT` names them, and `HELD_OUT_ONLY_REVIEWED` names the
three signal words the new set alone holds. All three were in the app before the set was written.

## 2. The surface each question reaches

A row is right when the reading is a search, it is measured, and the surface is one its label
allows. For a `none` question, it is right when the reading is not a search. The wording tier gave
identical rows in both runs, as it should. The model tier is not deterministic.

| tier | run | all (78) | English (39) | Turkish (39) |
|---|---|---:|---:|---:|
| wording, before | 1, 2 | 43, 43 | 23, 23 | 20, 20 |
| wording, after | 1, 2 | 44, 44 | 23, 23 | 21, 21 |
| model, before | 1, 2 | 47, 45 | 25, 25 | 22, 20 |
| model, after | 1, 2 | 45, 43 | 24, 22 | 21, 21 |

**What this says.**
- **The wording tier gains one question:** a Turkish question made only of model names (#206).
- **The model tier's spread covers the difference.** Its change between before and after (−2 on each
  run) is within the two points its own two runs differ by. This milestone did not change what the
  model tier answers.
- **The weak kinds are the same on both tiers:**
  - real language tasks: wording tier 1 of 9;
  - real domain questions: wording 3 of 9, model 2 to 4;
  - general "which AI" questions on the model tier: 3 of 8. The model sends them to a surface the
    label does not allow.
- **On the wording tier, 10 questions fall to "not measured"** (the manual tier). 8 of them are
  searches. That is 8 of 71 searches on a device without Apple Intelligence that get no answer
  until the reader picks a surface. Filed (§5).

## 3. The refinements the words name (after; D-188 clause 6)

| | right on | needed on | a wrong one added on |
|---|---:|---:|---:|
| language | 74 of 78 | 10 | 0 |
| domain | 69 of 78 | 18 | 3 |

- **No language board was added where none was asked for.** Four real language tasks got none: the
  rule reads a language name only where a word makes it the task's (D-188 clause 6). The second
  review traded those four for no false additions.
- **The domain rule added a domain three times where the label has none,** and missed six.
- This is the device without the model. With the model, the model's own choice stands (D-188
  clause 6), and this probe did not measure it.

## 4. Our own list against the primary board's own order (after)

| measure | value |
|---|---|
| searches answered with a list (wording tier) | 65 of 78 |
| lists built from more than one board | 54 |
| boards per list | 1 board: 11 · 2: 8 · 3: 27 · 4: 15 · 5: 4 |
| models listed, mean | 126.8 (the primary board alone: 117.3) |
| top 10 shared with the primary board's top 10 | mean 5.2 (min 2, max 9) |
| the same first model | 26 of 54 |
| older boards named under a list | `epoch_mmlu` 28 times, `epoch_eci` 23, `swebench`, `epoch_swe_bench_verified` and `aider` 7 each, others fewer |

**What this says.**
- **The combined list is a different answer.** About half of its top ten is not in the primary
  board's top ten, and its first model differs on half of the lists.
- **The set cannot say which answer is better.** It is labelled for the question's surface, not for
  the best model. No ground truth for "the best model" exists here.
- **D-188's revisit condition is not triggered.** That condition needs a labelled set showing the
  combined list placing models worse for the questions it was built for, and this set cannot show
  that either way.
- **The lists are longer than the primary board's,** because coverage lets in a model that half of
  the boards rank.
- **Most families carry an older board.** Epoch's undated boards (`epoch_eci`, `epoch_mmlu`) are
  named on most `everyday` and `expert` lists, as D-188 clause 4 says they must be.

## 5. Follow-ups

- **#222:** on a device without Apple Intelligence, 8 of 71 held-out searches fall to "not
  measured". D-187 wants an understood question answered, and these are understood by a person.
  This is for M21-W2, beside #66.
- **A labelled set for "the best model"** would let the revisit condition of D-188 be measured. It
  needs a ground truth the boards do not give: a reader's own judgement on a sample of answers. That
  is the owner's call, and none is planned yet.
