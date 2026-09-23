---
record_type: review
id: m16-wave-4-rereview
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M16-W4 -- independent re-review of the fix round (D-157 amendment, commits 9e0b760..8463f74)

**Seat:** independent (Code-Reviewer + Tester combined). I wrote none of this wave, none of its
review and none of this fix round.

**Scope:** `git diff origin/main...HEAD` on `enhancement/m16-w4-fixes`, merge base `9058683`, four
commits:
- `9e0b760` and `24a0c72` are the red tests.
- `7446079` is the fix.
- `8463f74` commits the review record and removes the working plan from main.

I read the round against the findings of `docs/reviews/m16-wave-4-review.md`, against the
amendment at the end of D-157 in `docs/decisions.md`, and against the re-measured
`docs/research/m16-w4-derived-registry-2026-09-23.md`.

**Policy:** I read my policy only from `git show origin/main:subagent-profiles/Code-Reviewer.md`
and `.../Tester.md`. `git diff --stat origin/main...HEAD -- subagent-profiles AGENTS.md .agents
.claude permission-matrix.md docs/security-baseline.md` is empty. Nothing in the diff addresses a
reviewer, so there is no injection-class finding. The only removed test lines
(`git diff origin/main...HEAD -- tests`) are two lines of the `test_registry_derived.py` module
docstring, whose claim the fix corrects. No test was weakened or deleted.

**Families:** the author is recorded as Claude, and this seat is also Claude. No second family was
available to me, so this is the fallback. My context was fresh: I did not see the author's session
or the first review seat's session.

**Snapshot.** Every result below is against HEAD `8463f74` and these md5s, identical in the
repository and in my copy at the start and at the end:
- `registry.py` `8f065f54...`
- `refresh_job.sh` `96c461bb...`
- `test_registry_derived.py` `d2743a5a...`
- `test_registry.py` `fd767bcb...`
- `test_refresh_job_install.py` `b995d3bd...`

The owner's `advisor.db` and `advisor.db.refresh.json` were `214139e9...` and `d729a3f6...` before
and after my work. I read them only as copies in my own scratch subdirectory.

**How I worked:**
- I made an `rsync` copy of the tree in a NEW subdirectory of the session scratch directory. The
  copy left out the two untracked root files that are not this branch's (an HTML page and a Markdown
  note), and every bytecode cache.
- The copy's editable-install `.pth` was repointed at the copy's own `src`. I confirmed that
  `import app.workflows.registry` resolves inside the copy.
- `make` ran with `-o install -o .venv/bin/python`.
- I downloaded `https://epoch.ai/data/benchmark_data.zip` once into my subdirectory: HTTP 200,
  2,306,818 bytes, 84 top-level entries unpacked.
- I built a fresh candidate: `python -m app.workflows.build --db <scratch>/c.db --epoch-dir
  <scratch>/epoch`, with live upstreams.
- I ran one real refresh cycle on a copy of the served artifact with exactly the wrapper's new
  command (`--fetch-epoch`).
- I replayed the two red commits from `git archive` exports.

I made no git state change and started nothing on :8080. I read the installed launchd wrapper and
plist only. The only repository file I created is this one. `git status --short` shows the same two
untracked files before and after, plus this record.

## Verdict

**PASS-WITH-MINORS: 0 BLOCKING, 0 MAJOR, 3 MINOR, 2 NIT.**

**What this round got right.**
- **BLOCKING-1 is closed where it acts: on today's data.** I grouped every name that no curated
  rule takes by its derived id: 1,323 ids from all pricing aliases and score names of a fresh
  build. That covers all 242 registered ids and every one of the 505 multi-member groups.
  - **No derived id joins two version, variant, size, date or effort tokens.** Every member of
    every group that differs by more than case, route or separators is listed in "The merge hunt"
    below.
  - **No registered id has price routes that name two different model vendors.**
  - **51 adversarial pairs** of intended-different products gave 50 distinct ids. The one
    collision (`openai.o1-v1:0` and `openai.o1`) is one product, so my pair was wrong, not the
    grammar.
