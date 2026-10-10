---
record_type: wave
id: m21-wave-3-close
status: draft
process_version: v6.6
date: 2026-10-10
---
# Wave-Close Checklist — M21 Wave 3, the phone's promises, held further

**Fourteen issues as the milestone plan's W3 names them: #223, #219, #220 (partial: its on-device
glow measurement is the owner's), #168, #170, #174, #188, #169, #175, #132, #173, #171, #172, #85.**

**What the phone now holds.**
- **The compiled gate refuses more shapes.**
  - A URL loaded as text, as data, as a collection or by a parser.
  - The standings date chosen anywhere but its store.
  - The reader's text in a request's arguments.
  - Process-wide state and Foundation's shared state in a sink.
  - A served number followed through `Any` and text.
  - Every arithmetic shape the reviews planted.
  - The gate's fixture (`scripts/client_decl_fixtures/`) is the definition. The gate's self-test now
    compares the fixture's refusals with its committed dump line for line.
  - On a Mac without Xcode the gate fails (G-10); elsewhere it skips.
- **The held reading** decides in `Engine/HeldReading.swift`, where Swift tests drive it.
- **The phone states each engine refusal in the reader's language,** keyed on `error.code` (#223).
- **The boards screen** lays out its rows lazily.
- **The Apple Intelligence state** is read again when the app returns to the front.

**What the records now say.** Five review rounds found records that said more than the gates hold,
each time in another sentence. After the third, the slice came out:
- the records stopped describing refused forms in prose;
- every row about these gates is "Held in part" and names the fixture's rules or the pins' tests,
  ending with "any other form is not held (G-x)";
- other records point at those rows;
- `tests/unit/test_security_invariants.py` holds that wording;
- older records outside the wave go to #248's sweep (M21-W4).

The gaps G-1, G-2, G-10 to G-15 are open, each on its issue.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m21-plan.md` §2 W3: **HIGH**, since the privacy and arithmetic gates (D-180, D-181), `EngineClient.swift` and `ContentView.swift` (added at W3, #188) are security globs (§3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit, from `23573d8`/`5702663` to `e22c4c7`/`d8b0017`. The Tester built all 17 red commits from `git archive`: each fails only on its own tests and the three Swift ones compile; one red assertion dropped in its fix commit (`5702663`) with its reason (`docs/reviews/m21-wave-3-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | Rounds 1 to 5 BLOCKING, each on a record stating more than the gates hold (`docs/reviews/m21-wave-3-review-round-1.md` to `-round-5.md`). Round 6, scoped to the wave's own text after the third verdict took the slice out: `docs/reviews/m21-wave-3-review.md` (`9bc26e9`), **MINOR**, M1–M5, K1, K2, R1, R2. `docs/reviews/m21-wave-3-tester.md` (`4e66194`): **MINOR**, M1–M6, K1, R1, R2. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M21 closure seat reads this slice, and #241 asks it to | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 22 faults in a scratch mirror: 13 caught as delivered, 20 with its tests (`4e66194`); the two left are overclaims beside a fixed sentence or a pointer, which the wording test says it does not read (#248). The six review rounds planted their own; every survivor is held, or its record now says the form is not held. Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-GAP-001 and REQ-APP-005 through the compiled gate on the shipping client and its fixture (`tests/unit/test_client_decl_gate.py`, `make client-decls`), the text pins (`tests/unit/test_router_hints.py`, `tests/unit/test_ios_client_contract.py`) and the Swift tests (`HeldReadingTests.swift`, `StandingsStoreTests.swift`, `LanguageTests.swift`); the records through `tests/unit/test_security_invariants.py` | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | `docs/security-invariants.md`: 18 rows held in part, each naming its fixture rules or pin tests; gaps G-11 (#244), G-12 (#241), G-13 (#246), G-14, G-15 (#247) new, G-1 and G-2 narrowed (#242), G-10 on #243. Negative tests: the fixture's refused shapes and the self-test's line-for-line comparison (`tests/unit/test_client_decl_gate.py`) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made in a scratch mirror or from saved bytes, and checked (`docs/reviews/m21-wave-3-tester.md`). The session started outside the repository, so its hooks did not load (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | What the compiled gate refuses has one producer, its fixture (`scripts/client_decl_fixtures/`), compared line for line with `tests/unit/data/g2_fixture_ast.txt` by the self-test; the records name its rules, held by `tests/unit/test_security_invariants.py` | ✅ |
| 9b | Scope & draft PR | Delivered: #223, #219, #168, #170, #174, #188, #169, #175, #132, #173, #171, #172, #85; #220 in part. Filed: #241 to #249. Draft PR on `wave/m21-w3` against `main`, stacked on `wave/m21-w2` | ✅ |
| 9a | Economy | `git diff --shortstat origin/wave/m21-w2...HEAD`: 35 files, 9783 insertions(+), 1297 deletions(-), of which most are the gate, its fixture and dump, its tests and seven review records; the app's change is `HeldReading.swift` (new), `ContentView.swift`, `EngineClient.swift`, `Language.swift` and `StandingsStore.swift` | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make ui-test · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` at `40f0565`: 19 of 19 and 2 of 2; again at `79a9f75`, the merged head with W1 and W2: 19 of 19 and 2 of 2 (`ios/UITests/ScreenPathTests.swift`). One fix commit (`312eeac`) was made in a command after a green `make check-fast` with no change between, not chained to it. The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-10 · Wave commit range: `origin/wave/m21-w2...HEAD`

