---
record_type: wave
id: m18-wave-4-close
status: draft
process_version: v6.6
date: 2026-10-04
---
# Wave-Close Checklist — M18 Wave 4, the engine and data backlog

**Eleven issues from M17's seats, fixed or ruled, each red first.** The decisions the triage left open
are D-173, taken on the owner's standing instruction of 2026-09-29. Here is what changed.

**Ranking:**
- A tie is ordered by model id. The frontier keeps that order, and so do the value and cheapest picks
  (#44).
- An effort suffix the reconcile resolves no longer counts as unknown (#45).
- A `-latest` token is refused unless a date or a version follows it (#48).

**The refresh:**
- It compares rosters by id and records re-spellings (#39).
- It refuses a night that loses a quarter of the accessibility values (#42).
- It checks the serving bounds on its candidate, with the bounds the engine serves under (#57).

**`/v1/boards`:**
- It is built once per artifact and compressed on request (#55).
- Boards that no question selects stay published (#77).

**Also:**
- The fetch deadline is decided before the client is closed (#71).
- The Epoch bundle has live contract tests (#79).
- The retired refresher's installer is gone (#76).

**The owner chose the order on 2026-10-04:** W4 before W2, because the simulator stays off for now.
#74 and #56, the app's own code, moved to W2.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m18-plan.md:89` "W4 — Engine and data backlog (risk: **MED**)". It is **HIGH** by the plan's security globs (`src/app/adapter/main.py`, `src/app/clients/**`), as the wave plan `docs/plans/m18-wave-4-plan.md` recorded; that plan is deleted in this close | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red first, in pairs: P1 `6858d30`, `e4e2695` → `293c918`; P2 `35c87e9` → `4a47877`; P3 `1d7cfaa` → `6c0c242`; P4 `baebf92` → `5623f4b`; review round 1 `81a3942` → `77d3b2f`. The rest are test-only additions for code already right: round 2 `4d07e50` and the Tester's `db1d1de`. `make check-fast` PASS before every commit, its exit code read | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m18-wave-4-review.md`: the second Code-Reviewer's **PASS-WITH-MINORS** at `ddf8443`, after the first seat's BLOCKING at `5807fbe` (B1: the refresh child did not see the engine's bounds). `docs/reviews/m18-wave-4-tester.md`: **PASS-WITH-MINORS**. Three seats ran one after another, each in its own worktree behind command guards (#52) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (the owner's ruling, 2026-09-29); the M18 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester injected 55 faults: 41 killed, 3 equivalent (N1–N3), 11 survived. Each survivor got its test in `db1d1de` (T1–T9). The second Code-Reviewer ran 18 mutants, and the first ran 9; their survivors got tests in `4d07e50`. Every fault was restored in place, checked by sha256, `git hash-object` and `git diff --quiet` | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The ranking goes through `coding_ranking` and `recommend` (`tests/unit/test_rank.py`, `test_pareto_dominance.py`). The guards go through `refresh()` and `fingerprint_of` (`tests/unit/test_refresh.py`, `test_nightly_refresh.py` through `run_once`). The route goes through the FastAPI app (`test_board_standings.py`). The fetch goes through `fetch_bounded_bytes` (`test_fetch_bounds.py`). The contracts run with `RUN_CONTRACT_TESTS=1`, once live: 12 boards and 971 metadata rows. REQ-ING-004, which the plan named, is not cited: no W4 change touched provenance, and its own tests pass | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | "The refresh publishes nothing the engine would refuse at start": `test_a_candidate_past_a_serving_bound_is_refused`, `test_a_first_artifact_past_a_bound_is_refused_too`, `test_the_child_checks_the_bounds_the_engine_serves_under`. "Nothing the refresh loads imports the adapter": `test_nothing_the_refresh_loads_imports_the_serving_adapter`. "Every route is behind the Host check, gzip included" (D-171 holds, `test_engine_host.py`). The single list is #89 | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None by any seat, each attested in its file. The author restored his own mutants in place and checked them by hash | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a served tie order: `rank.ranked_with_ids` (the one query) and `recommend.first_cheapest`. Producers of the bounds: `serving_bounds.bounds_from_env` (one spelling, `BOUND_VARIABLES`), read by the engine at start and by the refresh child (`nightly.CHILD_ENV`). Producers of a published artifact: `refresh._cycle` only, through `_reason_to_refuse` | ✅ |
| 9b | Scope & draft PR | Draft PR on `wave/m18-w4`, against `main`; merge #99 (W1) first. Delivered: the eleven issues. Moved to W2 by the amendment: #74, #56. Filed and triaged: #100–#106 | ✅ |
| 9a | Economy | `git diff --shortstat d528fd3 HEAD`: 34 files, +2304/−464 before this close. Code (`src/`, `scripts/`, `deploy/`): 15 files, +370/−343, the retired refresher's removal among them. VARIANCE noted: eleven issues in one wave, two Code-Reviewer rounds and a Tester | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. Not run, by the owner's instruction of 2026-10-01 (NO-ENVIRONMENT): the simulator. Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-04 · Wave commit range: `d528fd3..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M6 | fixed `4d07e50` |
| review M7 | fixed `4d07e50` |
| review M8 | fixed `db1d1de` (the expiry night through the cycle); REQ-ING-004 is not cited because no W4 change touched provenance |
| review M9 | fixed `4d07e50` |
| review M10 | fixed `4d07e50` |
| review M11 | fixed `4d07e50` |
| review M12 | fixed `db1d1de` |
| review K4 | #105 |
| review R4 | #106 |
| tester T1 | fixed `db1d1de` |
| tester T2 | fixed `db1d1de` |
| tester T3 | fixed `db1d1de` |
| tester T4 | fixed `db1d1de` |
| tester T5 | fixed `db1d1de` |
| tester T6 | fixed `db1d1de` |
| tester T7 | fixed `db1d1de` |
| tester T8 | fixed `db1d1de` |
| tester T9 | fixed `db1d1de` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        src/app/workflows/{rank,recommend,registry,build,refresh,serving_bounds (new)}.py ·
                src/app/adapter/{main,nightly}.py · src/app/clients/protocols.py ·
                scripts/README.md · scripts/{enable_refresh,install_refresh_wrapper,refresh_job,
                retire_refresh}.sh and deploy/com.hcs.modelranking.refresh.plist (removed)
                tests/unit/test_{rank,pareto_dominance,build,moving_aliases,refresh,nightly_refresh,
                board_standings,fetch_bounds,engine_service}.py · test_refresh_job_install.py (removed)
                tests/integration/test_epoch_bundle_contract.py (new)
                docs/decisions.md (D-173, notes on D-128, D-132, D-154, D-166, D-167) · docs/prd.md ·
                docs/coverage-by-req.md (note) · docs/skip-budget.txt (75) · docs/plans/m18-plan.md
                docs/reviews/m18-wave-4-{review,tester}.md
Mutant set author: the independent seats (two Code-Reviewers, the Tester); the lead agent's own
                faults are supporting evidence only
Observed RED:   the first Code-Reviewer's B1 (the child's allowlist without the bound variables)
                turned test_the_child_checks_the_bounds_the_engine_serves_under red on 81a3942
Owner instruction: "not yet, W4 first" (2026-10-04, translated from Turkish), asked whether the
                simulator could be used, and "proceed with what you recommend" (2026-09-29, translated
                from Turkish) for the decisions. Delivered: the engine backlog, D-173 recording each
                decision
K.8 contracts:  /v1 unchanged in fields and routes; tied rows are ordered by id; responses of 1 KB or
                more are gzip-encoded when asked. rank.ranked_with_ids and app.workflows.serving_bounds
                are new, shared by the engine and the refresh
Stopped at three attempts: none
Hand-kept lists: serving_bounds.BOUND_VARIABLES with its defaults table (the one spelling, read by the
                engine and by nightly.CHILD_ENV); the Epoch contract test's floor of 200 metadata rows
```
