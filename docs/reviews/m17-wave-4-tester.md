---
record_type: review
id: m17-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-26
---
# Wave 4 Tester Review (m17)

**Reviewer:** Tester subagent, second seat (fresh eyes). This seat did not write any of the wave's code. It is not one of the wave's Code-Reviewers, not its security seat, and not the previous Tester.
**Independent:** yes
**Date:** 2026-09-26
**Commit range:** `7d7a9ac..4203673` (the whole wave)
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)
**Supersedes:** the BLOCKING Tester verdict committed at `b35eb3e`. It stays in git history.
**Model routing (HIGH, advisory):** the author is from the Claude family (`GP-Agent: claude-code/local-lane`). This reviewer is also Claude (Opus 5.5). Fallback reason: no second model family is available to this seat. Fresh context: this seat started from the role file, the plan, D-167, the three committed reviews and the diff. It has no memory of the authoring or reviewing sessions.
**Base-pinned policy:** `.claude/agents/Tester.md`, `.agents/rules/practices.md` and `permission-matrix.md` §11 do not change in the range.

## Verdict
BLOCKING

The previous verdict's findings, re-run:
- **B2 is resolved.** Its mutant is now killed.
- **B3 is resolved.** `main.py` is back to 97.06 %, and it leaves uncovered exactly the lines the base left uncovered.
- **M1, M2, M3, M5, M6 and M8 are resolved.** Each mutant is killed.
- **M4's refusal is sound.** I measured it (see "Judgments").

The wave's behaviour is right wherever I measured it:
- On the real `advisor.db`, the Swift `combine` and my own Python implementation of D-167 clause 3 agree on all 2,316 board sets (0 disagreements).
- `make check-fast` passes.

Three load-bearing behaviours still have a fault that stays green across the whole suite. At HIGH tier, the fault-injection protocol makes the missing test mandatory in this wave. I checked each fix below against its mutant in scratch. I may edit only this file, so the tests are the author's to write.
- **B1:** `/v1/boards` fails closed on an unbuilt artifact, but nothing tests that. Drop the guard and the route answers **200 with no boards**, and every test still passes. A phone would store that answer for a day.
- **B2:** the previous B1 is only half resolved. The tests now tell the mean from the best and the worst rank, but a **geometric mean** or a **quadratic mean** of the ranks still passes all 299 Swift tests. On real data either one changes the list in 96 % of multi-board choices.
- **B3:** the plan says "each result names the boards it came from" (P3). Its test cannot tell the chosen boards from every board in the payload.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `4203673`. The mutant ids are defined under "Fault injection".

**P1: the route** (`tests/unit/test_board_standings.py`, header cites D-160 and D-167)
- **Declared and additive.**
  - Test: `tests/unit/test_api_v1.py:541`.
  - GREEN. R-PY30 is killed.
- **Positions only, no score.**
  - Tests: `test_board_standings.py:119` and `:140`.
  - GREEN. R-PY13 is killed.
  - On `advisor.db`, the payload's key set is exactly the frozen one. The word "score" appears only in attribution prose ("Coding scores: swebench.com …"), never as a key or a number.
- **D-112 effort.**
  - Tests: `:74`, `:85`, `:288`, `:300` and `:314`.
  - GREEN. R-PY01, 02, 03, 06, 07 and 19 are killed.
  - The evidence tie-break's harness and name order is unpinned (**M2**).
- **Competition ties.**
  - Test: `:67`.
  - GREEN. R-PY04 and R-PY05 are killed.
  - `advisor.db`: 0 violations across 63 boards and 6,955 positions.
- **Only rankable models.**
  - Tests: `:107`, and `:363` (previous M3).
  - GREEN. R-PY16 and R-PY12 are killed.
  - `advisor.db`: `models` is exactly the set of models that stand.
- **Dates and attribution.**
  - Tests: `:154` and `:169`, and `:350` (previous M2).
  - GREEN. R-PY11, R-PY14, R-PY15, N02 and N03 are killed.
  - An undated board's `evidence_date: null` is unpinned (**M1**).
- **Models: blend, display, vendor, accessibility.**
  - Test: `:185`.
  - GREEN. R-PY20, N04, N05 and N09 are killed.
- **Boot refusals and the egress bound.**
  - Tests: `:245`, `:267` and `:98`, and `:382` (previous M1).
  - GREEN. R-PY21, 22, 23 and 24, and N18, are killed.
  - The bound's 25,000 default is unpinned (**M3**).
