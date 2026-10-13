---
record_type: review
id: backlog-data-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# Tester review: the backlog data wave (#234, #232, #233, #230, #264, #235, #262, #269, #266)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `origin/main..7bdc4da` (23 commits, `36164d8` to `7bdc4da`). Each was read with `git show`. The
worktree is detached at `7bdc4da`, with its own `.venv` (`app.__file__` resolves inside the worktree).
**Risk tier:** MEDIUM

Inputs read: the nine issues (`gh issue view`), D-195 (`docs/decisions.md`, end of file) and the D-189 amendment
line, the three Code-Reviewer rounds with the author's dispositions, and `.agents/rules/practices.md`.

## Verdict
MINOR

Every acceptance criterion the wave touched now has a citing test that fails on a planted fault and passes on
the shipped code. Of 64 faults planted in the wave's code, the wave's own tests caught 53. This review adds 10
tests (25 cases), and they catch 10 of the 11 survivors. The 11th (F37) changes nothing in today's artifact.
Four more faults on the D-195 clauses (F67 to F70) survived the wave's suite, and the added tests catch them.

D-195's *Consequence* holds exactly on a relinked copy of the artifact. Both refresh gates pass from the
original to the relinked copy.

One finding is left open (M1). D-195 clause 4 and round 3's M4 disposition say MiniMax's `-lightning` tier is
refused on the price path. MiniMax M2.5's rule still refuses it in the regex instead. As a result, a score
under that name would derive a model of its own, served at the tier's price.

The #218 revert leaves no trace.

## Suite
- Full Python unit suite at `7bdc4da`, before any test was added:
  `.venv/bin/python -m pytest -q tests/unit -n 4 -p no:randomly`
  - Result: **2787 passed, 9 skipped** in 59 s. Coverage was 92.19% against a 60% floor.
  - The 9 skips need the owner's Epoch bundle or an OS-level offline run.
