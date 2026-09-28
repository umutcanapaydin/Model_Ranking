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
