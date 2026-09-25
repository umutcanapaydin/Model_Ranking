---
record_type: review
id: m17-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# M17-W4 Code Review: board standings to the phone, and the combination on it

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `7d7a9ac..939aeb5` (9 commits, 20 files, +1349 / -36)
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)

**What I read first.** `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md`, neither
touched by the range. Then the wave plan, `docs/plans/m17-plan.md` §W4, D-105 (`docs/decisions.md:322`),
D-112 (`:486`), D-160 (`:2771`) and the new D-167 (`:3082`). I read the code before the commit
messages.

**How I worked.**
- **Tests run.** The wave's Python files and the gates they touch: 74 passed
  (`test_board_standings.py`, `test_api_v1.py`, `test_ios_payload_contract.py`,
  `test_ios_client_contract.py`, `test_router_hints.py`). `scripts/client_decl_gate.py`: PASS, 13
  client files in 4 configurations. `cd ios && swift test`: 289 tests, 0 failures. `make check-fast`
  was also run; its result is at the end of this file.
- **Mutants.** Each was run in place, restored by copy, and checked with sha256 against the
  pre-mutation hash (`standings.py` 424522e8…, `Combine.swift` 3935d5d3…, `Models.swift` 91430484…,
  `ContentView.swift` 45dca9cc… = HEAD). `PYTHONDONTWRITEBYTECODE=1` throughout.
  - Killed: the attribution check dropped (`test_an_unattributed_source_fails_rather_than_publishing`);
    `FileManager` added to `Combine.swift` (both `client_decl_gate.py` and `test_router_hints.py`
    refuse it); `ContentView.swift` renamed back to `position - 1` (the position tripwire fires at
    `ContentView.swift:790`); `Combine.swift:66` `<` changed to `<=`
    (`testATieTakesTheHigherRankAndTheNextModelSkipsPastIt`).
  - Survived: the "one source holds one board" refusal deleted (`standings.py:77-79`); the board
    dates computed over unpriced rows (`standings.py:54`); `JOIN models` dropped from `_BEST`
    (`standings.py:37`); an aliased position (`let p = s.position; return p + 1` in `Models.swift`).
- **Measurements** on the worktree's `advisor.db`, read only: 63 boards, 303 models, 6,962
  positions, 346,112 bytes raw, 31,769 gzip, ~30 ms per `board_standings` call. I compared each
  surface's primary board on `/v1/boards` with `ranked_population` for that surface.
- **Network.** None. I did not call `build()` and did not set `RUN_CONTRACT_TESTS`.
- **Concurrent writer.** During the review another process modified `ios/ModelRanking/ContentView.swift`
  in this worktree. It added an uncommitted block after `gaps.record(typed)` that decodes a `URL` built
  from `typed` and loads a `GapRegisterStore` from it. The block looks like a gate probe, and I did not
  write it. It was gone, and the file was byte-identical to HEAD, before I wrote this verdict. My
  `swift test` run may have overlapped it; it passed. See **K2**.

## Verdict
BLOCKING

