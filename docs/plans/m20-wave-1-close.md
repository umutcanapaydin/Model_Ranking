---
record_type: wave
id: m20-wave-1-close
status: draft
process_version: v6.6
date: 2026-10-08
---
# Wave-Close Checklist — M20 Wave 1, every board that measures a task, named by the engine

**One issue, as the milestone plan's W1 names it: #209.**

**What the engine now says** (D-188 clause 1, proposed).
- `/v1/categories` names, for every surface, its family: every board that measures that task, the
  primary first, as `boards`. Additive; no field changes meaning. The phone decodes it
  (`CategoryInfo.boards`) and keeps no copy of its own.
- The families are one declared table in a client-free module (`app.workflows.families`), with every
  other served board named outside with its reason. A family holds at most one board of each source,
  and each search surface keeps its one board.
- A gate holds that every board in a family can be served, that every board the engine can serve is
  in a family or named outside, and that D-188 clause 1's table equals the module.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m20-plan.md` §2 W1: **HIGH**, since `src/app/adapter/main.py` changes and it is a security glob (§3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #209 (`1074c85`, `928440d`), the review (`ab14584`, `6921a75`), the Tester (`c6bf5d1`, `1389d7d`). Each red commit's only failures were its own tests (`make check-fast`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m20-wave-1-review.md` (`5d8c4b4`): **MINOR**, M1–M6, K1, R1. `docs/reviews/m20-wave-1-tester.md` (`707c626`): **MINOR**, M1–M5. Each seat had its own worktree at its range's end, its own venv, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M20 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The review planted 13 faults, all caught. The Tester planted 14: 9 caught as delivered, 12 with its tests (`707c626`); the two left (a board moved between families) are caught since `1389d7d` by the test that holds D-188's table equal to `FAMILIES`. Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-CMB-001 through `/v1/categories` on the served app (`test_families.py`), and decoded on the phone (`EngineClientTests.swift`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | None changed. The new module imports no client (W-125), held by the server-import test over `src/app/workflows/families.py` | N/A |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python and restored from saved bytes (`docs/reviews/m20-wave-1-tester.md`) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | The one producer of a family is `app.workflows.families.FAMILIES`, served by `main.py`'s categories route; the gate reads both | ✅ |
| 9b | Scope & draft PR | Delivered: #209. Filed: #214 (review K1). Draft PR on `wave/m20-w1` against `main` | ✅ |
| 9a | Economy | `git diff --shortstat origin/main HEAD`: 14 files, 1099 insertions(+), 1 deletion(-), of which the code is `families.py` (85), `main.py` (5) and `Models.swift` (4); the rest are tests, the two verdicts, the M20 and M21 plans and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` was not run: no screen changed in this range. The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-08 · Wave commit range: `origin/main..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `6921a75` |
| review M2 | fixed `6921a75` |
| review M3 | fixed `6921a75` |
| review M4 | fixed `ab14584` |
| review M5 | fixed `6921a75` |
| review M6 | fixed `6921a75` |
| review K1 | #214 |
| review R1 | fixed `4f7fd8a` (on wave/m20-w2) |
| tester M1 | fixed `1389d7d` |
| tester M2 | fixed `707c626` |
| tester M3 | fixed `707c626` |
| tester M4 | fixed `1389d7d` |
| tester M5 | fixed `707c626` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        docs/architecture.md docs/decisions.md docs/plans/m20-plan.md docs/plans/m21-plan.md docs/prd.md docs/reviews/m20-wave-1-review.md docs/reviews/m20-wave-1-tester.md ios/EngineTests/EngineClientTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/Engine/Models.swift src/app/adapter/main.py src/app/workflows/families.py tests/unit/test_families.py tests/unit/test_uncertainty_contract.py docs/plans/m20-wave-1-close.md
Mutant set author: the Tester seat (14) and the review seat (13); the author's plants are supporting evidence only
Observed RED:   the Tester's survivors die on its tests (`707c626`) and on the D-188 table hold (`1389d7d`); the review's M1 to M5 on `ab14584`
Owner instruction: "Yes, of course, let's do it in M20; it's our biggest strength" (owner, 2026-10-08, translated from Turkish), on the app composing its own list per question from many boards
K.8 contracts:  `/v1/categories` gains `boards` per surface (additive; no field changes meaning); `CategoryInfo.boards` on the phone
Stopped at three attempts: NONE
Hand-kept lists: `FAMILIES` and `OUTSIDE_FAMILIES` (the gate holds both against what the engine can serve), D-188 clause 1's table (held equal to `FAMILIES`)
```
