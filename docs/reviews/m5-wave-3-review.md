# Wave 3 Code Review (m5)

**Reviewer:** Code-Reviewer subagent (fresh eyes — did not author W3)

**Date:** 2026-08-16

**Commit range:** `de7cb0e..62a9166`; also reviewed the current documentation-only gate repair

**Source:** A — protected-base `subagent-profiles/Code-Reviewer.md`; no Stage-1 override declared

**Risk tier:** HIGH (new board ingestion; `docs/plans/m5-plan.md:207-209`)

## Verdict

**PASS**

The signed two-category decision is applied through the existing D-105 mechanism. DeepSWE is a
local-only, separately attributable source; its release dates never become evidence dates; all 49
usable rows retain harness and effort identity; and the selected `high` evidence produces the
published 5/10 coding, 6/10 agentic-coding, and 6/10 union. No production, test, K.8, or scope
blocker remains.

Two gate failures observed during review were closed before this verdict:

- `.language-allow` now gives reasoned exemptions for exact Turkish product-output assertions and
  the append-only W2 blocker evidence. Repository and install record checks now pass.
- `docs/reviews/m5-w3-board-application.md` was reflowed to remove three trailing hard-break
  spaces. `git diff --check de7cb0e` now passes.

## Findings

### BLOCKING

None.

### MINOR

None in the reviewed W3 range. The pre-existing documentation drift listed under K.9 does not
alter a runtime contract or the signed W3 measurements.

### PASS evidence

- `src/app/clients/deepswe.py:39-66` is a concrete `RawSource` implementation with a fixed local
  filename and fixed provenance URL. It imports no HTTP client and has no network branch.
- `src/app/clients/deepswe.py:95-152` preserves score scale, harness, source, and effort. Unknown
  effort is skipped/countable, conflicts are counted, duplicates deterministic, and non-finite or
  out-of-range scores cannot enter the database.
- `src/app/clients/deepswe.py:100-101,130-140` always sets `run_date=None`; model release date is
  never promoted to evaluation time.
- `src/app/clients/epoch.py:35-48` makes verification-clock errors source-specific without changing
  the Epoch parser contract.
- `src/app/workflows/ingest.py:35-45,194-217` publishes unknown/conflict counts and the independent
  source clock, then uses the existing atomic score replacement boundary.
- `tests/unit/test_deepswe_workflow.py:48-264` covers local acquisition, clock/provenance,
  accounting, date isolation, source-isolated reruns, real reconciliation, and live coverage JSON.
- `docs/reviews/m5-w3-board-application.md:13-64` matches the independent board replay.
- No dependency, build, CI, schema, migration, decision, hook, or destructive-operation change is
  present.

## File-by-file review

| File | Result | Evidence |
|---|---|---|
| `docs/reviews/m5-w3-board-application.md` | PASS | Independently reproduced facts and acceptance path |
| `src/app/clients/deepswe.py` | PASS | Local client, strict parser, protocol conformance |
| `src/app/clients/epoch.py` | PASS | Source-aware clock error only; Epoch behavior preserved |
| `src/app/workflows/ingest.py` | PASS | Additive report fields and atomic DeepSWE workflow |
| `src/app/workflows/recommend.py` | PASS | CLI usage now lists the data-owned category; behavior unchanged |
| `tests/unit/test_deepswe_workflow.py` | PASS | Six W3 tests including real bundle and live JSON boundary |
| `.language-allow` fix delta | PASS | Narrow, reasoned product/audit exemptions only |

## Acceptance criteria

- **REQ-ING-010:** `deepswe.py:39-66` and `test_deepswe_workflow.py:48-70,114-123` cover the
  allowlisted local client, no URL fallback, canonical clock, and per-source failures.
- **REQ-ING-011b:** `test_deepswe_workflow.py:73-111,159-264` proves release-date isolation,
  selected-plan 0/0/6/4 health, source telemetry, and the live JSON boundary. Generic four-state
  and 60-day semantics remain locked by `test_coverage.py:230-294`.
- **REQ-CAN-005:** `test_deepswe_workflow.py:73-111,176-197` covers stored effort,
  unknown/conflict reporting, and the real distribution. `test_effort.py:389-398` locks the full
  owner-bundle shape.
- **REQ-REC-011:** `test_effort.py:245-300` requires `high`, same-harness/source higher evidence,
  and exact no-higher disclosure. W3's real path requires every selected plan row to be high and
  DeepSWE-sourced.
