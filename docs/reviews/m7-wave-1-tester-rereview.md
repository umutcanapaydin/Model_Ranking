# Wave 1 Tester RE-REVIEW (m7) — the fix delta

**Reviewer:** Tester subagent (fresh eyes — did not author the wave or the fix delta, K.7)
**Date:** 2026-08-18
**Scope:** `git diff fa87fbf..HEAD` — commits `6952a55`, `48e0bb7`
**Risk tier:** HIGH (V4C-50 — a fix inherits the risk class of the bug it fixes; both fixed bugs
destroyed or fabricated the artifact this milestone exists to produce)
**Prior verdict:** BLOCKING (`docs/reviews/m7-wave-1-tester.md`) — 55 mutants, 26 survivors, 53% kill

## Verdict

**BLOCKING — on one finding, and not on any of the ones I was asked to look for.**

The fix delta is a real improvement and the mutation numbers say so: **63 mutants, 41 killed as
submitted (65%), 54 killed (86%) after the 7 tests I added here.** `build.py` went from 89% to 98%
coverage. Every one of my four prior BLOCKING items is genuinely closed, and each one is now
defended by a test that dies when I break the thing it names. The `unresolvable_modules` extraction
in particular is the right instinct correctly applied — I could not find a way to disable that guard
without turning a test red.

The BLOCKING item is elsewhere, it is in the fix delta, and no test in this repository can see it:

> **The CI step that handles exit 3 is unreachable, so the B1 fix does not work and the job fails
> on every run.**

Detail in BLOCKING-1 below, with a reproduction. It is the wave's own recurring lesson arriving one
layer up: the exit-3 handler was written, reviewed by three seats, and never executed by anything.

## BLOCKING

### B-1 — `.github/workflows/contract-tests.yml:89-99`: the exit-3 handler cannot run

The step is:

```yaml
        run: |
          set -o pipefail
          python -m app.workflows.build --db ci_advisor.db | tee build-report.json
          code=${PIPESTATUS[0]}
          if [ "$code" = "3" ]; then
            ...
```

GitHub Actions runs a `run:` block with **`bash -e {0}`** when no `shell:` is given (I checked —
this workflow has no `shell:` key and no `defaults.run.shell`; setting `shell: bash` would add
`-eo pipefail`, which is the same or worse). With `-e` active and `pipefail` switched on by the
step's own first line, the pipeline exiting 3 **aborts the script immediately**. `code=${PIPESTATUS[0]}`
never executes, the `if` never executes, and the step exits 3.

Reproduced, not reasoned:

```
$ bash -e probe.sh          # GitHub's default form
report
step exit=3                 # handler never printed

$ bash probe.sh             # same script without -e
report
REACHED-HANDLER code=3
::notice::degraded
step exit=0
```

The consequence is exactly what the step's own comment says must not happen. The comment reads:

> *"The first version of this step just ran the command, which meant it returned 3 on every run,
> forever, and the three steps below it never executed. Three review seats found that
> independently: this wave replaced an unrun step with an unpassable one, and a permanently red
> step is how a `continue-on-error` gets added later (V4C-13)."*

The replacement has the same behaviour as the thing it replaced. A CI runner has no Epoch bundle
by D-101, so `main()` returns 3 by design on every run, so this step fails on every run, so the
three steps below it still never execute.

**Remedy** (suppressing `-e` for this one command, which `||` does):

```yaml
        run: |
          code=0
          python -m app.workflows.build --db ci_advisor.db > build-report.json || code=$?
          cat build-report.json
          if [ "$code" = "3" ]; then
            ...
```

**Why this is BLOCKING and not MINOR:** the whole justification for W1 is that the pipeline stopped
being unrun CI configuration and became tested product code. The one part that is still unrun CI
configuration is the part that decides whether the job passes — and it is wrong. Shipping it means
the first real run of this workflow is red, which is the documented on-ramp to `continue-on-error`.

**Why no test caught it:** `test_ci_argument_drift.py` now resolves module names and checks flag
vocabularies. Neither reaches shell semantics. I do not think a general "execute the workflow"
check belongs in this wave; I do think the remedy above plus a one-line comment naming `-e` as the
reason is the whole fix.

