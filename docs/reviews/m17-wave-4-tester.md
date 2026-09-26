---
record_type: review
id: m17-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-26
---
# Wave 4 Tester Review (m17)

**Reviewer:** Tester subagent, fifth seat (fresh eyes). This seat wrote none of the wave's code. It is not one of the wave's Code-Reviewers, not its security seat, and not any of the four earlier Testers.
**Independent:** yes
**Date:** 2026-09-26
**Commit range:** `7d7a9ac..aaafb5c` (the whole wave)
**Risk tier:** HIGH (`docs/plans/m17-wave-4-plan.md:11`)
**Supersedes:** the fourth Tester's BLOCKING verdict, committed in `f3d513c`. That verdict and the three before it (`b35eb3e`, `a5b85ec`, `1cff428`) stay in git history.
**Scope:** the wave **without the combination**. At the owner's ruling (2026-09-26), `Combine.swift` and `CombineTests.swift` left the wave in `6aa7aff`, filed as #61 (D-167 amendment, `docs/decisions.md:3138-3143`). This verdict tests P1 (the route), P2 (fetch, store and gates), P4 (the measurement record) and D-167 clauses 1, 2 and the file-system half of clause 4. Clause 3 is not tested here. The fourth Tester's B1 belonged to the combination and moves with it to #61.
**Model routing (HIGH, advisory):** the author is from the Claude family (`GP-Agent: claude-code/local-lane`). This reviewer is also Claude (Opus 5.5). Fallback reason: no second model family is available to this seat. Fresh context: this seat started from the role file, `practices.md`, the plan, D-167 and its amendments, the committed reviews and the diff. It has no memory of any authoring or reviewing session.
**Base-pinned policy:** `.claude/agents/Tester.md`, `.agents/rules/practices.md`, `docs/permission-matrix.md` and `.github/` are unchanged in the range (`git diff --stat 7d7a9ac..aaafb5c` on them is empty).

## Verdict
PASS-WITH-MINORS

**The fourth Tester's B2, M1 and M2 are resolved.** `aaafb5c` changes tests only (`StandingsStoreTests.swift`, `test_board_standings.py`). I re-ran each surviving mutant from that verdict with its exact spec, in place, and each is now killed by an assertion:
- **B2:** T4-ST01 (an unchanged refetch not saved) and T4-ST02 (stamped at the old stamp plus a day) are killed by `ios/EngineTests/StandingsStoreTests.swift:89` (XCTest failures at `:101` and `:103`).
- **M1:** T4-PY02 (the date counts rows the effort policy excluded) is killed by `tests/unit/test_board_standings.py:513`.
- **M2:** T4-PY03 (`10 *` the bound) is killed by `tests/unit/test_board_standings.py:489-490`.
- T4-ST03 (`<=` to `<` on the future-stamp guard) still survives. The fourth Tester already classed it as equivalent in practice, and I agree.

**Nothing load-bearing survives.** 31 new mutants on the route, the store, the client and the three gates: 29 killed, 1 equivalent in practice, 1 not equivalent (**M1**, a date rule that no ADR fixes). Every touched module keeps or gains branch coverage. `make check-fast` passes. The payload record reproduces to the byte.

**The removal left no dangling permission, manifest entry or test.** Some prose still says, in the present tense, that the phone combines the boards (**M2**).

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `aaafb5c`. Mutant ids are defined under "Fault injection".

