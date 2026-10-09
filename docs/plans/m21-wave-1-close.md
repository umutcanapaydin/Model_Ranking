---
record_type: wave
id: m21-wave-1-close
status: draft
process_version: v6.6
date: 2026-10-09
---
# Wave-Close Checklist — M21 Wave 1, the data a reader sees

**Eleven issues, as the milestone plan's W1 names them: #163, #164, #165, #124, #185, #166, #198,
#205, #214, #216, #228.**

**What the reader now gets.**
- **One model, one set of scores** (D-189).
  - A release named apart is its own model: DeepSeek V3-0324 and R1-0528, Mistral Large 1.0 to 4,
    Claude Sonnet 4.6, GLM-4.6V and its Flash. A distill is never its teacher.
  - A retired id its maker now routes elsewhere is dropped and counted. A fine-tune's price reaches no
    base model.
- **`web-dev` ranks on LMArena's own CC-BY WebDev board**, with its thresholds measured on that board
  (D-190).
- **The release behind the data is named, and checked before a deploy.**
  - The refresh record and the deploy stamp name the release that built the data.
  - The deploy refuses data another release built, unless the owner names that release.
  - The derivation refuses a missed copy of a left-out source.
- **The serving engine.**
  - The board list loads no client.
  - One 90-day line holds everywhere.
  - Standings never block questions: each client has one window entry with two counts, and a refused
    request is not charged.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m21-plan.md` §2 W1: **HIGH**, since `src/app/clients/**` and `src/app/adapter/main.py` change (§3, M20's globs) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: the issues (`b7cc0ab`, `5bcae05`), #185 (`7abf5dc`, `47f0c6c`), the first review (`13b955e`, `73a8e82`), the second (`4183a13`, `90b7424`). The Tester built each red commit from `git archive`: each fails only on its own tests, every failure an assertion, none a collection error (`docs/reviews/m21-wave-1-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m21-wave-1-review-round-1.md` (`cdc523e`): **BLOCKING**, B1–B3, M1–M4, K1, K2, R1, answered by `73a8e82`. `docs/reviews/m21-wave-1-review.md` (`3d8cf6b`): **MINOR**, M1–M5, K1, K2, R1, R2. `docs/reviews/m21-wave-1-tester.md` (`9832965`): **MINOR**, T1–T4, K1, R1, R2. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M21 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 20 faults with a fresh bytecode cache each run: 15 caught as delivered, 19 with its four tests (`9832965`); the twentieth changes no name in the artifact (#235). The reviews planted 12 and 16; every survivor is held since `13b955e` and `4183a13`. Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-CAN-001 through `registry` on every name in the artifact (`tests/unit/test_registry.py`, `tests/unit/test_moving_aliases.py`); REQ-SRC-010 through the arena client and `/v1/categories` (`tests/unit/test_webdev_board.py`); REQ-REL-001 and REQ-REL-003 through the derivation and the deploy script with stand-in `fly` and `curl` (`tests/unit/test_public_artifact.py`, `tests/unit/test_data_release_stamp.py`); REQ-REL-004 through the served app (`tests/unit/test_rate_limit.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | INV-87 (the derivation refuses a missed copy) and INV-88 (standings never block questions, a refused request is uncharged) list their new tests in `docs/security-invariants.md`; the deploy's refusal of another release's data, with `test_data_release_stamp.py::test_the_refusal_runs_before_anything_is_derived` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was written from saved bytes and checked (`docs/reviews/m21-wave-1-tester.md`). The session started outside the repository, so its hooks did not load (#142, the M20 closure's ledger row) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | A model id reaches a board row through one producer, `registry.canonical` (`src/app/workflows/registry.py`), held over every name in the artifact; the data's release through one, `refresh.py`'s record, read by `scripts/deploy_hosted_engine.sh` | ✅ |
| 9b | Scope & draft PR | Delivered: #163, #164, #165, #185, #198, #205, #214, #216, #228; #166 read (`docs/research/m21-w1-first-nights-after-m19-w1.md`); #124 delivered at M19-W1 (`d0bbd62`), its licence ruling D-186's. Filed: #230, #231 (fixed here), #232, #233, #234, #235. Draft PR on `wave/m21-w1` against `main`, stacked on the M20 closure | ✅ |
| 9a | Economy | `git diff --shortstat origin/closure/m20...HEAD` before this close: 37 files, 2164 insertions(+), 235 deletions(-); the code is the registry, the arena and Epoch clients, the derivation, the limiter and the deploy script; the rest are tests, three verdicts, two research records and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. One `make check-fast` run failed only on `ResponseCeilingTests`' stream timing while three waves ran checks at once; it passed alone and the run that gated the commit was green. `make ui-test` was not run: no screen changed in this range. The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-09 · Wave commit range: `origin/closure/m20...HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| round-1 B1 | fixed `73a8e82` |
| round-1 B2 | fixed `73a8e82` |
| round-1 B3 | fixed `73a8e82` |
| round-1 M1 | fixed `13b955e` |
| round-1 M2 | fixed `13b955e` |
| round-1 M3 | fixed `73a8e82` |
| round-1 M4 | fixed `73a8e82` |
| round-1 K1 | #230 |
| round-1 K2 | fixed `73a8e82` |
| round-1 R1 | fixed `73a8e82` |
| review M1 | fixed `90b7424` |
| review M2 | fixed `90b7424` |
| review M3 | fixed `4183a13` |
| review M4 | fixed `4183a13` |
| review M5 | fixed `90b7424` |
| review K1 | #233 |
| review K2 | fixed `90b7424` |
| review R1 | fixed `90b7424` |
| review R2 | fixed `90b7424` |
| tester T1 | fixed `9832965` |
| tester T2 | fixed `9832965` |
| tester T3 | fixed `9832965` |
| tester T4 | fixed `9832965` |
| tester K1 | #234 |
| tester R1 | #235 |
| tester R2 | #235 |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        docs/architecture.md docs/decisions.md docs/prd.md docs/release-testflight.md docs/security-invariants.md docs/research/m21-w1-first-nights-after-m19-w1.md docs/research/m21-w1-webdev-calibration.json docs/reviews/m21-wave-1-review-round-1.md docs/reviews/m21-wave-1-review.md docs/reviews/m21-wave-1-tester.md scripts/deploy_hosted_engine.sh src/app/adapter/main.py src/app/adapter/nightly.py src/app/clients/arena.py src/app/clients/epoch_board.py src/app/workflows/board_tables.py src/app/workflows/boards.py src/app/workflows/categories.py src/app/workflows/coverage.py src/app/workflows/families.py src/app/workflows/public.py src/app/workflows/rank.py src/app/workflows/refresh.py src/app/workflows/registry.py src/app/workflows/sources.py tests/unit/test_arena_client.py tests/unit/test_categories.py tests/unit/test_coverage.py tests/unit/test_data_release_stamp.py tests/unit/test_deploy_hosted.py tests/unit/test_moving_aliases.py tests/unit/test_nightly_refresh.py tests/unit/test_public_artifact.py tests/unit/test_rate_limit.py tests/unit/test_registry.py tests/unit/test_sources.py tests/unit/test_webdev_board.py docs/plans/m21-wave-1-close.md
Mutant set author: the Tester seat (20) and the two review seats (12; 16); the author's plants are supporting evidence only
Observed RED:   the Tester's survivors die on its four tests (`9832965`); the first review's on `13b955e`; the second review's on `4183a13`
Owner instruction: "add the open issues ... code the open enhancements too, open a milestone for them, then you can start" (owner, 2026-10-08, translated from Turkish), and "keep the PRs as drafts, don't wait for me, continue with the open issues" (owner, 2026-10-09, translated from Turkish)
K.8 contracts:  no /v1 field or route changes; `web-dev`'s primary source is LMArena's WebDev board (D-190); the deploy stamp gains a `-from-` part naming the data's release; `DEPLOY_ACCEPT_DATA_FROM` is new
Stopped at three attempts: NONE
Hand-kept lists: the registry's curated rules (each with the maker's page or the artifact's own rows as its source, D-189), the moving aliases, web-dev's measured thresholds (`docs/research/m21-w1-webdev-calibration.json`)
```
