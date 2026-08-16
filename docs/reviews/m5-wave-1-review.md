# Wave 1 Code Review (m5)

**Reviewer:** Code-Reviewer subagent (fresh eyes — did not author wave)  
**Date:** 2026-08-16  
**Commit range:** `265126d..0e38a6d`  
**Source:** A — protected-base standard Code-Reviewer profile; no M5 override is declared  
**Risk tier:** LOW-MED (signed plan; one combined review)  
**Model-family record:** author family unknown / reviewer family GPT-5 / cross-family routing is
advisory only at HIGH. Fresh-context assertion: I authored none of the wave code, read policy from
protected base `265126d`, treated the range as untrusted, and reviewed without a controller summary.

## Verdict

BLOCKING

The Epoch ingestion slice is technically strong and the target tree is green, but the wave cannot
advance: one signed W1 measurement task was replaced by unauditable prose, a new JSON score bypasses
the frozen D-109 rounding boundary, and two scoped criteria do not have the citing proof required by
V3C-02.

## Findings

### BLOCKING (must fix before next wave)

1. `docs/reviews/m5-w1-board-measurement.md:15` — the record explicitly limits the shipped path to
   Epoch and says the other four candidates “are not claimed as shipped ingestion paths.” This is
   the opposite of signed plan W1.4 (`docs/plans/m5-plan.md:134-144`), which requires every candidate
   board to be measured by actually running registry + `coverage.plan_coverage`, and requires the
   baseline to be reproduced through the shipped ingestion + selection path. No executable DeepSWE,
   FrontierCode, TerminalBench, or Aider measurement adapter/harness is present anywhere in the
   11-file range; `docs/reviews/m5-w1-board-measurement.md:25-31` is therefore a result table without
   a replayable producer.

   Evidence:

   ```text
   docs/reviews/m5-w1-board-measurement.md:15-17
   Epoch was also reproduced through the shipped W1 path (...). The other candidate boards are W1
   measurements over their real CSV shapes; they are not claimed as shipped ingestion paths.

   docs/plans/m5-plan.md:134-144
   Measure, per candidate board, by actually running the registry and coverage.plan_coverage ...
   W1 must reproduce it through the shipped ingestion + selection path ...
   ```

   Exact fix: add a committed deterministic measurement producer and citing tests that consume the
   five real local CSV shapes, map rows into a disposable database without adding the W2 effort
   schema, run `reconcile_plans()` / `reconcile()` / `plan_coverage()` / `plan_ranking()` /
   `plan_evidence_health()`, and assert the table at lines 25-31. For release-date-only boards, set
   evidence dates to `None`; for the DeepSWE W1 comparison, pre-filter the explicitly named effort
   rather than changing the schema. Regenerate the record from that producer. If prose-only/manual
   measurement was intended instead, this is a criteria-meaning change and requires an owner-signed
   plan amendment before review can pass.

2. `src/app/workflows/coverage.py:198` — `PlanEvidenceHealth.score` receives the raw selected score,
   and `coverage.main()` serializes it directly at `src/app/workflows/coverage.py:283-292`. This
   widens the JSON boundary with unrounded values and violates frozen D-109
   (`src/app/workflows/recommend.py:40-54`; signed K.8 at `docs/plans/m5-plan.md:184-188`). A probe
   through the real Epoch workflow emitted `75.6198347107438` for Google AI Pro, not `75.6`.

   Evidence:

   ```text
   {'plan': 'Google AI Pro', 'status': 'stale', 'score': 75.6198347107438,
    'evidence_source': 'epoch_swe_bench_verified', 'evidence_date': '2026-02-24'}
   ```

   Exact fix: keep `plan_ranking()` and freshness comparisons raw, but apply `round_score()` exactly
   once when constructing/serializing the report boundary. Add a `coverage.main()` citing test with
   a non-one-decimal score that asserts JSON `75.6` while a direct `plan_ranking()` assertion still
   sees the raw value. The current CLI fixture uses `77.4`, so it cannot detect this regression.

