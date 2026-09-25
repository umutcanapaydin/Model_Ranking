---
record_type: review
id: fix-issue-38-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---

# Issue #38 Tester Review (fix-issue)

**Reviewer:** Tester subagent (fresh eyes; did not write the fix or its tests)
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `7d7a9ac..139a3ab` (`git merge-base origin/main HEAD` = `7d7a9ac`): `6714528` (red test) + `139a3ab` (fix), branch `fix/issue-38-parenthesised-effort`
**Risk tier:** severity:medium, triage `fix-issue`
**Acceptance criterion:** issue #38 as corrected by its triage comment. An effort in a trailing parenthesis (`GPT 6 Astra (Max)`, `Claude Opus 5 (High)`, `gpt-5 (low)`) is read the same way as the underscore/suffix form, for derived and curated names alike, and the effort goes in the `effort` column. A parenthesis that is not a trailing schema effort level (`(no thinking)`, `(default)`, `(May 2024)`, `(High) (0813)`) stays part of the name. Triage scope: "red tests on the nine spellings above".
**Workspace:** I used the fix worktree read-only, except for in-place fault injection in `src/app/workflows/registry.py` (sha256 `bde50039…34a3b6` checked after every mutant and again at the end). I extracted both commits with `git archive` into `scratchpad/tester38/{red,green}`. I used no `git checkout`, `restore` or `stash`, and committed nothing. I did not call `build()`, did not use the network and did not set `RUN_CONTRACT_TESTS`. I opened the two candidate databases read-only (their sha256 was the same before and after).

## Verdict
MINOR

Both halves of #38 are fixed. The red test fails on `6714528` for the reason the issue gives and passes on `139a3ab`. Every criterion has a citing test that exercises it. The unit suite is green. 7 of 10 mutants are killed: one survivor is equivalent and two are gaps (T2, T3). Of the served effects the author measured, none is a defect of this fix. The display-name respelling (T4) and a counter the author did not list (T5) come from rules that were there before #38, and I recommend filing both. Nothing blocks. The gaps are rows to add to one parametrize list.

## Acceptance-criterion coverage

| Criterion | Citing test (cites `#38` in the module docstring, `tests/unit/test_parenthesised_effort.py:1`) | Asserts | Result |
|---|---|---|---|
| A derived name reads its parenthesised effort | `test_parenthesised_effort.py:21-30` `test_a_derived_name_reads_its_parenthesised_effort` | `derive_identity` gives `(gpt6-astra, max)`, `(grok4.7, xhigh)`, `(gemini3.8-flash, high)`, `(kimi-k3, max)` | GREEN (4 of the 9 triage spellings: T1) |
| A curated name reads its parenthesised effort and loses it from the name | `test_parenthesised_effort.py:33-40` `test_a_curated_name_reads_its_parenthesised_effort` | `resolve_effort` gives `("Claude Opus 5", max/high)`, `("gpt-5", low)` | GREEN |
| A parenthesis that is not a trailing effort stays name text | `test_parenthesised_effort.py:43-51` | `(no thinking)`, `(default)`, `(May 2024)`, `(20250929)`, `(High) (0813)`, `(thinking)`: effort None from both functions | GREEN (`(none)`/`(minimal)` not pinned: T3) |
| Effort stored in the `effort` column; the row links to the model without it; the served name has no `(Max)` | `test_parenthesised_effort.py:59-80` (through `_store_scores` + `reconcile`) | `GPT 6 Astra (Max)` → `(gpt6-astra, max)`, next to Epoch's `gpt-6-astra_high` → `(gpt6-astra, high)`; `Claude Opus 5 (High)` → `(claude-5-opus, high)`; `"(" not in display` | GREEN |
| Neighbours: the existing underscore/suffix grammar | `tests/unit/test_registry.py` (whole file, unchanged) | the pre-#38 grammar tests | GREEN |

