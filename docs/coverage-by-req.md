---
record_type: register
id: coverage-by-req
status: ratified
date: 2026-08-18
---
# REQ-ID coverage trace — M9 Quality Gate (Stage 4.1)

**Scope:** every acceptance criterion in M7's signed scope (`docs/plans/m7-plan.md` §1), traced to
its implementing code and to the test(s) that would FAIL if the criterion were violated (V3C-02,
BLOCKING).

**This register replaces the M6 trace.** The M6 version is preserved in git history at the M6
closure commit and nothing in it is retracted.

**Evidence pinning.** Working tree at `194d578`. `make check` exit 0, **511 passed / 12 skipped**.
Line numbers below were DERIVED by symbol search rather than transcribed — M6's reviews caught this
author transcribing numbers that did not hold, three separate times.

**What this gate owes the reader before the table.** Every row below reads COVERED or PARTIAL, and
that is the same state in which three review seats found **thirty BLOCKING defects in W1 alone**.
Coverage means a citing test exists and was shown able to fail. It does not mean the control runs
on every path, which is the specific thing this project has been wrong about in five consecutive
milestones.

| # | REQ-ID | Verdict | Implementing code | Citing test shown able to fail |
|---|---|---|---|---|
| 1 | **REQ-ING-012** — one runnable production entry point builds the artifact | COVERED | `src/app/workflows/build.py` (`build`, `main`), `src/app/workflows/sources.py` | `test_build.py::test_build_produces_an_artifact_that_can_actually_answer`; `test_sources.py` derives the client list with `ast` so the registry cannot silently disagree with the tree |
| 2 | **REQ-ING-013** — a partial build is a failed build | COVERED | `build.py` (`_ingest_curated`, `_ingest_sources`, `_ingest_bundles`, the read-back floors, temp-then-rename) | `test_build_artifact_safety.py` — 16 tests, each verified RED against its mutant |
| 3 | **REQ-CAN-003** — medians unchanged after leaving the read path | COVERED | `rank.py::build_price_medians` called from `build.py` | Value-for-value: 72 medians and 9 recommendation shapes byte-identical against a pre-change baseline, on a read-only connection. `test_serializer_parity.py` holds the shape |
| 4 | **REQ-API-007** — no write, no full-database copy in the serving path | COVERED | `adapter/main.py` — `serving_snapshot` DELETED, `open_readonly` at the call site | `test_api_config.py::test_w017_is_closed_by_deletion_not_by_a_bounded_copy` asserts the MECHANISM: it parses the adapter and fails on any `backup()` call or `:memory:` connection |
| 5 | **REQ-API-008** — an unbuilt artifact is refused, not answered empty | COVERED | `rank.py::require_price_medians`, `main.py::_database_unusable`, the CLI's exit 2, `/v1`'s 503 | `test_unbuilt_evidence.py` (8 tests), `test_api_v1.py::test_an_unbuilt_artifact_is_refused_rather_than_answered_empty`, `test_cli_e2e.py::test_cli_an_unbuilt_artifact_exits_2_not_1` |
| 6 | **REQ-API-009** — the deployed service answers a real query with correct content | **PARTIAL** | `scripts/journey.py` | 4/4 PASS against a container and falsified two ways — **but never over a network. W-030.** |
| 7 | **W-017** — amplification removed, not bounded | COVERED | the deletion in `main.py` | Stage 4.0 re-derived it independently: a file inflated to 121 MB with the same 73 models cost **zero** additional memory |
| 8 | **W-023** — the shipped artifact serves real answers | COVERED | `advisor.db` rebuilt through `app.workflows.build` | `test_api_config.py::test_the_repositorys_own_artifact_is_checked_not_assumed`, **inverted** at W1: it used to assert the artifact was broken and went red the moment it was fixed |

## The two criteria this gate will not call covered

**REQ-API-009 is PARTIAL and the honest word for the gap is "network".** Every journey run was
against `127.0.0.1`. TLS, DNS, Fly's proxy and real latency are unexercised (**W-030**), and the
platform's own behaviour — volume permissions against a non-root uid, OOM and restart under a
256 MB VM, `force_https` — is unexercised too (**W-031**). Both were named by the Stage-4.0 seat
itself rather than discovered afterwards.