- **Closed 503 paths.**
  - Tests: `:236`, `:331`, `:403` (parametrised), `:423` and `:434`.
  - GREEN. R-PY25, 26, 27 and 32, and N11, N13 and N14, are killed.
  - **The unbuilt-artifact guard is NOT proven. R-PY31 survives (B1).**
- **A query string is ignored.**
  - Tests: `:227`.
  - GREEN. R-PY28 is killed.
  - `advisor.db`: 499,117 identical bytes with and without `?boards=epoch_chess&task=coding`.
- **The payload contract against the Swift structs.**
  - Test: `tests/unit/test_ios_payload_contract.py:264`.
  - GREEN. R-G11, R-G12 and R-G15 are killed.

**P2: fetch and store**
- **Nothing sent.**
  - Tests: `ios/EngineTests/EngineClientTests.swift:470` and `:491`.
  - GREEN. R-EC01, R-EC02 and R-EC04 are killed.
- **The ceiling.**
  - Tests: `EngineClientTests.swift:518`, and `StandingsStoreTests.swift:119` and `:131` (previous M6).
  - GREEN. R-FS02, R-FS03 and R-FS04 are killed.
  - The comment at `:132` cites D-167 for a number D-167 does not contain (**M4**).
- **An unreadable response is refused.**
  - Test: `EngineClientTests.swift:505`.
  - GREEN. R-EC03 is killed.
- **Freshness and clock skew.**
  - Tests: `StandingsStoreTests.swift:51` and `:65`.
  - GREEN. R-ST01, R-ST02, R-ST08, R-ST09, A-ST10 and A-ST13 are killed.
- **The last good payload is kept, and a fresh fetch is stamped.**
  - Tests: `:76` and `:86`, and `:124` (previous M5).
  - GREEN. R-ST03, R-ST04, R-ST05, A-ST12 and A-ST14 are killed.
- **Non-file addresses refused.**
  - Test: `:93` (`load`).
  - GREEN. R-ST06 is killed.
  - R-ST07 (`save`) is equivalent: I measured it (see "Judgments").
- **Only decoded fields are stored.**
  - Test: `:105`.
  - GREEN. R-FS01 is killed.

**P3: the combination** (`ios/EngineTests/CombineTests.swift`, header cites D-160 clause 2 and D-167 clause 3)
- **All present.**
  - Test: `:30`.
  - GREEN. R-SW01 is killed.
- **Re-ranked among the common models.**
  - Test: `:38`.
  - GREEN. R-SW05 is killed.
- **Ordered by the mean of the ranks.**
  - Tests: `:38` and `:69` (previous B1).
  - GREEN. R-SW11 (best rank) and A-SW02 (worst rank) are killed.
  - **A-SW01 (geometric mean) and A-SW03 (quadratic mean) survive (B2).**
- **Competition ties when re-ranking.**
  - Test: `:59`.
  - GREEN. R-SW02 and A-SW04 (dense) are killed.
- **Ties broken by id, never by display name.**
  - Tests: `:48`, and `:78` (previous B2).
  - GREEN. R-SW03 and R-SW04 are killed.
- **One board, board order, positions per board.**
  - Tests: `:90`, `:96` and `:105`.
  - GREEN. R-SW12 and A-SW05 are killed.
- **Each result names the boards it came from.**
  - Test: `:105-110`.
  - **NOT proven. A-SW06 survives (B3).**
- **Refusals and duplicates.**
  - Tests: `:116`, `:124`, `:130`, `:136` and `:145`.
  - GREEN. R-SW06, 07, 08, 09 and 10 are killed.

**The gates**
- **The D-126 text gate.**
  - Test: `tests/unit/test_router_hints.py:233`.
  - GREEN. R-G01, R-G02, R-G07, R-G14 and A-G18 are killed. A-G18 moves the store to the Documents folder, and the exact `.cachesDirectory` expression catches it.
- **client-decls.**
  - PASS in 4 configurations. R-G16 and R-G17 FAIL in all 4.
  - A-G19 survives: it lets `Combine.swift` write files by editing the gate's own list. This is the known K1 (`docs/reviews/m17-wave-4-review.md:313`), not a new finding.
- **The arithmetic and sort tripwires.**
  - Tests: `tests/unit/test_ios_client_contract.py:207`, `:211` and `:308`.
  - GREEN. R-G03, R-G04, R-G05, R-G08, R-G09, R-G10 and R-G13 are killed.
  - R-G06 survives. It is filed as #60, which is OPEN.

**P4: measured and recorded**
- Reproduced at `4203673` through `TestClient` on the worktree's `advisor.db`:
  - 63 boards, 303 models, 6,955 positions;
  - 499,117 bytes raw and 36,407 gzip;
  - `_egress_problems` returns `[]`.
