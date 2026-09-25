---
record_type: review
id: m17-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-26
---
# Wave 4 Tester Review (m17)

**Reviewer:** Tester subagent, fourth seat (fresh eyes). This seat wrote none of the wave's code. It is not one of the wave's Code-Reviewers, not its security seat, and not any of the three earlier Testers.
**Independent:** yes
**Date:** 2026-09-26
**Commit range:** `7d7a9ac..1398820` (the whole wave)
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)
**Supersedes:** the third Tester's BLOCKING verdict, committed in `1cff428`. That verdict and the first two (`b35eb3e`, `a5b85ec`) stay in git history.
**Model routing (HIGH, advisory):** the author is from the Claude family (`GP-Agent: claude-code/local-lane`). This reviewer is also Claude (Opus 5.5). Fallback reason: no second model family is available to this seat. Fresh context: this seat started from the role file, `practices.md`, the plan, D-167 and its amendments, the committed reviews and the diff. It has no memory of any authoring or reviewing session.
**Base-pinned policy:** `.claude/agents/Tester.md`, `.agents/rules/practices.md` and `docs/permission-matrix.md` are unchanged in the range (`git diff --stat 7d7a9ac..1398820` on them is empty).

## Verdict
BLOCKING

**The third Tester's findings are resolved.** `1398820` changes tests only. `git diff --stat ebde1d6..1398820 -- src ios/ModelRanking scripts` is empty. I re-ran every surviving mutant from that verdict, and each one is now killed:
- B1: T3-ST01, T3-ST02 and T3-ST03 are killed by `StandingsStoreTests.swift:65` (XCTest assertions at `:82`, `:83`, `:84` and `:86`).
- M1: T3-SW01 is killed by `CombineTests.swift:127`.
- M2: T3-PY01 is killed by `test_board_standings.py:487`.
- M3: T3-PY18 is killed by `test_board_standings.py:498`.
- M4: the pin at `test_board_standings.py:474` no longer depends on the environment. Its new form has a MINOR gap of its own (**M2** below).

**The production code is right.** On the real payload from `advisor.db`, I compared Swift's `combine()` with my own Python reading of D-167 clause 3, written from the ADR's text. Over 6,241 real board sets there were 0 disagreements (details under P3). `make check-fast` passes.

**Two load-bearing behaviours still have faults that no test catches:**
- **B1:** the combination's **re-rank among the shared models** (D-167 clause 3) is unpinned. Rank each model on the whole board instead, and all 302 Swift tests still pass. On the real boards, that fault changes the list in 5,617 of 6,001 board sets. It also changes the first line of the research record's first table.
- **B2:** the store's day restarts only when the refetched standings **differ**. If a refetch that returns the same standings is not stamped, all 302 tests still pass. The phone would then fetch on every question until the engine's standings change.

For each one, a test that passes on HEAD and fails on the mutant is verified in scratch. Writing those tests is the author's job, because this seat may modify only this file.

**Third-strike check.**
- **B2 does not repeat an earlier BLOCKING twice.** The store's refresh was BLOCKING only in the third verdict (its B1), not in the first or second.
- **B1 falls under a clause that was BLOCKING in both earlier verdicts: D-167 clause 3's ordering.**
  - The first verdict's B1 was a sum against the best rank.
  - The second verdict's B2 was the arithmetic mean against other means.
  - Both were about the step that aggregates the ranks (`Combine.swift:69`). Their mutants are killed today.
- **B1 is a different fault.** It is in the step before, the re-rank (`Combine.swift:68`). No earlier verdict raised it or tested it.
- **This seat's judgement: B1 is not the same finding,** so it is not a third strike. But it has the same pattern: every fixture is one where the wrong rule gives the same order as the right one. The controller should decide whether `/close-wave` step 3 counts "the ordering rule" as one finding. If it does, this is the third BLOCKING on it.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `1398820`. Mutant ids are defined under "Fault injection".

