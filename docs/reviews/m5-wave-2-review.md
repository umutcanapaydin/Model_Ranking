# Wave 2 Code Review (m5)

**Reviewer:** Code-Reviewer subagent (fresh eyes - did not author wave)
**Date:** 2026-08-16
**Commit range:** `96ba91d..964a389`
**Source:** A - protected-base `subagent-profiles/Code-Reviewer.md`; no M5 override is declared
**Risk tier:** HIGH (`docs/plans/m5-plan.md:198-209`: migration + input parsing)
**Model-family record:** author family unknown / reviewer GPT-5 family / cross-family routing was not
available from the dispatch. Fresh-context assertion: I authored none of this wave, read reviewer
policy and the signed plan from protected base `96ba91d`, treated the complete 12-file diff as
untrusted, and did not use commit summaries as review input.

## Verdict

BLOCKING

The effort schema, parser, registry precedence, named-`high` selection, and both shipped CLI shapes
are substantially in place. The wave cannot close because the ranking artifact violates frozen
D-109, the no-higher-effort sentence makes a stronger and sometimes false claim, higher-effort
evidence can cross harness identity, and the new coverage effort predicate has no mutation-sensitive
entrypoint test.

## Findings

### BLOCKING (must fix before next wave)

1. `src/app/workflows/rank.py:196-224` - `export_ranking()` serializes `RankingRow` with raw
   `asdict()` values, including the newly added `higher_effort_score`, directly to JSON and CSV.
   This violates the frozen D-109 boundary in protected-base `docs/decisions.md:406-423`, which says
   every score reaching a JSON contract or user-facing string is rounded once to one decimal.

   Evidence: an independent boundary probe constructed a row with `score=60.555` and
   `higher_effort_score=75.555`; both the JSON and CSV contained those exact raw values. Internal
   selection should stay raw, but the artifact boundary must round `score`, `secondary_score`, and
   `higher_effort_score`. Add a D-109-citing export test that proves raw `RankingRow` values remain
   unchanged while every score field in both artifacts is one-decimal.

2. `src/app/workflows/recommend.py:144-164` - the fallback branch equates "no published higher
   effort row" with "this model was published only at high effort." Those states are not
   equivalent. A model may have `low` and `high` evidence but no `xhigh`/`max` evidence.

   Evidence: an independent production-path probe inserted the same model at `low=40` and
   `high=60`. `recommend(..., task="agentic-coding")` emitted:

   ```text
   Bu model yalnız high effort düzeyinde yayımlanmış; daha yüksek effort karşılaştırması yok.
   ```

   The first clause is false for that database. `tests/unit/test_effort.py:179-226` checks only the
   second clause and gives the no-higher model exactly one row, so the overclaim stays green. Use a
   sentence that states only the known fact (ranked at `high`; no higher comparison exists), or pass
   enough row-state to distinguish the signed plan's genuine one-row branch. Add the adversarial
   lower-plus-selected/no-higher case through both model and subscription output.

3. `src/app/workflows/rank.py:55-72` and `src/app/workflows/subscribe.py:188-205` -
   `higher_effort_evidence()` selects `MAX(score)` by model, benchmark, metric, and effort but does
   not constrain the selected row's harness. The signed invariant at `docs/plans/m5-plan.md:95-103`
   makes score identity `(model, harness, effort)` specifically to prevent a best-case number from
   being silently substituted. The output reports the selected `high` harness but has no provenance
   field for a different higher-effort harness, so this becomes an undisclosed cross-harness range.

   Evidence: with `high=60` and `max=70` on `h-selected`, plus `max=99` on `h-foreign`, the shipped
   helper returned `("max", 99.0)`. `tests/unit/test_effort.py:133-173` uses
   `mini-swe-agent` for every row and cannot catch this. Carry the selected harness into the
   higher-effort lookup (and keep the chosen evidence provenance auditable); add a citing
   adversarial test proving another harness cannot supply the range in model or plan output.

