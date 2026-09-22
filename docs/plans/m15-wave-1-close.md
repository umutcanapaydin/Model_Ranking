---
record_type: wave
id: m15-wave-1-close
status: draft
process_version: v5.0
date: 2026-09-22
---
# Wave-Close Checklist — M15 Wave 1, what we can answer, measured (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**All 22 boards of the licensed dataset, measured on one footing.** Distinct models, the ranked
population (reconciled AND priced), leader, spread and the floor under both candidate rules, one
table from one script. It answered W-094 (the owner then ruled D-148) and chose W3's three surfaces.
Nothing in this wave reaches a reader.

**This record is written at M15-W4, after the wave was committed (`17e6554`).** The wave closed
without one; its review ran afterwards and is cited below. Stated rather than back-dated.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m15-plan.md` §2 W1 "(risk: **MED**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | `scripts/survey_boards.py` run against a throwaway copy of `advisor.db`; raw runs kept outside the tree (`terminal_output/model_ranking/m15-runs/`). No test file: the wave ships a measurement script and a record, not product code | ✅ |
| 3 | Review per tier: MED → independent Code-Reviewer | `docs/reviews/m15-wave-1-review.md` (`seat: independent`, 2026-09-22): **PASS WITH FINDINGS**, 0 BLOCKING / 2 MAJOR / 6 MINOR. The seat recomputed every cell of the W-094 table with its own queries: every floor value is right; three statements were not | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass | Not owed: MED tier (D-141 binds HIGH waves). The script reads a copy and writes nothing to the artifact, which the Stage 4.0 seat re-checked (`docs/reviews/m15-closure-security-review.md` §0) | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | No mutants: a measurement record has no gate to turn red. Its equivalent is independent recomputation, which row 3's seat did for all eleven W-094 rows (`docs/reviews/m15-wave-1-review.md` "W-094 table") | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | The wave's output is a record the owner rules from (plan §2 W1), not a criterion. The one number that later became a shipped threshold is pinned where it ships: `PINNED_SCORE_ANCHORS` in `tests/unit/test_uncertainty_contract.py` (W3) | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None changed: `git show --stat 17e6554` touches no file under `src/`, `ios/` or `tests/` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; the script writes only to a temporary copy (`scripts/survey_boards.py` `--db` help: "read-only; every write goes to a copy") | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | The ranked count comes from the engine's own `ranked_population` (REQ-EVI-002), called after `_store_scores` and `reconcile` on a copy; no query of the script's own | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: the 22-board table, W-094's measurement, the retrieval-pricing answer, W3's shortlist. **Not done in W1:** the gap register's first read, owed by plan §2 W1 — done at W4 (`docs/research/m15-gap-register-first-read.md`). Deferred with a record: a script mode reproducing all eleven W-094 rows (review M-2), to M16 with the D-148 re-derivation | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | `17e6554`: two files, the script and its record | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: the survey on a throwaway copy; the independent recomputation (row 3) · outcome: committed 17e6554, record corrected 2026-09-22 (8640202)` | ✅ |

## What the review changed

- **M-1 (the wrong rule named as shipped).** The M8 floors are the top third of the board's ROWS,
  not of distinct models. Corrected in the record's appended section, and the owner then ruled the
  ROWS count for every surface (D-148 clause 1).
- **M-2 (8 of 11 rows not reproducible by the script).** Owed with the M16 re-derivation.
- **m-1, m-2, m-3** (style-control gaps, `agentic-coding`'s pooled efforts, "nine of eleven")
  corrected in the record. **m-4, m-5** fixed in `scripts/survey_boards.py` at `8640202`.
  **m-6** (private engine internals) left as is; the script says what it borrows.

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-22 · Wave commit range:
`855b44a..17e6554`, record corrected in `8640202`

## Wave footprint — RECORD ONLY

```
Touched:        scripts/survey_boards.py (new) · docs/research/m15-board-survey-2026-09-21.md (new)
K.8 contracts:  none. Nothing served changed.
```
