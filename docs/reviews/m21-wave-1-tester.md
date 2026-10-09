---
record_type: review
id: m21-wave-1-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 1 Tester Review (the data a reader sees)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `origin/closure/m20..90b7424` (base `972b55e`). The commits are: red `b7cc0ab`, fix
`5bcae05`, red `7abf5dc`, fix `47f0c6c`, research `e7e7a1a`, review `cdc523e`, red `13b955e`, fix
`73a8e82`, reviews `d776a1e` and `3d8cf6b`, red `4183a13`, fix `90b7424`. Each was read with `git show`.
The worktree is detached at `90b7424`.
**Risk tier:** HIGH

Routing: the author and this seat are both claude-code. No second family was available. The context is
fresh. This seat read the plan's W1 rows, D-189, D-190, both review rounds and the commits. It read none of
the author's summaries before the code.

## Verdict
MINOR

The wave does what its eleven issues ask. Every mapping it changed in the artifact is one it meant to
change. The four red commits each fail only on their own tests.

Of 20 faults planted in the wave's code, the wave's tests catch 15. The 4 tests this review adds (5 cases)
catch 4 of the other 5, and they pass on the shipped code. The fifth survivor changes no name in the
artifact. Nothing blocks.

Four findings remain, all closed by the added tests:
- the deploy's escape hatch for a named release is held by no test (T1);
- the deploy's cut of the record's sha to seven characters lost its only test in this wave (T2);
- two nights in a row that do not publish are held by no test (T3);
- a refusal's log line in a later minute is held by no test (T4).

One defect of #163's class sits outside the wave's changes: Fireworks' DeepSeek V3.1 and V3.2 aliases are
priced as DeepSeek V3 (K1).

## How it was checked

- **The wave's tests.** The 12 test files the wave changed, run in the worktree: `495 passed`.
- **`make check-fast`, once, before anything was planted.** PASS in 91.4 s.
  - lint, typecheck, records, client-decls, test and swift-test all pass;
  - the test leg: `2343 passed, 25 skipped`, total coverage 92.05%, module floor PASS (47 modules);
  - coverage on the touched modules:
    - `registry.py` 99%, `main.py` 98%, `nightly.py` 99%, `refresh.py` 96%;
    - `coverage.py` 94%, `public.py` 87%;
    - `board_tables.py`, `boards.py`, `categories.py` and `sources.py` 100%.
- **The red commits.** Each was extracted with `git archive` into a scratch folder. Its own test files,
  and the files that import them, were run there with `PYTHONPATH` at that tree's `src`. Every failure is
  an assertion, or a lookup of something the fix adds (`KeyError`, `StopIteration`). None is a
  collection error.

  | red commit | files run | failed | all failures its own? |
  |---|---|---|---|
  | `b7cc0ab` | coverage, data_release_stamp, moving_aliases, nightly_refresh, public_artifact, rate_limit, registry, deploy_hosted | 25 of 367 | yes |
  | `7abf5dc` | categories, webdev_board, arena_client, sources, families | 5 of 64 | yes |
  | `13b955e` | categories, data_release_stamp, deploy_hosted, rate_limit, registry, moving_aliases, webdev_board | 37 of 331 | yes |
  | `4183a13` | data_release_stamp, deploy_hosted, rate_limit, registry, moving_aliases | 18 of 341 | yes |

  Some tests these commits add already pass at their red commit. Each guards code that was already right,
  as its commit message says: `13b955e`'s tests for M1 and M2, and `4183a13`'s tests for M3 and M4 and its
  refusal-before-derivation test for R1. The second review's plants, and this seat's R1 to R3 and L3
  below, show the M1 to M4 guards catching the faults they were written for.
