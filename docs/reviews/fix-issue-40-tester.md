---
record_type: review
id: fix-issue-40-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---

# Issue #40 Tester Review (fix-issue)

**Reviewer:** Tester subagent (fresh eyes; did not write the fix or its tests)
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `7d7a9ac..c027fb5` (two commits: `29e6064` red tests, `c027fb5` fix)
**Risk tier:** LOW (issue #40 is `severity:low`, latent)

**Inputs I read:** issue #40 and its triage comment (the pinned fix); D-166 clauses 1-3 and both appended notes (`docs/decisions.md:3050-3086`); the policy from the base: `.claude/agents/Tester.md` and `.agents/rules/practices.md`. The range does not touch them.

**Method:** I extracted `29e6064` and `c027fb5` with `git archive` into my scratchpad and ran every test and probe there. `pytest`'s `pythonpath = ["src"]` puts the extracted `src` first; I confirmed that the red tree imported its own `registry.py`. I ran no checkout, restore or stash in the worktree, and I changed no file in it except this one. I did no build and used no network. The candidate `../base38.db` was read only through a copy (sha256 `b5c59630…dd408`, the same before and after).

## Verdict
MINOR

The fix does what the issue pins, and the red tests prove it red to green. On the 2026-09-25 candidate no served model, link, drop or access row changes. Three gaps remain in the tests and the rule. None of them is live today.

## Acceptance-criterion coverage
- **An undated name ending in `-latest` derives no model** → `tests/unit/test_moving_aliases.py:82-88` (8 cases: case variants, a slash route, a vendor route) and `:98-108` (through `reconcile`). Red on `29e6064`, GREEN on `c027fb5`. The rule is at `src/app/workflows/registry.py:438,466`.
- **A dated release after it still derives** → `test_moving_aliases.py:91-95` (`chatgpt-4o-latest-20250326`, `gpt-5.2-chat-latest-20260210`, `claude-instant-1.2`). GREEN on both commits, as a guard should be. It kills the over-reaching mutants F3 and F10 (below).
- **`Command R+` and `claude-instant-v1` join the list** → `test_moving_aliases.py:16-23` (list equality, each entry with a reason) and `:82` (`Command R+`, `anthropic.claude-instant-v1`, `claude-instant-v1`). The entries are at `registry.py:433-434`. Red on `29e6064`, GREEN on `c027fb5`.
- **A curated rule still takes a name it matches (clause 2)** → `test_moving_aliases.py:60-76` covers a listed alias through `reconcile`. `tests/unit/test_registry.py:46` (`gpt-5-chat-latest` → `gpt-5-chat`) covers a `-latest` name at `canonicalize` level only. No test covers a `-latest` name through `reconcile`: see **T2**.
- **`@latest` stays a route decoration (out of scope)** → unchanged. `gpt-4o@latest` → `gpt4o` on both commits, and `vertex_ai/mistral-large@latest` → `mistral-large` on the candidate.

## Red to green on the reported symptom
- **`29e6064` on its own tests:** 9 failed, 17 passed. All 8 `derive_identity` cases derived an id, and the reconcile test registered one model (`assert 1 == 0`).
- **`c027fb5`:** `tests/unit/test_moving_aliases.py` 26 passed.
- **`c027fb5`'s test file against `29e6064`'s source:** 10 failed, 16 passed. The corrected reconcile test is red for the right reason: without the fix, `gemini-flash-latest` registers a derived model with the id `gemini-flash-latest`.
- **The probe rename is legitimate.** On `29e6064` the original `mistral-large-latest` row was linked to the curated `mistral-large` (`models=[('mistral-large', 'Mistral Large', 'Mistral')]`). It was never derived. So the red test failed for the wrong reason, and no fix that respects D-166 clause 2 could have turned it green. `gemini-flash-latest` matches no curated rule and was derived before the fix, so it tests the rule itself. Nothing was weakened or deleted: the assertions are unchanged and only the name moved. The `derive_identity` list at `:84` still includes `mistral-large-latest`, which is correct at that level. One history note: `29e6064` on its own does not contain a valid red reconcile test. `c027fb5` does, and it is proven red above.

## Edge-case probes (`derive_identity`, both commits; 66 names)
- **`-latest` in the middle:** `chatgpt-4o-latest-20250326`, `gemini-1.5-pro-latest-001`, `foo-latest-preview`, `latest-model` and `gpt-latest-mini` all still derive. A date or version after `-latest` is kept, as D-166 says. A non-date word after it is kept too: see **T3**.
- **Case:** `CHATGPT-4O-LATEST`, `gemini-flash-LATEST`, `Claude 3.5 Sonnet Latest` and `gpt4o latest` are refused after the fix. The check runs on the lowercased, normalised text.
- **Routed and vendor-prefixed:** `openrouter/openai/chatgpt-4o-latest`, `azure/mistral-large-latest`, `anthropic.claude-3-5-sonnet-latest`, `us.anthropic.claude-3-5-sonnet-latest-v1:0`, `oci/cohere.command-latest` and `bedrock/…/anthropic.claude-instant-v1` are refused. `anthropic.claude-instant-v1:0` was already refused before the fix: `-v1:0` is stripped and the name folds to the listed `claude-instant`. So the new `claude-instant-v1` entry makes the two Bedrock spellings agree. `anthropic.claude-v1`, `claude-instant-v1.2` and `…-v1:2:100k` still derive, so versioned names are not refused.
- **Underscore effort:** `foo-latest_high` and `gpt-5-chat-latest_high` are refused after the fix. The effort is stripped first. `gpt-5-chat-latest_foo` derives `gpt5-chat-latest-foo`, because `foo` is not an effort and is kept as a name token. That is a synthetic name.
- **Parenthesised effort or date:** `gpt-5-chat-latest (high)`, `o3 (high)` and `chatgpt-4o-latest (2025-02-15)` return None on both commits. Parentheses fail the grammar's `fullmatch` (`registry.py:464`), so the fix changes nothing here. On the candidate, the curated `gpt-4o` rule takes the dated parenthesised rows, so no score is lost.
- **Names that contain "latest":** `latest`, `latestgpt`, `gpt-latestx`, `my-latest2` and `gpt-5-latest-v2` derive on both commits. `chat-latest` is refused after the fix, which is correct: OpenAI's `chat-latest` is an undated alias. Two synthetic spellings still derive: `gpt-4o.latest` (dot) and `gpt-4o-latest@2025` (an `@` date, which the fix reads as dated). No real name has either shape.
- **False refusal of a real release: none found.** On the candidate, 4,977 distinct score and price names were checked. 104 change derivation between the commits, and every one is an undated name ending in `-latest` or one of the two listed spellings (`Command R+`, `*anthropic.claude-instant-v1`). Each is a moving alias by its name.

## Candidate check (read-only copy of `../base38.db`)
- No model id contains `latest`, and neither `command-r+` nor `claude-instant-v1` is registered (306 ids).
- I cleared the links on two copies, reran `reconcile` with each commit's source, and then ran `access.link`. The results are identical: 306 models, 305 score ids, 304 price ids, 1,875 drops, and 647/290 access linked/unlinked with the same conflicts. The access-table hash is `6c38ee4d…1540` for both commits. The red run's model set equals the shipped one. So the author's claim holds: no served list changes.
- The other callers of `derive_identity` (`access.py:82`, `registry.py:499` `_derived_display`) look up only registered or derived ids. No such id ends in `-latest`, so their behaviour is unchanged.

## Fault injection (on the scratch copy of `c027fb5`; each mutant restored in a `finally` block; sha256 `cee98327…ed70` checked after each, equal to the worktree's file)
| id | mutant | existing tests |
|---|---|---|
| F1 | drop `or text.endswith(_LATEST_SUFFIX)` (`registry.py:466`) | KILLED (`:82[chatgpt-4o-latest]`) |
| F2 | `_LATEST_SUFFIX = "latest"` (no hyphen) | survived; changes 0 candidate names (equivalent in practice) |
| F3 | `"-latest" in text` instead of `endswith` | KILLED (`:91[chatgpt-4o-latest-20250326]`) |
| F4 | case-sensitive check on the raw name | KILLED (`:82[Gemini-Flash-Latest]`) |
| F5 | drop `command-r+` | KILLED (`:21`, `:82[Command R+]`) |
| F6 | drop `claude-instant-v1` | KILLED (`:21`, `:82[anthropic.claude-instant-v1]`, `:82[claude-instant-v1]`) |
| F7 | check before the effort is stripped | **survived the whole unit suite** (T1) |
| F8 | check before the colon and Bedrock decorations are removed | **survived the whole unit suite** (T1) |
| F9 | refuse only unrouted names (`and not routed`) | **survived the whole unit suite** (T1); would derive 2 real candidate names, `oci/cohere.command-latest` and `oci/cohere.command-plus-latest` |
| F10 | also refuse `-latest` + a trailing date | KILLED (`:91`) |
| F11 | swap the two operands of the `or` | survived; equivalent |
| F12 | `reconcile` skips curated matching for `-latest` names | **survived the whole unit suite** (T2); would drop `mistral/mistral-large-latest` and `chatgpt-4o-latest` from their curated models |

Kill rate with the existing tests: 6 of 10 non-equivalent mutants (F2 and F11 left out). With the tests proposed below: 10 of 10.

## Suite result
- `tests/unit` on `c027fb5` (`-n auto --no-cov`): **1371 passed, 56 skipped** in 33.7 s. Every skip is a gitignored `advisor.db` or an unset `EPOCH_DATA_DIR`. The worktree has no `advisor.db` either.
- `ruff check` and `mypy` on the two changed source and test files: clean.
- Coverage: the fix adds one constant and one condition, and F1/F3/F4 show both are executed and asserted.

## Mocks / contract tests
- No integration is touched. `reconcile` runs on an in-memory schema (`schema.connect(":memory:")`), as the existing D-166 tests do.

## BLOCKING
- none

## MINOR (the author fixes each on this branch or files it as an issue)
- **T1** `src/app/workflows/registry.py:466`, `tests/unit/test_moving_aliases.py:82-84`: the tests do not pin where the rule runs. Three placements survive the whole unit suite: before the effort strip (F7), before the decorations (F8), and unrouted names only (F9). The eight cases have no underscore effort, no `:`/`-v1:0` decoration and no dotted vendor head that ends in `-latest`. Real feed names depend on the rule's position: `oci/cohere.command-latest` (F9) and Bedrock's `…-latest-v1:0` shape (F8). Add four cases to the `:82` list, all red on `29e6064` and green on `c027fb5` (measured): `gpt-5-chat-latest_high`, `gpt-4o-latest:free`, `oci/cohere.command-latest`, `us.anthropic.claude-3-5-sonnet-latest-v1:0`.
- **T2** `tests/unit/test_moving_aliases.py:98-108`, `docs/decisions.md:3085` ("A curated rule still takes a `-latest` name it matches"): this sentence, added by this fix, has no test through `reconcile`. F12 survives the whole unit suite. The author found the right case, `mistral-large-latest` → the curated `mistral-large`, and moved the test away from it instead of asserting it. Add: `_row(conn, "mistral-large-latest")`, `reconcile`, then assert `scores.model_id == "mistral-large"` and that the name is not in `dropped_names`. It passes on `c027fb5` and fails under F12 (measured).
- **T3** `src/app/workflows/registry.py:436-438,466`: a `-latest` followed by a word rather than a date still derives. The candidate's price feed carries `xai/grok-4.20-beta-latest-reasoning` and `…-beta-latest-non-reasoning`, which derive `grok4.20-beta-latest-reasoning`. Its sibling `xai/grok-4.20-reasoning-latest` is refused. D-166's note says "ending in `-latest`", so the fix meets the text as written. But the issue's premise ("a `-latest` alias moves by definition") applies to both spellings. Latent: the curated `grok-4.20` rule takes both names today, so nothing derives. File it (`/file-issue`), for example: refuse `-latest` unless only a date or version token follows.

## Observations (out of scope; no action required on this branch)
- **O1** `chatgpt-4o-latest` (undated) is taken by the curated `gpt-4o` rule on both commits. That is clause 2 by design, so the new rule does not change where that alias's scores land.
- **O2** A pre-existing spelling split: `Command-R+-08-2024` derives `command-r+-08-2024`, while `command-r-plus-08-2024` derives `command-r-plus08-2024`. These are two ids for one dated release. This fix adds `command-r+` only as an undated list entry. The author can `/file-issue` it if wanted.

## Tests added or extended by this review
- None in the worktree (the brief allows only this file). The proposed tests for T1 and T2 were run in my scratchpad copy of each commit: 4 failed and 1 passed on `29e6064`; 5 passed on `c027fb5`; they kill F7, F8, F9 and F12.
