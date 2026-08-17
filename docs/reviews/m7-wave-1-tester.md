# Wave 1 Tester Review (m7)

**Reviewer:** Tester subagent (fresh eyes — did not author any of the wave's code, K.7)
**Date:** 2026-08-17
**Commit range:** `9f4471d..fa87fbf` (f8e4445, 422455d, fa87fbf)
**Risk tier:** HIGH (plan §2 W1 — new production entry point + untrusted network input; V3C-78
auto-escalation). Fault injection is therefore MANDATORY, not recommended (V3C-72).
**Code-Reviewer verdict on this wave:** BLOCKING (`docs/reviews/m7-wave-1-review.md:26`). This
review was run anyway, because the fault-injection evidence is what tells the author which of the
Code-Reviewer's findings are *unproven* rather than merely *unpretty*.

## Verdict

**BLOCKING**

Not because the code is wrong — most of it is right — but because on the two criteria this wave
exists to prove, **the tests could not tell right from wrong**. 55 mutants were injected into the
wave's own code; **26 stayed green on a fully-green suite (kill rate 29/55 = 53%)**, including every
guard that implements REQ-ING-013's headline sentence. I wrote 8 tests during this review, which
raises the kill rate to **40/55 = 73%**; 2 of the 15 survivors are equivalent mutants and 13 are
real, open gaps listed below.

## Acceptance-criterion coverage (V3C-02 — REQUIRED)

- **REQ-ING-012** → `tests/unit/test_build.py:118` `test_build_produces_an_artifact_that_can_actually_answer`
  (module docstring cites the REQ-ID; §-comment at `tests/unit/test_build.py:115`) — asserts the real
  entry point produces non-empty `models`/`pricing`/`scores`/`px_median` — GREEN.
  **Partially proven.** The acceptance sentence in `docs/prd.md` is *"the counts it reports are read
  back OUT of the built file rather than reported by the writers"*. Before this review nothing ever
  re-opened the file: `_read_back` counts through the same live connection the build wrote on, and
  `test_counts_are_read_back_from_the_database_not_from_the_writers`
  (`tests/unit/test_build.py:136`) compares the report against **that same connection** — a
  mirror-implementation test. Now covered by
  `tests/unit/test_build.py:299` `test_cli_artifact_reopened_from_disk_holds_what_the_payload_claims`.
- **REQ-ING-013** → `tests/unit/test_build.py:154-256` (nine citing tests under the
  `# --- REQ-ING-013` banner) — GREEN, but **three of the four failure modes the criterion names
  had no citing test at all** and their guards could be deleted with the suite staying green:
  - *empty `px_median`* — `build.py:303-305` (M01) and `build.py:310-313` (M02/M28) both deletable.
    This is Trap 1 of the plan verbatim, the single defect the wave was written to prevent.
    **Now covered:** `tests/unit/test_build.py:167` and `tests/unit/test_build.py:183`.
  - *a curated stage that stores nothing* — `build.py:146-148` (M13) deletable, **still open**.
  - *an optional source that fails* — `build.py:243-247` (M22/M43) deletable, the whole of D-121's
    mechanism uncovered (`coverage: 246-247 missed`). **Now covered:**
    `tests/unit/test_build.py:200`.
- **W-023** (plan §1 criterion 8, "W1 owns 1, 2 and 8"; plan §2 W1 item 4: *"W-023 closes here or
  the wave does not close"*) → **NOT CLOSED, no citing evidence.** `advisor.db` in the tree is dated
  `Aug 16 00:52` — before this wave — and holds `models=72, pricing=2565, scores=630,
  **px_median=0**`. The artifact the wave was supposed to produce with the new entry point does not
  exist, and the one that is present is the exact 200-with-zero-picks shape Trap 1 describes.
  BLOCKING against the plan's own exit condition. (Independently found by the Code-Reviewer as B7.)

## Fault-injection protocol (V3C-72) — atomic log

Method, per the profile: mutate IN PLACE via exact string replacement → run
`.venv/bin/python -B -m pytest -q --no-header -p no:cacheprovider --no-cov` (the `-B` is mandatory,
W-022) → restore the exact original bytes in a `finally:` → re-hash. **No `git checkout`, `git
restore` or `git stash` was used at any point.** Driver:
`scratchpad/runner.py`. Every mutant was run against the FULL suite, and rounds 1 and 2 were run
twice (once to measure, once to attribute the killing test) — identical results both times.

**Baseline:** `396 passed, 12 skipped in 3.22s`.

### Restoration proof (md5, before → after)

| File | Baseline md5 | Final md5 | Status |
|---|---|---|---|
| `src/app/workflows/build.py` | `a7589eadd3f248ba7becd0fdf93ff8cf` | `a7589eadd3f248ba7becd0fdf93ff8cf` | **identical** |
| `src/app/workflows/sources.py` | `5daafb6c62beb1de4e4c3d23379bb507` | `5daafb6c62beb1de4e4c3d23379bb507` | **identical** |
| `.github/workflows/contract-tests.yml` | `8a60342dc23f69efb6b4fb03a301e055` | `8a60342dc23f69efb6b4fb03a301e055` | **identical** (`git diff --quiet` clean vs HEAD) |
| `tests/unit/test_ci_argument_drift.py` | `c5f990353df09731811832e3b9108a38` | `c5f990353df09731811832e3b9108a38` | **identical** |
| `tests/unit/test_build.py` | `f9a83e4a05d696ee9045add531fe02dc` | `df2d993d4bcca5246bfc6032bb57d594` | changed **deliberately** — 6 tests added by this review |
| `tests/unit/test_sources.py` | `55d2583e80550688b6627afebb0d464a` | `c60b93de4394ee16189eb2c56bd0215e` | changed **deliberately** — 2 tests added by this review |

`git status --porcelain` after the run shows only the two intentional test-file modifications. No
source file under `src/` and no CI file was left altered.

### Mutant table (55 mutants)

`RED` = at least one test failed (mutant killed). `GREEN` = suite fully passed with the fault in
place (a finding). "After" = result once this review's 8 new tests were in place.

| # | file:line | Mutation | Before | Killed by | After |
|---|---|---|---|---|---|
| M01 | `build.py:303` | `price_models <= 0` → `< 0` (empty px_median accepted) | **GREEN** | — | RED — `test_an_unbuilt_px_median_fails_the_build` |
| M02 | `build.py:310` | `px_median` dropped from the read-back tuple | **GREEN** | — | RED — `test_a_median_writer_that_reports_success_without_writing_is_caught` |
| M03 | `build.py:303+310` | both px_median guards removed at once | **GREEN** | — | RED — both of the above |
| M04 | `build.py:240` | `if source.required:` → `if False:` (required source degrades like optional) | RED | `test_a_source_that_stores_nothing_fails_the_build` +3 | RED |
| M05 | `build.py:377` | `main()` returns 0 instead of 3 with operator actions pending | RED | `test_cli_reports_three_when_a_surface_lost_its_evidence` | RED |
| M06 | `build.py:366` | `target.unlink(missing_ok=True)` removed (half-built db survives) | RED | `test_cli_leaves_no_half_built_artifact_behind` | RED |
| M07 | `build.py:233` | `minimum_rows` floor never enforced | RED | `test_a_source_that_stores_nothing_fails_the_build` +1 | RED |
| M08 | `sources.py:109` | litellm `minimum_rows` 100 → 0 | RED | `test_every_remote_source_declares_a_non_zero_floor` | RED |
| M09 | `build.py:210` | `_ingest_bundles` swallows a bundle failure silently | RED | `test_a_bundle_directory_without_the_allowlisted_files_is_reported` | RED |
| M10 | `build.py:153` | `_surfaces_left_without_evidence` returns `[]` | RED | `test_the_blinded_surface_list_is_derived_from_categories_not_typed` +4 | RED |
| M11 | `test_sources.py:30` | `_client_classes()` → `{}` (anti-vacuity probe) | RED | `test_the_walk_finds_clients_at_all` +1 | RED |
| M12 | `contract-tests.yml:91` | stale `--budget dusuk` re-introduced | RED | `test_every_flag_value_ci_passes_is_one_the_code_accepts` | RED |
| M13 | `build.py:146` | `_ingest_curated` accepts a stage that stored 0 | **GREEN** | — | **GREEN** |
| M14 | `build.py:124` | `_IDENTIFIER` guard disabled | RED | `test_read_back_refuses_a_table_name_it_cannot_vouch_for` | RED |
| M15 | `build.py:341` | `--force` no longer required to clobber | RED | `test_cli_refuses_to_overwrite_without_force` | RED |
| M16 | `build.py:345` | missing input file no longer refused | RED | `test_cli_refuses_a_missing_input_file` | RED |
| M17 | `build.py:224` | empty source list accepted | RED | `test_an_empty_source_list_is_refused` | RED |
| M18 | `build.py:206` | a bundle that stored 0 rows counts as success | **GREEN** | — | **GREEN** |
| M19 | `build.py:197` | absent bundle directory silently skipped | RED | `test_a_missing_bundle_directory_is_reported_not_skipped` +1 | RED |
| M20 | `build.py:291` | collapsed-reconciliation floor removed | RED | `test_a_collapsed_registry_fails_the_build` | RED |
| M21 | `build.py:285` | bundle reports dropped from `report.sources` | **GREEN** | — | **GREEN** |
| M22 | `build.py:286` | failed REMOTE optional sources dropped from `required_operator_actions` | **GREEN** | — | RED — `test_a_failed_optional_source_names_the_surface_it_blinds` |
| M23 | `sources.py:144` | arena flipped back to `required=True` (D-121 reversed) | **GREEN** | — | RED — `test_arena_is_the_only_optional_source` |
| M24 | `build.py:307` | `conn.commit()` removed | **GREEN** | — | **GREEN — equivalent mutant** (see below) |
| M25 | `build.py:368` | a failed build exits 0 instead of 2 | RED | `test_cli_leaves_no_half_built_artifact_behind` | RED |
| M26 | `test_ci_argument_drift.py:46` | `_run_scripts()` → `[]` (anti-vacuity probe) | RED | `test_the_workflows_are_actually_parsed` | RED |
| M27 | `build.py:302` | `build_price_medians` no-op'd, `price_models` faked to 1 | RED | `test_build_produces_an_artifact_that_can_actually_answer` +5 | RED |
| M28 | `build.py:311` | whole read-back empty-table floor disabled | **GREEN** | — | RED — `test_a_median_writer_that_reports_success_without_writing_is_caught` |
| M29 | `build.py:359` | `--epoch-dir` silently ignored by the CLI | **GREEN** | — | RED — `test_cli_epoch_dir_argument_actually_reaches_the_bundle_stage` |
| M30 | `sources.py:155` | the deepswe bundle removed from `LOCAL_BUNDLES` | RED | `test_a_missing_bundle_directory_is_reported_not_skipped` +2 | RED |
| M31 | `sources.py:157` | deepswe bundle wired to the WRONG ingest fn (`ingest_epoch`) | **GREEN** | — | **GREEN** |
| M32 | `sources.py:113` | openrouter wired to the WRONG ingest fn (`ingest_litellm`) | **GREEN** | — | **GREEN** |
| M33 | `build.py:377` | exit 3 only when MORE THAN ONE action is pending | **GREEN** | — | RED — `test_cli_exit_three_fires_on_a_single_missing_action` |
| M34 | `build.py:374` | `payload["built"]` inverted | RED | `test_cli_reports_three_when_a_surface_lost_its_evidence` | RED |
| M35 | `build.py:55` | `MINIMUM_MODELS_REGISTERED` 20 → 1 | RED | `test_the_default_model_floor_is_not_weakened_by_tests_lowering_it` +1 | RED |
| M36 | `build.py:284` | local-bundle stage skipped entirely | RED | `test_a_missing_bundle_directory_is_reported_not_skipped` +2 | RED |
| M37 | `build.py:298` | `reconcile_plans` stage skipped entirely | **GREEN** | — | **GREEN** |
| M38 | `build.py:280` | rosters stage skipped entirely (`rosters_stored = 1`) | **GREEN** | — | **GREEN** |
| M39 | `build.py:277` | plans stage skipped entirely | RED | 10 tests (collateral: rosters then reject unknown plan ids) | RED |
| M40 | `build.py:127` | read-back counts fabricated as 1 | RED | `test_counts_are_read_back_from_the_database_not_from_the_writers` | RED |
| M41 | `sources.py:123` | swebench `minimum_rows` 1 → 10000 | **GREEN** | — | **GREEN** |
| M42 | `build.py:183/195` | `LOCAL_BUNDLES` re-bound as a default argument (the injection defect) | RED | `test_cli_reports_zero_when_nothing_is_missing` | RED |
| M43 | `build.py:246` | a failed OPTIONAL source vanishes with no `missing` entry | **GREEN** | — | RED — `test_a_failed_optional_source_names_the_surface_it_blinds` |
| M44 | `sources.py:136` | arena renamed, so `CATEGORIES.primary_source` no longer resolves | **GREEN** | — | RED — `test_every_source_a_category_names_as_primary_exists_in_the_registry` |
| M45 | `build.py:349` | `--force` no longer removes the stale target before rebuilding | **GREEN** | — | **GREEN** |
| M46 | `sources.py:64` | `RemoteSource.required` defaults to `False` | RED | `test_an_unreachable_source_fails_the_build_rather_than_being_skipped` +3 | RED |
| M47 | `build.py:206` | bundle floor `<= 0` → `< 0` | **GREEN** | — | **GREEN** |
| M48 | `build.py:167` | surface derivation matches the wrong field (`task` not `primary_source`) | RED | `test_the_blinded_surface_list_is_derived_from_categories_not_typed` +3 | RED |
| M49 | `sources.py:153` | local-bundle `reason` emptied | RED | `test_local_bundles_state_why_they_are_never_fetched` | RED |
| M50 | `build.py:128` | `_read_back` forces `px_median` to 0 (control mutant) | RED | `test_build_produces_an_artifact_that_can_actually_answer` +5 | RED |
| M51 | `contract-tests.yml:81` | CI invokes `python -m app.workflows.builder` (module does not exist) | **GREEN** | — | **GREEN** |
| M52 | `contract-tests.yml:89` | CI recommend step reads `never_built.db` | **GREEN** | — | **GREEN** |
| M53 | `build.py:239` | below-floor REQUIRED source no longer wrapped as "dependency unusable" | **GREEN** | — | **GREEN** |
| M54 | `build.py:284` | `bundle_dir` never forwarded to `_ingest_bundles` | **GREEN** | — | RED — `test_cli_epoch_dir_argument_actually_reaches_the_bundle_stage` |
| M55 | `build.py:307` | `conn.commit()` → `conn.rollback()` | **GREEN** | — | **GREEN — equivalent mutant** (see below) |

**Kill rate: 29/55 (53%) as the wave was submitted → 40/55 (73%) after this review's tests.**
Advisory per V4C-01; no threshold gates. Reported beside coverage, not instead of it — the module
reports 89% line coverage with `build.py:304-305, 312-313` (the px_median guards) among the missed
lines, which is precisely why coverage alone would have passed this wave.

**Equivalent mutants (not findings):** M24 and M55. Every stage function uses `with conn:`
(`ingest.py:63,126`, `rank.py:162`, `registry.py:237,267`), which commits on block exit, so
`build.py:307`'s `conn.commit()` has nothing left to commit and `rollback()` at that point discards
nothing. Verified empirically by re-opening the produced file read-only. The line is harmless but
also load-bearing for nothing; the Code-Reviewer may want it removed or commented as belt-and-braces.

## BLOCKING

1. **`src/app/workflows/build.py:146-148`** — `_ingest_curated`'s *"a printed zero is not a pass"*
   floor is uncovered (`coverage: 147-148 missed`) and deletable with the suite green (M13).
   `test_empty_plans_fail_the_build` (`tests/unit/test_build.py:236`) looks like its citing test but
   is not: `plans: []` raises `SourceError` from the parser and exits through the `except` branch at
   line 143, never reaching the floor. The branch that catches a *well-formed document holding
   nothing* — the one the docstring says it exists for — has never executed. REQ-ING-013 names this
   failure mode explicitly.
2. **`src/app/workflows/build.py:206-212`** — the local-bundle path's floor AND its success path are
   both uncovered (`coverage: 206-208, 212 missed`). M18 and M47 (a bundle storing 0 rows treated as
   success) stay green, and M21 (successfully-ingested bundles dropped from `report.sources`) stays
   green because **no test in the suite has ever ingested a bundle successfully**. The commit message
   for this change is *"local bundles ingest, so Ruling A stops being hollow"*; the ingestion working
   is asserted nowhere. Every bundle test asserts on the FAILURE report. A fixture bundle directory
   (a minimal allowlisted CSV under `tmp_path`) is needed — the `EPOCH_DATA_DIR`-gated skips do not
   substitute, because they are skipped in CI and locally.
3. **`.github/workflows/contract-tests.yml:81` and `:89-96`** — the wave's stated purpose is that CI
   now invokes the real entry point, and nothing verifies that the invocation resolves. M51
   (`python -m app.workflows.builder`, a module that does not exist) and M52 (the recommend steps
   pointed at a database no step ever writes) both stay green. `test_ci_argument_drift.py` checks
   `--budget`/`--task` *values* and stops there, so the file remains prose to the test suite in
   exactly the dimension that matters: **whether the command runs at all.** This is the same class of
   defect the wave's own module docstring says it exists to end — an unrun step does not hold still,
   it rots — reproduced one layer up. Extend the derivation to assert that every `python -m <module>`
   in a workflow is importable and that every `--db <name>` a step reads is written by an earlier
   step in the same job.
4. **W-023 is not closed** — `advisor.db` (mtime `Aug 16 00:52`, i.e. pre-wave) holds
   `px_median = 0`. Plan §2 W1 item 4 makes producing this artifact with the new entry point the
   wave's exit condition. There is no evidence in the tree that the entry point has ever been run
   against real sources, and no test asserts anything about the shipped artifact. (Same conclusion as
   the Code-Reviewer's B7, reached independently.)

## MINOR (queue to next-M / K.9 gap-fill)

- **`src/app/workflows/sources.py:113,157`** — the registry's `(client, ingest)` pairing is
  unchecked. M31 (deepswe bundle wired to `ingest_epoch`) and M32 (openrouter wired to
  `ingest_litellm`) both stay green. `test_sources.py` proves every client is *declared* and every
  declared class *exists* — set membership in both directions — but never that a source is wired to
  its own ingest function. A mis-wiring produces a build that succeeds and stores the wrong evidence.
- **`src/app/workflows/sources.py:123,130,141`** — `minimum_rows` values are unpinned above zero.
  `test_every_remote_source_declares_a_non_zero_floor` catches `0` (M08 RED) but M41 raising
  swebench's floor to 10 000 — which would make every real build fail — stays green. The floors are
  a per-source judgement; assert the declared value, not merely its sign.
- **`src/app/workflows/build.py:280-282, 298`** — M38 (rosters stage deleted, `rosters_stored`
  hard-coded to 1) and M37 (`reconcile_plans` deleted) stay green. The happy-path test asserts
  `report.rosters_stored > 0` and `plans_matched` is never asserted at all, so both are assertions on
  a **report field** rather than on rows in the artifact. REQ-ING-012 lists `rosters` and
  `reconcile_plans` among the stages the entry point must run; assert their tables in
  `report.verified`, which is read from the database.
- **`src/app/workflows/build.py:349-350`** — the `--force` rebuild path is untested end to end; M45
  (stale target never unlinked before the rebuild) stays green. No test in the suite passes
  `--force`, so the one destructive operation the CLI offers is exercised only by its refusal.
- **`src/app/workflows/build.py:239`** — M53 stays green: narrowing the `except` so a below-floor
  REQUIRED source no longer becomes "dependency unusable" changes the operator-facing sentence and
  nothing notices. `test_a_source_that_stores_nothing_fails_the_build` matches `"below its floor"`,
  which both paths emit.
- **`scripts/smoke_deps.py`** — 110 lines changed in this wave to derive its probes from
  `REMOTE_SOURCES`, and no test references it (`grep -rn smoke_deps tests/` → empty). Its coupling to
  the registry is the wave's own claim; nothing holds it.
- **`tests/unit/test_ci_argument_drift.py:67` `test_the_check_can_fail`** — the test fabricates a
  string, runs the regex over it, and asserts the regex works. It proves the *matcher*, not the
  *guard*. M12 shows the real guard does fire on a real workflow, so the guard is sound — but this
  test's name promises the stronger thing. Either point it at a real workflow copy or rename it.

## Tests that assert prose rather than behaviour

Checked explicitly, because M6 shipped two guards that matched a string while the control behind them
was commented out.

- `tests/unit/test_sources.py:68` `test_local_bundles_state_why_they_are_never_fetched` asserts
  `bundle.reason.strip()` is non-empty. Any non-blank string passes. It is a documentation check
  wearing a test's clothes — acceptable as such, but it proves nothing about the D-101 boundary. The
  boundary itself (never fetch at runtime) has no negative test in this wave.
- `tests/unit/test_build.py:192` `test_build_error_names_the_operator_action_not_a_stack_trace`
  asserts the literal substring `"shape has changed"`. Behaviourally anchored (M07 kills it), but it
  will break on a message reword rather than on a behaviour change.
- `tests/unit/test_build.py:146` `test_the_default_model_floor_is_not_weakened_by_tests_lowering_it`
  asserts a constant equals 20. Legitimate and effective (M35 RED) — noted only because it is the
  one place the production floor is pinned.

No mirror-implementation test was found that passes *by construction*, except
`test_counts_are_read_back_from_the_database_not_from_the_writers`
(`tests/unit/test_build.py:136`), which compares the report against the same connection it was
derived from — addressed by the reopened-file test added here.

## Weakened / deleted-to-green check (V3C-86 — BLOCKING at HIGH tier)

`git diff 9f4471d..HEAD -- tests/` shows three ADDED test files and no modification or deletion of
any existing test. No test was skipped, weakened, or xfailed to force green. **PASS.**

## Network isolation (permission-matrix §3)

- **Baseline: clean.** The full suite run under a `socket.connect` guard that blocks any non-loopback
  address reports `NETGUARD violations: 0` with `396 passed, 12 skipped`. No test reaches the real
  network today. The 5 contract tests that would are correctly gated behind `RUN_CONTRACT_TESTS=1`.
- **But the isolation is accidental, not enforced — MINOR, and the wave already paid for this once.**
  `tests/unit/test_build.py:382` `test_cli_refuses_to_overwrite_without_force` and
  `tests/unit/test_build.py:395` `test_cli_refuses_a_missing_input_file` both call the real `main()`
  **without patching `REMOTE_SOURCES`**. They stay offline only because `main()` returns at line 343
  or 347 before reaching `build()`. Proof: with the `--force` guard alone disabled (M15), that test
  reached the live network — `NETGUARD: outbound connect blocked: ('185.199.108.133', 443)`, and in
  the unguarded run it spent 25.2s and surfaced a real HTTP 500 from
  `datasets-server.huggingface.co`. The wave's own docstring calls an injection point that cannot be
  injected *"this project's most-repeated defect"* (`build.py:267-271`); the remedy shipped was a
  comment. **Ship the gate in the same change (V4C-49):** a conftest-level socket guard failing any
  outbound connect outside `RUN_CONTRACT_TESTS=1` would have caught the original default-argument bug
  mechanically instead of via an upstream outage. Recommended as a W2 item, not blocking W1.

## Mocks / contract tests (V3C-44)

- Canonical fake: `app.clients.fakes.FakeRawSource`, used by `tests/unit/test_build.py:82-99` through
  the real `RemoteSource` shape. No bespoke parallel stub was introduced. **OK.**
- Contract tests against the real APIs exist and are network-gated: `tests/integration/
  test_litellm_contract.py`, `test_scores_contract.py`, `test_arena_openrouter_contract.py`. **OK.**
- **Gap:** there is no canonical fake for a LOCAL BUNDLE. Every bundle test drives the failure path,
  so `LocalBundle.client_type(...)` is never successfully constructed in any test (BLOCKING item 2).

## Suite result

- `.venv/bin/python -B -m pytest -q` at wave submission: **396 passed, 12 skipped in 3.22s.**
- After this review's 8 added tests: **404 passed, 12 skipped in 3.69s.**
- `make typecheck`: `Success: no issues found in 31 source files`.
- `ruff check` on both touched test files: `All checks passed!`
- Coverage on the wave's new code: `src/app/workflows/build.py` 89% (missing 147-148, 206-208, 212,
  246-247, 304-305, 312-313, 350, 362→366, 370→373, 381); `src/app/workflows/sources.py` 100%.
  Note that the 100% on `sources.py` is import-level coverage of a data structure and says nothing
  about wiring correctness (M31/M32 stayed green at 100% coverage).

## Tests added/extended this review

All 8 were verified red→green: each was confirmed to FAIL against the mutant it targets (round 5,
above) and to PASS against the unmutated tree.

- `tests/unit/test_build.py:167` `test_an_unbuilt_px_median_fails_the_build` — REQ-ING-013, Trap 1.
  Kills M01, M03.
- `tests/unit/test_build.py:183` `test_a_median_writer_that_reports_success_without_writing_is_caught`
  — REQ-ING-013 read-back floor. Kills M02, M28.
- `tests/unit/test_build.py:200` `test_a_failed_optional_source_names_the_surface_it_blinds` —
  REQ-ING-013 + D-121's mechanism. Kills M22, M43.
- `tests/unit/test_build.py:299` `test_cli_artifact_reopened_from_disk_holds_what_the_payload_claims`
  — REQ-ING-012's "read back OUT of the file" acceptance sentence.
- `tests/unit/test_build.py:327` `test_cli_exit_three_fires_on_a_single_missing_action` — D-120/D-121
  exit contract. Kills M33.
- `tests/unit/test_build.py:344` `test_cli_epoch_dir_argument_actually_reaches_the_bundle_stage` —
  REQ-ING-012's CLI surface. Kills M29, M54.
- `tests/unit/test_sources.py:80` `test_arena_is_the_only_optional_source` — D-121. Kills M23, M46.
- `tests/unit/test_sources.py:92` `test_every_source_a_category_names_as_primary_exists_in_the_registry`
  — the join key the blinded-surface report depends on. Kills M44.

## What this wave got right, stated because a BLOCKING verdict is not a verdict on the engineering

29 of 55 mutants died on the submitted tree, and the ones that died are not trivial: the exit-code
contract, the half-built-artifact deletion, the `--force` refusal, the identifier guard, the
surfaces-derived-from-CATEGORIES translation, the CI vocabulary drift, and — notably — the
default-argument injection defect (M42) that this milestone's history says keeps recurring. The
anti-vacuity guards in both derived-list tests genuinely fire (M11, M26). The failure is
concentrated in one place and it is a consistent one: **the tests prove what happens when a stage
fails LOUDLY, and almost never what happens when a stage succeeds QUIETLY with nothing in it.**
