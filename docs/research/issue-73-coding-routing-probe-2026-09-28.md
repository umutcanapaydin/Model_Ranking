---
record_type: register
id: issue-73-coding-routing-probe-2026-09-28
status: ratified
process_version: v6.6
date: 2026-09-28
---
# Issue #73: where the on-device model sends coding questions, measured

**Measured 2026-09-28** on the owner's Mac (Apple Intelligence available), through
`scripts/router_probe/RefinementProbe.swift` in a scratch copy of `ios/`. Every configuration ran at
least twice, because the model is not deterministic. Issue #73. Plan:
`docs/plans/issue-73-plan.md` (deleted before merge).

## 1. The sets (D-147 clause 5)

- **Held out:** `scripts/router_probe/coding_heldout_questions.json`, 80 questions, half in Turkish.
  An independent agent wrote them from the surface list and the problem statement. It never saw the
  new wording. The set contains:
  - 40 coding questions: 20 plain, 12 that mention web things (a Django ORM bug, a failing Express
    test, a CORS error) and 8 that mention files or documents (parse a CSV, an awk one-liner on a
    log, a PDF library failing);
  - 16 web-development questions;
  - 16 document questions, including technical documents that are not coding;
  - 8 questions near coding that belong elsewhere.
- **Tuning:** `scripts/router_probe/coding_tuning_questions.json` (24, the author's) and the existing
  genuine sets (`probe_questions.json`, `heldout_questions.json`,
  `refinement_heldout_questions.json`).

## 2. The reproduction: `main` at 3f2e91d

| held-out group | run 1 | run 2 |
|---|---:|---:|
| coding (20) | 9 | 7 |
| coding, near web (12) | 1 | 1 |
| coding, near documents (8) | 0 | 0 |
| web-dev (16) | 16 | 16 |
| document (16) | 15 | 15 |
| other (8) | 7 | 7 |

**Coding questions that reach `coding`:** 10 and 8 of 40. With `agentic-coding` counted too, 17 and
13. Only `task=coding` shows Ruling A's two answers (`src/app/adapter/main.py`, `CODING_INTENT`).

**Where the rest went:**
- `document`: 11 and 7
- `agentic-coding`: 7 and 5
- `web-dev`: 4 and 6
- `computer-use`: 3 and 7
- search, factuality, assistant, everyday and vision: the remainder

The tuning set tells the same story: its 24 questions scored 16 and 20.

## 3. Three variants on the tuning set, each run twice

| variant | coding tuning (24) | surface probe (43) | refinement set surfaces (40) |
|---|---:|---:|---:|
| `main` (baseline) | 16, 20 | 27, 28 | 30, 30 |
| 1. coding, agentic-coding and computer-use descriptions, and the instruction sentence | 22, 22 | 29, 30 | 26, 28 |
| 2. the coding description and the sentence only | 23, 21 | 27, 25 | 28, 27 |
| 3. coding and computer-use descriptions, and the sentence (committed, `cc70ce8`) | 23, 21 | 28, 29 | 29, 30 |

**Why variant 3.** Variant 1's new agentic-coding wording ("it plans … opens a pull request") pulled a
question about making up with a friend ("how do I take the first step") into `agentic-coding` in both
runs. Variant 2 put the surface probe at the bar (25).

## 4. The held-out measure, variant 3, twice

| held-out group | run 1 | run 2 | `main` |
|---|---:|---:|---:|
| coding (20) | 13 | 13 | 9, 7 |
| coding, near web (12) | 9 | 7 | 1, 1 |
| coding, near documents (8) | 1 | 2 | 0, 0 |
| web-dev (16) | 16 | 16 | 16, 16 |
| document (16) | 14 | 15 | 15, 15 |
| other (8) | 7 | 8 | 7, 7 |

**Coding questions reaching `coding`:** 23 and 22 of 40, against 10 and 8 on `main`. **The owner's
target was 28**, so the measure was not met.

**The rest went to:**
- `document`: 5 in both runs
- `web-dev`: 4 and 7
- `agentic-coding`: 4 and 3
- `computer-use`, `search`: 1 or 2 each

The weakest group is coding that mentions a file, a log or a PDF (1 and 2 of 8).

## 5. Ruling and state

**Owner ruling, 2026-09-29** *(translated from Turkish)*: variant 3 is **not merged**. The whole of
#73 moves to M18, beside #66: both are limits of the on-device model reading a question.

This branch keeps variant 3 and this record as the starting point. The held-out set has now been
run, for the final measure only; M18 should write a fresh one before tuning against this one.
