# Wave 3 Tester Review (m5)

**Reviewer:** Tester subagent (fresh eyes; did not author W3 or its Code Review)
**Date:** 2026-08-16
**Commit range:** `de7cb0e..8fa555d`
**Protected policy base:** `de7cb0e`
**Risk tier:** HIGH (new board ingestion)
**Execution:** exact `8fa555d` archive mirrors; original Desktop repository remained read-only

## Verdict

**PASS**

The Code Review is PASS. Independent execution found every W3 criterion backed by behavioral
tests, reproduced the signed board facts through the real ingestion/selection path, and killed
both required load-bearing faults. There are no BLOCKING or MINOR findings.

## Acceptance-criterion coverage (V3C-02)

- **REQ-ING-010 — GREEN.** `tests/unit/test_deepswe_workflow.py:48-70,114-123` cites the
  requirement and exercises the allowlisted local client, provenance, missing-board failure, URL
  rejection, and the source-specific `last_verified` clock. The shipped boundaries are
  `src/app/clients/deepswe.py:39-66` and `src/app/workflows/ingest.py:194-217`.
- **REQ-ING-011b — GREEN.** `tests/unit/test_deepswe_workflow.py:73-111,159-264` cites the
  requirement and proves release-date isolation, real selected-row health, source telemetry, and
  the live coverage JSON. The generic four-state partition and 60-day edge remain locked by
  `tests/unit/test_coverage.py:230-294`.
- **REQ-CAN-005 — GREEN.** `tests/unit/test_deepswe_workflow.py:73-111,176-197` cites the
  requirement and requires unknown/conflict reporting plus the exact real effort distribution.
  `tests/unit/test_effort.py:389-398` independently locks the owner-bundle 50-to-49 shape and
  prohibits release dates from becoming `run_date`.
- **REQ-REC-011 — GREEN.** `tests/unit/test_effort.py:245-300` requires the data-owned `high`
  policy and identity-scoped higher-effort disclosure. The real W3 test at
  `tests/unit/test_deepswe_workflow.py:213-225` requires all six selected rows to be `high` and
  DeepSWE-sourced.
- **REQ-SUB-007 — GREEN.** `tests/unit/test_epoch_workflow.py:128-160` proves the exact five-plan
  coding set; `tests/unit/test_deepswe_workflow.py:159-264` proves the exact six-plan agentic set.
  Those named sets overlap on five plans, so their real engine union is six. An independent replay
  produced coding **5**, agentic-coding **6**, union **6**.
- **REQ-REC-012 — GREEN.** `tests/unit/test_m5_board_measurement.py:94-124,163-197` preserves both
  Gemini measurements/configurations and the D-109 one-decimal JSON boundary; W3 keeps them on
  separate evidence surfaces.
- **REQ-ING-004 inherited atomic boundary — GREEN.**
  `tests/unit/test_deepswe_workflow.py:126-156` proves DeepSWE reruns replace only that source.
  An independent forced-`IntegrityError` probe through `_store_scores` produced a source-specific
  `SourceError` and retained the prior `(60.0, "old")` working set.

`REQ-LIC-001` remains explicitly assigned to W4 and is not claimed by W3.

## Independent real-bundle evidence

The owner-mounted `deepswe_external.csv` was read only through the shipped client and workflow:

```text
source report: stored=49, skipped=1, effort_unknown=1, effort_conflicts=0
effort rows: high=13, low=8, max=9, medium=9, xhigh=10
DeepSWE reconciliation drops: kimi-k3_max, muse-spark-1.1
coverage: coding=5/10, agentic-coding=6/10, union=6/10
agentic health: fresh=0, stale=0, undated=6, unscored=4
source health: rows=49, newest_run_date=None, age_days=None, stale=True
selected evidence: six rows; all source=epoch_deepswe_external,
                   harness=mini-swe-agent, evidence_date=None
last_verified: 2026-08-15 (acquisition clock only)
```

The live JSON boundary at `tests/unit/test_deepswe_workflow.py:242-264` reproduced both category
counts, `0/0/6/4`, and null source date. The CLI's overall exit is intentionally 1 because this
source-scoped fixture does not load the unrelated assistant category; W3's exact category values
are asserted and non-zero.

