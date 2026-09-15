---
record_type: review
id: m13-wave-2-tester
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W2 — Tester seat (fault injection, V3C-72)

**Reviewer:** Tester seat. This separate session did not author any of the wave's code.
**Date:** 2026-09-15
**Subject:** the frozen diff `m13-w2.diff`: 1279 lines, 13 files, 3 of them new. It was applied to `HEAD` 3440abe.
**Risk tier:** HIGH, so V3C-72 applies in full.
**Policy source (V4C-06):** `subagent-profiles/Tester.md`, `AGENTS.md` and the format example `docs/reviews/m13-wave-1-tester.md`, all read with `git show HEAD:`. The seat read no policy from the diff.
**Cross-model routing (V4C-03):** author family `not stated to this seat` / reviewer family `Claude (Opus 5)` / fallback: no second family was available in this session. **Fresh-context assertion:** this seat received only the diff and the task. It has none of the authoring session's context.

**Provenance.** The repository was read-only for this seat. Every mutation was made in a private copy under the session scratchpad: `git archive HEAD`, then `git apply` of the frozen diff. A second copy, used only for probe tests, was built the same way. The seat's only write to the repository is this file. At the end, `git status` in the repository matched its state at the start.

## Verdict: PASS WITH FINDINGS

Every criterion has a citing test that enters through the live entry point, and every citing test goes RED when its behaviour is broken. **Seven of 36 mutants stayed GREEN.** One is equivalent (S1). The other six are findings, and one of them is MAJOR: removing a guard on the REQ-UNC-002 evidence line prints a false sentence on the production path, and no test notices. Under the Tester profile ("write the missing test THIS wave (mandatory)") and `AGENTS.md` §3 ("stay-green fault with no test" is escalate-now), the four tests named below must land before the wave closes. This seat cannot add them. For three of the four, the seat ran the named test against its mutant in the probe copy and watched it go RED.

## Baseline

| What | Result |
|---|---|
| Python, patched copy, `pytest tests/unit` | **855 passed / 7 skipped** |
| Python, unpatched HEAD copy | 843 passed / **1 failed** / 7 skipped. The failure is `test_rosters.py::test_stale_unselected_roster_link_is_not_disclosed`; see the rosters trials below. |
| Swift, patched copy, `swift test` | **163 tests, 0 failures** (132 at HEAD; the wave adds 31) |
| Test counts reconcile | Python 851 → 862 collected, exactly the 11 new tests in `test_uncertainty_contract.py`. Swift +31, exactly `UncertaintyTests.swift`. |
| Coverage on touched modules | `adapter/main.py` 96%, `workflows/recommend.py` 95%. The only uncovered lines in the wave's new code are `main.py:1154-1155` (mutant P3b). |
| Test integrity (V3C-86) | No test was deleted, skipped or xfailed. The one removed `assert` (`test_secondary_evidence_age.py`) is the same assertion, reformatted after the rename. |

**Environment note: not a wave defect, but it cost the seat a false start.** `git archive` does not export the gitignored `advisor.db`. Without it, both copies fail 41 tests with 4 errors, all `KeyError: 'answers'` in `test_why_facts.py` and `test_budgets_endpoint.py`, plus `FileNotFoundError` in `test_unavailable_after_boot.py`. The seat made a read-only copy of the artifact into each private tree, after which both were green as above. `pyproject.toml`'s `pythonpath = ["src"]` is relative, and `app.__file__` resolved inside the copy.

## Trial table

Every trial had the same five-step shape, logged as one atomic sequence by the harness:
1. Record the pre-injection md5.
2. Apply one exact string replacement (occurrence count asserted as 1).
3. Run the suite. Swift mutants ran **both** `swift test` and the Python suite, because Python tests read the Swift sources. ContentView mutants ran Python only, because `ios/Package.swift` does not compile `ContentView.swift`.
4. Revert in place by the inverse replacement.
5. Compare the md5 with step 1.

A final md5 of all five mutated files matched the pre-injection values.