No test was deleted, skipped or weakened. The range adds one test file and touches no other test (`git diff --stat`: `tests/unit/test_parenthesised_effort.py | 80 +`).

## Red to green on the reported symptom

- `6714528` (`git archive`, worktree venv, `pythonpath = src` resolves to the extracted tree): `tests/unit/test_parenthesised_effort.py` gives **8 failed, 6 passed**. All 4 derived cases, all 3 curated cases and the store/reconcile test fail. The last one fails with `assert (None, 'unspecified') == ('gpt6-astra', 'max')` (`:74`), which is the issue's symptom. The 6 negative cases pass on both commits, as neighbours should.
- `139a3ab`: **14 passed**.

## Suite result

- Unit suite on HEAD, in the worktree: `.venv/bin/python -m pytest -q -p no:cacheprovider --no-cov -n auto tests/unit` gives **1373 passed, 56 skipped** in 29 s. The skips are the `advisor.db` / `EPOCH_DATA_DIR`-gated tests (W-108), not this change.
- Pre-fix tree without the new file: 1359 passed, 56 skipped. The difference is exactly the 14 new tests.
- Coverage of `src/app/workflows/registry.py` over the unit suite: 98% on `6714528` → **99%** on `139a3ab`. Every new line is covered.
- `ruff check` on both touched files passes, and `mypy registry.py` passes.

## Edge-case probes (`scratchpad/tester38/probe_edges.py`, on `139a3ab`)

- **All nine triage spellings** derive with the right effort: `deepseek-v4.1-flash/max`, `muse-spark1.3/max`, `glm5.3/max`, `gemini3.7-flash/high`, `muse-spark1.2/xhigh`, plus the four in the test.
- **Case:** `(MAX)`, `(mAx)`, `(HIGH)`, `(xhigh)`, `(Medium)` are all read and lower-cased.
- **Whitespace:** `Astra(Max)`, `Astra   (Max)`, `Astra\t(Max)`, `Opus 5(High)` and outer spaces are all read. `( Max )` stays name text, and the grammar drops it.
- **Non-effort parentheses:** `(Maximum)`, `(none)`, `(minimal)`, `(unspecified)`, an unclosed `(Max`, `(Max) (0813)` and `(Max) (High)` are not read as an effort.
- **Curated full name whose base does not canonicalise to the same model:** `Qwen3.7 (Max)` has no curated rule for either half, so the grammar reads it as `qwen3.7`/`max`, exactly as `qwen3.7_max` is read, and the family `qwen3.7-max` is not touched. `o3-mini (high)` and `Gemini 3 Flash Lite (High)` have no rule for the full name, so they are counted `unclassified_suffix` and derived with the effort. `qwen3.7-max (High)` and `GPT-5 Pro (High)` keep their variant and read the effort.
- **Modality refusal:** `gpt-5-image (high)` (refused `image`) and `gpt-5-audio (low)` (refused `audio`) give `unclassified_suffix=False`, keeping the M14-W1 MINOR-4 rule. `derive_identity` returns None.
- **Explicit effort that disagrees:** `resolve_effort("Claude Opus 5 (Max)", "high")` gives effort `high`, `conflict=True`, which matches `claude-opus-5_max` with `high`. For a derived name (`GPT 6 Astra (Max)` with `low`) the explicit value wins with `conflict=False`, the same as `gpt-6-astra_max` with `low` today. The row stays `low`, because `_register_derived` only overwrites `unspecified` (`registry.py:585`).
- **`unclassified_suffix` parity:** `GPT 6 Astra (Max)` and `gpt-6-astra_max` both give `True`. `Claude Opus 5 (High)` and `claude-opus-5_high` both give `False`. See T5 for what this does to the served counter.

## Served effect (the author's candidates, rerun read-only with `../cmp38.py` and three read-only probes)

