# Wave 1 Code Review (m5)

**Reviewer:** Code-Reviewer subagent (fresh eyes — did not author wave)
**Date:** 2026-08-16
**Commit range:** `265126d..8fe1a1e`
**Source:** A — protected-base `subagent-profiles/Code-Reviewer.md`; no M5 override is declared
**Risk tier:** LOW-MED (signed plan; one combined review)
**Model-family record:** author family unknown / reviewer GPT-5 family / cross-family routing is
advisory only at HIGH. Fresh-context assertion: I authored none of the wave code, re-read policy and
the signed plan from protected base `265126d`, treated every changed file as untrusted, and reviewed
the complete 15-file range plus both fix deltas without relying on commit summaries.

## Verdict

PASS

The final fix delta closes both prior blockers and all recorded minors. Epoch is ingested as an
independently attributable source, selected-plan evidence health implements the signed four-state
partition, every candidate board is replayed through the real engine path, the before measurement is
now backed by a pinned complete-board extract, and the standalone JSON boundary obeys D-109 while
internal comparisons retain source precision.

## Findings

### BLOCKING (must fix before next wave)

None.

### MINOR (queue for K.9 gap-fill or next-M)

None.

### PASS (what looks good)

- Prior replay blocker closed: `src/app/workflows/board_measurement.py:548-570` runs the complete
  baseline plus five-candidate producer. Each board receives an isolated database and
  `src/app/workflows/board_measurement.py:357-411` executes curated plan/roster ingestion,
  reconciliation, `plan_coverage()`, raw `plan_ranking()`, and `plan_evidence_health()`.
- Prior baseline-integrity blocker closed: `data/m5-swebench-baseline.json:2-19` carries pinned commit,
  immutable URL, raw SHA-256, extract SHA-256, retrieval date, board, counts, and exact retained field
  set. `src/app/workflows/board_measurement.py:35-45,212-253` freezes those values, requires exactly
  one 180-row Verified board, enforces every parser-consumed field, and verifies the canonical extract
  hash. `src/app/workflows/board_measurement.py:414-444` then requires the shipped parser to reproduce
  173 stored / 7 skipped before running the real registry and selection path.
- Prior D-109 blocker closed: Gemini source fractions remain raw inside
  `src/app/workflows/board_measurement.py:508-545`; `src/app/workflows/board_measurement.py:573-583`
  converts them to percentage points and rounds exactly once at JSON output. The documented record
  reports `75.6% / 11.8% / 6.4x` at `docs/reviews/m5-w1-board-measurement.md:74-90`.
- Prior real-entry/default-path minor closed: `src/app/workflows/board_measurement.py:47,586-610`
  derives defaults from the repository root and sends the explicit output payload through the real
  CLI. `tests/unit/test_m5_board_measurement.py:163-197` changes to an unrelated working directory,
  calls `main()`, checks `75.6 / 11.8 / 6.4`, proves no raw fractions leak, and scans every emitted
  score for the one-decimal boundary.
- Prior selected-date minor closed: `src/app/workflows/coverage.py:187-198` parses the complete date
  and round-trips the canonical lexical form; `tests/unit/test_coverage.py:275-282` rejects both an
  invalid date and an otherwise parseable date with a junk suffix.
- Prior Gemini failure-path minor closed: `src/app/workflows/board_measurement.py:514-522` reuses the
  finite-score validator and rejects missing, zero, non-finite, negative, or out-of-fraction-range
  evidence with `SourceError`, before division.
- Prior module-contract minor closed: `src/app/workflows/coverage.py:13-18` now documents all three
  derived reports rather than referring to “both.” Source-global `source_health()` remains separate
  and unchanged while the plan-selected API reuses the ranking row the product actually selects.
- `src/app/clients/epoch.py:35-48,51-189` enforces a strict independent verification clock, local
  allowlisted bundle access, documented HTTPS provenance, the distinct `inspect_ai` harness, project
  percentage scale, newest-evaluation duplicate selection, counted discards, and loud source errors.
  `src/app/workflows/ingest.py:149-173` reuses atomic per-source replacement, so Epoch and
  swebench.com rows never overwrite or merge across source identity.
