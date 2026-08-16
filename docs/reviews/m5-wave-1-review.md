# Wave 1 Code Review (m5)

**Reviewer:** Code-Reviewer subagent (fresh eyes — did not author wave)
**Date:** 2026-08-16
**Commit range:** `265126d..bc31b55`
**Source:** A — protected-base `subagent-profiles/Code-Reviewer.md`; no M5 override is declared
**Risk tier:** LOW-MED (signed plan; one combined review)
**Model-family record:** author family unknown / reviewer GPT-5 family / cross-family routing is advisory
only at HIGH. Fresh-context assertion: I authored none of the wave code, re-read policy and the signed
plan from protected base `265126d`, treated every changed file as untrusted, and reviewed the complete
15-file range rather than relying on commit summaries.

## Verdict

BLOCKING

The first fix delta closes the earlier candidate-replay, coverage-JSON, citation, strict-clock, and
module-contract findings. The target tree is green and the five-board numbers replay. It still cannot
advance: the new standalone producer leaks raw scores through its JSON output in direct conflict with
D-109, and the claimed real “before” measurement is self-proved from a three-row curated fixture whose
completeness and pinned-source provenance are not validated.

## Findings

### BLOCKING (must fix before next wave)

1. `src/app/workflows/board_measurement.py:138-153,467-478,531` — the decision-evidence producer
   preserves source fractions as `epoch_score` / `deepswe_score` and serializes the dataclass with
   `json.dumps(asdict(report))`. The real CLI therefore emits `0.756198347107438` and
   `0.11751662971175167`, while selected plan scores are correctly rounded at
   `src/app/workflows/board_measurement.py:332-342`. D-109 is frozen by signed plan K.8 and requires
   **every score reaching JSON** to be rounded once to one decimal. This is a real boundary defect,
   not ranking math: `_gemini_contradiction()` may compare raw inputs, but the JSON contract may not
   expose them as scores. The load-bearing CLI is also untested: `tests/unit/test_m5_board_measurement.py:11-26`
   imports/calls `measure_w1_boards()` directly and never calls `main()` or `python -m`.

   Direct producer evidence:

   ```json
   {
     "epoch_selected": [{"plan": "Google AI Pro", "score": 75.6}],
     "gemini_contradiction": {
       "epoch_score": 0.756198347107438,
       "deepswe_score": 0.11751662971175167,
       "ratio": 6.434819897084048
     }
   }
   ```

   Protected decision evidence: `docs/decisions.md:406-425` says every score reaching a JSON
   contract is rounded to `SCORE_DECIMALS = 1`, exactly once at the boundary, while comparisons keep
   raw values. Protected `AGENTS.md:101` additionally requires a test through every load-bearing real
   entry point.

   Exact fix: keep raw fractions for internal equality/ratio calculations, but build an explicit
   output DTO/serializer that converts the two benchmark results to the report's percentage-point
   scale and applies `round_score()` once (expected `75.6` and `11.8`); display the ratio consistently
   as `6.4`. Add a real-entry test that calls `main()` (or the documented `python -m` command), parses
   stdout JSON, and asserts every emitted score has the one-decimal boundary while direct internal
   selection/comparison still sees raw values. If exact source fractions must themselves remain JSON
   score fields, that is a D-109 criteria-meaning exception and needs an owner-signed ADR rather than
   an implicit bypass.