- **The previous seat's reproductions are now red tests.** Eleven of my twelve grammar mutants (M1-M12) go RED,
  including the pre-fix behaviour restored line by line (M2, M3, M5).
- **MINOR-1 is closed.** The counts are consistent on real data.
- **MINOR-2 is closed.** All five of the previous seat's GREEN mutants are now RED.
- **The median table matches my refused cycle** on 7 of 8 moved surfaces exactly (MINOR-3).

**What remains:**
- **The stated residual is honest in kind but understated in reach (MINOR-1).** Undated and moving
  API aliases are registered today on exactly the basis the amendment describes. There are more of
  them than its two examples, and "spell identically" undersells the grammar's own part, because
  the route is removed first.
- **MAJOR-1 is fixed in the tree, but the job that runs executes an installed COPY of the wrapper
  (MINOR-2).** That copy still passes the hand-kept bundle. The reinstall step is written nowhere
  on the branch.
- **Two of the fix's load-bearing lines are unpinned (MINOR-3).** One is the "Bedrock tag only after
  a head" guard. The other is the wrapper test, which is a text grep.

## Disposition of the review's findings

| Review | Disposition | Evidence I ran |
|---|---|---|
| BLOCKING-1 (the grammar strips `-vN`, `:x`, `@x` and vendor heads; products merge) | **CLOSED** (residual: MINOR-1) | `registry.py:344-359`: closed lists. `:392-397` `_decorated` keeps any non-listed suffix as a token. `:400-410` `_without_heads` drops a vendor head only before its family word. `:425-426` `ft:` gives None. `:429-430` `-v1`/`-v1:0` is stripped only when routed. Replay of `9e0b760` on the pre-fix `src`: **13 FAIL**, which are 8 of the 9 `never_derive_one_id` cases, the vendor-head, Bedrock-tag, fine-tune, `deepseek-v5` + `DeepSeek-V2` and negative-count tests. All are green at HEAD. On live data: `deepseek-coder-v2` and `deepseek-coder` are apart, and `mistral-7b-instruct` v0.2, v0.3 and the undated name are three ids (`mistral7b-instruct-v0.2`, `mistral7b-instruct-v0.3`, `mistral7b-instruct`). The three texts are corrected: `registry.py:333-341`, the test docstring `:8-11` and D-157's amendment. |
| MAJOR-1 (the launchd wrapper never fetches) | **CLOSED in the tree; OPEN in the field** (MINOR-2) | `scripts/refresh_job.sh:25` passes `--fetch-epoch`, and no `EPOCH` variable is left. Test `test_refresh_job_install.py:62`: replay of `24a0c72` gives 1 FAIL on the pre-fix wrapper. My M14 is RED. I ran the new command on a copy of the served artifact: it fetched, then **exit 3**, refused by D-132 as the record predicts, and left no scratch. The installed copy that launchd runs is unchanged (MINOR-2). |
| MINOR-1 (`scores_dropped` can be negative) | **CLOSED** | `registry.py:588-593`: the totals are taken before any row changes. Test `test_registry_derived.py:159` FAILS at `9e0b760` and is green at HEAD. M13 (recount after the links) is RED. On a reset copy of my fresh build: `reconcile` gives 937 matched + 489 dropped = 1,426 distinct `(raw_name, effort)` pairs taken before, and 2,173 + 1,232 = 3,405 aliases. 489 pairs and 652 rows stay NULL afterwards. |
| MINOR-2 (five unpinned load-bearing lines) | **CLOSED** | Killer tests `test_registry.py:559` (Fable guard), `test_registry_derived.py:171` (curated exclusion), `:177` (vendor from the route), `:183` (`models_registered`) and `:188` (`_none`/`_minimal`). The previous seat's M21, M23, M29, M31 and M32, re-applied as my M16-M20, are all RED. |
| MINOR-3 (the median move is not in the record) | **CLOSED** (one stale number: NIT-2) | The record gains the median table (`m16-w4-derived-registry-2026-09-23.md`, "Median price per surface") and the two-guard paragraph. My refused cycle gives the same eight surfaces. Seven match to the cent: assistant $2.95 → $0.83 (-72%), computer-use -45%, everyday -64%, expert -68%, factuality -56%, mathematics -67%, vision -48%. The eighth, web-dev, is $2.98 → $1.67 (-44%) against the record's $1.69 (-43%), which is live upstream movement between the two runs. The PR line is still owed: no PR exists yet for this branch. |
| NIT-1 (drift lines repeat the source name) | **OPEN** | `build.py:392` and `:451` are unchanged. Carry it to the close record. |
| NIT-2 (the grammar's display and vendor choices) | **RECORDED** | This is D-157's stated cost. The Nova models still display as `amazon.nova-lite-v1:0`, and so on. |
| NIT-3 (the bundle-gated tests pin 2026-08-15) | **OPEN** (queued to the closure) | Not touched on the branch. Carry it to the close record. |

## The merge hunt (BLOCKING-1's hardest question)

**Method.** From my fresh build (`c.db`: 3,405 aliases, 2,581 score rows), I mirrored `reconcile`
exactly:
- **Aliases:** `canonicalize_with_reason`, then `derive_identity`.
- **Score names:** `split_harness`, then `resolve_effort`, then `canonicalize_with_reason`, then
  `derive_identity`.

I kept every name no curated rule takes and grouped the names by derived id. The results:
- **1,323 ids.** 242 of them are registered, which equals the build report's `derived` (242).
- **317 models and 652 of 2,581 score rows unmatched**, exactly the record's numbers.
- **505 ids have more than one member.** I sorted them into three classes:

1. **Token-removing groups.** In these, the members differ by more than case, route and separators.
   There are 102; I read every member.
   - Every removal is from the closed list: a region head, a vendor head before its family, a
     routed `-v1`/`-v1:0`, `:batch`, `@latest` or `@default`, or the underscore effort.
   - The joined names are one product in every case except `claude-instant` (below).
   - The Bedrock `-v2:0` Sonnet (`claude3.5-sonnet20241022-v2.0`), `gpt-oss-120b-1:0`,
     `deepseek.v3.2` and `nvidia.nemotron-*` stay apart as splits.
2. **Separator-only groups.** These are joined only by the `5-5` → 5.5 and `gpt-6` → `gpt6`
   rules. There are 32, for example `llama-3.1-405b`/`llama3.1-405b`, `grok-4-1`/`grok-4.1` and
   `starcoder-2-15b`/`starcoder2-15b`. All are one product.
3. **Route and case groups.** I checked every registered id's price routes against
   `_VENDOR_SLUGS`. No id carries two known model vendors; the extra segments are hosts and regions
   (`models`, `us-gov-west-1`, `eu`, `perplexity`).

**Adversarial pairs.** I ran 51 pairs of different products through `derive_identity`:
- `:high`/`:low`, `qwen3:8b`/`:32b`, `:thinking`/`:beta`/plain, `@001`/`@002`/`@latest`;
- `v0:1`/`v0:2`, `claude-v2:1`/`claude-v2`/`claude-v21`, `deepseek-v2`/`v2.5`;
- routed `-v1` against `-v2:0`, `deepseek.r1` against `r1`;
- `llama-3-1-8b`/`llama-3-18b`, `model-1-2`/`model-12`, `gemma:2b`/`gemma-2-2b`;
- `ft:` in three spellings, the `ca.` and `sa.` region heads, `gpt-5 @ high`, and others.

50 of the 51 pairs gave distinct ids. The one collision, `openai.o1-v1:0` and `openai.o1`, is one
product.

**What the grammar still joins, and whether the amendment states it.** The registered ids whose
price alias and score name are undated or moving names include:
- the amendment's own `claude3.5-sonnet` (the price routes are OpenRouter, Vertex, Snowflake,
  Replicate and Vercel; the scores are ECI and a 2024-06-20 SWE-agent run) and
  `mistral7b-instruct`;