- `src/app/workflows/subscribe.py:115-184` remains the single deterministic selected-row source of
  truth. It filters both benchmark and metric, keeps raw score ordering, totally orders equal-score
  evidence, and carries model/harness/date/source provenance from the exact selected row.
- No W2 effort schema/policy, W3 primary-category application, W4 licence/CI work, M6 API surface,
  dependency, migration, CI, or protected governance change leaked into W1.

## Prior finding disposition

| Prior finding | Final evidence | Status |
|---|---|---|
| Candidate boards were prose-only | `board_measurement.py:299-411,470-570`; `test_m5_board_measurement.py:43-91` | CLOSED |
| Coverage JSON leaked raw selected score | `coverage.py:197-209`; `test_coverage.py:311-334` | CLOSED |
| REQ-SUB-007 / REQ-REC-012 proof absent | `test_m5_board_measurement.py:43-160` | CLOSED |
| `last_verified` validation duplicated/permissive | `epoch.py:35-48`; `test_epoch_ingest.py:120-125` | CLOSED |
| Coverage module contract stale | `coverage.py:1-18` | CLOSED |
| Board JSON leaked raw Gemini scores | `board_measurement.py:573-610`; `test_m5_board_measurement.py:163-197` | CLOSED |
| Before input was a three-row self-proving fixture | `m5-swebench-baseline.json:1-1105`; `board_measurement.py:212-253,414-444`; `test_m5_board_measurement.py:127-160` | CLOSED |
| CLI defaults depended on current directory | `board_measurement.py:47,590-592`; `test_m5_board_measurement.py:171-172` | CLOSED |
| Selected evidence accepted junk-suffixed dates | `coverage.py:187-198`; `test_coverage.py:275-282` | CLOSED |
| Gemini zero/non-finite evidence could escape | `board_measurement.py:514-522`; independent injection probe | CLOSED |

## Changed-file review coverage

| Changed file | Review result |
|---|---|
| `data/m5-swebench-baseline.json` | PASS — complete pinned 180-row parser-field extract and metadata |
| `docs/reviews/m5-w1-board-measurement.md` | PASS — replay method, complete baseline, candidate table, rounded contradiction, owner gate |
| `docs/reviews/m5-wave-1-review.md` | This final fresh-eyes verdict |
| `src/app/clients/epoch.py` | PASS — client/parser/provenance/clock/duplicate policy |
| `src/app/clients/fakes.py` | PASS — canonical fake extension; no bespoke parallel mock |
| `src/app/workflows/board_measurement.py` | PASS — replay, integrity validation, raw math, JSON boundary, defaults, failure paths |
| `src/app/workflows/coverage.py` | PASS — plan API, strict dates, D-109 output, source health separation |
| `src/app/workflows/ingest.py` | PASS — atomic, isolated Epoch integration |
| `src/app/workflows/subscribe.py` | PASS — deterministic selected-row provenance and metric filter |
| `tests/unit/test_coverage.py` | PASS — partition/source-max/date/CLI/D-109 evidence |
| `tests/unit/test_epoch_ingest.py` | PASS — parser/provenance/duplicate/loud-fail/real-shape contract |
| `tests/unit/test_epoch_workflow.py` | PASS — production wiring and real 2/3/0/5 distribution |
| `tests/unit/test_m5_board_measurement.py` | PASS — full baseline/candidates/citations/real CLI and D-109 boundary |
| `tests/unit/test_registry.py` | PASS — live Epoch aliases without ordered-rule changes |
| `tests/unit/test_subscribe.py` | PASS — exact selected evidence provenance assertions |

## Acceptance criteria evidence (REQUIRED for PASS verdict)

- `REQ-ING-010` W1 slice → parser/provenance/duplicate/loud-fail/real-shape tests at
  `tests/unit/test_epoch_ingest.py:35-155`; production ingest/source isolation/clock at
  `tests/unit/test_epoch_workflow.py:39-125`. W4 still owns serving attribution and CI staleness.