2. `data/m5-swebench-baseline.json:1-24` and
   `tests/unit/test_m5_board_measurement.py:34-49` — REQ-SUB-007's “real engine before and after”
   proof uses a hand-curated file containing only three `Verified` results, then asserts the expected
   1/10 result derived from those same three rows. Nothing in the file, producer, or test proves that
   the extract is complete for the official board or that omitted rows cannot match another curated
   plan. `src/app/workflows/board_measurement.py:34-37` compounds this by labelling the bytes with a
   mutable `master` URL rather than a pinned revision. The parser and registry are real, but their
   input is a self-fulfilling acceptance fixture, so the signed plan's warning not to treat planning
   measurement as acceptance proof remains live.

   In-range evidence:

   ```text
   data/m5-swebench-baseline.json:2-23       one board, exactly 3 result objects
   board_measurement.py:34-37                .../master/data/leaderboards.json
   test_m5_board_measurement.py:35           assert baseline == 1/10
   docs/reviews/m5-w1-board-measurement.md:34 pre-Epoch baseline is 1/10
   ```

   The official read-only referent supplied during review is pinned commit
   `f42505b21a0eb31a9cc1204caafcbe0da6c1a259`, raw SHA-256
   `fa4b61d3167dfe99e1a834e007a38372c5bac07b7627f8e2c3904fb48cd4a006`, with 180 raw `Verified`
   rows and 173 after the existing parser's de-duplication. None of those provenance/count facts is
   currently encoded or checked by the range under review; that absence is the finding.

   Exact fix: replace the three-row fixture with a complete pinned 180-row extract (retaining all
   parser-consumed fields), pin `BASELINE_SOURCE_URL` to the commit, and commit/check provenance
   metadata including retrieval date, raw SHA-256, raw row count 180, and parser result count 173.
   The REQ-SUB-007 test must first reject truncation/provenance drift, then run the existing shipped
   ingest + registry + selection path and assert the independently derived 1/10 before result.

### MINOR (fix with the blocking delta or queue explicitly)

1. `src/app/workflows/board_measurement.py:512-514` — new standalone CLI defaults use working-directory
   relative paths (`data/...`) instead of `_repo_root()`, contrary to protected seed F.4. The fully
   explicit documented command works, but defaults fail when the module is launched outside the repo
   root.

2. `src/app/workflows/coverage.py:17` — the module now exposes plan coverage, source health, and
   selected-plan evidence health, but the contract still says “Both are DERIVED.” Change this to
   “All three” so the previously reported documentation drift is fully closed.

3. `src/app/workflows/coverage.py:187-196` — selected evidence validation slices `[:10]` before
   `date.fromisoformat()`. Consequently a corrupt value such as `2026-06-17junk` is silently treated
   as fresh/stale even though `tests/unit/test_coverage.py:275-281` claims corrupt selected dates fail
   loudly. Existing parsers emit canonical dates, so this is not the current real-bundle result, but
   strict parse-and-round-trip should defend the public report boundary.

4. `src/app/workflows/board_measurement.py:453-478` — Gemini evidence parsing accepts non-finite
   values and zero; division by zero escapes `main()`'s declared exit-2 error path. Reuse the finite
   score validator and fail with `SourceError` for non-positive denominator evidence.

### PASS (what looks good)

- Prior BLOCKING-1 is closed: `src/app/workflows/board_measurement.py:483-505` now runs a deterministic
  five-board producer; `:304-358` uses real plan/roster ingest, reconciliation, `plan_coverage()`,
  `plan_ranking()`, and `plan_evidence_health()` in isolated databases. Candidate adapters keep
  release-only boards undated and do not add W2 schema/policy.
- Prior BLOCKING-2 is closed for the production coverage surface:
  `src/app/workflows/coverage.py:157-223` reuses raw `plan_ranking()` selection and rounds only the
  report row; `tests/unit/test_coverage.py:310-333` proves raw `75.6198347107438` remains inside
  ranking while coverage JSON emits `75.6`.
- Prior BLOCKING-3 is closed at the citation/content layer:
  `tests/unit/test_m5_board_measurement.py:30-77` cites REQ-SUB-007 and replays all five candidate
  distributions; `:80-110` cites REQ-REC-012 and verifies both real scores, harness/effort,
  Epoch log id/URL, and the unresolved disclosure record. BLOCKING-2 above is about the independent
  integrity of the before input, not a missing citation.
- Prior MINOR-1 is closed: one strict `validate_last_verified()` helper lives at
  `src/app/clients/epoch.py:35-48`, is reused by client and workflow at `:67` and
  `src/app/workflows/ingest.py:156-160`, and compact/week-date regressions are cited at
  `tests/unit/test_epoch_ingest.py:120-125`.