- The previous M8 row is now labelled "served after the first nightly refresh with W3 (2026-09-25 23:05 local)". That is before its commit, `ebde1d6`, at 23:37 +0300.
- **"A combination on real boards compared by hand"**, done independently. `tester2-w4/real_combine.py` re-implements D-167 clause 3 from its text: exact rational means, competition ranks among the common models, the id tie-break. It compares that against the Swift `combine` run in a probe package over HEAD's Engine sources. Across the 2,316 sets (every single board, every pair and 300 random sets of 3 to 6 boards; 2,176 of them multi-board with 2 or more models), there are **0 disagreements**. Each single board equals its own order.

## Red→green on reported symptoms
- **`4203673` is tests only.** Its production files are byte-identical to `ebde1d6`: the sha256 values for `standings.py`, `main.py`, `Combine.swift`, `StandingsStore.swift`, `Models.swift` and `EngineClient.swift` all equal the previous verdict's.
- **Each added test's red is its mutant.** I re-applied each one here: SW11, SW04, ST05, FS02, FS04, PY12, PY14, PY15, PY21 and PY22. Each goes RED on its mutant and GREEN on HEAD.
- **Weakened or deleted tests:** none. `4203673` adds 145 lines and deletes 1, a line in the research record. The previous seat covered the rest of the range, and I re-checked it.

## Suite result
- **`make check-fast` at `4203673`, clean tree: PASS.**
  - lint, typecheck and records pass;
  - test: **1455 passed, 23 skipped**, and coverage-floor PASS (41 modules);
  - client-decls: PASS in 4 configurations;
  - swift-test: **299 tests, exactly the manifest**.
- **Coverage on touched code**, from `pytest tests/unit -n auto --cov=src --cov-branch`. The base is a `git archive` of `7d7a9ac` in scratch; HEAD is the worktree.
  - **`src/app/adapter/main.py`: 96.73 % → 97.06 %.**
    - At HEAD, 12 lines and 3 branches are missing. That is the same set as at the base, shifted by the wave's insertions. No wave line is uncovered.
    - `:520-521` is the old ranking-rows refusal, which `_egress_problems` moved from the base's `:540-541`.
  - `src/app/workflows/standings.py`: new, at **100 %**.
  - No module dropped. Total: 91.15 % → 91.44 %.
- **Clean-up after the runs.**
  - `git status` is clean. Every mutated file's sha256 equals `git show HEAD:<file>`.
  - Two `.pyc` files, `adapter/main` and `workflows/standings`, were rewritten during the runs, despite `PYTHONDONTWRITEBYTECODE=1`. Their headers matched the restored sources. I deleted both anyway.

## Judgments on the refused and filed findings
- **M4 (the `isFileURL` guard in `save()`): the refusal is sound.**
  - In a probe package (`tester2-w4/probe`, no network), I ran `save()` with the guard removed against five kinds of non-file URL:
    - a `data:` URL;
    - a custom scheme, with and without a host, whose path points into scratch;
    - a scheme-less absolute path;
    - a scheme-less relative path.
  - The guard-less `save()` created **no file and no folder** in all five cases, and so did the guarded one.
  - Neither `createDirectory(at:)` nor `Data.write(to:)` acts on a non-file URL, so no offline test can tell the two apart. R-ST07 survives the full 299-test suite, and it is equivalent.
  - The guard stays as defence in depth. `load()`'s guard is pinned (R-ST06 killed).
- **M7 → #60** is OPEN, and R-G06 still survives. Accepted as filed.

## Fault injection (HIGH: mandatory)
- **Harness.** Each mutant was applied in place as a byte replacement by `tester2-w4/mut2.py`, then restored in place, with the sha256 checked after every restore and `PYTHONDONTWRITEBYTECODE=1` set.
- **Commands.**
  - Every Python mutant ran against the whole unit suite (`-n auto`).
  - Swift mutants ran against `CombineTests|StandingsStoreTests|BoardsRequestTests`. Every Swift survivor was then re-run against the full `swift test` (299 tests), and each still survived.
  - Gate mutants ran through their gate.
- **What counts as killed.** For every Swift kill, the output shows an XCTest `error: -[…]` assertion. None was a compile error.
- **Ids.**
  - `R-` means one of the previous seat's mutants, re-run.
  - `N-` and `A-` mean new mutants from this seat.

