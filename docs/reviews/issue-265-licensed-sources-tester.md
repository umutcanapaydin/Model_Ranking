---
record_type: review
id: issue-265-licensed-sources-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# #265 Tester review: the unlicensed sources move to licensed data (D-194)

**Reviewer:** Tester seat. I wrote none of the code in the range and took no part in either code review. Policy was read from `.claude/agents/Tester.md` and `.agents/rules/practices.md`, and the range touches neither file.
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `origin/main..4764de7`
**Risk tier:** MEDIUM

## Verdict
BLOCKING

The parsers, the models.dev maker filter and the retired attribution are well pinned: 17 of 28 planted faults were killed. Two things D-194 promises have no test that would fail if they broke:
- **B1.** TB 4.0 and ARC-AGI-2 rows never go through the build's ingest path in any test.
- **B2.** The ARC derivation's "a missing task scores 0" rule is untested.

The served behaviour is right today, as measured below. Nothing in CI holds it there.

## What was run (unmodified tree)

- **Unit suite:** `.venv/bin/python -m pytest -q -p no:cacheprovider --no-cov tests/unit` gave 2693 passed and 9 skipped in 210 s.
- **End to end on the branch artifact.** I used `TestClient` with `MODEL_RANKING_DB` set to a copy of the seat's `advisor.db` (sha256 `bc5435b0…`, unchanged at the end).
  - `/v1/recommendations?task=computer-use`: on `unlimited` the picks are Claude Opus 5.5 at 64.8 (best quality), GPT 6.1 Sol at 58.2 (best value) and GPT 6 Sol at 49.4 (budget). On `medium` the best-quality pick is Sonnet 5.5 at 61.8.
  - `?task=abstract`: Claude Opus 4.6 at 79.0, GPT-5.4 at 75.8 and Gemini 3 Flash at 34.0.
  - `/v1/boards` serves `arc_agi_2` (24 standings) and `terminalbench_4` (21), each with its MIT or Apache-2.0 citation. The 12 credits are `lmarena, litellm, models_dev, swebench, aider, terminal_bench, arc_prize, epoch, datacurve, epoch_compilation, helm, arena_site`. None of `openrouter`, `arc_prize_leaderboard` or `terminal_bench_2` appears.
  - `/v1/categories` gives these families: `computer-use` [`terminalbench_4`, `arena_agent`]; `abstract` [`arc_agi_2`, `epoch_chess`, `epoch_mystery`]; `agentic-coding` [`epoch_deepswe_external`, `terminalbench_4`, `arena_agent`].
- **Transition.** I used a copy of `main`'s served artifact (sha256 `80fa996a…`) with this branch's code.
  - The startup check `standings_problem` passes. Both surfaces answer `no_evidence`, as the runbook says. The credits are D-193's (`openrouter`, `arc_prize_leaderboard`, `terminal_bench_2`).
  - Refresh gates, with `main`'s artifact as live and the branch's as candidate: `degradations` returns [] and `upward_anomalies` returns []. `computer-use` goes from 0 to 21 models and `abstract` from 0 to 24. The largest surface median price move is `agentic-coding`, $3.83 to $4.30 (+12 %, under the 25 % limit).
