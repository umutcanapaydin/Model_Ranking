---
record_type: review
id: m17-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-26
---
# Wave 4 Tester Review (m17)

**Reviewer:** Tester subagent, third seat (fresh eyes). This seat wrote none of the wave's code. It is not one of the wave's Code-Reviewers, not its security seat, and not either of the earlier Testers.
**Independent:** yes
**Date:** 2026-09-26
**Commit range:** `7d7a9ac..f781cbd` (the whole wave)
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)
**Supersedes:** the second Tester's BLOCKING verdict, committed in `a5b85ec`. That verdict and the first Tester's (`b35eb3e`) stay in git history.
**Model routing (HIGH, advisory):** the author is from the Claude family (`GP-Agent: claude-code/local-lane`). This reviewer is also Claude (Opus 5.5). Fallback reason: no second model family is available to this seat. Fresh context: this seat started from the role file, `practices.md`, the plan, D-167 and its amendments, the three committed reviews and the diff. It has no memory of any authoring or reviewing session.
**Base-pinned policy:** `.claude/agents/Tester.md`, `.agents/rules/practices.md` and `permission-matrix.md` §11 are unchanged in the range.

## Verdict
BLOCKING

**The second Tester's findings are resolved.** `f781cbd` changes tests only. The sha256 of every production file equals its value at `4203673`. I re-ran each surviving mutant from that verdict, and each one is now killed:
- B1 (R-PY31): killed by `test_board_standings.py:402` `[empty_medians]`;
- B2 (A-SW01, A-SW03): killed by `CombineTests.swift:105`;
- B3 (A-SW06): killed by `CombineTests.swift:114`;
- M1 (N08), M2 (N01) and M3 (N15, N16): killed by `test_board_standings.py:454`, `:461` and `:474`;
- M4: the comment at `StandingsStoreTests.swift:132` now cites the research record, not D-167.

**Everything I measured on the wave's behaviour is right.** `make check-fast` passes. `combine()` matches my own implementation of D-167 clause 3 on 3,000 fuzzed inputs, with 0 disagreements (see P3). The research record's three combination tables reproduce exactly on `advisor.db`.

**One load-bearing behaviour still has a fault that no test can catch (B1).** It is the store's second day. The tests prove the first refetch after a day. They do not prove that the refetched standings are stored and served. Break either of those, and all 300 Swift tests still pass. The phone would then:
- fetch again every time it is asked, from the second day on; or
- serve yesterday's standings right after fetching today's.

At HIGH tier, the fault-injection protocol makes the missing test mandatory in this wave. I verified the fix in scratch. It is the author's to commit, because this seat may modify only this file.

**Third strike:** none. B1 is new. Neither earlier Tester raised the store's refresh cycle as BLOCKING. The first Tester's M5 was a MINOR, and it covered only the stamp on a first fetch. No finding here repeats one that was BLOCKING in both earlier verdicts.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `f781cbd`. The mutant ids are defined under "Fault injection".

**P1: the route** (`tests/unit/test_board_standings.py`, header cites D-160 and D-167)
- **Declared and additive.**
  - Test: `tests/unit/test_api_v1.py:541`.
  - GREEN.
- **Positions only, and no score.**
  - Tests: `test_board_standings.py:119` and `:140`.
  - GREEN. T3-PY17 (a score field added to each standing) is killed by `:140`.
- **Tied models share a position.**
  - Test: `:67`.
  - GREEN. T3-PY03 (no ties) and T3-PY04 (dense ranking) are killed.
  - Exact-equality ties are unpinned (**M3**).
- **D-112 effort, and the evidence row.**
  - Tests: `:74`, `:85`, `:288`, `:300`, `:314` and `:461`.
  - GREEN. T3-PY02, T3-PY05, T3-PY06 and T3-PY07 are killed.
  - Name before harness survives (**M2**).