- `src/app/clients/epoch.py:51-189` keeps the source, documented HTTPS provenance, `inspect_ai`
  harness, project percentage scale, evaluation clock, duplicate policy, and loud-fail behavior
  explicit. `src/app/workflows/ingest.py:149-173` reuses atomic per-source replacement, so Epoch and
  swebench.com rows are not merged or overwritten across source identity.
- `src/app/workflows/subscribe.py:115-184` supplies one deterministic selected-row source of truth,
  carries provenance/date from the exact row, filters both benchmark and metric, and leaves raw score
  ordering intact. `plan_evidence_health()` adds a plan-level API without changing source-global
  `source_health()`.
- No `scores.effort` schema, effort policy, primary-category switch, W4 attribution/CI work, new
  dependency, migration, CI, or protected governance file leaked into W1.

## Changed-file review coverage

| Changed file | Review result |
|---|---|
| `data/m5-swebench-baseline.json` | BLOCKING-2: incomplete/unpinned baseline evidence |
| `docs/reviews/m5-w1-board-measurement.md` | PASS results/disclosure; depends on both blockers; minor hard-break whitespace only |
| `docs/reviews/m5-wave-1-review.md` | Prior verdict independently rechecked and replaced by this re-review |
| `src/app/clients/epoch.py` | PASS client/parser/provenance/strict source clock |
| `src/app/clients/fakes.py` | PASS canonical fake extension; no bespoke parallel mock |
| `src/app/workflows/board_measurement.py` | PASS replay architecture; BLOCKING-1 JSON; MINOR defaults/failure validation |
| `src/app/workflows/coverage.py` | PASS plan-level API and D-109 fix; MINOR doc/date strictness |
| `src/app/workflows/ingest.py` | PASS atomic, isolated Epoch integration |
| `src/app/workflows/subscribe.py` | PASS deterministic selected-row provenance and metric filter |
| `tests/unit/test_coverage.py` | PASS selection/partition/source-max/CLI/D-109 evidence |
| `tests/unit/test_epoch_ingest.py` | PASS parser, provenance, duplicate, loud-fail, real-shape contract |
| `tests/unit/test_epoch_workflow.py` | PASS production wiring and real 2/3/0/5 distribution |
| `tests/unit/test_m5_board_measurement.py` | PASS candidate/citation content; BLOCKING-1 real-entry gap and BLOCKING-2 input integrity |
| `tests/unit/test_registry.py` | PASS live Epoch aliases without ordered-rule changes |
| `tests/unit/test_subscribe.py` | PASS exact selected evidence provenance assertions |

## Acceptance criteria evidence (REQUIRED for PASS verdict)

- `REQ-ING-010` W1 slice → parser/provenance/duplicate/loud-fail/real-shape tests at
  `tests/unit/test_epoch_ingest.py:35-155`; production ingest/source isolation/clock at
  `tests/unit/test_epoch_workflow.py:39-125`. PASS for W1; W4 owns attribution and CI staleness.
- `REQ-ING-011b` W1 slice → exhaustive four-state partition and selected-row-not-source-max at
  `tests/unit/test_coverage.py:230-281`; frozen CLI error/rounding boundary at `:284-333`; real Epoch
  `2 fresh / 3 stale / 0 undated / 5 unscored` at `tests/unit/test_epoch_workflow.py:128-160`. PASS.
- `REQ-SUB-007` → citing five-board test exists at
  `tests/unit/test_m5_board_measurement.py:30-77`, but acceptance remains **BLOCKED** by the unverified
  three-row before-input at `data/m5-swebench-baseline.json:1-24` (BLOCKING-2).
- `REQ-REC-012` → `tests/unit/test_m5_board_measurement.py:80-110` cites it and verifies both source
  rows plus artifact referents; `docs/reviews/m5-w1-board-measurement.md:68-84` discloses the unresolved
  contradiction. PASS for disclosure content, subject to the JSON output fix in BLOCKING-1.
- `REQ-CAN-005` / `REQ-REC-011` belong to W2; `REQ-LIC-001` belongs to W4. Their absence here is
  plan-compliant.

## K.8 contract drift check