4. `src/app/workflows/coverage.py:103-144` - the new `ranking_effort` filter is correct but has no
   test that can fail if the predicate at lines 122-129 is removed. This is a new load-bearing policy
   producer on a HIGH wave: without the filter, coverage can say a plan is agentic-scoreable from a
   `max`-only row while both recommendation engines correctly return no `high` answer.

   Evidence: `tests/unit/test_coverage.py:65-214` exercises only the existing `coding`/unspecified
   category, and `tests/unit/test_effort.py:1-238` never imports or calls `plan_coverage` or coverage
   `main()`. Removing only the effort predicate leaves all 239 tests green. Add a REQ-CAN-005 or
   REQ-REC-011-citing live coverage-entry test: a linked plan with only `max` DeepSWE evidence is
   unscoreable for `agentic-coding`; inserting the same identity at `high` makes it scoreable.

### MINOR (queue for K.9 gap-fill or next-M)

- `src/app/workflows/schema.py:143-146` describes post-M1 migrations as additive and "never
  destructive," while the authorized effort migration at `src/app/workflows/schema.py:173-215`
  necessarily rebuilds and drops the old `scores` table. The signed plan explicitly requires this
  rebuild and D-100 makes the evidence DB disposable, so the implementation choice is acceptable;
  update the stale comment so operators do not infer a safety property the code does not have.

### PASS (what looks good)

- `src/app/workflows/schema.py:38-52,153-215` adds the five-level effort domain plus
  `unspecified`, expands the source-row UNIQUE identity with effort, preserves legacy rows as
  `unspecified`, and rebuilds the obsolete UNIQUE key. `tests/unit/test_schema.py:54-100` reaches
  this through `connect()` on a pre-W2 database, preserves the row, admits high and max separately,
  rejects a duplicate high identity, proves idempotence, and rejects unknown effort.
- `src/app/workflows/registry.py:143-191,266-281` resolves all five terminal suffixes before
  canonicalization and keeps explicit-column precedence/conflict state. The canonical-equality guard
  preserves `qwen3.7-max` as a model family. `tests/unit/test_effort.py:21-56` covers both separators,
  all five levels, family-max protection, explicit conflict, and unknown accounting.
- `src/app/clients/deepswe.py:18-115` validates the required shape and HTTPS provenance, accepts
  only finite fractions in `[0,1]`, never turns `Release date` into evaluation age, uses explicit
  effort over a suffix, counts unknown/conflicting rows, de-duplicates deterministically, and fails
  a wholly unusable board loudly.
- `src/app/workflows/ingest.py:101-143` validates effort before source replacement and stores suffix
  inference through the existing atomic score path. Existing sources retain `unspecified`, so their
  category results are unchanged.
- `src/app/workflows/categories.py:13-74` keeps the policy in data and implements the delegated
  choice as a separate `DeepSWE` / `high` `agentic-coding` category. This early category entry is
  required to exercise W2's live output and is consistent with the owner-delegated gate; it does not
  switch the existing `coding` category before W3.
- `src/app/workflows/rank.py:107-188` and `src/app/workflows/subscribe.py:130-214` filter both
  benchmark and metric at exactly the data-owned effort. The live model and subscription tests at
  `tests/unit/test_effort.py:179-226` prove `max` cannot enter `high` ordering and both CLI payloads
  carry the named effort plus a higher-effort score.
- `src/app/workflows/recommend.py:167-191` and `src/app/workflows/subscribe.py:250-276` correctly
  round recommendation score fields and higher-effort score fields at their JSON boundary. The
  D-109 defect is confined to `export_ranking()`.
- No dependency, HTTP API, CI, plan-primary switch, Epoch attribution, closure-ledger, or protected
  governance edit leaked into W2.

## Changed-file review coverage

