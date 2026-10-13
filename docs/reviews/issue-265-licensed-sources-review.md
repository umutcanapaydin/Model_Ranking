---
record_type: review
id: issue-265-licensed-sources-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# Independent review: #265, the unlicensed sources move to licensed data (D-194)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `origin/main..015cfa4`
**Risk tier:** MEDIUM

## Verdict
BLOCKING

Two blocking findings. (1) The committed ARC-AGI-2 derivation gives a score of 0 to every setting
whose attempts ARC Prize never marked. Seven of the 24 models ranked on `abstract` are served at
0.0, and one of them provably solved tasks. (2) Engine code from this range refuses to start on any
artifact built by `main`'s code. On the owner's Mac the install then rolls back, and the startup
refresh that would repair the artifact never runs.

How the review was done. I read all eleven commits (`git log origin/main..015cfa4` lists 11, not
13) against D-194, D-185, D-188 and D-193. I made 17 read-only GETs: models.dev once, GitHub's
listing plus two TB 4.0 submissions, and the Hugging Face dataset's info, card and ten task files.
I ran the parsers over the live payloads and the new preflight over a copy of the owner's served
artifact. I planted 20 faults, each restored from its bytes and checked by sha256: 13 were killed
and 7 survived (M3). `git status` was clean at the end. The wave's unit tests pass (201), and
`coverage_floor --derive` matches the skip budget of 85.

### BLOCKING

- **B1** `scripts/derive_arc_public_eval.py:56-66` (`task_score`), `data/arc-agi-2-public-eval.json`, `docs/decisions.md:4839`.
  **Problem.** The derivation scores a pair as solved only when `correct is True`. 38 settings
  have no `results.json`. Some of them carry marks (GPT-5.4, Kimi K2.5, GLM-5 and others), but in
  others ARC Prize never scored the attempts: the field is `null`, not `false`. The derivation reads
  `null` as "wrong". At revision `026789c1`, these settings are committed at `score: 0.0`: Claude Sonnet 4.5 (all five thinking budgets, including 32k at $100),
  Claude Haiku 4.5 (five budgets), Claude 3 Haiku, GPT-4.1 (three sizes), GPT-4o, GPT-5 Pro ($961),
  Grok 4 Fast, and Qwen3 235B Instruct 2507.
  **Measured.**
  - `claude-sonnet-4-5-20250929-thinking-32k/135a2760.json`, `gpt-5-pro-2025-10-06/135a2760.json`
    and `grok-4-fast-reasoning/135a2760.json` have `correct: None` on both attempts. The
    `claude-opus-4-5` and `gpt-5-4-high` files mark the same task `True`/`False`.
  - On task `1818057f`, GPT-5 Pro's two attempts are equal to the answer `gpt-5-4-high` is marked
    correct for. GPT-5 Pro solved it, and the committed derivation still gives it 0.
  - The built artifact ranks 7 of `abstract`'s 24 models at exactly 0.0 (Claude 3 Haiku, Claude
    Haiku 4.5, Claude Sonnet 4.5, GPT-4o, GPT-5 Pro, Grok 4 Fast, Qwen3 235B), all from unscored
    folders.
  **Failure scenario.** A reader asking a puzzle question sees GPT-5 Pro and Claude Sonnet 4.5
  ranked last with "0 % correct", a measurement nobody made.
  - The zeros also lower `abstract`'s floor (`top_third` of the board) and the stderr median (M1).
  - The records claim the opposite: D-194's table says "each attempt marked `correct`", and
    `docs/process-log.md:784` says the other settings are "scored from their attempts".
  - `tests/unit/test_arc_agi_2.py:81-88` pins the behaviour: any non-`True` mark counts as unsolved.
  **Fix.**
  - In `task_score`, tell a pair whose attempts carry no boolean `correct` apart from a wrong pair.
    Leave a setting with unscored attempts out of the record, as `left_out_as_unscored`, or score it
    against ARC-AGI-2's published public-evaluation solutions.
  - Re-derive at the same revision, re-run `calibrate_surface.py`, and correct D-194's table, its
    cost line ("ranks 24 models") and the process log.
  - Add a test that a `null` mark is never a 0.

