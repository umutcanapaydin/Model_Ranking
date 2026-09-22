---
record_type: review
id: m16-router-floor-measurement
status: ratified
seat: author
date: 2026-09-22
---
# M16-W1 — the router's floor, re-measured under D-147, and what actually moved

**Owed by W-118** (M15-W3 independent review, MAJOR-1): D-147 changed how a surface scores a
question, and `SimilarityRouter.defaultFloor = 0.15` kept a justification measured before that
change — nine hints of one sentence each. The seat showed nonsense scoring 0.196–0.235, above the
floor, and "what time is it" routing to `vision` at 0.548 with `unmeasured` false. This record is
the re-measurement. **Seat: author.** It measures; it does not review itself.

## The five sets, and when each was written

| Set | Size | Written | Used for |
|---|---|---|---|
| `probe_questions.json` | 21 | M15-W3 (D-147) | the tuning set of the original recalibration |
| `heldout_questions.json` | 22 | M15-W3, before any change | generalisation, never tuned against |
| `nonsense_questions.json` | 16 | M16-W1, **before this change** | what the floor is for: input that means nothing |
| `offtopic_questions.json` | 16 | M16-W1, **before this change** | ordinary questions with no measured surface |
| `offtopic_heldout_questions.json` | 16 | M16-W1, **before this change, and not read until the end** | the off-topic fix on questions not tuned against -- within the same distribution, see below |

The two off-topic sets were written at the same time and neither was opened while the examples were
being changed except the first; the held-out one was measured once, at the end.

**Four labels in the off-topic tuning set (`offtopic_questions.json`, not `probe_questions.json`) were corrected before re-measuring, and it is stated here rather
than buried:** `is it going to rain tomorrow`, `how much does a tesla cost` and
`recommend a good pizza place` accept `search` (a question about current facts is what that surface
is for), and `explain quantum entanglement to me` accepts `expert`. Those answers are right; the
first labels were the author's guess. The held-out set's labels were not touched. The three M16-W1 sets were untracked when this was
written, so the relabelling has no before-state in git; the independent seat checked it by
sensitivity instead (every off-topic tuning label forced to `assistant|everyday~` gives 3/16 → 7/16),
so the 6/16 → 11/16 below is not its artefact.

## What was changed

Nothing but example questions — no threshold, no scoring, no code path.

- **`assistant` got three general examples** (a general-knowledge question, a household how-to,
  and a greeting-shaped opener) in place of `give me advice on asking for a raise`,
  `rewrite this paragraph to sound friendlier` and `chat with me about my weekend plans`.
  There was no home for an ordinary question, so ordinary questions went to whatever surface had
  the shortest question-shaped examples.
- **`vision`'s six examples now name the image** ("what is in this picture **i uploaded**",
  "what does this chart **in the image** show", "explain the diagram **in this image**"; four of
  six changed; `describe this photo` and `read the text in this screenshot` did not). They were
  question-shaped sentences that any short question resembled, which is why `what time is it`
  scored 0.548 there.

## The measurement

Every cell is `correct / total`, run with `scripts/router_probe/probe.swift` (top2 mode, the
router's own scoring) against the examples extracted from `Router.swift` at each tree.

| Set | Before | After | Before @0.20 | After @0.20 |
|---|---|---|---|---|
| probe (21) | 21/21 | **21/21** | 21/21 | 21/21 |
| held-out (22) | 18/22 | **18/22** | 18/22 | 18/22 |
| nonsense (16) | 12/16 | 12/16 | 12/16 | 12/16 |
| off-topic, tuning (16) | 6/16 | **11/16** | 6/16 | 11/16 |
| off-topic, held out (16) | 3/16 | **8/16** | 3/16 | 8/16 |

**The floor does not move, and the measurement is why.** The lowest score of any CORRECT route
across the probe and held-out sets is 0.232; nonsense scores 0.161–0.395. The ranges overlap, so no
value of the floor separates them: 0.15 and 0.20 give the identical answer on all 86 questions,
question by question, and 0.30 would decline four correct routes to catch three nonsense strings.
A floor is the right control for "resembles nothing at all" and it cannot be made into a control
for "resembles the wrong thing".

**What the floor does still do:** it is the one thing standing between a Turkish sentence embedded
as English and a confident route (the comment above `defaultFloor` in `Router.swift`), and the
independent seat's earlier finding stands — a test must exercise both sides of it.

## What is still wrong, measured

- **Nonsense is declined 12 times in 16, and never by the floor** — by the decline groups scoring
  higher than any surface. `hjkl hjkl hjkl` still reaches `mathematics` (0.212), `test test`
  `mathematics` (0.242), `123456` `web-dev` (0.229), `qq ww ee rr tt` `everyday` (0.285).
- **Greetings and thanks decline** (`hello`, `good morning`, `thanks`). Counted as misses in the
  table above; arguably the right answer, since neither is a task to recommend a model for.
- **Five off-topic questions still land on a measured surface**, e.g. `what does this word mean in
  english` → `vision` 0.452, `is coffee bad for you` → `search` 0.423.
- Held-out generalisation is unchanged at 18/22, which is where D-147 left it.
- **The off-topic held-out set is not independent in shape from the one tuned against** (M16-W1
  review): `how do i remove a coffee stain` sits beside the new example `how do i get red wine out of
  a carpet`, `good morning`/`thanks` beside `hi can you help me with something`, `who wrote the
  odyssey` beside `what is the tallest mountain in the world`. 3/16 → 8/16 is a within-distribution
  measure, not an out-of-sample one. W-123 carries the real test to M16-W4, against public prompt
  corpora the author did not write.

## What this does not claim

It does not claim the router is right, only that it is measurably less wrong on ordinary questions
and unchanged on everything measured before. It measures wording similarity on a Mac, not the
on-device tier order, and the router's speed on a phone is still unmeasured (D-147's open cost).