**Deferring the deploy (D-123) does not convert them into coverage.** A local container is a good
proxy for a platform and is not the platform, and this project's recurring defect is precisely the
step where a proxy gets written down as the thing itself.


---

## M9 — the refresh (REQ-REF), added at the M9 quality gate

**Scope:** every acceptance criterion in `docs/plans/m9-plan.md` §1. An independent seat reviewed
W2 and returned **BLOCKING with three findings**, all of them in rows that read COVERED at the
time — so the caveat above is not rhetorical, it is this milestone's measured experience.

| # | REQ-ID | Verdict | Implementing code | Citing test shown able to fail |
|---|---|---|---|---|
| 1 | **REQ-REF-001** — one command performs one cycle and never leaves the artifact worse | COVERED | `src/app/workflows/refresh.py` (`refresh`, `_cycle`), which CALLS `build.py` rather than reimplementing its safety | `test_refresh.py`: failed build, raising builder, unreadable candidate, a build that FAILS while leaving something readable, no candidate surviving any outcome, and a **real SIGKILL in a subprocess** with the artifact verified byte-identical |
| 2 | **REQ-REF-002** — "changed" is decided on the content that would be SERVED | COVERED | `refresh.py::serving_summary`, `_row_digest`, derived from `RankingRow`'s fields minus a measured exclusion set | `test_refresh.py`: insensitive to `observed_at` and sub-precision noise; sensitive to score, a one-cent price, a model rename, harness, effort, a surface going blind, the same evidence under a different surface, and **a freshness update** — the case an independent seat found the first version could not publish at all |
| 3 | **REQ-REF-003** — a refresh REFUSES to publish something worse (D-128) | COVERED | `refresh.py::degradations`, `EXIT_REFUSED` | `test_refresh.py`: blinded surface, 33% loss NAMED, **exactly 25%**, a pricing feed that blinds a budget, and the two non-degradations (a surface growing, scores falling) proven to publish |
| 4 | **REQ-REF-004** — every cycle leaves a durable record of what it did (D-129) | COVERED | `refresh.py::write_status`, the `record()` wrapper reached from every return AND from `except BaseException` | `test_refresh.py`: published / unchanged / failed / refused / **crashed**, the refusal naming its surface, the payload's numbers matched against the artifact, `at_iso` against `at`, and the rename's source proven not to be its destination |
| 5 | **REQ-REF-005** — runs every 12 hours; a human can find out it STOPPED | **PARTIAL — agent-side complete, one owner command from live** | `deploy/com.hcs.modelranking.refresh.plist` (`launchd`, `StartInterval`), `runner`'s refresh-status section | `test_refresh.py::test_consecutive_refusals_are_counted_and_reset`; `runner` reports cycle age, ARTIFACT age and escalates at two refusals. **The plist is not installed — that is the owner's command and deliberately not the agent's.** Until it is loaded, nothing runs every twelve hours |
| 6 | **REQ-REF-006** — the engine serves a replaced artifact without a restart | COVERED | No new code: measured before the milestone was planned and PINNED here | `test_refresh.py`: a swap under `TestClient` changes the next response, and a reader opened BEFORE the swap finishes on a coherent artifact rather than half of each |
| 7 | **REQ-REF-007** — ingestion never runs on the serving host (D-116) | **PARTIAL, and the missing half cannot be met today** | `refresh.py` imports nothing from `app.adapter` | `test_refresh.py::test_the_refresh_never_imports_the_serving_adapter` walks the AST. **The structural half is enforced; the physical half is unmeetable while the owner's Mac is both the serving host and the only host there is.** It becomes real when D-123 discharges |

**Two rows are PARTIAL and neither is a hedge.** REQ-REF-005 needs one `launchctl load` that an
agent must not run on someone's machine; REQ-REF-007 needs a second host that does not exist. Both
are stated as half-met rather than rounded up, because rounding up is how a proxy becomes the thing
itself — which the M7 note above already warns about and which this project has done before.