- **Only rankable models.**
  - Tests: `:107` and `:363`.
  - GREEN. T3-PY19 (LEFT JOINs) is killed.
- **Dated and attributed.**
  - Tests: `:154`, `:169`, `:350` and `:454`.
  - GREEN. T3-PY09 (the pricing attribution dropped) and T3-PY10 (the oldest observation) are killed.
- **Models: blend and accessibility.**
  - Test: `:185`.
  - GREEN. T3-PY08 (rounded to 1 place) is killed.
- **A query string is ignored.**
  - Test: `:227`.
  - GREEN. T3-PY20 is killed. It gives the route a `boards=` query that filters the payload.
- **Bounds checked at boot.**
  - Tests: `:245`, `:267`, `:382` and `:474`.
  - GREEN. T3-PY11, T3-PY12 and T3-PY13 are killed.
  - The pin at `:474` is conditional (**M4**).
- **The closed 503 paths, and the refusal after boot.**
  - Tests: `:236`, `:331`, `:402` (3 cases), `:425` and `:436`.
  - GREEN. R2-PY31, T3-PY14, T3-PY15 and T3-PY16 are killed.
- **The payload contract against the Swift structs.**
  - Test: `tests/unit/test_ios_payload_contract.py:264`.
  - GREEN.

**P2: fetch and store**
- **`testTheBoardsRequestCarriesNothing`, and no header of its own.**
  - Tests: `ios/EngineTests/EngineClientTests.swift:470` and `:491`.
  - GREEN. T3-EC01 (a query item sent) is killed.
- **An oversized or undecodable response is refused.**
  - Tests: `EngineClientTests.swift:505` and `:518`, and `StandingsStoreTests.swift:119` and `:131`.
  - GREEN. T3-EC02 (`<` at the ceiling) is killed.
- **The last good payload is kept when a fetch fails.**
  - Test: `StandingsStoreTests.swift:76`.
  - GREEN. T3-ST05 is killed.
- **Refetched after a day and not before.**
  - Tests: `StandingsStoreTests.swift:51` and `:65`.
  - GREEN. T3-ST04 (two days) is killed.
  - **Only the first cycle is proven. T3-ST01, T3-ST02 and T3-ST03 survive (B1).**