- **REQ-SUB-007:** `test_m5_board_measurement.py:43-91,127-160`,
  `test_epoch_workflow.py:128-160`, and `test_deepswe_workflow.py:199-258` prove the pinned baseline,
  exact 5/10 and 6/10 categories, and six-plan union.
- **REQ-REC-012:** `test_m5_board_measurement.py:94-124,163-180` preserves raw contradiction
  evidence and requires rounded 75.6/11.8/6.4 output; W3 carries both separately.

`REQ-LIC-001` remains W4 scope and is neither claimed nor implemented in W3.

## K.8 contract drift

- `RawSource` is unchanged; DeepSWE conforms structurally.
- Schema identity remains benchmark + metric + harness + effort + source; no W3 migration.
- Registry remains ordered first-match and unmatched names remain NULL/countable.
- D-105 remains data-owned; D-109 remains output-only rounding; D-110 is untouched.
- Coverage and recommendation CLI exit behavior is unchanged.

**Verdict:** no K.8 drift.

## Hardened producers and citing tests

- **Local allowlisted/no-HTTP acquisition:** `DeepSWEClient.__init__/fetch_raw`; client negative
  tests at `test_deepswe_workflow.py:48-70`. A reviewer socket-denial probe completed the read.
- **Provenance, effort, release-date separation:** `parse_deepswe`; workflow and real-shape tests.
  Reviewer probes confirmed empty, missing-column, unterminated, wholly unusable, and invalid
  provenance payloads all raise `SourceError`.
- **Atomic replacement:** `ingest_deepswe -> _store_scores`; rerun isolation test. Reviewer forced
  an `IntegrityError` and confirmed the prior working set survived.
- **Selected-row effort/freshness/telemetry:** `plan_ranking`, `plan_coverage`,
  `plan_evidence_health`, and `source_health`; real workflow and effort fault tests.
- **Gaps:** none for a signed W3 acceptance invariant.

## Independent real-bundle evidence

```text
CSV records: 50
parse: 49 stored; skipped=1; unknown_effort=1; conflicts=0
effort rows: high=13, low=8, max=9, medium=9, xhigh=10
DeepSWE unmatched: kimi-k3_max, muse-spark-1.1
coverage: coding=5/10; agentic-coding=6/10; union=6/10
agentic health: fresh=0, stale=0, undated=6, unscored=4
DeepSWE source health: rows=49, newest_run_date=None, age_days=None, stale=True
selected rows: six; all harness=mini-swe-agent, effort=high,
               source=epoch_deepswe_external, evidence_date=None
```

Raw selection remained full precision; the application record publishes 72.8, 69.4, 53.8, and
11.8 under D-109.

## Gates

- Focused real-bundle changed surface: **62 passed**.
- Full suite with the real Epoch bundle: **247 passed, 5 expected network-contract skips**.
- Ruff: PASS.
- Mypy: PASS, 26 source files.
- Black: PASS sequentially and on each W3-changed file (the review mirror could not create Black's
  aggregate multiprocessing socket).
- Repository/install record checks, records self-test, and pin check: PASS after the language
  allowlist repair.
- `git diff --check de7cb0e`: PASS after the documentation reflow.
- The reviewer changed no production/test file and made no commit.

## Scope and countersignatures

- Checkpoint: six files, +416/-6. Reviewed repair adds only `.language-allow` and report reflow.
- Build/CI/deploy/schema/migration boundary: no W3 touch.
- **Countersignature 1:** real source is 50 CSV records -> 49 stored, one unknown effort, zero
  conflicts; confirmed against parser, report, real test, and independent replay.
- **Countersignature 2:** category numerators are not additive: 5/10 and 6/10 overlap on five named
  plans, making the union exactly 6/10; confirmed through plans/rosters, reconciliation, coverage,
  and live JSON.

## K.9 candidates outside W3

- `subscribe.py:103-107` contains a stale internal comment saying coding has one scoreable plan;
  update it during W4 documentation sync.
- `docs/coverage-by-req.md` still marks REQ-ING-011b deferred and `docs/architecture.md` still lists
  the pre-Epoch topology. Reconcile these closure surfaces after W4.
- A permanent exact assertion for the two DeepSWE score drop names and a future policy for surplus
  unheaded CSV fields are useful hardening candidates, not current failures.

## Risks queued

No new risk. W4 still owns CC-BY attribution, Epoch staleness CI, and carried ledger items. M6 owns
the public HTTP API contract.
