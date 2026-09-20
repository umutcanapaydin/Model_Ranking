---
record_type: wave
id: m14-wave-2-close
status: draft
process_version: v5.0
date: 2026-09-20
---
# Wave-Close Checklist — M14 Wave 2 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**Two surfaces from the boards we already license.** `document` ("Working with documents") and
`factuality` ("Getting facts right"), fed by two more configs of the LMArena dataset the product
already reads under CC-BY-4.0. Both answer all three budgets on the live artifact; the nine existing
surfaces' answers are unchanged.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m14-plan.md` §2 W2 "(risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first on the review's decisive mutant: with `ingest_arena`'s lookup replaced by the text label, `test_ingest_stores_each_board_under_its_own_benchmark` fails; restored, `908 passed, 13 skipped` | ✅ |
| 3 | Review per tier: HIGH → Code-Reviewer + Tester separately | Code-Reviewer: `docs/reviews/m14-wave-2-review.md` (`seat: independent`), 5 MAJOR / 9 MINOR, all dispositioned. **Tester seat not convened — NO-ENVIRONMENT for an independent Tester on 2026-09-20; ledger L1** | WAIVED |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | **WAIVED 2026-09-20 — ledger L2.** The slice is `src/app/clients/arena.py` + `src/app/workflows/ingest.py`: an unauthenticated public dataset read through the existing capped client, no auth, PII, payment, crypto or migration | WAIVED |
| 5 | Tester fault-injection: break → RED → reverted | By the author on a copy of `src/app/workflows/ingest.py`: the review's MAJOR-1 mutant now dies on the named test; the seat's own mutants (fourth board sharing an id; class-level name) are covered by `test_each_board_carries_its_own_source_id_and_benchmark` | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-SRC-011 → `tests/unit/test_arena_client.py::test_ingest_stores_each_board_under_its_own_benchmark` (through `ingest_arena`); REQ-SUR-001 → `tests/unit/test_categories.py::test_the_two_board_surfaces_rank_only_their_own_board`; both in `docs/prd.md` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None new. The board-isolation invariant's negative half is `test_ingest_refuses_a_source_no_board_claims` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; mutants ran on copies of `src/app/workflows/ingest.py`. No commit made — L3 | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | One board = one source id = one benchmark label. Producers: `ARENA_BOARDS`, `ArenaClient.__init__`, `parse_arena(benchmark=)`, `RemoteSource` name ↔ client name, `ingest_arena` — each now cited (`docs/reviews/m14-wave-2-review.md` producer table; the ingest gap closed) | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Planned (re-planned after W1): `document` and `factuality`. Delivered: both, with calibration record `docs/reviews/m14-category-calibration.md`. Deferred: `search_factuality` (retrieval-SKU pricing, `docs/plans/m14-plan.md` §2 W2); per-source carry-forward (D-144 ruling) to M15 | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | **VARIANCE:** ~520 lines across `src/app/clients/arena.py`, `src/app/workflows/categories.py`, tests and Swift; about a third is the review round. Not split after review | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: pytest 908 passed / 13 skipped, ruff check, check_records, wave_check_all · Swift and the full make check: run by the owner's runner after this record, see L4 · outcome: uncommitted, unsigned` | WAIVED |

## Ledger rows

- **L1 — Tester seat not convened.** The Code-Reviewer seat was independent and found five MAJOR;
  a separate Tester was not run. Owning milestone: M14 closure (Stage 4.0 covers the milestone).
- **L2 — pulled-forward security pass not run** (V3C-78; D-141 still awaiting the owner).
- **L3 — no commit.** The owner makes the commits; `note.txt` carries the prepared sequence.
- **L4 — Swift not run by the author.** Three Swift test files and two Swift source files changed
  (id lists, hints, Turkish titles). The owner's `make check` through the runner is the measurement.

Filled by: lead agent (Claude Code, cloud lane, D-117) · Date: 2026-09-20 · Wave commit range:
`c0b71c6..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        src/app/clients/arena.py · src/app/workflows/{ingest,sources,rank,categories}.py
                scripts/calibrate_board.py (new) · scripts/refresh_job.sh (new)
                ios/ModelRanking/Engine/{Router,Language}.swift
                ios/EngineTests/{FrontDoorTests,RouterBoundaryTests,OwnerSessionDefectTests,
                LanguageTests}.swift
                tests/unit/{test_arena_client,test_sources,test_categories,test_category_titles}.py
                docs/{decisions,prd,warnings.ledger}.md · docs/reviews/m14-* · deploy/*.plist

K.8 contracts:  `/v1/categories` gains two ids (additive; no existing id moved). `scores.source`
                gains `arena_document`, `arena_factuality`; `arena` unchanged. The refresh job's
                plist now runs `~/Library/Application Support/model-ranking/refresh_job.sh` and logs
                to `~/Library/Logs` (W-096).
```
