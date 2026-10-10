---
record_type: review
id: m21-wave-1-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-09
---
# M21 Wave 1 Code Review, round 2 (the data a reader sees)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-09
**Commit range:** `cdc523e..d776a1e` (this round: red `13b955e`, fix `73a8e82`, rename `d776a1e`), read
against the whole wave `972b55e..d776a1e`
**Risk tier:** HIGH

Routing: the author and reviewer are both claude-code (local lane, per the commits' `GP-Agent`). No
second family was available to this seat. The context is fresh: this seat read the round-1 record,
the plan's W1 rows, D-189, issues #230 to #232 and the two commits. It did not read the author's
summary before the code.

## Verdict
MINOR

Every round-1 finding is closed in code and in the refreshed artifact:
- `everyday`'s ECI board now ranks DeepSeek R1 at its own 138.97, and R1-0528 at 141.29.
- The 8B distill's three rows sit on a model of their own.
- Mistral Large is five models, priced 4/12, 2/6, 2/6, 0.438/1.312 and 0.68/2.09.
- Claude Sonnet 4 is ranked at its own 1350.8 (`arena`) and 141.69 (ECI).

The limiter's one entry per client is bounded, per client, and charges no refusal. The deploy fails
closed and still deploys only `origin/main`'s tip (`scripts/deploy_hosted_engine.sh:42-48`,
unchanged).

What is left is smaller:
- The new GLM-4.6V rule merges one model and drops another spelling (M1).
- The distill rule misses the Fireworks spelling round 1 named (M2).
- Five planted faults survive the tests (M3, M4).
- One line of the architecture record lags (M5).

None of these misranks a model in today's artifact.

## How it was checked

- **Round 1 against the code.** Read `docs/reviews/m21-wave-1-review-round-1.md`, then
  `git show 13b955e` and `git show 73a8e82`. Read issues #230, #231 and #232 with `gh issue view`.
- **Every name in the artifact through both registries.** All 5,260 distinct score names and price
  aliases in the worktree's `advisor.db` went through round 1's registry (`e7e7a1a`) and through
  HEAD's, using `canonicalize_with_reason` and then `derive_identity`. 83 names changed. Each one
  was read; the questionable ones are M2 and the note under M3.
- **Made-up names against the curated rules.** About 120 names were probed for the R1, Mistral
  Large, Sonnet 4/4.6 and GLM rules. They included dated, effort, size, distill and provider
  spellings, and future minors. Reconcile's own path (`split_harness`, then `resolve_effort`) was
  traced for the GLM-4.6V spellings.
- **The research note's twice-ranked query.** Ran it on the artifact. Every candidate it lists that
  is not split here is in #232, apart from dated snapshots D-189 keeps gathered.
- **The deploy refusal.** The deploy tests run the deploy script, so this seat did not run them.
  Instead it copied lines 57-77 of the script, the record read and the refusal, into a scratch
  script. That copy ran in a scratch repository against 14 records:
  - accepted: a record naming HEAD's release, and one with a longer sha;
  - refused: another release, a missing record, a JSON list, a number, a value with a newline, a bare
    `release-`, and a `dev-` build;
  - accepted only when `DEPLOY_ACCEPT_DATA_FROM` named that exact value.
- **Tests.** 358 passed, 4 deselected (the deploy-running tests), over these files:
  - `test_registry.py`, `test_moving_aliases.py`, `test_registry_derived.py`;
  - `test_rate_limit.py`;
  - `test_categories.py`, `test_webdev_board.py`, `test_families.py`;
  - `test_data_release_stamp.py`.
- **Planted faults.** Planted 16 faults. Each file was restored by its bytes and checked by sha256.
  Each run used a fresh `PYTHONPYCACHEPREFIX`. A first pass without one ran a stale `.pyc`: two
  plants of the same size, written within one second. After the restores, `git status` was clean,
  and the hashes were:
  - `registry.py` `288fc580`
  - `main.py` `5920a330`
  - `categories.py` `e28654b2`