### Swift: `ios/ModelRanking/Engine/Uncertainty.swift`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| S1 | `tieBands`: `<=` → `<`, tolerance kept (:72) | RED | **none: GREEN** (equivalent; see below) | True |
| S1b | `<=` → `<` and the tolerance dropped | RED | `testAGapExactlyAtTheMarginIsATieBecauseTheEngineSaysSo` | True |
| S2 | tolerance dropped: `<= margin` (:72) | RED | **none: GREEN** | True |
| S3 | chaining: anchored on the previous row, not the band's first row | RED | 6: `testRowsWithinTheMarginOfTheLeaderShareItsBand`, `testTheNextBandIsAnchoredAtTheFirstRowOutsideTheLast`, `testAModelAloneInItsBandKeepsItsPosition`, `testShortLabelsForTheRankingList`, `testBandsOnEachMetricFamilyWithTheMarginsTheEngineShips`, `testTheRankLabelIsTurkishOnATurkishScreen` | True |
| S4 | nil-margin fallback returns one band | RED | `testNoMarginMeansTodaysStrictOrderNotOneBigBand`, `testAMarginThatIsNotAUsableNumberIsTreatedAsNone` | True |
| S5 | `rankLabel`: a shared band prints `#` (:92) | RED | `testEveryRowInABandCarriesTheSameRankAndNoneClaimsAnOrder`, `testAModelAloneInItsBandKeepsItsPosition`, `testTheRankLabelIsTurkishOnATurkishScreen` | True |
| S5b | `shortRankLabel`: a shared band prints `#` | RED | `testShortLabelsForTheRankingList` | True |
| S6a | `rankLabel`: a lower shared band inherits the leader's rank | RED | `testAModelAloneInItsBandKeepsItsPosition` | True |
| S6b | `shortRankLabel`: a lower shared band inherits the leader's rank | RED | `testShortLabelsForTheRankingList` | True |
| S6c | `TieBand.rank` is always 1 | RED | `testAModelAloneInItsBandKeepsItsPosition`, `testShortLabelsForTheRankingList`, `testTheRankLabelIsTurkishOnATurkishScreen` | True |
| S7 | `leaderBandSentence` emitted for a band of 1 (`top.isShared` removed) | RED | `testNothingIsSaidWhenTheLeaderStandsAlone` | True |
| S15 | `leaderBandSentence` counts bands, not rows | RED | `testTheLeadersBandIsStatedOncePerRanking` | True |
| S8 | `evidenceBreadth`: "High" maps to 1 (:167) | RED | `testTwoCurrentBenchmarksStateTheOlderOnesAge`, `testAPayloadThatContradictsItselfIsNotRendered` | True |
| S9 | the secondary age is dropped entirely (`age = nil`) | RED | `testASecondScoreFromAStaleBoardCarriesItsAge`, `testTheAgeSurvivesTheTurkishScreen`, `testTwoCurrentBenchmarksStateTheOlderOnesAge` | True |
| S9b | the stale-secondary age is omitted from the English sentence | RED | `testASecondScoreFromAStaleBoardCarriesItsAge` | True |
| S9c | the counted secondary's age is omitted | RED | `testTwoCurrentBenchmarksStateTheOlderOnesAge` | True |
| S10 | the `label()` guard is bypassed | RED | `testABenchmarkNameThatIsASentenceIsNotInterpolated` | True |
| S11 | a negative age is printed (range check removed) | RED | `testAnAgeThatCannotBeADayCountIsNotPrintedAsOne` | True |
| S12 | the "High"-without-a-second-score guard is removed | RED | `testAPayloadThatContradictsItselfIsNotRendered` | True |
| S14 | the `secondaryScore != nil` guard is removed (:187) | RED | **none: GREEN** | True |

### Server: `src/app/adapter/main.py`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| P1 | `close_call_margin` serves `spec.value_window` | RED | `test_the_served_margin_reproduces_the_engines_own_close_call_decision[outside]`, `test_every_advertised_surface_publishes_its_margin_on_its_own_scale` | True |
| P2a | undated board: age `0` instead of `null`, inside `_secondary_ages` | RED | `test_an_undated_second_board_publishes_no_age` | True |
| P2b | age `0` instead of `null`, at the route | RED | `test_an_undated_second_board_publishes_no_age`, `test_the_published_age_is_the_one_that_decided_the_count`, `test_discovery_answers_without_an_artifact_and_says_the_age_is_unknown[unset/missing/not-sqlite]` | True |
| P3a | `_secondary_ages` re-raises on a bad artifact (query `except`) | RED | `test_discovery_answers_without_an_artifact_and_says_the_age_is_unknown[not-sqlite]` | True |
| P3b | `_secondary_ages` re-raises on a bad artifact (open `except`, :1154-1155) | RED | **none: GREEN** | True |
| P4a | `_evidence_dating` drops the benchmark name (undated branch) | RED | `test_an_undated_surface_names_its_benchmark_on_the_live_route` | True |
| P4b | `_evidence_dating` drops the benchmark name (mixed branch) | RED | `test_a_mixed_answer_names_its_benchmark_too` | True |
| P4c | the call site passes `spec.title` instead of the benchmark | RED | `test_an_undated_surface_names_its_benchmark_on_the_live_route` | True |
| P5 | `close_call_margin` leaks into the `/v1/recommendations` answer | RED | `test_the_recommendations_route_did_not_gain_a_field`, `test_api_config.py::test_the_public_payload_carries_only_declared_fields`, `test_api_v1.py::test_coding_returns_both_surfaces_and_nothing_ranks_them` | True |
| P6 | the age is inherited from a neighbour surface (`ages.get("coding")`) | RED | `test_the_published_age_is_the_one_that_decided_the_count` | True |
| P7 | `secondary_benchmark` serves the primary | RED | `test_an_undated_second_board_publishes_no_age`, `test_the_published_age_is_the_one_that_decided_the_count` | True |