**Concurrency controls added at W3 and traced here** because they protect every row above:
`refresh.py::_hold_lock` (an `O_EXCL` lock, `EXIT_BUSY`, pid-liveness reclaim) and the baseline
re-read before `replace`. Cited by four tests: lock held, dead holder reclaimed, live holder
respected, and a baseline replaced mid-cycle refusing rather than overwriting.

## M13 — traced at the M13 quality gate (Stage 4.1)

**The gap before this section, stated first.** This register stopped at M9. M10, M11 and M12 each
closed with their criteria traced in their closure reports, and nothing was added here. Those rows
are not reconstructed now: a trace written three milestones late is transcription, not measurement.
The owner should decide whether to backfill them or retire this register in favour of the closure
reports.

**Evidence pinning.** a5e3c89. `make check` exit 0, 874 Python / 215 Swift.

| # | REQ-ID | Verdict | Implementing code | Citing test shown able to fail |
|---|---|---|---|---|
| 1 | **REQ-FIX-001** — Pareto dominance admits equality on one axis | COVERED | `recommend.py::_dominates`, `subscribe.py::_plan_dominates` | `test_pareto_dominance.py`: one table run against both engines; 7 of its cases failed on the pre-fix predicate |
| 2 | **REQ-FIX-002** — startup refuses an unservable database | COVERED | `main.py::_probe_database` runs a real ranking per surface | `test_startup_schema_validation.py::test_an_artifact_that_ranks_nothing_is_refused` and its positive pair |
| 3 | **REQ-FIX-003** — attribution changes the refresh fingerprint | COVERED | `refresh.py::UNHASHED_ROW_FIELDS` without `evidence_source` | `test_refresh_attribution_fingerprint.py`; `test_refresh.py`'s real cycle |
| 4 | **REQ-FIX-004** — `runner` cannot score an unrun leg as a pass | COVERED | `scripts/runner_verdict.sh` | `test_runner_accounting.py`, executing `runner`'s own wrappers |
| 5 | **REQ-UNC-001** — no order inside the engine's margin | COVERED | `Uncertainty.swift::rankRanges`; margin on `/v1/categories` (D-138) | `UncertaintyTests.testTwoModelsInsideTheMarginOfEachOtherAlwaysOverlap` (property, every shipping margin); `test_uncertainty_contract.py::test_the_served_margin_reproduces_the_engines_own_close_call_decision` |
| 6 | **REQ-UNC-002** — a count, never "confidence"; a stale second board carries its age | COVERED | `Uncertainty.swift::evidenceLine`/`evidenceBreadth`; `recommend.confidence_of` (D-139) | `EvidenceBreadthTests.testASecondScoreFromAStaleBoardCarriesItsAge`, `…NoRenderingEverCallsACoverageCountAConfidence`; `test_secondary_evidence_age.py` |
| 7 | **REQ-UNC-003** — every source dated, or named | COVERED, with a visible lag | `main.py::_evidence_dating`; terminalbench's `Run date` read | `test_uncertainty_contract.py::test_an_undated_surface_names_its_benchmark_on_the_live_route`; `test_board_run_dates.py`. **The shipping artifact predates the terminalbench fix** |
| 8 | **REQ-ASK-001** — focusable, raises a keyboard, submittable without one | **PARTIAL** | `FrontDoor.swift::canSubmit`; `ContentView` focus, send button, synchronous in-flight flag | `FrontDoorTests.SubmissionTests`; the source-contract test. **Focus verified on the simulator; the keyboard and typing were not** (W3 close, ledger L2) |
| 9 | **REQ-ASK-002** — shows what it understood; corrected in one tap | COVERED | `echoLine`, `surfaceChoices`, `SimilarityRouter` alternatives | `FrontDoorTests.EchoTests`, `AlternativeSurfaceTests`; the Change sheet seen on the simulator |
| 10 | **REQ-ASK-003** — an unmeasured question gets a ranking and the sentence | COVERED | `routingNotice`; `TieredRouter` manual fallback unmeasured | `FrontDoorTests.UnmeasuredQuestionTests`; `RouterBoundaryTests.testWithNoTierAtAllTheReaderStillGetsASurface` |
| 11 | **REQ-ASK-004** — an older answer never replaces a newer selection | COVERED | `RequestGate`, applied in `ContentView.load()` | `FrontDoorTests.RequestGateTests`; the source-contract test's three guards |
| 12 | **REQ-CMP-004** — a score says what it is out of | COVERED, per metric family | `Scores.swift::scoreText`/`figuresLine` (D-140), called by `PickRow` and `RankedRow` | `ScoresTests.ScoreFormTests`, one per metric family, each in both languages; `test_ios_client_contract.py::test_every_score_on_screen_goes_through_the_figures_line`, shown RED on three mutants of the call sites |