- `deepseek-chat` and `deepseek-reasoner` (DeepSeek's API aliases, scored by Epoch in 2026-07 and
  2025-12);
- `command-r`, `command-r-plus` and `mistral-medium` (Arena scores, current LiteLLM aliases);
- `gpt4-turbo`, `gpt4o-mini`, `o1`, `o1-mini` and `yi-large`;
- `claude-instant`: Bedrock's `anthropic.claude-instant-v1` with Epoch's undated "Claude Instant".

For each of these, the names do not say whether the score and the price are the same release. That
is exactly the amendment's residual, and the amendment says so honestly. It names two examples,
though, and "names two sources spell identically" undersells the reach (MINOR-1).

## Mutants

Every mutant was applied in place to the copy, one at a time. I replaced one unique string,
refusing any string that did not match exactly once. I ran the four registry and wrapper test files
on the mutant, and the full suite with `-n auto` whenever those stayed green. Then I wrote the
original bytes back and asserted the md5 equal. No restore failed. Afterwards, `diff -rq` of the
copy's `src`, `tests` and `scripts` against the repository was empty.

| # | Mutant (load-bearing line) | Result |
|---|---|---|
| M1 | `registry.py:397` `_decorated` strips every suffix | RED, 6 (`never_derive_one_id` `names1`-`names6`) |
| M2 | `:427` everything after `@` stripped (the pre-fix line) | RED, 2 (`@001`/`@002`, `@20240620`) |
| M3 | `:431` everything after `:` stripped (the pre-fix line) | RED, 5 |
| **M4** | **`:429` `if routed:` becomes `if True:` (the Bedrock tag stripped without a head)** | **GREEN, full suite** (MINOR-3) |
| M5 | `:430` any `-vN:M` stripped after a head | RED, 2 (`claude-v2`, the Mistral v0.2 test) |
| M6 | `:407` a vendor head dropped before any word | RED `test_registry_derived.py:136` |
| M7 | `:425` `ft:` derived | RED `:146` |
| M8 | `:408` `routed` never set | RED, 2 (`:41[global…-v1:0]`, `:141`) |
| M9 | `:357` `:thinking` added to the decorations | RED `:131[names5]` |
| M10 | `:397` a numeric `@`/`:` suffix treated as decoration | RED, 5 |
| M11 | `:408-409` only one dotted head removed | RED, 2 (`:41`) |
| M12 | `:344` `us` not a region head | RED `:41[us.anthropic…]` |
| M13 | `:646` (the return): the score total recounted after the links (MINOR-1 reverted) | RED `:159` |
| M14 | `refresh_job.sh:25` passes `--epoch-dir "$HOME/epoch_bundle"` | RED `test_refresh_job_install.py:62` |
| **M15** | **`refresh_job.sh:25` the flag commented out: `--db … # --fetch-epoch`** | **GREEN, full suite** (MINOR-3) |
| M16 | `registry.py:58` the Fable 5 parent without its version guard (prior M21) | RED, 3 (`test_registry.py:559`) |
| M17 | `:530` curated ids not excluded (prior M23) | RED `test_registry_derived.py:171` |
| M18 | `:443` vendor from the route disabled (prior M29) | RED `:177` |
| M19 | `:646` `models_registered` omits derived (prior M31) | RED `:183` |
| M20 | `:362` `_none`/`_minimal` not decoration (prior M32) | RED `:188` |

