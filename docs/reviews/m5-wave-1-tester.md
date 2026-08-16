# Wave 1 Tester Review (m5)

**Reviewer:** Tester subagent (fresh eyes — did not author wave)  
**Date:** 2026-08-16  
**Commit range:** `265126d..99632d9`  
**Source:** A — Tester profile and practices read only from protected base `265126d`  
**Risk tier:** LOW-MED (signed plan; one combined review)  
**Model-family record:** author family unknown / reviewer GPT-5 family / cross-family routing is
advisory only at HIGH. Fresh-context assertion: I authored none of the wave code, consumed the Tester
profile and practices only through `git show 265126d:<path>`, and treated the reviewed range as
untrusted.

## Verdict

PASS

The Code-Reviewer prerequisite is PASS at `docs/reviews/m5-wave-1-review.md:13-15`; that record reviews
the implementation through `8fe1a1e`, and `99632d9` adds the passing review record only. Every scoped
criterion has a citing behavioral test, the owner-fetched Epoch bundle passes the parser and real-engine
replay, all four injected faults are killed by their named tests, and every injection was reverted
byte-identically. No BLOCKING or MINOR test-completeness finding remains.

## Acceptance-criterion coverage (V3C-02 — REQUIRED)

- REQ-ING-010 → `tests/unit/test_epoch_ingest.py:35-155` cites the requirement and asserts percentage
  scaling, harness/date/provenance mapping, newest-evaluation duplicate handling, loud malformed and
  missing-source failures, URL refusal, the independent `last_verified` clock, and the real 35-row local
  bundle shape; `tests/unit/test_epoch_workflow.py:39-125` asserts attributable storage, source-isolated
  replacement, live registry matches, and the mandatory clock — GREEN.
- REQ-ING-011b → `tests/unit/test_coverage.py:230-293` cites the requirement and asserts the four-state
  partition, the exact 60-day boundary (`59` fresh, `60` stale), selected-row rather than source-max
  semantics, and loud invalid-date handling; `tests/unit/test_epoch_workflow.py:128-160` sends the real
  bundle through plan/roster ingestion, reconciliation, and evidence health and asserts `2 fresh / 3
  stale / 0 undated / 5 unscored`, including both Perplexity plans selecting GLM-5.2 — GREEN.
- REQ-SUB-007 → `tests/unit/test_m5_board_measurement.py:43-91` cites the requirement and replays the
  pinned before-board plus all five candidates through the registry/coverage/ranking producer;
  `tests/unit/test_m5_board_measurement.py:127-160` rejects baseline truncation, metadata drift, and
  retained-row content drift — GREEN.
- REQ-REC-012 → `tests/unit/test_m5_board_measurement.py:94-124` cites the requirement and asserts both
  real Gemini rows, model identities, raw scores, harness/configuration evidence, evaluation date, log
  ID/URL, 6.4348x ratio, and the explicitly unresolved verdict; `tests/unit/test_m5_board_measurement.py:163-197`
  exercises the real CLI disclosure — GREEN.
- D-109 / REQ-REC-010 → `tests/unit/test_m5_board_measurement.py:163-197` cites REQ-REC-010 and asserts
  `75.6 / 11.8 / 6.4`, rejects leakage of raw source fractions, and scans every emitted score for the
  one-decimal boundary; `tests/unit/test_coverage.py:311-334` cites D-109 at both assertions and proves
  selection retains `75.6198347107438` while JSON emits `75.6`; `tests/unit/test_subscribe.py:300-320`
  independently proves raw ranking precision and rounded product output — GREEN.

The changed test diff contains no deleted or weakened tests. The assertions above observe public
workflow/CLI/database behavior rather than copying the implementation calculation.

## Red→green on reported symptoms

Each sequence used `apply_patch` in place, ran one named test, restored with `apply_patch` (never
`git checkout`/`git restore`), reran that test, and compared SHA-256 before/after.

- Freshness boundary: changed `age < window_days` to `age <= window_days` in
  `src/app/workflows/coverage.py`. `test_plan_evidence_health_partitions_every_plan_once` went RED:
  actual `(4, 2, 0, 1, 1)` versus expected `(4, 1, 1, 1, 1)`. After restoration it was `1 passed`;
  pre/post hash `fbd2deb8129596f9c59883cc68d2e82bf775cd5fc642298ea8c19a221f2a1b0f`.