One finding blocks: **B1**. D-167 ranks every board on each model's best row across effort levels.
That silently departs from D-112, which the owner signed. On the one board with an effort policy, the
DeepSWE board, the order and the population differ from the product's own `agentic-coding` surface.
And the payload drops the effort a position was earned at, which D-112 requires to be disclosed.
Nothing else blocks. The payload carries no score and nothing derived from the question. The route
is additive, the boot bound is correct, each gate widened for one named file only, and red came first.

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `src/app/workflows/standings.py:34-40`, `docs/decisions.md:3100-3101` (D-167 clause 2),
  `docs/plans/m17-wave-4-plan.md:64-65`, against `docs/decisions.md:486-496` (D-112) and
  `src/app/workflows/categories.py:112-125`. **"Best row on the board" takes the maximum across effort
  levels. That reverses a ratified owner ruling for one board, and drops a disclosure the ruling
  requires for all of them. No ADR supersedes or amends D-112.**
  - The facts:
    - `_BEST` is `MAX(s.score) … GROUP BY s.source, s.benchmark, s.metric, s.model_id`, with no
      effort term.
    - D-112 (owner-signed at M5): *"Q1's single-effort rule binds a category that HAS an effort
      policy"*. For a category without one, *"the answer carries `effort_mix_notice` whenever the
      compared picks come from different effort levels. Each pick also publishes the effort of its
      OWN evidence."*
    - `agentic-coding` has that policy (`ranking_effort="high"`, `categories.py:124`), and its
      primary board is `epoch_deepswe_external`.
  - Measured on `advisor.db`:
    - **DeepSWE board on `/v1/boards`:** 25 models, #1 GPT-6 Astra, #2 Gemini 3.8 Flash.
    - **`agentic-coding` surface (`ranked_population`):** 18 models, #1 Gemini 3.8 Flash, #2 GPT-6
      Astra.
    - The same app would therefore show two different orders for the same board: one on the
      `agentic-coding` surface, and one in a W5 combination.
    - Seven models stand on the board only because of their `max`, `xhigh`, `medium` or `low` rows.
      The surface excludes them by ruling.
  - The other 12 surfaces' primary boards match `ranked_population` in membership and in order
    (positions never decrease along the surface's order). `coding` differs by design: its surface
    ranks "SWE-bench Verified" across two sources, and each source is its own board.
  - **The disclosure half is wider:**
    - 546 (board, model) pairs on 51 of the 63 boards hold more than one effort level.
    - The payload carries no effort (`STANDING_KEYS = {"model", "position"}`,
      `tests/unit/test_board_standings.py:23`, frozen). So W5 cannot say that a combined list
      compares models at unequal effort, which D-112 requires of every answer.
    - The test fixture pins the cross-effort behaviour on purpose: `a` at `max` 70 against others at
      `unspecified`, in `test_board_standings.py:46-52` and `:65-70`.
  - **The plan's parity claim is false in code.** Plan `:64-65` says the position uses *"the same
    'best score per model' `ranked_population` uses"*. For `agentic-coding`, `ranked_population`
    filters `effort = 'high'` (`rank.py:281`, `:329`). `_BEST` does not.
  - **Why this blocks.** A decision reversed without `superseded by`/`amends` is BLOCKING under this
    profile (seed B.2). D-167 neither cites D-112 nor states that it departs from it.
  - **Two ways out, each small:**
    - **(a)** Honour D-112. Use the category's `ranking_effort` when a board is a surface's primary
      source with a policy (today only `epoch_deepswe_external` at `high`). Add each standing's
      `effort`, an additive key decided in D-167, so W5 can disclose a mix. Pin both in
      `test_board_standings.py`.
    - **(b)** Ask the owner to rule that boards are exempt from D-112 in both respects. Record that
      ruling in D-167 as an explicit amendment of D-112, with the DeepSWE divergence measured above.
      Either way the plan's `:64-65` sentence must become true.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/standings.py:66-79`, `src/app/adapter/main.py:501-535`, `:1401-1405`.
  **The payload's three refusals (an undeclared metric direction, an unattributed source, a source
  holding two boards) fire only at request time.**
  - A build that adds a lower-is-better metric boots green, `/health` says healthy, and every
    `/v1/boards` request is a generic 500 (`main.py:706-718`).
  - The wave already opens the artifact at boot for the row count (`_standings_row_count`). Calling
    `board_standings` there and reporting the `ValueError` as a boot problem is a few lines. It fails
    at deploy, which is the reason `_egress_problems` exists (`main.py:590-600`).
  - Separately, the two-boards refusal (`standings.py:77-79`) has no test. Deleting it survives the
    suite (mutant above).
- **M2** `ios/ModelRanking/ContentView.swift:785-787`,
  `tests/unit/test_ios_client_contract.py:178-198`. **The rename `position` → `place` answers a
  name-based tripwire by changing the name.**
  - The value is a locally computed index (`rankOf`, `Engine/Router.swift:723-725`), not a served
    position, so no rule is broken. But the fix avoids the gate rather than going through it, and it
    touches a screen file in a wave whose plan says *"No screen changes"* (`m17-wave-4-plan.md:21`).
    The plan does not list the edit.
  - The mutant shows the gate's limit: `let p = s.position; return p + 1` in `Models.swift` passes.
  - Two options:
    - Record the exemption as data with its reason, the way `SORTING_PERMITTED` does, and revert the
      rename.
    - Keep the rename, and state the tripwire's name-based limit in the test's docstring, and name
      the edit in the plan.