**P1: the route** (`tests/unit/test_board_standings.py`, header cites D-160 and D-167)
- **Declared and additive:** `tests/unit/test_api_v1.py:541`. GREEN.
- **Positions only, no score:** `:119` and `:140`. GREEN.
- **Tied models share a position; only exact ties:** `:67` and `:498`. GREEN. T3-PY18 is killed.
- **D-112 effort and the evidence row:** `:74`, `:85`, `:288`, `:300`, `:314`, `:461` and `:487`. GREEN. T3-PY01 and T4-PY07 are killed.
- **Only rankable models:** `:107` and `:363`. GREEN.
- **Dated and attributed:** `:154`, `:169`, `:350` and `:454`. GREEN. The date's scope under an effort policy is unpinned (**M1**).
- **Models: blend and accessibility:** `:185`. GREEN.
- **A query string changes nothing:** `:227`. GREEN.
- **Bounds and refusals checked at boot:** `:245`, `:267`, `:382` and `:474`. GREEN. T4-PY04 is killed. The default's pin reads source text (**M2**).
- **The closed 503 paths:** `:236`, `:331`, `:402` (3 cases), `:425` and `:436`. GREEN. T4-PY05 (the reason leaked into the body) is killed by `:331`.
- **The payload contract against the Swift structs:** `tests/unit/test_ios_payload_contract.py:264`. GREEN.

**P2: fetch and store**
- **The request carries nothing, and no header of its own:** `ios/EngineTests/EngineClientTests.swift:470` and `:491`. GREEN. T4-EC01 (a header on the boards request only) is killed by `:491`.
- **An oversized or undecodable response is refused:** `EngineClientTests.swift:505` and `:518`; `StandingsStoreTests.swift:143` and `:155`. GREEN.
- **The last good payload is kept when a fetch fails:** `StandingsStoreTests.swift:100`. GREEN. T4-ST04 is killed.
- **Refetched after a day and not before:** `StandingsStoreTests.swift:51`, `:65` and `:89`. GREEN. T4-ST05 (12 hours) is killed.
  - **Proven only when the refetched standings differ from the stored ones: T4-ST01 survives (B2).**
- **Only decoded fields are stored:** `:129`. GREEN. T4-ST07 is killed.
- **The caches directory:** pinned by the exact expression in `tests/unit/test_router_hints.py:359`. T4-ST06 (the documents directory) is killed.
- **The client-declaration gate and the D-126 text gate:** `make check-fast` runs `client-decls`, which PASSES (13 files, 4 configurations). `test_router_hints.py` is GREEN. #51 and #60 are accepted as filed and not re-raised.

**P3: the combination** (`ios/EngineTests/CombineTests.swift`, header cites D-160 clause 2 and D-167 clause 3)
- **All present:** `:30`. GREEN. T4-SW04 is killed.
- **Re-ranked among the common models:** `:38` claims it ("d is on y only and does not count").
  - **It does not prove it: T4-SW02 survives (B1).**
- **Ordered by the arithmetic sum, ties rank competitively:** `:59`, `:69` and `:105`. GREEN. T4-SW01 is killed.
- **Ties broken by id, never by name:** `:48` and `:78`. GREEN. T4-SW03 and T4-SW06 are killed.
- **One board, choice order, duplicates, refusals:** `:90`, `:96`, `:138`, `:146`, `:152`, `:158` and `:167`. GREEN. T4-SW05 (an unknown board skipped) is killed.
- **Each result names its boards, in the chosen order:** `:114` and `:127`. GREEN. T3-SW01 is killed.
- **Independent check on real data, new at this seat.**
  - A scratch probe package compiles HEAD's `ios/ModelRanking/Engine/*.swift`, byte-identical by sha256 (`tester4-w4/engine-src.sha`).
  - It reads the real payload from a local file: `board_standings(open_readonly(advisor.db))`, with 63 boards, 303 models and 6,955 positions. It calls `combine()` on 6,241 board sets: every ordered pair, plus a fixed sample of triples.
  - `tester4-w4/real_check.py` computes each result from D-167's text: exact rational means, competition ranks among the shared models, and the id tie-break.
  - What is compared: the order, each entry's published positions, and `list.boards`. It also checks that the list is never longer than the smallest chosen board.
  - Result: **0 disagreements**, 6,001 of the sets with 2 or more models.
  - The checker can fail: with T4-SW02 in the probe copy it reports **5,617 disagreements**.

