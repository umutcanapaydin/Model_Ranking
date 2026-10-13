---
record_type: review
id: backlog-data-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# Independent review: the backlog data wave (#234, #232, #266, #233, #230)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `origin/main..0d5bc8b` (8 commits, `36164d8` to `0d5bc8b`, on `origin/main` `9d2bbfc`)
**Risk tier:** MEDIUM

## Verdict
BLOCKING

The registry splits are right, and both refresh gates pass on the real artifact. One new rule puts a
speed tier priced at double into Kimi K2.7 Code, and that raises its served price by 25% on four
surfaces (B1). The #230 line misreads the board nearest its limit on two kinds of night, and its
test does not cover three of the four branches it adds.

How the review was done:
- **Commits.** I read all 8 commits and issues #234, #232, #233, #230 and #266, and checked them against
  D-189 (`docs/decisions.md:4571`).
- **Regex audit.** I ran every distinct `scores.raw_name` and `pricing.alias` in a copy of the worktree's
  `advisor.db` (sha256 `bc5435b0…`, built before the wave) through `origin/main`'s registry and through
  this branch's registry. Of 4,592 names, 87 change model. Each of the 87 is one of the intended moves.
  No name moves into a wrong model, and none of the new rules swallows a name it should not.
  - The `p` separator always sits between digits, so `kimi-k2-preview` and `deepseek-v3-pro` still read
    as before.
  - `resolve_effort` keeps `Kimi K2.5 (high)` and `DeepSeek V3.2 (high)` as before. Names like
    `-thinking-max` resolve to the new models.
- **Engine checks.** I reconciled two copies of the artifact, one with `origin/main`'s `src`
  (`git archive`) and one with this branch's. I then ran `reconcile`, `access.link`, `reconcile_plans`
  and `build_price_medians` on both, and ran the gates through `fingerprint_of(Path)`.
  - Rebuilding with `origin/main`'s code gives the served artifact's digest exactly.
  - Old against new: `degradations` = [] and `upward_anomalies` = [].
  - `largest_board_change` = `board epoch_webdev`, 3 of 134. Nothing is renamed.
  - Six models are new. `assistant` grows from 207 to 209 models and `coding` from 56 to 58. Every
    surface median moves by less than 4%.
- **Faults.** I planted 8 faults, each restored from its bytes and checked by sha256. Four were caught
  and four survived (M2).
- **Tests.** The full suite passes: 2752 passed, 29 skipped (`pytest -n 4 --no-cov tests`).
  `test_model_families.py` and `test_ios_client_contract.py` pass. `ModelFamilies.swift` does not need
  regenerating, because no new first word appears.

**Price medians that move (input/output, $ per M), old code against new code, same data:**

| model | before | after | why |
|---|---|---|---|
| deepseek-v3 | 0.56/1.25 | 0.89/1.0 | #234's correction, as the issue predicted |
| deepseek-v3.1 | 0.55/1.65 | 0.58/1.69 | Terminus leaves, Fireworks' `v3p1` joins |
| deepseek-v3.2 | 0.5/1.5 | 0.53/1.59 | Speciale and Exp leave, `v3p2` joins |
| qwen3-coder | 0.712/3.157 | 0.975/4.65 | 30B-A3B and Next leave; the 480B flagship's own price |
| kimi-k2 | 0.6/2.5 | 0.6/2.3 | Thinking and the `k2p*` releases leave |
| **kimi-k2.7-code** | **0.95/4.0** | **1.188/5.0** | **B1: a speed tier at double the price joins** |
| new: deepseek-v3.1-terminus 0.27/1.0 · deepseek-v3.2-exp 0.27/0.41 · deepseek-v3.2-speciale 0.58/1.68 · kimi-k2-thinking 0.6/2.5 · qwen3-coder-30b-a3b 0.3/1.425 · qwen3-coder-next 0.6/1.44 | | | |

**#266, judged.** The author's ruling holds against D-189 clause 1: a model is a release its maker names.
- OpenAI's guide makes Pro a request parameter (`reasoning.mode: "pro"`) that works on any GPT-5.6
  model. It has no model id of its own and is billed at that model's token rates.
- GPT-5 Pro and GPT-5.4 Pro are different: each has an id and a price of its own. The artifact prices
  them at 15/120 and 30/180, against 4/20 for GPT-5.6 Sol.
- Keeping the Sol, Luna and Terra rules unguarded is therefore consistent with the other Pro rules.
- No `gpt-5.6-*-pro` price alias is left in this artifact. OpenRouter's rows went with D-194.
- Two gaps remain. The ruling turns down the fix the issue asked for, and it is recorded only in a
  test docstring (M3). Its effect on scores was not looked at (K2).

