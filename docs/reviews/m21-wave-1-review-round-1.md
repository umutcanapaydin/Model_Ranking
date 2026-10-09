---
record_type: review
id: m21-wave-1-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 1 Code Review (the data a reader sees)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `origin/closure/m20..e7e7a1a` (base `972b55e`; red `b7cc0ab`, fix `5bcae05`, red `7abf5dc`, fix `47f0c6c`, research `e7e7a1a`)
**Risk tier:** HIGH

Routing: author family claude-code (local lane, per the commits' `GP-Agent`), reviewer family the
same. No second family was available to this seat. The context is fresh: this seat read only the
plan, the issues, the ADRs and the diff.

## Verdict
BLOCKING

Most of the wave is sound:
- the rate limiter's own window and the uncharged refusal;
- the survivor check;
- the 90-day line;
- the board table's move;
- the refresh record's build fields;
- `web-dev`'s licence, attribution and family.

The deploy still refuses anything but `origin/main`'s tip (`scripts/deploy_hosted_engine.sh:36-47`,
unchanged).

The registry rules are the problem. They do not meet the wave's first criterion: "a release's later
snapshot … stays with its own model" (#163, D-189 clause 1). The artifact this wave refreshed still
ranks DeepSeek R1 on R1-0528's ECI score (B1). The new R1-0528 rule takes an 8B distill as R1-0528
(B2). D-189 also says no other family was ranked twice by one board, but the same artifact shows
Mistral Large and Claude Sonnet 4.6 (B3). Each fix is a regex change and a parametrized test.

## How it was checked

- **Plan and issues first.** Read `docs/plans/m21-plan.md` §1 row W1, §2 W1 and §5, D-189 and D-190,
  and issues #163, #164, #165, #124, #185, #166, #198, #205, #214, #216 and #228. Then read each
  commit with `git show`.
- **Names through both registries.** Ran 44 names through the base registry
  (`origin/closure/m20:src/app/workflows/registry.py`) and through HEAD's, using
  `canonicalize_with_reason` and `derive_identity`.
- **The refreshed artifact, read only.** Queried the worktree's `advisor.db`: DeepSeek, Grok,
  `ft:`, Mistral Large, Sonnet and GLM rows and prices. Then listed every board that ranks one
  model under two or more raw names.
- **An artifact older than this wave.** Copied `advisor.db` to the scratchpad and deleted its 140
  `arena_webdev` rows. Then asked `/v1/recommendations?task=web-dev` and `/v1/categories` through
  `TestClient`.
- **Tests.**
  - The unit suite passed: 2113 passed, 9 skipped.
  - The files that run the deploy, install, engine-service or UI scripts were left out. So were the
    three deploy tests in `test_data_release_stamp.py`. They run the deploy script against stand-in
    `fly` and `curl` in a scratch repository. They ran once in a first batch of 319 targeted tests
    (all passed) and were not run again.
- **Planted faults.** Planted 12 faults, each restored by its bytes and checked by sha256. After
  the restores, `git status` was clean. The files' hashes after restore:
  - `main.py` `5891122f`
  - `categories.py` `e28654b2`
  - `registry.py` `10a26141`
  - `public.py` `47700f2d`
  - `refresh.py` `4d50cfce`
  - `nightly.py` `b2d5826c`
  - `boards.py` `27469063`

| Plant | Result |
|---|---|
| `/v1/boards` shares the question window (`key = client`) | caught |
| a refused request is charged | caught (`test_a_refused_request_is_not_charged`) |
| the boards key truncated to the path: one boards window for every client | **survived** (M2) |
| `web-dev` thresholds put back to Epoch's copy's 100.0 / 6.8 | **survived** (M1) |
| the survivor check skips the copies | caught |
| a refused cycle records its own build as served | caught |
| the refresh child loses `APP_BUILD` | caught |
| the V3-0324 rule loses `(Mar 2025)` | caught |
| `boards.py` reads `EPOCH_BOARDS` through `sources` | caught |
| V3's `(0324)` exclusion removed; R1's `0528` exclusion removed | survived, but dead code: the dated rule precedes and wins (not a finding) |

## Findings

### BLOCKING

