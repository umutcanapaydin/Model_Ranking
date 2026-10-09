---
record_type: register
id: m21-w2-reading-probe
status: draft
process_version: v6.6
date: 2026-10-09
---
# M21-W2: reading what is not a search, measured on M20-W5's held-out set (#66, #222, #194, #218)

**Measured 2026-10-09** on the owner's Mac, where Apple Intelligence runs, through
`scripts/router_probe/ReadingProbe.swift` in scratch copies of `ios/`:
- **before:** `closure/m20` at `972b55e`;
- **after:** `wave/m21-w2` at `460b7cd`.

Each copy ran the model tier twice and the wording tier (`PROBE_TIER=wording`) twice. The runs and the
scorer (`score_w2.py`, counts only) are in `docs/research/m21-w2-runs/`.

## 1. The set

`scripts/router_probe/wording_heldout_m20_questions.json`, written for #195 by an independent seat, is
still unread by the author. It holds 78 questions (39 English, 39 Turkish): 71 searches and 7 that are
not a search.
- **Tuning for this wave:** only sentences the wave wrote itself (`own_sentences_tuning.json`, 37) and
  the existing tuning sets.
- **Measured a second time.** M20-W5 measured the set once, and this wave measured it again. It is
  spent. Its retirement waits on a fresh set, because the held-out gate needs one live set (§5).

## 2. Results

A row is right when it is a search, measured, and on a surface its label allows. For a question that
is not a search, it is right when it is not read as a search. "Asked" means the question back.

| tier, run | right (78) | searches not measured (71) | searches asked (71) | searches given the note (71) | non-searches given the note or asked (7) |
|---|---:|---:|---:|---:|---:|
| wording, before 1 and 2 | 44, 44 | 8, 8 | 0, 0 | 0, 0 | 3, 3 |
| wording, after 1 and 2 | 44, 44 | **4, 4** | 0, 0 | 0, 0 | 3, 3 |
| model, before 1 and 2 | 44, 48 | 1, 1 | 4, 4 | 0, 0 | 4, 3 |
| model, after 1 and 2 | 45, 47 | 3, 1 | 5, 3 | 0, 0 | 5, 3 |

On the wave's own 37 sentences (the wording tier, `own-sentences-*.json`), 11 fell to "not measured"
before and none after.

## 3. What it says, issue by issue

- **#222:** on the wording tier, the searches that fall to "not measured" went from 8 to 4 of 71.
  - All 8 before, and all 4 after, are Turkish.
  - The four that moved now go to `everyday`, the general answer. None of their labels allows it, so
    the right count stays 44: each is answered now, but not from the board its label names.
  - Of the four left, one each is a single surface's question, a second-meaning word, a language task
    and a domain question.
  - Reading them to tune would spend the set; a new set should measure the next step.
- **#194:** no search was given the note on either tier. On the model tier 3 to 5 of 71 searches were
  asked, against 4 and 4 before, which is within the model's spread. The issue's sign was "more than 4
  of 40 genuine searches asked"; here it is 3 to 5 of 71.
- **#218:** a question with a Turkish letter or question word no longer reaches the English
  embedding. On the wording tier the Turkish right count is 21 of 39, before and after.
- **#66:** the set has 7 questions that are not a search. The wording tier catches 3 of 7 (2 notes, 1
  question back) before and after. The model tier catches 3 to 5 of 7. Seven questions cannot show
  D-169 clause 6's catch bar (40 of 50). **#66 is carried:** a fresh set of at least 50 non-searches,
  written by an independent seat, is what can close it.

## 4. Not measured here

- **#226's judgement:** that is the owner's (`docs/judgement-sheet.md`).
- **The UI paths of #199:** `make ui-test` ran 18 of 19 under heavy load: the routing came from the
  fixture, and the one failure was `testACardOpensItsEvidence`'s window snapshot timing out in `setUp`.
  Run alone at a lower load, it passed.

## 5. The set's retirement

`tests/unit/test_ios_client_contract.py`'s held-out gates assert that a live held-out set exists. With
this set retired, none would, so the gate stays as it is. The lead's next step is a fresh set from an
independent seat, then this set joins `RETIRED_HELD_OUT`. #222's own text asks the same: "measured on a
new set".

