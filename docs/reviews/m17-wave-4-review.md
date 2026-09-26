---
record_type: review
id: m17-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# M17-W4 Code Review (re-review): board standings to the phone, and the combination on it

**This verdict supersedes the BLOCKING verdict** committed in `cc31cd4` (range `7d7a9ac..939aeb5`).
That version stays in git history. The code comments that cite "review B1" and "review M1" to "review M5" refer to it.
My own findings are numbered from **M6** so the two sets cannot be confused.

**Reviewer:** Code-Reviewer seat, fresh eyes. This is a new seat. I wrote none of this wave's code, tests or
records, and I am not the previous reviewer.
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `7d7a9ac..abf284b` (12 commits, 21 files, +2185 / -34), read as a whole. I read the
review round (`ee312f8` red, `abf284b` fix) against the previous verdict.
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)
**Model routing (HIGH, advisory):** author family Claude (commit trailers `GP-Agent:
claude-code/local-lane`), reviewer family Claude (Opus 5.5). Fallback reason: no second family is
available to this seat. Fresh context: this seat had none of the authoring context.

**What I read first.** I read `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md`
(`git diff --stat 7d7a9ac..HEAD -- .claude .agents AGENTS.md` is empty, so the policy is the base
ref's). Then the wave plan, `m17-plan.md` §W4 (`:74-80`), D-112 (`docs/decisions.md:486`), D-160,
and D-167 with its amendment (`:3082-3133`). I read the code before the commit messages.

**How I worked.**
- **Gate.** `make check-fast` at `abf284b`, with a clean tree: **PASS** in 52.7 s.
  - lint and typecheck: PASS.
  - records: PASS.
  - test: 1444 passed, 23 skipped.
  - client-decls: PASS, 13 files in 4 configurations.
  - swift-test: PASS, 295 tests, exactly the manifest.
- **Mutants.** Each mutant ran in place and was restored by copy. Each restore was checked with sha256 against the pre-mutation hash:
  - `standings.py` dcc105bf…
  - `main.py` 87a6b43a…
  - `StandingsStore.swift` 556c0c66…
  - `Models.swift` 57df1eca…
  - `EngineClient.swift` 386eaaab…
  - `Detail.swift` 654ba7dc…

  `PYTHONDONTWRITEBYTECODE=1` was set throughout. The tree is clean apart from this file.
  - **Killed (9).**
    - The D-112 effort filter dropped (`standings.py:90-91`).
    - `effort` made a constant.
    - `ranking_effort` made `None`.
    - Ties no longer shared.
    - The two-boards refusal made a no-op.
    - The boot-time `ValueError` branch returning `None` (`main.py:234`).
    - The `isFileURL` guard removed from `load()`.
    - `FetchedStandings` keeping the raw bytes instead of re-encoding.
    - The `do/catch` in `boards()` removed.

    I also planted `total += x.position` in `Engine/Detail.swift`, and the position tripwire refused it.
  - **Survived (4).**
    - `_evidence` ordering the run date oldest-first (**M8**).
    - `ValueError` removed from the route's `except` (`main.py:1410`): the whole unit suite passed, 1435 passed (**M7**).
    - The `isFileURL` guard removed from `save()` (**M9**).
    - An aliased position, `let p = s.position; return p + 1`, planted in `Detail.swift` (**R4**).
- **Measured** on the worktree's `advisor.db`, read only. It is the candidate artifact the research record calls "main, with W3": 63 boards, 303 models.
  - The route served through `TestClient`: **499,117 bytes raw, 36,407 gzip**. It returned 6,955 positions in about 60 ms, and a query string gave the same bytes.
  - Each of the 14 surfaces' primary boards compared with `ranked_population`:

    | surfaces | membership | positions along the surface's order | each standing's effort | board size |
    |---|---|---|---|---|
    | the 12 other single-source surfaces | the same | never decrease | equals the surface's pick effort | as the surface |
    | `agentic-coding` (DeepSWE) | the same | never decrease | equals the surface's pick effort | 18, `ranking_effort: "high"`, #1 Gemini 3.8 Flash, #2 GPT-6 Astra, as on the surface |
    | `coding` | differs by design: the surface ranks SWE-bench Verified across two sources | | | |

  - Only `epoch_deepswe_external` holds the DeepSWE benchmark, at five effort levels.
- **Network.** None. I did not call `build()`, did not set `RUN_CONTRACT_TESTS`, and wrote no test.
  I was the only seat in the worktree.

## Verdict
PASS-WITH-MINORS

The previous BLOCKING finding, B1, is resolved. The board a surface ranks at one effort now stands at that
effort, and every standing and board carries the effort D-112 requires to be disclosed. It is pinned by
tests and matches the product's own surfaces on real data. Previous M1, M2, M4 and M5 are resolved, and
so are security S1, S2, S4 and S7. Previous M3 was fixed and then regressed in the same commit: adding
`effort` to every standing grew the payload by about 44 %, and four places still state the old size
(**M6**). Nothing blocks.
- The payload carries no score.
- The request carries nothing about the question.
- Each gate widened for one named file only.
- The ADR was amended, not edited.

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M6** The size facts are stale again, in four places: `src/app/adapter/main.py:218-219`,
  `ios/ModelRanking/Engine/EngineClient.swift:153-155`,
  `docs/research/m17-w4-standings-payload-2026-09-25.md:25-34` and `docs/decisions.md:3132-3133` (the
  D-167 amendment). The fix that added `effort` measured nothing after the change.

  The amendment written in `abf284b` says *"about 350 KB raw and 32 KB compressed"*. The same commit
  adds `"effort"` to every standing and `"ranking_effort"` to every board (`standings.py:104`, `:110`).
  On the same candidate artifact the served route is now **499,117 B raw and 36,407 B gzip**, for
  6,955 positions. So `main.py:218` still says *"6,962 positions, 346 KB (32 KB gzipped)"*, and
  `EngineClient.swift:153-154` says *"About 350 KB … the ceiling is ten times that"*, when 4 MiB is
  about 8.4 times. The research record says *"about twelve times"* (`:30`). It also says the smallest
  board is *"25 models (`epoch_deepswe_external`)"* (`:33`), but under the D-112 filter that board
  ranks **18**. Its table (`:25`) predates the fix.

  The previous M3 was exactly "the size facts disagree with the measurement", and the drift came
  back one commit later. It is not blocking, because every bound still holds with room: the 25,000
  positions are 3.6 times the 6,955 measured, and the 4 MiB are 8.4 times the 499 KB. The fix:
  re-measure at HEAD and correct the three files. Give D-167 a dated addendum line rather than
  editing the amendment's body.

- **M7** `src/app/adapter/main.py:1410-1415`, `:1290-1297`. **The route's refusal path is untested, and
  its log line does not say what the comment promises.**

  Removing `ValueError` from the route's `except` survives the whole unit suite (1435 passed). With
  it removed, a refused payload becomes the global handler's 500 instead of the closed 503. The
  comment says the operator gets a log line. `_warn_once` logs `message % type(exc).__name__`, so the
  line reads *"/v1/boards cannot publish the artifact: ValueError"* and names no source and no metric.

  The comment names the one case this path exists for: a nightly refresh swapping the artifact under
  a running process. That is exactly the case in which the boot check's detailed message never ran,
  so the operator learns only that something failed. The fix: add a route test that plants an
  unattributed source after boot and asserts a 503 with `evidence_unavailable`. Then log the
  exception text for this call, since it names only public source ids, or reword the comment.

- **M8** `src/app/workflows/standings.py:65-71`. **The evidence row's tie-break is claimed to mirror
  `rank.category_ranking`, and nothing tests it.**

  `_evidence` picks, among a model's rows with equal best score, the newest run, then harness, then
  name. That decides which `effort` a standing discloses, which is the D-112 disclosure B1 asked for.
  Reversing the run-date sort (`reverse=True` → ascending) passes all 51 tests in
  `test_board_standings.py`, `test_ios_payload_contract.py` and `test_api_v1.py`, because every
  fixture gives all rows the same date. Today every surface's effort matches (measured above), so
  this is a missing pin, not a live defect. The fix: one fixture with a model whose best score
  appears at two efforts on two dates, and an assertion that the newer run's effort is published.

- **M9** `ios/ModelRanking/Engine/StandingsStore.swift:67`, `ios/EngineTests/StandingsStoreTests.swift:3-4`,
  `:93-103`. **Two leftovers from the S1 and S2 fixes.**

  The red test pinned both halves of S1 (load, then save, then load, against an `https` URL). It
  reached the network, so it was replaced with a `data:` URL test that pins only `load()`. Deleting
  `url.isFileURL` from `save()` survives `StandingsStoreTests` (10 run, 0 failures). No egress follows,
  because `Data.write(to:)` and `createDirectory` refuse a non-file URL. But the guard the security
  finding asked for is only half pinned. The fix: a `save` to the same `data:` URL, then an assertion
  that nothing is created in the folder.

  Separately, the test file's header still says the store holds what the engine sent *"byte for
  byte"*. Since S2 it holds the standings re-encoded (`Models.swift:391-404`).

### PASS (what looks good)

- **The previous B1 is resolved in code, ADR and tests.**
  - `_policies()` maps each surface's `(primary_source, primary_benchmark)` to its `ranking_effort`
    (`standings.py:59-62`), and rows at any other effort are skipped (`:89-91`).
  - `test_a_board_a_surface_ranks_at_one_effort_stands_at_that_effort`
    (`test_board_standings.py:85-95`) pins DeepSWE at `high`: `c_low` at 90 and `a_max` at 70 are
    excluded.
  - `test_each_standing_carries_the_effort_of_its_own_evidence` (`:74-82`) pins the disclosure on a
    board with no policy.
  - D-167 is amended below its body, not edited (`docs/decisions.md:3121-3133`;
    `git diff 0ba004c HEAD` shows lines appended only). It now says clause 2 follows D-112, so no
    supersession is owed.
  - On real data every single-source surface's board equals the surface in membership, order and
    evidence effort.
- **The previous M1 is resolved.**
  - `_standings_problem` builds the payload at boot and reports each `ValueError` with its message
    (`main.py:223-249`).
  - `test_a_payload_the_route_would_refuse_refuses_the_boot_instead` covers the unattributed source
    and the undeclared direction (`test_board_standings.py:263-285`).
  - The two-boards refusal is pinned (`:98-104`), and its mutant is killed.
- **The previous M2 is resolved the way it recommended.** `ContentView.swift` is untouched across
  the range (`git diff --stat` is empty), so `position - 1` stands (`ContentView.swift:787`). It is
  exempted as data with its reason, in the `EGRESS_EXACT` style (`test_ios_client_contract.py:190-195`).
  The exemption must match exactly once, and a stale exemption fails (`:217-221`, `:235`).
- **The previous M4 is resolved.**
  - `testTheBoardsRequestSetsNoHeaderOfItsOwn` (`EngineClientTests.swift:491-503`) checks the
    headers, method and body.
  - `testAnUnreadableResponseIsRefusedRatherThanStored` (`:505-516`) kills the removed `do/catch`.
- **The previous M5 is resolved.** `standings.py` no longer holds an `API_VERSION` or a `noqa`, and the route adds
  the version (`main.py:1409`). `PAYLOAD_KEYS` and `ENVELOPE_KEYS` are frozen separately
  (`test_board_standings.py:21-22`).
- **The security fixes hold.**
  - **S1:** `load()` and `save()` guard `isFileURL` (`StandingsStore.swift:54`, `:67`). The load half
    is pinned offline with a `data:` URL.
  - **S2:** the 4 MiB ceiling is enforced inside `FetchedStandings.init`, and only re-encoded,
    decoded fields are kept (`Models.swift:395-404`). The smuggled-key test kills the raw-bytes
    mutant.
  - **S4:** `POSITION_ARITHMETIC` sees `+=` and `$0 + $1.position`
    (`test_ios_client_contract.py:182-185`, parametrized `:198-209`).
  - **S7:** a duplicate listing counts once (`Combine.swift:64-65`, `CombineTests.swift:115-122`).
- **The invariants of the first round still hold.**
  - No key containing "score" is in the payload (`test_board_standings.py:119-137`).
  - Every key set is frozen (`:140-151`).
  - A query string gives the same bytes (`:227-233`; I also checked this on `advisor.db`).
  - `boards()` takes no argument and sends `query: []` (`EngineClient.swift:200-201`).
  - `FILESYSTEM_FILES` has exactly two entries (`client_decl_gate.py:123-126`).
  - `SCORE_ARITHMETIC_PERMITTED` is unchanged (`test_ios_client_contract.py:171`).
- **The ordering in `Combine.swift` is correct.** It uses competition ranking among the shared
  models, a sum equal in order to the mean, and ties by id (`Combine.swift:60-79`). One board
  reproduces the engine's order, because the engine also breaks ties by id (`standings.py:98`).
- **Red came first, and the review round was honest about it.** `ee312f8` holds only tests plus the
  `ContentView.swift` revert. `abf284b` edited three red tests. Two were for conflicts between red
  tests: S2 contradicted "keeps the bytes the engine sent", and the new `rankingEffort` field was
  added to a test fixture. The third replaced a test that reached the network. Its commit message
  says so.
- **No drive-bys and no swallowed failures.** Every file in the range is in the plan's scope. The
  two `except sqlite3.Error: return None` in `_standings_problem` defer to `_database_unusable`,
  which reports the same artifact, and the docstring says so (`main.py:224-226`). There is no AI
  attribution in any commit.

## Producers of hardened invariant(s)

This wave hardens five invariants:
1. no score on the wire (D-105, D-167 clause 2);
2. nothing question-derived in the request (D-160 clause 1);
3. D-112 effort parity and disclosure on every board;
4. the file system only in named files;
5. position arithmetic in one file.

| producer | invariant | citing test | gap |
|---|---|---|---|
| `standings.board_standings` (`standings.py:74`) | 1, 3 | `test_the_payload_carries_no_score_at_all`, `test_the_key_sets_are_frozen`, `test_a_board_a_surface_ranks_at_one_effort_stands_at_that_effort`, `test_each_standing_carries_the_effort_of_its_own_evidence` | the tie-break that picks the disclosed effort (**M8**) |
| `_standings_problem` / `_egress_problems` (`main.py:223`, `:515`) | the refusals and the bound at boot | `test_an_artifact_that_would_publish_too_many_standings_refuses_to_boot`, `test_a_payload_the_route_would_refuse_refuses_the_boot_instead` | none |
| route `boards()` (`main.py:1392`) | 1, 2 | `test_a_query_string_changes_nothing`, `test_a_missing_artifact_is_unavailable_not_empty`, `test_the_boards_payload_satisfies_every_struct_the_app_decodes` | the post-boot refusal path (**M7**) |
| `EngineClient.boards()` (`EngineClient.swift:200`) | 2 | `testTheBoardsRequestCarriesNothing`, `testTheBoardsRequestSetsNoHeaderOfItsOwn`, `testAnUnreadableResponseIsRefusedRatherThanStored`, `testAnOversizedPayloadIsRefusedBeforeItIsDecoded` | none |
| `FetchedStandings.init` (`Models.swift:395`) | what is stored | `testOnlyTheFieldsTheAppDecodesAreStored`, `testAPayloadOverTheCeilingIsNeverAccepted` | none |
| `StandingsStore.load/save` (`StandingsStore.swift:51`, `:66`) | 4 | `EGRESS_EXACT` (`test_router_hints.py:358-365`), `client_decl_gate.py:123`, `testAStorePointedAnywhereButAFileReadsNothing` | the `save` guard is not pinned (**M9**) |
| `combine` (`Combine.swift:43`) | 5 | `test_position_arithmetic_happens_only_where_an_adr_permits_it`, `test_the_position_tripwire_sees_each_spelling`, `CombineTests` (12) | the tripwire matches names, so an alias passes (**R4**) |

## Acceptance criteria evidence

- **P0**: D-167 → `docs/decisions.md:3082-3120`, committed in `0ba004c` before any test. Its
  amendment is at `:3121-3133`.
- **P1**:
  - route declared and additive → `tests/unit/test_api_v1.py:541`
  - shape frozen → `tests/unit/test_board_standings.py:21-26`, `:140-151` (in that file rather than
    `test_api_v1.py`)
  - rankable only (REQ-EVI-002) → `:107-116`
  - attributed and dated → `:154-166`
  - unattributed refused → `:169-173`
  - ties share a position → `:67-71`
  - no score → `:119-137`
  - query string ignored → `:227-233`
  - boot bound → `:245-260`
  - refusals at boot → `:263-285`
  - effort per D-112 → `:74-95`
  - Codable keys → `tests/unit/test_ios_payload_contract.py:264-283`
- **P2**:
  - request carries nothing → `ios/EngineTests/EngineClientTests.swift:470-478`
  - no header of its own → `:491-503`
  - undecodable refused → `:505-516`
  - oversized refused → `:518-528`, and in the type → `StandingsStoreTests.swift:119-122`
  - day cadence → `StandingsStoreTests.swift:51-63`
  - future stamp → `:65-74`
  - last good kept → `:76-84`
  - file-system gate → `scripts/client_decl_gate.py:123-126`, run PASS
  - D-126 text gate → `tests/unit/test_router_hints.py:358-365`, passing
- **P3**:
  - missing model absent → `ios/EngineTests/CombineTests.swift:30-36`
  - order from positions → `:38-46`
  - ties by id → `:48-57`, `:59-67`
  - one board equals its order → `:69-73`
  - unknown board refused → `:95-101`
  - result names its boards → `:84-93`
  - permitted by D-160 → `tests/unit/test_ios_client_contract.py:177`, `:211-235`, `:289`
- **P4**:
  - payload measured → `docs/research/m17-w4-standings-payload-2026-09-25.md:22-34` (stale, **M6**)
  - combination by hand → `:36-70` (no DeepSWE board in its examples, so unaffected by B1)
  - security pass → `docs/reviews/m17-wave-4-security.md`, PASS-WITH-MINORS

## K.8 contract drift check

`grep -n` at `abf284b`:
```
src/app/adapter/main.py:109:DECLARED_ROUTES: frozenset[str] = frozenset(
src/app/adapter/main.py:1300:@app.get(f"/{API_VERSION}/categories")
src/app/adapter/main.py:1355:@app.get(f"/{API_VERSION}/budgets")
src/app/adapter/main.py:1392:@app.get(f"/{API_VERSION}/boards")
src/app/adapter/main.py:1421:@app.get(f"/{API_VERSION}/recommendations")
src/app/workflows/rank.py:109:def attributions_for(evidence_sources: Iterable[str], *, priced: bool) -> tuple[str, ...]:
src/app/workflows/rank.py:176:def build_price_medians(conn: sqlite3.Connection) -> int:
src/app/workflows/rank.py:250:def ranked_population(conn: sqlite3.Connection, spec: CategorySpec) -> list[RankingRow]:
src/app/workflows/boards.py:28:def declared() -> list[Board]:
src/app/workflows/access.py:101:def served(conn: sqlite3.Connection) -> dict[str, str]:
ios/ModelRanking/Engine/EngineClient.swift:200:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/EngineClient.swift:212:    private func get<T: Decodable>(_ path: String, query: [URLQueryItem]) async throws -> T {
ios/ModelRanking/Engine/EngineClient.swift:222:    private func fetch(_ path: String, query: [URLQueryItem]) async throws -> Data {
tests/unit/test_ios_client_contract.py:171:SCORE_ARITHMETIC_PERMITTED = {"Uncertainty.swift": "D-138"}
tests/unit/test_ios_client_contract.py:177:POSITION_ARITHMETIC_PERMITTED = {"Combine.swift": "D-160, D-167"}
tests/unit/test_ios_client_contract.py:190:POSITION_ARITHMETIC_EXACT = {
scripts/client_decl_gate.py:107:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:123:FILESYSTEM_FILES = {
tests/unit/test_api_v1.py:541:    expected = {"/health", "/v1/categories", "/v1/recommendations", "/v1/budgets", "/v1/boards"}
```
- These are unchanged apart from line shifts: the existing routes, `attributions_for`,
  `build_price_medians`, `ranked_population`, `declared`, `served` and `SCORE_ARITHMETIC_PERMITTED`.
- `get<T>` keeps its signature.
- `FILESYSTEM_FILE` → `FILESYSTEM_FILES` as the plan intends. Outside `FILESYSTEM_FILES`, a grep finds
  the old name only in the plan's own grep paste (`m17-wave-4-plan.md:45`, dated 7d7a9ac).
- `/v1` gains one route and changes none.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py`: **the declaration gate has no committed negative fixture.**
  Only `Makefile` references it. Nothing would notice an edit that made it pass everything. It is
  carried from the superseded verdict, because the finding still stands at `abf284b`. Enhancement.
- **K2** `ios/EngineTests` (see `abf284b`'s message and `git diff ee312f8 abf284b --
  ios/EngineTests/StandingsStoreTests.swift`): **no gate keeps a Swift test off the network.** The red
  commit `ee312f8` shipped a test that read `https://example.com/standings.json`. Anyone who checks
  it out and runs `swift test` reaches the internet, and the test passed whatever the code did. The
  D-126 text gates scan the app, not the tests. The fix: a test-tree scan for `https?://` URLs handed
  to `Data(contentsOf:)`, `String(contentsOf:)` or a store's `init(url:)`. Process bug.
- **K3** `ios/ModelRanking/Engine/FrontDoor.swift:286`, `scripts/client_decl_gate.py:95-97`,
  `tests/unit/test_router_hints.py`: **the older half of security S1, which that review said to
  file, is not fixed by this wave.** `GapRegisterStore.init(url:)` has no `isFileURL` guard. Both
  D-126 gates also miss a `URL` built through `Decodable` (`[URL].self`), which is the probe the
  security pass ran.
- **K4** Worktree process: **two review seats mutating one worktree at once read each other's
  mutants.** The previous round saw this. This round had one seat, so it did not recur. It is
  carried so the finding is not lost with the superseded file. Process bug.

## Risks queued to next M

- **R1** **Two boards are one benchmark.** `swebench` and `epoch_swe_bench_verified` are both
  "SWE-bench Verified". It is real if W5 can choose both for one question, because the benchmark
  would count twice in the sum. Carried from the superseded verdict.
- **R2** **The all-present rule empties lists.** DeepSWE now ranks 18, not 25, so any list that
  includes it holds at most 18 models. The research record's third example keeps 3. It is real if W5's
  intents routinely pick a small board beside a disjoint one.
- **R3** **The route is rebuilt on every request, uncompressed.** It serves 499 KB raw (36 KB gzip) in about 60 ms,
  unauthenticated, bounded at 25,000 positions. It is real once phones fetch daily and egress or
  latency shows up (see also security S5).
- **R4** **The position tripwire matches names.** `let p = s.position; return p + 1` planted in
  `Engine/Detail.swift` passes `test_position_arithmetic_happens_only_where_an_adr_permits_it`. The
  score tripwire has the same limit. It is real if W5 adds a screen file that computes on an aliased
  position. The ADR permits no such file.
- **R5** `standings.py:59-62`: **the effort policy follows a surface's PRIMARY SOURCE, while the surface
  ranks the benchmark across every source.** A second source publishing DeepSWE would stand on best
  evidence while the surface ranks it at `high`. Two surfaces naming one primary board at different
  efforts would silently overwrite each other in the dict. Today one source holds DeepSWE, as
  measured. It is real the day a second source ingests an effort-policy benchmark.