**Totals:** 20 mutants: 18 RED and 2 GREEN (MINOR-3). None is equivalent.

**Killer tests.** I wrote two tests in scratch, not in the repository. Each passes on HEAD and is
RED on its mutant; the md5 check after that run matched too. They are in MINOR-3.

**Is M4 a live defect?** I applied M4 in process to the same 1,323-id grouping. It changes only
four ids: `nova-lite`, `nova-micro`, `nova-pro` and `nova2-lite` absorb the unrouted
`amazon/nova-*-v1` spellings, which are the same products. So today M4 would reduce splits, not
merge anything. The GREEN is a pin gap on a stated contract ("only after its prefix", `registry.py:335`),
not a live merge.

**Red to green, replayed** (`git archive` of each red commit, its own `src`, the copy's venv):
- `9e0b760`: **13 FAIL**, 50 pass. The one `never_derive_one_id` case that passes pre-fix is
  `names8` (NIT-2).
- `24a0c72`: **1 FAIL** (`test_refresh_job_install.py:62`).

All are green at HEAD.

## Findings

### MINOR-1 -- the stated residual is honest in kind but understated in reach

The amendment (`docs/decisions.md`, D-157 amendment, last sentence), the module comment
(`registry.py:340-341`) and the record ("What the grammar cannot see") say:
- names two sources spell identically are one model;
- this holds even where a vendor reused the name;
- the examples are `claude-3.5-sonnet` and `mistral-7b-instruct`.

That is true, and it is the only class of merge I found. Two things are understated:
- **The reach.** At least eleven more ids are registered today on the same basis, because their
  names are moving API aliases, listed above: `deepseek-chat`, `deepseek-reasoner`, `command-r`,
  `command-r-plus`, `mistral-medium`, `gpt4-turbo`, `gpt4o-mini`, `o1`, `o1-mini`, `yi-large` and
  `claude-instant`.
  - A score under such a name was measured on whichever release the alias meant on the run date.
  - The price is whatever the alias means today. Examples: `deepseek-chat` is scored by Epoch GPQA
    on 2026-07-16, and `mistral-medium` is Arena's.
  - That is the "vendor reused the name" case, repeated across every undated alias. The reader of
    the record sees two instances, not a class.
- **"Spell identically"** is before the grammar removes the route, case and separators. The
  grammar makes `vertex_ai/claude-3-5-sonnet`, `openrouter/anthropic/claude-3.5-sonnet` and
  `snowflake/claude-3-5-sonnet` identical. Where a host's undated id means a different release than
  another host's, the ROUTE was the only carrier of that fact, and the grammar removes it first.

**Why MINOR and not higher:**
- No grammar could split these; the sources do not.
- The amendment names the class and the only remedy (a curated rule).
- On today's data, the prices joined under `claude3.5-sonnet` are equal ($3/$15; Replicate
  $3.75/$18.75).

