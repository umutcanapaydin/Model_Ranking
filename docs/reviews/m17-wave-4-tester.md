---
record_type: review
id: m17-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# Wave 4 Tester Review (m17)

**Reviewer:** Tester subagent (fresh eyes — did not author wave, and is neither of its Code-Reviewers nor its security seat)
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `7d7a9ac..ebde1d6` (15 commits, 21 files)
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)
**Model routing (HIGH, advisory):** author family Claude (`GP-Agent: claude-code/local-lane` trailers) / reviewer family Claude (Opus 5.5). Fallback reason: no second model family is available to this seat. Fresh context: this seat started from the role file, the plan, D-167 and the diff, with no memory of the authoring sessions.
**Base-pinned policy:** `.claude/agents/Tester.md`, `.agents/rules/practices.md` and `permission-matrix.md` §11 are unchanged in the range (`git diff --stat 7d7a9ac..ebde1d6` lists none of them).

## Verdict
BLOCKING

The wave's behaviour is correct everywhere I measured it. On the real `advisor.db`, all 12 single-source surfaces match their board exactly: the same models, in the same order, at the same effort. The suite is green. 16 of the 17 gate mutants were refused, and every route and store criterion has a citing test that catches a mutant.

Three things stop the wave from closing under this profile's rules:
- **The combination's ordering rule is not proven.** A best-rank aggregation survives all 295 Swift tests (**B1**).
- **"Never by a display name" is not proven.** A tie broken by display name survives all 295 Swift tests (**B2**).
- **Coverage dropped on a touched module** (`permission-matrix.md` §11), in `main.py` (**B3**).

Each fix is a few lines, and I verified each proposed test against its mutant in scratch. I may modify only this file, so the tests are the author's to add. None of the three is a defect in shipped behaviour.

## Acceptance-criterion coverage (REQUIRED)

Each criterion lists its citing tests, what they assert, and the mutant ids that prove each test can fail. The ids are listed under "Fault injection" below. All tests are green at `ebde1d6`.

**P1: the route** (`tests/unit/test_board_standings.py`, header cites D-160 and D-167)
- **Declared and additive.**
  - Test: `tests/unit/test_api_v1.py:541`. The expected route set gained only `/v1/boards`, and no existing key-set test changed in the range.
  - GREEN. PY30 (route undeclared) is killed.
- **Positions only, no score anywhere.**
  - Tests: `test_board_standings.py:119` (walks every key; positions are ints) and `:140` (frozen key sets).
  - GREEN. PY13 (a `score` field added) is killed by both.
- **D-112 effort, per board and per standing.**
  - Tests: `:74`, `:85`, `:288` (the M8 tie-break), `:300` (the R5 benchmark policy) and `:314` (two efforts refused).
  - GREEN. PY01, PY02, PY03, PY06, PY07 and PY19 are killed.
  - On `advisor.db`, every standing on `epoch_deepswe_external` is at `high`. The effort of every standing equals what the surface picks on all 12 single-source surfaces.
- **Tied positions (competition ranking).**
  - Test: `:67`.
  - GREEN. PY04 (no ties) and PY05 (dense ranking) are killed.
  - On `advisor.db`: 0 competition-ranking violations across 63 boards and 6,955 positions.
- **Only rankable models stand.**
  - Test: `:107`.
  - GREEN. PY16 (unpriced models joined) is killed.
  - PY17 (LEFT JOIN on `models`) survives, but it is equivalent: the inner join on `px_median` still drops a NULL `model_id`.
  - The model list is not pinned to the models that stand (**M3**).
- **Attribution.**
  - Tests: `:154`, `:169`, and the boot-time case `:267`.
  - GREEN. PY11 is killed by both.
- **The boot refusals.**
  - Test: `:267`, parametrised over an unattributed source and an undeclared metric direction.
  - Test: `:98`, a source holding two boards.
  - GREEN. PY09, PY10, PY23 and PY24 are killed.
- **The egress bound.**
  - Test: `:245`.
  - GREEN, but it cannot tell positions from boards, or `>` from `>=` (**M1**).
- **The post-boot 503.**
  - Test: `:331`. It asserts the closed 503, no reason in the body, and the reason in the log.
  - GREEN. PY25, PY26, PY27 and PY32 are killed. PY32 is the second review's surviving mutant, "ValueError dropped from the route's except", and it is now killed.
- **The query string is ignored.**
  - Test: `:227`.
  - GREEN. PY28 (a `boards=` query that filters) is killed.
  - Measured on `advisor.db`: the same 499,117 bytes with and without a query.