- **Weakened or deleted tests.** No test that existed at `972b55e` is missing at `90b7424`. Three fix
  commits change existing tests, and each change keeps what the test holds:
  - `5bcae05` gives two `test_coverage.py` tests a 59-day window, so they still test a stale plan under
    #216's line;
  - `47f0c6c` takes `webdev` out of the unknown-config list, since the board is now read;
  - `73a8e82` moves `test_a_curated_rule_still_takes_a_latest_name` from `mistral-large-latest`, which
    now moves, to `claude-3-5-haiku-latest`.

  One test added in this wave was weakened later in it. `b7cc0ab`'s
  `test_the_deploy_stamp_names_the_release_that_built_the_data` used a 16-character record
  (`release-1234567890abcdef`, stamped `-from-1234567`). `13b955e` rewrote it to HEAD's own seven
  characters. The new refusal needed that, but it left the cut to seven characters with no test (T2).
- **Every name in `advisor.db` through both registries.** This was done on a scratch copy of the artifact
  with every `model_id` cleared.
  - The copy was reconciled with `reconcile` and `reconcile_plans` from `origin/closure/m20` (extracted
    with `git archive`), and again from `90b7424`. Then every row's model id was compared.
  - Separately, each of the 5,260 distinct names went through `split_harness`, `resolve_effort`,
    `canonicalize_with_reason` and `derive_identity`.
  - 137 names changed model, in 22 groups. Each change is intended:
    - DeepSeek: V3-0324 (2 score names from V3, 2 prices from no model), R1-0528 (16 names from R1), the
      Qwen3-8B distill (3 from R1), and two Llamagate distills that leave R1;
    - Claude Sonnet 4.6 (28 names from Sonnet 4), and `databricks-claude-sonnet-4-1`, which leaves Sonnet
      4 and joins no model;
    - Mistral Large 1.0, 2, 2.1, 3 and 4 (6, 8, 4, 11 and 5 names), and 10 undated names that now move;
    - GLM-4.6V (4 names from GLM-4.6);
    - Claude Haiku 5.5 (22 names, from the derived `claude-haiku5.5`);
    - 6 `ft:` aliases that leave GPT-4o, GPT-4.1 (all sizes) and o4-mini;
    - `grok-code-fast-1` and `grok-4-1-fast-reasoning` (7 names), which now derive nothing.
  - 18 more names change only their curated lookup, and reach the same place as before. These are 12
    V3-0324 aliases that already derived `deepseek-v3-0324`, and 6 `ft:` aliases that already reached no
    model.
  - **No changed mapping merges two models or splits one.** Each new id's names were listed in full. Then
    each board's rows were grouped by model. The only groups with two raw names that are new at HEAD are
    Sonnet 4.6's effort spellings (`_high`, `_max`, `_32K`) on the Epoch boards, which are one model.
- **Made-up names.** 45 names were probed at HEAD against the rules this wave wrote. They included:
  - free-tier and quantized suffixes, Epoch's `_32K` and `_unknown`, and `@` dates;
  - a `1m` context suffix, `24.11`, `FlashX`, and Hugging Face's `Mistral-Large-Instruct-2411`;
  - Volcengine's dated spellings.

  None merges two models. Two are dropped rather than joined: `Mistral-Large-Instruct-2411` and
  Volcengine's `deepseek-v3-250324`. Neither is in today's artifact.
- **The moved Epoch board table.** `EPOCH_BOARDS` (12 boards) and `ARENA_SLICES` hash the same at both
  commits.
- **Planted faults.** 20 faults were planted, one at a time, each as a Python byte swap in the worktree.
  - Each fault string was checked to occur exactly once before it was planted.
  - The 12 test files the wave changed were then run with `PYTHONDONTWRITEBYTECODE=1` and a fresh, empty
    `PYTHONPYCACHEPREFIX` for each run, so no `.pyc` was read.
  - The original bytes were written back in a `finally`, and their sha256 compared with the hash taken
    before the plant. Every restore matched.
  - Each survivor was then run against every unit test file except the six that run install, engine
    service or UI scripts: 2,237 tests, of which 2,228 passed and 9 skipped on every survivor. The four
    that matter were then run again against this review's tests.
  - After all runs, `git status --short` shows only this review's two test files. The sha256 of each file
    after its restores:
    - `registry.py` `2623abad0a72`, `main.py` `5920a330160b`, `deploy_hosted_engine.sh` `e0869394944f`;
    - `refresh.py` `4d50cfce9b3f`, `public.py` `47700f2dcb74`, `coverage.py` `e8127e9fcecf`,
      `arena.py` `e49dda5ad084`.

