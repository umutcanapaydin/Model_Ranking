---
record_type: review
id: m18-wave-7-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W7 Code Review: the issue backlog

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `e023296..58e8bf4` (W7's own commits `976f559`, `593718c`, `f8ca4d9`, `7b2b668`; 31
files, +574 / -58). `e023296` is the closed M18-W6 head. `58e8bf4` merges W6's last commits under W7;
its only hand resolution is one blank line in `docs/plans/m18-plan.md`.
**Risk tier:** HIGH (`docs/plans/m18-wave-7-plan.md:14`). #104 touches `scripts/engine_service.sh`, a
security glob. By D-172 no security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the base profile
(`.claude/agents/Code-Reviewer.md`, unchanged in the range), the wave plan, the milestone plan's W7
amendment and the 13 issues. Then I read the diff. I read the commit messages last.

**Summary.** The wave closes all 13 issues it planned, and every gate is green in this seat. Each
fix holds against its own mutant, with one exception (M3). The code changes are small and careful.
The weak spots are in the new gates: three of them check less than their docstrings, the
security-invariants list or the plan say. Nothing blocks. Seven MINORs:

1. **M1.** The network guard holds only inside the test process. A child process, `gethostbyname`,
   UDP and import-time code all pass it. Yet INV-6 is now marked fully held and G-5 closed.
2. **M2.** The PRD gate reads only the `| REQ-` table rows. It skips 105 of 421 line pointers, the
   `**Status:**` lines, including `test_rank.py:103`, which #105 itself names. `Makefile:108` is stale.
3. **M3.** #102's budget half, and the "same model, no trade-off" half, are held by no test. Two
   mutants pass all 1743 tests.
4. **M4.** #112's tests read constants and a frozen id list, not the served names, as the plan's
   acceptance check says. No rule applies Claude's word order where `models.display` is filled.
5. **M5.** #114's reload gate matches three spellings. `importlib.reload(engine)` passes it, and the
   five `ConfigError` failures come back.
6. **M6.** #104's hint now runs, but it builds `advisor.db` in the release folder. The service reads
   `$DEPLOY/data/advisor.db`, so the launcher still says "missing".
7. **M7.** #118's new label is read by `probe.swift`, which has no `NOT_A_SEARCH` case. It scores
   the three relabelled rows as misses whatever the router does.

## Verdict

