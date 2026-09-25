---
record_type: wave
id: m17-wave-3-close
status: draft
process_version: v6.6
date: 2026-09-25
---
# Wave-Close Checklist — M17 Wave 3, Epoch's own boards, the Agent Arena boards, accessibility, no ids from moving aliases

**The engine now stores eleven more boards for W4 to combine, plus one attribute:**
- five boards Epoch runs itself: SimpleQA Verified, FrontierMath Tiers 1-3, FrontierMath Tier 4,
  chess puzzles and mystery game puzzles;
- the six Agent Arena configs, on their own IPS metric (#24);
- each model's accessibility, from Epoch's `model_metadata.csv`.

D-164 now fingerprints and guards every declared board that no surface ranks on. That set is
derived from the surfaces, never listed by hand. By D-166, no model is derived from an undated API
alias whose meaning moves. No surface, `/v1` route or app screen changes. The first night after the
merge was measured against the served artifact: it publishes, and no guard objects.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m17-plan.md` §2 W3 "(risk: **MED**)". The wave plan (`docs/plans/m17-wave-3-plan.md`, deleted in this close as DevFlow requires) asked for a repeat of W2's security look on the changed parquet reader (row 4) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every phase went red-first in its own commit, then green: P1 `1f55e7d`→`26382e6`, P2 `2dcb9c7`→`d63de1f`, P3 `5a6285b`→`2bb90d4`, P4 `2472da4`→`e08b965`. P5's measurement found the missing-table crash, fixed `8ea2532`→`333542c`. The review fixes were `5fc89b6`→`fd31317`, then `35296f3`, `de50f91` and `bce4ac6`, each with its mutants killed. `make check-fast` PASS at every push | ✅ |
| 3 | Code-Reviewer and Tester as two separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m17-wave-3-review.md`: **PASS-WITH-MINORS**. `docs/reviews/m17-wave-3-tester.md`: **PASS-WITH-MINORS**, a second Tester's verdict that supersedes the first Tester's BLOCKING one (committed at `c482cc3`: B1 skip budget, B2 coverage of `build.py`, both fixed in `de50f91`). All three are `seat: independent` subagents that wrote none of the wave's code | ✅ |
| 4 | *(plan-tag)* security look at the reader's column map (D-165) | Done by the Code-Reviewer as part of its brief (review, "Security look"). The value column comes only from declared `ArenaSlice` data, passed as argv JSON with no shell. The child still reads exactly four columns, under unchanged caps and the 8 MiB answer bound. The value column must be float or integer, and `score_rows` refuses non-numbers, bools, non-finite values and anything outside the board's band. No finding. MED wave, so no separate Security-Reviewer seat | ✅ |
| 5 | Tester fault-injection, restore byte-identical | First Tester (its verdict at `c482cc3`): 39 faults in place, 30 red; each survivor became B2/T1-T4 or was shown equivalent. Second Tester (`docs/reviews/m17-wave-3-tester.md`): 40 mutants on a byte-identical scratch copy, 33 killed; four are equivalent on the real data, and the rest became T5/T6. The author's own mutants were all red, each restored byte-identical by SHA-256: review M1 (4), M6 (1), Tester T1-T4/B2 (5), T5 (3) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The Code-Reviewer's table ("Acceptance criteria evidence") and the second Tester's criterion table map P1-P5 to tests. The paths are the real `build()` (`tests/unit/test_access.py`, `test_carry_forward.py`), `_ingest_slices` (`test_agent_boards.py`), `parse_arena_slices` spawning the real reader, and `serving_summary`/`refresh` for D-164 (`test_uncovered_boards.py`). The first night was measured through the refresh's own decision functions (`docs/research/m17-w3-boards-and-first-night-2026-09-25.md`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | D-165 still holds for a second value column. Its negatives: a text `score` column is refused by the reader (`test_agent_boards.py`, T4), one file read for boards with two value columns is refused (M1), and `model_metadata.csv` resolving outside the bundle is refused by the shared path guard (`test_access.py`, T3). The invariants list is still not maintained (W-131); these are this wave's rows for it | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, by the author or any seat. Each seat attests it in its file (`docs/reviews/m17-wave-3-review.md`, `docs/reviews/m17-wave-3-tester.md`, and the first Tester's at `c482cc3`). Mutants were reverted in place and checked by SHA-256 (the author's scripts check `git diff --stat -- src` is empty after each run) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | The boards D-164 covers are `boards.uncovered()`, derived from `ARENA_SLICES`, `EPOCH_BOARDS` and `CATEGORIES` (primary only, review M2). The tables a source's rows live in are `build.CARRY_TABLES`, now read by the carry and its rollback (review M1). `refresh._served_without` keeps a third copy (filed #41) | ✅ |
| 9b | Scope & draft PR | Draft PR on `wave/m17-w3`, issues #37 and #24. Planned vs delivered: P1-P5 delivered. The one deviation: plan decision 4's table `model_access(model_id, accessibility, source)` shipped as `access(raw_name, model_id, accessibility, source, source_url, observed_at)`, keyed by the source's own name, which lets a disagreement be counted. Deferred with an issue: #38-#42 (below). The PR opens after both reviews and `/pre-merge`, as the owner asked | ✅ |
| 9a | Economy | `git diff --shortstat c04ec4f HEAD`: 32 files, +1954/−97, of which `src/` and `scripts/` are +488/−85. The rest is tests, three review records, the plan, a research record and D-166. VARIANCE noted: two review rounds added about 400 lines of tests | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every push) · make wave-check · make gate · CI (py3.12, py3.14, live-contracts, secret-scan, dep-audit, governance) · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. Bypass: none. The skip budget rose from 66 to 72 in the tree, with its reason (`docs/skip-budget.txt`: six env-gated contract tests for the agent configs, review M1) | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-09-25 · Wave commit range: `c04ec4f..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `35296f3` |
| review M2 | fixed `fd31317` |
| review M3 | fixed `fd31317` |
| review M4 | fixed `fd31317` |
| review M5 | fixed `fd31317` |
| review M6 | fixed `35296f3` |
| review K1 | #38 |
| review R1 | #39 |
| review R2 | refused — it is D-166's intended cost, ruled by the owner, and it was measured below D-128's quarter on every surface (worst 5 of 190). A source that fails the same night and cannot carry is exactly what D-128 refuses, and review M1's tests now pin the carry on a pre-W3 artifact |
| tester T5 | fixed `bce4ac6` |
| tester T6 | fixed `bce4ac6` |

The first Tester's findings (BLOCKING verdict at `c482cc3`): B1, B2 and T1-T4 were fixed in
`de50f91`. Its K1 is #40, its K2 is #41 and its R1 is #42.

## Wave footprint — RECORD ONLY

```
Touched:        src/app/clients/{arena,arena_slices,parquet_reader,epoch_board,fakes}.py
                src/app/workflows/{access,boards}.py (new) · src/app/workflows/{build,refresh,rank,
                registry,schema,sources}.py · scripts/survey_boards.py
                tests/unit/test_{access,agent_boards,moving_aliases,uncovered_boards}.py (new)
                tests/unit/test_{arena_slices,board_run_dates,build,build_artifact_safety,
                build_slices,carry_forward,refresh_boards}.py · tests/integration/
                test_arena_openrouter_contract.py · docs/decisions.md (D-166) · docs/skip-budget.txt
                docs/research/m17-w3-boards-and-first-night-2026-09-25.md · docs/reviews/m17-wave-3-*.md
Mutant set author: the independent seats (Code-Reviewer, two Testers) and the lead agent
                (supporting evidence only)
Observed RED:   with `access` dropped from CARRY_TABLES,
                test_the_attribute_itself_carries_with_its_rows failed ("absent", not "carried")
Owner instruction: "A ve B sınıfı", "Bu adlarla model türetme", "Evet, W3'te" (2026-09-25,
                translated from Turkish: "classes A and B"; "derive no model from these names";
                "yes, in W3") -- delivered as the five Epoch boards, D-166, and the accessibility
                attribute; #24's agent boards on their own metric as ruled the same day.
K.8 contracts:  /v1 unchanged. New table `access` (additive; no existing column changed).
                ServingSummary.slices renamed to .boards; score_rows gains keyword arguments with Elo
                defaults; parquet_reader's column set comes from the declared value column.
Stopped at three attempts: NONE
Hand-kept lists: registry.MOVING_ALIASES (13, each with its reason; D-166 clause 3 grows it by
                review); access.ACCESSIBILITY (the file's seven values).
```