- The same suite with this review's tests: **2812 passed, 9 skipped** in 60 s.
- `ruff check` passes on the three touched test files.
- **Weakened tests.** Comparing the wave's test files with `origin/main`, three lines are removed. Each one is a
  ruling the wave makes, and none loosens a test:
  - `deepseek-v3.2-exp` now expects its own id (#232);
  - `test_a_record_without_a_build_says_unknown` becomes `..._says_unstamped_not_unknown` (#235 R2).
- **#218.** The revert leaves no trace:
  - `git diff da61494^ 2a071c0` names no `ios/` file, and `git diff origin/main..7bdc4da -- ios` is empty;
  - no commit message in the range carries a closing keyword (`fix #N`, `closes #N`), and #218 is still OPEN;
  - the remaining `#218` mentions in `ios/` (`ReadingM21Tests.swift`, `.language-allow`) are on `origin/main`
    already.

## Measurement on the relinked artifact
Method:
- The inputs were the worktree's `advisor.db` (sha256 `bc5435b0…`, unchanged at the end) and copies of it.
- On each copy, every `model_id` was set NULL in `access`, `pricing`, `scores`, `px_median` and `plan_models`, and
  `models` was emptied.
- Each copy then ran `reconcile`, `access.link`, `reconcile_plans` and `build_price_medians`, in a build's order.
  One copy used `origin/main`'s `src` and one used `7bdc4da`'s, each taken from `git archive`.
- The gates were run through `fingerprint_of(Path)` with `7bdc4da`'s code.

Results:
- **Reproduction.** Relinking with `origin/main`'s `src` reproduces the served artifact exactly: 0 score rows,
  0 price aliases, 0 medians, 0 access rows and 0 model ids differ.
- **Served against `7bdc4da`.** Every number in D-195's *Consequence* holds:
  - **135 score rows** go to the new ids: 61 to V3.2-Exp, 37 to V3.1-Terminus, 35 to K2 Thinking and 2 to
    Qwen3-Coder 30B-A3B.
  - **45 price aliases** leave K2, Qwen3-Coder and DeepSeek V3, V3.1 and V3.2 for the six new ids and K2.7 Code.
  - **3 score rows and 6 aliases** reach the point release they name.
  - **55 score rows and 1 alias** link to K2.
  - **12 aliases are refused for `speed-tier`**, and **3 Cyber aliases** leave GPT-5.5 and GPT-5.6.
  - **Six ids are new**: `deepseek-v3.1-terminus`, `deepseek-v3.2-exp`, `deepseek-v3.2-speciale`,
    `kimi-k2-thinking`, `qwen3-coder-30b-a3b` and `qwen3-coder-next`.
  - **Every median that moves** matches D-195. Kimi K2.7 Code stays 0.95/4.0.
  - Two moves the clause does not mention:
    - `azure_ai/FW-Kimi-K2.7-Code`, unlinked before, now links to K2.7 Code;
    - 17 `epoch_access` rows follow the same splits, and `gpt-5.4-cyber` and `gpt-5.5-cyber` unlink there.

    Neither contradicts the clause.
- **Gates**, from `fingerprint_of(served)` to `fingerprint_of(relinked)`:
  - `degradations` = [] and `upward_anomalies` = [];
  - `largest_board_change` = `board arena_text_polish`, 6 of 232, limit 0.25;
  - surfaces grow by 1 to 3 models each: `assistant` 207 to 210, `coding` 56 to 58;
  - surface median prices move by less than 4%: `coding` 2.15 to 2.075.

## Acceptance-criterion coverage

| Criterion | Citing test | Red→green proven |
|---|---|---|
| #234: Fireworks' `v3p1` and `v3p2` are V3.1 and V3.2, with a test per spelling | `tests/unit/test_registry.py:868`, `:876`; added `:989` | yes (F01, F02, F04, F05, F07; F03 and F06 only by the added test) |
| #232 / D-195 clause 1: K2 Thinking, K2.7 Code, Qwen3-Coder 30B-A3B and Next, V3.1-Terminus, V3.2-Exp and V3.2-Speciale are their own models | `test_registry.py:911`, `:36` | yes (F08 to F15) |
| D-195 clause 2: K2-Instruct-0905, K2's dated previews, grok-4-fast's modes, Qwen3-Max-Thinking and qwen3.7-max-preview stay gathered | `test_registry.py:911` (0905), `:925`; added `:1037` | yes (F16; F68 and F69 only by the added test) |
| #266 / D-195 clause 3: GPT-5.6 Pro is the model it runs | `test_registry.py:853` | yes (F17, F18) |
| D-195 clause 3: a Pro-mode row (`_promax`) stays `unspecified` | added `test_registry.py:1045` | yes (F67, only by the added test) |
| D-195 clause 4: a speed tier's price is refused as `speed-tier`, and its score is the model's | `test_registry.py:955`, `:972`; added `:1012` | yes (F25 to F32, F34 to F36, F38; F33 only by the added test). F37 survives as an equivalent. M2.5's `-lightning` is not met (M1). |
| #269 / D-195 clause 5: Cyber is not GPT-5.4, 5.5, 5.6 or any 5.6 variant | `test_registry.py:934`; added `:1000` | yes (F19 to F22; F23 and F24 only by the added test) |
| #269: Gemini 3.8 Flash Cyber is not Gemini 3.8 Flash | added `test_registry.py:1062` | yes (F70, only by the added test) |
| #233: an Aider architect and editor pair is skipped and counted | `tests/unit/test_aider_ingest.py:120` | yes (F40, F41) |
| #230: the outcome line carries `renamed_count` and `largest_board_change` | `tests/unit/test_refresh_board_ids.py:253` | yes (F42, F43, F45) |
| #230, round 1's M1 and M2, round 2's M4, round 3's M2: the figure judges boards as the guards do | `test_refresh_board_ids.py:300`, `:306`, `:314`, `:323`, `:339`, `:352`; added `:369`, `:392`, `:408` | yes (F44, F48 to F52; F46, F47, F53 and F54 only by the added tests) |
| #264: `make install` refuses a linked venv, or one whose editable install names another tree | `tests/unit/test_venv_owner.py:50`, `:60`, `:70`, `:79` | yes (F57, F58, F62, F64) |
| #264, round 2's M2: a Windows drive is kept, and a path in another case is the same tree | `test_venv_owner.py:89`, `:95`; added `:115` (Windows layout) | yes (F59, F60; F61 only by the added test) |
| #264, round 2's R1: every `make install` checks the venv | `test_venv_owner.py:107` | yes (F63) |
| #235 R1: a qwen-based R1 distill is not R1 | `test_registry.py:918` | yes (F39) |
| #235 R2, round 2's M3, round 3's M2: a hand-run cycle records `unstamped`, which no name deploys, and a pre-#198 record keeps `unknown` | `tests/unit/test_data_release_stamp.py:52`, `:60`, `:201`, `:214` | yes (F55, F65, F66) |
| #262: every source an answer cites is credited by `/v1/boards`, a secondary the effort filter hides included | `tests/unit/test_credits_cover_citations.py:47`, `:57` | yes (F56) |
| Round 1's B1 and round 2's B1 and K1: Kimi's and MiniMax's tiers are refused on the price path only | `test_registry.py:955` | yes (F25, F26, F28 to F32, F34, F35, F38) |
| Round 1's K1: K2's dated previews are K2 | `test_registry.py:925` | yes (F16) |
| Round 3's M4: MiniMax M2.1's `-lightning` is refused | `test_registry.py:955` | yes (F27, F31) |
| Round 3's K1: the Sol, Luna, Terra and GPT-5.4 rules refuse `cyber` | `test_registry.py:934`; added `:1000` | yes (F21, F22; F23 and F24 only by the added test) |
| Round 1's M3, round 2's M1, round 3's M1 and M3: the records and the deploy's text | docs and script text, held by no test | N/A. The text was read: `scripts/deploy_hosted_engine.sh:90` and `docs/release-testflight.md:47` and `:83` say `unstamped`. D-195's numbers were measured above. |

## Fault injection

Each fault was planted as a single exact string replacement and the bytes were then restored. Every restore
was checked by sha256: 98 restores, all matching. The first run was stopped while F03 was planted, and that
file was written back from `7bdc4da`'s bytes, with its sha256 checked (`9439c7fe…`). `git status` showed only
this review's test files afterwards.

The faults ran against the touched test files. A survivor was run again on the whole unit suite: 2787 passed
each time without the added tests, and 2802 or 2810 passed with the added tests deselected. F67 to F70 were
first run on the suite with the new tests deselected, then with them.

| Fault | File:line | Caught by |
|---|---|---|
| F01 V3.1 without `p` | `src/app/workflows/registry.py:184` | `test_registry.py:868` |
| F02 V3.2 without `p` | `registry.py:183` | `:868` |
| F03 V3's guard without `p` | `registry.py:190` | **survived**; added `:989` |
| F04 K2.5 without `p` | `registry.py:223` | `:868` |
| F05 K2.6 without `p` | `registry.py:222` | `:868`, `:955` |
| F06 K2's guard without `p` | `registry.py:226` | **survived**; added `:989` |
| F07 Terminus without `p` | `registry.py:182` | `:876`, `:911` |
| F08 no V3.2-Exp rule | `registry.py:180` | `:36`, `:911` |
| F09 no V3.1-Terminus rule | `registry.py:181` | `:911` |
| F10 no V3.2-Speciale rule | `registry.py:178` | `:911` |
| F11 no Qwen3-Coder 30B rule | `registry.py:209` | `:911` |
| F12 no Qwen3-Coder-Next rule | `registry.py:210` | `:911` |
| F13 30B joins the 480B flagship | `registry.py:209`, `:211` | `:911` |
| F14 no K2 Thinking rule | `registry.py:221` | `:911`, `:955` |
| F15 no K2.7 Code rule | `registry.py:220` | `:911`, `:955` |
| F16 K2's dated previews unlinked again | `registry.py:226` | `:925` |
| F17 Sol refuses `pro` | `registry.py:132` | `:853`, live-name mapping `:331` |
| F18 Luna refuses `pro` | `registry.py:133` | `:853` |
| F19 GPT-5.6 takes `cyber` | `registry.py:135` | `:934` |
| F20 GPT-5.5 takes `cyber` | `registry.py:136` | `:934` |
| F21 GPT-5.4 takes `cyber` | `registry.py:137` | `:934` |
| F22 Sol takes `cyber` | `registry.py:132` | `:934` |
| F23 Luna takes `cyber` | `registry.py:133` | **survived**; added `:1000` |
| F24 Terra takes `cyber` | `registry.py:134` | **survived**; added `:1000` |
| F25 `price_refusal` returns None | `registry.py:354` | `:955` |
| F26 the pricing loop skips `price_refusal` | `registry.py:1006` | `:955` |
| F27 `lightning` not a tier word | `registry.py:348` | `:955` |
| F28 `highspeed` not a tier word | `registry.py:348` | `:955` |
| F29 `fast` not a tier word | `registry.py:348` | `:955` |
| F30 `turbo` not a tier word | `registry.py:348` | `:955` |
| F31 M2.1 not tiered | `registry.py:346` | `:955` |
| F32 K2 not tiered | `registry.py:346` | `:955` |
| F33 K2.5 not tiered | `registry.py:346` | **survived**; added `:1012` |
| F34 K2 Thinking not tiered | `registry.py:346` | `:955` |
| F35 K2.7 Code not tiered | `registry.py:346` | `:955` |
| F36 every family tiered | `registry.py:354` | `:972` |
| F37 the whole alias searched, not its last segment | `registry.py:353` | **survived**. Equivalent on today's artifact: no provider prefix holds a tier word. |
| F38 a tier refused on the score path too | `registry.py:1024` | `:955` |
| F39 the distill guard without `qwen` | `registry.py:66` | `:918` |
| F40 the Aider pair kept | `src/app/clients/aider.py:95` | `test_aider_ingest.py:120` |
| F41 the Aider pair not counted | `aider.py:98` | `test_aider_ingest.py:120` |
| F42 no `renamed_count` | `src/app/workflows/refresh.py:179` | `test_refresh_board_ids.py:253` |
| F43 no `largest_board_change` in the line | `refresh.py:180` | `:253` |
| F44 the refused outcome without the figure | `refresh.py:1406` | `:306` |
| F45 the published outcome without the figure | `refresh.py:1446` | `:253` |
| F46 `baseline` replaced by None at the one call | `refresh.py:1390` | **survived**; added `:369` |
| F47 `live` passed as the baseline | `refresh.py:1390` | **survived**; added `:369` |
| F48 no gain direction | `refresh.py:321` | `:300` |
| F49 a board appearing not excused | `refresh.py:320` | `:323` |
| F50 a board the baseline emptied skipped | `refresh.py:319` | `:352` |
| F51 a zero change reported | `refresh.py:309` | `:314` |
| F52 a surface's own boards ignored | `refresh.py:313` | `:300` |
| F53 the smallest change kept | `refresh.py:309` | **survived**; added `:392` |
| F54 the loss and gain limits swapped | `refresh.py:317` | **survived**; added `:408` |
| F55 a hand-run cycle records `unknown` | `refresh.py:829` | `test_data_release_stamp.py:52` |
| F56 secondaries not credited | `src/app/workflows/standings.py:145` | `test_credits_cover_citations.py:57` |
| F57 a linked venv not refused | `scripts/venv_owner.py:58` | `test_venv_owner.py:70` |
| F58 the editable install not checked | `venv_owner.py:61` | `test_venv_owner.py:60` |
| F59 the Windows drive dropped | `venv_owner.py:43` | `test_venv_owner.py:89` |
| F60 trees compared by `resolve()` | `venv_owner.py:51` | `test_venv_owner.py:95` |
| F61 the Windows `Lib/site-packages` layout not read | `venv_owner.py:29` | **survived**; added `test_venv_owner.py:115` |
| F62 no check before pip | `Makefile:83` | `test_venv_owner.py:79` |
| F63 no check on every install | `Makefile:96` | `test_venv_owner.py:107` |
| F64 the CLI exits 0 | `venv_owner.py:75` | `test_venv_owner.py:70` |
| F65 a pre-#198 record turned `unstamped` | `refresh.py:833` | `test_data_release_stamp.py:214` |
| F66 the deploy accepts `unstamped` | `scripts/deploy_hosted_engine.sh:86` | `test_data_release_stamp.py:60` |
| F67 `_promax` read as `max` | `registry.py:395` | **survived**; added `test_registry.py:1045` |
| F68 Qwen3-Max-Thinking split | `registry.py:212` | **survived**; added `:1037` |
| F69 grok-4-fast-non-reasoning split | `registry.py:171` | **survived**; added `:1037` |
| F70 the derive grammar strips `-cyber` | `registry.py:657` | **survived**; added `:1062` |

### BLOCKING
None.

### MINOR
- **M1** `src/app/workflows/registry.py:262`: MiniMax M2.5's rule still refuses `-lightning` in the regex
  (`(?![-_ ]?lightning)`).
  - **What was claimed.** Round 3's M4 asked for this guard to move to the price path. Its disposition
    ("Fixed. `-lightning` is a speed-tier word and MiniMax M2.1 is in `SPEED_TIERED`") did half of that.
  - **Failure scenario,** probed on an in-memory artifact with `7bdc4da`'s code:
    - A price alias `minimax/MiniMax-M2.5-lightning` (the artifact has it) and a score row named
      `MiniMax-M2.5-lightning` (none today) are reconciled.
    - Both link to a derived model `minimax-m2.5-lightning`, and its price is the tier's.
    - The price is not counted as `speed-tier`.

    D-195 clause 4 says the score is M2.5's and the price is refused for its reason, and M2.1's twin does exactly
    that. Today the alias only goes unlinked, so no served number is wrong. The first board to list the
    Lightning tier would put it on surfaces as a model of its own, at twice M2.5's output price.
  - **Fix.**
    - Drop `(?![-_ ]?lightning)` from the M2.5 rule. `price_refusal` already refuses the alias, because
      `minimax-m2.5` is in `SPEED_TIERED` and `lightning` is a tier word.
    - Add `("minimax/MiniMax-M2.5-lightning", "minimax-m2.5")` to
      `test_a_speed_tiers_score_is_its_models_and_its_price_is_refused` (`tests/unit/test_registry.py:955`).
    - D-195's count of speed-tier refusals becomes 13. No median moves, because the alias is refused either way.

The survivors below are closed by this review's tests. They need no action beyond keeping the tests:
- **T1** `registry.py:190`, `:226` (F03, F06): the V3 and K2 guards' `p` held no test. Every `p` name in the
  wave's tests was taken by an earlier rule. Added `test_a_p_spelled_point_release_no_rule_names_never_falls_into_the_major`.
- **T2** `registry.py:133-134` (F23, F24): the Luna and Terra `cyber` guards held no test. Added
  `test_a_cyber_model_is_not_luna_or_terra_either`.
- **T3** `registry.py:346` (F33): K2.5's place in `SPEED_TIERED` held no test. Added
  `test_every_kimi_release_refuses_a_speed_tiers_price`.
- **T4** `refresh.py:1390` (F46, F47): round 3's M2 asked for an expiry night through the cycle. Making
  `baseline` a required argument does not stop None or `live` being passed. Added
  `test_an_expiry_night_through_the_cycle_records_the_figure_against_its_baseline`.
- **T5** `refresh.py:309`, `:317` (F53, F54): no test had two boards changing at once, and the two limits are
  equal. Added `test_of_several_boards_that_changed_the_figure_names_the_one_nearest_its_limit` and
  `test_a_loss_reports_the_loss_limit_and_a_gain_the_gain_limit`.
- **T6** `scripts/venv_owner.py:29` (F61): the Windows venv layout held no test (round 2's F9). Added
  `test_a_windows_venv_whose_editable_install_names_another_tree_is_refused`.
- **T7** D-195 clauses 2 and 3, and #269's Gemini spelling (F67 to F70): the gathered cases, the `_promax` row
  and Gemini 3.8 Flash Cyber held no test. Added `test_what_d195_keeps_gathered_stays_one_model`,
  `test_a_pro_mode_run_is_its_model_at_no_stated_effort` and
  `test_gemini_3_8_flash_cyber_derives_apart_from_gemini_3_8_flash`.

## Tests added this review
All 25 cases pass on `7bdc4da`, and each test fails on the fault it names.

- `tests/unit/test_registry.py:989` `test_a_p_spelled_point_release_no_rule_names_never_falls_into_the_major`
  (4 cases): #234, D-195 clause 4.
- `tests/unit/test_registry.py:1000` `test_a_cyber_model_is_not_luna_or_terra_either` (4 cases): #269, D-195
  clause 5, round 3's K1.
- `tests/unit/test_registry.py:1012` `test_every_kimi_release_refuses_a_speed_tiers_price` (3 cases): D-195
  clause 4.
- `tests/unit/test_registry.py:1037` `test_what_d195_keeps_gathered_stays_one_model` (7 cases): D-195 clause 2.
- `tests/unit/test_registry.py:1045` `test_a_pro_mode_run_is_its_model_at_no_stated_effort`: D-195 clause 3,
  round 1's K2.
- `tests/unit/test_registry.py:1062` `test_gemini_3_8_flash_cyber_derives_apart_from_gemini_3_8_flash` (2 cases):
  #269.
- `tests/unit/test_refresh_board_ids.py:369` `test_an_expiry_night_through_the_cycle_records_the_figure_against_its_baseline`:
  #230, round 3's M2.
- `tests/unit/test_refresh_board_ids.py:392` `test_of_several_boards_that_changed_the_figure_names_the_one_nearest_its_limit`:
  #230.
- `tests/unit/test_refresh_board_ids.py:408` `test_a_loss_reports_the_loss_limit_and_a_gain_the_gain_limit`: #230.
- `tests/unit/test_venv_owner.py:115` `test_a_windows_venv_whose_editable_install_names_another_tree_is_refused`:
  #264, round 2's M2.

## K.9 candidates spotted outside this wave's scope
- **K1** `src/app/workflows/registry.py:132`: the Sol, Luna and Terra `cyber` guards look only right after the
  variant's name.
  - **Failure scenario.** `gpt-5.6-sol-pro-cyber` canonicalizes to `gpt-5.6-sol`, so a Pro-mode spelling of the
    Cyber model would price Sol. No such name is in the artifact.
  - **Fix.** Use `(?!.*cyber)` in the three lookaheads, with a test name for each. File it only if a provider
    lists such a name.

## Risks queued to next M
None.