**P4: measured and recorded**
- `board_standings` on the worktree's `advisor.db`, serialised with the record's method, gives 63 boards, 303 models and 6,955 positions. That is 499,614 bytes raw and 36,392 gzip; the record has 499,633 and 36,407. The same boards, models and positions, and within 0.01 %.
- The record's three tables reproduce exactly from my own replay. Their sums are:
  - 3, 5, 9, 11 and 12;
  - 4, 7, 14, 19 and 19, with the GPT-5.5 and Qwen3.8 Max tie ordered by id;
  - 4, 5 and 9.
- `docs/research/m17-w4-standings-payload-2026-09-25.md:39-72`.

## Red→green on reported symptoms
- **`1398820` is tests only.** It touches `CombineTests.swift`, `StandingsStoreTests.swift`, `test-manifest.txt` and `test_board_standings.py`.
- **Each added test's red is the third Tester's mutant.** I re-applied each one here, and each goes RED on its new test (see "Fault injection").
- **Weakened or deleted tests across the whole range:** one line is removed, the old route set at `test_api_v1.py:539`, and a superset replaces it.
  - Inside `1398820`, the environment-conditional ceiling pin was replaced by a source-text pin. It no longer passes vacuously, but it proves less than a value pin would (**M2**).

## Suite result
- **`make check-fast` at `1398820`, clean tree: PASS in 48.5 s.**
  - lint, typecheck and records pass;
  - test: **1461 passed, 23 skipped**, and coverage-floor PASS (41 modules, floor 60 %);
  - client-decls: PASS;
  - swift-test: **302 tests, exactly the manifest**.
- **Coverage on touched code.** Branch coverage from `pytest tests/unit -n auto --cov=src --cov-branch`. HEAD is the worktree. The base is a `git archive` of `7d7a9ac` in scratch, with `PYTHONPATH` set to its `src`.
  - The base tree has no `advisor.db`, so 56 of its tests skip, which puts its figures lower. The third Tester, with the database, measured `main.py` at 96.73 % at base.
  - `src/app/adapter/main.py`: 95.86 % → **97.06 %**;
  - `src/app/workflows/rank.py`: 93.67 % → **97.47 %**;
  - `src/app/workflows/standings.py`: new, **100 %**, with no missing line or branch.
  - **No module dropped.** Total: 91.08 % → 91.44 %.
- **Clean-up.**
  - `git status` is clean.
  - All 220 tracked files under `src tests ios scripts` match the pre-run sha256 baseline (`tester4-w4/sha-baseline.txt`).
  - The `__pycache__` set equals the pre-run list. Two existing `.pyc` files were rewritten despite `PYTHONDONTWRITEBYTECODE=1`: `adapter/__pycache__/main` and `workflows/__pycache__/standings`. I deleted both.

## Fault injection (HIGH: mandatory)
- **Harness.** `tester4-w4/mut4.py` makes exact byte edits in place. It restores in place and asserts that the sha256 equals the pre-edit value after every restore; every restore matched (`tester4-w4/mutants.log`). `PYTHONDONTWRITEBYTECODE=1` is set.
- **Commands.**
  - Python mutants ran against the whole unit suite (`-n auto`).
  - Swift mutants ran against `CombineTests|StandingsStoreTests|BoardsRequestTests`. Every survivor was re-run against the full `swift test` (302 tests, 0 failures).
  - T4-ST06 ran against the Swift-reading Python tests and `make client-decls`.
  - Every Swift kill is an XCTest `error: -[…]` assertion, never a compile error.
- **Ids.** `T3-` is one of the third Tester's survivors, re-run. `T4-` is a new mutant from this seat.