- **B2** `src/app/workflows/rank.py:89-105`, `src/app/workflows/board_tables.py:45-53` (the removed `epoch_terminalbench`/`epoch_arc_agi` citations), `src/app/workflows/standings.py:107`, `src/app/workflows/serving_bounds.py:81`.
  **Problem.** `board_standings` raises on any evidence source missing from `SOURCE_ATTRIBUTION`,
  and the boot check (`validate_startup_config`, then `_egress_problems`, then
  `standings_problem`) turns that into a refused start.
  **Measured.** I copied the owner's served artifact (built by `main`: `epoch_arc_agi` 245 rows,
  `epoch_terminalbench` 59, `openrouter` 433). I then ran `scripts/engine_service.sh`'s own
  preflight snippet with this range's code (`APP_ENV=test`). It printed
  `MODEL_RANKING_DB cannot publish /v1/boards: unattributed evidence source 'epoch_arc_agi'; add it to SOURCE_ATTRIBUTION`.
  **Failure scenario.**
  1. The owner runs `scripts/install_engine_service.sh` for the merged release.
  2. The persistent `data/advisor.db` still holds the retired sources, so the wrapper prints
     "REFUSED to start" and exits 1.
  3. The install waits 60 s for `/health`, then rolls `current` back to the previous release.
  4. The refresh that would rebuild the artifact is owned by the engine ("since #258 the engine
     starts that refresh itself", `docs/release-testflight.md:44`), so it never runs. The new
     release cannot be installed without a hand refresh, and the runbook does not say so.

  The same holds in the other direction. Once a new-code refresh publishes, an older release
  refuses that artifact (`terminalbench_4`, `arc_agi_2` unattributed), so the install's own rollback
  path is closed.
  The hand refresh also has nothing to carry for the three new names. They are required by default
  (`sources.py:140,167,174`), so one GitHub or models.dev failure in that first build is a
  `BuildError`, not a carried night.
  **Fix.**
  - Keep the two retired citations, and their `arc_prize`/`terminal_bench` credits as "retired",
    attributed for one release, so an artifact built by `main` boots and is replaced by the startup
    refresh. Or have `board_standings` skip, and log, sources that no build declares any more.
  - Add a test that builds a fixture artifact holding `epoch_arc_agi`, `epoch_terminalbench` and
    `openrouter` rows, and asserts `standings_problem` returns None under this code.
  - State the transition in `docs/release-testflight.md`.

### MINOR

- **M1** `docs/research/d194-abstract-calibration.json:46`, `src/app/workflows/categories.py:210`. `abstract`'s `close_call` of 4.1 comes from a stderr (2.066) that is the median binomial stderr over all 61 derived settings.
  - **Why it is too small.** 21 of those settings sit at 0.0 (stderr 0), most of them falsely
    (B1), and the rest are far below the floor. The script's own rule says the surface is sized on
    the ranked population (`calibrate_surface.py:8-15`). Over the 9 models above the floor, the
    median binomial stderr is 4.39, which gives a `close_call` of 8.8.
  - **What a binomial stderr can and cannot claim.** Over 120 tasks with partial credit it is a
    fair first approximation of sampling noise. But it says nothing about run-to-run variance, and
    a population of zeros drives it to 0.
  - **Effect.** The window is unchanged (the 12.2-point gap is wider than either value). But Grok
    4.20 and GPT-5.2 Pro, and Claude Opus 4.5 and GPT-5.2, are called decisively at margins inside
    the board's noise.
  - **Fix.** Have `calibrate_surface.py` compute ARC's stderr from the ranked population above the
    floor, and record that population. Re-run it after B1.

- **M2** `src/app/clients/terminalbench.py:63`. The `download_url` check is a string prefix test, but httpx removes dot segments before the request.
  - **Measured.**
    `https://raw.githubusercontent.com/harbor-framework/terminal-bench/../../evil/repo/main/x.json`
    passes `startswith(_RAW_PREFIX)` and is requested as
    `https://raw.githubusercontent.com/evil/repo/main/x.json`.
  - **What it would take.** A listing GitHub itself altered, so the risk is defence in depth. The
    docstring promises "a listing that points anywhere else is refused". A sibling repository whose
    name shares the prefix (`terminal-bench-x`) is correctly refused, thanks to the trailing slash.
  - **Fix.** Check `httpx.URL(link).path` (normalised) against
    `/harbor-framework/terminal-bench/<ref>/leaderboard/submissions/`. Or build the raw URL from an
    `entry["name"]` matched against `^[A-Za-z0-9._-]+\.json$`. Add the `..` case to the test.

- **M3** `src/app/clients/terminalbench.py:52-59,93-94`, `src/app/clients/models_dev.py:57,100`. Seven planted faults survive the whole wave suite.
  - The `MAX_SUBMISSIONS` cap removed.
  - The unsupported-effort skip removed. Its own comment says that row "would fail the whole
    source at the store".
  - The `type == "file"` filter removed.
  - The listing-is-a-list refusal removed.
  - `models_dev._made_by` without its `"/" not in model_id` clause.
  - `context` accepting a bool.
  - `parse_arc_agi_2`'s `min_tasks` fallback changed to 0.

  **The slash clause is load-bearing on today's catalogue.** Without it, the parser reads
  `thinkingmachines/inkling-small` from Arcee's entry as Arcee's model (Thinking Machines has no
  family word), and NVIDIA's `nvidia/nemotron-3-*`.
  **Fix.** One test for each, the slash rule with the live Arcee case as its fixture.

- **M4** `docs/decisions.md:4889-4892` (D-194, "The cost"). The ADR explains the price rises as "an open-weight model's second price is now its maker's list price, not the cheapest host's".
  - **Measured against the owner's served artifact (`main`, 01:00 today).** Much of the shift is
    something else. `main` linked OpenRouter's half-price `:batch` rows to the base model (65
    aliases across 62 models; `:batch` is a registry decoration). It also linked
    `openai/gpt-5.6-sol-pro` to GPT-5.6 Sol (K1).
  - **Budget crossings.** Removing those rows moves Claude Opus 5.5 from a blended $7.40 to $8.40,
    out of the `medium` budget ($8, a hard pre-score filter). GLM-5.1, GLM-5.2, GLM-5.3 and Qwen2.5
    VL 72B move out of `low` ($2). GPT-5.6 Sol rises from $5.50 to $8.00.
  - **Why it matters.** These are reader-visible answer changes, and the record names neither the
    cause nor the crossings.
  - **Fix.** Name both causes in the cost section, and list the models that cross a `BUDGETS` edge.

