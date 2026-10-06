---
record_type: wave
id: m19-wave-1-close
status: draft
process_version: v6.6
date: 2026-10-06
---
# Wave-Close Checklist — M19 Wave 1, what the reader sees

**Eight issues, as the milestone plan's W1 and its two amendments name them.**

**What a reader sees.**
- #112: 74 models served under a lower-case spelling of their id are named as their makers spell
  them, each with its maker's page beside it in `registry.DISPLAY_NAMES`. The artifact test now
  names models by the build's own `reconcile`, which found 17 of them the old approximation hid.
- #129: one release is one model, dated or not, where its maker lists one snapshot: Claude 3 Haiku,
  Opus and Sonnet, Claude 3.5 Haiku, GPT-4.1 mini and nano, GPT-5, GPT-5.2 Pro, GPT-5.4 Pro, o3,
  o3-mini, o3-pro, Mistral Small 3.1 and Mistral Medium 3.5. `mistral-medium-3` joins D-166's moving
  aliases.
- #162: each GPT-5 minor release's mini, nano, chat and Codex mini is a model of its own.
- #130: `o3-mini-high` is o3-mini at high effort; a Sonar name's `-high` stays its name.
- #124 (the part #88 does not rule): Epoch's external boards credit their original sources, SWE-bench
  and Aider each carry their own licence, Creative Commons notices link their material and licence,
  and nothing claims an OpenRouter term its terms do not state.
- #101: plans break a tie as models do, the better score and then the stable id, never the name.

**What the owner sees.**
- #100 (D-179): the board guards compare a row by the model it links to, so a re-spelling refuses no
  night; an expiry night's baseline unlinks what the expiry orphans, as a build does.