**Re-runs (6): all killed.** T3-PY01, T3-PY18, T3-ST01, T3-ST02, T3-ST03 and T3-SW01.

**New Python mutants (8): 4 killed, 4 survived.**
- **Killed:**
  - T4-PY04: the boot check stops refusing a payload the route would refuse;
  - T4-PY05: the refusal's reason leaks into the 503 body;
  - T4-PY07: `ranking_effort` is dropped from the board;
  - T4-PY08: the metric-direction guard is removed.
- **Survived, non-equivalent:**
  - **T4-PY02**: the board's date also counts rows its effort policy excluded. That is **M1**.
  - **T4-PY03**: the bound is computed as 10 × the default. That is **M2**.
- **Survived, equivalent under every stated rule, and not findings:**
  - T4-PY01 orders a tie inside the payload by raw name. D-167 clause 2 says a tie's order carries no meaning, and the bytes stay stable, so `:227` holds.
  - T4-PY06 orders `models` by display name. The phone looks models up by id, and no rule orders that list.

**New Swift mutants (14): 10 killed, 4 survived.**
- **Killed:** T4-ST04 to T4-ST07, T4-SW01, T4-SW03 to T4-SW06, and T4-EC01.
- **Survived, non-equivalent:**
  - **T4-SW02**: each model ranked on the whole board, not among the shared models. That is **B1**.
  - **T4-ST01**: an unchanged refetch is not saved. That is **B2**.
  - **T4-ST02**: a refetch is stamped at the old stamp plus one day. It is closed by B2's test. On its own it would be MINOR: after an N-day gap, it costs at most N−1 extra fetches.
- **Survived, equivalent in practice:** T4-ST03 changes `fetchedAt <= now` to `<`. It differs only when a question arrives at exactly the stored instant.

**Kill rates, non-equivalent mutants, re-runs included:**
- Python: 6 of 8, **75 %**;
- Swift: 14 of 17, **82 %**.

## Mocks / contract tests
- **The engine route, seen by the phone.**
  - The one canonical stub is `StubProtocol` in `ios/EngineTests/EngineClientTests.swift`. No parallel stub was added.
  - The contract is `tests/unit/test_ios_payload_contract.py:264`. It drives the real route through `TestClient` into the Swift structs.
  - OK.
- **External integrations:** none new in this wave.

## BLOCKING
- **B1** `ios/ModelRanking/Engine/Combine.swift:64-68`; `ios/EngineTests/CombineTests.swift:38-46`. **"It re-ranks them on each board among themselves by position" (D-167 clause 3; plan P3) has no test that fails when the re-rank is removed.**
  - **The mutant, T4-SW02.** `let rank = 1 + board.standings.filter { $0.position < standing.position }.count` ranks a model among every model on the board, not among the shared ones. All 302 Swift tests pass (`tester4-w4/outputs/T4-SW02-…@swall.txt`: "Executed 302 tests, with 0 failures").
  - **Why `:38` does not catch it.** Its x board holds only shared models, so its gapped positions 1, 5 and 9 re-rank to 1, 2 and 3 either way. On y, d is counted under the mutant, and the order a, c, b comes out the same. Every other multi-board fixture holds only shared models. The test's own comment, "d … does not count", is never checked.
  - **The consequence on real boards.** Without the re-rank, a large board outweighs a small one. On `advisor.db` the list changes in 5,617 of 6,001 board sets with 2 or more models.
    - In the research record's first table (`arena_text_coding` + `epoch_swe_bench_verified`), Claude Opus 4.6 becomes first instead of Claude Opus 4.7, and 24 of 30 places differ.
    - This is the owner's ruled rule (D-167 clause 3), the product's own ordering.
  - **Fix**, verified in scratch (`tester4-w4/probe/Tests/ProbeTests/Tester4Probe.swift`, `testModelsOnlyOneBoardRanksDoNotCountInTheReRank`). It passes on HEAD and fails on T4-SW02 (`tester4-w4/probe_red.log`):
    - board x ranks c 1, d 2, e 3, a 4, b 5; board y ranks a 1, b 2, c 3;
    - assert the order **a, c, b**;
    - counting d and e gives c, a, b.