| Author's claim | Confirmed | Judgment |
|---|---|---|
| no degradation, no upward anomaly | `degradations: []`, `upward: []` | not a defect |
| agent-board unmatched rows 60 → 6 | 60 → 6. The 6 are `Qwen3.8 Flash Next`, the separate gap triage named | not a defect |
| Muse Spark 1.2 newly ranked on 3 surfaces | assistant, factuality, vision, from the Arena text/vision spelling `muse-spark-1.2 (xHigh)` → `muse-spark1.2`/`xhigh`, a model already registered with a price | intended |
| `coding` effort labels unspecified → high/medium | SWE-bench's `Gemini 3 Flash (high)`, `MiniMax M2.5 (high)`, `GLM 5 (high)`, `DeepSeek V3.2 (high)`, `Claude 4.5 Haiku (high)`, `GPT 5.1 Codex (medium)`: the source's own stated effort, now stored. Positions are unchanged | intended |
| two derived display names change spelling | `gpt6-astra` `GPT-6 Astra` → `GPT 6 Astra`, `glm5.3` `GLM-5.3` → `GLM 5.3` | rule from before #38, side effect (T4) |

What I found in addition:
- 189 score rows changed. Every one ends in a trailing parenthesised effort. 106 only gained an effort. 83 went from unlinked to linked. **No row moved to a different model.** No model display in `fix38.db` contains `(`. The model set grows by one id (`grok4.7`).
- On `mathematics`, `GPT 6 Astra` moves from 5th to 3rd. It is tied at 100.0 with `GPT-5.5` and `GPT-5.6 Sol`, and ties are ordered by display (`rank.py:323`). A space sorts before `-`, so this is only the respelling (T4). The data did not change.
- `effort_unknown` rises by 85 across 31 sources. The author's list does not mention it (T5).

## Fault injection (in place, restored byte-identically in a `finally`, sha256 checked after each mutant)

Script: `scratchpad/tester38/mutate38.py`. Each mutant first ran `-x` on `test_parenthesised_effort.py` + `test_registry.py`, and if that stayed green, the whole unit suite with `-n auto`. The run had a hard timeout, and on timeout the process group got SIGKILL. At the end `registry.py` sha256 was `bde50039cba6efd817e9f05bbe7212d9f041f2a4e57213cc545c8d126334a3b6`, the same as before injection, and `git status --short` was empty.

| # | Mutant | Result | Killing test / note |
|---|---|---|---|
| A | `resolve_effort` ignores parentheses (`registry.py:298`) | KILLED | `test_parenthesised_effort.py:38` [Claude Opus 5 (Max)] |
| B | `derive_identity` ignores parentheses (`:445`) | KILLED | `:27` [GPT 6 Astra (Max)] |
| C | display keeps the parenthesis (`:496`) | KILLED | `:59` (`"(" not in display`) |
| D | `\Z` anchor removed (`:265`) | KILLED | `:48` [DeepSeek V4 Pro (High) (0813)] |
| E | `re.I` removed | KILLED | `:27` [GPT 6 Astra (Max)] |
| F | `\s*` → `\s+` | **SURVIVED** (1373 passed) | gap: T2 |
| G | effort group widened to `\w+` | KILLED | `:48` [(default)] |
| H | `none|minimal` admitted in the parenthesis | **SURVIVED** (1373 passed) | gap: T3 |
| I | parenthesis regex tried before the suffix regex (`:298`) | survived, **equivalent** | a name cannot end in both `)` and a letter, so the two regexes never both match |
| J | `xhigh` dropped from the level list | KILLED | `:27` [Grok 4.7 (xHigh)] |

Kill rate: 7/9 non-equivalent mutants.

