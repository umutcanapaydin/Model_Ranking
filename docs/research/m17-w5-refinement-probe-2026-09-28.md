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
every figure for this branch is from at least two runs and is given as a range. `main`'s figure is
from one run; two identical runs of the shipped branch differ by 5 (25 and 30). Issue #64.

## 1. The question sets

- **Surface probe:** `scripts/router_probe/probe_questions.json` (21, the tuning set) and
  `heldout_questions.json` (22), the wording tier's existing sets (D-147).
- **Refinement set 1:** 45 questions, 12 in Turkish, written by an independent agent that saw only
  a description of the surfaces and refinement values, never the table or its reasons (D-147
  clause 5). **It was used to decide the change in §3, so it is not the final measure.**
- **Refinement set 2:** 40 NEW questions, 17 in Turkish, written by a second independent agent after
  that decision. §4 is measured on it alone. 19 of them need neither a language nor a domain; under
  the ruling that coding takes no refinement (§4), 21 do.

Both sets are committed as `scripts/router_probe/refinement_questions.json` and
`refinement_heldout_questions.json`, verbatim, so a later change knows what it must not tune against
(D-147 clause 5).

## 2. Surfaces: the richer schema routes better

| router | surface probe (43) |
|---|---:|
| `main`, one field | 20 |
| branch with surface, language, domain and kind | 30-34 |
| branch with surface, language and domain | 27-29 |
| as shipped: the same, with the reworded decline instructions (§4) | 25-30 |

`main`'s on-device tier sent most questions to `assistant` or `agentic-coding`. The branch's object
schema, whose field descriptions say what each field is, chooses the surface correctly more often.
As shipped, the gain is on the held-out questions: 12 and 16 of 22, against `main`'s 7. On the 21
tuning questions it scores 13 and 14, against `main`'s 13. With the kind field still in the
schema, the gain showed on both sets.

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

**As shipped** (corrected at the code review, M2):
- languages and domains only (16 entries);
- the instructions no longer decline medical or legal questions (owner ruling 2026-09-28, D-168
  review note 5);
- `software` no longer refines `coding` (review B2, owner ruling). The set's two coding questions
  expected `software`, and are scored as expecting none.

| | run 1 | run 2 |
|---|---:|---:|
| surface right | 26 | 28 |
| language right | 37 | 37 |
| domain right | 34 | 35 |
| both refinements right | 31 | 32 |
| spurious additions | 6 | 4 |
| missed refinements | 3 | 4 |
| questions needing none that stayed clean (of 21) | 16 | 18 |
| Turkish questions with the right task language (of 17) | 15 | 15 |

**The decline wording changed nothing measurable.** The same two runs before it (with the coding
ruling applied) scored 28 and 28 on surfaces, 33 and 33 on both refinements, 4 and 6 spurious
additions, and 17 of 21 clean. The medical and legal questions were answered with their domain both
before and after: the model had not followed the decline sentence. On the surface probe the new
wording scored 25 and 30 of 43, against 27 and 29 before it.

**The task-language rule holds on the device.**
- Turkish questions about a task in no listed language got no language board in all but two cases.
- Turkish questions naming one (a Polish email, a request to converse in Russian) got it, except a
  Spanish birthday poem, which got no language in either run. It is one of the two misses in the
  15 of 17.

**The residual spurious additions come from tricky wording.**
- "my german shepherd barks all night" added German.
- "a nice way to say no to a wedding invite" added entertainment.

## 5. What the combined lists would hold

Each shipped run's choices were applied to the live `/v1/boards` payload (release `cce2ced`,
2026-09-28): the surface's primary board plus its refinements, keeping only the models every chosen
board ranks (D-167 clause 3, #54 as ruled).
- **Combined lists:** 15 and 12 of the 40 questions select more than one board.
- **Their sizes:** from **32 to 189 models**, median **98** in both runs. (The first version of this
  record gave a median of 107 for 14 lists; the code review recomputed 102.5 from those lists, M2.)
- **Why they stay large:** the language and domain slices are Arena text slices ranking 136 or more
  models, so the 3-model lists #54 measured for three small boards do not arise with this table.
- **The smallest lists:** 32 to 34 models, when a question routes to `document`, whose own board
  ranks 34.

## Method, re-runnable

- **Harness.** `scripts/router_probe/RefinementProbe.swift`, an XCTest run in a scratch copy of
  `ios/`: it calls `ModelRouter().route(q, within: served)` for each question and writes the surface
  and each refinement value. Its header says how to run it.
- **Where it runs.** Only on a Mac with Apple Intelligence enabled. Elsewhere it fails and says the
  model is unavailable, rather than writing rows of `nil`.
- **Scoring.**
  - An expected value `a|b` accepts either. `DECLINE` expects `unmeasured`.
  - "Both refinements right" means the language and the domain both match.
  - A spurious addition is a value where none of the expected values was chosen, and a missed one is
    `none` where a value was expected.
  - A Turkish question is one written in Turkish, not one naming a Turkish place.
  - The sets' `kind` column is ignored since kinds were withdrawn.
- **List sizes.** Computed from `GET /v1/boards` with `CATEGORIES[surface].primary_source` and the
  table's boards.