- **Calibration records.** Both records reproduce from their own `above_floor`, `floor` and `stderr` through `thresholds()`: 3.3 / 10.0 / 4 and 8.8 / 9.5 / 3. The binomial stderr reproduces at 4.392.
- **models.dev (one read-only GET).** The live catalogue parses to 257 maker rows, the same count as the artifact's `models_dev` pricing rows.
- **Edge cases, measured on the artifact:**
  - **TB 4.0 effort `none`.** `z-ai/glm-5.3-flash` is stored as `unspecified`. The parser half is tested (`test_terminalbench_4.py:60`); the stored value is not (B1).
  - **ARC effort suffixes.**
    - `claude-opus-4-6-thinking-120K-high` is stored as `claude-4.6-opus` at `high`, and its `-max/-medium/-low` siblings at their own levels.
    - `-thinking-16k/-32k/-64k`, `-thinking-none` and `-thinking-minimal` are all stored as `unspecified`.
    - `abstract` has no `ranking_effort`, so the board stands on each model's best row, and Opus 4.5 stands at its 64k score, 40.28 (R1).
  - **A model on both TB 4.0 and Arena Agent.** All 21 TB 4.0 models are also on `arena_agent`. The engine publishes both boards and the family; the phone combines them (D-188, generic and unchanged here).
  - **A models.dev outage.** Carry-forward is keyed by source name and is generic. `test_carry_forward.py:144` (`test_pricing_is_carried_like_evidence`) and `:134` cover it. On the transition night there is nothing to carry, and `:115` covers a required source failing with nothing to carry.
- **Records.** Every test that PRD REQ-ING-005 and REQ-SRC-012 name exists and passes. `public.LEFT_OUT == {}` is pinned at `test_public_artifact.py:37`.

## Mutation table

Each fault was planted by exact string replacement, restored from the original bytes and checked by sha256 (all 28 matched). The killing test was found on an 18-file targeted subset. Every subset survivor was then re-run against the whole unit suite (2693 passed each time).