- `REQ-ING-011b` W1 slice → exhaustive four-state partition, strict corrupt-date handling, and
  selected-row-not-source-max at `tests/unit/test_coverage.py:230-293`; raw-selection/rounded-JSON
  boundary at `tests/unit/test_coverage.py:311-334`; real Epoch `2 fresh / 3 stale / 0 undated /
  5 unscored` at `tests/unit/test_epoch_workflow.py:128-160`.
- `REQ-SUB-007` → full before/candidate real-engine measurement at
  `tests/unit/test_m5_board_measurement.py:43-91`; pinned complete-board provenance, row count,
  parser count, extract hash, truncation, metadata drift, and content drift at
  `tests/unit/test_m5_board_measurement.py:127-160`.
- `REQ-REC-012` → raw internal source evidence and exact artifact referents at
  `tests/unit/test_m5_board_measurement.py:94-124`; real-entry rounded disclosure/no-leak evidence at
  `tests/unit/test_m5_board_measurement.py:163-197`; unresolved disclosure at
  `docs/reviews/m5-w1-board-measurement.md:74-90`.
- D-109 / citing `REQ-REC-010` regression → `tests/unit/test_m5_board_measurement.py:163-197` proves
  raw math remains internal and every JSON score has one-decimal output precision.
- `REQ-CAN-005` / `REQ-REC-011` belong to W2; `REQ-LIC-001` belongs to W4. Their absence is
  plan-compliant, not a W1 proof gap.

## K.8 contract drift check

Protected-plan grep against `8fe1a1e`:

```text
src/app/workflows/schema.py:27:CREATE TABLE IF NOT EXISTS pricing (
src/app/workflows/schema.py:38:CREATE TABLE IF NOT EXISTS scores (
src/app/workflows/schema.py:59:CREATE TABLE IF NOT EXISTS plans (
src/app/workflows/schema.py:71:CREATE TABLE IF NOT EXISTS plan_config (
src/app/workflows/schema.py:77:CREATE TABLE IF NOT EXISTS plan_models (
src/app/clients/protocols.py:13:class RawSource(Protocol):
src/app/workflows/registry.py:134:def canonicalize(name: str) -> ModelRule | None:
src/app/workflows/registry.py:135:    """First-match-wins lookup; None = unmatched (caller counts drops)."""
src/app/workflows/categories.py:14:class CategorySpec:
src/app/workflows/categories.py:34:        primary_benchmark="SWE-bench Verified",
src/app/workflows/recommend.py:47:def round_score(value: float) -> float:
src/app/workflows/subscribe.py:96:    equivalent_plans: tuple[str, ...]
src/app/clients/epoch.py:26:SOURCE_NAME = "epoch_swe_bench_verified"
src/app/workflows/ingest.py:149:def ingest_epoch(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
src/app/workflows/coverage.py:265,272,285:return 2
src/app/workflows/coverage.py:305:return 1
src/app/workflows/coverage.py:306:return 0
src/app/workflows/board_measurement.py:608:return 2
src/app/workflows/board_measurement.py:610:return 0
```

Schemas, `RawSource`, registry first-match semantics, D-105 benchmark+metric category selection,
existing CLI exits, D-109 rounding, and D-110 equivalence remain intact. Epoch's new source and
provenance surface is present. **Verdict: OK — no K.8 drift.**

## Hardened-invariant producers

- Producers of hardened invariants: `EpochClient` / `parse_swe_bench_verified` (provenance, clock,
  newest-evaluation duplicate policy); `ingest_epoch` (atomic source isolation); `plan_ranking`
  (raw deterministic selected row); `plan_evidence_health` (strict four-state partition);
  `validate_baseline_snapshot` / `_baseline` (pinned complete before-evidence);
  `_output_payload` / `board_measurement.main` (D-109 decision-record boundary).
- Citing tests per producer: `tests/unit/test_epoch_ingest.py:35-155`;
  `tests/unit/test_epoch_workflow.py:39-160`; `tests/unit/test_coverage.py:230-334`;
  `tests/unit/test_m5_board_measurement.py:43-197`.