- **B1** `src/app/workflows/registry.py:177-179`. The R1-0528 rule does not read Epoch's
  `(May 2025)`, so DeepSeek R1 is still ranked on R1-0528's score.
  - **Scenario.** In the artifact this wave refreshed:
    ```
    epoch_eci | DeepSeek-R1 (May 2025) | deepseek-r1 | 141.29
    epoch_eci | DeepSeek-R1            | deepseek-r1 | 138.97
    ```
    `epoch_eci` is `everyday`'s primary board (`categories.py:146`), and a ranking takes a model's
    best row. So `everyday` ranks DeepSeek R1 at R1-0528's 141.29. This is #163's defect in the very
    family D-189 clause 1 says it fixed "whichever way a board spells its date". Epoch spells V3-0324
    as `(Mar 2025)` (handled) and R1-0528 as `(May 2025)` (not handled). The parametrized test
    (`tests/unit/test_registry.py:681-700`) has no `(May 2025)` case.
  - **Fix.** Add `\(may[-_ ]?2025\)` to the R1-0528 rule's alternatives and to R1's exclusion. Add
    `("DeepSeek-R1 (May 2025)", "deepseek-r1-0528")` to the test.

- **B2** `src/app/workflows/registry.py:177`. The new R1-0528 rule merges a different model: the
  distilled Qwen3-8B.
  - **Scenario.** `deepseek[-_ ]?r1[-_ ]?(?:0528|\(0528\))` matches the distilled Qwen3-8B
    (`DeepSeek-R1-0528-Qwen3-8B`). In the artifact:
    - three board rows sit on `deepseek-r1-0528`: `epoch_aime` 43.9, `epoch_gpqa` 9.3 and
      `epoch_chess` 3.0;
    - two prices sit in its median: `fireworks_ai/…/deepseek-r1-0528-distill-qwen3-8b` 0.2/0.2 and
      `novita/deepseek/deepseek-r1-0528-qwen3-8b` 0.06/0.09.

    R1-0528's only chess row is the 8B distill's. `abstract`'s family (`families.py:30`) therefore
    places R1-0528 by an 8B model's score. The old R1 rule at least refused `distill` right after
    `r1`; the new rule refuses nothing. Before the wave the same names went to `deepseek-r1`, and R1
    still takes `llamagate/deepseek-r1-8b` and `llamagate/deepseek-r1-7b-qwen` at 0.1/0.2 and
    0.08/0.15.
  - **Fix.**
    - Refuse a distill after the date, in both rules: for example
      `(?![-_ ]?(?:distill|qwen|llama))` after `0528`, and a size token (`-8b`, `-7b`) on R1.
    - Test that the three spellings take no curated rule and derive a model of their own.

- **B3** `docs/decisions.md:4530-4533`, `src/app/workflows/registry.py:200` and `:90`. D-189's
  "Applied" paragraph is false, and clause 1 is not applied to two families the artifact shows.
  - **Scenario: Mistral Large.** D-189 keeps Mistral Large gathered because "none was found ranked
    twice by one board under two releases". Arena ranks `mistral-large-2402`, `-2407`, `-2411`,
    `-3` and `-4`, all as `mistral-large`, at 1176 to 1428. Its 35 price aliases run from $0.5/$1.5
    (Large 3, `mistral-large-2512`) to $8/$24 (2402 on Azure); the median is 1.34/4.045. It is
    ranked on Large 3's 1427.6 at almost three times Large 3's price. Mistral names Large 3 and
    Large 4 apart, and #163 lists `mistral-large` among the families "joined or split" by the rule.
  - **Scenario: Claude Sonnet 4.6.** The same query finds Claude Sonnet 4.6 (`claude-sonnet-4-6`,
    `Claude Sonnet 4.6`) ranked as `claude-4-sonnet`:

    | board | Sonnet 4.6's row | Sonnet 4's own row |
    |---|---:|---:|
    | `arena` | 1457.7 | 1350.8 (thinking), 1339.3 |
    | `arena_text_coding` | 1503.6 | 1414.4 (thinking), 1379.4 |
    | `epoch_eci` | 152.24 | 141.69 |
    | `arena_webdev` (the new board) | 1522.4 | none: Sonnet 4.6's is that model's only row |

    "Claude Sonnet 4" is shown with 4.6's scores, and Sonnet 4.6 never appears.
  - **Fix.** Either:
    - split per clause 1: Mistral Large 2402, Large 2 (2407 and 2411), Large 3 and Large 4, plus a
      `claude-4.6-sonnet` rule ahead of `claude-4-sonnet` (whose lookahead then excludes `[.\-]?6`),
      each with a red test; or
    - correct the Applied paragraph and file both families before #163 closes.

    In either case, add the query this seat ran to the wave's record: boards ranking one model under
    two or more raw names, read for releases named apart.

