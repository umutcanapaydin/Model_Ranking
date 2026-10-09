---
record_type: wave
id: m21-wave-2-close
status: draft
process_version: v6.6
date: 2026-10-09
---
# Wave-Close Checklist — M21 Wave 2, reading what is not a search

**Nine issues as the milestone plan's W2 names them. Delivered: #193, #186, #180, #199, #226. Taken
out after three verdicts and carried open: #194, #218, #222. Carried: #66 (the set holds 7
non-searches, too few for its bar).**

**What ships** (D-191):
- **Model comparisons.** A short question made only of model names, from every family the registry
  names, and Turkish particles is a comparison, answered from `everyday` (#206, widened).
  `ModelFamilies.swift` is generated from the registry, and a test holds it equal byte for byte.
- **The held-out gates.** They match each list as the app does, read the wording tier's sentences and
  the family words, and name where each entry only the live set holds came from (#186, #180).
- **The probe rows.** `ProbeRows.swift` is shared by both harnesses and tested (#193).
- **The UI routing.** The UI target's routing and expected readings live in one fixture, which an
  Engine test and the screen tests both read (#199).
- **The owner's judgement sheet.** It is blinded, its key is kept outside the repository, and it has
  a scorer that reads D-188's revisit (#226).

**What came out.** Three rules met the next phrasing at each verdict, as M19's image rule did. Each
was taken out, and its path is back to `972b55e`:
- #194's model names in the fact doubt;
- #218's Turkish signals before the embedding;
- #222's Turkish general ask.

Every held-out row now reads as it did at `972b55e`.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m21-plan.md` §2 W2: **HIGH**, since `ios/ModelRanking/Engine/Router.swift` and `Reading.swift` are security globs (§3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit, fourteen pairs from `9d89aee`/`483c619` to `239a171`/`35a8563`; the Tester built all fourteen red commits from `git archive`: each fails only on its own tests and each compiles (`docs/reviews/m21-wave-2-tester.md`). The removal is `35a8563`, after the Tester's verdict | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m21-wave-2-review-round-1.md` (`66ce7b5`): **MINOR**, M1–M8, K1, R1. `docs/reviews/m21-wave-2-review.md` (`c58afe8`): **MINOR**, M1–M8, K1, R1. `docs/reviews/m21-wave-2-tester.md` (`a52d6c8`): **MINOR**, M1–M6, K1, R1. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild`; none read the held-out questions | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M21 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 22 faults: 18 caught as delivered, all 22 with its tests; those holding the removed rules were dropped with the rules and named in `d902991`. The reviews planted their own; each survivor is held or its rule is out. Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-ASK-005 through `TieredRouter.route` and `SimilarityRouter.route` (`ios/EngineTests/ReadingM21Tests.swift`, `KeywordRoutingTests.swift`); the gates through the tree (`tests/unit/test_ios_client_contract.py`); the fixture through both suites (`tests/unit/test_screen_paths.py`, `ScreenPathFixtureTests.swift`); the sheet through its script (`tests/unit/test_judgement_sheet.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | None changed. Nothing typed leaves the phone: the reading stays a pure function over the question (`tests/unit/test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine`); the judgement key is refused inside the repository by its real path (`tests/unit/test_judgement_sheet.py`) | N/A |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was written from saved bytes and checked (`docs/reviews/m21-wave-2-tester.md`). The session started outside the repository, so its hooks did not load (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | A comparison's model words come from one producer, `scripts/model_family_words.py` (`ios/ModelRanking/Engine/ModelFamilies.swift`), held equal to `render()`; the held-out gates read every list the reading uses (`tests/unit/test_ios_client_contract.py`) | ✅ |
| 9b | Scope & draft PR | Delivered: #193, #186, #180, #199, #226. Taken out and open: #194, #218, #222, each with its measured state. Carried: #66. Filed: #237, #238, #239. Draft PR on `wave/m21-w2` against `main`, stacked on `wave/m21-w1` | ✅ |
| 9a | Economy | `git diff --shortstat origin/wave/m21-w1...HEAD`: 48 files, 14627 insertions(+), 62 deletions(-); the probe runs' per-question output is most of it, kept so a run can be scored again; the app's change is `Router.swift` (15 lines) and the generated `ModelFamilies.swift` | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit but 9613a2b, a docs commit gated by check-records only; check-fast ran green after it) · make swift-test · make client-decls · make ui-test (ScreenPathTests 19 of 19 at the head; earlier runs failed only on #227's flake) · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. The per-wave security pass is not run by rule (D-172). Bypass: `9613a2b`, recorded with the M20 closure's pending ledger row for the same control | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-09 · Wave commit range: `origin/wave/m21-w1...HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| round-1 M1 | #194 |
| round-1 M2 | fixed `f666828` |
| round-1 M3 | fixed `35a8563` |
| round-1 M4 | fixed `26a334a` |
| round-1 M5 | fixed `35a8563` |
| round-1 M6 | fixed `adc7c8d` |
| round-1 M7 | fixed `be93e5a` |
| round-1 M8 | fixed `08673fa` |
| round-1 K1 | fixed `f666828` |
| round-1 R1 | #237 |
| review M1 | fixed `26a334a` |
| review M2 | fixed `35a8563` |
| review M3 | fixed `35a8563` |
| review M4 | #194 |
| review M5 | fixed `f976da7` |
| review M6 | fixed `35a8563` |
| review M7 | fixed `9195d39` |
| review M8 | fixed `42d4e7e` |
| review K1 | #238 |
| review R1 | #239 |
| tester M1 | fixed `35a8563` |
| tester M2 | fixed `35a8563` |
| tester M3 | fixed `35a8563` |
| tester M4 | #218 |
| tester M5 | fixed `35a8563` |
| tester M6 | refused — the three rules it names were taken out at `35a8563`, so there is nothing left for a test to hold |
| tester K1 | #238 |
| tester R1 | fixed `35a8563` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .language-allow docs/decisions.md docs/judgement-sheet.md docs/prd.md docs/research/judgement/questions.json docs/research/m21-w2-reading-probe.md docs/research/m21-w2-runs/ docs/reviews/m21-wave-2-review-round-1.md docs/reviews/m21-wave-2-review.md docs/reviews/m21-wave-2-tester.md ios/EngineTests/JudgementRowTests.swift ios/EngineTests/ProbeRows.swift ios/EngineTests/ReadingM21Tests.swift ios/EngineTests/ScreenPathFixtureTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/Engine/ModelFamilies.swift ios/ModelRanking/Engine/Router.swift ios/UITests/ScreenPathTests.swift ios/UITests/ScreenPaths.json scripts/judgement_sheet.py scripts/model_family_words.py scripts/router_probe/JudgementProbe.swift scripts/router_probe/ReadingProbe.swift scripts/router_probe/ReplayProbe.swift src/app/workflows/registry.py tests/unit/test_ios_client_contract.py tests/unit/test_judgement_sheet.py tests/unit/test_model_families.py tests/unit/test_screen_paths.py docs/plans/m21-wave-2-close.md
Mutant set author: the Tester seat (22) and the two review seats; the author's plants are supporting evidence only
Observed RED:   the Tester's four survivors die on its tests (`d902991`, those for what stays); the reviews' survivors on their red commits, or their rule is out (`35a8563`)
Owner instruction: "keep the PRs as drafts, don't wait for me, continue with the open issues" and "process the waves one by one" (owner, 2026-10-09, translated from Turkish)
K.8 contracts:  no /v1 field or route changes; `ModelFamilies.words` is new in the Engine, generated from the registry; the UI routing fixture `ios/UITests/ScreenPaths.json` is new
Stopped at three attempts: #194's model names in the fact doubt, #218's Turkish signals and #222's Turkish general ask, each taken out at its third verdict (`26a334a`, `35a8563`); the issues carry them open
Hand-kept lists: `HELD_OUT_ONLY_REVIEWED` (each entry with its origin), the comparison particles and tier words
```