### The `test_rosters.py` fixture clock pin: `src/app/workflows/subscribe.py::_stale_notice`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| R1 | age EVERY candidate roster link of every ranked plan (early return bypassed) | RED | `test_stale_unselected_roster_link_is_not_disclosed` | True |
| R2 | age every candidate link, keeping the "no selected roster row" early return | RED | `test_stale_unselected_roster_link_is_not_disclosed` | True |

**Answer to the question set:** yes. After the pin, the test discriminates the property its docstring claims, "staleness follows the selected evidence row, not every candidate link", in both mutant shapes. Before the pin it could not. On the unpatched HEAD copy the test is already RED on 2026-09-15: the unpinned `RunContext()` stamps the wall clock, the fixture's `last_verified: 2026-08-15` becomes 31 days old, and the price-staleness notice fires. So the test was failing for a reason unrelated to its claim, and a failing test discriminates nothing. The pin (`test_rosters.py:225`) is a genuine red→green: RED at HEAD, GREEN with the wave. Pinning did not weaken the assertion. The roster link is still dated `2026-05-01`, 107 days before the pinned anchor.

### ContentView wiring: `ios/ModelRanking/ContentView.swift`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| W1 | bands computed with `margin: nil` (:152) | RED | **none: GREEN** | True |
| W2 | `secondaryAgeDays: nil` passed to `PickRow` (:166) | RED | **none: GREEN** | True |
| W3 | the evidence line is not rendered (:668) | RED | **none: GREEN** | True |

## Kill rate

**29 of 36 killed (81%).** Excluding S1, which is equivalent: **29 of 35 (83%).** By area:

| Area | Killed |
|---|---|
| Engine Swift | 17 of 20 |
| Server | 10 of 11 |
| Rosters | 2 of 2 |
| ContentView wiring | 0 of 3 |

## Surviving mutants and the test each needs

| Mutant | Severity | Where | Finding | Test that should exist | Probe |
|---|---|---|---|---|---|
| **S14** | **MAJOR** | `Uncertainty.swift:187` | The `secondaryScore != nil` guard is load-bearing on the production path and nothing pins it. `ContentView.swift:165-166` passes the *surface's* second board and age to *every* `PickRow`, and most coding picks have no Aider score. Without the guard, such a pick reads *"Measured on 1 benchmark (run 2026-02-17). Aider polyglot also scored it, but last ran 332 days ago, so it is not counted."* That is a false claim about the evidence, in the sentence REQ-UNC-002 exists to make honest. The one test that passes `secondaryScore: nil` with a board named (`testNoRenderingEverCallsACoverageCountAConfidence`) asserts only the absence of "confiden". | `testASecondBoardThatDidNotScoreThePickIsNotMentioned`: `evidenceBreadth(verdict: "Medium", secondaryScore: nil, secondaryBenchmark: "Aider polyglot", secondaryAgeDays: 332, evidenceDate: "2026-02-17", .english) == "Measured on 1 benchmark (run 2026-02-17)."` | **RED against S14, GREEN on the wave's code** |
| **S2** | MINOR | `Uncertainty.swift:40,72`; `UncertaintyTests.swift:31-33` | `bandTolerance` is never exercised. The test built to pin it rests on a false premise: its comment says `94.4 - 89.4` is `5.000000000000009` in a Double, but it is exactly `5.0`. So the test pins `<=` (it kills S1b) and not the tolerance. A comment asserting the opposite of the arithmetic is the recurring defect this project records. | `tieBands([55.2, 54.4], margin: 0.8)` returns one band. That gap is `0.8000000000000043` in a Double, at `computer-use`'s shipping margin. Correct the comment in the same change. | **RED against S2, GREEN on the wave's code** |
| **P3b** | MINOR | `main.py:1153-1155` | D-138 states that discovery "still answers with no artifact at all". That is proven for an unset path, a missing path and a non-SQLite file, all of which land on the *query* `except`. The *open* `except` is uncovered (coverage confirms it), and making it re-raise turns `/v1/categories` into a 500 for an artifact that exists but cannot be opened, with the suite green. | `test_discovery_answers_when_the_artifact_cannot_be_opened`: a real file on `MODEL_RANKING_DB`, then either `monkeypatch.setattr(adapter, "open_readonly", <raises sqlite3.OperationalError>)` or `chmod 0`. Asserts 200, all nine surfaces, and every `secondary_age_days` null. | **RED against P3b (both variants), GREEN on the wave's code** |
| **W1-W3** | MINOR | `ContentView.swift:152,166,668` | The view's calls into the Engine are unexecuted (`ios/Package.swift` compiles only `Engine/`, by design and by statement) and no source contract pins them. The view could band with no margin, drop the age, or never render the evidence line, and both suites would stay green. This is W1's BLOCKING-1 shape, where the library was proven and the instrument was not, held to MINOR here because the Engine function is the agreed entry point for Swift and the gap is declared in `Package.swift`. | A source-contract test in `tests/unit/test_ios_client_contract.py`, the file that already reads `ContentView.swift` (`:105`). It asserts that the executable statements, not comments, pass `info?.closeCallMargin` to both `tieBands` and `leaderBandSentence`, pass `info?.secondaryAgeDays` / `info?.secondaryBenchmark` to `PickRow`, and render `Text(evidenceText)`. | Not probed |
| S1 | none | `Uncertainty.swift:72` | Equivalent. With the tolerance in place, `<` and `<=` differ only at a gap of exactly `margin + 1e-9`, which a one-decimal payload (D-109) cannot produce. | none | n/a |