## Fault-injection protocol (V3C-72) — atomic log

Method: mutate IN PLACE by exact string replacement → run the FULL suite with
`.venv/bin/python -B -m pytest -q --no-header -p no:cacheprovider --no-cov` → restore the original
bytes in a `finally:` → re-hash. **No `git checkout` / `git restore` / `git stash` was invoked at
any point.** Driver, uniquely named per the coordinator's instruction:
`scratchpad/tester_m7w1_rereview_driver.py`.

**Baseline:** `462 passed, 12 skipped in 3.66s`.

Two mutants were discarded as invalid rather than counted: `R51` (the inserted `return` landed after
the fixture's last statement — a no-op; re-done correctly as `R53`) and `R61` (`return None or (...)`
still returns the value; re-done correctly as `R61b`). **63 valid mutants.**

### Restoration proof (md5)

| File | Baseline | Final | Status |
|---|---|---|---|
| `src/app/workflows/build.py` | `fff1d21f06ee083918771fd13ab0c225` | `fff1d21f06ee083918771fd13ab0c225` | **identical** |
| `src/app/clients/litellm.py` | `13a9c07da9f2f6ea09db3b94f42118a1` | `13a9c07da9f2f6ea09db3b94f42118a1` | **identical** |
| `src/app/adapter/main.py` | `36bb720ee4673fb9418bfe714677db61` | `36bb720ee4673fb9418bfe714677db61` | **identical** |
| `src/app/workflows/sources.py` | `5daafb6c62beb1de4e4c3d23379bb507` | `5daafb6c62beb1de4e4c3d23379bb507` | **identical** |
| `.github/workflows/contract-tests.yml` | `f353cf039a24a4bb5506c9b5f819937b` | `f353cf039a24a4bb5506c9b5f819937b` | **identical** |
| `tests/unit/test_ci_argument_drift.py` | `cee4548283d65e3c7703be7c0c36e666` | `cee4548283d65e3c7703be7c0c36e666` | **identical** |
| `tests/unit/test_build_artifact_safety.py` | `965e00a569b8dbcc916b7872ad302546` | `b7f0021a159136809d9bf91eefd2ed6d` | changed **deliberately** (3 tests added) |
| `tests/unit/test_parser_envelopes.py` | `e92506e25525c1911f71ed77235791e6` | `53f089bf54b3f892cd498889d1206c0a` | changed **deliberately** (predicate extracted + 1 test) |
| `tests/unit/test_empty_answer_reasons.py` | `3b5d53e10ba8231e03b4630cf0bbc8c4` | `a6c4a9748e1a5d9ca403defc0053ba01` | changed **deliberately** (1 test added) |
| `tests/unit/test_build.py` | `df2d993d4bcca5246bfc6032bb57d594` | `d57df959b0007708346d81d24c5cb32c` | changed **deliberately** (1 test added) |
| `tests/unit/test_sources.py` | `c60b93de4394ee16189eb2c56bd0215e` | `24c3017c784284bc689a305a2f5e7aa9` | changed **deliberately** (1 test added) |

`git status --porcelain` shows only the five intentional test modifications. Every source file and
the workflow file are byte-identical to their pre-injection state.

### Mutant table (63 valid mutants)

"After" = the result once this re-review's 7 tests were in place.

