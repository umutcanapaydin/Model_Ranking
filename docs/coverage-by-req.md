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