- **The payload contract against the Swift structs.**
  - Test: `tests/unit/test_ios_payload_contract.py:264`.
  - GREEN. G11 (a required field the route does not serve), G12 and G15 (CodingKey drift) are killed.

**P2: the fetch and the store**
- **Nothing sent.**
  - Tests: `ios/EngineTests/EngineClientTests.swift:470` (path and no query) and `:491` (no header of its own, GET, no body).
  - GREEN. EC01 (a query item), EC02 (an `X-Task` header) and EC04 (an extra path segment) are killed.
- **The ceiling, and an unreadable response refused.**
  - Tests: `EngineClientTests.swift:518` and `:505`, and `StandingsStoreTests.swift:119`.
  - GREEN. FS03 and EC03 are killed.
  - The ceiling's boundary and its size are unpinned (**M6**).
- **Freshness.**
  - Test: `StandingsStoreTests.swift:51`.
  - GREEN. ST01 (fresh at exactly a day), ST08 and ST09 are killed.
- **Clock skew.**
  - Test: `StandingsStoreTests.swift:65`.
  - GREEN. ST02 is killed.
- **Keeping the last good payload.**
  - Tests: `StandingsStoreTests.swift:76` and `:86`.
  - GREEN. ST03 and ST04 are killed.
  - The time stamped on a fresh fetch is unpinned (**M5**).
- **Non-file addresses refused.**
  - Test: `StandingsStoreTests.swift:93`, which pins `load()` offline with a `data:` URL.
  - GREEN. ST06 is killed.
  - The guard in `save()` is unpinned (**M4**).
- **Only decoded fields stored.**
  - Test: `StandingsStoreTests.swift:105`.
  - GREEN. FS01 (raw bytes kept) is killed.

**P3: the combination** (`ios/EngineTests/CombineTests.swift`, header cites D-160 clause 2 and D-167 clause 3)
- **The all-present rule.**
  - Test: `:30`.
  - GREEN. SW01 (union instead of intersection) is killed.
- **Re-ranking among the common models.**
  - Test: `:38`.
  - GREEN. SW05 (raw positions) is killed.
  - **The ordering by the mean of the ranks is NOT proven: SW11 survives (B1).**
- **Competition ties.**
  - Test: `:59`.
  - GREEN. SW02 is killed.
- **The id tie-break.**
  - Test: `:48`.
  - GREEN. SW03 (id reversed) is killed.
  - **"Never by a display name" is NOT proven: SW04 survives (B2).**
- **Duplicates.**
  - Tests: `:109` (a board chosen twice) and `:115` (a model listed twice).
  - GREEN. SW06 and SW07 are killed.
- **Refusals.**
  - Tests: `:95` (an unknown board), `:103` (no board) and `:124` (an undescribed model).
  - GREEN. SW08, SW09 and SW10 are killed.
- **One board chosen, board order irrelevant, the boards named.**
  - Tests: `:69`, `:75` and `:84`.
  - GREEN. SW12 (positions dropped) is killed.

**The gates**
- **The D-126 text gate.**
  - Tests: `tests/unit/test_router_hints.py:233` (`test_the_gap_register_stays_on_the_device`), with `StandingsStore.swift` allowed by exact expressions only (`:359-365`).
  - GREEN. These mutants are killed:
    - G01, a second FileManager call in the store;
    - G02, a second `Data(contentsOf:)`;
    - G07, Combine touching the file system;
    - G14, the store building a URL.
- **client-decls.**
  - Gate: `scripts/client_decl_gate.py:123-126`, which names `StandingsStore.swift` and `FrontDoor.swift` and nothing else.
  - PASS in all 4 configurations. Two mutants were run through the real compiler gate, and both FAIL in all 4 configurations:
    - G16, `FileManager` in `Combine.swift`;
    - G17, `URLSession` in `StandingsStore.swift`.
  - A direct probe of `problems()` also refuses the file system in Combine, ContentView and EngineClient.