| # | file:line | Mutation | As submitted | Killed by | After |
|---|---|---|---|---|---|
| R01 | `build.py:411` | `replace` → `copyfile`: workspace survives a SUCCESSFUL build | **GREEN** | — | RED — `test_a_successful_rebuild_replaces_the_artifact_and_leaves_nothing_behind` |
| R02 | `build.py:400` | failed build no longer unlinks the workspace | RED | `test_no_workspace_file_survives_either_outcome` +2 | RED |
| R03 | `build.py:386` | pre-build `workspace.unlink` removed | **GREEN** | — | RED — `test_a_stale_workspace_from_a_killed_run_is_never_reused` |
| R04 | `build.py:385` | workspace IS the target again (pre-fix defect restored) | RED | `test_a_failed_rebuild_leaves_the_previous_artifact_untouched` | RED |
| R05 | `build.py:397` | `except BaseException` → `except Exception` | RED | `test_a_keyboard_interrupt_leaves_no_artifact_behind` | RED |
| R06 | `build.py:406` | undeclared exception dressed as exit 2 instead of re-raised | RED | `test_an_undeclared_exception_leaves_no_artifact_behind` +1 | RED |
| R07 | `build.py:401` | `ValueError` dropped from the declared tuple | **GREEN** | — | **GREEN** |
| R08 | `build.py:358` | directory-target guard disabled | RED | `test_building_over_a_directory_fails_cleanly` | RED |
| R09 | `build.py:250` | `reset_source` rejection rollback removed entirely | RED | `test_a_rejected_optional_source_leaves_none_of_its_rows_behind` | RED |
| R10 | `build.py:250` | rollback clears only `scores`; `pricing` rows survive | **GREEN** | — | RED — `test_a_rejected_source_leaves_none_of_its_PRICING_rows_behind` |
| R11 | `build.py:251` | rollback called with a name matching no rows | RED | `test_a_rejected_optional_source_leaves_none_of_its_rows_behind` | RED |
| R12 | `build.py:299` | `bundles=` never forwarded to `_ingest_bundles` | **GREEN** | — | RED — `test_the_bundles_parameter_is_honoured_over_the_module_registry` |
| R13 | `litellm.py:78` | envelope guard disabled (AttributeError escapes) | RED | `test_a_hostile_envelope_...[*-litellm]` ×5 | RED |
| R14 | `litellm.py:79` | guard downgraded from `SourceError` to a silent empty parse | **GREEN** | — | **GREEN** |
| R15 | `litellm.py:78` | guard accepts lists too | RED | `test_a_hostile_envelope_...[json-array-litellm]` | RED |
| R16 | `main.py:743` | no-evidence branch disabled (budget blamed again) | RED | `test_a_surface_with_no_evidence_source_says_so...` +1 | RED |
| R17 | `main.py:743` | no-evidence branch fires ALWAYS | **GREEN** | — | RED — `test_a_surface_with_evidence_but_nothing_affordable_blames_the_budget` |
| R18 | `main.py:745` | no-evidence sentence loses the "no evidence" phrasing | RED | `test_a_surface_with_no_evidence_source_says_so...` +1 | RED |
| R19 | `test_ci_argument_drift.py:96` | `app.` filter inverted | RED | `test_the_module_check_can_fail` | RED |
| R20 | `test_ci_argument_drift.py:98` | `find_spec` result ignored | RED | `test_the_module_check_can_fail` | RED |
| R21 | `contract-tests.yml:91` | CI invokes `app.workflows.builder` | RED | `test_every_module_ci_invokes_actually_resolves` | RED |
| R22 | `build.py:417` | exit 3 → 0 (regression probe) | RED | `test_cli_exit_three_fires_on_a_single_missing_action` +6 | RED |
| R23 | `build.py:311` | px_median floor removed (regression probe) | RED | `test_an_unbuilt_px_median_fails_the_build` | RED |
| R24 | `build.py:146` | `_ingest_curated` zero floor removed (M13 regression) | RED | `test_a_curated_stage_that_stores_zero_fails_the_build` | RED |
| R25 | `build.py:206` | bundle zero-row floor removed (M18/M47 regression) | RED | `test_a_bundle_that_stores_zero_rows_is_a_missing_bundle` | RED |
| R26 | `build.py:212` | bundle success path dropped (M21 regression) | RED | `test_a_bundle_that_ingests_successfully_is_counted` | RED |
| R27 | `build.py:411` | `--force` rebuild keeps the STALE artifact, reports success | **GREEN** | — | RED — `test_a_successful_rebuild_replaces_the_artifact_and_leaves_nothing_behind` |
| R28 | `main.py:745` | no-evidence sentence stops naming which benchmark is absent | **GREEN** | — | **GREEN** |
| R29 | `test_parser_envelopes.py:52` | the wrong-exception arm stops failing | **GREEN** | — | RED (as R61b) — `test_the_envelope_contract_check_can_fail` |
| R30 | `test_ci_argument_drift.py:79` | `_MODULE` regex made non-matching | RED | `test_the_module_check_can_fail` | RED |
| R31 | `contract-tests.yml:102` | recommend steps read a db no step writes (M52) | **GREEN** | — | **GREEN** |
| R32 | `build.py:183` | `bundles` re-bound as a default argument (M42 regression) | RED | 10 tests | RED |
| R33 | `main.py:750` | no-evidence answer drops `source_health` | RED | `test_an_absent_evidence_source_is_never_reported_healthy` +1 | RED |
| R34 | `build.py:300` | bundle reports never extended into `report.sources` | RED | `test_a_bundle_that_ingests_successfully_is_counted` | RED |
| R35 | `sources.py:144` | arena flipped to required | RED | `test_arena_is_the_only_optional_source` | RED |
| R36 | `build.py:395` | `--epoch-dir` ignored again | RED | `test_cli_epoch_dir_argument_actually_reaches_the_bundle_stage` +1 | RED |
| R37 | `build.py:319` | read-back `px_median` floor dropped | RED | `test_a_median_writer_that_reports_success_without_writing_is_caught` | RED |
| R38 | `main.py:743` | branch keyed on a field that is always present | **GREEN** | — | **GREEN — equivalent** |
| R39 | `litellm.py:80` | guard made a dead expression | RED | `test_a_hostile_envelope_...[*-litellm]` ×5 | RED |
| R40 | `build.py:250` | rollback runs only for REQUIRED sources | RED | `test_a_rejected_optional_source_leaves_none_of_its_rows_behind` | RED |
| R41 | `build.py:250` | rollback clears only `pricing`; `scores` rows survive | RED | `test_a_rejected_optional_source_leaves_none_of_its_rows_behind` | RED |
| R42 | `build.py:411` | successful build never installs the workspace | RED | `test_cli_artifact_reopened_from_disk_holds_what_the_payload_claims` +4 | RED |
| R43 | `build.py:415` | payload reports the WORKSPACE path to the operator | **GREEN** | — | RED — `test_a_successful_rebuild_replaces_the_artifact_and_leaves_nothing_behind` |
| R44 | `sources.py:109` | litellm floor 100 → 99 | RED | `test_source_floors_are_pinned_by_value_not_only_by_sign` | RED |
| R45 | `build.py:301` | degraded remote sources dropped from operator actions | RED | `test_a_failed_optional_source_names_the_surface_it_blinds` +1 | RED |
| R46 | `build.py:124` | `_read_back` identifier guard disabled | RED | `test_read_back_refuses_a_table_name_it_cannot_vouch_for` | RED |
| R47 | `main.py:743` | branch keyed on `stale` instead of source absence | **GREEN** | — | RED — `test_a_surface_with_evidence_but_nothing_affordable_blames_the_budget` |
| R48 | `litellm.py:78` | guard accepts any object exposing `.items()` | **GREEN** | — | **GREEN — equivalent** |
| R49 | `build.py:361` | `--force` refusal removed | RED | `test_cli_refuses_to_overwrite_without_force` | RED |
| R50 | `build.py:232` | rollback moved BEFORE ingest instead of after rejection | RED | `test_a_rejected_optional_source_leaves_none_of_its_rows_behind` | RED |
| R52 | `build.py:358` | directory guard made unreachable | RED | `test_building_over_a_directory_fails_cleanly` | RED |
| R53 | `test_build_artifact_safety.py:99` | `_offline` autouse fixture disabled | RED | `test_a_failed_rebuild_leaves_the_previous_artifact_untouched` +3 | RED |
| R54 | `main.py:755` | the BUDGET sentence replaced with an unrelated string | **GREEN** | — | RED — `test_a_surface_with_evidence_but_nothing_affordable_blames_the_budget` |
| R55 | `main.py:755` | the BUDGET branch reuses the NO-EVIDENCE sentence | **GREEN** | — | RED — same |
| R56 | `main.py:745` | the NO-EVIDENCE branch reuses the BUDGET sentence | RED | `test_a_surface_with_no_evidence_source_says_so...` +1 | RED |
| R57 | `main.py:755` | **both empty-answer branches return no reason at all** | **GREEN** | — | RED — same |
| R58 | `litellm.py:79` | guard message stops naming the offending type | **GREEN** | — | **GREEN** |
| R59 | `build.py:386` | stale workspace reused and its rows survive | **GREEN** | — | RED — `test_a_stale_workspace_from_a_killed_run_is_never_reused` |
| R60 | `build.py:411` | non-atomic install: copy then unlink | **GREEN** | — | **GREEN** |
| R62 | `build.py:401` | declared tuple WIDENED to `Exception` | RED | `test_an_undeclared_exception_leaves_no_artifact_behind` | RED |
| R63 | `build.py:251` | rollback keyed on the client name instead of the registry name | **GREEN** | — | **GREEN — equivalent** (now pinned equal by a new test) |
| R64 | `sources.py:112` | a registry entry renamed away from its client's name | RED | `test_a_registry_name_matches_the_name_its_client_writes_rows_under` +1 | RED |
| R61b | `test_parser_envelopes.py:54` | extracted predicate never reports a violation | — | `test_the_envelope_contract_check_can_fail` | RED |