| Plant | Result |
|---|---|
| R1-0528 loses `\(may 2025\)` | caught |
| Large 3 loses `2512` | caught |
| Large 2.1 loses `(Nov 2024)` | caught |
| a catch-all `mistral-large` rule after Large 1.0 | caught |
| `web-dev` back to 100.0 / 6.8 (round 1's M1) | caught |
| a refusal charges the count | caught |
| every path charged to questions | caught |
| standings keyed per path, apart from the client's entry (round 1's R1) | caught |
| one boards window for every client (round 1's M2) | caught |
| a refusal logged every time | caught |
| the size alternative dropped from `_NOT_A_DISTILL` | **survived** (M3) |
| the R1-0528-Qwen3-8B rule removed | **survived** (M3) |
| Sonnet 4's lookahead back to `(?![.\-]?5)` | **survived** (M3) |
| a new minute resets only the count it charges | **survived** (M4) |
| Sonnet 4.6 loses `(?!\d)`; `glm-4.6` loses `(?!v)` | survived, but dead: the rule before it wins (not a finding) |

## Round 1's findings

| Finding | Closed by | Evidence |
|---|---|---|
| B1 | `registry.py:189-190` | `test_registry.py:692`; plant caught; artifact: R1 at 138.97, R1-0528 at 141.29 on `epoch_eci` |
| B2 | `registry.py:66`, `:187-192` | `test_registry.py:725-733`; artifact: the distill's 3 rows apart (M2 and M3 remain) |
| B3 | `registry.py:97-98`, `:213-226`, `:549`; `decisions.md:4530-4546` | `test_registry.py:736-776`; 3 plants caught; #232 holds the other candidates |
| M1 | `test_categories.py:543`, `:555` | plant caught |
| M2 | `main.py:828-829`; `test_rate_limit.py:384`, `:392` | plant caught |
| M3 | `architecture.md:75-78`, `:491-493`; `security-invariants.md:167-168` | `architecture.md:15` lags (M5) |
| M4 | `deploy_hosted_engine.sh:67-77` | `test_data_release_stamp.py:66`, `:84` (read, not run); this seat's 14-case run |
| K1 | #230 | filed |
| K2 | `registry.py:212-213`; #231 | `test_registry.py:779`; M1 remains |
| R1 | `main.py:217-224`, `:297-323` | `test_rate_limit.py:401`; plant caught |

## Findings

### BLOCKING

None.

### MINOR

- **M1** `src/app/workflows/registry.py:212`, `tests/unit/test_registry.py:779-785`. The new
  `glm-4.6v` rule, `glm[-_ ]?4[.\-]?6v(?!\w)`, merges too far on one side and splits too far on the
  other.
  - **Scenario: the merge.** `-` is not a word character, so `glm-4.6v-flash`, `zai/glm-4.6v-flash`
    and `GLM-4.6V-Flash (thinking)` all canonicalize to `glm-4.6v`. GLM-4.6V-Flash is the 9B model
    Zhipu publishes beside the 106B GLM-4.6V. That size figure is this seat's knowledge; with no
    network, it did not re-read Zhipu's page. Once a price list carries it, its price joins
    GLM-4.6V's median, and a board that ranks both ranks GLM-4.6V twice. That is B2's and K2's class,
    in a rule this round wrote. The test lists `zai/glm-4.6v-flash`, but its added assertion is
    skipped for `flash`, so it accepts either answer.
  - **Scenario: the split.** `_` is a word character, so Epoch's spellings `glm-4.6v_32K` and
    `glm-4.6v_unknown` take no rule. `resolve_effort` leaves both unchanged; the artifact holds 74 such
    Epoch names, among them `claude-sonnet-4-6_unknown`. They derive `glm4.6v32k` and `glm4.6v`, which
    have a score but no price, so the row is dropped. Every other curated rule takes these
    spellings. Epoch already ranks GLM-4.6 on two boards.
  - **Fix.** Use `glm[-_ ]?4[.\-]?6v(?![a-z\d])(?![-_ ]?flash)`. Assert that `glm-4.6v-flash` is
    not `glm-4.6v`, and that `glm-4.6v_32K` is.

- **M2** `src/app/workflows/registry.py:187-188`. The distill's own rule misses Fireworks'
  spelling, one of the two aliases round 1's B2 named.
  - **Scenario.** `deepseek[-_ ]?r1[-_ ]?0528[-_ ]?qwen3[-_ ]?8b` does not take
    `fireworks_ai/accounts/fireworks/models/deepseek-r1-0528-distill-qwen3-8b` (0.2/0.2). That alias
    derives `deepseek-r1-0528-distill-qwen3-8b`, which has no score, so the price is dropped. The
    curated distill is therefore priced at Novita's 0.06/0.09 alone. One model under two names, only
    one reached.
  - **Fix.** Use `deepseek[-_ ]?r1[-_ ]?0528[-_ ]?(?:distill[-_ ]?)?qwen3[-_ ]?8b`. Assert that
    both of round 1's aliases reach `deepseek-r1-0528-qwen3-8b`.

- **M3** `tests/unit/test_registry.py:725-733`, `:736-765`. Three of the new rules' clauses are held
  by no test (plants above).
  - **Scenario.**
    - Dropping the size alternative from `_NOT_A_DISTILL` (`registry.py:66`) puts
      `llamagate/deepseek-r1-8b` (0.1/0.2) back in R1's price median. Round 1's B2 named that alias,
      yet every registry test still passes. The distill test's six names are each refused by
      `distill`, `qwen` or the distill's own rule, so none of them reaches the size clause.
    - Removing the R1-0528-Qwen3-8B rule passes too: the test accepts `None`.
    - Sonnet 4's new lookahead claims "a minor version after 4 (one digit, not a date) is another
      release". Reverting it passes as well: `claude-sonnet-4-7` goes back to Sonnet 4. In today's
      artifact the lookahead changes one name, `databricks/databricks-claude-sonnet-4-1` (3/15).
      That name is now dropped instead of joining Sonnet 4, which is the safer side.
  - **Fix.**
    - Add `llamagate/deepseek-r1-8b` and `deepseek-r1:8b` to the distill test.
    - Assert `deepseek-r1-0528-qwen3-8b` for the three Qwen3-8B spellings.
    - Assert that `claude-sonnet-4-7` is not `claude-4-sonnet`.

- **M4** `src/app/adapter/main.py:311-312`, `tests/unit/test_rate_limit.py:104`. No test holds that
  a new minute resets both of a client's counts.
  - **Scenario.** Planted `window[0] = minute; window[bucket] = 0` in place of
    `window = [minute, 0, 0, 0]`. All 36 rate-limit tests passed. Under that change, a phone that
    took four standings in one minute and asks a question first in the next keeps its standings count
    at 120. It is then refused `/v1/boards` for every minute that opens with a question. The R1 fix
    introduced this two-count entry, and `test_the_next_minute_serves_again` checks one count only.
  - **Fix.** Add a test with the clock held:
    - four `/v1/boards` answers in minute N;
    - one question in minute N+1;
    - then a `/v1/boards` answer, which must be 200.

- **M5** `docs/architecture.md:15`. Round 1's M3 is not wholly closed.
  - **Scenario.** The system diagram still says "six Arena boards"; line 75 now says seven. One fact
    in two places has already drifted.
  - **Fix.** Say "seven Arena boards" at line 15.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/registry.py:25-36` (`split_harness`), `src/app/workflows/families.py:23`.
  An Aider architect pair is credited to its editor model.
  - **Scenario.** `split_harness` reads `o3 (high) + gpt-4.1` as harness `o3 (high)` and model
    `gpt-4.1`. Rankings take a model's best row (`rank.py:206`, `:328`). So `aider`, a board in the
    `coding` family, ranks GPT-4.1 at the pair's 78.2 against its own 52.4. Likewise,
    `DeepSeek R1 + claude-3-5-sonnet-20241022` puts Claude 3.5 Sonnet (Oct) at 64.0 against its own
    51.6. No issue covers it: `gh issue list --search aider` finds none.
  - **Fix.** `/file-issue` it. The Aider client should drop or label an architect pair (`A + B` on
    that board is two models, not a harness and a model), with a red test on both rows.

- **K2** `src/app/workflows/registry.py:191-192`. The `deepseek-r1` rule has no boundary after
  `r1`.
  - **Scenario.** `DeepSeek-R1-Zero`, `deepseek-r1-lite-preview`, `tngtech/deepseek-r1t-chimera` and
    `deepseek-r1t2-chimera` are each a model of its own, and each canonicalizes to `deepseek-r1`.
    So does Volcengine's `deepseek-r1-250528`, which is R1-0528. B1's class: a date spelling the
    0528 rule does not read. None is in today's artifact.
  - **Fix.** Add the names to #232, or file them. Refuse `zero`, `lite` and a letter right after
    `r1`, and read `250528` as R1-0528, each with a red test.

## Risks queued to next M

- **R1** `scripts/deploy_hosted_engine.sh:72`. `DEPLOY_ACCEPT_DATA_FROM=unknown` names a class, not
  a release.
  - **The risk.** It covers a missing record, an unreadable one, and any artifact whose builder
    cannot be read. If the owner exports it for one deploy, a later deploy from a copy with no
    `.refresh.json` beside it passes without a word. The refusal running before the derivation is
    also held by no test: the test checks only that `fly` was not called.
  - **What would show it is real.** A hosted `/health` build ending `-from-unknown` after the Mac
    has refreshed under M21. The fix would be to refuse `unknown` when the record file is missing,
    or to read the acceptance from an argument rather than the environment.

- **R2** `src/app/workflows/registry.py:218-219`. `mistral-large-4(?!\d)` and
  `mistral-large-(?:3(?!\d)|2512)` would take a future `mistral-large-3.1` or `4.1`. Sonnet 4's rule
  was changed in this round to refuse exactly that. **What would show it is real:** a Mistral
  release named with a minor version, ranked by a board as its major.

## Acceptance criteria evidence

| Criterion | Code | Test | Status |
|---|---|---|---|
| #163 (REQ-CAN-001) | `registry.py:66`, `:97-98`, `:178-192`, `:212-226` | `test_registry.py:681-701`, `:725-785` | met; M1 to M3 |
| #164 | `registry.py:550-552` | `test_moving_aliases.py:161-166` | met (round 1) |
| #165 | `registry.py:334-336` | `test_registry.py:705-714` | met (round 1) |
| #124 | none in this wave | `test_attribution_terms.py` (M19-W1) | delivered by M19-W1 |
| #185 (REQ-SRC-010) | `categories.py:208-224`; `sources.py:226-235` | `test_webdev_board.py`; `test_categories.py:543`, `:555` | met |
| #198 (REQ-REL-003) | `refresh.py:789-797`; `deploy_hosted_engine.sh:55-81` | `test_data_release_stamp.py:56`, `:66`, `:84` (read, not run); `test_deploy_hosted.py:45-48` | met; R1 |
| #205 (REQ-REL-001) | `public.py:47-52` | `test_public_artifact.py:335` | met (round 1) |
| #214 | `boards.py:15` | `test_nightly_refresh.py:783` | met (round 1) |
| #216 | `coverage.py:207` | `test_coverage.py:436` | met (round 1) |
| #228 (REQ-REL-004) | `main.py:217-224`, `:297-323`, `:825-829` | `test_rate_limit.py:364`, `:374`, `:384`, `:392`, `:401` | met; M4 |
| #166 | `docs/research/m21-w1-first-nights-after-m19-w1.md` | none | met; #230 |

## Producers of hardened invariants

- **INV-88.**
  - Producers: `_limited` (`main.py:816`), `_client_key` (`main.py:279`) and `_over_limit`
    (`main.py:297`).
  - Citing tests: the 15 listed at `security-invariants.md:168`.
  - Gaps: M4 (a new minute's reset of both counts).
- **INV-87.**
  - Producer: `public.derive`, whose one caller is the deploy script, now behind the data-release
    refusal at `deploy_hosted_engine.sh:72`.
  - Citing tests: the 9 listed at `security-invariants.md:167`.
  - Gaps: none new.
- **REQ-CAN-001 / D-189.**
  - Producers: `MODEL_RULES` (`registry.py:69-240`), `canonicalize_with_reason` (`registry.py:318`)
    and `derive_identity` (`registry.py:564`).
  - Citing tests: `test_registry.py:697`, `:728`, `:762`, `:773`, `:780`.
  - Gaps: M1, M2, M3.

## K.8 contract drift check

Plan §5 says no `/v1` field changes. `git diff e7e7a1a..d776a1e -- src/app/adapter/main.py` adds or
removes no response key (0 lines matching `"key":`). The one changed signature is a test helper:
```
src/app/adapter/main.py:268:def rate_window_used(key: str, now: float, bucket: int = _QUESTIONS) -> int:
tests/unit/test_rate_limit.py:380:    assert main.rate_window_used("k", 600.0) == 3
```
Verdict: OK.