- **The position tripwire.**
  - Tests: `tests/unit/test_ios_client_contract.py:207` (7 spellings) and `:211`.
  - GREEN. G03 (position arithmetic in the store), G08 (new arithmetic in ContentView) and G13 (Combine's arithmetic renamed away, so its permission goes stale) are killed.
- **The sort tripwire.**
  - Test: `test_ios_client_contract.py:308`, with the permission at `:289`.
  - GREEN. G04 (a sort in the store) and G05 (a second sort in Combine on another receiver) are killed.
  - G06 survives: a second `common.sorted()` in Combine (**M7**).
- **The exact ContentView exemption.**
  - Test: `test_ios_client_contract.py:211`, with the exemption at `:190-195`.
  - GREEN. G09 (the variable renamed, so the exemption is stale) and G10 (the exempt expression appears twice) are killed.

**P4: measured and recorded** (`docs/research/m17-w4-standings-payload-2026-09-25.md`)
- Reproduced on the worktree's `advisor.db` through `TestClient` at `ebde1d6`:
  - 63 boards, 303 models and 6,955 positions;
  - 499,117 bytes raw and 36,407 gzip. The record says 499,633 raw, from `json.dumps`, which escapes non-ASCII characters; the gzip size is identical;
  - the ceiling is 8.4 times that;
  - the boot's `_egress_problems` finds no problem.
- One row of the record is dated after its own commit (**M8**).

## Red→green on reported symptoms (and phase order)
Each red commit's tree was run through `git archive` in scratch, at the red commit and at its green commit.
- **P1.** `b62f451` is red: 14 Python tests fail, `ModuleNotFoundError: app.workflows.standings`, and the route set is off by one. `ed6c954` is green: 72 passed.
- **P2.**
  - `60cf310` is red: the payload contract test fails, and the Swift test target does not compile (`FetchedStandings`, `StandingsStore` and `boards()` are missing).
  - `73fe0e8` is green: BoardsRequest 3/3 and StandingsStore 7/7.
  - The only test edits in the green commit are raw-string `\#` line continuations, with the JSON content unchanged.
- **P3.**
  - `a1b0c87` is red: the tripwire fails because the permission is stale, and the Swift build fails (`combine` and `CombineError` are missing).
  - `d020a96` is green: Combine 11/11.
  - It adds 2 tests after mutation testing (the tie test, and the "ghost" model fixture made meaningful). Neither was red first, both strengthen the suite, and both catch a mutant (SW02, SW09).
- **Review round 1.**
  - `ee312f8` is red: 13 Python tests fail, and the Swift build fails (`extra argument 'effort'`).
  - `abf284b` is green: 86 Python tests; Combine 12, BoardsRequest 5, StandingsStore 10.
  - The green commit rewrote the S1 test from `https://example.com` to a `data:` URL. The first version would have reached the network, and it never ran, because the red target did not compile. The rewrite dropped the `save()` half (**M4**). That is not a weakening to force green: on the pre-fix code, that half could not fail either.
- **Review round 2.**
  - `c9ec11b` is red: 3 tests fail (R5 twice, M7).
  - The M8 test was green at its red commit. The commit says so ("M8 is pinned by the previous commit"): the code was already right, and the test is a pin. It does catch PY07.
  - `ebde1d6` is green: 90 passed.
- **Weakened or deleted tests:** none. Every test edit in the range is an addition, a rename that follows the S2 behaviour change, or the S1 rewrite above.

## Suite result
- `make check-fast` at `ebde1d6`, clean tree: **PASS**.
  - lint, typecheck and records pass;
  - test: **1448 passed, 23 skipped**, and coverage-floor PASS (41 modules);
  - client-decls PASS: 13 files in 4 configurations;
  - swift-test PASS: **295 tests, exactly the manifest**.
- `git status` was clean before and after. Every mutated file's sha256 equals `git show HEAD:<file>` after the run:
  - `standings.py` 1c616456…
  - `main.py` a7786919…
  - `Combine.swift` 762693db…
  - `StandingsStore.swift` 556c0c66…
  - `Models.swift` 57df1eca…
  - `EngineClient.swift` b1b6847b…
  - `ContentView.swift` c549c36c…
- **Coverage on touched code**, from the same command (`pytest tests/unit -n auto --cov-branch`) on `7d7a9ac` and on `ebde1d6`:
  - `src/app/workflows/standings.py` is new, at **100 %**;
  - `src/app/adapter/main.py` went **96.73 % → 96.08 %** (**B3**);
  - the total went 91.15 % → 91.31 %.

## Fault injection (HIGH: mandatory)
Each mutant was applied in place and restored in place by the scratch harness `tester-w4/mut.py`, with the sha256 checked after every restore and `PYTHONDONTWRITEBYTECODE=1` set. One stale `main.cpython-314.pyc` was compiled from mutant PY32 by an xdist worker. Its header's size and mtime did not match the restored source, so Python would have recompiled it. I deleted it anyway.

A mutant counts as killed only when an assertion failed. For every Swift mutant, the output shows `error: -[… test…]` from XCTest, not a compile error.

**Python (32 mutants): 24 killed, 8 survived, 3 of them equivalent.**
- **Killed:** PY01-PY11, PY13, PY16, PY19, PY20, PY23-PY30 and PY32.
- **Survived.** Each was re-run against the whole unit suite (`-n auto`) and still survived:
  - **PY12:** `models` not filtered to the standing models (**M3**);
  - **PY14:** `evidence_date = min` (**M2**);
  - **PY15:** `observed_at = min` (**M2**);
  - **PY17:** LEFT JOIN on `models`. Equivalent;
  - **PY18:** a standing's effort taken from the policy. Equivalent: the filter makes the two equal;
  - **PY21:** the bound counts boards, not positions (**M1**);
  - **PY22:** the bound refuses at `>=` (**M1**);
  - **PY31:** `require_price_medians` dropped from the route. Equivalent in what a reader sees: the `sqlite3.Error` path gives the same 503. The route's non-ValueError branch is uncovered (**B3**).
- **Kill rate:** 24/29 non-equivalent, **83 %**.

**Swift (29 mutants): 23 killed, 6 survived.** Each survivor was re-run against the full `swift test` (295 tests) and still survived.
- **Killed:** SW01-03, SW05-10, SW12, ST01-04, ST06, ST08, ST09, FS01, FS03 and EC01-04.
- **Survived:**
  - **SW11:** the order is a model's best rank, not the sum (**B1**);
  - **SW04:** a tie is broken by display name (**B2**);
  - **ST05:** a fresh fetch is stamped with `Date()` instead of `now` (**M5**);
  - **ST07:** the `isFileURL` guard is removed from `save()` (**M4**; equivalent as far as egress goes);
  - **FS02:** the ceiling refuses at `<` instead of `<=` (**M6**);
  - **FS04:** the ceiling is raised to 1 GiB (**M6**).
- **Kill rate:** 23/28 non-equivalent, **82 %**.

**Gates (17 mutants): 16 killed.**
- **Killed:** G01-G05 and G07-G17. G16 and G17 ran through the real `scripts/client_decl_gate.py`.
- **Survived:** G06 (**M7**).

**Probes that close each survivor** were written in scratch only, since I may not edit tests.
- **Swift.** `tester-w4/probe/` is a SwiftPM package over a copy of the HEAD Engine sources; it uses no network. Its 3 tests pass on HEAD. Each one fails on its mutant:
  - `testTheOrderIsTheMeanRankNotTheBestRank` fails on SW11;
  - `testAnEqualSumIsBrokenByIdEvenWhenTheNamesDisagree` fails on SW04;
  - `testAFreshFetchIsStampedWithNow` fails on ST05.
- **Python.** `tester-w4/probe_py.py` passes on HEAD, and fails on each of PY12, PY14, PY21 and PY22.

**Independent real-data check.** On the worktree's `advisor.db`, each of the 12 single-source surfaces was compared with its board, using `rank.category_ranking`:
- the set of models is the same;
- there are 0 order violations: a higher score always means a smaller position, and equal scores share a position;
- the efforts differ 0 times.

`coding` is excluded: it ranks SWE-bench Verified across two sources by design.

## Mocks / contract tests
- **The engine route, seen by the phone.** The canonical stub is the existing `StubProtocol` (`ios/EngineTests/EngineClientTests.swift`), extended with `lastRequest`. No parallel stub was added. The contract is `tests/unit/test_ios_payload_contract.py:264`: it drives the real route through `TestClient` and checks the result against the Swift structs. OK.
- **External integrations:** none new in this wave.

## BLOCKING
- **B1** `ios/ModelRanking/Engine/Combine.swift:69,76-79`; `ios/EngineTests/CombineTests.swift:38-46,59-67`. **The combination's ordering rule, "orders them by the mean of those ranks" (D-167 clause 3), has no test that can fail.**
  - Replace the sum with a model's best rank (SW11: `sums[m] = min(sums[m], rank)`). All 295 Swift tests still pass.
  - Every fixture that orders 2 or more models gives the same order under both rules. In `:38`, a (1,2), b (2,3) and c (3,1) order a, c, b either way, and so do the tie fixtures.
  - The criterion's test does not assert its claimed behaviour. For the milestone's own product ordering, that is BLOCKING here (fault that stays green, HIGH tier).
  - **Fix**, verified in scratch against SW11: boards x = a, b, c and y = b, c, a. The sums give **b, a, c**; the best rank would give a, b, c.
- **B2** `ios/EngineTests/CombineTests.swift:25,53-56`; `Combine.swift:78`. **"Ties are broken by model id, never by a display name" (plan P3; D-167 clause 3) is not proven.**
  - The fixture helper sets `display: $0.uppercased()`, so display order equals id order for every model in the file. The test comment says "the id decides, whatever the names say", and the names never disagree.
  - Breaking the tie by `models[id].display` (SW04) passes all 295 Swift tests.
  - **Fix**, verified in scratch against SW04: model `a` displayed "Zeta" and model `b` displayed "Alpha", on mirrored boards. Assert `["a", "b"]`.
- **B3** `src/app/adapter/main.py:229-230, 1405-1406`, and the branch `1414->1418`. **Coverage dropped on a touched module: 96.73 % → 96.08 %**, from the same command at `7d7a9ac` and at `ebde1d6`. `permission-matrix.md` §11 lists "Coverage drop on touched module" as BLOCKING.
  - Everything the wave left uncovered is new code:
    - `_standings_problem` returns None when `open_readonly` raises (`:229-230`);
    - `/v1/boards` answers 503 when `open_readonly` raises (`:1405-1406`);
    - the route's 503 for `UnbuiltEvidenceError` or `sqlite3.Error` (the non-ValueError side of `:1414`).
  - The last of these is also why PY31 cannot be told apart.
  - **Fix:** two route tests: a database without `px_median` gives a closed 503, and an unreadable file gives a closed 503. A boot test with an unopenable artifact would also cover `:229-230`.
  - `make coverage-floor` passes. Its 60 % per-module floor is not the rule this item cites.

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `src/app/workflows/standings.py:144-146`, `src/app/adapter/main.py:240`; `tests/unit/test_board_standings.py:256`. **The egress bound's unit and edge are unpinned.**
  - The boot test sets the ceiling to 1 on an artifact with 2 boards and 6 positions. So a count of boards (PY21) still trips it, and so does `>=` (PY22).
  - Counting boards would make the bound about 110 times weaker on real data: 63 boards against a ceiling of 25,000.
  - Probe: a ceiling of 6 is accepted and a ceiling of 5 is refused. It kills both mutants.
- **M2** `standings.py:120-121`; `test_board_standings.py:154-163`. **A board's date, "the newest `run_date`, else the newest `observed_at`" (plan, Design), is unpinned.** Every row in every fixture has the same date, so `min` survives for both (PY14, PY15). Probe: two rows dated 2026-08-01 and 2026-09-18, and assert the later one.
- **M3** `standings.py:135`. **`models` holding only models that stand is unpinned (PY12).** No fixture has a priced model that stands on no board. Probe: a priced model with no score row must be absent.
- **M4** `ios/ModelRanking/Engine/StandingsStore.swift:67`. **The second review's M9, first half, is still open.**
  - The `isFileURL` guard in `save()` is unpinned (ST07). `ebde1d6` fixed only M9's header wording.
  - No egress follows today, because `Data.write(to:)` refuses a non-file URL. But the guard security S1 asked for is half pinned.
  - The review's own fix still applies: `save` to the `data:` URL, then assert that nothing was created.
- **M5** `StandingsStore.swift:86`. **The time stamped on a fresh fetch is unpinned (ST05).** Stamping `Date()` instead of `now` passes every test. Probe: `current(now:)` with a successful fetch, then `load()?.fetchedAt == now`.
- **M6** `ios/ModelRanking/Engine/Models.swift:396`, `EngineClient.swift:156`. **Only "one byte over" is tested for the phone's ceiling.**
  - Refusing at exactly the ceiling (FS02) survives.
  - So does raising it to 1 GiB (FS04). Nothing ties the constant to the measured 500 KB that its comment and D-167 cite.
- **M7** `tests/unit/test_ios_client_contract.py:289`. **The sort permission for Combine is keyed by receiver name.** A second `common.sorted()` in `Combine.swift` passes (G06). This is the same class as the second review's R4, which is carried as a risk. File it, or accept it on the record.
- **M8** `docs/research/m17-w4-standings-payload-2026-09-25.md:27`. **The row "served on 2026-09-26 (the first night with W3)" was committed in `ebde1d6` at 2026-09-25 23:37 +0300 (20:37 UTC).** A measurement cannot be dated after the commit that records it. Either the date or the label is wrong. Correct it, or say what was actually measured.

## Tests added/extended this review
- None in the repository. This seat may modify only this file.
- Scratch probes that prove the missing tests can fail (not committed):
  - `/private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/tester-w4/probe/Tests/ProbeTests/ProbeTests.swift`, for B1, B2 and M5;
  - `…/tester-w4/probe_py.py`, for M1, M2 and M3.
- Mutant specs and outputs: `…/tester-w4/{py,sw,gate}_mutants.json`, `…/tester-w4/outputs/`, `…/tester-w4/mutants.log`.
