---
record_type: plan
id: issue-73-plan
status: draft
process_version: v6.6
date: 2026-09-28
---
# Issue #73 plan — coding questions reach the coding surface

**Stopped 2026-09-29 by the owner's ruling, not merged, moved to M18.** Variant 3 reached 22–23 of
40 on the held-out set (target 28). See `docs/research/issue-73-coding-routing-probe-2026-09-28.md`.

**Working plan for `fix/issue-73-coding-routing`**, deleted before merge. Triage verdict: `work-issue`,
so the owner rules each decision. Risk: **MED**. The change is wording the on-device model reads: the
surface descriptions in `CategoryHints.byID` and one sentence of its instructions. The schema,
`ModelOutputBoundary` and every D-126 gate stay as they are. The wording tier routes on its own
examples and is untouched (`tests/unit/test_router_hints.py`, the M15-W3 note).

## The problem, measured (the reproduction)

On an independent set of 80 questions, `main` sends coding questions elsewhere:

| | run 1 | run 2 |
|---|---:|---:|
| to `coding` | 10/40 | 8/40 |
| to `coding` or `agentic-coding` | 17/40 | 13/40 |

The rest go to:
- `document`: 7–11
- `agentic-coding`: 5–7
- `web-dev`: 4–6
- `computer-use`: 3–7

Web-dev and document questions are already right: 16/16 and 15/16. Only `task=coding` shows Ruling A's
two answers, so the target is `coding` itself.

The model's routing cannot be reproduced in the suite, so the reproduction is this measurement. It is
recorded before any change, in
`docs/research/issue-73-coding-routing-probe-2026-09-28.md`, with both question sets committed.

## Ruled by the owner, 2026-09-28 (translated from Turkish)

1. **Improve the routing:** the instructions and the surface descriptions separate coding from web
   development and document work. The change is measured at least twice on an independent set, and
   the general sets are measured too.
2. **The acceptance measure, in both runs:**
   - at least **28/40** coding questions reach `coding`;
   - web-dev stays at least **15/16**, and document at least **14/16**;
   - the general sets stay inside today's ranges: the surface probe at 25/43 or more, and the
     held-out refinement set's surfaces at 26/40 or more.
3. **Three variants.** If none meets the measure on the tuning set, the work stops and goes back to
   the owner, as #66 did.

## Sets (D-147 clause 5)

- **Tuning:** `scripts/router_probe/coding_tuning_questions.json` (24, the author's) and the existing
  genuine sets.
- **Held out:** `scripts/router_probe/coding_heldout_questions.json` (80), written by an independent
  agent that never saw the descriptions' new wording. Its only use is the final measure.

## Phases

- **P0.** This plan, then the reproduction commit: both sets and the baseline record.
- **P1.** The descriptions and the instruction sentence, tuned on the tuning set (at most three
  variants).
- **P2.** The final measure: the chosen variant, twice on the held-out and general sets, added to the
  record.
- **P3.** The fresh-eyes Tester alone (`docs/reviews/fix-issue-73-tester.md`), then `make gate` and
  `/pre-merge`. Only then does the draft pull request open (owner rule).

## Out of scope

- #66: a question that is not a model search (moved to M18).
- The wording tier's examples.
- Any schema or boundary change.