**One row is PARTIAL and it is not a hedge.** REQ-ASK-001's keyboard half needs a person at a
keyboard, which this environment cannot supply and the plan (§4) reserved for the owner anyway.

---

## M14 — traced at the M14 quality gate (Stage 4.1)

**Evidence pinning.** `fc7fe5b` plus the closure wave. `pytest 918 passed / 13 skipped`; Swift
`241 test(s)` from the owner's `make check` of 2026-09-20, which predates this wave's one new Swift
test. Line numbers are derived by symbol search, never transcribed (M6's lesson, three times).

**Read the verdicts literally.** COVERED means a named test fails if the criterion is violated, and
for four rows below that is only true *after* the closure seat's findings were fixed — those rows
say so, because a trace that hides how close it came is not a trace.

| # | REQ-ID | Verdict | Implementing code | Citing test shown able to fail |
|---|---|---|---|---|
| 1 | **REQ-SRC-010** — the board's licence is on record before its data is served | COVERED (as amended) | `src/app/clients/arena.py` header; the grant is dataset-level CC-BY-4.0 at D-101 | `tests/unit/test_arena_client.py::test_every_registered_arena_board_is_attributed_and_floored` — a board with no attribution fails it |
| 2 | **REQ-SRC-011** — each board under its own source id and benchmark, never defaulted | COVERED | `src/app/clients/arena.py::ARENA_BOARDS`, `src/app/workflows/ingest.py::ingest_arena` | `test_arena_client.py::test_ingest_stores_each_board_under_its_own_benchmark` (through the real ingest; kills the W2 mutant that merged `document` into `assistant`), `::test_ingest_refuses_a_source_no_board_claims` |
| 3 | **REQ-IMG-001** — the ranked population is counted and published before any threshold | COVERED | `scripts/calibrate_board.py`, `src/app/workflows/rank.py::ranked_population` | `docs/plans/m14-wave-1-close.md` — the count was zero and the wave stopped; `test_calibrate_board.py` self-check |
| 4 | **REQ-IMG-002/003** — the tenth surface and its routing | **NOT DELIVERED** | — | Dropped with the image surface when REQ-IMG-001 measured zero. No disposition existed until the closure seat found it: `docs/warnings.ledger.md` W-105, owning milestone M15 |
| 5 | **REQ-SUR-001** — the two new surfaces rank only their own board | COVERED **after the closure seat** | `src/app/workflows/categories.py`, `src/app/workflows/rank.py::category_ranking` | `tests/unit/test_categories.py::test_a_board_only_reaches_its_own_surface_through_the_ranking_query` — three boards, one shared model at three ratings. The wave-2 record cited a test that read four dataclass fields and could not fail on this (W-102) |
| 6 | **REQ-GAP-001** — every decline recorded on the device, and nothing leaves it | COVERED **after the closure seat** | `ios/ModelRanking/Engine/FrontDoor.swift::GapRegister`, `recordsGap`, `GapRegisterStore` | `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device` — now bans every network door in `ContentView.swift` as well; the seat's four-line `URLSession` mutant was re-run and dies (W-099). Bounds and eviction: `ios/EngineTests/FrontDoorTests.swift::GapRegisterTests`, `GapRegisterHardeningTests` |
| 7 | **REQ-GAP-002** — the owner reads the register, most-asked first | COVERED in code; **one half is the owner's** | `ios/ModelRanking/ContentView.swift` `gapSheet`, `GapRegister.ordered` | `FrontDoorTests.swift::GapRegisterTests`. The plan's definition of done also asks that it be read on a running app at least once: **not done**, `docs/closure-report-m14.md` §0 |
| 8 | **REQ-SCR-001** — a score out of 100 on every card and row; no metric name in front of the reader | COVERED | `ios/ModelRanking/Engine/Uncertainty.swift::scoreOutOf100`, `anchoredFact`; `Scores.swift::figuresLine` | `ios/EngineTests/ScoresTests.swift::OutOf100Tests`, `OutOf100SentenceTests`; `tests/unit/test_ios_client_contract.py::test_every_score_on_screen_goes_through_the_figures_line`. ECI stays rank-only by D-143 |
| 9 | **REQ-SCR-002** — per surface, strictly monotonic, never reorders | COVERED | the same conversion | `ScoresTests.swift::testTheConversionNeverReordersOnAnyPinnedAnchor` — all four pinned anchors, ±400 Elo at the served resolution |
| 10 | **REQ-SCR-003** — no surface's 100 comes from the current board, and a recalibration cannot move it | COVERED **after the closure seat** | `src/app/workflows/categories.py::CategorySpec.score_anchor`, `src/app/adapter/main.py` `/v1/categories` | `tests/unit/test_uncertainty_contract.py::test_the_served_anchor_does_not_follow_a_moved_floor` (the seat's surviving mutant now dies, W-107), `::test_every_elo_surface_publishes_its_pinned_score_anchor`; client-side row pins in `test_ios_client_contract.py` |
| 11 | **REQ-SCR-004** — ties are the engine's; the tie note speaks the card's scale | COVERED (as amended by D-146 clause 3) | `ios/ModelRanking/Engine/Uncertainty.swift::rankRanges`, `leaderSentence` | `ScoresTests.swift::testTheLeaderNoteSpeaksPointsWhenAnchored`, which also asserts the ranges are byte-identical before and after |
| 12 | **REQ-RUN-002 (carried)** — the 12-hour refresh runs, and can be installed from this repository | COVERED **after the closure seat** | `deploy/com.hcs.modelranking.refresh.plist`, `scripts/refresh_job.sh`, `scripts/enable_refresh.sh`, `scripts/install_refresh_wrapper.sh` | `tests/unit/test_refresh_job_install.py` — three tests pinning the plist's program, both installers' destinations and the log paths against each other (W-100) |