**Python (52 mutants): 39 killed, 13 survived; 6 of the survivors are equivalent or outside any stated rule.**
- **Killed:**
  - R-PY01 to R-PY16, R-PY19 to R-PY30, and R-PY32 (the previous survivors PY12, 14, 15, 21 and 22 are now killed);
  - N02, N03, N04, N05, N09, N11, N13, N14, N17 and N18.
- **Equivalent, or outside any rule:**
  - R-PY17: LEFT JOIN on `models`. The `px_median` inner join still drops a NULL id;
  - R-PY18: a standing's effort taken from the policy. The filter makes the two equal;
  - N06: boards in reverse order. No order is specified;
  - N07: tied models in some other order. D-167 clause 2 says a tie's order means nothing (#44);
  - N12: the `is_file()` check dropped. A directory still gets the 503 from `open_readonly`;
  - N20: the empty-effort skip in `_policies` dropped. No conflict arises in today's `CATEGORIES`.
- **Non-equivalent survivors:**
  - **R-PY31** (`require_price_medians` dropped from the route): **B1**;
  - **N01** (the evidence tie broken by harness in reverse): **M2**;
  - **N08** (an undated board given its observation date as `evidence_date`): **M1**;
  - **N15** and **N16** (the default bound at 2,500,000, or at 5,000, below the measured 6,955): **M3**;
  - **N10** (a board dated from its evidence rows only, not every row it keeps). Not a finding: "the newest `run_date`" does not say which rows.
  - **N19** (`elo` removed from `HIGHER_IS_BETTER`). Not a finding: it fails closed, since the boot refuses on real data.
- **Kill rate:** 39 of 46 non-equivalent mutants, **85 %**. The previous seat's rate was 83 %.

**Swift (43 mutants): 35 killed, 8 survived; 4 of the survivors are equivalent.**
- **Killed:**
  - R-SW01 to R-SW12, R-ST01 to R-ST06, R-ST08, R-ST09, R-FS01 to R-FS04, and R-EC01 to R-EC04 (the previous survivors SW04, SW11, ST05, FS02 and FS04 are now killed);
  - A-SW02, A-SW04, A-SW05, A-ST10, A-ST12, A-ST13 and A-ST14.
- **Equivalent:**
  - R-ST07: measured, see M4 above;
  - A-SW07 (the last duplicate model description wins) and A-SW08 (rank counted on the whole board): these differ only on a malformed payload that lists one model twice, and no rule covers that case;
  - A-EC05 (an `EngineError` wrapped again as `.undecodable`): the same case, and its detail still says "larger than".
- **Non-equivalent survivors:**
  - **A-SW01** (sum → product of the ranks, a geometric mean): **B2**;
  - **A-SW03** (sum → sum of squared ranks, a quadratic mean): **B2**;
  - **A-SW06** (`CombinedList.boards` = every board in the payload): **B3**;
  - **A-ST11** (a store stamped at exactly `now` is fetched again). Not a finding: it differs only at zero elapsed time and costs one extra download.
- **Kill rate:** 35 of 39 non-equivalent mutants, **90 %**.