It matters because D-157's revisit trigger is "a derived registration is found merging two
different models", and this is the one way that trigger can still fire. The owner should read the
reach before the deliberate publish.

*Remedy:* in the research record, list the undated-alias ids registered today as the residual's
current instances, one line each, or count them. Reword "spell identically" to "spell identically
once the route, case and separators are removed". No code change.

### MINOR-2 -- the running refresher executes an installed copy of the wrapper, which still passes the hand-kept bundle; the reinstall step is written nowhere

The plist `com.hcs.modelranking.refresh` runs `/bin/bash "~/Library/Application
Support/model-ranking/refresh_job.sh"` (`ProgramArguments[1]`). That is the copy
`scripts/install_refresh_wrapper.sh` writes, not `scripts/refresh_job.sh`. Read-only, the installed
copy still has `EPOCH=".../epoch_data"` (line 18) and `--epoch-dir "$EPOCH"` (line 24).

So merging this branch changes nothing on the owner's machine until he runs
`scripts/install_refresh_wrapper.sh`. The review's remedy (b) said so ("have the owner reinstall
it"). The fix commit, the test and the research record do not, and no PR body exists yet.
The consequence is the original MAJOR-1: the deliberate publish, then every cycle refused against
the stale bundle.

The order also matters:
- **Reinstalled before the deliberate publish:** the job fetches and is refused by D-132 every
  cycle until the publish (measured: exit 3). That is by design.
- **Reinstalled after it:** the stale-bundle refusals start at once.

*Remedy:* put one line in the PR's "After merge" list and in the close record, with its order:
"run `scripts/install_refresh_wrapper.sh` at or before the deliberate publish". `install_refresh_wrapper.sh`
prints the `launchctl kickstart` line to prove it through launchd.

### MINOR-3 -- two of the fix's load-bearing lines are unpinned