## Faults planted

"Wave's tests" are the 12 test files the wave changed, at `90b7424`. "Added" are this review's 4 tests.

| # | fault | file | wave's tests | with the added tests |
|---|---|---|---|---|
| R1 | the size alternative dropped from `_NOT_A_DISTILL` | `registry.py:66` | caught (4: `test_registry.py:729`) | caught |
| R2 | the R1-0528-Qwen3-8B rule removed | `registry.py:187-188` | caught (3: `:816`) | caught |
| R3 | Sonnet 4's lookahead back to `(?![.\-]?5)` | `registry.py:98` | caught (3: `:824`) | caught |
| R4 | R1-0528 loses Volcengine's `250528` | `registry.py:190` | caught (`:838`) | caught |
| R5 | R1 loses `(?![a-z])` (the R1T Chimeras back on R1) | `registry.py:194` | caught (2: `:832`) | caught |
| R6 | `glm-4.6v` back to `(?!\w)` (Epoch's `_32K`) | `registry.py:217` | caught (2: `:801`) | caught |
| R7 | Large 4 loses its minor-version refusal | `registry.py:226` | caught (2: `:845`) | caught |
| R8 | the fine-tune refusal reads the whole name, not the last route segment | `registry.py:345` | caught (`:708`) | caught |
| R9 | `mistral-large` dropped from `MOVING_ALIASES` | `registry.py:558` | caught (5: `test_moving_aliases.py:22`, `test_registry.py:774`) | caught |
| R10 | `qwen` dropped from `_NOT_A_DISTILL` | `registry.py:66` | **survived**, 2,237 tests too | survived (equivalent on all 5,260 names; R1 below) |
| L1 | every path charged to the questions count | `main.py:828` | caught (4: `test_rate_limit.py:331`, `:364`, `:392`, `:401`) | caught |
| L2 | a new minute keeps the "logged" flag | `main.py:312` | **survived**, 2,237 tests too | caught (`test_rate_limit.py:431`, T4) |
| L3 | a new minute keeps the standings count | `main.py:312` | caught (2: `:348`, `:417`) | caught |
| D1 | the acceptance compared with the short sha, not the record's release | `deploy_hosted_engine.sh:85` | **survived**, 2,237 tests too | caught (`test_data_release_stamp.py:122`, T1) |
| D2 | the record's sha not cut to seven characters | `deploy_hosted_engine.sh:71` | **survived**, 2,237 tests too | caught (2: `test_data_release_stamp.py:138`, T2) |
| D3 | a missing record read as `unknown` | `deploy_hosted_engine.sh:62` | caught (`test_data_release_stamp.py:98`) | caught |
| F1 | a cycle not published carries the previous cycle's builder, not the served one's | `refresh.py:796` | **survived**, 2,237 tests too | caught (`test_data_release_stamp.py:153`, T3) |
| F2 | the survivor check ignores the copies | `public.py:91` | caught (`test_public_artifact.py:335`) | caught |
| C1 | a plan's evidence stale at day N (two 90-day lines again) | `coverage.py:207` | caught (2: `test_coverage.py:230`, `:436`) | caught |
| A1 | the WebDev client built on the `text` config | `arena.py:465` | caught (2: `test_sources.py:150`, `:174`) | caught |

The wave's tests catch 15 of 20 (75%). With the added tests, 19 of 20 are caught. The four plants that
survived the second review (R1, R2, R3 and L3 here) are now caught by `4183a13`'s tests. No mutation runner
is wired for this stack, so there is no kill rate beyond this table.

## Acceptance-criterion coverage

| Issue / criterion | Code | Citing tests | Result |
|---|---|---|---|
| #163 (REQ-CAN-001, D-189 clause 1) | `registry.py:66`, `:86`, `:95-98`, `:179-195`, `:214-235` | `test_registry.py:697`, `:729`, `:763`, `:774`, `:781`, `:801`, `:816`, `:824`, `:832`, `:838`, `:845` | GREEN; K1 is outside the changed rules |
| #164 (D-189 clause 2) | `registry.py:557-562` | `test_moving_aliases.py:163` | GREEN |
| #165 (D-189 clause 3) | `registry.py:343-346` | `test_registry.py:708` | GREEN |
| #124 | none in this wave | `test_attribution_terms.py:45`, `:54`, `:63` (M19-W1) | GREEN |
| #185 (REQ-SRC-010, D-190) | `arena.py:102-106`, `:459-465`; `sources.py:226-235`; `categories.py:208-224`; `families.py:31`, `:62`; `rank.py:77` | `test_webdev_board.py:24`, `:33`, `:39`, `:45`; `test_categories.py:543`, `:555`; `test_sources.py:150`, `:174` | GREEN |
| #198 (REQ-REL-003) | `refresh.py:789-797`, `:911-913`; `nightly.py:97-99`; `deploy_hosted_engine.sh:55-101` | `test_data_release_stamp.py:37`, `:52`, `:57`, `:67`, `:85`, `:98`, `:111`; `test_nightly_refresh.py:800`; added `test_data_release_stamp.py:122`, `:138`, `:153` | GREEN (T1 to T3) |
| #205 (REQ-REL-001) | `public.py:47-52`, `:89-92` | `test_public_artifact.py:335` | GREEN |
| #214 | `boards.py:15`; `board_tables.py` | `test_nightly_refresh.py:783` | GREEN |
| #216 (D-188 clause 4) | `coverage.py:205-207` | `test_coverage.py:436`, beside `:306` for a source | GREEN |
| #228 (REQ-REL-004) | `main.py:211-224`, `:297-323`, `:825-829` | `test_rate_limit.py:364`, `:374`, `:384`, `:392`, `:401`, `:417`; added `:431` | GREEN (T4) |
| #166 | `docs/research/m21-w1-first-nights-after-m19-w1.md` | none (a reading of three nights) | met; #230 |

## Red→green on reported symptoms

- #163, #164, #165, #205, #214, #216, #228 and #198's record were red at `b7cc0ab` (25 failures) and green
  at `5bcae05`.
- #185 was red at `7abf5dc` (5 failures) and green at `47f0c6c`.
- The first review's B1 to B3, K2, M4 and R1 were red at `13b955e` (37 failures) and green at `73a8e82`.
- The second review's M1, M2, K2, R1 and R2 were red at `4183a13` (18 failures) and green at `90b7424`.
- Claude Haiku 5.5's rule has no red commit of its own. Its red was `test_display_names.py` on the
  refreshed artifact (`47f0c6c`'s message). At `7abf5dc` neither of its spellings matches a rule, so its
  test, added in `47f0c6c`, would have failed there.

## Mocks / contract tests

- LMArena's WebDev board reads through the one Arena client and the canonical fake (`FakeRawSource`,
  `test_arena_client.py:412`). The board's live shape was read once by
  `scripts/calibrate_board.py --config webdev` (`docs/research/m21-w1-webdev-calibration.json`, 140
  rows). The floor of 70 is pinned against the measured 141 (`test_arena_client.py:370`, `:375`). OK.
- No other integration is new.

## Findings

### BLOCKING
None

### MINOR

- **T1** `scripts/deploy_hosted_engine.sh:84-90`, `tests/unit/test_data_release_stamp.py:85-94`. The
  deploy's escape hatch for data a named release built is held by no test.
  - **Failure scenario.**
    - The refusal tells the owner to deploy anyway with `DEPLOY_ACCEPT_DATA_FROM=<the record's release>`,
      and the runbook says the same (`docs/release-testflight.md:25`).
    - The only acceptance test uses `unknown`. There the record's value and the short sha are both
      `unknown`, so the test cannot tell them apart.
    - Planted D1 compares the acceptance with the short sha (`$FROM`) instead of the record's release
      (`$DATA_BY`), and none of 2,237 tests fails.
    - Under D1, the owner's pasted `DEPLOY_ACCEPT_DATA_FROM=release-1234567` is refused. Nothing would
      catch a change that let `unknown` accept any data either.
  - **Fix.** Added `test_the_owner_accepts_the_release_the_refusal_names_and_unknown_never_stands_for_it`
    (`tests/unit/test_data_release_stamp.py:122`). With a record naming `release-1234567`:
    - `unknown` is refused, and the refusal names the release to accept;
    - that release deploys, stamped `-from-1234567`.

    It catches D1. The author commits it.

- **T2** `scripts/deploy_hosted_engine.sh:71`, `tests/unit/test_deploy_hosted.py:48`. The cut of the
  record's sha to seven characters is held by no test since `13b955e`.
  - **Failure scenario.**
    - The Mac's engine is stamped `release-<RELEASE>` (`scripts/engine_service.sh:36`).
    - RELEASE holds what `git rev-parse --short origin/main` printed at install
      (`scripts/install_engine_service.sh:109`, `:127`). Git lengthens that past seven characters as a
      repository grows: it prints eight from 16,384 objects. This repository holds about 12,400
      (`git count-objects -v`), and prints seven today.
    - `b7cc0ab`'s stamp test used a 16-character record. `13b955e` rewrote it to HEAD's own seven
      characters, and nothing else checks the cut.
    - Planted D2 drops the cut, and none of 2,237 tests fails. Under D2, once the repository crosses that
      size, every deploy refuses the data HEAD's own release built.
  - **Fix.** Added `test_a_longer_spelling_of_heads_release_is_heads_data` (`:138`). Records of 9 and 40
    characters for HEAD deploy, stamped `-from-<first seven>`. It catches D2.

- **T3** `src/app/workflows/refresh.py:796-797`, `tests/unit/test_data_release_stamp.py:37-49`. Two nights
  in a row that do not publish are held by no test.
  - **Failure scenario.**
    - The record test runs published, refused, published.
    - Planted F1 carries forward the previous cycle's `built_by` instead of its `served_built_by`, and none
      of 2,237 tests fails.
    - Under F1, the Mac moves to a new release and then has two failed or refused nights, for example a
      source that is down two nights running. The second record names the new release as the builder of
      the old artifact still served.
    - The deploy then ships the old release's data under the new stamp without a word, which is #198's
      defect.
  - **Fix.** Added `test_nights_not_published_in_a_row_keep_naming_the_served_build` (`:153`). One build
    publishes. Then another build has a failed, a refused and a failed night, and each record still names
    the first build. It catches F1.

- **T4** `src/app/adapter/main.py:311-318`, `tests/unit/test_rate_limit.py:175-183`. That a later minute's
  refusal is logged again is held by no test.
  - **Failure scenario.**
    - #228 keeps a "refusal logged" flag in the client's entry, because a refused request is no longer
      charged.
    - Planted L2 keeps that flag when a new minute resets the counts, and none of 2,237 tests fails.
    - Under L2, a client refused in one minute is never logged again while its entry lives. A scraper
      that comes back every minute is seen once.
    - The W5 review's M4 asked that a refused client be seen once per window.
  - **Fix.** Added `test_a_refusal_in_a_later_minute_is_said_again` (`tests/unit/test_rate_limit.py:431`).
    A client refused in two minutes is logged once in each. It catches L2.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/registry.py:177-178`, `:183-184`. Fireworks' DeepSeek V3.1 and V3.2 aliases
  are priced as DeepSeek V3.
  - **Failure scenario.**
    - Fireworks spells a point release with `p`: `deepseek-v3p1`, `deepseek-v3p1-terminus`,
      `deepseek-v3p2`.
    - The V3.1 and V3.2 rules read only `[.\-]`. V3's lookahead `(?![.\-]?\d)` does not refuse `p1`, so
      all three aliases take V3's rule.
    - In the refreshed artifact, V3's price median is 0.56/1.25. Without the three aliases it would be
      0.89/1.0, measured with `build_price_medians` on a scratch copy.
    - V3 is ranked on `arena`, the text slices and `aider`, so a reader is told V3 costs 37% less per
      input token than its own prices say.
    - This is #163's class (a later release's rows on its predecessor), in the rule this wave edited. The
      mapping is the same at `972b55e`, so the wave did not cause it.
    - It is not in #232's list, because #232's query reads scores and these are prices. Volcengine's
      `deepseek-v3-250324` (V3-0324) reaches no rule either. Unlike R1's `250528`, it is dropped rather
      than joined, and it is not in today's artifact.
  - **Fix.** `/file-issue` it. Read `[.\-p]` in the V3.1 and V3.2 rules, as the V4 and GLM-5 rules already
    do, and `(?![.\-p]?\d)` in V3's. Add a red test with the three Fireworks aliases.

## Risks queued to next M

- **R1** `src/app/workflows/registry.py:66`. The `qwen` alternative in `_NOT_A_DISTILL` is held by no
  test.
  - **The risk.** Planted R10 drops it, and none of 2,237 tests fails. Reconciled with R10, the artifact
    changes no row and no name: every distill in today's sources also carries `distill` or a listed size.
    So the clause guards a spelling no source uses yet. This review wrote no test, because only a made-up
    name would reach the clause.
  - **What would show it is real.** A host alias that names a DeepSeek distill by its base without a size
    or `distill`, for example `deepseek-r1-qwen3`, joining R1's price median.

- **R2** `scripts/deploy_hosted_engine.sh:70-73`, `:101`. An accepted builder that is not `release-*` is
  stamped `-from-unknown`.
  - **The risk.** An engine run by hand (`dev-<sha>`, `scripts/engine_service.sh:43`) that the owner
    accepts by name gets the same `/health` stamp as a record from before #198. The stamp then cannot say
    which of the two shipped.
  - **What would show it is real.** A hosted `/health` build ending `-from-unknown` while the Mac's record
    names a `dev-` build.

## Tests added/extended this review

All four are uncommitted in the worktree. They pass on the shipped code (`89 passed` over
`test_data_release_stamp.py`, `test_rate_limit.py` and `test_deploy_hosted.py`), and `ruff check` passes.
- `tests/unit/test_data_release_stamp.py:122`
  `test_the_owner_accepts_the_release_the_refusal_names_and_unknown_never_stands_for_it`: #198, REQ-REL-003
  (T1, catches D1).
- `tests/unit/test_data_release_stamp.py:138` `test_a_longer_spelling_of_heads_release_is_heads_data`
  (9 and 40 characters): #198 (T2, catches D2).
- `tests/unit/test_data_release_stamp.py:153` `test_nights_not_published_in_a_row_keep_naming_the_served_build`:
  #198 (T3, catches F1).
- `tests/unit/test_rate_limit.py:431` `test_a_refusal_in_a_later_minute_is_said_again`: #228, REQ-REL-004
  (T4, catches L2).

The author also adds the three #198 tests to REQ-REL-003's evidence cell in `docs/prd.md`, and the fourth
to REQ-REL-004's.