**Kill rate: 41/63 (65%) as submitted → 54/63 (86%) after this review's tests.** Prior round for
comparison: 29/55 (53%). Advisory per V4C-01.

## The survivor that matters most, because it is a fix un-covering its own origin

**`src/app/adapter/main.py:752-757` — the BUDGET branch has no citing test after this change.**
Six independent mutants of it stayed green, including `R57`, which makes the branch return
`unavailable_reason: None` — an answer with no picks and no stated reason at all.

The mechanism is worth stating precisely because it is not carelessness and would repeat:

- Before this wave the budget sentence was covered by `tests/unit/test_api_v1.py:598`
  (`assert answer["unavailable_reason"]`), which uses an **empty** database.
- The fix adds a branch *above* it that fires when a surface has no evidence source. An empty
  database has no evidence source. So the new branch now catches that test.
- The old branch kept the assertion's name and lost its coverage. `coverage` agrees: `main.py:752`
  is a **missing line** in the current suite.

Nobody edited a test, nobody weakened one, and the V3C-86 "deleted-to-green" check passes cleanly —
`git diff fa87fbf..HEAD -- tests/` shows additions and one deliberate, well-documented inversion,
with no deletion or skip. The invariant died anyway, by *inheritance*. **A new branch placed above
an old one silently adopts the old one's tests.** I would put that in the seeds; it is a general
shape and this repository just produced a clean instance of it.

