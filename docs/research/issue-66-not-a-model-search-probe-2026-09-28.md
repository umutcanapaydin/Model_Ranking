---
record_type: register
id: issue-66-not-a-model-search-probe-2026-09-28
status: ratified
process_version: v6.6
date: 2026-09-28
---
# Issue #66: can the on-device model tell a model search from everything else? Measured: not yet

**Measured 2026-09-28** on the owner's Mac, where Apple Intelligence runs, through
`scripts/router_probe/RefinementProbe.swift`, in a scratch copy of `ios/`. The work was stopped by the
owner's ruling after five variants, and moved to M18. This branch is **not merged**. It is kept as
the record and the starting point.

## 1. What was asked

D-169 (on this branch), ruled by the owner:
- **What gets the note.** Input that is not a search for a model gets a guiding note instead of a
  ranking. That means an attempt to instruct the model, chit-chat or nonsense, an everyday trivia
  question, or a request to act on content pasted in.
- **Where the line sits.** The owner drew it during this work. A task or question inside an area a
  surface measures is a model search, even when it is written as the task itself: "fix a bug in my
  python repo", "what is the weather in Berlin today".
- **The acceptance measure.** On every genuine search, at most 2 false positives per run, and at
  least 80 % caught.

## 2. The sets

- **Tuning (147 questions).**
  - The existing `offtopic_questions.json`, `offtopic_heldout_questions.json` and
    `nonsense_questions.json`, relabelled to the owner's line.
  - The author's `notasearch_tuning_questions.json` (16: injections, Turkish input, pasted content).
  - The genuine sets `probe_questions.json`, `heldout_questions.json` and
    `refinement_heldout_questions.json`.
  - That gives 39 exactly not-a-search, 19 honestly ambiguous (either answer accepted) and 89 genuine.
- **Held out (80).** `notasearch_heldout_questions.json`, written by an independent agent that never
  saw an instruction, and relabelled by it when the owner drew the line: 40 not-a-search, 36 genuine
  and 4 ambiguous. **It was never run.** No variant passed on the tuning set, so it stays clean for
  M18.

## 3. Five variants, each run once on the tuning set

| variant | injection | pasted content | chit-chat or nonsense | everyday trivia | caught | false positives |
|---|---:|---:|---:|---:|---:|---:|
| 1. a second closed value in the surface field | 0/6 | 0/3 | 3/22 | 0/8 | 3/39 | 1/89 |
| 2. a yes/no field generated before the surface (literal reading) | 2/6 | 2/3 | 10/22 | 6/8 | 20/39 | 27/89 |
| 3. the yes/no field, instructions on the owner's line | 1/6 | 0/3 | 13/22 | 0/8 | 14/39 | 2/89 |
| 4. five named kinds instead of yes/no | 3/6 | 3/3 | 14/22 | 5/8 | 25/39 | 45/89 |
| 5. a separate classifier call first, with examples on both sides | — | — | — | — | 33/39 | 46/89 |

Variant 5 was scored on the totals only. The exact instructions of each variant are on #66.

## 4. What the numbers say

- **One value among the surfaces is almost never chosen.** For nonsense the model picked the
  existing decline instead.
- **Every variant that catches more also cuts genuine searches.** The false positives are the
  product's normal input, the task written as itself:
  - "summarise this 40 page contract pdf for me";
  - "fix a bug in my python repo";
  - "what is the weather in berlin today";
  - "write a short horror story …".

  The small on-device model cannot hold the line between "summarise this PDF" (a need) and
  "summarise this: <text>" (content pasted in). That holds with examples, and with a dedicated
  call.
- **The only variant inside the false-positive bound (3) catches a third, mostly nonsense.** Here the
  owner chose to stop rather than lower the bar.
- **Injection is harmless either way.** The schema admits only declared values (D-126, the M17-W5
  security pass). A missed injection produces a ranking nobody wanted, never text the model wrote.

## 5. For M18

Directions not tried:
- **Structural signals the model is bad at, decided in code and tested:**
  - pasted content: a colon followed by a long text, code, or several lines;
  - text with no word in any language.
- **A stronger model**, where the device offers one.
- **Asking the reader** instead of deciding for them: a one-tap "did you mean to find a model?"

Related: W-123 (M18), where ordinary questions still reach a measured surface.