- **M4 is GREEN.** Nothing asserts that an UNROUTED `-v1` stays a token. The module comment
  (`registry.py:335`), the amendment and the record all state the restriction "only after its
  prefix", and the previous seat's remedy step 1 asked for exactly that. Killer (verified: GREEN on
  HEAD, RED on M4):
  ```python
  def test_an_unrouted_v1_is_a_version_not_decoration() -> None:
      assert _id("claude-v1") != _id("Claude")
  ```
- **M15 is GREEN.** `test_refresh_job_install.py:62` asserts `"--fetch-epoch" in text`, over the
  whole file. A command with the flag commented out, or moved to a comment line, passes it. Killer
  (verified: GREEN on HEAD, RED on M15): take the one non-comment line that runs
  `app.workflows.refresh`, `shlex.split(line, comments=True)`, and assert `--fetch-epoch` in the
  tokens and `--epoch-dir` not.

## NITs

### NIT-1 -- `anthropic.claude-v1` derives to the bare family word `claude`

The routed `-v1` strip removes Claude 1's generation token: 4 live aliases
(`anthropic.claude-v1`, `bedrock/*/anthropic.claude-v1`) derive to `claude`. The unrouted
`claude-v1` stays `claude-v1`. Nothing is registered under `claude` today (no score name derives
to it). But any board that ever names a model just "Claude", or an `X + Claude` harness row, would
be priced as Claude 1 on Bedrock.

The same strip gives `claude-instant` (registered, see MINOR-1). This is the one place where
Bedrock's `-v1` is a model generation rather than an API tag. A curated `claude-1` rule, or no
`-v1` strip when the remainder would be a bare family word, closes it.

### NIT-2 -- three small text defects

- **A stale number in the research record.** Its "Why the nightly refresh will not publish this"
  says "`assistant` is 123 of 188". Its own table says 189, and my refused cycle says "124 of 189".
  The 123/188 pair is the pre-fix measurement.
- **A test case that never reproduced the bug.** `test_registry_derived.py:129` (`names8`,
  `us.deepseek.r1-v1:0` against `deepseek.v3-v1:0`) passes on the pre-fix code, because it gave
  `r1` and `v3`: distinct bare tokens, not a merge. The defect it names is pinned by `:136`
  instead. Either drop the case or pair it with `r1`.
- **Clause 2 of D-157 still says the grammar removes "dates"** (`decisions.md:2618`). No version of
  the grammar ever did. The amendment's closed list supersedes that wording, but it does not say it
  corrects it. One clause would.

## Hardened-invariant producer section (Code-Reviewer §2a-bis)

**Invariant 1 (D-157 clause 3, as amended): no two products share a derived id; the grammar
removes only the closed list.**
- There is one producer: `derive_identity` (`registry.py:413`), with its helpers `_decorated`
  (`:392`) and `_without_heads` (`:400`), and the lists at `:344-359`.
- It has one consumer: `_unmatched` (`registry.py:559`), which stages the id for `_Pending`.
- Citing tests: `test_registry_derived.py:41`, `:50`, `:54`, `:131`, `:136`, `:141`, `:146`,
  `:150` and `:188`.
- Gaps: MINOR-3 (M4), and the residual class (MINOR-1), which no grammar can see.

**Invariant 2 (D-157 clause 1): the curated rules win.**
- The producer is `_Pending.ready` (`registry.py:530`).
- Citing tests: `test_registry_derived.py:109` and `:171`. M17 is RED.
- Gaps: none found.

**Invariant 3 (REQ-CAN-001, as amended): the drop counts are totals of the same pairs, taken at
one moment.**
- The producer is `reconcile` (`registry.py:588-593`, and the return at `:646`).
- Citing test: `test_registry_derived.py:159`. M13 is RED.
- The live invariant holds: 1,426 = 937 + 489.

**Invariant 4 (D-158): the refresher that runs fetches Epoch.**
- The producers are `scripts/refresh_job.sh:25`, and `adapter/nightly.py` (unchanged).
- Citing test: `test_refresh_job_install.py:62`. M14 is RED; M15 is GREEN (MINOR-3).
- Gap: the installed copy (MINOR-2).