## Review findings — each one fixed here, filed, or refused

Rounds 1 to 5 were answered in order: round 1 by `826ab04`/`312eeac`, `08f21f0`/`39a1c86` and
`3b1fc8c`; round 2 by `3eee132`; round 3 by `5ab4077`/`45a2c68`; round 4 by `be11e1a`/`770e00e` and
`f6dcc67`; round 5 by `962af31`/`b46e976`, with their K and R items on #241 to #248. The rows below are
the last round's and the Tester's.

| finding | disposition |
|---|---|
| review M1 | fixed `3c35ef5` |
| review M2 | fixed `3c35ef5` |
| review M3 | fixed `3c35ef5` |
| review M4 | fixed `3c35ef5` |
| review M5 | fixed `3c35ef5` |
| review K1 | #247 |
| review K2 | #248 |
| review R1 | #247 |
| review R2 | #243 |
| tester M1 | fixed `4e66194` |
| tester M2 | fixed `d8b0017` |
| tester M3 | fixed `79a9f75` |
| tester M4 | fixed `4e66194` |
| tester M5 | fixed `79a9f75` |
| tester M6 | fixed `4e66194` |
| tester K1 | #249 |
| tester R1 | #248 |
| tester R2 | #243 |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        Makefile docs/architecture.md docs/decisions.md docs/plans/m21-plan.md docs/prd.md docs/security-invariants.md docs/reviews/m21-wave-3-review-round-1.md docs/reviews/m21-wave-3-review-round-2.md docs/reviews/m21-wave-3-review-round-3.md docs/reviews/m21-wave-3-review-round-4.md docs/reviews/m21-wave-3-review-round-5.md docs/reviews/m21-wave-3-review.md docs/reviews/m21-wave-3-tester.md ios/EngineTests/HeldReadingTests.swift ios/EngineTests/LanguageTests.swift ios/EngineTests/StandingsStoreTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/ContentView.swift ios/ModelRanking/Engine/EngineClient.swift ios/ModelRanking/Engine/HeldReading.swift ios/ModelRanking/Engine/Language.swift ios/ModelRanking/Engine/StandingsStore.swift scripts/client_decl_fixtures/ scripts/client_decl_gate.py tests/unit/data/g2_fixture_ast.txt tests/unit/test_client_decl_gate.py tests/unit/test_error_codes.py tests/unit/test_ios_client_contract.py tests/unit/test_router_hints.py tests/unit/test_security_invariants.py docs/plans/m21-wave-3-close.md
Mutant set author: the Tester seat (22) and the six review seats; the author's plants are supporting evidence only
Observed RED:   the Tester's survivors die on its tests (`4e66194`); each round's on its red commit (`826ab04`, `08f21f0`, `5ab4077`, `be11e1a`, `962af31`, `2d3a1e0`, `e22c4c7`)
Owner instruction: "keep the PRs as drafts, don't wait for me, continue with the open issues" and "process the waves one by one" (owner, 2026-10-09, translated from Turkish)
K.8 contracts:  no /v1 field or route changes; the app states engine error codes itself (`Language.swift`); `HeldReading` is new in the Engine; the gate's fixture and dump are its definition
Stopped at three attempts: the records' description of the gates (a record stating more than the gates hold), taken out at the third BLOCKING verdict (`45a2c68`, `770e00e`): the records name the fixture's rules, and older records go to #248
Hand-kept lists: the gate's rule lists and its fixture (`scripts/client_decl_fixtures/`, #242 proposes an allowlist), the off-register PRD rows in the wording test
```
