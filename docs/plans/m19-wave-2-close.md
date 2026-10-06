---
record_type: wave
id: m19-wave-2-close
status: draft
process_version: v6.6
date: 2026-10-06
---
# Wave-Close Checklist — M19 Wave 2, the phone's promises, held by what the code does

**Six issues, as the milestone plan's W2 names them, with #132 left by the valve (the W2 amendment).**

**What the phone promises, now held on the compiled module.**
- #85 (D-180): the two privacy sinks, `EngineClient.swift` and `StandingsStore.swift`, are checked on
  what the compiler resolved. A sink holds only values, reads no other file's mutable state, calls
  only what is listed, and the code it runs elsewhere reads no shared mutable state. Only the engine's
  answer and the store build standings, only the engine client builds a client on an address, only the
  store builds or saves to a store, a kept type is extended and conformed nowhere else, and no file
  touches memory unsafely. These are the routes D-180 names; gap G-1 holds the rest (#172).
- #60 (D-181): arithmetic on a served number, every number a decoded type stores, is followed through
  the names, operators and methods D-181 lists, and a sort is keyed on its resolved receiver and
  counted. Gap G-2 holds the rest (#171, #173).
- #107: a URL made by any call, held in any type or made by a cast, is the network outside its files.
- #110: the text pins read only code some build compiles, in three values, and a directive inside a
  comment or a string is text.
- #144 (INV-85): the engine session neither keeps nor sends a cookie.
- #138 (D-182): each pick carries its model's id on `/v1`, and the app's cards follow it.

**What the wave does not claim.** The W2 criterion, "by any route the compiler accepts" and "however
the value is named", is not met as worded: no check over the compiler's declarations proves either.
Three Code-Reviewers ran; the first two were BLOCKING on routes past the rules of the day. The privacy
routes were closed by rules that do not grow by spelling; the arithmetic shapes the second review
found were not chased a third time, and the records were narrowed instead, as it recommended
(`m19-plan.md`, the second W2 amendment).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m19-wave-2-plan.md` (deleted in this close) and `docs/plans/m19-plan.md` §2 W2: **HIGH**, since `EngineClient.swift`, `src/app/adapter/main.py` and the client gates are security globs (`m19-plan.md` §3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #85 (`7f0dd29`, `a37f6a3`), #60 (`74f0a60`, `dc68029`), #107 (`250a03c`, `1ba65c0`), #110 (`d2dd6b9`, `40ec649`), #144 (`c79444c`, `89f724d`), #138 (`41c300a`, `68609b3`); the first review (`9a5785f`→`28fd9df`, `22c3d1c`→`ef2f4fc`, `72ead87`→`6752538`), the author's own probes (`90bfbd7`→`14087b4`, `ce03842`→`e05b6fc`), the second review (`4fa43cc`→`42433cf`). Each red commit's only failures were its own tests (measured with `make check-fast`); one red test checked too loosely and was tightened in its fix, as `42433cf` says. Slips in row 8 | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | Code review, three rounds by three seats. Round 1 is `docs/reviews/m19-wave-2-review-round-1.md`, BLOCKING (B1, B2), on `1843437..40bb4d1`. Round 2 is `docs/reviews/m19-wave-2-rereview.md`, BLOCKING (B1 to B3), on `1843437..4e737ea`. Round 3, the verdict of record, is `docs/reviews/m19-wave-2-review.md`, **MINOR**, on `1843437..c327192`: every blocking mutant of both earlier rounds refused, the records claiming what the code holds. The Tester is `docs/reviews/m19-wave-2-tester.md`, **MINOR**, on `1843437..fc369d5`. Each seat had its own worktree at its range's end, its own venv from the locks and a copy of the served artifact, behind stubs refusing `launchctl`, `simctl` and `xcodebuild` (D-174). The round-1 file moved from `-review.md` (`c327192`, the M18-W3 precedent) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172. The M19 closure seat reads this slice, from `docs/security-invariants.md` (INV-62, -63, -66, -67, -76, -78 and INV-85 changed here; gaps G-1 and G-2 open in part) | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 78 faults: 71 killed as delivered (91 %), 77 with its five tests (`2ef2024`); S15b is its M6, a record narrowed in `6a576ae`. Every fault restored byte-identical (sha256). The reviewers' mutants were replayed by the author on the shipping client, each planted alone in all four configurations and restored byte-identical: the first review's A0 to A14 and O1, with eight more shapes the author found (`14087b4`), S3, S2b and F2; the second review's P3w, U8, U9, U10, U11, S5, S5b, O2 and O4 (`42433cf`). The third review replayed every blocking mutant of both earlier rounds | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-GAP-001 and REQ-APP-005 through `make client-decls`, which compiles the shipping client in four configurations and fails on any refusal (`main()`; `test_client_decl_gate.py::test_main_refuses_a_release_dump_that_carries_a_ui_test_hook`, `::test_a_permission_the_client_no_longer_uses_fails_the_gate`), and each rule through `problems(references(...))` on the compiled fixture. INV-85 through the session the app builds (`EngineClientTests.swift::testTheShippedSessionNeitherStoresNorSendsACookie`, via `EngineClient()`). REQ-API-001 through `GET /v1/recommendations` (`test_api_v1.py::test_each_pick_carries_the_id_of_the_model_it_ranks`) and `recommend()` (`test_recommend.py::test_two_models_that_share_a_name_keep_their_own_ids`, `::test_each_pick_carries_its_own_models_id_the_budget_pick_included`); the cards through `pickCards` (`AnswerPlanTests.swift::testTwoModelsThatShareEveryShownValueAreTwoCards`). `make ui-test` 18/18 on `fc369d5` | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | `docs/security-invariants.md`: INV-63 (`test_a_url_inside_another_type_is_made_all_the_same`, `::test_a_url_out_of_any_by_a_cast_is_made`), INV-66 (`test_a_sink_holds_nothing_another_file_can_change`, `::test_the_code_a_sink_runs_reads_no_shared_mutable_state`, `::test_a_kept_type_is_extended_only_in_its_own_file_and_conforms_to_no_protocol_the_app_declares`, `::test_no_file_touches_memory_unsafely`), INV-76 (`test_arithmetic_on_a_served_number_is_refused_whatever_carries_it`), INV-78 (`test_router_hints.py::test_a_branch_no_build_compiles_is_dropped_however_its_condition_is_spelled`, `test_ios_client_contract.py::test_a_pin_here_never_reads_a_branch_no_build_compiles`), INV-85 (`test_turning_cookies_off_is_the_one_cookie_symbol_allowed_and_only_in_the_door`). Five rows hold in part, each naming its gap | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every mutant was planted from Python, restored from saved bytes in a `finally` and compared. **Slips**, none pushed: two docs-only commits (`d3bb627`, `c327192`) were gated on `make check-records` rather than `make check-fast`, which ran clean on the tree right after them. The session started outside the repository, so its hooks were not loaded (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Enumerated by each review seat's producer section, last in `docs/reviews/m19-wave-2-review.md`: the boards request (`EngineClient.boards()`, `fetch`, `init(baseURL:session:)`), the standings file (`FetchedStandings.init(payload:)` with its reach, `StandingsStore.init(url:)`, `save(_:at:)`), the URL makers, the served numbers and orderings, what the pins read, and the cookie configuration, each with its citing test. Gaps tracked: G-1 (#172), G-2 (#171, #173) | ✅ |
| 9b | Scope & draft PR | Delivered: #107, #110, #144, #138, #60 (its probes and its asked change). In part: #85 (its two mutants refused; the remaining routes are #172). Deferred by the valve: #132. Filed: #168, #169, #170, #171, #172, #173, #174, #175. Draft PR on `wave/m19-w2` against `main`, opened in this close | ✅ |
| 9a | Economy | `git diff --shortstat 1843437 HEAD`: 32 files changed, 7472 insertions(+), 60 deletions(-) before this close's own records. Over the ~400-line guide: the code is 6 files, 1054 insertions(+), 15 deletions(-), mostly the gate; 3,306 lines are the fixture's committed dump, and the rest are tests, four verdicts and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make ui-test (18/18) · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. The per-wave security pass is not run by rule (D-172). Bypass: none; the slips are in row 8 | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-06 · Wave commit range: `1843437..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| round-1 review B1 | fixed `ef2f4fc` (with `14087b4`; the records narrowed in `e150b7c`) |
| round-1 review B2 | fixed `28fd9df` |
| round-1 review M1 | fixed `6752538` |
| round-1 review M2 | fixed `6752538` |
| round-1 review M3 | fixed `6752538` |
| round-1 review M4 | fixed `ef2f4fc` |
| round-1 review M5 | fixed `ef2f4fc` |
| round-1 review M6 | fixed `f135c05` |
| round-1 review M7 | fixed `b48d8b0` |
| round-1 review M8 | fixed `b48d8b0` |
| round-1 review M9 | fixed `93afe06` |
| round-1 review K1 | #168 |
| round-1 review K2 | #169 |
| round-1 review R1 | #170 |
| round-1 review R2 | fixed `ef2f4fc` |
| round-1 review R3 | fixed `ef2f4fc` |
| rereview B1 | fixed `42433cf` |
| rereview B2 | fixed `42433cf` |
| rereview B3 | #173 (the records narrowed in `e150b7c`, as the review recommended) |
| rereview M1 | #172 |
| rereview M2 | fixed `42433cf` |
| rereview M3 | fixed `42433cf` |
| rereview M4 | fixed `42433cf` |
| rereview M5 | #173 |
| rereview M6 | fixed `42433cf` |
| rereview K1 | fixed `42433cf` |
| rereview R1 | #173 |
| rereview R2 | fixed `e150b7c` |
| rereview R3 | #173 |
| review M1 | fixed `fc369d5` |
| review M2 | #173 |
| review K1 | #174 |
| review R1 | #175 |
| review R2 | refused — a row copied between `ranked_with_ids` and the picks fails loudly with a `KeyError` on the first request of every surface, which `test_recommend.py` and `test_api_v1.py` run on every suite; identity is #102's rule, and D-182 follows it on purpose |
| review R3 | #175 |
| tester M1 | fixed `2ef2024` |
| tester M2 | fixed `2ef2024` |
| tester M3 | fixed `2ef2024` |
| tester M4 | fixed `2ef2024` |
| tester M5 | fixed `2ef2024` |
| tester M6 | fixed `6a576ae` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        docs/decisions.md docs/plans/m19-plan.md docs/plans/m19-wave-2-plan.md docs/prd.md docs/security-invariants.md docs/reviews/m19-wave-2-review-round-1.md docs/reviews/m19-wave-2-rereview.md docs/reviews/m19-wave-2-review.md docs/reviews/m19-wave-2-tester.md ios/EngineTests/AnswerPlanTests.swift ios/EngineTests/EngineClientTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/Engine/AnswerPlan.swift ios/ModelRanking/Engine/EngineClient.swift ios/ModelRanking/Engine/Models.swift scripts/client_decl_fixtures/{Combine,ContentView,Detail,EngineClient,Models,Router,StandingsStore}.swift scripts/client_decl_gate.py src/app/adapter/main.py src/app/workflows/recommend.py tests/unit/data/g2_fixture_ast.txt tests/unit/test_api_v1.py tests/unit/test_client_decl_gate.py tests/unit/test_ios_client_contract.py tests/unit/test_recommend.py tests/unit/test_router_hints.py tests/unit/test_uncertainty_contract.py docs/plans/m19-wave-2-close.md (and the plan deleted)
Mutant set author: the Tester seat (78 faults) and the three Code-Reviewer seats; the author's replays are supporting evidence only
Observed RED:   the Tester's G9, G29, G30, C1 and E4 survived the suite and die on its five tests (`2ef2024`); the first review's A0 to A14 and O1 and the second review's privacy mutants survived the gate and die on the rules of `ef2f4fc`, `14087b4` and `42433cf`
Owner instruction: "all merged" (owner, 2026-10-06), merging the M19 plan, which the owner approves by merging it (m19-plan.md); "merged continue" (owner, 2026-10-06), after W1; and "proceed with what you recommend, don't ask" (owner, 2026-09-29, translated from Turkish). W2 delivers the plan's second wave as amended three times
K.8 contracts:  client_decl_gate.NETWORK_FILE, FILESYSTEM_FILES, FIXTURE_REFUSALS, references(), problems() unchanged in signature; PROVENANCE, SINK_FILES, SINK_HELD_TYPES, SINK_CALLS_PERMITTED, KEPT_TYPES, UNSAFE, FIELD_KINDS, ARITHMETIC_PERMITTED (keyed by function), SORTS_PERMITTED, NOT_SERVED and SNAPSHOT added or reshaped; EngineClient gains init() and its init(baseURL:session:) takes no default address; /v1 picks gain `model_id` (additive, D-182)
Stopped at three attempts: NONE. The third Code-Reviewer was MINOR; the arithmetic slice was narrowed at the second, not taken out
Hand-kept lists: SINK_HELD_TYPES, SINK_CALLS_PERMITTED, FIELD_KINDS, ARITHMETIC_PERMITTED, SORTS_PERMITTED, NOT_SERVED, UNSAFE; each permission fails the gate when the shipping client no longer uses it
```