**Symbol check** (`grep -n "_REGION_PREFIXES\|_VENDOR_FAMILIES\|_COLON_DECORATION\|_AT_DECORATION\|def _decorated\|def _without_heads\|_DOTTED_PREFIXES" src/app/workflows/registry.py`):

```
344:_REGION_PREFIXES = frozenset({"us", "eu", "au", "jp", "apac", "global", "us-gov", "ca", "sa"})
348:_VENDOR_FAMILIES: dict[str, tuple[str, ...]] = {
357:_COLON_DECORATION = frozenset({"batch", "free", "nitro", "floor", "exacto"})
359:_AT_DECORATION = frozenset({"default", "latest"})
392:def _decorated(text: str, mark: str, decoration: frozenset[str]) -> str:
400:def _without_heads(text: str) -> tuple[str, bool]:
```

`_DOTTED_PREFIXES` is gone, with no caller left behind. `derive_identity` keeps its signature
(`:413`), and its only caller is unchanged.

**Other branch changes, each read:**
- `.path-refs-allow` gains `docs/plans/m*-wave-*-plan.md`. It is narrow, it carries its reason,
  and it matches DevFlow's rule that a working plan leaves the default branch.
- `docs/plans/m16-plan.md:131` names the close record, which the lead writes next.
- The deleted `docs/plans/m16-wave-4-plan.md` is referenced only by review records, which the new
  glob covers.

## K.9 candidates outside this round's scope

- **`split_harness` still credits an architect pair to its editor model.** "DeepSeek R1 +
  claude-3-5-sonnet-20241022" is one of the two score names of the registered
  `claude3.5-sonnet20241022`. This carries over from the previous review, and it predates the wave.
- **`_derived_vendor`'s family fallback and its "Other" return (`registry.py:448-451`) are not
  executed by any test** at HEAD: coverage lists `448-451` as missing. The route test pins the
  first half; the fallback, which assigns 23 models to "Other", has no citing test.

## Gates

`make -o install -o .venv/bin/python check-fast` on the copy, 16 s:
- **python leg PASS:**
  - lint: ruff "All checks passed!".
  - typecheck: mypy "Success: no issues found in 35 source files".
  - test: pytest **1165 passed, 15 skipped**, total coverage 90.04%. `registry.py` is at 95%; its
    missing lines are 309, 436, 448-451 and 571.
  - coverage-floor: "PASS: 35 module(s)".
- **client leg PASS:** client-decls.
- **records leg FAIL, 1 of 14 conformance tests.** check-records, its self-test, install-check,
  harvest-context-check, shell-dialect ("11 script(s)") and wave-check-all ("42 … record(s)")
  PASS. The one failure is `test-documented-paths`: 1 dangling, `docs/plans/m16-plan.md:131`
  names the wave's close record, which does not exist yet. This is the expected failure; the lead
  writes that record after this review. **Nothing else failed.**
- **swift leg:** FAIL on the first run, because the copied `ios/.build` module cache is bound to the
  repository's path (an artifact of the copy). After removing that cache in the copy,
  `make swift-test-parallel` passed: "PASS: 268 test(s), exactly the ones named in the manifest".

## What I did not check

- **A night on the owner's machine.** I ran one refresh cycle on a copy, not a scheduled night
  through launchd, and I did not run `install_refresh_wrapper.sh`.
- **Whether each alias-class pair in MINOR-1 is really two releases.** That needs each board's
  run-date roster and each host's alias history. I report the class and the names, not a per-pair
  verdict.
- **The per-surface picks table** in the research record. I reproduced 317 models, 242 derived and
  652 of 2,581, the new-names percentages and the medians, not the picks.
- `make check` (the merge gate). I ran `check-fast` as instructed. `secrets`, `deps`, `slopsquat` and
  `falsify` are not in `check-fast`, and I did not run them separately.
- Security (Stage 4.0). This round touches no fetch or archive code.