| Changed file | Review result |
|---|---|
| `src/app/clients/deepswe.py` | PASS - strict effort-aware parser; W3 still owns public board ingest |
| `src/app/workflows/categories.py` | PASS - delegated separate category and data-owned `high` |
| `src/app/workflows/coverage.py` | BLOCKING - correct effort filter has no fault-sensitive test |
| `src/app/workflows/ingest.py` | PASS - validated atomic generic effort storage |
| `src/app/workflows/rank.py` | BLOCKING - cross-harness higher evidence and raw artifact output |
| `src/app/workflows/recommend.py` | BLOCKING - no-higher branch overclaims only-one-row state |
| `src/app/workflows/registry.py` | PASS - suffix family, precedence, family-max guard |
| `src/app/workflows/schema.py` | PASS with MINOR comment drift - migration and identity preserve data |
| `src/app/workflows/subscribe.py` | BLOCKING by shared higher-evidence helper; boundary rounding passes |
| `tests/unit/test_categories.py` | PASS - category map and selected effort locked |
| `tests/unit/test_effort.py` | BLOCKING gaps - no cross-harness, lower-only/no-higher, coverage, export probes |
| `tests/unit/test_schema.py` | PASS - pre-wave migration, UNIQUE, idempotence, unknown rejection |

## Acceptance criteria evidence

- `REQ-CAN-005` - citing schema/migration tests at `tests/unit/test_schema.py:54-100`; suffix,
  precedence, conflict, unknown, and stored-suffix tests at `tests/unit/test_effort.py:21-73`; real
  owner bundle contract at `tests/unit/test_effort.py:229-238`. The real bundle test passed with
  50 raw rows -> 49 parsed, 1 skipped/unknown, 0 conflicts, all five effort values, and no evaluation
  dates. Criterion closure remains BLOCKED until score identity is preserved across the
  higher-effort comparison and the coverage producer has a fault-sensitive test.
- `REQ-REC-011` - real recommendation CLI citing test at `tests/unit/test_effort.py:179-200` and real
  subscription CLI citing test at `tests/unit/test_effort.py:202-226`. Both prove high-only ordering,
  max disclosure, no-higher disclosure, and one-decimal recommendation JSON. Criterion closure
  remains BLOCKED by the false only-one-row claim and cross-harness range.
- D-105 category contract - `tests/unit/test_categories.py:104-111` proves the third category is a
  map entry and its ranking effort is data. Ranking and plan-ranking both constrain benchmark,
  metric, and effort at `src/app/workflows/rank.py:116-166` and
  `src/app/workflows/subscribe.py:134-186`.
- D-109 frozen boundary - recommendation and subscription JSON pass at
  `tests/unit/test_effort.py:179-226`; ranking JSON/CSV fail at
  `src/app/workflows/rank.py:211-224` as recorded in BLOCKING-1.

## K.8 contract drift check

Protected-plan grep against `964a389`:

```text
src/app/workflows/schema.py:45:    effort      TEXT NOT NULL DEFAULT 'unspecified'
src/app/workflows/schema.py:52:    UNIQUE (raw_name, benchmark, metric, harness, effort, source)
src/app/workflows/schema.py:128:class ScoreRow:
src/app/workflows/schema.py:154:EFFORT_LEVELS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")
src/app/clients/protocols.py:13:class RawSource(Protocol):
src/app/workflows/registry.py:135:def canonicalize(name: str) -> ModelRule | None:
src/app/workflows/registry.py:156:def resolve_effort(model_name: str, explicit: str | None = None)
src/app/workflows/categories.py:14:class CategorySpec:
src/app/workflows/categories.py:28:    ranking_effort: str | None = None
src/app/workflows/rank.py:55:def higher_effort_evidence(
src/app/workflows/rank.py:107:def category_ranking(
src/app/workflows/coverage.py:103:def plan_coverage(
src/app/workflows/subscribe.py:130:def plan_ranking(
src/app/workflows/recommend.py:144:def effort_disclosure(
src/app/workflows/recommend.py:320:def main(argv: list[str] | None = None) -> int:
```

The schema delta, `RawSource`, registry first-match semantics, D-105 data category, and existing CLI
exit shape are intact. K.8 is **drifted** at two load-bearing edges: D-109 is violated by ranking
artifact serialization, and higher-effort comparison drops the harness component of the signed score
identity. D-110 equivalence logic is carried unchanged.