- **Only decoded fields are stored.**
  - Test: `:105`.
  - GREEN. T3-EC03 (the engine's bytes stored verbatim) is killed.
- **The client-declaration gate and the D-126 text gate.**
  - `make check-fast` runs `client-decls`, which PASSES in 4 configurations. `tests/unit/test_router_hints.py` is GREEN.
  - K1/#51 and #60 are accepted as filed. They are not re-raised here.

**P3: the combination** (`ios/EngineTests/CombineTests.swift`, header cites D-160 clause 2 and D-167 clause 3)
- **All present.**
  - Test: `:30`.
  - GREEN. T3-SW05 (union) and T3-SW06 (the third board ignored) are killed.
- **The order comes from positions: re-ranked, then summed.**
  - Tests: `:38`, `:59`, `:69` and `:105`.
  - GREEN. T3-SW03, R2-A-SW01 and R2-A-SW03 are killed.
- **Ties broken by id, deterministic.**
  - Tests: `:48` and `:78`.
  - GREEN. T3-SW04 is killed.
- **One board, board order, duplicates, refusals.**
  - Tests: `:90`, `:96`, `:127`, `:135`, `:141`, `:147` and `:156`.
  - GREEN. T3-SW07 and T3-SW08 are killed.
- **Each result names the boards it came from, with its positions.**
  - Test: `:114`.
  - GREEN. R2-A-SW06 and T3-SW02 are killed.
  - The chosen order is unpinned (**M1**).
- **Independent check, new at this seat.**
  - Setup:
    - A scratch probe package compiles HEAD's `Engine/` sources, byte-identical by sha256.
    - The probe generates 3,000 random payloads with ties: 2,552 of them hold a tie. It then chooses random sets of boards, repeats included.
    - The output is compared with `tester3-w4/fuzz_check.py`. That script is my own implementation from D-167's text: exact rational means, competition ranks among the common models, and the id tie-break.
  - What is compared: the order, each entry's published positions, and `list.boards`.
  - Result: **0 disagreements**, 1,197 of them multi-board with 2 or more models.
  - The checker can fail: with the quadratic-mean mutant in the probe copy, it reports 241 disagreements.

**P4: measured and recorded**
- Reproduced at `f781cbd` through `TestClient` on the worktree's `advisor.db`, with `APP_BUILD` set:
  - 200, with 63 boards, 303 models and 6,955 positions;
  - 499,117 bytes raw and 36,407 gzip;
  - `_egress_problems` returns `[]`, and there are no startup warnings.
- The record's three tables reproduce exactly from my own replay:
  - arena_text_coding + epoch_swe_bench_verified: 30 in common, starting "Claude Opus 4.7, 3, [4, 1]";
  - arena_text_math + epoch_frontiermath + epoch_aime: 51 in common, with the GPT-5.5 and Qwen3.8 Max tie at 19;
  - arena_text_coding + arena_agent + epoch_terminalbench: 3 in common.
- `docs/research/m17-w4-standings-payload-2026-09-25.md:25-27`.

## Red→green on reported symptoms
- **`f781cbd` is tests only.** It touches 4 files: `CombineTests.swift`, `StandingsStoreTests.swift`, `test-manifest.txt` and `test_board_standings.py`.
- **Each added test's red is the second Tester's mutant.** I re-applied each mutant here, and each goes RED on the new test (see "Fault injection").
- **Weakened or deleted tests across the whole range: none.** `git diff 7d7a9ac..f781cbd -- tests ios/EngineTests` removes exactly one line. It is the old route set in `test_api_v1.py:539`, and a superset replaces it.
- In `f781cbd`, the `no_medians` case is kept beside the new `empty_medians` case, and the `:114` assertions are unchanged. The only change there is an added unchosen board.

## Suite result
- **`make check-fast` at `f781cbd`, clean tree: PASS in 39.0 s.**
  - lint, typecheck and records pass;
  - test: **1459 passed, 23 skipped**, and coverage-floor PASS (41 modules, floor 60 %);
  - client-decls: PASS, 13 files in 4 configurations;
  - swift-test: **300 tests, exactly the manifest**.
- **Coverage on touched code.** Branch coverage came from `pytest tests/unit -n auto --cov=src --cov-branch`. HEAD is the worktree. The base is a `git archive` of `7d7a9ac` in scratch, with `PYTHONPATH` set to its `src`.
  - **`src/app/adapter/main.py`: 96.73 % → 97.06 %.** At both base and HEAD, 12 lines and 3 branches are missing. They are the same lines, shifted by the wave's insertions, so no wave line is uncovered.
  - `src/app/workflows/rank.py`: 93.67 % → 97.47 %.
  - `src/app/workflows/standings.py`: new, at **100 %**, with no missing line or branch.
  - No module dropped. Total: 91.15 % → 91.44 %.
- **Clean-up after the runs.**
  - `git status` is clean.
  - The sha256 of all 220 tracked files under `src tests ios scripts` equals the pre-run baseline (`tester3-w4/sha-baseline.txt`).
  - Two existing `.pyc` files were rewritten despite `PYTHONDONTWRITEBYTECODE=1`: `adapter/__pycache__/main` and `workflows/__pycache__/standings`. I deleted both. The `__pycache__` set otherwise equals the pre-run list.

## Fault injection (HIGH: mandatory)
- **Harness.** `tester3-w4/mut3.py` edits exact bytes in place. It restores in place and asserts that the sha256 equals the pre-edit value after every restore. `PYTHONDONTWRITEBYTECODE=1` is set.
- **Commands.**
  - Python mutants ran against the whole unit suite (`-n auto`).
  - Swift mutants ran against `CombineTests|StandingsStoreTests|BoardsRequestTests`. Every survivor was re-run against the full `swift test` (300 tests).
  - For every Swift kill, the output shows an XCTest `error: -[…]` assertion. None was a compile error.
  - Python and Swift runs never overlapped, because some Python tests read the Swift sources.
- **Ids.** `R2-` means one of the second Tester's survivors, re-run. `T3-` means a new mutant from this seat.

**Python (25 mutants): 23 killed, 2 survived.**
- **Killed:**
  - R2-PY31, R2-N01, R2-N08, R2-N15 and R2-N16 (all five previous survivors);
  - T3-PY02 to T3-PY17, T3-PY19 and T3-PY20.
- **Survived:**
  - **T3-PY01** (the evidence tie broken by name before harness): **M2**;
  - **T3-PY18** (scores that round equal treated as tied): **M3**.
- **Kill rate:** 23 of 25, **92 %**.

**Swift (20 mutants): 15 killed, 5 survived.**
- **Killed:**
  - R2-A-SW01, R2-A-SW03 and R2-A-SW06 (all three previous survivors);
  - T3-ST04, T3-ST05, T3-SW02 to T3-SW08, and T3-EC01 to T3-EC03.
- **Non-equivalent survivors:**
  - **T3-ST01**: `save(fresh, at: now)` runs only when nothing was stored. That is **B1**;
  - **T3-ST02**: the stored standings are served after a successful refetch. That is **B1**;
  - **T3-ST03**: a refetch is saved with the old stamp. That is **B1**;
  - **T3-SW01**: `list.boards` and each entry's positions follow the payload's order, not the chosen order. That is **M1**.
- **Outside any stated rule:** T3-ST06, where `load()` decodes the stored bytes without passing them through `FetchedStandings`, so the ceiling is skipped on read. The file is one the app itself wrote from a payload that already passed the ceiling. Not a finding.
- **Kill rate:** 15 of 19 non-equivalent mutants, **79 %**.

## Mocks / contract tests
- **The engine route, seen by the phone.**
  - The one canonical stub is `StubProtocol` in `ios/EngineTests/EngineClientTests.swift`. No parallel stub was added.
  - The contract is `tests/unit/test_ios_payload_contract.py:264`. It drives the real route through `TestClient` into the Swift structs.
  - OK.
- **External integrations:** none new in this wave.

## BLOCKING
- **B1** `ios/ModelRanking/Engine/StandingsStore.swift:84-87`; `ios/EngineTests/StandingsStoreTests.swift:51-63`. **"The store refetches after a day and not before" (plan P2; D-167 clause 1) is proven only for the first day.**
  - Each of these mutants passes all 300 Swift tests:
    - **T3-ST01:** the refetch is not saved over an existing store;
    - **T3-ST03:** the refetch is saved with the old stamp;
    - **T3-ST02:** the stored standings are served instead of the fetched ones.
  - The test at `:51` counts fetches but never checks what was served or stored after the refetch. Every fixture fetches the same payload, so stale and fresh look identical. `:86` and `:124` start with an empty store, so the save runs under every mutant.
  - Under T3-ST01 or T3-ST03, from the second day on the phone fetches `/v1/boards` every time it is asked, forever. Each request then marks when a question was asked, and every question costs a 500 KB download. That breaks D-167 clause 1's "fetches again when it is a day old", which the owner ruled. Under T3-ST02, the first question after a refresh is answered from yesterday's boards.
  - **Fix**, verified in scratch (`tester3-w4/probe/Tests/ProbeTests/Tester3Probe.swift`, `testTheSecondDayIsServedFromTheRefetchAndNotFetchedAgainForADay`). It passes on HEAD's sources, and it goes RED on T3-ST01, T3-ST02 and T3-ST03 (`tester3-w4/probe_red.log`):
    1. Store a payload whose board is `old` at `arrived`.
    2. At `arrived + 86_400`, call `current` with a fetch that returns a payload whose board is `new`. Assert that the served board ids are `["new"]` and that `load()?.fetchedAt == arrived + 86_400`.
    3. An hour later, call `current` again. Assert that the fetch count is still 1.

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `ios/ModelRanking/Engine/Combine.swift:25-26,47-52,84`; `ios/EngineTests/CombineTests.swift:114-125`. **"In the order the boards were chosen" is documented and unpinned.**
  - `list.boards` and each entry's positions could follow the payload's order, not the chosen order (T3-SW01), and all 300 tests would still pass. The `:114` test chooses `["x", "y"]`, which is also the payload's order.
  - The second Tester's B3 fix proposed choosing `["y", "x"]`, and `f781cbd` kept `["x", "y"]`.
  - W5's detail screen reads these lists.
  - **Fix**, verified against T3-SW01: `testTheListAndEachEntryFollowTheChosenOrderNotThePayloads` in the same probe file. With payload x, y, z, choose `["y", "x"]`. Assert that the boards are `["y", "x"]` and that a's positions are `[y: 4, x: 1]`.
- **M2** `src/app/workflows/standings.py:77`; `tests/unit/test_board_standings.py:461-471`. **The evidence tie-break's priority, harness before name, is unpinned.**
  - Sorting by `(raw_name, harness)` (T3-PY01) passes every test. In the new fixture, the `a-harness` row with the lowest harness also has the lowest name.
  - `rank.category_ranking` orders harness before name (`rank.py:290`), and the docstring claims the same.
  - **Probe** (`tester3-w4/probe_py.py harness-before-name`): name `a-name` with harness `b-harness` at `low`, and name `z-name` with harness `a-harness` at `max`, both at one score and one date. The standing must say `max`. It passes on HEAD and fails on T3-PY01.
- **M3** `src/app/workflows/standings.py:111`; `tests/unit/test_board_standings.py:67`. **A tie is exact equality of scores, and nothing pins that.**
  - Treating scores that round equal as tied (T3-PY18) passes every test. Every fixture's scores are whole numbers apart.
  - Arena's Elo scores and Epoch's percentages carry decimals.
  - **Probe** (`probe_py.py near-scores-not-tied`): a at 55.4 and b at 55.2 must stand 1 and 2. It passes on HEAD and fails on T3-PY18.
- **M4** `tests/unit/test_board_standings.py:480`. **The pin for the second Tester's M3 is conditional.** When `MODEL_RANKING_MAX_PUBLISHED_STANDINGS_ROWS` is set in the environment, the test asserts nothing and passes. Pin the default where it is read, with the variable removed: for example, re-evaluate the module-level expression under `monkeypatch.delenv`. Or skip the test loudly when the variable is set.

## Tests added/extended this review
- None in the repository. This seat may modify only this file.
- Scratch probes, not committed. Each passes on HEAD and fails on its mutant:
  - `/private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/tester3-w4/probe/Tests/ProbeTests/Tester3Probe.swift`: B1 (T3-ST01, ST02 and ST03) and M1 (T3-SW01). The red runs are in `…/tester3-w4/probe_red.log`;
  - `…/tester3-w4/probe_py.py`: M2 (T3-PY01) and M3 (T3-PY18);
  - `…/tester3-w4/probe/Tests/ProbeTests/FuzzProbe.swift` and `…/tester3-w4/fuzz_check.py`: the P3 fuzz comparison.
- Mutant specs and outputs:
  - `…/tester3-w4/{py_specs,sw_specs,py_probe_specs}.json`;
  - `…/tester3-w4/outputs/`;
  - `…/tester3-w4/mutants.log`;
  - `…/tester3-w4/{py_run,sw_run,sw_full}.log`;
  - coverage in `…/tester3-w4/cov-{base,head}.json`.
