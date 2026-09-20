---
record_type: review
id: m14-wave-2-review
status: ratified
seat: independent
date: 2026-09-20
---
# M14-W2 — Code-Reviewer seat

**How this record was produced.** A separate session with no authoring context, on Claude Opus 5
(the author's family, so no cross-family check was possible — V4C-03/04). Policy read from the base
tree: `subagent-profiles/Code-Reviewer.md`, `docs/plans/m14-plan.md`, `AGENTS.md` §3/§5,
`docs/decisions.md` D-105/D-121/D-142/D-144, `docs/warnings.ledger.md` W-094. It read the 509-line
diff, ran the 905-test suite, ruff, mypy, `check_records.py`, `wave_check_all.py`,
`conformance_gate.py`, compared `recommend()` for every surface and budget on a copy of the live
artifact against a `patch -R` pre-wave tree, and ran mutants on a full copy. Swift was read, not run.

**Verdict: PASS-WITH-FINDINGS.** No BLOCKING. Five MAJOR, nine MINOR, three NIT.

## Findings and disposition

| # | Finding | Disposition |
|---|---|---|
| MAJOR-1 | The ingest line that keeps boards apart had no test: replacing it with the text label merged `document` into `assistant` (Claude Opus 5 at 1516.3 became the chat leader) and 905 tests stayed green. The `getattr` fallback also defaulted any source without a label to the text board | **FIXED.** `ingest_arena` looks the label up from `ARENA_BOARDS` by source id and refuses an unregistered one. `test_ingest_stores_each_board_under_its_own_benchmark` goes through the real entry point and kills the mutant; `test_ingest_refuses_a_source_no_board_claims` pins the refusal |
| MAJOR-2 | The thresholds cited an owner ruling ("A") that no base record contained, and W-094 still said a decision was pending | **FIXED.** D-145 records the ruling; W-094 carries its M14 disposition |
| MAJOR-3 | 1468.0 / 1451.0 matched neither definition of "board third"; "admits 32" was 31; the cited script could not produce a board-third floor | **FIXED.** One rule — top third of the whole board over distinct models — gives **1467.5** and **1450.6**, now in the code; admits 10 of 29 and 32 of 59, verified. `calibrate_board.py` prints `board_third_D145`, so the shipped number is reproduced by the script. Record: `docs/reviews/m14-category-calibration.md` |
| MAJOR-4 | The new router hints were never exercised: every Swift routing test passed a hard-coded nine-id list, and the router centres on the mean over the ids it is given; the Turkish-name test was not extended | **FIXED in code, verified by the owner's `make check`.** All three Swift id lists are now the eleven served ids; the Turkish-name test covers eleven. Hints reworded away from their neighbours ("report" removed; nothing that reads as a general question). The routing tests over eleven ids ARE the re-run of the M10 probe |
| MAJOR-5 | No REQ-IDs and no citing tests | **FIXED.** REQ-SRC-011 and REQ-SUR-001 in `docs/prd.md`, each cited by a named test |
| m1 | The board-uniqueness test checked three hand-picked clients, not the table | **FIXED** — iterates `ARENA_BOARDS` |
| m2 | `ArenaBoard.minimum_rows` was never read | **FIXED** — `sources.py` reads it; one source of truth |
| m3 | Subclasses reported `arena` at class level | **FIXED** — each declares its own `name`, tested at class and instance level |
| m4 | A test still called D-144 "proposed" | **FIXED** |
| m5 | No licence record for the new configs | **ACCEPTED** — the grant is dataset-level and recorded at D-101; the plan's §4 wording is amended rather than a duplicate review written |
| m6 | Registry drift for 8 unmatched models not accounted for | **ACCEPTED** — none carries a price, so a rule would be dead code by the table's own standard; listed in the calibration record |
| m7 | `document` at `low` budget is degenerate (one model holds all three picks and nothing clears the floor) | **ACCEPTED** — disclosed by the engine's own warning, as on `agentic-coding` |
| m8 | `close_call` uses a new rule | **ACCEPTED, stated** in `categories.py` and the calibration record |
| m9 | More optional sources raise the chance D-128 refuses a whole cycle | **ACCEPTED** — the owner's D-144 ruling (per-source carry-forward) is the remedy, scheduled for M15 |
| NITs | formatting-only edits; close titles in both languages; dataset-level citation | noted; titles judged sound by the seat |

## What held
`category_ranking` joins on benchmark and metric, and the live artifact carries three distinct labels
with no leak either way. A missing new source makes its surface disclose rather than answer (D-121).
Attribution is served. The nine existing surfaces' answers were identical before and after the wave
on the same database.