- **M3** `src/app/adapter/main.py:217-219`,
  `docs/research/m17-w4-standings-payload-2026-09-25.md:30-32`, `docs/decisions.md:3115-3116`,
  `docs/plans/m17-wave-4-plan.md:23-24`. **The size facts disagree with the measurement and with
  each other.**
  - `main.py` says *"About 8,500 … about 250 KB; … near three times that"*. The measurement is 6,962
    positions and 346 KB, so 25,000 is 3.6×.
  - The research record says both bounds are *"about ten times over"*. The engine's is 3.6×; only
    the phone's 4 MiB is about 12×.
  - D-167 and the plan say *"about 250 KB (about 60 KB compressed), measured on the served
    artifact"*. The record measured 325-346 KB raw and 30-32 KB gzip.
  - Fix the comment and the record. For D-167, add an addendum rather than an edit
    (supersede-never-edit).
- **M4** `ios/EngineTests/EngineClientTests.swift:469-477`, against plan `:110`, `:112`. **Two plan
  items have no citing test.**
  - *"no header derived from the question"*: the test asserts only path and query.
  - *"an … undecodable response is refused"*: nothing drives a malformed body through `boards()`.
    Removing the `do/catch` at `EngineClient.swift:207-211` would surface a raw `DecodingError`
    instead of `EngineError.undecodable`, and no test would notice.
  - `boards()` takes no argument, so a header derived from the question is structurally unlikely.
    The plan still named a test for it.
- **M5** `src/app/workflows/standings.py:26`, `:45`. **Small hygiene.**
  - `API_VERSION = "v1"` is a second copy of `main.py:75`: one fact in two places.
  - `# noqa: S608` silences a finding on an f-string that only splices a module constant (seed H.1).
    Building `standings_row_count`'s query as a constant string removes the need for it.
  - The plan's *"a ceiling on the number of boards"* (`m17-wave-4-plan.md:67-68`) is not built.
    Boards are at most positions, so this is covered implicitly. Say so in the plan, or drop the
    clause.

### PASS (what looks good)

- **No score leaves the engine.**
  - `board_standings` selects `MAX(score)` only to order rows, and emits `{"model", "position"}`
    (`standings.py:85`).
  - Model rows carry id, display, vendor, blend and accessibility (`:89-97`).
  - `test_the_payload_carries_no_score_at_all` walks every key, and every key set is frozen
    (`test_board_standings.py:85-117`).
- **Nothing question-derived is sent.**
  - The route takes no parameters, and `test_a_query_string_changes_nothing` compares bytes
    (`:191-197`).
  - `EngineClient.boards()` takes no arguments and sends `query: []` (`EngineClient.swift:200-201`).
  - `testTheBoardsRequestCarriesNothing` pins the path and the absence of a query.
- **Tie semantics match D-167.**
  - The engine uses competition ranking over the best row, with ties ordered by `model_id`
    (`standings.py:61`, `:82-84`).
  - `Combine.swift` re-ranks the common models on each board by "1 + models strictly above", sums
    the ranks (the same order as the mean, since counts are equal), and breaks ties by id
    (`Combine.swift:62-77`). One board chosen reproduces the engine's own order, ties included,
    because both break ties by id.
  - Across harnesses (swebench: 36 harnesses, one effort) the best-row rule is the same one the
    `coding` surface uses.
- **The boot bound is sound.** `standings_row_count` and the payload share one query (`_BEST`), so
  the bound counts exactly what is published. The refactor into `_egress_problems` keeps the two
  existing messages word for word (`main.py:501-535`). The test proves the refusal and the recovery
  (`test_board_standings.py:209-224`).
- **The gates widened by exactly one file each.**
  - `FILESYSTEM_FILES` has two entries (`client_decl_gate.py:123-126`).
  - The seven `EGRESS_EXACT` entries are whole expressions, each required to occur exactly once
    (`test_router_hints.py:358-365`, `:398-405`). What stays in `StandingsStore.swift` after they are
    removed matches no pattern.
  - `POSITION_ARITHMETIC_PERMITTED` and the `SORTING_PERMITTED` entry name only `Combine.swift`, and
    the stale-permission check keeps them honest.
  - Planting `FileManager` in `Combine.swift` is refused by both file-system gates.