- Gaps: none in the W1 slice. Non-finite/zero Gemini branches were additionally exercised by the
  reviewer with zero on either side plus `nan` / `inf`; all four returned the declared `SourceError`.

## Independent artifact countersignatures for future wave-check rows

No M5-W1 close checklist exists yet. Two randomly chosen future facts were recomputed from artifacts:

```text
baseline: pinned commit f42505b21a0eb31a9cc1204caafcbe0da6c1a259
baseline: 180 complete extract rows -> shipped parser 173 stored + 7 skipped -> 1/10 plans
Epoch:    5/10 = 2 fresh + 3 stale + 0 undated + 5 unscored
DeepSWE:  6/10 = 0 fresh + 0 stale + 6 undated + 4 unscored
```

The independently recomputed canonical extract SHA-256 was
`b5b45c86522fa6a7ffa89e4fb2cf01fcc12df071b1a57f84dc285d274ec772a8`, matching code and metadata.
The artifact also records pinned raw SHA-256
`fa4b61d3167dfe99e1a834e007a38372c5bac07b7627f8e2c3904fb48cd4a006`.

## Verification run

- Exact producer launched from `/private/tmp` using only the default plan/roster/baseline paths and
  the owner-mounted Epoch bundle: exit 0; baseline `180 / 173 / 7 / 1-of-10`; candidate table exactly
  Epoch 5/10, DeepSWE 6/10, FrontierCode 3/10, TerminalBench 5/10, Aider 0/10.
- The same real CLI emitted Gemini `75.6`, `11.8`, ratio `6.4`, unit `percentage points`, and selected
  Epoch scores at one decimal. Neither raw fraction appeared in stdout; direct internal assertions
  retained `0.756198347107438`, `0.11751662971175167`, and their raw ratio.
- Baseline validation independently reproduced 180 rows, canonical retained fields
  `cost/date/name/resolved`, matching extract hash, and shipped parser `173 stored / 7 skipped`.
- Reviewer fault probes: Epoch zero, DeepSWE zero, Epoch `nan`, and DeepSWE `inf` each raised
  `SourceError: REQ-REC-012 Gemini evidence has an unusable fractional score`.
- Real-bundle changed-surface suite (`test_m5_board_measurement`, `test_epoch_ingest`,
  `test_epoch_workflow`, `test_coverage`): `38 passed`.
- `ruff check src tests`: clean. `black --check src tests`: 54 files unchanged.
  `mypy --cache-dir /private/tmp/m5-w1-final-mypy src`: success, 25 source files.
- Controller's already-green full `make check`: `221 passed, 5 skipped`; skips are the existing
  opt-in network contract tests.
- `git diff --check 265126d..8fe1a1e` reports only two intentional Markdown hard breaks at
  `docs/reviews/m5-w1-board-measurement.md:3-4`; no production/test whitespace error.
- Reviewer runtime was Python 3.14; project target remains Python 3.11, covered by the controller's
  normal target-version gate at wave close.

## K.9 candidates spotted outside this wave's scope

- `docs/coverage-by-req.md:23-24` still describes REQ-ING-011b/REQ-ING-010 as having no code or tests.
  Closure should refresh the traceability ledger; the stale M4 carry row is not evidence against the
  present implementation.
- The signed M5 plan does not include the otherwise mandatory Stage-1 subagent-profile source
  section. This review used Source A because no override exists and the controller explicitly
  dispatched the protected-base profile. Repair the plan template/next signed amendment without
  changing this product verdict.

## Risks queued to next M

- Keep effort storage, effort precedence/conflict accounting, and named-effort ranking/disclosure in
  **W2**. W1 correctly pre-filters `high` only inside the measurement adapter and does not add
  `scores.effort`.
- Keep the signed primary-board/category application in W3 and Epoch attribution plus CI staleness in
  W4. Those planned absences are not W1 failures.
- Keep API/deployment work in M6. W1 introduces no HTTP surface.
