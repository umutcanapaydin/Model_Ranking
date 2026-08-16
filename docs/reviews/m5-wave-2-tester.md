# Wave 2 Tester Review (m5)

**Reviewer:** Tester subagent (fresh eyes; did not author W2 or its Code Review)
**Date:** 2026-08-16
**Commit range:** `96ba91d..795facb`
**Protected policy base:** `96ba91d`
**Risk tier:** HIGH (migration + input parsing)
**Execution:** exact `795facb` archive mirror; original Desktop repository remained read-only

## Verdict

**PASS**

The Code re-review is PASS. Independent execution found every W2 acceptance criterion backed by
behavioral tests, all required tests green on the clean checkpoint, and all three manual mutants
killed. There are no BLOCKING or MINOR findings.

## Acceptance-criterion coverage (V3C-02)

- **REQ-CAN-005 — GREEN.** `tests/unit/test_schema.py:54-100` exercises the real `connect()`
  migration from a pre-W2 database, proves row preservation, effort-aware uniqueness,
  idempotence, and rejection of unknown effort. `tests/unit/test_effort.py:25-77` proves every
  suffix level, protects the Qwen `-max` model-family name, counts explicit/suffix conflicts and
  unknown effort, and persists inferred effort through the existing ingest entrypoint.
- **REQ-CAN-005 live/coverage boundary — GREEN.** `tests/unit/test_effort.py:325-398` executes the
  real coverage CLI, proves max-only evidence cannot satisfy a data-owned high policy, then proves
  a matching high row makes the plan scoreable. The owner-mounted 50-row DeepSWE CSV parses to 49
  stored rows with exactly one counted unknown/skipped row, zero conflicts, all five effort levels,
  and no release date promoted to evaluation date.
- **REQ-REC-011 — GREEN.** `tests/unit/test_effort.py:245-300` runs both shipped recommendation
  entrypoints. It requires high-only selection, same-harness-and-source higher-effort evidence,
  exact identity-scoped no-higher wording, and adversarial rejection of foreign harness/source
  scores. The enforcing paths are `src/app/workflows/rank.py:56-79,113-198` and
  `src/app/workflows/recommend.py:144-164`.
- **D-109 boundary retained — GREEN.** `tests/unit/test_effort.py:303-322` keeps raw
  `60.555/75.555` comparison values and requires one-decimal `60.6/75.6` in both JSON and CSV.
  Boundary code is `src/app/workflows/rank.py:206-245`.

## Red-to-green and fault injection (V3C-72)

All mutations used `apply_patch` in the disposable mirror and were reversed in place. No checkout,
restore, reset, or original-repository write was used.

1. **Effort-filter merge:** removed both high-effort predicates at
   `src/app/workflows/rank.py:125,138`. Named test
   `test_live_recommendation_ranks_high_and_discloses_higher_effort` went RED because the selected
   score became foreign/max `99.0` instead of high `60.0`. In-place restore returned `rank.py` to
   SHA-256 `44b0b3b782a2c0eef31ac6f355ca4306a791d27081f642e2ab657f39e60271a1`.
2. **Range disclosure removed:** replaced `src/app/workflows/recommend.py:160-163` with rank-level
   wording only. The same named CLI test went RED because `max effort` disappeared. In-place restore
   returned `recommend.py` to SHA-256
   `f0a675c37612fbd7d64acce4ca5b9543256beef50565e0e7434e93f3b6684ef7`.
3. **Evidence identity widened:** removed harness/source predicates from
   `src/app/workflows/rank.py:73-75`. The named CLI test went RED because the foreign-harness
   `99.0` score replaced the same-identity `75.0` range. In-place restore returned `rank.py` to the
   same byte-identical SHA-256 above.

Manual mutation result: **3/3 killed**. No mutation runner is wired, so no mechanical kill-rate is
available (V4C-01 remains advisory).

## Suite result

- Focused real-bundle gate: `pytest -q tests/unit/test_effort.py tests/unit/test_schema.py` —
  **27 passed**.
- Full gate with owner-mounted `EPOCH_DATA_DIR`: **241 passed, 5 expected network-contract skips**.
  The five skips are the existing `RUN_CONTRACT_TESTS=1` network tests; the local Epoch/DeepSWE
  contracts ran.
- Full coverage: **90% total**. Touched surfaces: DeepSWE 73% (new module), categories 100%,
  coverage 94%, ingest 94%, rank 98%, recommend 95%, registry 98%, schema 95%, subscribe 98%.
- Ruff: **PASS** (`src tests`).
- Black check: **PASS** (56 files unchanged).
- Strict mypy: **PASS** (26 source files).

The Python 3.14 test run emits widespread SQLite `ResourceWarning`s plus one dependency deprecation
warning. They do not alter the green result and are not attributable to a failed W2 criterion; no
warning was suppressed.

## Test integrity (HIGH tier)

- Wave test diff: one new 398-line effort suite plus additive schema/category assertions; no
  negative test was deleted, skipped, or weakened to green.
- Tests assert shipped CLI/database behavior rather than mirroring helper internals.
- The load-bearing effort filter, range text, and harness/source identity each demonstrably fail
  under independent faults.

## Mocks / contract tests (V3C-44)

- Existing ingest integration uses the canonical `FakeRawSource` at `src/app/clients/fakes.py`; no
  competing DeepSWE fake appeared.
- Real local-file contract is `tests/unit/test_effort.py:389-398`, executed against the
  owner-mounted documented Epoch bundle: **50 source rows -> 49 stored + 1 disclosed unknown**.

## Cross-model / context record (V4C-03/V4C-04, advisory)

- Author family: not reliably recorded in the supplied range.
- Tester family: GPT-5 family; cross-family status unknown, non-blocking.
- Fresh-context assertion: tester did not author W2 code, did not perform its Code Review, and read
  all governing policy/profile text from protected base `96ba91d`.

## BLOCKING

None.

## MINOR

None.

## Tests added/extended this review

None. Existing tests killed all injected faults; production and test files were left byte-identical
to `795facb`.