- #106: a derived `latest-v` id is said in the refresh record's drift, under the source `registry`.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m19-wave-1-plan.md` (deleted in this close) and `docs/plans/m19-plan.md` §2 W1: **HIGH**, since the registry and the refresh's guards are touched and `src/app/clients/**` is a security glob (`arena.py`, `openrouter.py` changed) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #101 (`be00142`, `2283576`), #106 (`26912cc`, `0b84bf8`), #130 (`99dd07c`, `f9ee9ce`), #162 (`56af6ad`, `250da28`, `8c36386`), #129 (`74cc67a`, `2f52cec`, `40a399d`, `b4fc97c`), #100 (`373bad4`, `0b7ab37`), #124 (`73ae5bc`, `ba64b20`), #112 (`a3793f5`, `97231c9`). Each commit ran after `make check-fast`; a red commit's only failures were its own tests, except two slips in row 8 | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m19-wave-1-review.md` (`379a17a`): **MINOR**, M1–M7, K1, R1–R3, on `dd68917..a460f5e`. `docs/reviews/m19-wave-1-tester.md` (`09798ba`): **MINOR**, M1–M6, K1, R1, on `dd68917..a182a53`. Each seat had its own worktree at its range's end, its own venv from the locks and a copy of the served artifact, behind stubs refusing `launchctl`, `simctl` and `xcodebuild` (D-174) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172. The M19 closure seat reads this slice, from `docs/security-invariants.md` (INV-54, INV-57, INV-59 changed here) | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 21 faults: 18 killed (85.7 %), and with its three tests (`60fa2b0`) all 21. Each reverted in place, sha256 equal before and after. The reviewer's 7 mutants: 5 killed, and its two survivors (#101's picks and group order by name) die since `fe143e8`, replayed there with the file restored byte-identical. After the fix round the author replayed the Tester's 21 on `e53be26`, the whole unit suite each time: all 21 killed, each file restored byte-identical (sha256). The first replay stopped at its time limit with T11 planted; it was reverted in place from its spec and checked against `HEAD`'s blob before the rest ran | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | #101 through `recommend_subscription` (`test_subscribe.py::test_a_price_tie_among_plans_goes_to_the_plan_id_through_the_answer`). #100 through `refresh()` (`test_refresh_board_ids.py::test_a_re_spelled_board_publishes_and_records_the_re_spellings`). #106 through `build()` and `/health`'s `_drifted` (`test_build.py::test_a_derived_latest_v_id_is_said_in_the_drift_not_refused`). #112 by `reconcile` over the artifact's rows (`test_display_names.py::test_every_model_the_artifact_serves_is_named_by_this_code_as_a_product`). #129, #130 and #162 through `canonicalize` and `derive_identity`, the two doors `reconcile` uses, and #130 through ingest's effort (`test_registry_derived.py::test_o3_mini_high_is_stored_as_o3_mini_at_high_effort_on_the_path_a_build_takes`). #124 through the table `attributions_for` and `/v1/boards` read (`test_attribution_terms.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | `docs/security-invariants.md`: INV-54 compares a board's rows by model (D-179, `7836f15`), with `test_refresh_board_ids.py::test_what_the_board_guards_are_for_still_refuses` and `::test_an_unlinked_row_is_still_compared_by_its_name`; INV-57 gains the expiry baseline's unlinking (this close), with `::test_a_price_feeds_expiry_is_judged_against_the_links_a_build_would_make`; INV-59 (`7836f15`) gains `test_moving_aliases.py::test_mistral_medium_3_is_an_alias_of_a_later_release` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None. Twice the author set uncommitted work aside with `git stash push` on named files to measure a red commit against committed code, after copying each file to the scratchpad; after `git stash pop` each compared byte-identical with its copy (`cmp`). **Two slips**, both caught before any push: `c673dda` was first committed while `make check-fast` failed (a shell `&&` chain ran the commit after a passing `grep`), and `0b7ab37` was first committed with a lint failure. Each was amended locally once the gate ran clean; three unpushed commits were amended in all, and nothing pushed was rewritten. The session started outside the repository, so its hooks were not loaded (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | D-179's board identities: `serving_summary` for each surface's own board (`floors.board_rows`) and each declared board, `_served_without` on an expiry night, and `refresh()`'s record of re-spellings, each with a test in `test_refresh_board_ids.py`. One release, one model: `canonicalize` (pricing and score names, through `reconcile`), `access.link` (`test_access.py::test_names_link_to_the_models_their_scores_link_to_and_a_disagreement_gives_no_value`) and `reconcile_plans` (no new test; measured, no plan row changes model) | ✅ |
| 9b | Scope & draft PR | Delivered: #101, #106, #130, #162, #129 (with GPT-5, Mistral Small 3.1 and Mistral Medium 3.5, by the milestone plan's W1-close amendment), #100, #112. In part: #124 (where attribution must appear waits on #88). Filed: #163, #164, #165, #166. Draft PR on `wave/m19-w1` against `main`, opened in this close | ✅ |
| 9a | Economy | `git diff --shortstat dd68917 HEAD`: 28 files changed, 1862 insertions(+), 132 deletions(-) (before this close's own records). Over the ~400-line guide: the code is 9 files changed, 387 insertions(+), 85 deletions(-), and most of it is the name table (74 names, each with its source); the rest are tests and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. The per-wave security pass is not run by rule (D-172). Bypass: none; the two slips are in row 8 | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-06 · Wave commit range: `dd68917..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `a182a53` |
| review M2 | fixed `fe143e8` |
| review M3 | fixed `de5eac2` |
| review M4 | fixed `802a1fd` |
| review M5 | fixed `a182a53` |
| review M6 | fixed `a182a53` |
| review M7 | fixed `6194257` |
| review K1 | #165 |
| review R1 | #166 |
| review R2 | fixed `7ee3567` |
| review R3 | refused — the phone keeps nothing by model id that outlives a fetch: its stored state is the language, the gap register (questions, not models) and the standings cache, which each fetch replaces whole (`StandingsStore.swift`); #138 (W2) keys cards on the ids served then |
| tester M1 | fixed `60fa2b0` |
| tester M2 | fixed `60fa2b0` |
| tester M3 | fixed `60fa2b0` |
| tester M4 | fixed `e991903` |
| tester M5 | fixed `1ef03ae` |
| tester M6 | fixed `e53be26` |
| tester K1 | fixed `1ef03ae` |
| tester R1 | #166 |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        README.md docs/decisions.md docs/plans/m19-plan.md docs/plans/m19-wave-1-plan.md docs/prd.md docs/reviews/m19-wave-1-review.md docs/reviews/m19-wave-1-tester.md docs/security-invariants.md src/app/clients/arena.py src/app/clients/openrouter.py src/app/workflows/board_tables.py src/app/workflows/build.py src/app/workflows/floors.py src/app/workflows/rank.py src/app/workflows/refresh.py src/app/workflows/registry.py src/app/workflows/subscribe.py tests/unit/test_access.py tests/unit/test_attribution_terms.py tests/unit/test_build.py tests/unit/test_display_names.py tests/unit/test_moving_aliases.py tests/unit/test_pareto_dominance.py tests/unit/test_recommend.py tests/unit/test_refresh_board_ids.py tests/unit/test_registry.py tests/unit/test_registry_derived.py tests/unit/test_subscribe.py docs/plans/m19-wave-1-close.md (and the plan deleted)
Mutant set author: the Tester seat (21 faults) and the Code-Reviewer seat (7); the author's replays are supporting evidence only
Observed RED:   the reviewer's mutant 1, #101's picks by name, survived the suite and dies on test_subscribe.py::test_a_price_tie_among_plans_goes_to_the_plan_id_through_the_answer; the Tester's F11, the o3-mini rule refusing `-high`, survived and dies on test_registry_derived.py::test_o3_mini_high_is_stored_as_o3_mini_at_high_effort_on_the_path_a_build_takes
Owner instruction: "all merged" (owner, 2026-10-06), merging the M19 plan, which the owner approves by merging it (m19-plan.md); and "proceed with what you recommend, don't ask" (owner, 2026-09-29, translated from Turkish). W1 delivers the plan's first wave as written and amended
K.8 contracts:  registry.DISPLAY_NAMES (74 names added), MODEL_RULES (new rules), MOVING_ALIASES (+mistral-medium3); refresh.ServingSummary gains `spellings`, `board`/`boards` hold rows by model (D-179); floors.board_names becomes board_rows; subscribe.first_cheapest_plan; rank.AIDER_ATTRIBUTION and board_tables' attribution constants. No /v1 field changes; models.display values and model ids move
Stopped at three attempts: NONE
Hand-kept lists: registry.DISPLAY_NAMES (74 more names, each with its maker's page), registry.MODEL_RULES' one-snapshot rules, test_display_names.LOWER_CASE_ON_2026_10_06, test_registry.ONE_SNAPSHOT_RELEASES, board_tables.EPOCH_EXTERNAL_ATTRIBUTION
```