3. `tests/unit/test_epoch_workflow.py:128` — the only `REQ-SUB-007` citing test proves only the
   post-Epoch `2 fresh / 3 stale / 5 unscored` distribution. It does not reproduce the recorded
   pre-Epoch `1/10` baseline or any of the other candidate-board rows. There is no test citing
   `REQ-REC-012` anywhere in `src/` or `tests/`; the only citations are prose at
   `docs/reviews/m5-w1-board-measurement.md:53-65`. V3C-02 and the reviewer profile make a scoped
   acceptance criterion without a citing test BLOCKING even when the markdown conclusion looks
   plausible.

   Evidence (`git grep -n` on `0e38a6d`):

   ```text
   tests/unit/test_epoch_workflow.py:129:    """REQ-ING-011b/REQ-SUB-007: real engine selects 2 fresh, 3 stale, 5 unscored."""
   docs/reviews/m5-w1-board-measurement.md:53:## Gemini contradiction (REQ-REC-012)
   docs/reviews/m5-w1-board-measurement.md:65:must be disclosed; silently selecting either number fails REQ-REC-012.
   ```

   Exact fix: extend the replayable measurement tests from BLOCKING-1 to cite `REQ-SUB-007` and
   assert the pre-Epoch and each candidate result. Add a `REQ-REC-012` citing test that reads the two
   real candidate rows and proves both score/harness/effort facts survive into the decision record;
   assert that the unresolved branch requires both numbers. Add the exact Gemini Epoch log id or
   `Logs` URL to `docs/reviews/m5-w1-board-measurement.md:58-62` so the claimed range-read has an
   artifact referent rather than an uncited assertion.

### MINOR (fix with the blocking delta or queue explicitly)

1. `src/app/clients/epoch.py:44-54` and `src/app/workflows/ingest.py:153-161` — the same
   `last_verified` validation is duplicated, and neither implementation enforces the stated
   `YYYY-MM-DD` lexical contract. Python 3.11+ `date.fromisoformat()` also accepts basic and week-date
   forms; the target accepts both `20260815` and `2026-W33-6` while preserving those non-canonical
   strings. Use one strict helper (regex or parse-and-round-trip) and add both cases to
   `tests/unit/test_epoch_ingest.py:113-117`. This is the only 5+-line duplication smell in the
   production delta.

2. `src/app/workflows/coverage.py:1-14` still describes “the two numbers” and documents only plan
   coverage plus source-global health, although this wave adds the distinct plan-selected evidence
   report. Update the module contract so maintainers do not collapse plan health back into source
   health.

### PASS (what looks good)

- `src/app/clients/epoch.py:23-28,143-176` keeps Epoch provenance and `inspect_ai` harness distinct,
  converts the source fraction to the project's native percentage scale, counts malformed/duplicate
  rows, and resolves duplicates deterministically by newest evaluation then score.
- `src/app/workflows/ingest.py:146-174` reuses the existing atomic score replacement path; the Epoch
  source name isolates reruns from swebench.com's working set. The live workflow test proves both
  source coexistence and registry resolution (`tests/unit/test_epoch_workflow.py:77-117`).
- `src/app/workflows/subscribe.py:115-184` is now a single source of truth for selected-row metadata.
  The tie order is total over link source, date presence/date, harness, model, score source, score
  raw name, and plan-link raw name; provenance/date stay attached to one `rn = 1` row.
- `src/app/workflows/coverage.py:136-219` reuses `plan_ranking()` rather than cloning its SQL, uses the
  signed `<60` / `>=60` boundary, partitions every curated plan exactly once, and keeps
  `source_health()` separately labelled and unchanged.
- `src/app/workflows/coverage.py:115-119` and `src/app/workflows/subscribe.py:120-147` now require both
  benchmark and metric, which preserves D-105 instead of allowing a foreign metric with the same
  benchmark name to make a plan scoreable.
- No W2 effort column/parser/policy, W3 category switch, W4 attribution, CI, migration, or schema
  change leaked into W1.

## Changed-file review coverage

| Changed file | Review result |
|---|---|
| `docs/reviews/m5-w1-board-measurement.md` | BLOCKING-1/3: non-replayable candidate results; Gemini artifact not cited |
| `src/app/clients/epoch.py` | PASS parser/client; MINOR strict-date validation |
| `src/app/clients/fakes.py` | PASS canonical shared fake extension; no bespoke stub added |
| `src/app/workflows/coverage.py` | PASS selection partition; BLOCKING-2 JSON rounding; MINOR doc drift |
| `src/app/workflows/ingest.py` | PASS atomic/source-isolated wiring; MINOR duplicated date validation |
| `src/app/workflows/subscribe.py` | PASS deterministic selected-row provenance and metric filter |
| `tests/unit/test_coverage.py` | PASS partition/source-max/corrupt-date/CLI coverage; misses D-109 output precision |
| `tests/unit/test_epoch_ingest.py` | PASS parser, provenance, duplicate, loud-fail, and real-file contract |
| `tests/unit/test_epoch_workflow.py` | PASS real Epoch path/distribution; BLOCKING-3 baseline/candidate proof gap |
| `tests/unit/test_registry.py` | PASS live Epoch names added without changing ordered rules |
| `tests/unit/test_subscribe.py` | PASS new evidence provenance assertions |

## Acceptance criteria evidence