Protected-plan grep against `bc31b55`:

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
src/app/workflows/coverage.py:263,270,283:return 2
src/app/workflows/coverage.py:303:return 1
src/app/workflows/coverage.py:304:return 0
src/app/workflows/board_measurement.py:530:return 2
src/app/workflows/board_measurement.py:532:return 0
```

Schemas, `RawSource`, registry first-match semantics, D-105 benchmark+metric category selection,
existing CLI exits, and D-110 equivalence are intact. Epoch's new source/provenance surface is present.
**Verdict: DRIFTED at D-109 only**, on the new board-measurement JSON path (BLOCKING-1).

## Hardened-invariant producers

- Producers of hardened invariants: `EpochClient` / `parse_swe_bench_verified` (provenance, clock,
  newest-evaluation duplicate policy); `ingest_epoch` (atomic source isolation); `plan_ranking`
  (raw deterministic selected row); `plan_evidence_health` (four-state exhaustive partition);
  `board_measurement.main` (decision-record JSON boundary).
- Citing tests per producer: `tests/unit/test_epoch_ingest.py:35-155`;
  `tests/unit/test_epoch_workflow.py:39-160`; `tests/unit/test_coverage.py:230-333`;
  `tests/unit/test_m5_board_measurement.py:30-110`.
- Gaps: no test crosses `board_measurement.main()` and therefore no test defends its D-109 output;
  no complete/pinned baseline producer defends REQ-SUB-007's before measurement.

## Independent artifact countersignatures for future wave-check rows

No M5-W1 close checklist exists yet. Two randomly chosen future facts were recomputed rather than
copied from the record:

```text
real producer: Epoch 5/10 = 2 fresh + 3 stale + 0 undated + 5 unscored
real producer: DeepSWE 6/10 = 0 fresh + 0 stale + 6 undated + 4 unscored
```

The same independent run also reproduced FrontierCode 3/10 undated, TerminalBench 5/10 stale, and
Aider 0/10. These countersign the candidate table, not the incomplete swebench.com before fixture.

## Verification run

- Exact documented five-board producer with
  `EPOCH_DATA_DIR=/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/epoch_data`: exit 0 and
  the signed candidate distributions above; the D-109 raw JSON evidence is pasted in BLOCKING-1.
- Real-bundle changed-surface suite (`test_m5_board_measurement`, `test_epoch_ingest`,
  `test_epoch_workflow`, `test_coverage`): `35 passed`.
- Full suite with the real Epoch bundle: `218 passed, 5 skipped`; all five skips are pre-existing
  opt-in network contract tests.
- `ruff check src tests`: clean. `black --check src tests`: 54 files unchanged.
  `mypy --cache-dir /private/tmp/m5-w1-review-mypy src`: success, 25 source files.
- `git diff --check` reports only two intentional Markdown hard breaks at
  `docs/reviews/m5-w1-board-measurement.md:3-4`; no production/test whitespace error.
- Runtime available to the reviewer was Python 3.14; project target remains Python 3.11, so the
  controller's normal target-version gate remains required at wave close.

## K.9 candidates spotted outside this wave's scope

- `docs/coverage-by-req.md:23-24` still describes REQ-ING-011b/REQ-ING-010 as having no code or tests.
  Closure should refresh the traceability ledger after W1 passes; the stale M4 carry row is not
  evidence against the present implementation.
- The signed M5 plan does not include the otherwise mandatory Stage-1 subagent-profile source
  section. This review used Source A because no override exists and the controller explicitly
  dispatched the protected-base profile. Repair the plan template/next signed amendment without
  changing this product verdict.

## Risks queued to next M

- Keep effort storage, effort precedence/conflict accounting, and named-effort ranking/disclosure in
  **W2**. The W1 measurement adapter may pre-filter `high`; it must not add `scores.effort`.
- Keep the signed primary-board/category application in W3 and Epoch attribution plus CI staleness in
  W4. Those planned absences are not W1 failures.
- Keep API/deployment work in M6. W1 introduces no HTTP surface and must not grow one while fixing
  these evidence-only blockers.