**#233, judged.**
- 3 of Aider's 68 rows hold a `+`: the two pairs the issue names, and `QwQ-32B + Qwen 2.5 Coder
  Instruct`, which was unlinked.
- None of Aider's model names uses `+` for anything but a pair.
- After the drop, 65 rows remain. Aider's `minimum_rows` is 1 (`src/app/workflows/sources.py:159`).
- The Aider board loses 3 of 68 rows, well inside both guards.

## Findings

### BLOCKING
- **B1** `src/app/workflows/registry.py:219` (with the pin at `tests/unit/test_registry.py:892`):
  Kimi K2.7 Code's new rule takes the speed tiers sold at double the price, so the wave serves the model
  25% dearer than its list price.
  - **What the rule takes.** `kimi[-_ ]?k2[.\-p]7[-_ ]?code` matches:
    - `moonshotai/kimi-k2.7-code-highspeed`: Moonshot's own models.dev entry, at 1.9/8.0;
    - `aihubmix/kimi-k2.7-code-highspeed`;
    - Fireworks' `kimi-k2p7-code-fast` routers, at 1.9/8.0.

    The base price is 0.95/4.0.
  - **Failure.** Before the wave, K2.7 Code was derived, and the derive grammar kept `-highspeed` apart.
    Its price was 0.95/4.0. Now the models.dev median is (0.95 + 1.9)/2, and the two-stage median
    serves **1.188/5.0**: +25% on input and output.
  - **Where it shows.** K2.7 Code ranks on `everyday`, `expert`, `mathematics` and `web-dev`, so every
    price, Budget Pick filter and Best Value sentence there carries the inflated figure. No gate sees it:
    `MAX_MEDIAN_PRICE_MOVE` watches surface medians, not one model's price.
  - **Same pattern in K2.6.** Fireworks' `kimi-k2p6-fast` (2.0/8.0) now joins K2.6. K2.6's median holds
    for now only because LiteLLM's other rows outvote it.
  - **Precedent.** The registry already keeps a speed tier out of its base model's price:
    `minimax-m2.5`'s `(?![-_ ]?lightning)`, pinned at `tests/unit/test_registry.py:270`.
  - **Fix.**
    - Add `(?![-_ ]?(?:highspeed|fast))` to the K2.7 Code rule, and `(?![-_ ]?fast)` to K2.6's.
    - Flip line 892's expectation to "not `kimi-k2.7-code`".
    - Add `moonshotai/kimi-k2.7-code-highspeed` and `fireworks_ai/kimi-k2p6-fast` to the
      never-the-base cases.
  - **Check.** I planted the lookahead. Only line 892 fails, and K2.7 Code's median goes back to
    0.95/4.0.

### MINOR
- **M1** `src/app/workflows/refresh.py:297-310`, called at `:1390` and `:1430`:
  `largest_board_change` does not judge boards the way the two guards do. On two kinds of night it
  therefore names the wrong board as nearest its limit, and that board is the figure #230 exists to
  record.
  - **A board appearing.** `_mostly_new` lets a board through when it had no rows before (a board
    returning). `largest_board_change` counts all of its rows as new (n of n, 100%), so it beats any
    real change.
  - **Measured.** I gave `epoch_x` a loss of 2 of 10 rows (20%) and added a new board `arena_new`
    with 3 rows. Both guards return []. The line reports
    `{"board": "board arena_new", "changed": 3, "of": 3, "limit": 0.25}` on a night that publishes,
    and hides `epoch_x`.
  - **An expiry night.** The guards judge against `baseline`, the live artifact without the expired
    source's rows (`_served_without`). The function is given `live`, so the expired board reads as 100%
    lost while the guards excuse it.
  - **Fix.**
    - Pass the cycle's `baseline` in.
    - Skip the "new rows" ratio when the board had no rows at baseline.
    - Measure lost rows against `baseline` and new rows against `base` (`prices or live`), as
      `upward_anomalies` does.
    - Add a test for each case.
- **M2** `tests/unit/test_refresh_board_ids.py:253-275`: the #230 test covers one branch only, a loss on
  a declared board on a night that publishes. Four planted faults survive (274 passed each time):
  - **F1** the "new rows" direction removed;
  - **F2** the refused outcome built without `largest_board_change`;
  - **F3** a surface's own boards (`OWN_BOARD`) ignored;
  - **F4** the `largest[0] > 0` filter removed, so a night with no change reports a zero-change board
    instead of `null`.

  Because the gain and loss limits are both 0.25, swapping them would not show either.
  - **Fix.** Add tests for:
    - a gain on an own board;
    - the refused path (exit 3, the line still carries the field);
    - a night with no board change, which gives `null`.
- **M3** `docs/decisions.md:4599` and `:4613`: the wave records nothing outside code and tests.
  - **What is missing.** D-189's *Applied* and *What stays gathered* paragraphs list every case split
    under clause 1 and name #232 as the home of the rest. This wave:
    - splits seven more releases;
    - keeps three gathered: K2-Instruct-0905 as a K2 snapshot, grok-4-fast's two modes, and GPT-5.6
      Pro as a mode;
    - turns down the fix #266 asked for.

    The #266 ruling on what a model is, with OpenAI's guide as its evidence, exists only in a test
    docstring. D-189 also says model ids move on the first night after a release. This wave moves rows
    into six new ids, and no record says so.
  - **Failure.** The next reader of D-189 finds #232's candidates described as "not split here", and
    #266 closed against its own stated fix with no ruling to point to.
  - **Fix.**
    - Amend D-189 with an *Amended by #232/#266 (2026-10-13)* line. It lists the seven splits and the
      three kept cases, and cites the maker pages and the date they were read.
    - Write the `docs/process-log.md` entry at close (D-172), including the six new ids and the
      `kimi-k2.7-code` price correction.

## K.9 candidates spotted outside this wave's scope
- **K1** `src/app/workflows/registry.py:223`: Kimi K2's dated snapshots are left unlinked. This was
  already so before the wave. The lookahead `(?![.\-p]\d)` reads the `-0` of a date as a point release.
  - **What falls out.** `kimi-k2-0905-preview` and `kimi-k2-0711-preview` (55 Arena rows across the
    Arena text slices), and `novita/moonshotai/kimi-k2-0905`.
  - **Why it is inconsistent.** The wave pins `Kimi-K2-Instruct-0905` as a K2 snapshot. These are the
    same snapshots without the word `Instruct`.
  - **Fix.** Use the single-digit form `(?![.\-p]\d(?!\d))`, as `deepseek-v4` and `glm-5` do, and add
    test cases. This is a bug.
- **K2** `src/app/workflows/registry.py:483`: Epoch's `_promax` suffix is read as the `unspecified`
  effort.
  - **Failure.** Under #266's ruling, Pro is a mode of GPT-5.6 Sol. Sol's Pro-mode Chess result
    (`gpt-5.6-sol_promax`, 64.0) beats its `_max` run (55.0), so the board ranks Sol at a Pro-mode score
    with no effort shown. FrontierMath Tier 4 has the same pair of rows (80.5 and 82.9).
  - **Fix.** File an issue: store Pro as a disclosed mode, or keep it out of the default row. This is an
    enhancement.
- **K3** `src/app/workflows/registry.py:135`: `gpt-5.6-cyber` and `bedrock_mantle/openai.gpt-5.6-cyber`
  (12.5/75 and 13.75/82.5) reach GPT-5.6's price median, though GPT-5.6-Cyber is a separate product.
  - **Effect.** GPT-5.6 is served at 4.2/21.0 against 4.1/20.5 without them. It is small now and grows
    with each Cyber listing.
  - **Fix.** Add a `cyber` exclusion to the lookahead, or a rule of its own. This is a bug.

## Risks queued to next M
- **R1** `src/app/clients/aider.py:95` and `src/app/workflows/build.py:304`: the pair drop happens only
  in `parse_polyglot`.
  - **The risk.** On a night Aider's fetch fails, `Carry.restore` copies Aider's rows from the live
    artifact as they are stored. If that artifact was built before this wave, the rows include
    `o3 (high) + gpt-4.1` and `DeepSeek R1 + claude-3-5-sonnet-20241022`. The reconcile links them back
    to GPT-4.1 and Claude 3.5 Sonnet. This lasts until the first successful Aider fetch, or up to
    `CARRY_MAX_AGE` (30 days).
  - **What would show it is real.** A refresh record that lists `aider` as carried while GPT-4.1 is
    still ranked at 78.2 on `aider`.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| B1 | Fixed. Kimi's speed tiers (`-highspeed`, `-turbo`, Fireworks' `-fast`) derive models of their own; K2.7 Code's median is 0.95/4.0. The test that pinned the old reading is turned. | `293412e` red, `64b0484` fix |
| M1 | Fixed. `largest_board_change` takes the cycle's baseline, measures losses against it and gains over the boards `live` serves, and excuses a board appearing for the first time. | `293412e` red, `64b0484` fix |
| M2 | Fixed. Tests for a gain on a surface's own board, a refused night, a night with no board change (`null`), a board appearing, and an expiry night. | `293412e` |
| M3 | Fixed. D-195 amends D-189 clause 1 with the seven splits, the kept cases and the #266 ruling; the process log is written at the wave's close. | this commit |
| K1 | Fixed in this wave: K2's dated previews are K2 (55 Arena rows). | `293412e` red, `64b0484` fix |
| K2 | Accepted under D-195 clause 3: a Pro run is the model it runs, its effort `unspecified`, as #267's ruling keeps ARC-AGI-2's budgets. | D-195 |
| K3 | Filed as #269. | - |
| R1 | Accepted. Aider is a static YAML file on GitHub, and a carried night lasts only until its next good fetch; the record lists `aider` as carried, which is the sign the reviewer names. | - |

