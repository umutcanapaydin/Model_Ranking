---
record_type: review
id: backlog-data-review-round-3
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# Independent review, round 3: the backlog data wave (#232, #234, #235, #262, #264, #266, #269)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `7bdc928..a594dfc` (9 commits). It also re-checks rounds 1 and 2
(`docs/reviews/backlog-data-review.md`, `docs/reviews/backlog-data-review-round-2.md`) and the author's
dispositions of both.
**Risk tier:** MEDIUM

## Verdict
MINOR

Round 2's B1 is fixed. A speed tier is now refused on the price path only, so Arena's
`kimi-k2-thinking-turbo` links to Kimi K2 Thinking again. The relinked artifact passes both refresh gates.
Four MINOR findings remain:
- the docs still say `unknown` where the code now records `unstamped`;
- two planted faults in the refresh fixes survive;
- D-195's *Consequence* has three counts that do not match the artifact;
- MiniMax M2.1's `lightning` tier still prices M2.1.

How the review was done:
- **Artifact.** I worked on copies of the worktree's `advisor.db` (sha256 `bc5435b0…`, unchanged at the
  end).
  - On each copy I set every `model_id` to NULL in `access`, `pricing`, `scores`, `px_median` and
    `plan_models`, and emptied `models`.
  - I then ran `reconcile`, `access.link`, `reconcile_plans` and `build_price_medians`, in a build's
    order. I did this with three trees from `git archive`: `origin/main`, `7bdc928` and `a594dfc`.
  - Rebuilding with `origin/main` reproduces the served links exactly: 0 score rows and 0 price aliases
    differ.
  - Served against `a594dfc`, using `a594dfc`'s `serving_summary`:
    - `degradations` = [] and `upward_anomalies` = [];
    - `largest_board_change` = `board arena_text_polish`, 6 of 232.