## Mocks / contract tests
- No integration is touched. The change is pure name grammar in `registry.py`. The store/reconcile test drives the real `_store_scores` and `reconcile` against an in-memory schema (`connect(":memory:")`).

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- **T1** `tests/unit/test_parenthesised_effort.py:21-26`: triage pinned the scope as "red tests on the nine spellings above", but the parametrize list has 4 of them (and `Kimi K3 (max)` is written lower-case, not as on the board). `Deepseek V4.1 Flash (Max)`, `Muse Spark 1.3 (Max)`, `GLM 5.3 (Max)`, `Gemini 3.7 Flash (High)` and `Muse Spark 1.2 (xHigh)` have no test. My probe and the live candidate show all five link correctly today. Add the five rows.
- **T2** `src/app/workflows/registry.py:265`: `\s*` deliberately admits `Name(High)` with no space, but no test pins it. Mutant F (`\s+`) stays green across 1373 tests. No live name has that form today, but boards do write parentheses with no space (`Gru(2024-08-24)` is in `fix38.db`). Add one row such as `("Claude Opus 5(High)", "Claude Opus 5", "high")`.
- **T3** `src/app/workflows/registry.py:265`, `tests/unit/test_parenthesised_effort.py:43-47`: no negative test pins that only schema levels count. Mutant H (admitting `none|minimal`, which `_UNDERSCORE_EFFORT` at `:366` does read) stays green. It is not harmless. In a scratch copy with mutant H, `resolve_effort("Claude Opus 5 (none)")` returned effort `none`, and `_store_scores` then raised `SourceError … CHECK constraint failed: effort IN (…)`, which aborts the whole source. Add `"Claude Opus 5 (none)"` and `"GPT 6 Astra (minimal)"` to the negative list. The divergence from the underscore form is deliberate: it follows the issue's fix shape. It should be pinned, not changed.
- **T4** `src/app/workflows/registry.py:500`, `src/app/workflows/rank.py:323` (recommend `/file-issue`; out of scope for #38): `_derived_display` picks the lexicographically first spelling that contains a space. Now that `GPT 6 Astra (Max)` is readable, its bare form wins over Epoch's `GPT-6 Astra` (and `GLM 5.3` over `GLM-5.3`), because a space sorts before `-`. Ranking ties are ordered by display, so `GPT 6 Astra` also moves ahead of `GPT-5.5` and `GPT-5.6 Sol` on `mathematics` at 100.0. This is not a defect of the fix: the new spelling is a board's own, and the chooser rule predates #38. But a new board's spelling can now rename a served model, and the name can flip back when that board is missing from a build. The curated family style is hyphenated (`GPT-5.6 Sol`, `GLM-5.2`). A stable preference (the most frequent spelling, or Epoch's) is an owner decision.
- **T5** `src/app/workflows/registry.py:324-326`, `src/app/workflows/ingest.py:124` (recommend `/file-issue`; the behaviour predates #38): at ingest, `resolve_effort` counts every derived parenthesised name as `unclassified_suffix`, because no curated rule exists to confirm the effort. `reconcile` then gives the row its effort (`registry.py:585`), but the count is never taken back. On the candidate, `effort_unknown` goes 558 → 643: each `arena_agent*` board 0 → 9, `aider` 0 → 7, and each Arena text/vision board +1. Those rows do have an effort. This is the same as Epoch's `gpt-6-astra_max` today, so it meets "read as the underscore form is read", but the disclosure now over-states unknown efforts on six more boards, and the author's list of served effects does not mention it.
- **T6** `src/app/workflows/registry.py:496`: `_derived_display` strips whitespace after the parenthesis `sub`, while `derive_identity` strips before matching (`:443`). So a candidate `"GPT 6 Astra (Max) "` (trailing space) becomes the display `GPT 6 Astra (Max)` (probe output). This cannot happen today: names reach it through `split_harness`, which strips (`src/app/clients/swebench.py:47-48`), and `fix38.db` has no name with a space after `)`. Strip before `sub` if this is touched again. No action is required for #38.

## Tests added/extended this review
- none. My brief allows me to write only this verdict in the worktree. The rows proposed in T1-T3 are for the author. The probes are in `scratchpad/tester38/` (`probe_edges.py`, `probe_db*.py`, `mutate38.py`).
