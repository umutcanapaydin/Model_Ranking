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

On the wave's own 37 sentences (a fix commit's message says 12; the run says 11) (the wording tier, `own-sentences-*.json`), 11 fell to "not measured"
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