| id | fault | file:line | result |
|---|---|---|---|
| M01 | a price of 0 counts (`v > 0` to `v >= 0`) | src/app/clients/models_dev.py:52 | killed: test_models_dev_ingest::test_only_the_model_makers_own_entries… |
| M02 | namespaced ids (`thinkingmachines/…`) read as the maker's | src/app/clients/models_dev.py:57 | killed: ::test_a_namespaced_model_in_a_makers_catalogue… |
| M03 | another maker's family (GLM under Alibaba) read as the maker's | src/app/clients/models_dev.py:57 | killed: ::test_a_model_another_maker_made_is_not_read… |
| M04 | `xai` routed as `xai` instead of `x-ai` | src/app/clients/models_dev.py:31 | killed: ::test_only_the_model_makers_own_entries… |
| M05 | a maker whose `models` is not an object is skipped, not refused | src/app/clients/models_dev.py:81 | killed: ::test_a_payload_that_is_not_a_catalogue_is_refused |
| T06 | effort `none` no longer unspecified | src/app/clients/terminalbench.py:39 | killed: test_terminalbench_4::test_each_submission_is_a_row… |
| T07 | dedupe key ignores effort (two efforts of one model collapse) | src/app/clients/terminalbench.py:155 | **survived whole suite** |
| T08 | `https` scheme check dropped from `_in_submissions` | src/app/clients/terminalbench.py:84 | **survived whole suite** (redundant: `protocols.ALLOWED_SCHEMES` refuses http in the fetch) |
| T09 | `type == "file"` filter removed | src/app/clients/terminalbench.py:58 | killed: ::test_only_json_files_are_read… |
| T10 | accuracy upper bound removed | src/app/clients/terminalbench.py:92 | killed: ::test_a_submission_without_a_usable_accuracy…[101.0] |
| T11 | keeps the worse of two runs | src/app/clients/terminalbench.py:158 | killed: ::test_two_runs_of_one_model_agent_and_effort_keep_the_better |
| A12 | task floor ignored at the build (`ran < 0`) | src/app/clients/arc_prize.py:81 | killed: test_arc_agi_2::test_a_setting_out_of_range_or_partial…[tasks_run-113] |
| A13 | licence check removed | src/app/clients/arc_prize.py:66 | killed: ::test_a_record_that_is_not_the_licensed_derivation_is_refused |
| A14 | run date dropped | src/app/clients/arc_prize.py:91 | killed: ::test_a_setting_is_stored_with_the_date_of_its_latest_run |
| D15 | ARC Prize's boolean mark overridden by the comparison | scripts/derive_arc_public_eval.py:80 | killed: ::test_a_pair_is_solved_by_either_attempt… |
| D16 | score over tasks run, not over 120 (a missing task no longer 0) | scripts/derive_arc_public_eval.py:197 | **survived whole suite** (B2) |
| D17 | derivation keeps partial settings (`< MIN_TASKS` to `< 0`) | scripts/derive_arc_public_eval.py:208 | **survived whole suite** (the build's A12 guard still holds the served set) |
| D18 | "predates the solutions" comparison inverted | scripts/derive_arc_public_eval.py:136 | killed: ::test_a_setting_is_dated_by_its_latest_attempt… |
| C19 | window rounded to 0.1, not to a half point | scripts/calibrate_surface.py:56 | **survived whole suite** (M1) |
| C20 | a model exactly on the floor left out of the window | scripts/calibrate_surface.py:49 | **survived whole suite** (M1) |
| R21 | retired sources unattributed | src/app/workflows/rank.py:215 | killed: test_public_artifact::test_an_artifact_an_older_release_built_still_boots… |
| R22 | an older artifact's OpenRouter prices credited to LiteLLM only | src/app/workflows/rank.py:211 | killed: ::test_a_priced_payload_must_say_which_price_sources_it_serves |
| R23 | retired TB 2.0 credited as the Apache-2.0 TB 4.0 publisher | src/app/workflows/rank.py:148 | killed: ::test_an_artifact_an_older_release_built_still_boots… |
| G24 | `named_vendors` matches whole words, not prefixes | src/app/workflows/registry.py:519 | **survived whole suite** (M4; equivalent on today's live catalogue: 257 rows either way) |
| S25 | TB 4.0's row floor 10 to 1 | src/app/workflows/sources.py:177 | **survived whole suite** (M4) |
| S26 | TB 4.0's RemoteSource wired to `ingest_arc_agi_2` | src/app/workflows/sources.py:176 | **survived whole suite** (B1) |
| S27 | a retired board served on `/v1/boards` with `attribution: null` | src/app/workflows/standings.py:124 | **survived whole suite** (M2) |
| I28 | `ingest_terminalbench_4` drops every row that carries an effort | src/app/workflows/ingest.py:198 | **survived whole suite** (B1) |

Of 28 faults, 17 were killed and 11 survived the whole suite. One survivor (T08) is redundant and one (G24) is equivalent on today's data.

### BLOCKING

- **B1** `src/app/workflows/ingest.py:187-203`, `src/app/workflows/sources.py:161-179`, `tests/unit/test_arc_agi_2.py:47`.
  **Gap.** `ingest_terminalbench_4` and `ingest_arc_agi_2` are called by no test (0 references in `tests/`; every other remote source has 2 to 14).
  - The RemoteSource entries are checked by name only.
  - `test_every_surface_answers_on_the_public_artifact` seeds `computer-use` and `abstract` rows by hand in SQL.
  - The tests that read the real artifact read a gitignored, prebuilt `advisor.db` and are skipped in CI.
  - So nothing drives a TB 4.0 or ARC payload through ingest, the store's effort resolution, reconcile and `/v1/recommendations`.
  - `test_arc_agi_2.py:47` says the setting's "effort is read from it at the store", and nothing asserts it.

  **Failure scenario.** S26 (TB 4.0 wired to the ARC ingest) and I28 (TB 4.0 rows with an effort dropped, which is 18 of 21) both pass all 2693 tests.
  - Under S26 every nightly build fails at the required `terminalbench_4`. On the first install there is nothing to carry, so `computer-use` stays dark on the Mac indefinitely. On later nights the carry hides it for 30 days, and then the build fails.
  - Under I28, `computer-use` ranks 3 models instead of 21 and the board's floor moves.
  - A store-side regression in suffix effort reading for ARC names (`-thinking-120K-high`) would equally go unseen.

  **Fix.** Add one test that, for `terminalbench_4` and for `arc_agi_2`:
  - looks up the registered `RemoteSource` and calls its own `.ingest` on a `FakeRawSource` holding the existing fixtures (`_raw(FILES)`; `RECORD` plus a `-thinking-16k` and a `-thinking-120K-high` setting);
  - runs `reconcile`, then asserts the stored `(model_id, effort)` per row: `max`; `none` stored as `unspecified`; `-high` as `high`; `-thinking-16k` as `unspecified`;
  - serves `/v1/recommendations?task=computer-use` and `?task=abstract` from that database through `TestClient`, and asserts the picks come from those rows under the shipped `close_call` and `value_window`.

- **B2** `scripts/derive_arc_public_eval.py:189-204` (the `score` closure in `main()`), `docs/decisions.md` D-194 clause 3.
  **Gap.** D-194 promises "a setting scores the sum over the 120 tasks, a missing task as 0". The aggregation lives in a closure inside `main()` that needs the network, so no test reaches it, and D16 (dividing by the tasks run) survives. No test checks the committed record against the rule either.

  **Failure scenario.** 9 of the 58 kept settings ran fewer than 120 tasks. Re-deriving with D16 serves them higher, and every test stays green:
  - Claude Opus 4.6 (120K, max) moves from 74.86 to 76.78 on 117 tasks.
  - Gemini 3 Deep Think moves from 46.53 to 47.72.
  - Gemini 3 Pro moves from 27.36 to 28.30.

  The re-derivation is the step D-194's "Revisit when" asks for whenever ARC Prize publishes new runs.

  **Fix.** Lift the per-setting aggregation into a pure function `(bodies, solutions) -> entry`. Test it with a setting of 117 tasks: its score is `100 * solved / 120`, and with 113 tasks it is left out. Add a committed-record test: for every setting, `score == round(100 * solved / tasks, 4)` and `tasks_run >= min_tasks`. Both hold today (58 of 58 checked).

### MINOR

- **M1** `tests/unit/test_calibrate_surface.py:50`.
  **Gap.** The test pins `CATEGORIES` to the calibration record, but not the record to the script. C19 (window rounding) and C20 (a model on the floor) survive. The records do reproduce today.
  **Failure scenario.** A later edit to `thresholds()` leaves the shipped pair silently unreproducible, or a hand-edited record passes.
  **Fix.** For each record, assert `thresholds([s for _, s in above_floor], floor=floor, stderr=stderr)` equals the record's `close_call`, `value_window` and `candidates`. For `abstract`, also assert `round(binomial_stderr(..., tasks=120), 3) == stderr`. Add a case with a score exactly on the floor.

- **M2** `src/app/workflows/standings.py:124`, `tests/unit/test_public_artifact.py:360`.
  **Gap.** The B2 transition test asserts the retired credits, but not the retired boards' own `attribution` on `/v1/boards`. S27, which serves `epoch_arc_agi` and `epoch_terminalbench` with `attribution: null`, survives.
  **Failure scenario.** Someone re-shapes that line as `SOURCE_ATTRIBUTION.get(source)`, a natural regression. On the transition the older artifact's ARC and TB 2.0 boards are then served uncited, which breaks D-194 clause 6 ("stay attributed and credited").
  **Fix.** In that test, assert each retired board's `attribution` equals `RETIRED_EXTERNAL_ATTRIBUTION[source]`, and that `attributions` carries `PRICING_ATTRIBUTION_OPENROUTER`.

- **M3** D-194 clause 6, `docs/release-testflight.md:50-57`.
  **Gap.** "Its startup refresh replaces that artifact" has no test. I measured the gates on the real copies (`degradations` [] and `upward_anomalies` [], above), but nothing pins that the gates ignore the retired sources.
  **Failure scenario.** The declared-board set behind `fingerprint_of` comes to include any source in `scores`. The first refresh past D-194 is then refused ("epoch_arc_agi would lose 100 % of rows"), and the Mac stays on the old artifact with `abstract` and `computer-use` dark.
  **Fix.** Add a fixture test: the live artifact holds `epoch_arc_agi`, `epoch_terminalbench` and `openrouter` rows; the candidate holds `arc_agi_2`, `terminalbench_4` and `models_dev`. Assert both gates return [].

- **M4** Smaller guards with no test that fails when they go:
  - **T07** `src/app/clients/terminalbench.py:155`. No fixture has one model and agent at two efforts. If TB 4.0 lists one, the lower-effort row is silently dropped.
  - **S25** `src/app/workflows/sources.py:178`, and `minimum_rows=30` at `:171`. `test_build_artifact_safety.py:448` does not pin either floor, so a truncated GitHub listing of a few files would publish.
  - **G24** `src/app/workflows/registry.py:519`. Prefix matching (`qwen3`, `glm4.5`) is untested. It is equivalent on today's catalogue only because the resold names happen to split into whole words.

  **Fix.**
  - Add one TB fixture with the same model at `high` and `max`, and assert two rows.
  - Pin `floors["terminalbench_4"] == 10` and `floors["arc_agi_2"] == 30`.
  - Add `glm4.5-air` under `alibaba` to the reseller test, and assert it is skipped.

- **M5** Stale test text:
  - `tests/unit/test_arc_agi_2.py:47-48` still says "no evaluation date, as the dataset gives none" (since M6 every setting is dated).
  - `tests/unit/test_families.py:80` subtracts `{"litellm", "openrouter"}` where the price sources are now `litellm` and `models_dev`. The assertion holds only because `models_dev` was never in `SOURCE_ATTRIBUTION`.

  **Failure scenario.** A reader trusts the docstring and believes ARC rows are undated. The families test reads as covering a price source the build no longer has.
  **Fix.** Correct the docstring, and use `{"litellm", "models_dev"}`.

## K.9 candidates spotted outside this wave's scope

None.

## Risks queued to next M

- **R1** `src/app/workflows/categories.py` (`abstract`, `ranking_effort=None`), `data/arc-agi-2-public-eval.json`.
  **Risk.** ARC's thinking-budget suffixes (`-thinking-1k` … `-64k`, `-thinking-none`, `-thinking-minimal`) are not effort levels, so a model's whole budget sweep is stored as `unspecified`. The board stands on the best: Claude Opus 4.5 is served at 40.28, which is its 64k run, labelled with no effort. Beside it, Opus 4.6 and 4.8 are labelled `high`.
  **What would show it is real.** A reader compares Opus 4.5 with 4.6 on `abstract` and reads the gap as a model difference, when it is partly a budget difference.
  **Possible answer.** Map the largest budget of a sweep to `max`, or disclose the budget in the standing.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| B1 | Fixed. `test_d194_build_path.py` ingests TB 4.0 and ARC-AGI-2 through the `RemoteSource` the build registers, asserts the stored efforts (`none` as unspecified, `-high`/`-xhigh` read at the store), and asks `/v1/recommendations` for `computer-use` and `abstract`. S26 and I28 now fail it. | `62ede41` |
| B2 | Fixed. `setting_score` holds the rule (a task not run is 0, over all 120); a test holds the rule and every committed score. D16 is killed (replanted). | `62ede41` red, `41eb885` fix |
| M1 | Fixed. Each calibration record is recomputed from its own `above_floor`, `floor` and `stderr`; the inclusive floor and the half-point rounding are tested. C19 and C20 are killed (C20 replanted). | `62ede41` |
| M2 | Fixed. The older-artifact test asserts each retired board's citation. S27 is killed (replanted). | `62ede41` |
| M3 | Fixed. A fixture test: `main`-shaped live artifact, new-source candidate, both gates return nothing. | `62ede41` |
| M4 | Fixed. Two efforts are two rows (T07); the TB 4.0 and ARC floors are pinned (S25); family words match at a word's start (G24). T08 is redundant, as the record says. | `62ede41` |
| M5 | Fixed. Both stale texts. | `62ede41` |
| R1 | Filed as #267. | - |