- **Red came first, three times.**
  - The implementation files were absent at each red commit: `b62f451` (no `standings.py`), `60cf310`
    (no `StandingsStore.swift` or `boards()`), `a1b0c87` (no `Combine.swift`).
  - The green commits edited their red tests only to fix raw-string continuations, to widen the
    tripwire so it sees a subscript, and to add two tests found by mutation. Each commit message says
    so.
- **`/v1` stays additive.** Only the route set gains `/v1/boards` (`test_api_v1.py:539-541`). No
  existing key, route or message changed. The additions are the payload contract test against the
  four new Codable structs (`test_ios_payload_contract.py:264-283`), and the store's behaviour
  (freshness, a clock that stepped back, the last good payload, an unreadable file), which is covered
  and killed by the author's six mutants and re-checked here.

## Producers of hardened invariant(s)

These are the invariants the wave hardens: no score on the wire, nothing question-derived in the
request, the file system in named files only, and position arithmetic in one file.

| producer | citing test | gap |
|---|---|---|
| `standings.board_standings` (`standings.py:58`) | `test_the_payload_carries_no_score_at_all`, `test_the_key_sets_are_frozen` | effort not carried (**B1**) |
| route `boards()` (`main.py:1385`) | `test_a_query_string_changes_nothing`, `test_a_missing_artifact_is_unavailable_not_empty` | refusals only at request time (**M1**) |
| `EngineClient.boards()` (`EngineClient.swift:200`) | `testTheBoardsRequestCarriesNothing`, `testAnOversizedPayloadIsRefusedBeforeItIsDecoded` | headers, undecodable body (**M4**) |
| `StandingsStore.save/load` (`StandingsStore.swift:51-71`) | `EGRESS_EXACT` (`test_router_hints.py:358-365`), `client_decl_gate.py:123`, `StandingsStoreTests` | none |
| `combine` (`Combine.swift:43`) | `test_position_arithmetic_happens_only_where_an_adr_permits_it`, `CombineTests` (11) | name-based tripwire (**M2**) |

## Acceptance criteria evidence

- **P0** D-167 → `docs/decisions.md:3082-3120`, committed (`0ba004c`) before any test or code.
- **P1**
  - route declared and additive → `tests/unit/test_api_v1.py:539-541`
  - shape frozen → `tests/unit/test_board_standings.py:106-117`, in that file rather than in
    `test_api_v1.py` as the plan says
  - rankable only (REQ-EVI-002) → `:73-82`
  - attributed and dated → `:120-139`
  - ties share a position → `:65-70`
  - no score → `:85-103`
  - query string ignored → `:191-197`
  - boot bound → `:209-224`
  - Codable keys → `tests/unit/test_ios_payload_contract.py:264-283`
  - direction refused → `test_board_standings.py:142-148`
- **P2**
  - request carries nothing → `ios/EngineTests/EngineClientTests.swift:469-477`
  - day cadence → `ios/EngineTests/StandingsStoreTests.swift:51-63`
  - future stamp → `:65-74`
  - last good kept → `:76-84`
  - oversized refused → `EngineClientTests.swift:488-499`
  - undecodable refused → **no test (M4)**
  - file-system gate → `scripts/client_decl_gate.py:123-126`, run PASS
  - D-126 text gate → `tests/unit/test_router_hints.py:358-365`, passing
- **P3**
  - missing model absent → `ios/EngineTests/CombineTests.swift:30-36`
  - order from positions → `:38-46`
  - ties by id → `:48-57`, `:59-67`
  - one board equals its order → `:69-73`
  - unknown board refused → `:95-101`
  - result names its boards → `:84-93`
  - permitted by D-160 → `tests/unit/test_ios_client_contract.py:172-198`, `:252-256`
- **P4** payload measured → `docs/research/m17-w4-standings-payload-2026-09-25.md:22-34` (figures
  corrected under **M3**); combination by hand → `:36-70`; security pass: not in this range,
  pending before merge as the plan says (`:14`).