## Per-criterion citing-test check (V3C-02)

| Criterion | Citing test, entering through the live entry point | Kills | Verdict |
|---|---|---|---|
| **REQ-UNC-001** (tie bands, `=1 of 50`, leader's band stated once) | **Server:** `test_uncertainty_contract.py:56` goes through the FastAPI route `GET /v1/categories` and `GET /v1/recommendations`, and checks the served margin against the engine's own `close_call` decision in both directions. `:82` does the same for all nine surfaces. **Swift:** `UncertaintyTests.swift` `TieBandTests` / `LeaderBandSentenceTests` call the public `tieBands`, `rankLabel`, `shortRankLabel` and `leaderBandSentence`, and `ContentView.swift` calls exactly these (`:151-156`, `:239`, `:634`, `:758`). | P1, S1b, S3-S7, S15 | **GREEN, genuine.** Two gaps: the tolerance (S2) and the view wiring (W1). "Stated once per ranking" is a view property that no test can reach. By reading: `Text(bandNote)` renders once on the home screen (`:171`) and once in the full list's header (`:727`), and `rankingPreview` only forwards it. |
| **REQ-UNC-002** (a count of benchmarks, never "confidence"; a >180-day second board carries its age) | **Server:** `:89` and `:129` go through `GET /v1/categories`. `:89` asserts the served age equals `recommend.secondary_age_days`, which is 317 on the fixture. **Swift:** `EvidenceBreadthTests` call the public `evidenceBreadth`, which `PickRow.evidenceText` calls (`ContentView.swift:614`). `:218` covers "never confidence" over every branch in both languages. The fallback, `confidence_basis`, is "one/two independent benchmark(s) (…)" (`recommend.py:269-274`) and never says "confidence". | P2a, P2b, P6, P7, S8-S12 | **GREEN, with the MAJOR gap S14** (a false sentence on the live path) and W2/W3. |
| **REQ-UNC-003** (an undated benchmark is named) | `test_uncertainty_contract.py:160` goes through `GET /v1/recommendations?task=agentic-coding` and asserts the note starts `"DeepSWE publishes no evaluation dates"`. `:174` covers the mixed branch directly. `test_board_run_dates.py` covers the terminalbench half. On the client, `classifyDisclosures` always renders a non-nil `datingNote` (`Router.swift:623-624`), so the named note reaches the screen, and `testAnUndatedSecondBoardSaysItCannotBeAged` names the undated second board. | P4a, P4b, P4c | **GREEN, genuine.** |

**D-138's side claim, "`/v1/recommendations` is byte-identical"**, is asserted by `:208` and by two pre-existing contract tests, all three of which kill P5.

## Outside this seat's scope, noted for the Code-Reviewer and the owner

The diff also edits `docs/closure-report-m12.md` to say the M12 closure report was **"SIGNED by the owner on 2026-09-15"**, quoting the owner. This seat cannot verify an owner signature that arrives inside an agent-authored wave diff, and it is unrelated to REQ-UNC-001..003. It does not attempt to change this seat's policy, so it is not an injection finding. It is recorded so that the owner, not the diff, confirms it.