### MINOR

- **M1** `src/app/workflows/categories.py:222-223`, `tests/unit/test_categories.py:538`. `web-dev`'s
  measured thresholds are held by no test.
  - **Scenario.** Planted `value_window=100.0, close_call=6.8`, Epoch's copy's old values. Every test
    in `test_categories.py`, `test_webdev_board.py`, `test_recommend.py` and
    `test_calibrate_board.py` passed. This is the gap the M15-W3 review (m-1) and the W4 review
    (MINOR-2) closed for vision and search: "putting a corrected margin back to its old value passed
    every test".
  - **Fix.** Add `"web-dev": (9.3, 37.3)` to the pinned table, read from
    `docs/research/m21-w1-webdev-calibration.json`.

- **M2** `src/app/adapter/main.py:823`, `tests/unit/test_rate_limit.py:364`. That the boards window
  is per client is never tested.
  - **Scenario.** Planted `[:64]` → `[:11]`, which keys every client's boards window to
    `/v1/boards|`: four standings a minute for all TestFlight phones together. All 33 rate-limit
    tests passed. `test_standings_never_block_questions` uses one address.
  - **Fix.**
    - Two `Fly-Client-IP` addresses each get four boards answers in one minute.
    - Add the reverse direction: 120 questions, then a boards answer is 200.

- **M3** `docs/architecture.md:75` and `:490`, `docs/security-invariants.md:167-168`. The records
  lag the code.
  - **Scenario.**
    - The architecture still says "Six Arena boards" are optional, without `arena_webdev`.
    - The deploy diagram still stamps `release-<sha>-data-<digest>`, without `-from-<sha>`.
    - INV-88's statement gained two clauses (its own window; a refusal is not charged), but its test
      column lists neither `test_standings_never_block_questions` nor
      `test_a_refused_request_is_not_charged`.
    - INV-87's column lacks `test_a_missed_copy_of_a_left_out_source_stops_the_derivation`.

    A reader of the invariant table cannot find what holds the new clauses.
  - **Fix.** Update the four entries.

- **M4** `scripts/deploy_hosted_engine.sh:57-73`, `src/app/workflows/public.py:60`. The deploy names
  the data's release but ships it whatever it is.
  - **Scenario.** D-190's consequence ("deployed after the Mac has refreshed once") rests on the
    owner reading one echo line.
    - On an artifact with the `arena_webdev` rows removed, `/v1/recommendations?task=web-dev`
      answers `no_evidence`.
    - `/v1/categories` still names `arena_webdev` as the primary.

    So a deploy from a Mac that has not refreshed with this release ships `web-dev` dark on the
    hosted engine. It is stamped `-from-unknown` (the old record has no `served_built_by`), and
    `/health` passes. This is #198's own framing: "the check is absent, not failing".
  - **Fix.** Either the derivation refuses when a surface's primary board holds no rows (D-186:
    every surface answers on TestFlight), or the deploy refuses `from-unknown` and an older data
    release without an explicit flag.

## K.9 candidates spotted outside this wave's scope

- **K1** `docs/research/m21-w1-first-nights-after-m19-w1.md:58-62`. The follow-up that would have
  made #166's prediction checkable lives only in a research note. That follow-up is to log each
  night's `renamed` count and its largest board change. A finding written only into this file is a
  finding nobody will query. **Fix:** `/file-issue` it.
- **K2** `src/app/workflows/registry.py:198`. The `glm-4.6` rule `glm[-_ ]?4[.\-]?6` also takes
  GLM-4.6V, the vision model:
  - `arena_vision` ranks "GLM-4.6" at 1163.9, which is 4.6V's row;
  - 4.6V's rows sit beside 4.6's own on `arena` (1376.7) and `arena_text_coding` (1390.2);
  - 4.6V's prices (0.3/0.9, two aliases) sit in 4.6's median.

  This predates the wave and is the class D-189 clause 1 rules on. **Fix:** `(?!v)` after `6`, a
  red test, and file it.

## Risks queued to next M

- **R1** `src/app/adapter/main.py:293-305`. Each client now holds two keys. So the full-table rule
  ("a crowd of new clients never resets a count it holds") holds per key, not per client. While the
  10,000-key table is full of this minute's keys, a client counted only for questions is served
  `/v1/boards` uncounted, and each answer is 0.5 MB. **What would show it is real:** a test that
  fills the table, then sends N boards requests from a client already in it, and gets N 200s.

## Acceptance criteria evidence