**Four rows read "COVERED after the closure seat", and that is the finding of this trace.** Each of
the four passed every gate in the repository while the criterion it names was unproven or, in
REQ-RUN-002's case, untrue. The gates did not get worse; the criteria got harder to prove in a lane
with no Swift compiler and no live artifact.


---

## M15 — traced at the M15 quality gate (Stage 4.1)

**Evidence pinning.** The M15-W4 tree (`8640202` plus the M15 closure commit).
`pytest 956 passed / 15 skipped` from `make check` on the owner's Mac, 2026-09-22; `swift-test PASS:
258 test(s) (floor 258)` from the same run. "Shown able to fail" names the mutant that turned the
test red, and which seat ran it.

| # | REQ-ID | Verdict | Implementing code | Citing test shown able to fail |
|---|---|---|---|---|
| 1 | **REQ-DTL-001** — one model opened from a pick or any row: score, price in both forms, tie margin; nothing computed by the client | COVERED | `ios/ModelRanking/Engine/Detail.swift::detailFacts`, `ContentView.swift::ModelDetail` | `ios/EngineTests/DetailTests.swift::DetailFactTests`; `tests/unit/test_ios_client_contract.py::test_the_detail_screen_is_reachable_and_composes_nothing_itself`, red on the W2 seat's mutant that stops the rows opening it (`docs/reviews/m15-wave-2-review.md`) |
| 2 | **REQ-DTL-002** — the metric and the engine's own number, with the board named and dated | COVERED | the same composer | `DetailTests.swift::testTheUnitTheCardHidesComesBackHere`, `::testARankOnlyMetricStillStatesItsNumberHere`, `::testAnUndatedBoardSaysItIsUndated` (W2 seat's mutants, re-run dead). **The surface's floor is not on the screen:** `/v1` does not publish it (W-112, M16) |
| 3 | **REQ-SUR-002** — three surfaces, each ranking only its own board; each reachable in a reader's own words | COVERED **after the W3 seat** for isolation; **PARTIAL** for "a reader's own words" | `src/app/workflows/categories.py`, `src/app/clients/arena.py::ARENA_BOARDS`, `ios/ModelRanking/Engine/Router.swift` | Isolation: `tests/unit/test_categories.py::test_a_board_only_reaches_its_own_surface_through_the_ranking_query`, now over every Arena surface — red on the seat's M7 (`vision` on the chat board), which passed the wave's own tree (W-117). Thresholds: `::test_the_m15_surfaces_ship_the_thresholds_their_calibration_record_states`, red on M5 and M8. Routing: `ios/EngineTests/FrontDoorTests.swift::testTheTwoNewSurfacesAreReachableByAsking` uses paraphrases of the router's own examples (W3 review m-4); held-out questions move into Swift in M16-W1 with W-118 |
| 4 | **REQ-SUR-003** — a board the engine cannot recommend from is refused, with the count on record | COVERED | `src/app/clients/arena.py::ARENA_BOARDS` (registered boards only); `docs/research/m15-board-survey-2026-09-21.md` | `tests/unit/test_arena_client.py::test_an_unregistered_board_is_refused_and_never_defaulted`; `::test_every_registered_arena_board_is_attributed_and_floored`, red on the seat's M9 (floor cut to 20) since the floors were pinned (W-117) |
| 5 | **REQ-GAP-001** (re-traced) — nothing the reader types leaves the device | COVERED **against every named shape**, not as a data flow (W-122) | every file under `ios/ModelRanking`; `EngineClient.swift` the one door | `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device`, rebuilt three times this milestone: 54 of 54 attempts die (M01–M11, M15 from the Stage 4.0 seat; N01–N11 from the W4 seat; the re-review's 27; four more); the gate at `d8cd650` caught 2 of the Stage 4.0 seat's 12 (W-121). Behavioural half: `ios/EngineTests/FrontDoorTests.swift`, backup exclusion read back from disk |
| 6 | **REQ-IMG-002/003** — the tenth surface and its routing | **NOT DELIVERED**, carried | — | Still with the image-pricing question (W-105, W-113's history). Named in `docs/plans/m16-plan.md` §1 as "not this milestone" |

**One row is PARTIAL and it is the seat's finding, not a hedge:** the router test proves the
examples' wording reaches each surface, not that a stranger's does.

## M16 — traced at the M16 quality gate (Stage 4.1)

**Evidence pinning.** `main` at `eee2faf` plus the M16 closure branch. Each row names the test that
cites the criterion and the mutant that has turned it red, with the seat that ran the mutant. The
full gate results are in `docs/closure-report-m16.md` §4.

| # | REQ-ID | Verdict | Implementing code | Citing test shown able to fail |
|---|---|---|---|---|
| 1 | **REQ-FLR-001** — `/v1/categories` publishes each surface's floor as its own field | COVERED | `src/app/adapter/main.py::categories` | `tests/unit/test_uncertainty_contract.py::test_every_surface_publishes_the_floor_it_recommends_from`, through `TestClient(adapter.app)`; RED on three mutants: the field dropped, served from `score_anchor`, and the floor moved (`docs/plans/m16-wave-1-close.md`) |
| 2 | **REQ-FLR-002** — the detail screen shows that floor, in both languages | COVERED | `ios/ModelRanking/Engine/Detail.swift::detailFacts` | `ios/EngineTests/DetailTests.swift` (floor on the card's scale, none invented, rank-only unit, Turkish screen); both doors pinned in `tests/unit/test_ios_client_contract.py`. W-112 FIXED |
| 3 | **REQ-PRC-001** — a surface whose price leaves something out says so as a code | COVERED | `src/app/workflows/categories.py::CategorySpec.price_excludes` | `tests/unit/test_uncertainty_contract.py::test_only_the_search_surfaces_say_the_search_call_is_not_in_the_price`; RED when every surface carries the code |
| 4 | **REQ-PRC-002** — every place that prints a search price says what it leaves out | COVERED | `Detail.swift::priceExclusion` | `tests/unit/test_ios_client_contract.py::test_every_place_that_prints_a_search_price_says_what_it_leaves_out`; `DetailTests`; `EngineClientTests` on a live payload. W-119 FIXED |
| 5 | **REQ-REF-008** — the engine refreshes itself once a night, in a child process, off by default, refused in production | COVERED | `src/app/adapter/nightly.py`, `main._lifespan` | `tests/unit/test_nightly_refresh.py`: window arithmetic, catch-up, a hanging child killed at the timeout, a child killed mid-publish (live artifact byte-identical); `docs/reviews/m16-wave-2-review.md` and `m16-wave-2-security.md` mutants |
| 6 | **REQ-REF-009** — a failed source carries its last good data for 30 days, then drops | COVERED | `src/app/workflows/build.py::Carry`, `refresh.py::_served_without` | `tests/unit/test_carry_forward.py`, `tests/unit/test_refresh_carry.py` through the real `refresh()` and `build.main`; three seats' mutants, the last round all RED (`docs/reviews/m16-wave-3-rereview-2.md`) |
| 7 | **REQ-ING-010** (amended by D-158) — the refresh fetches the Epoch bundle itself, as untrusted input | COVERED | `src/app/clients/epoch_bundle.py`, `refresh.py::_fetched_epoch`, `nightly.refresh_command`, `scripts/refresh_job.sh` | `tests/unit/test_epoch_bundle_fetch.py` (cycle through `refresh()`; every refusal; RED on the security seat's F1 archives); `tests/unit/test_epoch_layout.py` (the 2026-09 layout, drift to `/health`); `tests/unit/test_refresh_job_install.py` |
| 8 | **REQ-CAN-001** (superseded in part by D-157) — a name no curated rule matches is registered when it has a price and a score; two products never share an id | COVERED | `src/app/workflows/registry.py::derive_identity`, `reconcile` | `tests/unit/test_registry_derived.py` (the review's false-merge reproductions, RED on the pre-fix grammar: 13 FAIL replayed by the re-review), `tests/unit/test_registry_disclosure.py` through the real cycle |
| 9 | **REQ-CAN-002** — a variant's price or score never leaks into its parent | COVERED | `registry.py::MODEL_RULES` | `tests/unit/test_registry.py::test_variant_never_leaks_into_parent` (GPT-5 Thinking Mini, Claude Fable 5.1 added this milestone), `::test_the_fable_5_parent_keeps_its_version_guard` (RED on the review's M21) |
| 10 | **REQ-GAP-001** (re-traced) — nothing the reader types leaves the device | COVERED **against resolved declarations** (W-122 FIXED) | `scripts/client_decl_gate.py`, `make client-decls` | The gate type-checks the client and reads what the compiler bound; the W1 seats' bypass set dies on it (`docs/reviews/m16-wave-1-rereview-2.md`) |
| 11 | **REQ-RTR-005** — an unmeasured question routes to `assistant` and says so | **PARTIAL**, carried | `ios/ModelRanking/Engine/Router.swift` | `ios/EngineTests/RouterBoundaryTests.swift` floor tests hold the mechanism; the measurement found 5 of 16 ordinary questions reach a surface without saying so (W-123, now owned by M17: it waits for evidence about what people ask) |

**One row is PARTIAL, and it is a measurement, not a hedge:** row 11. Not traced here: the plan and
roster data (REQ-SUB-004, REQ-ING-009) were re-verified on 2026-09-23 (PR #4); that is data, gated by
the CI staleness steps, not a criterion with a test.