## K.8 contract drift check

`grep -n` at 939aeb5:
```
src/app/adapter/main.py:109:DECLARED_ROUTES: frozenset[str] = frozenset(
src/app/adapter/main.py:1293:@app.get(f"/{API_VERSION}/categories")
src/app/adapter/main.py:1348:@app.get(f"/{API_VERSION}/budgets")
src/app/adapter/main.py:1385:@app.get(f"/{API_VERSION}/boards")
src/app/adapter/main.py:1409:@app.get(f"/{API_VERSION}/recommendations")
src/app/workflows/rank.py:109:def attributions_for(evidence_sources: Iterable[str], *, priced: bool) -> tuple[str, ...]:
src/app/workflows/rank.py:176:def build_price_medians(conn: sqlite3.Connection) -> int:
src/app/workflows/boards.py:28:def declared() -> list[Board]:
src/app/workflows/access.py:101:def served(conn: sqlite3.Connection) -> dict[str, str]:
ios/ModelRanking/Engine/EngineClient.swift:214:    private func get<T: Decodable>(_ path: String, query: [URLQueryItem]) async throws -> T {
ios/ModelRanking/Engine/EngineClient.swift:224:    private func fetch(_ path: String, query: [URLQueryItem]) async throws -> Data {
tests/unit/test_ios_client_contract.py:169:SCORE_ARITHMETIC_PERMITTED = {"Uncertainty.swift": "D-138"}
tests/unit/test_ios_client_contract.py:175:POSITION_ARITHMETIC_PERMITTED = {"Combine.swift": "D-160, D-167"}
scripts/client_decl_gate.py:107:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:123:FILESYSTEM_FILES = {
tests/unit/test_api_v1.py:541:    expected = {"/health", "/v1/categories", "/v1/recommendations", "/v1/budgets", "/v1/boards"}
```
- The existing routes, `attributions_for`, `build_price_medians`, `declared`, `served` and
  `SCORE_ARITHMETIC_PERMITTED` are unchanged apart from line shifts.
- `get<T>` keeps its signature. Its transport half moved to `fetch`, with the same error
  vocabulary.
- `FILESYSTEM_FILE` became `FILESYSTEM_FILES`, as the plan intends (`:73-75`). No other file referenced
  it (`grep -rn FILESYSTEM_FILE scripts tests docs Makefile`).

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py` (no self-test). **The declaration gate has no committed
  negative fixture.** I proved by hand that it refuses `FileManager` in `Combine.swift`. Nothing in
  `make check` would notice if a later edit made it pass everything, whereas `check-records` has
  `check-records-selftest`. Enhancement.
- **K2** Worktree process (see "Concurrent writer" above). **Two review seats mutating one worktree
  at the same time can read each other's mutants.** An injected egress block in `ContentView.swift`
  was live while this seat ran tests and restored a file. Each seat should run in its own worktree,
  or the seats should run one after another. Process bug.

## Risks queued to next M

- **R1** **Two boards are the same benchmark.** `swebench` and `epoch_swe_bench_verified` are both
  "SWE-bench Verified" (measured). If W5 chooses both, one benchmark counts twice in the sum. It is
  real if W5's board choice can emit both ids for one question.
- **R2** **The all-present rule empties lists.** The research record's own third example keeps 3
  models (`m17-w4-standings-payload-2026-09-25.md:64-70`). It is real if W5's intents routinely
  select a small board with a disjoint one.
- **R3** **The route is recomputed on every request, uncached and unauthenticated.** About 30 ms on
  today's 6,962 positions, and bounded at 25,000. The engine also serves it uncompressed: 346 KB, 32
  KB gzip. It is real if request latency or egress shows up once phones fetch daily.

## `make check-fast`

Run at 939aeb5 with only this file uncommitted: **PASS** in 63.3 s, six legs.
- lint PASS
- typecheck PASS
- records PASS (`check-records`, selftest, `install-check`, `harvest-context-check`, `shell-dialect`,
  `wave-check-all`, `conformance`)
- test PASS
- client-decls PASS
- swift-test PASS
