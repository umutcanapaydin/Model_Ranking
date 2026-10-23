---
record_type: review
id: release-tester
status: draft
seat: independent
process_version: v7.2
date: 2026-10-23
---
# Release Tester Review

This verdict replaces the one of 2026-10-17 (reviewed head `9217c6c`, run golden-night), which stays in git history.
It is the light-mode Tester for release v0.1.0, dispatched by `/going-live`.

**Reviewer:** Tester subagent (`.claude/agents/Tester.md`, read from `main`). I had fresh eyes and wrote none of the
range's product code or tests. The only tests I wrote are the ones this review lists under "Tests added".
**Independent:** yes
**Date:** 2026-10-23
**Commit range:** `9217c6cf6b110c4e04c4ce48edd3dfd545b0e059..044a3091e25486e6f651339a17d26e9b8fde2999` (309 commits,
main's tip after #409), plus this review's two test commits `3e227ae` and `471bd73`.
**Reviewed head:** 471bd736a0995715dc62838f13e4b0fcbf4d4f1a
**Risk tier:** HIGH. The range touches the deploy gate (`scripts/deploy_gate.py`), the hosted deploy scripts
(`scripts/deploy_hosted_engine.sh`, `scripts/nightly_hosted.sh`), the Bash guard (two owner bundles), CI installs, the
compiled client gate, and five new ingestion parsers.
**Seat:** my own worktree on `review/release-tester-v0.1.0`, cut from `044a309`, with its own `.venv` (`make install`,
`make hooks`) and a copy of the main clone's `advisor.db`; a second detached worktree at `9217c6c` measured the base
coverage. No launchd service, Fly, or owner data directory was touched; every probe ran in-process or on scratch
repositories the tests build. Scratch files stayed outside the repository.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: this seat read the code, the tests and the issues, not the implementers' sessions.

## Verdict
MINOR -- nothing BLOCKING is open. Every acceptance criterion in the range has a passing citing test or, where the
criterion is a measurement or an owner action, its record. Two faults stayed green and four touched modules lost
coverage; this review closed all six with tests. Three MINOR findings remain (M1-M3), one of them a criteria-meaning
question for the owner (M1).

## Scope

Everything merged since `9217c6c`: run bug-night (#335, #383), the DevFlow v7.2 upgrade (#327), #349, #350 (docs),
run night-351 (#357: #352, #358, #360), #365, #366, #368, run night-1021 (#370, #385: #372, #380-#384), #386,
run queue-1021 (#394: #388, #395, #397-#399, #402, #407) and its owner bundle (#409). The issues they close, with the
criteria in each issue body (and the ADRs they name: D-207 to D-219), are the acceptance criteria below.

## Suite result

| Run | Head | Result |
|---|---|---|
| `make check` | `044a309` | exit 0. pytest 4464 passed, 37 skipped; coverage-floor PASS; check_records PASS; conformance PASS (33); swift-test PASS: 727 tests, each in the manifest; SlowTierTests 7 of 7; client-decls PASS, 22 files in 4 configurations |
| commit-msg `make check-fast` | `3e227ae`, `471bd73` | PASS, 6 of 6 legs, each time |
| `make check` | `471bd73` | exit 0. pytest 4475 passed, 37 skipped; coverage-floor PASS; check_records PASS; conformance PASS (33); swift-test PASS: 727 tests; SlowTierTests 7 of 7; client-decls PASS, 22 files in 4 configurations |
| CI `ci.yml` on main | `044a309` | `test (py3.14)`, `install-and-governance`, `secret-scan`, `dep-audit` success; `test (py3.12)` cancelled at its 15-minute limit with no failing test (M2). The same tree (`git diff 9a50c08 044a309` is empty) passed every job on PR #409's run 39782357385 |
| CI `contract-tests.yml` on main | `044a309` | success: the live contract tests of every new source ran against the real upstreams |

Every pytest skip is an environment skip: `RUN_CONTRACT_TESTS` (the live contracts, run by CI's contract job, green
above) or `EPOCH_DATA_DIR` (the owner's Epoch bundle). No skip, `xfail` or `XCTSkip` was added in the range.

**Coverage on touched code** (`src/` modules changed in the range; base measured at `9217c6c`, head from the runs
above). Total 92.2 % to 92.6 at `044a309` and 92.8 at `471bd73`.

| Module | Base | `044a309` | `471bd73` |
|---|---|---|---|
| `adapter/main.py` | 98.3 | 98.3 | 98.3 |
| `clients/arena.py` | 92.5 | 94.3 | 94.3 |
| `clients/datacurve.py` | new | 98.7 | 98.7 |
| `clients/deepswe.py` | 76.8 | 78.0 | 78.0 |
| `clients/litellm.py` | 98.0 | 98.2 | 98.2 |
| `clients/livebench.py` | new | 94.7 | 94.7 |
| `clients/metr.py` | new | 95.5 | 95.5 |
| `clients/osworld.py` | new | 95.0 | 95.0 |
| `clients/protocols.py` | 100.0 | 100.0 | 100.0 |
| `clients/simplebench.py` | new | 100.0 | 100.0 |
| `clients/terminalbench.py` | 90.3 | 90.3 | 90.3 |
| `workflows/board_tables.py` | 100.0 | 100.0 | 100.0 |
| `workflows/build.py` | 95.3 | 95.3 | 95.3 |
| `workflows/categories.py` | 100.0 | 100.0 | 100.0 |
| `workflows/coverage.py` | 94.3 | 94.4 | 94.4 |
| `workflows/families.py` | 100.0 | 100.0 | 100.0 |
| `workflows/ingest.py` | 97.8 | 98.3 | 98.3 |
| `workflows/public.py` | 86.7 | 87.0 | 87.0 |
| `workflows/rank.py` | 99.0 | 99.0 | 99.0 |
| `workflows/recommend.py` | 95.5 | 94.7 | 96.5 |
| `workflows/refresh.py` | 95.7 | 95.7 | 95.7 |
| `workflows/registry.py` | 99.5 | 98.8 | 99.5 |
| `workflows/sources.py` | 100.0 | 100.0 | 100.0 |
| `workflows/standings.py` | 100.0 | 100.0 | 100.0 |
| `workflows/subscribe.py` | 96.3 | 95.6 | 96.4 |
| `workflows/yaml_guard.py` | 100.0 | 95.5 | 100.0 |

At `044a309` four touched modules were below their base, each on lines the range added and no test reached:
`recommend.py:293-294` and `:539-540` (D-218 clause 1's two refusals), `registry.py:1027-1028` (a curated rule with a
media modality, #378), `subscribe.py:435` (the quality-only plan answer, #378) and `yaml_guard.py:137, 147-148` (the
recursion catches of the queue-1021 integration review's M2). A coverage drop on a touched module is BLOCKING
(`permission-matrix.md` section 11), so this review wrote the tests; each is red with its guard removed (faults SU1,
Y1, Y2, R1, R2, RG1 below). The other touched modules are at or above their base; new modules: `datacurve.py` 98.7,
`livebench.py` 94.7, `metr.py` 95.5, `osworld.py` 95.0, `simplebench.py` 100.

## Acceptance-criterion coverage

Each line names the citing test as `file:line` and what it asserts. All GREEN at `471bd73`.

**Run bug-night**
- **#295 (D-208)** a Turkish verb clause before "yapay zeka" names the task:
  `ios/EngineTests/TaskBeforeGeneralWordsTests.swift:7`, `:15`, `:23` (the rule's helpers); end to end, the golden
  question's `known_miss` mark is gone and `ios/EngineTests/GoldenQuestionTests.swift` asserts it (fault SW2b red).
- **#326** an encoded `..` in the raw path is refused: `tests/unit/test_terminalbench_4.py:158` (T1 red).
- **#331** ci-diff reads `gp_version` under the marker's comment lines: `conformance/test-ci-diff.py:53`.
- **#332** `.mcp.json` stays removed (absent at head) and the two record corrections: documents only, held by
  `make check-records`. No code criterion.
- **#325** ignored, untracked documents are not graded; tracked ones still are:
  `tests/unit/test_documents_skip_ignored.py:47`, `:54` (LR1, LR2 red).
- **#330** a far-off id is a name, not the next place: `conformance/test-next-adr.py:31` (NA1 red).
- **#328** a timed-out hook call is reported by its case, and fixture git starts no maintenance:
  `tests/unit/test_bash_guard_conformance_timeout.py:28`, `tests/unit/test_guard_fixture_maintenance.py:28`.
- **#341** a committed conflict marker fails; a heading underline and a fenced example do not:
  `tests/unit/test_conflict_markers.py:39`, `:46`, `:51` (CM1 red).
- **#314 (D-209 clause 6)** a file over the ceiling is refused before it is read, and a test plants one:
  `ios/EngineTests/KeptAnswerTests.swift:95`, `:279`; the read order: `tests/unit/test_answers_size_before_read.py:30`,
  `:37` (a source pin; see Test integrity).
- **#322** aliases, enum payloads, the existential and the unseen allowed sides:
  `tests/unit/test_kept_answer_provenance.py:197`, `:207`, `:218`, `:236`.
- **#319 (D-209 clause 5)** review-need derives its policy scripts:
  `tests/unit/test_review_need_derived_policy.py:24`, `:34`, `:48`, `:64`, `:77`, `:102`, `:111` (RN1 red).
- **#309 (D-209 clause 8)** a request in a tearDown that skips `super` fails its own test:
  `ios/EngineTests/WholeTestObserverTests.swift:7`.
- **Owner bundle #383 (D-209): #256, #287, #305, #317, #318, #320, #344** --
  `tests/unit/test_bash_guard_bounds.py:814` (#256), `:887` (#287), `:929` (#305), `:956` (#317), `:1057` (#318),
  `:1007` (#320), `:1176` (#344); G3 red. **#81**: the workflow edits are the owner's; the required checks are held
  to `ci.yml`'s jobs by `conformance/test-ci-yaml.py:338`, and `governance-contract` is gone from both.

**DevFlow v7.2 (#327, D-207)** -- the project's rules kept where v7.2 meets them are held by the suites above
(`make check` green). One test changed its assertion with the policy: see Test integrity.

**Run night-351 and its follow-ups**
- **#351** -- the measurement harness: `tests/unit/test_model_tier_score.py:30`, `:39`, `:46`; a text that names an
  AI is a search unless it instructs the app: `ios/EngineTests/ReadingTests.swift:1006`, `:1024`; the glow:
  `ios/EngineTests/GlowStyleTests.swift:9`, `:17`; greedy decoding: `ios/EngineTests/RefinementBoundaryTests.swift:109`.
  The bar is a measurement on m25: see M1.
- **#348 (D-212 clause 1)** "no eligible model" says what the evidence held: `tests/unit/test_recommend.py:750`.
- **#354** focus prewarms once, only where the model is ready, and a send without focus still routes:
  `ios/EngineTests/PrewarmTests.swift:9`, `:15`, `:24` (SW4b, SW5b red).
- **#355** m25 written, sealed and judged once: `docs/research/reading-heldout-m25-result.md`. A measurement, not a
  test: see M1.
- **#361** an instruction only the model reads is not made a search by the AI it names:
  `ios/EngineTests/ReadingTests.swift:1035`, `:1051` (SW3b red).
- **#362** the S1 pin reads macOS 26's and macOS 27's schema, and a free string is never a choice:
  `ios/EngineTests/RefinementBoundaryTests.swift:119`, `:183`, `:191`, `:199`.
- **#363** a declaration printed with its header is read by every rule that reads its name:
  `tests/unit/test_client_decl_gate.py:506`; the manifest's sort: `tests/unit/test_swift_test_manifest.py:135`.
- **#367** the locks pin `certifi==2026.10.19` and `uv==0.13.4` (every lock under `requirements/`, checked here);
  the advisory is the `deps` leg's to hold, which this seat did not run.

**Run night-1021 and the merge of 2026-10-21**
- **#242 (D-214 clause 1)** nothing refused before is lost, and the twins are refused:
  `tests/unit/test_client_decl_gate.py:1060`, `:1073`, `:1097`.
- **#373** `tests/unit/test_client_decl_gate.py:1394` (C1, C2 red). **#374** `:1413` (C4 red).
  **#375** `:1430`, `:1450` (C5 red). **#371 (D-218 clause 4)** `:1485`, `:1517`, `:1535` (C3 red).
- **#376 (D-215)** Epoch's WebDev copy and the OpenRouter copies are gone; MMLU/HELM and SWE-bench stay credited:
  `tests/unit/test_webdev_board.py:39`, `:52`; `tests/unit/test_public_artifact.py:40`, `:61`, `:142`;
  `tests/unit/test_credits.py:66` (LL1, PB1 red). D-101's amendment passes `make check-records`.
- **#265 (D-216)** agentic-coding reads Datacurve's own leaderboard: `tests/unit/test_datacurve.py:45`, `:64`, `:72`;
  `tests/unit/test_datacurve_move.py:33`, `:46`, `:92`; contract: `tests/integration/test_scores_contract.py:39`
  (DC1, DC2 red).

**Run queue-1021 and its owner bundle**
- **#387 (D-217)** the night refreshes on the kept state, keeps only a good night, deploys only past the gate, and
  runs only on main: `tests/unit/test_nightly_hosted.py:63`, `:91`, `:273`, `:336`, `:373`, `:418` (N3 red). "Fresh
  with the Mac off" is the owner's to show once the workflow is installed (`docs/owner-actions.md`, the rows of
  2026-10-21); `.github/workflows/` does not hold it yet.
- **#389** the step that opens the database holds no token, and the token's step ships only the stamped copy:
  `tests/unit/test_nightly_hosted.py:200`, `:208`, `:244` (N1, N2, H4 red).
- **#391** the deploy ships its own checkout: `tests/unit/test_deploy_hosted.py:77`, `:90`, `:108` (H1, H2, H3 red).
- **#378 (D-218 clause 1)** five media surfaces on quality only:
  `tests/unit/test_media_surfaces.py:71`, `:123`, `:161`, and `:219` (added here); routing:
  `ios/EngineTests/MediaRoutingTests.swift:36`, `:57`; contract: `tests/integration/test_arena_openrouter_contract.py:43`
  (SW6b, SU1 red).
- **#379 (D-219)** four boards served, six skipped with their reasons in D-219's table:
  `tests/unit/test_osworld.py:46`, `:152`, `:257`, `:268`; `tests/unit/test_metr.py:40`, `:62`;
  `tests/unit/test_livebench.py:52`, `:72`; `tests/unit/test_simplebench.py:40`, `:152` (added here);
  `ios/EngineTests/LongTasksRoutingTests.swift:24`; contracts: `tests/integration/test_scores_contract.py:51`, `:63`
  (O1-O3, MT1, LB1, SB1, SB2 red).
- **#405** a quality-only surface is no plan-coverage gap; a priced one at zero still is:
  `tests/unit/test_coverage.py:449` (CV1 red).
- **#390** every `gh` spelling that starts a deploy workflow is a deploy:
  `tests/unit/test_deploy_gate_dispatch.py:196`, `:203`, `:207`, `:247`, `:291`, and through the guard `:334`
  (D1, D2, D4 red).
- **#392** no workflow restores a cache, and every install is hash-checked:
  `tests/unit/test_ci_installs.py:254`, `:298`, `:304`, `:319`, `:359` (CI1 red).
- **#400** `env -S` read anywhere in a cluster, an unreadable option refused:
  `tests/unit/test_bash_guard_env_split.py:95`, `:105`, `:121`, `:151`, `:167`, `:172` (G1, G2, G4 red).

## Red to green on reported symptoms

Each fix in the range landed after a red test commit (`git log 9217c6c..044a309`: "reproduce #N (red)" for #295,
#326, #331, #325, #330, #328, #341, #314, #322, #319, #309, #348, #354, #361, #362, #363, #373, #374, #375, #376,
#387, #389, #391, #371, #378, #379, #390, #405; the owner bundles' agent halves `f716219` and `22a7596`). The fault
injections below re-create each defect, and each turns its test red at `471bd73`.

## Fault-injection table

Protocol, one atomic sequence per row, logged by a scratch runner outside the repository: md5 the file; replace one
exact string that occurs once; run the named tests; revert in place by string replacement at the injected offset; md5
again. Every file came back byte-identical, and `git status` was clean after each batch apart from this review's own
test edits. `git checkout` and `git restore` were never used.

| # | Behaviour broken | File | Tests | Result |
|---|---|---|---|---|
| D1 | `gh run rerun` is no deploy (#390) | `scripts/deploy_gate.py` | test_deploy_gate_dispatch | RED |
| D2 | the dispatches API is no deploy (#390) | `scripts/deploy_gate.py` | test_deploy_gate_dispatch | RED |
| D4 | a base workflow git cannot show reads as complete | `scripts/deploy_gate.py` | test_deploy_gate_dispatch | RED |
| H1 | `MODEL_RANKING_REPO` read again (#391) | `scripts/deploy_hosted_engine.sh` | test_deploy_hosted | RED |
| H2 | a call from another tree not refused (#391) | `scripts/deploy_hosted_engine.sh` | test_deploy_hosted | RED |
| H3 | git's place variables honoured | `scripts/deploy_hosted_engine.sh` | test_deploy_hosted | RED |
| H4 | `--ship` ships a copy its stamp does not name (#389) | `scripts/deploy_hosted_engine.sh` | test_nightly_hosted | RED |
| N1 | the refresh runs beside `FLY_API_TOKEN` (#389) | `scripts/nightly_hosted.sh` | test_nightly_hosted | RED |
| N2 | the token's step derives from the database (#389) | `scripts/nightly_hosted.sh` | test_nightly_hosted | RED |
| N3 | a stale gate still deploys the night (#387) | `scripts/nightly_hosted.sh` | test_nightly_hosted | RED |
| CI1 | an unhashed `pip install` in the night (#392) | `scripts/ci/nightly-hosted.yml` | test_ci_installs | RED |
| G1 | an unreadable `env` cluster passes (#400) | the guard, a scratch copy | env_split + bounds | RED (3) |
| G2 | `-S` read only at a word's start (#400's defect) | the guard, a scratch copy | env_split + bounds | RED (15) |
| G3 | a command substitution read as safe (#344) | the guard, a scratch copy | env_split + bounds | RED (5) |
| G4 | `env -S` escapes read with the shell's rules (#400) | the guard, a scratch copy | env_split + bounds | RED (26) |
| T1 | `%` in the raw path passes (#326) | `src/app/clients/terminalbench.py` | test_terminalbench_4 | RED |
| O1 | OSWorld member size cap off (#379) | `src/app/clients/osworld.py` | test_osworld | RED |
| O2 | OSWorld resolved-cells cap off (#379) | `src/app/clients/osworld.py` | test_osworld | RED |
| O3 | OSWorld doctype and entity refusal off (#379) | `src/app/clients/osworld.py` | test_osworld | RED |
| MT1 | a negative METR horizon kept (#379) | `src/app/clients/metr.py` | test_metr | RED |
| LB1 | a LiveBench score past 100 kept (#379) | `src/app/clients/livebench.py` | test_livebench | RED |
| SB1 | an unranked SimpleBench row kept (#379) | `src/app/clients/simplebench.py` | test_simplebench | RED |
| SB2 | a SimpleBench model listed twice kept twice (#379) | `src/app/clients/simplebench.py` | test_simplebench | **GREEN**, then RED with the new test |
| DC1 | a Datacurve score outside 0..1 kept (#265) | `src/app/clients/datacurve.py` | test_datacurve | RED |
| DC2 | the lower of two Datacurve runs kept (#265) | `src/app/clients/datacurve.py` | test_datacurve | RED |
| CV1 | plan coverage counts unpriced surfaces (#405) | `src/app/workflows/coverage.py` | test_coverage | RED |
| LL1 | the ingest keeps `openrouter/` copies (#376) | `src/app/clients/litellm.py` | test_public_artifact | RED |
| PB1 | the public artifact keeps them (#376) | `src/app/workflows/public.py` | test_public_artifact | RED |
| SU1 | the quality-only plan answer removed (#378) | `src/app/workflows/subscribe.py` | test_media_surfaces | **GREEN** (no test reached it), then RED with the new test |
| Y1, Y2 | RecursionError let out at the count, the construct | `src/app/workflows/yaml_guard.py` | test_yaml_guard | **GREEN**, then RED with the new test |
| R1, R2 | a priced row with no price; a priced surface with no window | `src/app/workflows/recommend.py` | test_media_surfaces | **GREEN**, then RED with the new tests |
| RG1 | a media-modality curated rule ignored (#378) | `src/app/workflows/registry.py` | test_media_surfaces | **GREEN**, then RED with the new test |
| RN1 | policy tokens are the module names only (#319) | `scripts/review_need.py` | test_review_need_derived_policy | RED |
| LR1 | `documents()` grades ignored scratch (#325) | `conformance/lib_record.py` | test_documents_skip_ignored | RED |
| LR2 | a tracked file under an ignored path skipped (#325) | `conformance/lib_record.py` | test_documents_skip_ignored | RED |
| NA1 | a far-off id is the last place (#330) | `scripts/next_adr.py` | conformance/test-next-adr.py | RED |
| CM1 | the lone separator is no marker (#341) | `scripts/conflict_markers.py` | test_conflict_markers | RED |
| C1 | a curried call on the type not read (#373) | `scripts/client_decl_gate.py` | test_client_decl_gate | RED (the compiled self-test) |
| C2 | a key path from a served struct not read (#373) | `scripts/client_decl_gate.py` | test_client_decl_gate | RED (the compiled self-test) |
| C3 | the numeric generic rule off (#371) | `scripts/client_decl_gate.py` | test_client_decl_gate | RED |
| C4 | a store URL through a subscript not read (#374) | `scripts/client_decl_gate.py` | test_client_decl_gate | RED (the compiled self-test) |
| C5 | an edited pin reads as intact (#375) | `scripts/client_decl_gate.py` | test_client_decl_gate | RED |
| SW1 | the size not read before the bytes (#314) | `Engine/StandingsStore.swift` | test_answers_size_before_read; KeptAnswerTests | RED (the pin); KeptAnswerTests GREEN, 21 executed |
| SW2b | the verb-clause rule off (#295) | `Engine/Router.swift` | GoldenQuestionTests | RED |
| SW3b | the model's instruction attempt not carried (#361) | `Engine/Router.swift` | GuidingNoteTests | RED |
| SW4b | kept focus prewarms again (#354) | `Engine/FrontDoor.swift` | PrewarmTests | RED |
| SW5b | prewarm where the model is not ready (#354) | `Engine/FrontDoor.swift` | PrewarmTests | RED |
| SW6b | "draw a conclusion" makes a picture (#378) | `Engine/Router.swift` | MediaRoutingTests | RED |

Notes:
- **The guard (G1-G4).** `.claude/hooks/bash_guard.py` is the owner's, and this seat writes nothing under `.claude/`.
  The guard was copied byte for byte (same md5) under the worktree's gitignored `build/`, and
  `test_bash_guard_env_split.py` and `test_bash_guard_bounds.py` were copied beside it with only their `GUARD_DIR`
  line pointed at the copy; the unmodified copy passed 782 of 782 first. The copies were deleted afterwards.
- **The first Swift runs.** SW2 and SW3 first ran under a filter that named a helper class (`TaskBeforeGeneralWordsTests`)
  and the file's name rather than its class (`ReadingTests`), and stayed green. Re-run under the classes that hold the
  behaviour (`GoldenQuestionTests`, `GuidingNoteTests`), both went red. That was the runner's filter, not a hole.
- **SW1.** Removing the size check leaves behaviour unchanged when the file is read and then refused by its length,
  so only the source pin catches it. The pin is red; see Test integrity.

**Mutation kill-rate (advisory).** No mutation runner is wired for this stack. Of the 50 hand-made faults, 43 were
killed by the suite at `044a309` (SW1 by its source pin); all 50 are killed at `471bd73`. Y1, Y2, R1, R2 and RG1 were
aimed at lines the coverage read showed no test reached, so they were green by construction.

## Test integrity

- **Weakened or deleted to green.** Across the range no skip, `xfail` or `XCTSkip` was added. Removed test functions,
  each checked: three Swift image-routing tests (`74d6b6a`, #378 changed the behaviour by D-218 clause 1, and the
  replacements are in `MediaRoutingTests`); `test_local_client_*` (`9bfa886`, the dataset fallback left with #265);
  the OpenRouter and WebDev tests (`01814d2`, replaced by the #376 tests above). One assertion changed with a policy:
  `tests/unit/test_review_need_sensitive_paths.py` now expects `none` for a sensitive name with no HIGH path
  (`ad7c2ad`), as D-207 clause 1 states, and still fails the `hit = []` mutant. `conformance/test-agents-2a.py` and
  `conformance/test-schema-sync.py` left with the v7.2 apply (`7c45a5b`); see M3. No security-invariant test was
  weakened.
- **Mirror tests.** `tests/unit/test_answers_size_before_read.py:30` reads the source for the order of the size
  check and the read; it says so, and no executed test can see the order. `test_bash_guard_bounds.py`'s settings pin
  and `test_nightly_hosted.py`'s workflow-shape tests read files by design.
- **Canonical mocks.** The new sources are faked through `app.clients.fakes.FakeRawSource` and `respx`, as every
  source is; no bespoke stub appeared. Each new source has a live contract test (above), green in CI at `044a309`.

## BLOCKING
- none open. Found and closed in this review: the coverage drops on `recommend.py`, `registry.py`, `subscribe.py`
  and `yaml_guard.py`, and the green faults SB2 and SU1 (tests in "Tests added").

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `docs/research/reading-heldout-m25-result.md` and D-214 clause 2 -- #351's bar as the owner first set it
  (#351's comment, "as proposed", and #355's body) was at least 85% of searches right and beats the wording tier on
  both; D-214 clause 2 restates it as 80% and 80%, citing D-212 clause 3, which names no number. m25 read 82.7% of
  searches, and the wording tier's m25 score is not recorded. #351 and #355 closed on the 80% bar. A criteria-meaning
  question, so it is the owner's: confirm that D-214's bar is the bar, or record the wording tier on m25 and reopen.
- **M2** `.github/workflows/ci.yml` (`timeout-minutes: 15` for the test job) -- `test (py3.12)` was cancelled at its
  limit on the last three pushes to main (`3c7f797`, `a57445b`, `044a309`), each with no failing test; #406 recorded
  one such cancel. The release head's py3.12 proof is PR #409's run on the identical tree. Owner-only (workflow
  change): add this evidence to #406.
- **M3** `conformance/test-schema-sync.py` (removed in `7c45a5b`) -- the check that `schemas/record.schema.json` says
  what `scripts/check_records.py` enforces left with the v7.2 apply, while D-207 clause 4 keeps the schema. Run from
  `9217c6c` against `471bd73` it still passes, so nothing has drifted yet, but nothing now notices drift. Restore it as
  a project test, or file it.

## Known open gaps carried into the release (filed before this review)
#401 (deploy spellings the gate does not see), #403 (a media name that resolves to a priced text model), #404 (two
OSWorld fixes with no test), #396 (four #371 rebuild shapes), #406 and #408 (py3.12 CI timing and a memory-ceiling
flake). None is a criterion of an issue this range closed.

## Tests added this review
- `tests/unit/test_simplebench.py:152` -- #379 (REQ-SRC-013): a model listed twice is one row, the first. Red on SB2.
- `tests/unit/test_media_surfaces.py:219` -- #378 (D-218 clause 1, #405): a quality-only surface gives no plan
  answer under any budget. Red on SU1.
- `tests/unit/test_media_surfaces.py:236` -- D-218 clause 1: a priced row with no price is refused. Red on R1.
- `tests/unit/test_media_surfaces.py:254` -- D-218 clause 1: a priced surface with no value window is refused. Red on R2.
- `tests/unit/test_media_surfaces.py:272` -- #378: a curated rule that declares a media modality names the media model.
  Red on RG1.
- `tests/unit/test_yaml_guard.py:372` -- the queue-1021 integration review's M2: RecursionError at the count and the
  construct steps is the guard's error. Red on Y1 and Y2.
