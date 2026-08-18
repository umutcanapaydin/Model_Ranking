---
record_type: register
id: coverage-by-req
status: ratified
date: 2026-08-18
---
# REQ-ID coverage trace — M7 Quality Gate (Stage 4.1)

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