Now covered by `tests/unit/test_empty_answer_reasons.py:141`, which asserts both branches from a
**single request** (`task=coding&budget=low`: `coding` has evidence and nothing affordable →
budget sentence; `agentic-coding` has no arena source → gap sentence) and asserts the two strings
differ. That kills R17, R47, R54, R55 and R57 together.

## Remaining survivors (6 findings + 3 equivalent mutants) — all MINOR

- **`src/app/workflows/build.py:401` (R07)** — `ValueError` sits in the declared-exception tuple
  with no reachable trigger and no citing test; removing it changes nothing. The only `ValueError`
  in reach is `reset_source`'s unknown-table guard, which cannot fire against the hardcoded
  `("pricing", "scores")`. This is the *widening* direction of a catch, and R62 shows widening is
  dangerous here: it converts an unknown builder bug into a clean exit 2, defeating the `raise` five
  lines below that was added on purpose. **Either name the trigger with a test or delete the class.**
- **`src/app/clients/litellm.py:79` (R14)** — replacing `raise SourceError` with `return [], 0`
  stays green, because `test_parser_envelopes.py` deliberately permits a lenient parser. That is a
  defensible contract, and the `minimum_rows` floor does catch the consequence — but it means the
  *decision to refuse* is unpinned. MINOR; note it in the docstring or pin it.
- **`src/app/adapter/main.py:745` (R28) and `src/app/clients/litellm.py:79` (R58)** — both messages
  can stop naming the specific benchmark / the offending type and nothing notices. D-121's condition
  is that the surface *names* what is missing, so the specificity is arguably load-bearing prose.
  Cheap fix: assert `spec.primary_benchmark` appears in the gap sentence.