| Criterion | Code | Test | Status |
|---|---|---|---|
| #163 (REQ-CAN-001) | `registry.py:173-179` | `test_registry.py:681-700` | **not met** (B1, B2, B3) |
| #164 | `registry.py:524-525` | `test_moving_aliases.py:161-166` | met (1) |
| #165 | `registry.py:308-311` | `test_registry.py:703-712` | met (2) |
| #124 | none in this wave | `test_attribution_terms.py` (M19-W1) | delivered by M19-W1 (3) |
| #185 (REQ-SRC-010) | `arena.py:106`; `sources.py:226-235`; `categories.py:208-224`; `families.py:31` and `:62`; `rank.py:77` | `test_webdev_board.py:24-60` | met (4) |
| #198 (REQ-REL-003) | `refresh.py:789-797`; `nightly.py:97-99`; `deploy_hosted_engine.sh:57-70` | `test_data_release_stamp.py:36-77`; `test_nightly_refresh.py:800` | met (5) |
| #205 (REQ-REL-001) | `public.py:47-52` and `:90-92` | `test_public_artifact.py:335` | met |
| #214 | `boards.py:15` | `test_nightly_refresh.py:783` | met (planted import caught) |
| #216 | `coverage.py:207` | `test_coverage.py:436` | met (6) |
| #228 (REQ-REL-004) | `main.py:815-824` and `:305-317` | `test_rate_limit.py:364`, `:374` | met; M2, R1 |
| #166 | `docs/research/m21-w1-first-nights-after-m19-w1.md` | none | met: three nights read; K1 |

Notes:
1. The artifact links no price under the two xAI ids. The `azure_ai`, `xai` and `oci` aliases all
   have a NULL `model_id`.
2. All 12 LiteLLM `ft:` aliases are unlinked in the artifact.
3. `ARENA_ATTRIBUTION` (`board_tables.py:61-64`) names LMArena and links the dataset and CC BY 4.0.
4. M1 and M4 apply. The family is one board per vote: `arena_webdev` is config `webdev`, a vote of
   its own, and `test_families.py:175` holds it. `refined_board` stays `arena_text_coding`, the
   family's board of the text vote, which is correct.
5. The main-tip refusal is held by `test_deploy_hosted.py:180`. M4 applies.
6. Every engine line now reads "more than N days" as stale: `coverage.py:256`,
   `recommend.py:275` and `:465`, and `aider.py:139`.

## Producers of hardened invariants

- **INV-88.**
  - Producers: `_limited` (`main.py:810`), `_client_key` and `_over_limit` (`main.py:276-318`).
  - Citing tests: `test_rate_limit.py:364`, `:374`, and the list at `security-invariants.md:168`.
  - Gaps: M2 (the boards window per client), R1 (the full table).
- **INV-87.**
  - Producer: `public.derive` (`public.py:60`), whose one caller is the deploy script.
  - Citing test: `test_public_artifact.py:335`.
  - Gaps: none new. The count repeats the delete's predicate, so the two can drift together.
- **REQ-CAN-001 / D-189.**
  - Producers: `canonicalize_with_reason` (`registry.py:292`), `derive_identity`
    (`registry.py:536`) and `MODEL_RULES` (`registry.py:168-180`).
  - Citing tests: `test_registry.py:696`, `:707`; `test_moving_aliases.py:162`.
  - Gaps: B1, B2, B3.

## K.8 contract drift check

Plan §5: no `/v1` field changes. `git diff origin/closure/m20..HEAD -- src/app/adapter/main.py`
adds or removes no response key (0 lines matching `"key":`). The moved symbols:
```
src/app/workflows/board_tables.py:189:class EpochBoard:
src/app/workflows/board_tables.py:234:EPOCH_BOARDS: tuple[EpochBoard, ...] = (
src/app/clients/epoch_board.py:31:from app.workflows.board_tables import EpochBoard as EpochBoard
src/app/workflows/sources.py:46:from app.workflows.board_tables import EPOCH_BOARDS as _EPOCH_BOARDS
src/app/workflows/sources.py:269:EPOCH_BOARDS = _EPOCH_BOARDS
src/app/workflows/boards.py:15:from app.workflows.board_tables import ARENA_SLICES, EPOCH_BOARDS
src/app/workflows/build.py:56:from app.clients.epoch_board import EpochBoard, parse_board, read_bundle_file
```
Verdict: OK. The client imports the client-free table, the pattern `arena.py` and
`arena_slices.py` already use.