## 6. After the first review's fixes (`docs/reviews/m21-wave-2-review-round-1.md`, M1 to M8)

**Measured again** on the wording tier, twice, at the head after the fixes (`review-wording-1.json`,
`review-wording-2.json`; counts only, the same scorer).

| run | right (78) | searches not measured (71) | given the note | asked | non-searches caught (7) |
|---|---:|---:|---:|---:|---:|
| before (`972b55e`) | 44 | 8 | 0 | 0 | 3 |
| as first fixed (`460b7cd`) | 44 | 4 | 0 | 0 | 3 |
| after the review, run 1 and 2 | 44, 44 | 7, 7 | 0, 0 | 0, 0 | 3, 3 |

- **The review's M4 narrowed #222.** A Turkish ask is general only beside a model, an AI or a task a
  model does, so "which is best for coffee" is no longer answered with a ranking. Of the four held-out
  searches the first rule had moved, three fall back to "not measured". All seven left are Turkish.
- **The one search still moved** goes to `everyday`, which its label does not allow. So D-191's
  revisit condition is met on this set, now 1 of 1 (4 of 4 before the narrowing). D-191 says so and
  ships the rule as measured, for the reason it gives.
- **Own sentences.** Of the wave's own 37, 2 fall to "not measured" after the narrowing
  (`own-sentences-review.json`): the asks that name no task or model.
- **The model tier was not run again.** The review's changes reach it through the fact doubt's model
  names (M1 to M3), and also through clauses 1 and 2, because when the model declines the wording tier
  answers (the second review's M8).
- **The set is spent**, measured three times now. #237 asks for a fresh one from an independent seat,
  and then the set's retirement.

## 7. After the second review's fixes (`docs/reviews/m21-wave-2-review.md`, M1 to M8)

**Measured again** on the wording tier, twice, at `f976da7` (`review2-wording-1.json`,
`review2-wording-2.json`; counts only, the same scorer).

| run | right (78) | searches not measured (71) | given the note | asked | non-searches caught (7) |
|---|---:|---:|---:|---:|---:|
| before (`972b55e`) | 44 | 8 | 0 | 0 | 3 |
| after the first review (`f7efd1e`) | 44 | 7 | 0 | 0 | 3 |
| after the second review, run 1 and 2 | 44, 44 | 8, 8 | 0, 0 | 0, 0 | 3, 3 |

- **All 78 rows are identical to `972b55e`.** The Turkish general ask (#222, D-191 clause 4) is taken
  out, so the one held-out search it still caught is "not measured" again. #222 stays open with this
  state.
- **D-191's former revisit condition** (the general answer given to a search whose label names
  another surface) no longer applies: no rule gives that answer.
- **Own sentences.** Of the wave's own 37, 11 fall to "not measured" (`own-sentences-review2.json`), as
  before the wave.
- **Served names.** The probes route with no served names (`TieredRouter(model: nil)`, as the app does
  before standings are kept). The second reviewer re-ran the wording probe with the served snapshot's
  names (301 models), and none of the 78 rows changed. The model tier was not measured with them.
- **The model tier was not run again,** for the reason in §6.
- **The set is spent.** #237 asks for a fresh set.

## 8. After the Tester: two rules taken out (`docs/reviews/m21-wave-2-tester.md`, D-191)

**What changed.** #194's model names in the fact doubt and #218's Turkish signals before the embedding
were taken out after three verdicts each. Each is back to its `972b55e` state. #206's comparison of
model names stays, reading every ranked family (D-191 clause 1).

**Measured** on the wording tier, twice, at `35a8563` (`final-wording-1.json`, `final-wording-2.json`;
counts only, the same scorer):

| run | right (78) | searches not measured (71) | given the note | asked | non-searches caught (7) |
|---|---:|---:|---:|---:|---:|
| before (`972b55e`) | 44 | 8 | 0 | 0 | 3 |
| at `35a8563`, run 1 and 2 | 44, 44 | 8, 8 | 0, 0 | 0, 0 | 3, 3 |

- **All 78 rows read as at `972b55e`.** The kept comparison rule moves none of them.
- **#194, #218 and #222 stay open** with this state: 8 of 71 held-out searches not measured, all
  Turkish.
- **The served names and the model tier** are as §7 says. The served names no longer exist in the app.