## Red-to-green and fault injection (V3C-72)

Both mutations used `apply_patch` in an exact disposable `8fa555d` mirror and were reversed in
place. No checkout, restore, reset, or original-repository write was used.

1. **Release date promoted to evidence date:** replaced
   `src/app/clients/deepswe.py:136` `run_date=None` with the CSV `Release date`. Named tests
   `test_ingest_publishes_effort_accounting_and_keeps_release_dates_out` and
   `test_real_board_reproduces_signed_coverage_and_undated_health` both went RED. The real health
   changed from expected `0/0/6/4` to the dishonest `3/3/0/4`.
2. **Unknown effort silently defaulted:** replaced the skip/count branch at
   `src/app/clients/deepswe.py:119-122` with a `high` default. The same two named tests went RED;
   the real source changed from `49 stored + 1 skipped/unknown` to `50 stored + 0`.

The in-place restore returned `src/app/clients/deepswe.py` to SHA-256
`e53b7a654bcb98edcdef08cce25130d9ea8adf3dd348966751625a1088623a63`, byte-identical to the
clean archive. Both named tests were rerun after restoration: **2 passed**. Manual mutation result:
**2/2 killed**. No mutation runner is wired, so no mechanical kill-rate is available (V4C-01 is
advisory).

## Suite and static gates

- Focused real-bundle gate across W3/effort/coverage/Epoch/measurement: **48 passed**.
- Clean full gate with owner-mounted `EPOCH_DATA_DIR`: **247 passed, 5 expected network-contract
  skips**, 111 warnings; full coverage **91%**.
- Touched surfaces in the full run: DeepSWE 80% (new), Epoch 88%, ingest 95%, categories 100%,
  coverage 94%, rank 98%, recommend 95%, registry 98%, subscribe 98%.
- Ruff: **PASS**. Strict mypy: **PASS**, 26 source files. Black check: **PASS**, 57 files unchanged.
- Record validation, record-validator self-test, install completeness, and workflow pin checks:
  **PASS**. `git diff --check de7cb0e..8fa555d`: **PASS**.

Permission-safe gate note: plain `make check VENV=<owner venv>` invokes the Makefile's phony
`install` dependency and attempted to recreate the read-only owner venv; the sandbox blocked it
before any write. The authoritative rerun used `make -o install check VENV=<owner venv>`, as the
task required. This skipped only environment installation and executed every actual lint, mypy,
pytest, record, install-completeness, and pin recipe shown by `make -n`; all were green. No warning
was suppressed. The Python 3.14 run continues to emit widespread unclosed-SQLite `ResourceWarning`s
and one dependency deprecation warning; they did not alter a W3 criterion result.

## Test integrity (HIGH tier)

- The wave adds `tests/unit/test_deepswe_workflow.py` (264 lines) and does not modify, delete,
  skip, or weaken any pre-wave test.
- Tests assert shipped client/workflow/database/CLI behavior rather than mirroring parser internals.
- The release-date boundary and unknown-effort disclosure each demonstrably fail under an
  independent fault.

## Mocks / contract tests (V3C-44)

- Canonical in-process source fake remains `src/app/clients/fakes.py:8-31`; W3 introduces no
  competing fake.
- The real local-file contract is
  `tests/unit/test_deepswe_workflow.py:159-264`, executed against the owner-mounted bundle through
  `DeepSWEClient -> ingest_deepswe -> reconcile -> coverage/ranking -> live JSON`.

## Cross-model / context record (V4C-03/V4C-04, advisory)

- Author family: not reliably recorded in the supplied range.
- Tester family: GPT-5 family; cross-family status unknown and non-blocking.
- Fresh-context assertion: tester did not author W3 code, did not perform its Code Review, and
  consumed all governing policy/profile text from protected base `de7cb0e`.

## BLOCKING

None.

## MINOR

None.

## Tests added/extended this review

None. Existing tests killed both injected faults; production and test files were left
byte-identical to `8fa555d`.