- **`.github/workflows/contract-tests.yml:102` (R31)** — M52, still open by your choice. **My
  answer to your question is below.**
- **`src/app/workflows/build.py:411` (R60)** — replacing `Path.replace` with copy-then-unlink stays
  green even against my new test, because copy-then-unlink also ends with the right content and no
  leftovers. What is lost is **atomicity**: a crash mid-copy leaves a truncated file at the target.
  I did not write a test for this and I recommend you don't either — asserting "`replace` was
  called" is a mirror-implementation test, and crash injection is disproportionate. The honest
  control is the comment: name `Path.replace`'s atomic-rename guarantee as the mechanism, so a
  future refactor to `shutil.copy` has to argue with something.
- **Equivalent mutants, not findings:** R38 (every construction path for `health` sets `"sources"` —
  `main.py:522-531` and `main.py:720-725` — so the `.get` default is unreachable), R48 (`json.loads`
  cannot produce a non-dict exposing `.items()`), R63 (registry name and client name are now pinned
  equal by a new test, so keying on either is the same).

## Your two direct questions

**1. Does `never_built.db` (M52) belong in this wave?**
**Yes — but as a five-line rider, not as a feature.** My reasoning changed because of B-1. I was
going to say "defer it": a general CI-dataflow checker is M8-shaped work and the value is modest.
But B-1 is the second defect in this same file, in this same wave, in the same step, that three
review seats read past — and both were "the YAML says something the code never validates". While
you are already editing `test_ci_argument_drift.py` to fix nothing (it is correct), add the narrow
version: for each job, collect `--db <name>` values that a step *reads* and assert each is a name
some *earlier* step in that job writes. That is one more derivation over `_run_scripts()`, it reuses
the extraction pattern you already built, and it would have caught nothing today — which is the
point of shipping it while it is cheap. The general "verify the workflow's semantics" ambition
stays in M8.

**2. Does the conftest socket gate belong in W1?**
**Yes, and the evidence for it got stronger in this delta.** My W2 recommendation was made when the
only demonstration was M15. Since then: `R53` shows that eight CLI tests in the *new* file stay
offline solely because of one autouse fixture, and `R49` reproduces the guard-removal-reaches-the-
network path. Baseline is still clean — `NETGUARD violations: 0` across all 462 tests, and 0 again
across 469 with my additions — so this is prophylaxis, not a live incident. It belongs in W1 because
V4C-49 says ship the gate with the rule (permission-matrix §3 is the rule and has no gate), because
it has no dependency on W2, and because W2 touches the serving path, where an accidental live fetch
costs more. Roughly:

```python
# tests/conftest.py
import os, socket
if not os.environ.get("RUN_CONTRACT_TESTS"):
    _connect = socket.socket.connect
    def _guarded(self, addr):
        if isinstance(addr, tuple) and not str(addr[0]).startswith(("127.", "::1", "localhost")):
            raise RuntimeError(f"permission-matrix §3: no outbound HTTP from tests ({addr!r})")
        return _connect(self, addr)
    socket.socket.connect = _guarded
```

**I did not implement it.** A repo-wide test gate is a gate-definition change, which AGENTS.md §3
puts in the escalate-now class, and you asked for a judgement rather than a patch. It is a ten-minute
job and I would take it in W1.

## Confirmation of my four prior BLOCKING items

| Prior item | Status | Evidence |
|---|---|---|
| B1 `_ingest_curated` zero floor uncovered | **CLOSED** | R24 RED via `test_a_curated_stage_that_stores_zero_fails_the_build`; `build.py:147-148` now covered |
| B2 bundle floor + bundle SUCCESS path uncovered | **CLOSED** | R25, R26, R34 all RED; `build.py:206-212` covered; the `bundles=` injection point is now pinned by my `test_the_bundles_parameter_is_honoured_over_the_module_registry` |
| B3 CI can invoke a nonexistent module | **CLOSED for modules, and B-1 opened in the same step** | R21, R19, R20, R30 all RED. The extraction of `unresolvable_modules` is correct and I could not neuter it silently |
| B4 W-023 not closed | **CLOSED** | `advisor.db` rebuilt 2026-08-18 00:12 — `models=73, pricing=2583, scores=323, px_median=72`, `effort` column present, evidence from `aider`, `swebench`, `epoch_swe_bench_verified`, `epoch_deepswe_external` (49 rows, so `agentic-coding` is no longer hollow), no `arena` — exactly the D-121 degraded shape the ADR describes. Its citing test at `test_api_config.py:673` was correctly inverted rather than deleted |

