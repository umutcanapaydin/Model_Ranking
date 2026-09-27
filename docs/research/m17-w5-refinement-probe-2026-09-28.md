---
record_type: register
id: m17-w5-refinement-probe-2026-09-28
status: ratified
process_version: v6.6
date: 2026-09-28
---
# M17-W5: the on-device model choosing surfaces and refinements, measured

**Measured 2026-09-28** on the owner's Mac, where Apple Intelligence runs
(`SystemLanguageModel.default.availability == .available`). `ModelRouter.route` was called directly,
through a throwaway test target on a copy of the Engine package (never committed). Two versions ran
on the same questions:
- `main` at `c02fe0d`: a one-field schema, the surface;
- this branch: the surface plus one enumerated field per refinement kind (D-168).

**The model is not deterministic.** Two runs of the same questions agree on 35 of 43 surfaces, so
every figure here is from at least two runs and is given as a range. Issue #64.

## 1. The question sets

- **Surface probe:** `scripts/router_probe/probe_questions.json` (21, the tuning set) and
  `heldout_questions.json` (22), the wording tier's existing sets (D-147).
- **Refinement set 1:** 45 questions, 12 in Turkish, written by an independent agent that saw only
  a description of the surfaces and refinement values, never the table or its reasons (D-147
  clause 5). **It was used to decide the change in §3, so it is not the final measure.**
- **Refinement set 2:** 40 NEW questions, 17 in Turkish, 17 needing no refinement at all, written by a
  second independent agent after that decision. §4 is measured on it alone.

## 2. Surfaces: the richer schema routes better

| router | surface probe (43) |
|---|---:|
| `main`, one field | 20 |
| branch with surface, language, domain and kind | 30-34 |
| branch as merged: surface, language and domain | 27-29 |

`main`'s on-device tier sent most questions to `assistant` or `agentic-coding`. The branch's object
schema, whose field descriptions say what each field is, chooses the surface correctly more often
on both the tuning and the held-out questions.

**Regressions to know about.** Three questions that should be declined as unmeasured went to
`vision` in some runs:
- "make my profile photo look better";
- "turn this photo into a cartoon";
- "transcribe this voice memo".

A sentence in the instructions saying that `vision` measures understanding an image, not editing it,
was tried on the tuning question only. It did not move the image questions, and the total fell in
that run, so it was not kept. The decline tier for image editing is an open weakness of the
on-device tier.

## 3. The decision the first set informed

On set 1, with 32 refinements (languages including English, domains, and kinds of conversation and
image task):
- the language was right on 38-41 of 45 questions;
- the domain on 35-37;
- the kind on only 23-24;
- 21-25 refinements were added where none was expected.

**Two sources of error:**
- **English as a task language.** The model read it from the language the question was written in,
  on four English questions.
- **Every kind.** "Long prompt", "instruction following", "long conversation" and "hard prompts"
  were added to most questions (14 of 21 spurious additions in one run). After those four were
  removed, "creative writing" was added to most message-writing requests, and "writing about an
  image" to most image questions.

The first step removed English and the four vague kinds (`9423642`). The owner then ruled, from the
numbers on set 2 in §4, that a refinement is **a language or a domain** (D-168 note).

## 4. The final measurement, on set 2 (40 questions)

**With kinds as they stood (27 entries):**
- all refinements right on 18-20 of 40 questions;
- 14-15 spurious additions;
- 10-11 of the 17 questions needing none stayed clean.

**As merged, with languages and domains only (16 entries):**

| | run 1 | run 2 |
|---|---:|---:|
| surface right | 28 | 28 |
| language right | 37 | 37 |
| domain right | 34 | 35 |
| both refinements right | 31 | 33 |
| spurious additions | 4 | 5 |
| missed refinements | 5 | 3 |
| questions needing none that stayed clean (of 19) | 15 | 16 |
| Turkish questions with the right task language (of 18) | 16 | 16 |

**The task-language rule holds on the device.**
- Turkish questions about a task in no listed language got no language board in all but two cases.
- Turkish questions naming one ("Lehçe e-posta", "Rusça konuş") got it.

**The residual spurious additions come from tricky wording.**
- "my german shepherd barks all night" added German.
- "a nice way to say no to a wedding invite" added entertainment.

## 5. What the combined lists would hold

Run 1's choices were applied to the live `/v1/boards` payload (release `cce2ced`, 2026-09-28): the
surface's primary board plus its refinements, keeping only the models every chosen board ranks
(D-167 clause 3, #54 as ruled).
- **Combined lists:** 14 of the 40 questions select more than one board.
- **Their sizes:** from **32 to 188 models**, median **107**.
- **Why they stay large:** the language and domain slices are Arena text slices ranking 136 or more
  models, so the 3-model lists #54 measured for three small boards do not arise with this table.
- **The smallest lists:** 32 to 34 models, when a question routes to `document`, whose own board
  ranks 34.

## Method, re-runnable

- **Harness.** An XCTest in a copy of `ios/Package.swift` and `ios/ModelRanking/` calls
  `ModelRouter().route(q, within: served)` for each question and writes the surface and each
  refinement value.
- **Where it runs.** Only on a Mac with Apple Intelligence enabled; elsewhere the availability check
  returns before any call.
- **Scoring.** An expected value `a|b` accepts either. `DECLINE` expects `unmeasured`.
- **List sizes.** Computed from `GET /v1/boards` with `CATEGORIES[surface].primary_source` and the
  table's boards.