- **M5** `src/app/workflows/registry.py:495-502` (`_FAMILY_VENDORS`). The vendor of `hy4-preview` regresses from Tencent to "Other".
  - **Cause.** Only OpenRouter's `tencent/hy4-preview` route named it. models.dev lists no Tencent
    maker entry (only its coding and token plans), and the remaining LiteLLM alias is
    `aihubmix/hy4-preview`.
  - **Effect.** A served model's vendor is wrong on `/v1`. This is the only one of the
    route-to-vendor changes that went backwards. The three new routes (`upstage`, `stepfun`,
    `arcee-ai`) correctly moved `solar-pro4`, `step3.5-flash`, `step5-preview` and
    `trinity-large-thinking` from Other to their makers, and no LiteLLM alias was mis-attributed.
  - **Fix.** Add a family word for Hunyuan (for example `("hy4", "Tencent")` or a curated rule).
    Add a test that compares every served model's vendor across a source swap.

- **M6** `src/app/clients/arc_prize.py:89`, `scripts/derive_arc_public_eval.py:93-100`. The client stores `run_date=None` with the comment "the dataset dates no run". Every attempt's metadata carries `start_timestamp` (for example `2025-09-30T12:42:45Z` for Sonnet 4.5, `2026-02-27` for GPT-5.4 high).
  - **Effect.** `abstract`'s evidence is served undated, so REQ-UNC-003's ageing cannot see that
    the newest run is from early 2026.
  - **Fix.** Have the derivation record each setting's latest `start_timestamp` date, have the
    parser store it, and drop the claim.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/registry.py:132-134`. The curated rules `gpt-5.6-sol`, `gpt-5.6-luna` and `gpt-5.6-terra` have no `pro` guard, unlike `gpt-5.6`'s own rule on line 135.
  - **Measured.** `main`'s served artifact links `openai/gpt-5.6-sol-pro` and its `:batch` row to
    GPT-5.6 Sol.
  - **Failure scenario.** A Pro variant's price or score, from any source that lists it, is served
    as the base model's.
  - **Fix.** Add `(?![-_ ]?pro)` to the three rules, with a test. It is a bug, outside this wave's
    scope.

## Risks queued to next M

- **R1** `src/app/clients/models_dev.py:55-57`. The makers-only rule is a deny-list. A maker's entry is read unless the model id has a slash or names another vendor's family word.
  - **Today.** It holds on the live catalogue: I checked all 257 rows, and every row without a
    family word is the maker's own, such as Mistral's Pixtral and Voxtral, Meta's Muse Spark,
    Upstage's Solar and StepFun's Step.
  - **What would show the risk is real.** A maker's entry reselling a model with no known family
    word and no namespace, such as a Thinking Machines, Baidu or ByteDance model without the slash
    that catches `thinkingmachines/inkling-small` today. Its price would be filed under the
    reseller's route. Watch for a row whose vendor does not match its maker on the next catalogue.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| B1 | Fixed. An unmarked attempt is scored against ARC-AGI-2's published solution (`arcprize/ARC-AGI-2`, Apache-2.0, commit `f3283f72`); a boolean mark is kept. Re-derived at revision `026789c1`: GPT-5 Pro 13.3, Claude Sonnet 4.5 (32k) 14.7. The comparison agrees with 16,664 of 16,681 marks. The red test's "no setting at 0" was wrong (Claude 3 Haiku measures 0) and names the review's cases instead. | `e42ee05` red, `1f70333` fix |
| B2 | Fixed. The retired sources stay attributed and credited as D-193 credited them; the engine boots on `main`'s artifact (checked on the owner's served copy). The runbook states the first install and the one-way rollback. | `e42ee05`, `1f70333`, this docs commit |
| M1 | Fixed. `--binomial-tasks` takes the stderr over the models above the floor: close_call 8.8, window 9.5. | `1f70333` |
| M2 | Fixed. The normalised path must be in the submissions directory; `..`, another directory and a sibling repository are tested. | `e42ee05`, `1f70333` |
| M3 | Fixed. A test for each of the seven survivors. | `e42ee05` |
| M4 | Fixed. D-194's cost names both causes and every budget edge crossed, measured. | this docs commit |
| M5 | Fixed. Hunyuan's family words name Tencent. | `e42ee05`, `1f70333` |
| M6 | Fixed. Each setting carries its latest attempt's date, and the row stores it. | `e42ee05`, `1f70333` |
| K1 | Filed as #266. | - |
| R1 | Accepted as a risk. The deny-list is what the catalogue allows: models.dev names no maker for a model. Watched by the contract test's maker list and the review's check. | - |
