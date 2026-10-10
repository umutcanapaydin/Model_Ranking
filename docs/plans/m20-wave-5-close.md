---
record_type: wave
id: m20-wave-5-close
status: draft
process_version: v6.6
date: 2026-10-08
---
# Wave-Close Checklist — M20 Wave 5, build 3 on TestFlight, safely

**Two issues, as the milestone plan's W5 names them: #187 and #195. Build 3's deploy and upload are
the owner's steps (`docs/release-testflight.md`).**

**What changed.**
- **#187:** the hosted engine answers one client at most `MODEL_RANKING_RATE_LIMIT` times a clock
  minute (120 in `fly.toml`). A client is an IPv4 address or an IPv6 /64.
  - It is a fairness control, so it fails open, with one warning a minute.
  - A refusal is a 429 with `Retry-After`, logged once per client per window.
  - `/health` is never limited.
  - A crowd of new addresses never resets a count the table holds.
  - With no limit (the owner's Mac), the engine says so at boot.
  - The runbook gives the traffic arithmetic, and a check, after the first deploy, that Fly sets the
    client's address.
- **#195:**
  - A fresh labelled set, written by an independent seat, measures the question reading on both
    tiers, before and after M20.
  - It measures the words' refinements and our own list against the primary board's order
    (`docs/research/m20-w5-family-probe.md`).
  - The M19 held-out sets retire to tuning.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m20-plan.md` §2 W5: **HIGH**, since `src/app/adapter/main.py` and `fly.toml` are security globs (§3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #187 (`0c499b7`, `8f49a14`), the review (`3c5954f`, `2cbbf59`), the Tester (`af5c4f7`, `be8e737`). The Tester ran `3c5954f`'s tree: it fails only on its own tests (`docs/reviews/m20-wave-5-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m20-wave-5-review.md` (`13eb425`): **MINOR**, M1–M6, K1, R1, R2. `docs/reviews/m20-wave-5-tester.md` (`c645eb8`): **MINOR**, T1–T4, R1. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild`; neither read the held-out questions | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M20 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 22 faults in `src/app/adapter/main.py`: 17 caught as delivered, all 22 with its seven tests (`c645eb8`). The review's three survivors die on `3c5954f`. Every file restored byte-identical (sha256 `81533d3b…`) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-REL-004 through the served app (`TestClient` on `app.adapter.main.app`) and `validate_startup_config` (`tests/unit/test_rate_limit.py`, 27 tests, one with requests in flight together on one loop); `fly.toml` sets the limit (`::test_the_hosted_engine_sets_its_limit`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | The limiter fails open by design (AGENTS.md §5), held by `tests/unit/test_rate_limit.py::test_the_limiter_fails_open` and `::test_a_crowded_out_client_is_served`; an unreadable limit fails closed at boot in a strict environment (`::test_the_boot_check_refuses_an_unreadable_limit`). The client's address is trusted from `Fly-Client-IP`; the owner's post-deploy check verifies Fly sets it (`docs/release-testflight.md`) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was written from saved bytes and checked (`docs/reviews/m20-wave-5-tester.md`) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | One producer of a 429 `rate_limited`: the `_limited` middleware in `src/app/adapter/main.py`, reading `_over_limit`; one reader of the limit, `_rate_limit`, and one boot check, `rate_limit_problems` | ✅ |
| 9b | Scope & draft PR | Delivered: #187, #195. Filed: #222 (the measurement's wording-tier finding), #223 (review K1). The build number is 3 (`3d7336d`, `ios/ModelRanking.xcodeproj/project.pbxproj`); the deploy and build 3's upload are the owner's (`docs/release-testflight.md`). Draft PR on `wave/m20-w5` against `main`, stacked on `wave/m20-w4` | ✅ |
| 9a | Economy | `git diff --stat origin/wave/m20-w4...HEAD` before this close: 24 files, 8619 insertions(+), 38 deletions(-), of which the code is `main.py` (125) and `fly.toml` (3); the runs' per-question output is 7378 lines, kept so a run can be scored again; the rest are tests (346), two verdicts and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit but 3c5954f, committed with a lint finding fixed in 2cbbf59) · make swift-test · make client-decls · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` was not run: no screen changed in this range. The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-08 · Wave commit range: `origin/wave/m20-w4...HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `2cbbf59` |
| review M2 | fixed `3c5954f` |
| review M3 | fixed `3c5954f` |
| review M4 | fixed `2cbbf59` |
| review M5 | fixed `2cbbf59` |
| review M6 | fixed `2cbbf59` |
| review K1 | #223 |
| review R1 | fixed `2cbbf59` |
| review R2 | fixed `2cbbf59` |
| tester T1 | fixed `be8e737` |
| tester T2 | fixed `be8e737` |
| tester T3 | fixed `c645eb8` |
| tester T4 | fixed `be8e737` |
| tester R1 | fixed `be8e737` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        fly.toml src/app/adapter/main.py tests/unit/test_rate_limit.py tests/unit/test_ios_client_contract.py docs/release-testflight.md docs/prd.md docs/plans/m21-plan.md .language-allow docs/research/m20-w5-family-probe.md docs/research/m20-w5-runs/ scripts/router_probe/wording_heldout_m20_questions.json docs/reviews/m20-wave-5-review.md docs/reviews/m20-wave-5-tester.md docs/plans/m20-wave-5-close.md
Mutant set author: the Tester seat (22) and the review seat; the author's plants are supporting evidence only
Observed RED:   the Tester's five survivors die on its seven tests (`c645eb8`); the review's three on `3c5954f`
Owner instruction: "Yes, of course, let's do it in M20; it's our biggest strength" (owner, 2026-10-08, translated from Turkish); the plan's W5, build 3 against the hosted engine with a rate limit before any external tester
K.8 contracts:  no /v1 field or route changes; a new 429 `rate_limited` error in the API's one error shape, with `Retry-After`; `fly.toml` sets `MODEL_RANKING_RATE_LIMIT`
Stopped at three attempts: NONE
Hand-kept lists: `RETIRED_HELD_OUT` and `HELD_OUT_ONLY_REVIEWED` (each entry with its origin)
```