**P1: the route** (`tests/unit/test_board_standings.py`, whose header cites D-160 and D-167)
- **Declared and additive:** `tests/unit/test_api_v1.py:541`. GREEN.
- **Positions only, never a score (D-167 clause 2):** `:119` and `:140`. GREEN. T5-PY13 (a score beside the position) is killed by `:140`.
- **Tied models share a position (competition ranking), and only exact ties do:** `:67` and `:504`. GREEN. T5-PY02 (dense ranking) and T5-PY03 (ties on rounded scores) are killed.
- **Each model's best row, effort per D-112:** `:74`, `:85`, `:288`, `:300`, `:314`, `:461` and `:493`. GREEN. T5-PY04 (the worst row), T5-PY10 (the oldest run among equal scores) and T5-PY12 (two policies, the last one wins) are killed.
- **Only rankable models (reconciled and priced):** `:107` and `:363`. GREEN. T5-PY14 (`LEFT JOIN px_median`) is killed.
- **Dated and attributed:** `:154`, `:169`, `:350`, `:454` and `:513`. GREEN. T4-PY02 is now killed.
  - T5-PY11 (the date taken only from each model's evidence row) survives: **M1**.
- **Models carry the served blend and their accessibility:** `:185`. GREEN. T5-PY09 (the blend weights swapped) is killed.
- **A query string changes nothing (D-167 clause 1):** `:227`. GREEN. T5-PY05 (a `boards=` parameter that filters the payload) is killed.
- **Bounds and refusals checked at boot:** `:245`, `:267`, `:382` and `:474`. GREEN.
  - T5-PY07 (the bound counts boards, not positions) is killed.
  - T5-PY15 (the standings refusal dropped from the boot problems) is killed.
  - T4-PY03 is now killed.
- **The closed 503 paths:** `:236`, `:331`, `:402` (3 cases), `:425` and `:436`. GREEN.
  - T5-PY06 (a `ValueError` escapes as a 500) is killed by `:331`.
  - T5-PY08 (the route skips the price-median guard) is killed by `:402[empty_medians]`.
- **The payload contract against the Swift structs:** `tests/unit/test_ios_payload_contract.py:264`. GREEN.

**P2: fetch and store**
- **The request carries nothing: no query, no other path, no header of its own:** `ios/EngineTests/EngineClientTests.swift:470` and `:491`. GREEN. T5-EC01 (a query item) and T5-EC04 (another path) are killed by `:470`.
- **An oversized or undecodable response is refused:** `EngineClientTests.swift:505` and `:518`; `StandingsStoreTests.swift:160` and `:172`. GREEN. T5-EC02 (the ceiling made strict) and T5-EC03 (the ceiling removed) are killed.
- **The last good payload is kept when a fetch fails:** `StandingsStoreTests.swift:117`. GREEN.
- **Refetched after a day and not before, and the day restarts on every refetch:** `:51`, `:65`, `:89` and `:106`. GREEN.
  - T5-ST02 (a day old still counts as fresh) is killed by `:51` and `:65`.
  - T5-ST03 (the stored standings served after a refetch) is killed by `:65`.
  - T5-ST04 (the future-stamp guard removed) is killed by `:106`.
  - T5-ST05 (stamped with the wall clock, not `now`) is killed by `:165` and `:89`.
  - T4-ST01 and T4-ST02 are now killed by `:89`.
- **The store reads only a file on the device (security S1):** `:134`. GREEN. T5-ST01 (the `isFileURL` guard dropped from `load()`) is killed. The same guard in `save()` cannot be observed offline; that is accepted and not raised again.
- **The caches directory:** the exact expression is pinned by `tests/unit/test_router_hints.py:359`. T5-ST06 (Application Support) is killed by `test_router_hints.py:233`.
- **The client-declaration gate allows the file system in `StandingsStore.swift` and nowhere new (D-167 clause 4, file-system half):**
  - T5-G03 puts `FileManager` in `Models.swift`. `make client-decls` FAILS it on its own, in all four configurations ("reaches the file system, and only these files write one"). The text gate `test_router_hints.py:233` fails it too.
  - T5-G04 puts `URLSession.shared` in `StandingsStore.swift`. `make client-decls` FAILS it ("is the network, and EngineClient.swift is the one door (D-126)"), and so does `:233`.
- **The D-126 text gate still covers the store:** T5-G05 (a second `Data(contentsOf: url)` in the store) is killed by `test_router_hints.py:233`, because each exact exemption must occur exactly once.
- **The position tripwire, its ContentView exemption, and the now-empty permission:**
  - The tripwire lives at `tests/unit/test_ios_client_contract.py:178-237`, with `POSITION_ARITHMETIC_PERMITTED = {}` at `:178`.
  - T5-G01 (`position + 1` in `Models.swift`) is killed by `:212`.
  - T5-G02 (`$0.position * 2` in the store) is killed by `:212`.
  - T5-G06 changes the exempted `ContentView.swift:787` expression. It is killed by `:212`, whose exemption must match exactly once.
  - #60 (the tripwires match names) is accepted and not raised again.

**P4: measured and recorded** (`docs/research/m17-w4-standings-payload-2026-09-25.md:21-38`)
- I ran `board_standings` from a `git archive` of HEAD's `src` on the worktree's `advisor.db`. It gives 63 boards, 303 models and 6,955 positions.
- With `api_version`, serialised by the record's method, that is **499,633 bytes raw and 36,407 gzip**, exactly the record's figures.
- The smallest boards are 18 (`epoch_deepswe_external`), 27 and 28, and the largest 185, as recorded.
- No key contains "score". Every position is an integer. Five boards have no `evidence_date`, which matches `test_board_standings.py:455`'s docstring.
- The record's §2 replay of the combination rule is now marked as a replay of the rule, not of shipped code (`:15-18`). The replay's correctness belongs to #61.

**D-167 clause 3:** out of scope (#61). No code implements it on the branch, and the tripwire permits no file to do position arithmetic.

## Red→green on reported symptoms
- **`aaafb5c` is tests only.** `git show --stat` lists `StandingsStoreTests.swift` and `test_board_standings.py` only.
- **Each added test's red is the fourth Tester's mutant.** I re-applied T4-ST01, T4-ST02, T4-PY02 and T4-PY03, and each goes RED on its new test (see "Fault injection").
- **Weakened or deleted tests across the whole range, compared with `7d7a9ac`:** the only removed test line is the old route set at `test_api_v1.py:539`, replaced by a superset.
  - `CombineTests.swift` was added and then removed inside the range, with the code it tested, by the owner's ruling (`6aa7aff`).
  - Its 16 manifest entries and the `("Combine.swift", "common")` sorting permission left with it.
  - No test of the surviving code was weakened.

## Suite result
- **`make check-fast` at `aaafb5c`, clean tree: PASS in 41.3 s** (`tester5-w4/check-fast.log`).
  - lint, typecheck and records pass.
  - test: **1462 passed, 23 skipped**, and coverage-floor PASS (41 modules, floor 60 %).
  - client-decls: PASS.
  - swift-test: **287 tests, exactly the ones named in `ios/EngineTests/test-manifest.txt`**. That is 302, less the 16 combination tests, plus `:89`.
- **Coverage on touched code.** Branch coverage from `pytest tests/unit -n auto --cov=src --cov-branch`, lines and branches combined.
  - HEAD is the worktree. The base is a `git archive` of `7d7a9ac` in scratch, with the same `advisor.db` copied in, so no artifact test skips at either end.
  - `src/app/adapter/main.py`: 96.73 % → **97.06 %**. Its one new uncovered line, `:521`, is the pre-existing ranking-rows refusal moved into `_egress_problems`. It was also uncovered at base (`:541` there).
  - `src/app/workflows/standings.py`: new, **100 %**, with no missing line or branch.
  - `src/app/workflows/rank.py`: 93.67 % → 97.47 %.
  - **No module dropped** (a per-file comparison across all of `src`). Total: 91.15 % → 91.44 %.
- **Clean-up.**
  - `git status` is clean.
  - All 218 tracked files under `src tests ios scripts` match the pre-run sha256 baseline (`tester5-w4/sha-baseline.txt`).
  - The set of `__pycache__` directories and `.pyc` files equals the pre-run list. Two existing `.pyc` files were rewritten despite `PYTHONDONTWRITEBYTECODE=1`: `adapter/__pycache__/main` and `workflows/__pycache__/standings`. I deleted both.

## Fault injection (HIGH: mandatory)
- **Harness.** `tester5-w4/mut5.py` is adapted from the fourth Tester's. For each mutant it:
  1. makes exact byte edits in place, each of which must match exactly once;
  2. runs the command;
  3. restores in place;
  4. asserts that the sha256 equals the pre-edit value.

  All 38 restores matched (`tester5-w4/mutants.log`), and the tree's final sha256 matches the baseline. `PYTHONDONTWRITEBYTECODE=1` was set.
- **Commands.**
  - Python mutants ran against the whole unit suite (`-n auto`).
  - Swift mutants ran against `StandingsStoreTests|BoardsRequestTests` (19 tests). Every Swift kill is an XCTest `error: -[…]` assertion, never a compile error.
  - Gate mutants ran against `test_ios_client_contract.py` and `test_router_hints.py`. T5-G03 and T5-G04 were run again against `make client-decls` alone.
- **Ids.** `T4-` is one of the fourth Tester's survivors, re-run. `T5-` is a new mutant from this seat.

**Re-runs (5):**
- **Killed (4):** T4-ST01, T4-ST02, T4-PY02 and T4-PY03.
- **Survived, equivalent in practice:** T4-ST03, as the fourth Tester classed it.

**New Python mutants (15): 13 killed, 2 survived.**
- **Killed:** T5-PY02 to T5-PY10, and T5-PY12 to T5-PY15.
- **Survived, not equivalent:** **T5-PY11**. A board's date is taken only from each model's evidence row, not from every row that stands on the board. That is **M1**.
- **Survived, equivalent in practice, not a finding:** T5-PY01. `observed_at` also counts rows the effort policy excluded.
  - One build run stamps every row it writes with one `RunContext.observed_at` (`src/app/workflows/build.py:478`).
  - On `advisor.db`, all five DeepSWE efforts carry the same `observed_at`.

**New Swift mutants (10): 10 killed.** T5-ST01 to T5-ST06, and T5-EC01 to T5-EC04.

**New gate mutants (6): 6 killed.** T5-G01 to T5-G06. T5-G03 and T5-G04 are also killed by `client-decls` alone.

**Kill rates, non-equivalent mutants, re-runs included:**
- Python: 17 of 18, **94 %**;
- Swift: 12 of 12, **100 %**;
- gates: 6 of 6.

## Mocks / contract tests
- **The engine route, seen by the phone.**
  - The one canonical stub is `StubProtocol` in `ios/EngineTests/EngineClientTests.swift`. `BoardsRequestTests` uses it, and no parallel stub was added.
  - The contract is `tests/unit/test_ios_payload_contract.py:264`. It drives the real route through `TestClient` into the Swift structs.
  - OK.
- **External integrations:** none new in this wave.

## The removal of the combination: what it left
- **Code, tests and permissions: nothing dangling.**
  - `grep -rn 'Combine\.swift|CombineTests|combine(|CombineError'` over `src scripts ios tests` finds only prose. The `"Combine"` at `scripts/client_decl_gate.py:78` is Apple's framework on the import allowlist, and it predates the wave.
  - `POSITION_ARITHMETIC_PERMITTED` is empty, and T5-G01 and T5-G02 show that the tripwire still fires with the permission empty.
  - The `SORTING_PERMITTED` entry is gone.
  - The manifest has no `CombineTests` entry, and swift-test confirms the manifest matches exactly.
- **D-167:** its amendment (`docs/decisions.md:3138-3143`) records that clause 3 and the arithmetic half of clause 4 left the wave. The ADR's own clause 4 bullet (`:3110`) still names `Combine.swift`, which is correct for an append-only record.
- **The earlier review verdicts** (`m17-wave-4-review.md`, `m17-wave-4-security.md`) still list `Combine.swift` in their scope. They are dated records of what they reviewed, not claims about what ships, so this is not a finding.
- **Prose that still says the combination ships:** **M2**.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `src/app/workflows/standings.py:114-120`; `tests/unit/test_board_standings.py:350-360`. **What a board's date is taken from is unpinned. It could be the newest row standing on the board, or only each model's evidence row.**
  1. **The mutant, T5-PY11.** `kept = list(evidence)` dates a board from each model's evidence row alone. All 1,453 unit tests pass. At `:350` both rows have the same score, so the newest run is also the evidence row.
  2. **Effect on `advisor.db`.** Three of 63 boards change date:
     1. `swebench`: 2026-02-26 → 2026-02-19;
     2. `epoch_frontiermath`: 2026-09-18 → 2026-09-16;
     3. `epoch_terminalbench`: 2026-05-14 → 2026-04-23.
  3. **Why MINOR.** The plan (`m17-wave-4-plan.md:56`, "its date: the newest `run_date`") matches the code, but no ADR clause fixes which rows count. It is a disclosure date and does not change any position.
  4. **Probe, verified in scratch** (`tester5-w4/probe_m1.py`). It passes on HEAD's `src` and fails on T5-PY11:
     1. model `a` has a best score of 90, run on 2026-01-01, and a lower score of 50, run on 2026-09-01;
     2. assert `evidence_date == "2026-09-01"`.
- **M2** Prose that still says the phone combines the boards, although the combination left the wave (#61):
  1. **Code and tests:**
     1. `src/app/workflows/standings.py:1`: "what the phone combines on the device";
     2. `src/app/adapter/main.py:120-121` ("combines on the device") and `:1394` ("for the phone to combine on the device");
     3. `src/app/adapter/main.py:244`, the boot refusal the operator reads: "the phone combines what it receives, and a short board would change every list it joins";
     4. `ios/ModelRanking/Engine/StandingsStore.swift:76`: "The standings to combine now";
     5. `tests/unit/test_board_standings.py:3`: "The phone combines boards on the device";
     6. `tests/unit/test_ios_client_contract.py:214`: "a second combination".
  2. **The plan, which is deleted before merge:** `docs/plans/m17-wave-4-plan.md`
     1. `:8` and `:13-14`: the title and Goal;
     2. `:78-86`: the Design's `Combine.swift`;
     3. `:124`: "The arithmetic gate permits `Combine.swift`";
     4. `:126`: P4's "A combination on real boards";
     5. `:132`: "Two gate permissions widen (… arithmetic)".
  3. **Why MINOR.** It changes no behaviour and no gate. But a reader of the route, the store or the boot refusal is told a consumer exists that does not ship.
  4. **Fix.** Say "for the combination D-160 provides (#61)", or use the future tense. Mark the plan's stale lines the way `:115` already is.

## Tests added/extended this review
- None in the repository. This seat may modify only this file.
- Scratch, not committed. All paths are under `/private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/tester5-w4/`:
  - `probe_m1.py`: M1's probe. It passes on `tree-head/src` and fails on `tree-mut/src` (T5-PY11).
  - `py11_real.py`: T5-PY11's effect on the real boards.
  - `p4_measure.py`: the P4 figures, from `tree-head/src` (a `git archive` of HEAD).
  - `mut5.py`, `rerun_specs.json`, `new_specs.json`, `outputs/`, `mutants.log`, `rerun.log` and `new.log`: the mutants.
  - `cov-base.json` and `cov-head.json`: coverage, with the base from `tree-base/`.
  - `check-fast.log`, `sha-baseline.txt`, `pycache-before.txt` and `pycache-after.txt`.
