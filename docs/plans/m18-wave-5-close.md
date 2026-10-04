---
record_type: wave
id: m18-wave-5-close
status: draft
process_version: v6.6
date: 2026-10-04
---
# Wave-Close Checklist — M18 Wave 5, the gates and records backlog

**The controls the M17 seats found leaky now fail where they should, and the records describe the
product as it is.**

**Gates on the phone:**
- No Swift test reaches the network (#59).
- The declaration gate tests itself on a compiled fixture (#51).
- A URL decoded from text is the network outside the one door, and the gap register is file-only
  (#58).
- The text pins read code through a scanner that knows comments and strings (#98).

**Gates on the engine and the process:**
- The M17 closure Tester's seven holes are closed (#92).
- A planned wave needs its close (#82).
- A wave touching input parsing must be HIGH (#83).

**Records:**
- The app's requirement rows describe the combined list (#68).
- The PRD and ADR drift from the #28 audit is fixed, and D-154 and D-157 are accepted (#33).
- The architecture document and `AGENTS.md` §1 describe the product after M18-W4 (#80).
- The seats rule is D-174 (#52).
- #84 is resolved by D-172.

**Moved:** #60 and #85, the compiler-level tripwires (the plan's P4), go to W6 beside the
invariants list (#89), as the milestone plan's amendment of 2026-10-04 records.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m18-plan.md` §2 W5 "(risk: **MED**)". It is **HIGH** by the plan's security globs: `ios/ModelRanking/Engine/FrontDoor.swift`, and the D-126 gates in `scripts/client_decl_gate.py` and `tests/unit/test_router_hints.py`. The wave plan `docs/plans/m18-wave-5-plan.md` recorded it, and is deleted in this close | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red first, in pairs: #59 `5a3b1be` → `6efede4`; #51/#58 `93de739` → `90ead9d` and `1d2a455`; #98 `678a830` → `6894083`; P3 `ca8b785` → `f21f658`; review round 1 `3c584a5` → `a140265`; round 2 `9473872` → `74e2bd1`. Records went in their own commits (`656b391`, `0a36775`, `e5e37a8`). The Tester's tests are in `7a40704`. **One slip:** `90ead9d` was pushed with `make check-fast` red (a comment spelled the read the privacy gate counts); `1d2a455` fixed it, and since then a commit runs only when the checks' exit code is 0 | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m18-wave-5-review.md`: the second Code-Reviewer's **PASS-WITH-MINORS** at `a52c76d`, after the first seat's BLOCKING at `be2434f` (B1: `decodeIfPresent` producing a URL passed both gates). `docs/reviews/m18-wave-5-tester.md`: **PASS-WITH-MINORS**. Seats ran one after another, each in its own worktree behind command guards (D-174) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (the owner's ruling, 2026-09-29); the M18 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester injected 91 faults: 74 killed, 6 equivalent, 11 survived (kill rate 87.1 %). Each survivor got its test in `7a40704`, and with them all 85 non-equivalent faults are killed. The two Code-Reviewers ran 11 and 29 mutants. Every fault was restored in place and checked by sha256, `git hash-object` and `git diff --quiet` | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The Swift tripwire runs through `swift test` (`OfflineTestCase.swift`, 52 classes). The declaration gate runs through `make client-decls`, self-test first, with its rules on canned compiler output in `tests/unit/test_client_decl_gate.py`. The text gate runs through the client files (`test_router_hints.py`). Read-only opens are checked through the routes, the boot check and the refresh, with the interpreter's audit event (`test_readonly_uri.py`). The wave rules run through `wave_check.py` and `wave_check_all.py` on built record trees. Records: every PRD citation into this wave's files lands on its test, checked by a script; four older ones are #105 | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | "No test reaches the network": `testARequestAStubDeclinesIsCaughtToo` and a source check that the base fails such a test. "A URL decoded from text is the network outside `EngineClient.swift`": `test_a_url_decoded_if_present_is_the_network_too` and the compiled fixture. "The gap register is only ever a file": `testTheRegisterIsOnlyEverAFileOnThisDevice`. "Every reader opens the artifact read-only at run time": `test_every_reader_opens_the_artifact_read_only_at_run_time`. The single list is #89 | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None by any seat, each attested in its file | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a request in the Swift tests: `URLSession.shared` and `Data(contentsOf:)` (a registered protocol); sessions on `.default` and `.ephemeral` (exchanged getters); any session whose protocols a test sets (an exchanged setter). Background sessions are refused by source. Producers of a URL in the client: `EngineClient.swift` only, by both gates. Producers of a stored score: `_store_scores` and `Carry.restore`, both under the same rules | ✅ |
| 9b | Scope & draft PR | Draft PR on `wave/m18-w5` against `main`; merge #99 and #109 first. Delivered: P0-P3. Moved to W6 by amendment: #60, #85. Filed and triaged: #107, #108, #110 | ✅ |
| 9a | Economy | `git diff --shortstat 487dfc2 HEAD`: 51 files, +3173/−178 before this close, mostly records (the architecture rewrite, the PRD rows) and tests. Code (`src/`, `scripts/`, `ios/ModelRanking/`): 11 files, +202/−11. VARIANCE noted: a records-and-gates wave with two Code-Reviewer rounds and a Tester | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make client-decls · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. Not run, by the owner's instruction (2026-10-01, NO-ENVIRONMENT): the simulator. A review probe trapped a scratch `xctest` process once; it was not a gate, and #108 carries it. Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-04 · Wave commit range: `487dfc2..HEAD` (W5's own work on top of W4)

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M7 | fixed `74e2bd1` (the register test's comment and place); the text gate's other spellings are on #107 |
| review M8 | fixed `74e2bd1` |
| review M9 | fixed `74e2bd1` |
| review M10 | fixed `74e2bd1` |
| review M11 | fixed `7a40704` (background sessions refused by source; an alias to XCTestCase refused) |
| review K3 | #110 |
| review R4 | #108 |
| tester T1 | fixed `7a40704` |
| tester T2 | fixed `7a40704` |
| tester T3 | fixed `7a40704` |
| tester T4 | fixed `7a40704` |
| tester T5 | fixed `7a40704` |
| tester T6 | fixed `7a40704` |
| tester T7 | fixed `7a40704` |
| tester T8 | fixed `7a40704` |
| tester T9 | fixed `7a40704` |
| tester T10 | fixed `7a40704` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        ios/EngineTests/OfflineTestCase.swift (new) and every Swift test class (its base) ·
                ios/ModelRanking/Engine/FrontDoor.swift · scripts/client_decl_gate.py ·
                scripts/client_decl_fixtures/ (new) · scripts/wave_check.py · scripts/wave_check_all.py ·
                src/app/workflows/{build,ingest}.py · src/app/adapter/main.py (a docstring id)
                tests/unit/test_{router_hints,client_decl_gate,swift_tests_offline,readonly_uri,
                wave_check_m18_rules,carry_forward,stored_scores_are_bounded,calibrate_board,
                board_standings,engine_service,engine_address,swift_test_manifest,survey_floors,
                budgets_endpoint,recommend_assistant}.py
                docs/prd.md · docs/decisions.md (D-174; notes on D-154, D-156, D-157) ·
                docs/architecture.md · AGENTS.md (§1, §4) · docs/plans/m18-plan.md · docs/skip-budget.txt (76)
                docs/reviews/m18-wave-5-{review,tester}.md
Mutant set author: the independent seats (two Code-Reviewers, the Tester); the lead agent's own
                faults are supporting evidence only
Observed RED:   the first Code-Reviewer's mutant decoding a `URL?` in ContentView.swift turned
                test_a_url_decoded_if_present_is_the_network_too red on 3c584a5
Owner instruction: "you don't need to wait for the other PR, I'll merge in the right order, carry on"
                (2026-10-04, translated from Turkish), and "proceed with what you recommend"
                (2026-09-29, translated from Turkish). Delivered: W5 stacked on W4, its decisions
                recorded (D-174, the P4 amendment)
K.8 contracts:  NONE served: /v1 unchanged. The Swift test base `OfflineTestCase` is new, and every
                test class depends on it
Stopped at three attempts: none
Hand-kept lists: client_decl_gate.FIXTURE_REFUSALS (what the fixture must produce); the text gate's
                EGRESS patterns (one added); wave_check's footprint field names for the HIGH rule
```