**Gates (19 mutants): 17 killed.** R-G01 to R-G05, R-G07 to R-G17, and A-G18. The survivors are R-G06 (#60) and A-G19 (K1).

## Mocks / contract tests
- **The engine route, seen by the phone.** The one canonical stub is `StubProtocol` in `ios/EngineTests/EngineClientTests.swift`; no parallel stub was added. The contract is `tests/unit/test_ios_payload_contract.py:264`, which drives the real route through `TestClient` into the Swift structs. OK.
- **External integrations:** none new in this wave.

## BLOCKING
- **B1** `src/app/adapter/main.py:1408`; `tests/unit/test_board_standings.py:402-420`. **The route's fail-closed guard on an unbuilt artifact (REQ-API-008) has no test that fails when it is removed.**
  - With `require_price_medians(conn)` deleted (R-PY31), all 1,455 unit tests pass.
  - The B3 test's `no_medians` case runs `DROP TABLE px_median`. That also breaks `board_standings`' own join, so the route answers 503 with or without the guard.
  - The case the guard exists for is W-023's: an **empty** `px_median` (`rank.py:214-222`). On an empty `px_median`, the mutant answers **200** `{"boards":[],"models":[]}`. A phone would decode that, store it (`StandingsStore.current`) and refuse every combination for a day.
  - The previous seat called PY31 "equivalent in what a reader sees". It is not.
  - **Fix**, verified in scratch: add an `empty_medians` case (`DELETE FROM px_median` on `_seeded_db`) and assert the closed 503. It passes on HEAD and fails on R-PY31 (`tester2-w4/probe_py.py PY31`).
- **B2** `ios/ModelRanking/Engine/Combine.swift:69`; `ios/EngineTests/CombineTests.swift:38-46,69-76`. **"Ordered by the mean of those ranks" (D-167 clause 3) still admits two other means. The previous B1 is only half resolved.**
  - With the sum replaced by a product of the ranks (A-SW01, a geometric mean) or by a sum of squared ranks (A-SW03, a quadratic mean), all 299 Swift tests pass.
  - The two ordering fixtures give the same order under the arithmetic, geometric and quadratic means. The previous B1's own fix targeted only the best rank.
  - On `advisor.db`, the geometric mean gives a different list from the arithmetic mean in 2,081 of 2,176 multi-board choices, and the quadratic mean in 2,082.
  - **Fix**, verified in scratch against A-SW01, A-SW03, A-SW02 and R-SW11 (`tester2-w4/probe/Tests/ProbeTests/CombineProbe.swift`):
    - board x ranks a 1, p 2, b 3, m 4, e 5;
    - board y ranks m 1, p 2, e 3, b 4, a 5;
    - assert the order **p, m, a, b, e**;
    - the geometric mean reads m, p, a, b, e; the quadratic mean reads p, m, b, a, e.
- **B3** `ios/EngineTests/CombineTests.swift:105-110`; `Combine.swift:84`. **"Each result names the boards it came from" (plan P3) is not proven.**
  - The test's payload holds only boards x and y, and both are chosen. `CombinedList(boards: standings.boards, …)`, which names every board in the payload, passes all 299 tests (A-SW06).
  - W5's detail screen shows these boards' dates and attributions (`Combine.swift:29-30`), so the mutant would attribute a list to boards the reader never chose.
  - **Fix**, verified in scratch against A-SW06: put a third, unchosen board z in the payload, choose `["y", "x"]`, and assert `list.boards.map(\.id) == ["y", "x"]`.

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `src/app/workflows/standings.py:120`; `ios/ModelRanking/Engine/Models.swift:338-339`. **A board with no `run_date` publishing `evidence_date: null` is unpinned.**
  - Filling in the observation date (N08) passes every test, although the Swift model documents `nil` "for a board that publishes none".
  - 5 of the 63 real boards are undated.
  - Probe: `tester2-w4/probe_py.py N08`.
- **M2** `standings.py:77`. **The evidence row's last tie-break, harness then raw name, is unpinned.**
  - Reversing it (N01) passes every test. The second review's M8 claimed that this tie-break mirrors `rank.category_ranking`, and only the `run_date` step is pinned (R-PY07).
  - It decides which effort a standing discloses.
  - Probe: two rows with an equal score and an equal date, harness `h1` at `low` and `h2` at `max`; the standing must say `low` (`probe_py.py N01`).
- **M3** `src/app/adapter/main.py:220`. **The engine's default bound of 25,000 positions is unpinned. It is the Python half of the previous M6.**
  - Raising it 100 times (N15) passes every test. So does lowering it below the measured 6,955 (N16), which would refuse to boot on today's artifact.
  - The Swift ceiling is now pinned at 4 MiB. Its engine-side twin is not.
- **M4** `ios/EngineTests/StandingsStoreTests.swift:132`. **The test comment says the ceiling is "the number D-167 names". D-167 names no byte ceiling** (`docs/decisions.md:3082-3137`). The 4 MiB is stated in `docs/research/m17-w4-standings-payload-2026-09-25.md:33` and in `EngineClient.swift:153-156`. Cite the record, or add the number to D-167.

## Tests added/extended this review
- None in the repository. This seat may modify only this file.
- Scratch probes, not committed. Each passes on HEAD and fails on its mutant:
  - `/private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/tester2-w4/probe_py.py`: B1 (R-PY31), M1 (N08) and M2 (N01);
  - `…/tester2-w4/probe/Tests/ProbeTests/CombineProbe.swift`: B2 (A-SW01, A-SW03, A-SW02, R-SW11) and B3 (A-SW06);
  - `…/tester2-w4/probe/Tests/ProbeTests/M4Probe.swift`: the M4 judgment;
  - `…/tester2-w4/probe/Tests/ProbeTests/RealDataProbe.swift` and `…/tester2-w4/real_combine.py`: the real-data comparison.
- Mutant specs and outputs:
  - `…/tester2-w4/{py_specs,py_probe_specs,sw_specs,sw_full_specs,gate_specs,g12}.json`;
  - `…/tester2-w4/outputs/`;
  - `…/tester2-w4/mutants.log`.