- **B2** `ios/ModelRanking/Engine/StandingsStore.swift:84-87`; `ios/EngineTests/StandingsStoreTests.swift:51-87`. **"The store refetches after a day and not before" (plan P2; D-167 clause 1) is proven only when the refetched standings differ from the stored ones.**
  - **The mutant, T4-ST01.** `if fresh.payload != stored?.payload { save(fresh, at: now) }` is a plausible "don't rewrite identical bytes" optimisation. All 302 Swift tests pass.
  - **Why the tests miss it.** The third Tester's fix at `:65` refetches `"today"` over `"yesterday"`, so the save always runs. `:51` refetches identical standings, but it never looks at the stamp afterwards or asks again.
  - **The consequence.** Whenever the engine's standings have not changed since the last fetch, the stamp is never renewed. From then on, the phone fetches `/v1/boards` on every question, and each fetch marks when a question was asked. This is the same consequence the third Tester's B1 was raised for. It is reached through a path that B1's fix does not cover.
  - **Fix**, verified in scratch (`Tester4Probe.swift`, `testAnUnchangedRefetchAfterAGapRestartsTheDay`). It passes on HEAD and fails on T4-ST01 and on T4-ST02:
    1. Store a payload at `arrived`.
    2. At `arrived + 3 days`, call `current` with a fetch that returns the same payload. Assert that `load()?.fetchedAt` equals that time.
    3. An hour later, call `current` again. Assert that the fetch count is still 1.

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `src/app/workflows/standings.py:114-121`; `tests/unit/test_board_standings.py:85-95,350-360`. **A board's date comes from the rows that stand on it, and nothing pins that under an effort policy.**
  - T4-PY02 dates a board from every row, including rows its `ranking_effort` excluded. It passes every test: the policy fixtures give no `run_date`, and the dating fixture has no policy.
  - It has no effect on today's `advisor.db`: DeepSWE's filtered rows are no newer.
  - **Probe:** on `epoch_deepswe_external`, a `max` row dated 2026-09-20 and a `high` row dated 2026-09-01. Assert that `evidence_date == "2026-09-01"`.
- **M2** `tests/unit/test_board_standings.py:474-484`; `src/app/adapter/main.py:220`. **The M4 fix pins the default's text, not the bound's value.**
  - The test regex-matches `"25000"` in the module source. T4-PY03 (`MAX_PUBLISHED_STANDINGS_ROWS = 10 * int(...)`) passes every test, and so would a change to the whitespace or quoting that the regex does not expect.
  - The bound's behaviour is proven by `:245` and `:382`, so this is the record's figure only.
  - **Fix:** re-evaluate the module-level expression with the variable removed (`monkeypatch.delenv`, then `importlib.reload` in a subprocess, or read it through a small function) and assert that the value is 25,000.

## Tests added/extended this review
- None in the repository. This seat may modify only this file.
- Scratch probes, not committed. Each passes on HEAD's sources and fails on its mutant:
  - `/private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/tester4-w4/probe/Tests/ProbeTests/Tester4Probe.swift`. It covers B1 (T4-SW02) and B2 (T4-ST01, T4-ST02). The red runs are in `…/tester4-w4/probe_red.log`.
  - `…/tester4-w4/probe/Tests/ProbeTests/RealBoardsProbe.swift` with `…/tester4-w4/real_check.py`: the P3 real-data comparison. It reads `…/tester4-w4/boards.json`, a local file.
  - `…/tester4-w4/rerank_vs_full.py`: B1's effect on real boards.
- Mutant specs and outputs:
  - `…/tester4-w4/{rerun_specs,new_specs}.json`;
  - `…/tester4-w4/outputs/` and `…/tester4-w4/mutants.log`;
  - coverage in `…/tester4-w4/cov-{base,head}.json`;
  - `make check-fast` in `…/tester4-w4/check-fast.log`.