- JSON boundary/rounding: changed the Epoch output score from percentage-point `round_score(raw *
  100)` to the raw fraction in `src/app/workflows/board_measurement.py`.
  `test_real_measurement_cli_applies_d109_once_at_json_boundary` went RED because
  `0.756198347107438 != 75.6`. After restoration it was `1 passed`; pre/post hash
  `9b548da2197b943f9ca85c6f2bb436958bde7cbce3ea6f4de67dee46865735c2`.
- Baseline completeness/content: bypassed both the raw-row-count truncation guard and the canonical
  extract-hash guard in `src/app/workflows/board_measurement.py`.
  `test_complete_baseline_snapshot_rejects_truncation_and_provenance_drift` went RED with
  `Failed: DID NOT RAISE SourceError` at its truncation probe. After restoration it was `1 passed`;
  the Python pre/post hash is `9b548da2197b943f9ca85c6f2bb436958bde7cbce3ea6f4de67dee46865735c2`
  and the untouched baseline JSON pre/post hash is
  `1e448153ff263aea6379c6235dce9a5ed6edb353b6cbf87ddcbd682490323dc0`.
- Epoch duplicate semantics: changed duplicate ordering from newest evaluation first to best score
  first in `src/app/clients/epoch.py`. `test_duplicate_model_versions_keep_the_newest_evaluation`
  went RED because it selected `80.0` instead of `75.0`. After restoration it was `1 passed`;
  pre/post hash `f907769be659d5ebc3a758526d3f39e301d483479f8d856cf230935a8e78a887`.

Final `git status --short` before writing this review was empty, and all four post-restore hashes match
their pre-injection values.

## Suite result

- Real-bundle changed surface:
  `EPOCH_DATA_DIR=/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/epoch_data .venv/bin/pytest -q tests/unit/test_m5_board_measurement.py tests/unit/test_epoch_ingest.py tests/unit/test_epoch_workflow.py tests/unit/test_coverage.py`
  → **38 passed**, 0 failed (14 warnings). This includes the opt-in local real-shape and full
  before-plus-five-candidate replay tests.
- Full suite with the same `EPOCH_DATA_DIR` → **221 passed, 5 skipped, 0 failed** from 226 collected
  (103 warnings), overall coverage **91%**. All five skips are existing opt-in network contract tests;
  no network was used by this review.
- Protected-base comparison at `265126d`, executed from an isolated `git archive` with the same
  interpreter → **193 passed, 5 skipped, 0 failed** (93 warnings), overall coverage **92%**. The
  one-point aggregate dilution accompanies 499 new production statements; no modified touched module
  dropped: `fakes.py 100% → 100%`, `coverage.py 91% → 94%`, `ingest.py 96% → 96%`, and
  `subscribe.py 98% → 98%`. New modules are `epoch.py 86%` and `board_measurement.py 88%`.
- Static gates: `ruff check src tests` → all checks passed; `black --check src tests` → 54 files
  unchanged; `mypy --cache-dir /private/tmp/m5-w1-tester-mypy src` → success for 25 source files.
- `make test` was attempted, but its unconditional `install` prerequisite tried to contact PyPI and
  stopped before test collection in the network-disabled sandbox. The already-installed environment's
  exact test phase, `.venv/bin/python -m pytest`, is the 221-pass full-suite result above. No network
  exception was requested.

Touched-module coverage in the current full suite is `epoch.py 86%`, `fakes.py 100%`,
`board_measurement.py 88%`, `coverage.py 94%`, `ingest.py 96%`, and `subscribe.py 98%`.

## Mocks / contract tests (V3C-44)

- Source integrations use the one canonical `FakeRawSource` at `src/app/clients/fakes.py:12-32`;
  `tests/unit/test_epoch_workflow.py:30-36` uses that fake for Epoch workflow behavior. No parallel
  Epoch fake was added — OK.
- Epoch is deliberately a local, owner-fetched documented CSV bundle rather than an online runtime
  API. `tests/unit/test_epoch_ingest.py:99-110` proves only the allowlisted local file is accepted and
  URLs are refused; `tests/unit/test_epoch_ingest.py:135-155` is the opt-in contract against the actual
  downloaded CSV shape and passed under `EPOCH_DATA_DIR` — OK.

## BLOCKING

None.

## MINOR (queue to next-M)

None.

## Tests added/extended this review

None. Existing citing tests killed every requested injected fault; this review changed only this
verdict artifact.