My prior MINOR items on `minimum_rows` value-pinning (R44 RED) and the exit-3 threshold (R22 RED)
are also closed. All 8 tests I added at first review are present verbatim and all 8 still kill their
mutants.

## Test-integrity check (V3C-86 — BLOCKING at HIGH tier)

`git diff fa87fbf..HEAD -- tests/` — three files added, three extended, **nothing deleted, skipped,
weakened or xfailed.** The single test whose assertion was reversed
(`test_api_config.py:673`) is the intended and correct inversion of a known-defect pin, and its
docstring explains why. **PASS** — with the caveat recorded above that `main.py:752` lost its
coverage without any test being touched, which this check is not shaped to see.

## Prose-vs-behaviour

- `tests/unit/test_empty_answer_reasons.py:141` (as submitted, `test_the_two_reasons_are_not_the_same_sentence`)
  — its docstring promises *"A surface WITH evidence and an impossible budget must still get the
  budget sentence"*, and the test never requests an impossible budget and never asserts the budget
  sentence. That is the specific reason six mutants survived. The docstring is now true because the
  test beside it makes it so; consider folding the claim into the test that proves it.
- `tests/unit/test_parser_envelopes.py` (as submitted) — the wrong-exception arm could be turned off
  with no test noticing (R29). Fixed here by extracting `envelope_contract_violation` and driving it
  with a deliberately non-conforming parser, mirroring your own `unresolvable_modules` remedy.

## Network isolation (permission-matrix §3)

- Baseline **clean**: `NETGUARD violations: 0` across `462 passed, 12 skipped`, and `0` again after
  my additions (`469 passed`). No test reaches the real network.
- Isolation is still *accidental* rather than *enforced* — see question 2 above.

## Suite result

- As submitted: **462 passed, 12 skipped in 3.66s.**
- After this review's 7 tests: **469 passed, 12 skipped in 3.61s.**
- `make typecheck`: `Success: no issues found in 31 source files`. `ruff check tests/ src/`: clean.
- Coverage on the delta's files: `build.py` **98%** (89% at first review; missing only `421`, the
  `__main__` line, plus two partial branches), `litellm.py` **98%** (missing `109`),
  `main.py` **95%** — missing `752`, which is the BUDGET branch and the finding above.

## Tests added this re-review (7, each verified red→green against the mutant it targets)

- `tests/unit/test_build_artifact_safety.py:157` `test_a_successful_rebuild_replaces_the_artifact_and_leaves_nothing_behind` — kills R01, R27, R43
- `tests/unit/test_build_artifact_safety.py:217` `test_a_stale_workspace_from_a_killed_run_is_never_reused` — kills R03, R59
- `tests/unit/test_build_artifact_safety.py:495` `test_a_rejected_source_leaves_none_of_its_PRICING_rows_behind` — kills R10
- `tests/unit/test_build.py:443` `test_the_bundles_parameter_is_honoured_over_the_module_registry` — kills R12
- `tests/unit/test_sources.py:110` `test_a_registry_name_matches_the_name_its_client_writes_rows_under` — kills R64; makes R63 equivalent
- `tests/unit/test_empty_answer_reasons.py:141` `test_a_surface_with_evidence_but_nothing_affordable_blames_the_budget` — kills R17, R47, R54, R55, R57
- `tests/unit/test_parser_envelopes.py:79` `test_the_envelope_contract_check_can_fail` (+ `envelope_contract_violation` extracted at `:39`) — kills R61b/R29

## Closing note

You asked me to beat 53% and said you would rather I found ten survivors than confirmed fourteen.
I found twenty-two, and eleven of them were consequences of the fixes rather than of the original
code — which is V4C-50 stated as a measurement rather than as a rule. The one that decides this
verdict, though, was not a mutant at all: the CI step everyone reviewed and nobody ran.