MINOR

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `tests/conftest.py:51-79`; `docs/security-invariants.md:149`, `:179`. **The network guard
  is narrower than INV-6 and the G-5 closure say.**
  The guard patches `socket.socket.connect`, `connect_ex` and `socket.getaddrinfo`, inside a
  function-scoped fixture. I probed it from a scratch test (removed after):
  - A child process is not guarded. In a child started by a test, `socket.getaddrinfo.__qualname__`
    is `getaddrinfo` and `socket.socket.connect` is `socket.connect`, the real ones. Many tests start
    Python children (`test_cli_e2e.py`, `test_engine_service.py`, `test_nightly_refresh.py`, the new
    `--help` test).
  - `socket.gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, `getnameinfo` and
    `socket.socket.sendto` are the unpatched originals. Each is a name lookup or a packet that
    leaves the machine.
  - Module- and session-scoped fixtures, and code that runs at import, run before the fixture.
  - `RUN_CONTRACT_TESTS=1` lifts the guard for every test in the process, not only the contract
    tests. #122's triage asked for an opt-out "by marker". CI's contract job runs all of
    `tests/integration` that way (`.github/workflows/contract-tests.yml`).

  Why minor: no test reaches the network today, and the guard is a real gain. But INV-6's row now
  lists the new tests with no "Partial", and G-5 is closed, so the next seat will read the Python
  half as whole. Fix: keep G-5 open as a partial that names these paths, or close them (a
  `sitecustomize` on the children's `PYTHONPATH`, the other resolvers patched, the guard installed
  in `pytest_configure`, and an opt-out by marker).

- **M2** `tests/unit/test_prd_citations.py:48`; `docs/prd.md:71`, `:113`, `:272`, `:467`.
  **The PRD gate reads only table rows, so a quarter of the PRD's pointers are still unchecked.**
  `problems()` skips every line that does not start with `| REQ-`. The M1 to M5 requirements carry
  their evidence on `**Status:**` lines instead: 30 lines, 105 of the PRD's 421 line pointers.
  I ran the gate's own check over those lines. Three land on an assertion, not on a declaration:
  `test_arena_slices.py:539`, `test_epoch_bundle_fetch.py:78` and `test_rank.py:103`. Each is inside
  the right test today, but the gate would not see it move. #105 names `test_rank.py:103` as its
  first example. Separately, the gate checks `.py` and `.swift` pointers only. `Makefile:108` (cited
  at `:272` and `:467`, "a leg of `make check`") is `format:`; `check:` is at `Makefile:115`.
  The plan's acceptance check says "Every PRD `file:line` lands on a test declaration, and the stale
  ones are corrected" (`docs/plans/m18-wave-7-plan.md:43`). Fix: read every line that cites, allow a
  pointer into a test's body where the PRD says so ("asserted at"), and correct `Makefile:108`, or
  say in the gate what it leaves out.
  The 30 table pointers that did move are right. I read each against its row (PASS below).

- **M3** `src/app/workflows/recommend.py:532-533`; `tests/unit/test_recommend.py:638-652`.
  **Half of #102 is held by no test.** The new test checks the value pick only. I ran two mutants
  against the whole suite (`pytest -n auto`, 1743 tests):
  - `cheap_is_quality = cheap.model == quality.model` (the old rule, budget pick only): all pass.
  - `value_is_quality = False` and `cheap_is_quality = False` (what any step that copies a row would
    cause, since the rule is now identity): all pass. So no test says that a pick which IS the leader
    carries no trade-off.

  Identity is sound today. I traced every path: `eligible_rows`, `pareto_frontier` and
  `first_cheapest` hand on the same `RankingRow` objects, and `ranked_with_ids` gives one row per
  model id (`px_median.model_id` is the primary key). But identity is more fragile than the id
  comparison #102 asked for, and nothing holds it. Fix: extend the test to the budget pick, and add
  the positive case (a value or budget pick that is the leader has no `trade_off`).

- **M4** `tests/unit/test_display_names.py:17-27`, `:44-48`; `src/app/workflows/registry.py:557-558`;
  `docs/plans/m18-wave-7-plan.md:42`. **#112's tests do not read the served names, as the plan's
  check says.** The plan: "each held by a test over the served artifact's names". The tests read
  `MODEL_RULES`, `DISPLAY_NAMES` and a frozen set of 34 ids from 2026-10-04. So:
  - a new model the next refresh serves under its raw id passes;
  - a derived Claude name a board spells in the old order ("Claude 5.5 Opus") is served as is, and
    passes. #112's triage asked for "one rule for Claude's word order, applied where
    `models.display` is filled"; the wave changed constants instead.

  No served name is wrong today. I applied the new names to the served artifact's 315 models:
  no raw id is left beyond the six OpenAI ids, no Claude name is in the old order, no two models
  share a name, and every name passes `_DISPLAY`. Fix: one test over `advisor.db` (W-108 already
  reads it) that maps each served id through the rules and the table, or amend the plan's wording.

- **M5** `tests/unit/test_api_config.py:731-741`. **The reload gate matches three spellings.** Its
  regex is `\breload\(\s*(?:app\b|main_mod|adapter)`. I planted
  `import app.adapter.main as engine` and `main_mod = importlib.reload(engine)` in
  `test_empty_answer_reasons._answers`. The gate passed. Running that file before
  `test_api_config.py` then gave "5 failed, 27 passed", #114's exact failure. The fix itself is
  right: without the reload the two files pass in either order (32 passed, checked). Fix: run the two
  files in the failing order in a subprocess, as #114 suggested, or match any `reload(` and
  `sys.modules` deletion under `tests/`.

- **M6** `scripts/engine_service.sh:46-49`; `scripts/install_engine_service.sh:72`. **The hint
  builds the wrong file for the service.** The launcher checks `$DB`
  (`${MODEL_RANKING_DB:-advisor.db}`). The installed service sets
  `MODEL_RANKING_DB="$DEPLOY/data/advisor.db"`. The hint prints `--db advisor.db`, which the launcher
  runs from the release folder (`cd "$REPO"`). An operator who follows it builds a file the service
  never reads, and the next start says "missing" again. #104 asked for "a command that works". The
  command now runs (its `--help` exits 0), and `refresh` does publish a first artifact
  (`refresh.py:598-601`). Fix: print `--db "$DB"`. The new test checks flags only, so a test of the
  value would hold it.

- **M7** `scripts/router_probe/probe.swift:63-67`; `scripts/router_probe/offtopic_questions.json:33`.
  **The relabel meets #118's words, but its one reader scores it as a miss.** The off-topic sets are
  `[[question, label]]`. `probe.swift` is the only scorer that reads that shape. It knows `DECLINE`,
  `a|b~` and a bare surface id, and nothing else, so `NOT_A_SEARCH` is compared with a surface id
  and is always a MISS. `ReadingProbe.swift` reads questions only, and `score_reading.py` reads only
  `{q, expected}` sets. So the wording-tier probe on these sets now counts three rows wrong whatever
  the router does: the problem #118 describes, moved to another reader. Fix: teach `probe.swift`
  to skip or count `NOT_A_SEARCH` rows separately (the wording tier does not read "not a search";
  the app's reading does), or say so in its header.

### PASS (what looks good)

- **#102.** The rule is the row, not the display name (`recommend.py:532-533`). Identity is sound in
  every path today (M3 has the trace). The red test renames the value model to the leader's name and
  sees the trade-off kept (`test_recommend.py:638`); the old rule fails it (mutant killed).
- **#103.** `run.reports` gets the same discount as `report.sources` (`build.py:781`). `replace()`
  makes new objects, so the two lists share nothing. Nothing reads `run.reports` today (`git grep`).
  The test fails without the line (mutant killed).
- **#104.** `refresh` takes `--fetch-epoch` and publishes when no live artifact exists. The new test
  reads argparse's declared options, not the help's prose (mutant killed). Its children only print
  help.
- **#112.** The names are right. Anthropic's order is "Claude 3.5 Sonnet" up to 3.7 and "Claude
  Opus 4.5" from 4 on; the dated snapshots carry their real dates (2024-02-29, 2024-03-07,
  2024-06-20, 2024-10-22; o1 2024-12-17; o3 2025-04-16). No table key is owned by a curated rule, and
  every key is in the served artifact. The table cannot weaken D-157: each name passes `_DISPLAY`
  (`test_display_names.py:63`), and the table is code, not upstream text. A rename never refuses a
  refresh: `display_changes` only records it (`refresh.py:303-310`). One nit: the comment says
  "its maker's own spelling", but the table writes Xiaomi's "MiMo-V2-Flash" and Alibaba's
  "Qwen2.5-72B-Instruct" with spaces. That is the house style, not the maker's.
- **#114.** The reload is gone, and the app reads `MODEL_RANKING_DB` per request (`main.py:250-258`),
  so the tests still serve their own artifact.
- **#122.** The guard catches the planted requests (`test_no_network.py:14`), leaves loopback and
  Unix sockets alone, and broke nothing: 1743 passed. By reading the standard library, `ssl` and
  `asyncio` connections go through the patched `connect` and `getaddrinfo` too.
- **#123.** The new launcher case binds TEST-NET-1 with a Host list, so only the bound is wrong, and a
  regressed preflight fails to bind instead of serving. The nightly catch-up waits 60 s
  (`nightly.py:71`), past the test's 30 s timeout, so a regressed run starts no refresh. Replacing
  the preflight `if` with `if false` fails both parameters (mutant killed).
- **#105.** The 30 table pointers that differ from the base each land on the test their row means. I
  read every one. Eleven moved with this wave's own #119 edit, ten with its `test_engine_service.py`
  edits, nine with W6. The two stale ones I traced to their first commit (`REQ-GRD-003`,
  `REQ-REF-009`) are re-pointed to the test first cited. Moving one pointer by a line fails the gate
  (mutant killed).
- **#119.** The gate reads the tuning `.json` sets as decoded strings and never prints a question. I
  planted a live question (a long one inside a longer string, and a short one whole) in a scratch
  copy of a tuning set: both were caught, and the output named only the file and the length.
- **#121.** `save` still refuses a non-file URL before any write. The new test fails when
  `url.isFileURL` is removed (Swift mutant, 2 failures). The egress gate stays exact: each pinned
  expression must occur once and is removed before the scan (`test_router_hints.py:569-576`), so a
  second `write(` anywhere in `FrontDoor.swift` still fails. `make client-decls` is file-scoped and
  passes in all four configurations. The app builds the store only through `.onDevice`.
- **#124.** The payload and the README carry "Capabilities & benchmarking". The string is served
  from the constant at request time, so no artifact holds the old title. Both copies are pinned
  (mutants killed).
- **#120.** D-174's amendment names the served artifact and is an amendment, not a reversal. My own
  seat was set up that way, and the suite passed on it.
- **Records.** The invariants list closes G-4, G-5 and G-6, and the count line is right (71 rows, 5
  partial). The commit messages list each relabelled row (#118), and each issue's change. No drive-by
  edits: every file maps to a planned issue.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code:

- **INV-6 (no test reaches the network).** `socket.socket.connect` / `connect_ex`, `socket.getaddrinfo`
  (and through them `create_connection`, `ssl`, `httpx`, `asyncio`): `test_no_network.py:14`.
  `gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, `getnameinfo`, `sendto` / `sendmsg`:
  no test, unguarded. Child processes: no test, unguarded. Module/session fixtures and import time:
  no test, unguarded. `RUN_CONTRACT_TESTS=1`: unguarded by design.
- **INV-27 (the launcher refuses on any preflight problem).** The one branch at
  `engine_service.sh:63-67`, fed by `validate_startup_config`: the bind without hosts
  (`test_engine_service.py:376`), the ranked-rows and standings bounds (`:398-399`, new). The other
  producers (an unusable artifact, the refresh switch, a CORS wildcard) reach the same branch and
  run as a script in no test; the branch itself is held.
- **INV-67 (the typed question is kept only in the register file).** `GapRegisterStore.save` with the
  default writer: `FrontDoorTests.swift:765` (new) and the existing hardening tests.
  `GapRegisterStore.load`: `testTheRegisterIsOnlyEverAFileOnThisDevice`. A `write:` closure built in
  another file: no data-flow test; held by the file-scoped text gate and `client-decls` (G-1, #85).
- **#102's rule (a repeat is the same model).** The value pick: `test_recommend.py:638`. The budget
  pick: no test. The leader repeated: no test.

Gaps: M1 (INV-6), M3 (#102); INV-67's writer seam is G-1 (#85), already tracked; R3 below.

## Acceptance criteria evidence

From `docs/plans/m18-wave-7-plan.md:41-44`.

- P0, the plan and the amendment → `docs/plans/m18-wave-7-plan.md`; `docs/plans/m18-plan.md:230-233`.
- #102, a repeat by model id → `recommend.py:532-533` + `test_recommend.py:638`. Budget half unheld (M3).
- #103, one account → `build.py:781` + `test_build.py:549`.
- #104, a command that runs → `engine_service.sh:49` + `test_engine_service.py:561`. Wrong `--db`
  for the service (M6).
- #112, product names, one Claude order → `registry.py:82-87`, `:518-547`, `:557-558` +
  `test_display_names.py:44`, `:51`, `:58`, `:63`. Not over the served names (M4).
- #114, either order → `test_empty_answer_reasons.py:113-121` + `test_api_config.py:731`; checked
  by hand (32 passed in the failing order). The gate is narrow (M5).
- #122, a planted request fails → `tests/conftest.py:51-79` + `test_no_network.py:14`, `:24`.
  In-process only (M1).
- #123, the bound refusal as a script → `test_engine_service.py:398-419`.
- #105, every pointer lands, stale ones corrected → `test_prd_citations.py:66`, `:72` +
  `docs/prd.md` (30 pointers). Table rows only; `Makefile:108` stale (M2).
- #119, a held-out question in a tuning set fails → `test_ios_client_contract.py:192-215`, `:218`.
- #118, greetings labelled `NOT_A_SEARCH` → `offtopic_questions.json:33`,
  `offtopic_heldout_questions.json:7`, `:16`; listed in `f8ca4d9`'s message. Its reader (M7).
- #121, a non-file save fails a test → `FrontDoor.swift:290-297`, `:332` +
  `FrontDoorTests.swift:765`; `test-manifest.txt:170`; pins at `test_router_hints.py:525-526`.
- #124, Epoch's title → `board_tables.py:29`, `README.md:74` + `test_recommend.py:655`.
- #120, D-174 names the served artifact → `docs/decisions.md:3614-3619`.

## Every file in the diff

- `README.md`: Epoch's citation title (#124).
- `docs/decisions.md`: D-174's amendment (#120).
- `docs/plans/m18-plan.md`: the W7 amendment.
- `docs/plans/m18-wave-7-plan.md`: the wave plan (to be deleted before merge).
- `docs/prd.md`: 30 re-pointed citations (#105); sampled in full.
- `docs/security-invariants.md`: INV-6, INV-27, INV-67 rows gain tests; G-4 to G-6 closed (M1).
- `ios/EngineTests/FrontDoorTests.swift`, `test-manifest.txt`: the save-side test (#121).
- `ios/ModelRanking/Engine/FrontDoor.swift`: the injected writer (#121).
- `scripts/engine_service.sh`: the hint (#104, M6).
- `scripts/router_probe/offtopic_*.json`: three labels (#118, M7).
- `src/app/workflows/board_tables.py`: Epoch's title (#124).
- `src/app/workflows/build.py`: one account (#103).
- `src/app/workflows/recommend.py`: repeat by row (#102, M3).
- `src/app/workflows/registry.py`: Claude order and `DISPLAY_NAMES` (#112, M4).
- `tests/conftest.py`: the network guard (#122, M1).
- `tests/integration/test_cli_e2e.py`, `tests/unit/test_categories.py`, `test_rank.py`,
  `test_subscribe.py`: new Claude spellings in assertions only.
- `tests/unit/test_api_config.py`: the reload gate (#114, M5).
- `tests/unit/test_build.py`: #103's test.
- `tests/unit/test_display_names.py`: #112's tests (M4).
- `tests/unit/test_empty_answer_reasons.py`: the reload removed (#114).
- `tests/unit/test_engine_service.py`: #123's case and #104's test.
- `tests/unit/test_ios_client_contract.py`: the held-out gate reads `.json` sets (#119).
- `tests/unit/test_no_network.py`: #122's tests.
- `tests/unit/test_prd_citations.py`: the PRD gate (#105, M2).
- `tests/unit/test_recommend.py`: #102's and #124's tests, new Claude spellings.
- `tests/unit/test_router_hints.py`: two exact egress pins (#121).

## K.8 contract drift check

The plan's K.8: no `/v1` field changes; #112 changes `models.display` values only.

- `/v1`, the schema and the app's client are untouched:
  ```
  $ git diff --stat e023296 58e8bf4 -- src/app/adapter src/app/workflows/serialize.py src/app/workflows/schema.py ios/ModelRanking/Engine/Models.swift ios/ModelRanking/Engine/EngineClient.swift
  (no output)
  $ grep -n "display TEXT" src/app/workflows/schema.py
  27:    display TEXT NOT NULL,
  ```
- The ranking seam #102 relies on is unchanged:
  ```
  $ git grep -n "def ranked_with_ids\|def category_ranking" -- src
  src/app/workflows/rank.py:269:def category_ranking(conn: sqlite3.Connection, spec: CategorySpec) -> list[RankingRow]:
  src/app/workflows/rank.py:278:def ranked_with_ids(conn: sqlite3.Connection, spec: CategorySpec) -> list[tuple[str, RankingRow]]:
  ```
- `GapRegisterStore`'s public init gains a defaulted `write:` parameter. The app uses only `.onDevice`:
  ```
  $ git grep -n "GapRegisterStore" -- ios/ModelRanking
  ios/ModelRanking/ContentView.swift:49:    @State private var gaps = GapRegisterStore.onDevice.load()
  ios/ModelRanking/ContentView.swift:630:                        GapRegisterStore.onDevice.save(gaps)
  ios/ModelRanking/ContentView.swift:868:            GapRegisterStore.onDevice.save(gaps)
  ios/ModelRanking/Engine/FrontDoor.swift:278:public struct GapRegisterStore {
  ios/ModelRanking/Engine/FrontDoor.swift:288:    let write: (Data, GapRegisterStore) throws -> Void
  ios/ModelRanking/Engine/FrontDoor.swift:291:                write: @escaping (Data, GapRegisterStore) throws -> Void = { data, store in
  ios/ModelRanking/Engine/FrontDoor.swift:302:    public static var onDevice: GapRegisterStore {
  ios/ModelRanking/Engine/FrontDoor.swift:305:        return GapRegisterStore(
  ```
- Verdict: OK. No `/v1` field moved. The one widened Swift signature is internal to the app and is
  noted as R3.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/router_probe/offtopic_questions.json:5`, `:9`. **Knowledge questions in the
  off-topic sets still expect a surface.** "what is the capital of france" and "who won the world cup
  in 2022" are labelled `assistant|everyday~`. D-169 and REQ-ASK-005 name a knowledge question as not
  a search. #118's scope pinned greetings, thanks and chit-chat only, so this is outside it. Bug in
  test data.
- **K2** `src/app/workflows/registry.py:465-492`. **One release is served under two model ids, with
  its evidence split.** `claude3-haiku` holds Claude 3 Haiku's ECI score; `claude3-haiku20240307`
  holds its Arena, GPQA, AIME and MMLU scores. I checked the same split in the served artifact for
  Claude 3 Opus, Claude 3 Sonnet, Claude 3.5 Haiku, and `o3` (SWE-bench, Aider, ECI) beside
  `o3-2025-04-16` (Arena, GPQA, Epoch's SWE-bench Verified and more). #112's table makes each pair
  readable, as two models. Where a release had one snapshot, the dated id is the same model, so a
  list that joins boards can show it twice. Bug.
- **K3** `src/app/workflows/registry.py:281`, `:382`. **`o3-mini-high` is served as a model of its
  own.** It is o3-mini at high reasoning effort. The grammar reads `_high` and `(high)` as an effort,
  not `-high`, so OpenRouter's slug derives a separate model (`test_display_names.py:27` now blesses
  its name). Bug (REQ-CAN-005).
- **K4** `tests/unit/test_ios_client_contract.py:208-215`. **The held-out gate is case-sensitive.** A
  live question copied in upper case into a tuning set passes (planted and checked, unprinted). The
  `.swift` / `.py` half has the same rule. Enhancement.
- **K5** `docs/prd.md` REQ-REF-009 row. **The carry row cites the negative case only.**
  `test_nightly_refresh.py:653` is "nothing is carried when nothing is"; the test that names each
  carried source and its age (`:639`) is not cited. Enhancement (records).

## Risks queued to next M

- **R1** `src/app/workflows/registry.py:518-558`. **The name table wins over every source and grows
  by hand.** If a maker renames a model, or a board starts giving a good spelling, the table keeps
  its own. A new model served under its raw id is seen by no test (M4). What would show it: a refresh
  record whose `renamed` list stays empty while a board's spelling changed, or
  `select id from models where display = id` returning more than the six OpenAI ids.
- **R2** `tests/conftest.py:37-44`. **The guard trusts loopback.** A local proxy (`HTTPS_PROXY` to
  127.0.0.1) or any local relay carries a test's request off the machine and passes. No proxy
  variable is set in this seat. What would show it: a shell or CI runner with a proxy variable, and a
  test whose client honours it (`httpx` does by default).
- **R3** `ios/ModelRanking/Engine/FrontDoor.swift:288-296`. **The register's bytes now pass through a
  closure any file can supply.** Today only `.onDevice` builds the store, and the file-scoped gates
  refuse an egress API in any other file. A relay through an allowed sink is G-1 (#85). What would
  show it: a `write:` argument outside `FrontDoor.swift` and the tests.

## Gates and probes run

All in this seat's worktree, output to files, exit codes read:

- `make test`: 1743 passed, 25 skipped; coverage floor PASS. Exit 0.
- `make lint`, `make typecheck`, `make check-records`: exit 0.
- `make client-decls`: PASS, 19 files in 4 configurations. Exit 0.
- `make swift-test`: PASS, 451 tests, each in the manifest. Exit 0.
- #114 by hand: `test_empty_answer_reasons.py` before `test_api_config.py`, 32 passed.
- Mutants (each restored, `git diff --quiet` after each): 11 Python mutants on the fixes, 10 killed
  (M3's survived); the copied-rows mutant, survived the full suite (M3); the aliased reload, passed
  the gate (M5); three held-out plants, two caught (K4); one Swift mutant (`url.isFileURL` removed),
  killed.
- No network mutant was run: removing the guard would have sent real lookups. Those paths were
  checked by reading and by the `__qualname__` probe.

**Seat notes.** A `git grep` for `NOT_A_SEARCH` printed lines of a live held-out set to this seat's
terminal. Nothing from it is written in this record or anywhere else. No process I started is left
running; the worktree holds only this file as a change.