## Hardened-invariant producers

- Producers of hardened invariants: `DDL` / `_migrate_scores_effort` (effort domain and source-row
  identity); `resolve_effort` / `parse_deepswe` / `_store_scores` (suffix/column resolution,
  unknown/conflict accounting, persistence); `CategorySpec.ranking_effort` / `category_ranking` /
  `plan_ranking` / `plan_coverage` (single-level policy); `higher_effort_evidence` (range evidence);
  recommendation `_pick`, subscription `_pick`, and `export_ranking` (D-109/output disclosure).
- Citing tests per producer: `tests/unit/test_schema.py:54-100`;
  `tests/unit/test_effort.py:21-73,179-238`; `tests/unit/test_categories.py:104-111`.
- Gaps: `export_ranking` D-109 boundary; same-harness higher evidence; lower-plus-selected/no-higher
  truthful wording; `plan_coverage` effort filtering. These are BLOCKING-1 through BLOCKING-4.

## Independent artifact countersignatures for future wave-check rows

No M5-W2 close checklist exists yet. Two future facts were independently recomputed from artifacts:

1. The owner-mounted `deepswe_external.csv` contains 50 rows on one `mini-swe-agent` harness. The
   shipped parser produced 49 rows, exactly 1 skipped/unknown, 0 conflicts, all five effort levels,
   and `run_date=None` for every row.
2. Replaying those 49 rows through generic storage, reconciliation, median-price construction, and
   `category_ranking()` stored all 49, reconciled 47 with 2 counted drops, and produced 13 `high`
   agentic ranking rows. The chosen high rows remained raw internally; published higher evidence was
   available for 9 of the 13.

The pre-W2 migration test also independently preserved its one legacy row as `unspecified`, admitted
separate high and max identities (three total rows), rejected a duplicate high identity, and was
idempotent on a second `migrate()` call.

## Verification run

- Targeted real-bundle changed-surface suite:
  `test_effort.py test_schema.py test_categories.py test_coverage.py` -> `47 passed`.
- Full suite with `EPOCH_DATA_DIR=/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/epoch_data`
  and sandbox-safe pytest cache/coverage plugins disabled -> `239 passed, 5 skipped`.
- Static gates: `ruff check --no-cache src tests` -> clean; `mypy --cache-dir /tmp/model-ranking-m5w2-mypy src`
  -> success in 26 source files; `black --check src tests` -> 56 files unchanged;
  `git diff --check 96ba91d..964a389` -> clean.
- The literal `make check` wrapper could not run in this read-only reviewer sandbox because
  `pytest-cov` attempted to delete the repository's `.coverage` file and received `EPERM`. The same
  source/test suite plus ruff, mypy, and black were run without repository writes; this bypass is
  recorded rather than hidden.
- Independent fault probes reproduced: raw JSON/CSV scores (`60.555`, `75.555`); false only-high
  wording with low+high rows; cross-harness higher score choosing `99` instead of same-harness `70`.
- Review-start tree was clean. This verdict file is the only reviewer write; no production/test file
  or git state was changed.

## K.9 candidates spotted outside this wave's scope

- `src/app/clients/deepswe.py` intentionally has no public `ingest_deepswe` workflow yet. W3 owns the
  signed-board application; it must wire this parser through a first-class source report so its
  skipped/unknown/conflict counts are actually published rather than discarded.
- `src/app/workflows/rank.py:123-128` has only a partial deterministic tie order (date, harness),
  unlike the total provenance order in plan ranking. It is pre-existing behavior, not a W2 scope
  variance; queue a later deterministic-export hardening if multiple equal-score sources emerge.

## Risks queued to next M

- None from W2 belongs in the next milestone yet. Close the four blockers in a W2 fix delta, then
  keep real DeepSWE ingestion/coverage/freshness in W3, Epoch attribution and staleness CI in W4, and
  HTTP API/deployment work in M6 as signed.
