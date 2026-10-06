---
record_type: review
id: m19-wave-1-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# Wave 1 Tester Review (m19)

**Reviewer:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records,
and it is not the wave's Code-Reviewer.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `dd68917..a182a53` (41 commits; 27 files, +1379 / -126). It includes the
Code-Reviewer's verdict (`379a17a`) and the author's fix round after it (`2283576` to `a182a53`).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:46-48`, `docs/plans/m19-wave-1-plan.md:13-15`). The diff
touches `src/app/clients/**`, a security glob (`m19-plan.md:130`). By D-172 no security seat runs on
the wave.
**Code-Reviewer verdict:** MINOR, M1 to M7, K1, R1 to R3 (`docs/reviews/m19-wave-1-review.md`). Not
BLOCKING, so this seat runs. This seat is the first to test the fix round.
**Model routing (HIGH, advisory):** author family: Claude (all 41 commits carry `GP-Agent:
claude-code/local-lane`) / reviewer family: Claude (Opus 5.5). Fallback reason: no second model family
is available to this seat. Fresh context: I started from the base profile and rules, then read the
plans, the eight issues, the code review and the diff. I have no memory of any authoring or reviewing
session.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75d...`) on
`origin/main` and in the worktree. `git diff --stat dd68917 a182a53 -- .claude .agents
permission-matrix.md .github epb.html or.md tests/conftest.py ios src/app/adapter` is empty. No commit
message in the range carries `Co-Authored-By` or "Generated with".

## Verdict
MINOR

**Nothing blocks.** Each W1 criterion (REQ-CAN-001, REQ-CAN-002, REQ-SRC-010) has a citing test that
exercises it and passes. Each of the eight issues has a test that fails on the pre-wave code with an
assertion (not only an import error) and passes at `a182a53`. `make check-fast` is green. No test was
weakened, skipped or deleted to get there. Every changed line in `src/` is covered.

**Fault injection: 18 of 21 faults killed before this review (85.7%), 21 of 21 after.** Every fault
was planted in place and reverted in place, and each file's sha256 matched before and after. The
three faults that stayed green are M1, M2 and M3. I wrote a test for each one. Each new test passes at
`a182a53`, fails on its fault, and fails on the pre-wave code. The tests are uncommitted in this
worktree, listed at the end.

**Six MINORs, one K.9, one risk.** M1 to M3 are closed once the author commits the three tests. M4
is the review's M4, one rule over: a GPT-5.2 Codex mini still folds into GPT-5.2 Codex. M5 is the
finding to read: on a night a price feed's data expires, D-179's board guards count rows the expiry
itself unlinked as rows lost. It fails closed. M6 is a citation gap.

## Acceptance-criterion coverage (REQUIRED)

The criteria are `docs/plans/m19-plan.md:38`. The wave plan's phase checks are
`docs/plans/m19-wave-1-plan.md:34-37`. Every citing test below is GREEN at `a182a53`.

- **REQ-CAN-001, one release is one model** → `tests/unit/test_registry.py:593`
  (`test_each_gpt5_minor_release_is_a_model_of_its_own`, cites REQ-CAN-001 at `:596`): GPT-5 mini,
  GPT-5.1 Codex mini and GPT-5.4 mini resolve to three models, as do GPT-5 and 5.4 nano and GPT-5.1 to
  5.3 chat (#162). `:632` (`test_a_release_with_one_snapshot_is_one_model`, under the module's
  `cite REQ-CAN-001` at `:1`): 59 spellings of 14 one-snapshot releases each reach their one model
  (#129). `:640`: Claude 3.5 Sonnet's two snapshots stay two. `tests/unit/test_access.py:60`: GPT-5's
  dated and undated names link to `gpt-5`. — GREEN
- **REQ-CAN-001, an effort is never a model of its own** → `tests/unit/test_registry_derived.py:251`
  (cites REQ-CAN-005): the grammar reads `o3-mini-high` and `grok-4.7-xhigh` as efforts and leaves
  `magistral-medium`, `qwen3-max` and `gpt-5.1-codex-max` whole. `:263`: Sonar's `-high` stays its
  name (review R2). `:272` (**added here**, cites REQ-CAN-001 and REQ-CAN-005): Arena's and OpenRouter's
  `o3-mini-high`, through `ingest_arena`, `ingest_openrouter` and `reconcile`, is stored as `o3-mini`
  at effort `high`, and no model `o3-mini-high` is registered. `:305` (**added here**): a derived
  model's served name carries no dash effort. — GREEN
- **REQ-CAN-001, named in its maker's spelling** → `tests/unit/test_display_names.py:124` (artifact
  test, ran against this seat's `advisor.db`): every model the served artifact holds, re-named by this
  code's own `reconcile`, is neither its raw id nor a lower-case spelling of it, and every Claude is in
  Anthropic's order. `:100`: the 74 ids #112 listed each have a table name. `:106`: each table name is
  bounded and wins for its model. The file cites #112, not the REQ-ID (M6). — GREEN
- **REQ-CAN-002, a variant never leaks into its parent** → `tests/unit/test_registry.py:35` (cites
  REQ-CAN-002 at `:36`): `gpt-5.1-codex-mini` is its own model, and `gpt-5.1-nano` and
  `gpt-5.5-thinking-mini` reach no parent. `:649`: GPT-5 Codex mini is neither GPT-5 mini nor GPT-5
  Codex (review M4). `:661` (**added here**, cites REQ-CAN-002): no GPT-5.1 to 5.6 parent rule takes a
  mini, nano, chat or Thinking variant, and none reaches GPT-5's variant. — GREEN
- **REQ-SRC-010, each attribution matches its publisher's terms or waits on #88 by name** →
  `tests/unit/test_attribution_terms.py` (cites REQ-SRC-010 at `:1`; the #88 boundary is stated at
  `:12-13`). `:45`: each of the five boards Epoch compiles names its original source and link, credits
  Epoch's compilation, and claims no CC licence. `:54`: SWE-bench is CC-BY-NC-4.0 and Aider is
  Apache-2.0, in separate strings. `:63`: each CC source links its material and its licence. `:71`:
  neither the pricing credit nor the OpenRouter client claims "attribution required". `:76`: no credit
  the app shows carries backticks or a file name (review M7). Also `tests/unit/test_recommend.py:136`
  (the README carries Epoch's citation and the licence link). — GREEN
- **Wave plan P1, #101 ("one test states the rule for both engines")** →
  `tests/unit/test_pareto_dominance.py:205`: one test holds the model engine and the plan engine to
  the ranking's order, then the stable id. `tests/unit/test_subscribe.py:698` and `:712` hold it
  through `recommend_subscription`: the value pick, the group's member order, the group's "cheapest"
  sentence and the cheapest pick. — GREEN
- **Wave plan P1, #106** → `tests/unit/test_build.py:569`: a derived `latest-v` id is registered, said
  in the build's drift, and `/health` reads its source as `registry` (review M3). — GREEN
- **Wave plan P2, #100 / D-179 (on REQ-REF-003, INV-54)** → `tests/unit/test_refresh_board_ids.py:73`
  (a re-spelled board moves no guard, on both kinds of board), `:78` (the night publishes and records
  the re-spellings), `:130` (new models, more rows for the same models, rows moved to other models,
  and a quarter lost still refuse), `:138` (a harness or effort relabel moves nothing), `:149` (an
  unlinked row is still compared by name), `:162` (a link gained or lost counts, review M1). Module
  docstring cites D-179. — GREEN
- **Wave plan P3, #112 and #124** → as REQ-CAN-001 (names) and REQ-SRC-010 (credits) above.

## Red→green on reported symptoms

Method: the range-end test files were copied onto an export of `dd68917` (`git archive`, in the
scratchpad) and run against that code. Each line below failed there with an assertion, and passes at
`a182a53`.

- **#101** (plans tie by name) → `tests/unit/test_subscribe.py:698` failed `'Alpha Twin' == 'Zed
  Twin'` (the value pick went to the first name). `:712` failed the same way on the cheapest pick.
  `test_pareto_dominance.py:205` failed only on its import (`first_cheapest_plan` is new), so its
  `_pareto` half is proven by fault F6 instead. — GREEN after
- **#106** (a `latest-v` id goes unsaid) → `tests/unit/test_build.py:569` failed `assert notes`
  (`[]`). — GREEN after
- **#130** (`o3-mini-high` served as a model) → `tests/unit/test_registry_derived.py:272` (added
  here) failed with `('o3-mini-high', 'o3-mini-high', 'unspecified')`: the symptom as the issue states
  it. `:251` failed `DerivedIdentity(model_id='o3-mini-high', effort=None)`. — GREEN after
- **#162** (GPT-5.x minis, nanos and chats as one) → `tests/unit/test_registry.py:593` failed 10 of
  16 cases (`gpt-5.4-mini` → `gpt-5-mini`, `azure/gpt-5.1-chat` → `gpt-5-chat`, ...). `:35` failed.
  `:661` (added here) failed 30 cases. — GREEN after
- **#129** (one release, two ids) → `tests/unit/test_registry.py:632` failed 53 of 59 cases
  (`('Claude 3 Haiku', None)`, `'Agentless Lite + O3 Mini (20250214)'` → `o3`, ...).
  `tests/unit/test_access.py:60` failed `() == ('gpt-5',)`. — GREEN after
- **#100** (a re-spelling reads as names lost) → `tests/unit/test_refresh_board_ids.py:73` failed with
  "coding's board would lose 12 of 12 names". `:78` failed with the night refused. `:130[moved to
  other models]`, `:149` and `:162` failed. — GREEN after
- **#124** (credits lag the terms) → `tests/unit/test_attribution_terms.py:45` failed (5 cases:
  "'ARC Prize' in 'Epoch AI, ...'"), `:54`, `:63` (3 cases) and `:71` failed. — GREEN after
- **#112** (68 lower-case names) → `tests/unit/test_display_names.py:100` failed with the missing set
  (`c4ai-aya-expanse32b`, `codellama34b-instruct`, ...). `:124` failed. — GREEN after
- **The review's findings fixed in the range.** M2: `test_subscribe.py:698`, `:712` above. M3:
  `test_build.py:569`'s `_drifted(notes) == "registry"`. M4: `test_registry.py:649` failed on the
  pre-wave code (`gpt-5-codex-mini` → `gpt-5-mini`). M7: the backticked credit is in
  `board_tables.py:52` at `ba64b20`, the red commit. R2 was a defect this wave created and fixed, so
  the pre-wave code passes `test_registry_derived.py:263`; fault F13 shows the test catches its return.

## Suite result

- `make check-fast` (guard-bin stubs on `PATH`), at `a182a53`: **PASS** in 59.6 s. Lint, typecheck,
  records, test (**1924 passed, 25 skipped**), client-decls, swift-test. Evidence:
  `=============== 1924 passed, 25 skipped, 362 warnings in 32.44s ================`.
- `make check-fast` with this review's three tests added: **PASS** in 50.8 s, test leg **1956 passed,
  25 skipped** (32 new cases). Lint passes on the edited files.
- The 25 skips are the network contract tests (`RUN_CONTRACT_TESTS=1`) and the `EPOCH_DATA_DIR`
  local contracts. No `artifact` test is skipped: this seat's `advisor.db` is present.
- Coverage on touched modules, pre-wave export → `a182a53`: `refresh.py` 95% → 96%, `registry.py` 99%
  → 99%, `subscribe.py` 96% → 96%, `build.py` 95% → 95%, `rank.py` 97% → 97%, `board_tables.py` 100%
  → 100%, `floors.py` 100% → 100%, `clients/arena.py` 92% → 92%, `clients/openrouter.py` 96% → 96%.
  No drop. Of the 355 lines the range changed in `src/`, `coverage.json` lists none as missed, and no
  branch on them as missed.
- **First night, simulated independently** (the served artifact as live; the same rows re-built by
  `a182a53`'s code: ingest efforts, `reconcile`, medians, access links): `degradations` and
  `upward_anomalies` are both empty, 97 display names change, 0 board rows are re-spelled. The board
  nearest a limit is `epoch_frontiermath`, 18 of 114 rows (16%) lost and new. This matches D-179's
  re-measured number (`docs/decisions.md`, D-179 "Measured").

## Mocks / contract tests

- **OpenRouter** (`src/app/clients/openrouter.py`, a docstring change only): canonical fake
  `app.clients.fakes.FakeRawSource`; contract test `tests/integration/test_arena_openrouter_contract.py`,
  skipped offline. OK. This review's `:272` test drives OpenRouter and Arena through that same fake.
- **Arena** (`src/app/clients/arena.py`, its `ATTRIBUTION` is now read from `board_tables`): the same
  fake and contract test. OK.
- No new integration and no parallel mock in the range.

## Test integrity

- **Deleted or weakened tests:** one test was deleted,
  `test_pareto_dominance.py::test_the_subscription_frontier_orders_the_same_way`. It pinned the rule
  #101 reverses (a tie by name). Its replacement at `:205` pins the reverse, with names and ids sorting
  opposite ways. Every changed assertion follows a ruled change: `test_access.py:74` (#129's GPT-5
  join), `test_registry.py:37-40` and LIVE_NAME_EXPECTATIONS (#162, #129), `test_display_names.py`
  (`o3-mini-high` moved to `NO_LONGER_MODELS`, #130), `test_recommend.py` (SWE-bench and Aider split,
  #124). The artifact test was made stricter: it now names models through `reconcile` itself. No
  `skip` or `xfail` was added.
- **Mirror tests:** none found. The attribution tests check facts the publishers state (the `EXTERNAL`
  and `CREATIVE_COMMONS` tables), not the strings' construction. The board-guard tests drive
  `fingerprint_of` and `refresh()` on built artifacts.

## Fault injection

Each fault was planted by exact string replacement, the whole Python suite was run
(`pytest tests -n auto --no-cov`), and the fault was reverted in place by string replacement at the
offset it was planted. The sha256 matched before and after, and `git diff --stat` on the file was
empty, every time. The helper and its JSON log are in this seat's scratchpad (`m19w1_fi.py`,
`m19w1_fi.log`). Pre-injection sha256 prefixes: `subscribe.py` `551418a4f2d7782e`, `refresh.py`
`0b0ae36eeb3f7c8c`, `registry.py` `faf9f0594a5db064`, `build.py` `2980fdddb5b57d12`, `rank.py`
`9496a12b56455b95`, `floors.py` `1e5cc383c2709909`. All matched after the last revert.

| Fault | Planted | Result |
|---|---|---|
| F1 | `subscribe.py:446` value pick by `(monthly_usd, plan)` | killed: `test_subscribe.py:698` |
| F2 | `subscribe.py:451` cheapest pick by `(monthly_usd, plan)` | killed: `test_subscribe.py:712` |
| F3 | `subscribe.py:484` group order `(monthly_usd, plan, plan_id)` | killed: `test_subscribe.py:698` |
| F4 | `subscribe.py:506` group "cheapest" by `(monthly_usd, plan)` | killed: `test_subscribe.py:698` |
| F5 | `subscribe.py:300` `first_cheapest_plan` ignores the score | killed: `test_subscribe.py:712`, `test_pareto_dominance.py:205` |
| F6 | `subscribe.py:293` `_pareto` tie by `plan` | killed: `test_pareto_dominance.py:205` |
| F7 | `refresh.py:241` unlinked rows folded into one model (counted, not named) | killed: `test_refresh_board_ids.py:149` and 2 more |
| F8 | `refresh.py:372` `board_respellings` records nothing | killed: `test_refresh_board_ids.py:78` |
| F9 | `refresh.py:634` declared boards by raw name again | killed: 5 in `test_refresh_board_ids.py` |
| F10 | `refresh.py:1290` the night's `renamed` omits board re-spellings | killed: `test_refresh_board_ids.py:78` |
| F11 | `registry.py:134` the curated `o3-mini` rule refuses `-high` | **survived** (1924 passed) → M1 |
| F12 | `registry.py:722` the display keeps a dash effort | **survived** (1924 passed) → M2 |
| F13 | `registry.py:429` Sonar's `-high` read as an effort | killed: `test_registry_derived.py:263` (2) |
| F14 | `registry.py:127` GPT-5.2 takes an unnamed 5.2 mini, nano, chat | **survived** (1924 passed) → M3 |
| F15 | `registry.py:118` GPT-5 Codex takes a Codex mini | killed: `test_registry.py:649` (3) |
| F16 | `build.py:793` the #106 drift line loses its `registry:` source | killed: `test_build.py:569` |
| F17 | `rank.py:90` ARC-AGI credited to Epoch alone | killed: `test_attribution_terms.py:45` |
| F18 | `rank.py:53` external credits left out of `ATTRIBUTIONS` | killed: `test_attribution_terms.py:45` (5) |
| F19 | `registry.py:717` the display table bypassed | killed: `test_display_names.py:106`, `:124` |
| F20 | `floors.py:52` a surface's own board by raw name again | killed: 3 in `test_refresh_board_ids.py` |
| F21 | `registry.py:131` GPT-5's dated snapshot a model of its own again | killed: `test_registry.py:632` (2), `test_access.py:60`, `test_display_names.py:124` |

After this review's tests: F11 is killed by `test_registry_derived.py:272`, F12 by `:305`, and F14 by
`test_registry.py:661` (4 cases). Each rerun was reverted the same way and verified identical.

**Mutation kill rate (advisory, hand-run; no mutation runner is wired for this stack):** 18 of 21
(85.7%) on the range-end suite; 21 of 21 with this review's tests.

## BLOCKING

- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/registry.py:134`; `tests/unit/test_registry_derived.py:251`. **#130's
  expected result was unpinned on the path production takes.** Since #129 added the curated `o3-mini`
  rule (`d79d70d`), `o3-mini-high` no longer reaches `derive_identity`: the rule takes it and ingest's
  `resolve_effort` reads `high`. `:251` pins only the derived grammar. With the rule refusing `-high`
  (F11), the derived path proposes `o3-mini`, a curated id it may not take, so Arena's 26 `o3-mini-high`
  rows would be dropped, and all 1924 tests passed. Closed by `tests/unit/test_registry_derived.py:272`,
  added here (red on the pre-wave code with the issue's own symptom, red on F11). The author commits it.
- **M2** `src/app/workflows/registry.py:722-723`. **The display's dash-effort strip, added with #130,
  had no test.** Removing it (F12) let a model known only as `zeta-9-xhigh` be served under that
  name, effort and all, and the suite stayed green. Closed by `tests/unit/test_registry_derived.py:305`,
  added here. The author commits it.
- **M3** `src/app/workflows/registry.py:124-128`. **#162's guard on the GPT-5.x parent rules was pinned
  for two of five parents.** `test_registry.py:35` pins `gpt-5.1-nano` and `gpt-5.5-thinking-mini`
  only. With GPT-5.2's lookahead back to `(?:codex|pro)` (F14), `gpt-5.2-mini` and `gpt-5.2-nano`
  became GPT-5.2, the REQ-CAN-002 spike bug, and the suite stayed green. Closed by
  `tests/unit/test_registry.py:661`, added here (30 cases red on the pre-wave code, 4 red on F14). The
  author commits it.
- **M4** `src/app/workflows/registry.py:116`. **A GPT-5.2 Codex mini folds into GPT-5.2 Codex.** The
  review's M4 fix excluded `mini` from GPT-5 Codex's rule only. `gpt-5.2-codex`'s rule is still
  `gpt[-_ ]?5[.\-]?2[-_ ]?codex(?![-_ ]?max)`, so `canonicalize("gpt-5.2-codex-mini")`,
  `openai/gpt-5.2-codex-mini` and `GPT-5.2 Codex Mini` all return `gpt-5.2-codex`. GPT-5.1's is covered
  only because its own Codex mini rule comes first. No row in today's artifact carries the name, so
  nothing served moves yet. The rule predates the wave, but it is the wave's criterion (one release,
  one model; REQ-CAN-002). Fix: `(?![-_ ]?(?:max|mini))` on both 5.x Codex rules, with a `codex-mini`
  case added to `test_registry.py:661`'s variants; or file it.
- **M5** `src/app/workflows/refresh.py:1100-1129` (`_served_without`), `:235-246`
  (`board_identities`); `docs/decisions.md` D-179 "What an upstream's names can move now". **On an
  expiry night, D-179 counts the rows the expiry unlinked as rows lost.** D-156 clause 3 judges an
  expiry night against the live artifact without the expired source's rows, so that it "excuses
  exactly the loss those rows account for, on every guard". `_served_without` deletes the rows but
  keeps every `scores.model_id`. A build without a price feed re-reconciles, and D-157 links a derived
  model only while it has a price, so that model's board rows come back unlinked. D-179 now compares a
  linked row as its model and an unlinked one as its name. The baseline's rows are linked and the
  candidate's are not, so they read as lost and new. Measured on this seat's copy of the served
  artifact (re-reconciled with `a182a53`'s code, then `litellm` expired; script
  `m19w1_expiry_sim.py` in the seat's scratchpad): `board epoch_mmlu would lose 36 of 136 rows (26%,
  at or over the 25% limit)`, and the mirror `would be 36 of 136 rows this artifact has never seen`.
  The pre-wave code gives no board reason on the same night. It fails closed. Today the same night is
  already refused by the accessibility guard, for the same root cause (K1), so no served outcome
  changes yet. D-179 does not name the expiry night. The reviewer listed it as a gap ("the
  expiry-night baseline: no D-179-specific test"). Fix: re-reconcile the baseline in `_served_without`
  (with medians and access links), with a test of a price-feed expiry that keeps every board; or say
  in D-179 that an expiry night with derived links can refuse, and file the fix.
- **M6** `tests/unit/test_display_names.py:1`, `tests/unit/test_registry_derived.py:254-256`. **The
  maker's-spelling and effort halves of REQ-CAN-001 are proven by tests that do not cite it.** M19
  states REQ-CAN-001 as names, one release, and efforts (`m19-plan.md:38`), and the PRD lists these
  tests as its evidence (`docs/prd.md:91`). But `test_display_names.py` cites #112 only, and the
  dash-effort test cites REQ-CAN-005 only (seed E.2). This review's `:272` and `:305` cite REQ-CAN-001.
  Fix: add `REQ-CAN-001` to the display-name module's docstring and to the docstring at `:254`.

## K.9 candidates outside this wave

- **K1** `src/app/workflows/refresh.py:1100-1129`; D-173 clause 3 (#42), D-156 clause 3. **An expiry
  night of a price feed is refused by the accessibility guard.** The same root cause as M5, older than
  this wave: `_served_without` keeps `access` links and `model_id`s, and a build without the feed
  loses the derived models' links. On the served artifact, a `litellm` expiry is refused with
  "accessibility values would fall from 225 to 135 models (40%)" on the pre-wave code (228 to 152,
  33%, at `a182a53`). The expiry the refresh is meant to publish is refused every night until the
  owner publishes by hand. For `/file-issue`, together with M5 if M5 is not fixed in the wave.

## Risks queued to next M

- **R1** first night after merge. **This seat's simulation agrees with the reviewer's and D-179's**:
  it publishes, with `epoch_frontiermath` the nearest board at 16%. What would show a difference: a
  real nightly record that refuses, or one whose `renamed` lists board re-spellings (the simulation
  found 0). The phone-side orphaning of retired ids is the reviewer's R3.

## Tests added/extended this review

All three are uncommitted in this worktree. Each passes at `a182a53`, fails on the pre-wave code, and
fails on its fault.

- `tests/unit/test_registry_derived.py:272`
  `test_o3_mini_high_is_stored_as_o3_mini_at_high_effort_on_the_path_a_build_takes`: REQ-CAN-001,
  REQ-CAN-005, #130 (M1, F11).
- `tests/unit/test_registry_derived.py:305` `test_a_derived_models_name_carries_no_dash_effort`:
  REQ-CAN-001, #130, #112 (M2, F12).
- `tests/unit/test_registry.py:661` `test_no_gpt5_minor_release_rule_takes_another_releases_variant`
  (30 cases): REQ-CAN-002, #162 (M3, F14).
