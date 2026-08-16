# M5 Wave 4 Implementation Plan

**Goal:** Close REQ-LIC-001 and carried warnings W-003/W-004/W-006/W-007, add the
signed Epoch verification-cadence leg, and synchronize the current product documentation.

**Risk:** HIGH. The signed plan labels W4 LOW-MED by default, but W-004 exposes an existing schema
migration through a new operator command; migration work auto-escalates under P-005. The wave gets a
fresh Code Reviewer, Tester, and migration-focused security pass before close.

**Architecture:** Keep all new behavior additive. Recommendation ranking keeps its existing selected
row; roster-clock provenance is carried from that exact row and aged for the complete scoreable
ranking. Read-only commands stay read-only; schema mutation is available only through the explicit
`python -m app.workflows.schema migrate --db PATH` command, which refuses a missing database. Epoch acquisition freshness is a
separate clock from evaluation age and is checked by a small deterministic CLI used by the weekly
workflow.

## Existing gaps and files

1. **REQ-LIC-001:** define one Epoch CC-BY-4.0 citation in `clients/epoch.py`; include it in
   `workflows/rank.py` export attributions, the `sources` list of both recommendation payloads, and
   `README.md`. Test the real recommendation CLI boundary.
2. **W-007:** remove `ArenaClient.fetch_raw()`'s `/rows` fallback. A filter 500/429/page-cap error
   remains one source-specific `SourceError`; tests prove `/rows` is never called.
3. **W-003:** extend `PlanRank`/`PlanPick` with selected-link `last_verified`; preserve it in the
   deterministic tie-break query. Extend `_stale_notice` with a separate roster-link sentence aged
   against the corresponding plan ingest's `observed_at` and the data-owned window. Tests use fresh
   plan prices plus a stale selected roster and enter through `recommend.main()`.
4. **W-004:** add `schema.main()` with `migrate --db`: missing file/unusable database exit 2, migration
   success emits JSON and exit 0, rerun is idempotent. It opens SQLite in `mode=rw`; recommend and
   coverage remain migration-free read paths.
5. **W-006 / REQ-REC-013 / D-111:** add `excluded_by_budget` and `budget_notice` to subscription
   output. Count only scoreable plans, before the cap; do not overload D-110 equivalence. Test the
   shipped low-budget shape and CLI JSON.
6. **Epoch cadence:** add a deterministic 90-day `epoch` staleness command and committed acquisition-clock
   metadata, then add one unconditional step to the existing weekly staleness job. The workflow is
   DevOps-owned; the signed W4 scope authorizes the additive leg, and K.10 owner review remains a
   milestone-gate item.
7. **Records/docs:** append D-111, index M5 REQs in the PRD, disposition W-003/004/006/007 as fixed,
   update architecture/coverage trace/README, and refresh the current handoff only at closure.

## Test order

Write red acceptance tests first for all six behaviors, run the focused set to confirm failures,
implement minimally, then run focused tests, `make check`, Black, and `git diff --check`. Reviewers
fault-inject at least: Arena fallback restoration, selected roster clock omission, migrate command
silencing, and priced-out count suppression. The migration security pass also probes missing-file
refusal and preservation of legacy rows.

## K.8 contract snapshot at dispatch (`5eb3e15`)

```text
src/app/clients/protocols.py:13:class RawSource(Protocol):
src/app/workflows/schema.py:220:def migrate(conn: sqlite3.Connection) -> list[str]:
src/app/workflows/subscribe.py:35:class PlanRank:
src/app/workflows/subscribe.py:62:class PlanPick:
src/app/workflows/subscribe.py:88:class SubscriptionRecommendation:
src/app/workflows/subscribe.py:130:def plan_ranking(conn: sqlite3.Connection, spec: CategorySpec) -> list[PlanRank]:
src/app/workflows/subscribe.py:281:def recommend_subscription(
src/app/workflows/recommend.py:100:class Recommendation:
src/app/workflows/recommend.py:321:def main(argv: list[str] | None = None) -> int:
src/app/workflows/rank.py:25:ATTRIBUTIONS = (
```

Alternative considered for W-007: a tightly bounded `/rows` fallback. It still downloads category
slices the product does not use, cannot prove that the overall slice is complete before the cap, and
recreates the owner's self-rate-limit incident at a smaller threshold. Refusing the undocumented
recovery is the safer and simpler source-specific failure mode.