- **Faults.** I planted 15 faults, each restored from its bytes and checked by sha256. Eleven were caught
  and four survived. Two of the four are equivalent on today's data (F3, F4); the other two are M2. `git
  status` was clean afterwards.
- **Tests.** The four touched test files pass: 315 passed. All eight refresh, nightly, deploy and stamp
  files pass: 264 passed.

**Rounds 1 and 2, re-judged.**
- **Round 2 B1: fixed.**
  - The fix is `registry.price_refusal`, called only in `reconcile`'s pricing loop
    (`src/app/workflows/registry.py:1005-1006`). The score loop does not call it.
  - Measured:
    - `kimi-k2-thinking-turbo`'s Arena rows link to `kimi-k2-thinking`: 35 score rows, all moved from
      `kimi-k2`;
    - all 11 speed-tier price aliases are dropped as `speed-tier`;
    - Kimi K2.7 Code's median is 0.95/4.0.
  - Planting the refusal on the score path too (F5) fails 10 tests.
- **Round 2 M1: partly true.** D-195's numbers mostly hold, but three claims do not match the artifact
  (M3 below).
- **Round 2 M2: fixed.**
  - `editable_path` keeps `C:`.
  - `_same` uses `Path.samefile`.
  - Both changes are pinned: F10 and F11 are caught.
- **Round 2 M3: fixed in code.**
  - `_builds` records `unstamped`.
  - The deploy refuses `unstamped` whichever name `DEPLOY_ACCEPT_DATA_FROM` gives. It never suggests a
    name for it, because the `case` at `scripts/deploy_hosted_engine.sh:91-93` covers only `release-*`
    and `unknown`.
  - F6 and F14 are caught.
  - The prose was not updated (M1 below).
- **Round 2 M4: partly true.**
  - The emptied-baseline fallback now has a test (F8 caught).
  - The disposition says computing the figure once means "the refused path cannot drop the baseline".
    That holds only while the one remaining call passes it. Dropping `baseline` there still passes every
    test (M2 below).
  - `kimi-k2-turbo-preview` is a test name now (F15 caught).
- **Round 2 K1: fixed.** MiniMax's `-highspeed` tiers and DeepInfra's `M2.7-Turbo` are refused. The
  medians are M2.7 0.299/1.196 and M2.5 0.305/1.22, as D-195 says.
  - Two caveats: the commit subject of `c035b78` ("derive models of their own") is untrue, since none
    derives, and M2.1's `lightning` is missed (M4).
- **Round 2 R1: fixed.**
  - The `install:` recipe runs `scripts/venv_owner.py` first (`Makefile:96`).
  - `test`, `lint`, `typecheck` and `check-fast` all depend on `install`.
  - F12 is caught.
- **Round 1 dispositions.** Round 2 judged them, and its judgments still hold.
  - B1's "derive models of their own" was untrue, and is superseded by the price-path fix.
  - K3 (#269) is now addressed by `04c3f18` (F13 caught). It is still OPEN on GitHub, which is right
    until the merge.
- **#269.** `gpt-5.5-cyber`, `gpt-5.6-cyber` and `bedrock_mantle/openai.gpt-5.6-cyber` leave GPT-5.5 and
  GPT-5.6. They derive nothing, because no score names them. GPT-5.6's median moves 4.2/21.0 → 4.1/20.5,
  as D-195 says. `gpt-5.6 cyber` and `gpt-5.6_cyber` are refused too.
- **#218 (`da61494`, `d4a9441`).** Reverted by `2a071c0`, which is outside this range. The revert is right
  and exact.
  - `git diff da61494^ 2a071c0 -- ios` is empty.
  - D-191 clause 2 records the same rule taken out after three verdicts.
  - Re-adding the rule without a decision that supersedes D-191 would have been BLOCKING. The revert
    removes that.

## Findings

### BLOCKING
None.

### MINOR
- **M1** `scripts/deploy_hosted_engine.sh:89-90`, `docs/release-testflight.md:47` and `:83`: the deploy's
  refusal and the runbook still say "a refresh run by hand without `APP_BUILD` records `unknown`".
  - **What is true now.** The code records `unstamped` (`src/app/workflows/refresh.py:829`).
  - **Failure.** The owner's data says `unstamped`, and the deploy refuses it. The refusal then explains
    the case with a value the record does not hold. The runbook teaches the same wrong name: an owner
    who reads `unknown` there may reach for `DEPLOY_ACCEPT_DATA_FROM=unknown`, which this record never
    matches.
  - **Fix.** Say `unstamped` in all three places, and say that no `DEPLOY_ACCEPT_DATA_FROM` accepts it:
    the refresh has to be run again with `APP_BUILD`.
- **M2** `src/app/workflows/refresh.py:1390` and `:833`: two planted faults survive all 264 refresh,
  nightly, deploy and stamp tests.
  - **F7.** `largest_board_change(live, fresh)` with `baseline` dropped from the single call. This is round
    2's F4, still uncaught. No test runs an expiry night through `_cycle` and reads the recorded figure, the
    test round 2's M4 asked for.
  - **F9.** The fallback for a non-published cycle whose previous record has no `served_built_by` changed
    from `unknown` to `unstamped`.
    - **Failure.** The first unchanged night after a pre-#198 record would then record `unstamped`, and the
      deploy would refuse data that `DEPLOY_ACCEPT_DATA_FROM=unknown` is meant to accept.
    - **Why it matters now.** `unknown` now has one meaning, and this fallback is the only place a cycle
      still writes it.
  - **Fix.** Add two tests:
    - an expiry night through `_cycle`, asserting the record's `largest_board_change` against the baseline;
    - an unchanged cycle after a record without `served_built_by`, asserting `served_built_by == "unknown"`.
- **M3** `docs/decisions.md:4957-4964` (D-195 *Consequence*): three claims do not match a relink of the
  artifact of 2026-10-13 (served → `a594dfc`).
  - **The rest is exact, measured:**
    - 135 score rows go to new ids (37 V3.1-Terminus, 61 V3.2-Exp, 35 K2 Thinking, 2 Qwen3-Coder 30B);
    - 3 rows and 6 aliases reach K2.5, K2.6, V3.1 and V3.2;
    - 55 rows and 1 alias reach K2;
    - 3 Cyber aliases are refused;
    - the gates pass, and the largest board change is 6 of 232;
    - the DeepSeek V3, GPT-5.6 and MiniMax medians are as stated.
  - **"seven new ids".** Six are new. `kimi-k2.7-code` is already in the served artifact (9 score rows, 14
    aliases).
  - **"46 price aliases leave Kimi K2, Qwen3-Coder and DeepSeek V3, V3.1 and V3.2".** 45 leave those
    models. The 46th, `azure_ai/FW-Kimi-K2.7-Code`, was unlinked before.
  - **"11 speed-tier … aliases leave their base models' medians".** Only 9 were in any median, and the four
    Fireworks routers were in Kimi K2's, not their base models' (K2.6, K2.7 Code). The two
    `kimi-k2.7-code-highspeed` aliases were already unlinked when served.
  - **"The medians move to … 0.95/4.0 for Kimi K2.7 Code".** It is 0.95/4.0 in the served artifact
    already.
  - **Not stated.** Kimi K2's median moves from 0.6/2.5 to 0.6/2.4.
  - **Fix.** Restate the clause against the served artifact: six new ids, 45 aliases plus one previously
    unlinked, and 9 speed-tier aliases leaving Kimi K2's and MiniMax's medians. Drop K2.7 Code from the
    medians that move, and add Kimi K2's.
- **M4** `src/app/workflows/registry.py:263` and `:345-347`: MiniMax M2.1's speed tier still prices M2.1,
  although D-195 clause 4 (`docs/decisions.md:4948-4950`) says MiniMax's tiers were read and are refused.
  - **What happens.** `minimax/MiniMax-M2.1-lightning` (0.3/2.4, twice M2.1's output price) links to
    `minimax-m2.1`.
    - `minimax-m2.1` is not in `SPEED_TIERED`.
    - `_SPEED_TIER_WORD` has no `lightning`.
    - Only M2.5's rule refuses `lightning`, by a regex guard that adds nothing to the `speed-tier` count.
  - **Measured.** M2.1's median is 0.3/1.32. Without the lightning row it is 0.315/1.26, so the tier lifts
    the output median 4.8%.
  - **Same class.** `MiniMax-M2.7-lightning` canonicalizes to `minimax-m2.7` today. A listing of it would
    price M2.7.
  - **Fix.**
    - Add `minimax-m2.1` to `SPEED_TIERED`, and `lightning` to `_SPEED_TIER_WORD`.
    - Move M2.5's `(?![-_ ]?lightning)` guard to the price path, so its score name links and its price is
      counted as `speed-tier`.
    - Add `minimax/MiniMax-M2.1-lightning` to `test_a_speed_tiers_score_is_its_models_and_its_price_is_refused`.
    - Or narrow D-195 clause 4 to the tiers actually listed.

## K.9 candidates spotted outside this wave's scope
- **K1** `src/app/workflows/registry.py:132-137` (the GPT-5.x rules): the `cyber` exclusion is only on the
  bare GPT-5.5 and GPT-5.6 rules.
  - **What still joins.** `gpt-5.6-sol-cyber` canonicalizes to `gpt-5.6-sol`, and `gpt-5.4-cyber` to
    `gpt-5.4`. #269 quotes OpenAI that GPT-5.6-Cyber is "built on GPT-5.6 Sol", so a provider's Sol-named
    spelling is plausible.
  - **The artifact today.** It holds neither name, and `gemini-3.8-flash-cyber` is already unlinked. #269's
    body says the Gemini rule has no guard, which is not true of this tree.
  - **Fix.** Put `cyber` in the Sol, Luna and Terra rules' lookaheads too, and correct #269's body when it
    closes. Filing it is enough while no such name is served.

## Risks queued to next M
- **R1** `src/app/workflows/refresh.py:829`: the old code has already written records on disk, and those
  say `unknown` for cycles run without `APP_BUILD`.
  - **The risk.** Until the next cycle runs on this release, such a record can still be deployed with
    `DEPLOY_ACCEPT_DATA_FROM=unknown`. That is the ambiguity #235 R2 names, now transitional.
  - **Why it is bounded.** `scripts/engine_service.sh:53` always sets `APP_BUILD`, so only refreshes run by
    hand wrote such records, and the next published night replaces the value.
  - **What would show it is real.** A deploy that announces "a record from before #198" after #198 shipped.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Fixed. The deploy's refusal and both runbook passages say a hand-run refresh records `unstamped`, which no `DEPLOY_ACCEPT_DATA_FROM` accepts. | `06b09e5` |
| M2 | Fixed. `largest_board_change` takes the baseline as a required argument, so a call cannot leave it out; a refused cycle over a record from before #198 keeps `unknown`, now tested. | `0eaff74` red, `06b09e5` fix |
| M3 | Fixed. D-195's Consequence is rewritten from a relinked measurement: six ids new to the artifact plus K2.7 Code, 45 aliases, 12 speed-tier refusals, and every median that moves, Kimi K2's included. `c035b78`'s subject ("derive models of their own") was overtaken by `4bf45d0`, which refuses the prices instead. | this commit |
| M4 | Fixed. `-lightning` is a speed-tier word and MiniMax M2.1 is in `SPEED_TIERED`. | `0eaff74` red, `06b09e5` fix |
| K1 | Fixed in this wave: the Sol, Luna, Terra and GPT-5.4 rules refuse `cyber`; #269's body is corrected by a comment. | `0eaff74` red, `06b09e5` fix |
| R1 | Accepted. The Mac's service always sets APP_BUILD, and the next night that publishes rewrites the record. | - |