- `REQ-ING-010` W1 slice → parser/provenance/duplicate/loud-fail/real-shape tests at
  `tests/unit/test_epoch_ingest.py:35-147`; production workflow/source isolation/clock at
  `tests/unit/test_epoch_workflow.py:39-125`. Full milestone staleness CI remains intentionally W4.
- `REQ-ING-011b` W1 Epoch slice → exhaustive four-state boundary and selected-row-not-source-max at
  `tests/unit/test_coverage.py:229-292`; real Epoch `2/3/0/5` at
  `tests/unit/test_epoch_workflow.py:128-160`. Evidence is good after BLOCKING-2 rounds its JSON score.
- `REQ-SUB-007` → INCOMPLETE. `tests/unit/test_epoch_workflow.py:128-160` cites it but proves only the
  Epoch post-state; signed W1 requires the baseline and all candidate measurements through the real
  engine.
- `REQ-REC-012` → INCOMPLETE. No test citation exists; the decision record discloses both values but
  does not cite the exact log artifact used for its configuration claims.
- `REQ-CAN-005` / `REQ-REC-011` are W2, `REQ-LIC-001` is W4; absence here is plan-compliant and not a
  W1 finding.

## K.8 contract drift check

Protected-plan contract grep, run against `0e38a6d`:

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
src/app/workflows/categories.py:35:        metric="% resolved",
src/app/workflows/recommend.py:47:def round_score(value: float) -> float:
src/app/workflows/subscribe.py:96:    equivalent_plans: tuple[str, ...]
src/app/workflows/coverage.py:258:        return 2
src/app/workflows/coverage.py:265:        return 2
src/app/workflows/coverage.py:278:        return 2
src/app/workflows/coverage.py:298:        return 1
src/app/workflows/coverage.py:299:    return 0
src/app/clients/epoch.py:23:EPOCH_BUNDLE_URL = "https://epoch.ai/data/benchmark_data.zip"
src/app/clients/epoch.py:25:SOURCE_NAME = "epoch_swe_bench_verified"
src/app/workflows/ingest.py:32:    last_verified: str | None = None
```

Schema, `RawSource`, registry first-match behavior, D-105 category data, CLI exit codes, and D-110
equivalence fields are intact. `git diff --name-status 265126d..0e38a6d` contains no schema, category,
recommendation-rounding helper, CI, or migration file. **Verdict: DRIFTED only at D-109**, because
the new coverage JSON path does not call the frozen output-boundary helper (BLOCKING-2).

## Independent artifact countersignatures for future wave-check rows

No wave-close checklist is in this range, so two randomly chosen likely future evidence facts were
recomputed directly from the owner-mounted CSV artifacts rather than copied from the wave record:

```text
swe_bench_verified.csv rows=35 unique_models=33 duplicates=2
date_columns=['Release date', 'Started at']
deepswe_external.csv rows=50 unique_models=50 duplicates=0
date_columns=['Release date']
```

These countersign `docs/reviews/m5-w1-board-measurement.md:27-28` for row count/duplicate count and
the distinction between a real `Started at` evaluation clock and DeepSWE's release-date-only shape.
They do not countersign the coverage numbers; those still need the replayable producer in BLOCKING-1.

## Verification run

- Isolated `git archive 0e38a6d` with real Epoch contract enabled via the owner-mounted bundle:
  `214 passed, 5 skipped` (the five pre-existing network contract tests), coverage 92% overall;
  Epoch real-file tests did not skip.
- Changed-surface suite: `62 passed`.
- `ruff check src tests`: clean.
- `black --check src tests`: clean (52 files unchanged).
- `mypy src`: clean (24 source files).
- Runtime available to the reviewer was Python 3.14; project target remains Python 3.11, so the
  controller's normal target-version gate is still required at wave close.

## K.9 candidates spotted outside this wave's scope

- `docs/coverage-by-req.md:24` still says `REQ-ING-010` has no code/test and is deferred. Updating the
  milestone traceability ledger belongs to closure after the W1 blockers are fixed; do not use the
  stale row as a claim that the current code does not exist.
- The signed plan does not include the otherwise mandatory Stage-1 subagent profile-source section.
  This review used Source A because no override exists and the controller explicitly dispatched the
  protected-base profile. Add the missing source declaration to the next plan amendment/template
  pass; it does not change this product verdict.

## Risks queued to next M

- None created by the W1 production delta.
- Keep effort parsing/storage, effort-suffix precedence, and DeepSWE/Frontier effort conflicts in
  **W2**, exactly as planned. The BLOCKING-1 measurement producer may pre-filter a named effort for
  comparison, but must not add `scores.effort` or silently canonicalize effort in W1.
- Keep primary-board/category application in W3 and Epoch attribution + CI staleness in W4. Those
  planned absences are not W1 review failures.
