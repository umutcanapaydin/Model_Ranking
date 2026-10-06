---
record_type: review
id: m19-wave-1-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-06
---
# M19-W1 Code Review: what the reader sees

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-06
**Commit range:** `dd68917..a460f5e` (27 commits; 24 files, +935 / -120).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:46-48`, `docs/plans/m19-wave-1-plan.md:13-15`). The diff
touches `src/app/clients/**`, a security glob (`m19-plan.md:130`). By D-172 no security seat runs on
the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile and
`.agents/rules/practices.md` from `origin/main`, then the milestone plan (§1, §2 W1, §5, the
2026-10-06 amendment), the wave plan and D-179 with its amendment notes. Then I read the diff. I read
the commit messages last.

**Summary.** The wave delivers all eight issues it planned. Each one has a red test and a fix, and
the gates are green in this seat. I simulated the first night on a copy of the served artifact: it
publishes, and no two models share a display name. I planted seven mutants. Five were caught. The
two that survived are both in #101 (M2). Nothing blocks. Seven MINORs:

1. **M1.** The board guards count a row as lost when its link changes, even if its name does not.
2. **M2.** #101 is half pinned, and one name tie-break is left.
3. **M3.** The #106 note breaks the drift line format that `/health` parses.
4. **M4.** GPT-5 Codex mini still folds into GPT-5 mini.
5. **M5.** D-179's measured number does not reproduce.
6. **M6.** REQ-SRC-010 is a scoped criterion that no test cites.
7. **M7.** A reader-facing credit shows a file name in backticks.

## Verdict

MINOR

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/refresh.py:235-246` (`board_identities`), `:274-287` (`_mostly_lost`);
  `docs/decisions.md` D-179 "What an upstream's names can move now". **A row whose link changes
  counts as a row lost and a row new, even when its name is the same.** An unlinked row is compared
  by its name (a `str`). A linked row is compared as a `LinkedRow`. So a row that gains a link
  leaves the `str` set and joins the `LinkedRow` set: the board both "loses" it and "gains" it. The
  same happens in reverse when a link is lost. Before this wave, neither case moved a board guard.
  On the served artifact, many rows have a link that can move. On `assistant`'s own board, 42% of
  rows are unlinked and 29% link to *derived* models. Across Arena's 26 text slices, 21% to 42% are
  unlinked. D-157 links a derived model only while it has both a price and a score. So a pricing feed that adds or prunes models now moves board
  guards. D-179 does not list this case: it covers re-spellings and registry changes only.
  Evidence: a probe using the wave's own fixture (`test_refresh_board_ids._reasons`, in a temp
  dir). 12 unlinked rows gain a link and keep their names. The guard reports:
  ```
  board arena_agent would lose 12 of 12 rows (100%, at or over the 25% limit); ...
  board arena_agent would be 12 of 12 rows this artifact has never seen (100%, over the 25% limit); ...
  ```
  The board would serve 12 more rows, and the reason says it loses them. It fails closed (the night
  is refused), so this is MINOR, not BLOCKING. One fix: count a raw name that is present in both
  summaries as kept for D-128, whichever side links it. The other is to say in D-179 that a link
  change moves the guards.
- **M2** `src/app/workflows/subscribe.py:505-506`, `:445`, `:450`, `:483`;
  `tests/unit/test_pareto_dominance.py:205-220`. **#101 is half pinned, and one tie-break by name is
  left.**
  (a) `cheapest = min(members, key=lambda r: (r.monthly_usd, r.plan))` still breaks a price tie by the
  plan's name. The reader sees its result in "The cheapest in this group is {cheapest.plan}", which
  is #101's defect.
  (b) No behavioural test covers the value and cheapest call sites (`:445`, `:450`) or the
  equivalence sort (`:483`). Mutant 1 put both call sites back to `(r.monthly_usd, r.plan)`; mutant 2
  put `:483` back to `(r.monthly_usd, r.plan, r.plan_id)`. **Both survived the whole unit suite,
  1906 passed each time.** The red for `test_a_plan_pick_breaks_a_price_tie_by_plan_id` was an
  ImportError, because the helper did not exist yet (`be00142`). That is the W-113 class: "verified
  red" was an `AttributeError`.
  (c) The plan asks that "one test states the rule for both engines" (`m19-wave-1-plan.md:35`). The
  rule is stated in two tests that sit side by side.
- **M3** `src/app/workflows/build.py:792-793`; `src/app/adapter/nightly.py:184-188`, `:403-404`.
  **The #106 note does not follow the drift line format.** Drift lines are `<source>: <reason>`.
  `/health`'s `refresh_drift` is "a board whose layout changed in a bundle that arrived, by source
  name", and it takes the text before the first colon as a source. The new line, `derived <id>: a
  \`latest-v\` name ...`, therefore surfaces as a source called `derived <id>`. Checked:
  `_drifted(['epoch_eci: ...', 'derived gpt6-astra-latest-v2: ...'])` returns `'derived
  gpt6-astra-latest-v2, epoch_eci'`. The docstring of `test_build.py:569` says `/health` carries it.
  It does, but under a label that says something else.
- **M4** `src/app/workflows/registry.py:112`. **GPT-5 Codex mini still folds into GPT-5 mini.** The
  `gpt-5-mini` rule keeps `(?:codex[-_ ]?|thinking[-_ ]?)?mini`, so `canonicalize("gpt-5-codex-mini")`
  and `canonicalize("openai/gpt-5-codex-mini")` both return `gpt-5-mini`. #162 made GPT-5.1 Codex mini
  a model of its own because a Codex mini has its own prices and scores (`registry.py:102-104`). The
  same holds for OpenAI's GPT-5-Codex-Mini. Before this wave, that branch existed to catch any minor's
  codex mini. Now it catches only this one product. No row in today's artifact carries the name, so
  nothing served moves yet.
- **M5** `docs/decisions.md:3887-3889` (D-179 "Measured"). **The recorded number does not reproduce.**
  D-179 says `epoch_frontiermath` has "13% of its rows moved to other models". I re-measured with the
  range-end code on this worktree's copy of the served artifact. I re-inferred ingest efforts,
  re-reconciled, rebuilt `px_median`, then ran `fingerprint_of` with `degradations` and
  `upward_anomalies`. The result is **18 of 114 rows (16%)**, lost and new. The three extra rows are
  GPT-5's dated rows (`gpt5-2025-08-07` to `gpt-5`, `c673dda`), which were probably added after the
  measurement. The conclusion still holds: it publishes, nothing refuses, and the nearest board is
  still `epoch_frontiermath`. But a record's measured number should match the code that ships.
- **M6** `docs/plans/m19-plan.md:38`; `docs/prd.md:546`; `tests/unit/test_attribution_terms.py:1-14`.
  **REQ-SRC-010 is a scoped W1 criterion, and no test cites it.** The plan maps W1's attribution
  criterion to REQ-SRC-010. The new test file cites only #124 and #88. The PRD's REQ-SRC-010 row is
  unchanged, and the new evidence went onto REQ-LIC-001 instead (`docs/prd.md:370`). The
  `test_refresh_board_ids.py` docstrings likewise cite D-159, D-164 and D-173 but not D-179, the
  decision they prove (seed E.2).
- **M7** `src/app/workflows/board_tables.py:50-52`; `ios/ModelRanking/ContentView.swift:1452`. **A
  credit the reader sees contains a file name in backticks.** `epoch_mmlu`'s attribution ends "... and
  the model technical reports Epoch's \`mmlu_external.csv\` names." The app prints `board.attribution`
  as is, so the backticks and the file name reach the screen. In a wave titled "what the reader
  sees", the credit should name the reports in words.

### PASS (what looks good)

- **Red, then green, per issue.** Every issue has a `test: reproduce ... (red)` commit before its
  `fix:` commit (`be00142` then `35e8e26`, `26912cc` then `e6c57ce`, and so on). The commit messages
  carry no AI attribution and no destructive operation.
- **The guard change holds against its mutants.** Mutant 3 (rows compared by raw name again) turns 4
  tests in `test_refresh_board_ids.py` red. Mutant 4 (compare distinct models, so `copy` is dropped)
  turns `[more rows for the same models]` red. That is exactly the case D-179 clause 2 and its
  mitigation name.
- **Registry changes move only what they claim.** I compared old and new `reconcile` over every
  pricing alias, score name and plan row in the artifact. 163 pricing rows and 642 score rows change
  model, and each one belongs to #129, #130, #162 or the Mistral Medium alias. One is a fix nobody
  listed: `Agentless Lite + O3 Mini (20250214)` reached `o3`, and now reaches `o3-mini`. **Plan rows:
  0 changed.** Display names: the 75 table entries plus the joins, and no two models share a display
  name.
- **The first night publishes.** `degradations` and `upward_anomalies` are both empty. Re-spellings:
  0. Display changes: 97.
- **The effort and grammar mutants are caught.** Mutant 5 (no dash effort in `derive_identity`) is
  caught by `test_registry_derived.py:250`. Mutant 6 (no #106 note) is caught by `test_build.py:569`.
  Mutant 7 (the any-minor GPT-5 variant rules restored) is caught by `test_registry.py:35`.
- **The artifact test is now faithful.** `test_display_names.py:124` names models through the code's
  own `reconcile`, instead of approximating it. It found 17 more lower-case names, and the wave fixed
  them (`97231c9`, `a460f5e`).
- **The decisions are recorded properly.** D-179 has a rejected alternative and a mitigation. The
  amendment notes on D-159, D-164 and D-173 are appended, and the old bodies are not edited
  (`git diff` of `docs/decisions.md` adds lines only).
- **Out-of-bounds files untouched.** No `/v1` field changes, and nothing changes in `ios/`,
  `src/app/adapter/`, `tests/conftest.py`, `.github/`, `.claude/settings.json`, `epb.html` or `or.md`.
- **Attribution strings agree with the licence research.** They match
  `docs/research/data-licences-2026-10-04.md` (SWE-bench's CC BY-NC is note 7), and the commercial
  question stays with #88, where it belongs.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code:

- **D-179 (a board row is compared by the model it links to).**
  - `serving_summary`, each surface's own board, through `floors.board_rows`
    (`refresh.py:618`, `floors.py:48`): `test_refresh_board_ids.py:72`, `:129` (`coding's board`).
  - `serving_summary`, each declared board, inline query (`refresh.py:625-634`):
    `test_refresh_board_ids.py:72`, `:129`, `:137`, `:148`.
  - `refresh()`'s record of re-spellings (`refresh.py:1290`): `test_refresh_board_ids.py:77`.
  - `_served_without`, the baseline on an expiry night (`refresh.py:1100-1129`): no D-179-specific
    test. It calls the same `serving_summary`, and the existing expiry tests pass.
- **One release is one model, and a variant never leaks (REQ-CAN-001/-002).**
  - `canonicalize`, used by `reconcile` for pricing and score names: `test_registry.py:35`, `:593`,
    `:632`, `:640`.
  - `reconcile` over the real rows: `test_display_names.py:124` (names only).
  - `access.link`: `test_access.py:60-77` (the GPT-5 join).
  - `reconcile_plans`: no new test. Measured: 0 plan rows change on the artifact.
  - `resolve_effort` at ingest (`ingest.py:119`), which is the path `o3-mini-high` now takes (the
    curated rule wins): no test. `test_registry_derived.py:242` pins the derived path for that name,
    and production no longer reaches it.

Gaps: M1 (a link change reads as a loss); the expiry-night baseline; `reconcile_plans`; the
curated-path effort for `o3-mini-high`. M2 is the #101 tie-break gap.

## Acceptance criteria evidence (REQUIRED for PASS verdict)

- **REQ-CAN-001** (one release is one model; an effort is never a model; names in the maker's
  spelling):
  - `tests/unit/test_registry.py:604-645` (#129). The docstring at `:596` cites REQ-CAN-001.
  - `tests/unit/test_registry_derived.py:241-258` (#130; cites REQ-CAN-005).
  - `tests/unit/test_display_names.py:100`, `:124` (#112).
  - `tests/unit/test_moving_aliases.py:32` (the Mistral Medium 3 alias).
  - Code: `src/app/workflows/registry.py:89-139`, `:189-194`, `:419`, `:510`, `:588-681`.
- **REQ-CAN-002** (a variant never leaks into its parent): `tests/unit/test_registry.py:35-67` (cites
  REQ-CAN-002 at `:36`) and `:573-597` (#162). Code: `src/app/workflows/registry.py:96-124`.
- **REQ-SRC-010** (each attribution matches its publisher's terms, or waits on #88 by name): the
  substance is in `tests/unit/test_attribution_terms.py:45`, `:54`, `:63`, `:71` and
  `tests/unit/test_recommend.py:136`, `:172`. Code: `src/app/workflows/board_tables.py:22-64`,
  `src/app/workflows/rank.py:39-93`, `src/app/clients/openrouter.py:3-5`. The REQ-ID is cited nowhere
  (M6).
- **#100 / D-179, on REQ-REF-003:** `tests/unit/test_refresh_board_ids.py:72`, `:77`, `:129`, `:137`,
  `:148`. Code: `src/app/workflows/refresh.py:205-246`, `:361-377`.
- **#101:** `tests/unit/test_pareto_dominance.py:205`, `:214`. Code:
  `src/app/workflows/subscribe.py:286-299`, `:445`, `:450`, `:483` (partly unpinned; `:505` left, M2).
- **#106:** `tests/unit/test_build.py:569`. Code: `src/app/workflows/build.py:790-793` (M3).

## Every file in the diff

| File | What changed | Read |
|---|---|---|
| `README.md` | Epoch's licence link; the five external Epoch boards keep their own licences | ok |
| `docs/decisions.md` | D-179; amendment notes on D-159, D-164, D-173 | M5 |
| `docs/plans/m19-plan.md` | the #162 amendment | ok |
| `docs/plans/m19-wave-1-plan.md` | the wave plan (new) | ok |
| `docs/prd.md` | evidence on REQ-CAN-001, -002, LIC-001, REF-003 | M6 |
| `src/app/clients/arena.py` | `ATTRIBUTION` is read from `board_tables` (one string, W-125) | ok |
| `src/app/clients/openrouter.py` | the docstring says what OpenRouter's terms say | ok |
| `src/app/workflows/board_tables.py` | CC licence URIs, `EPOCH_CITATION`, external credits, `ARENA_ATTRIBUTION` | M7 |
| `src/app/workflows/build.py` | the #106 drift note | M3 |
| `src/app/workflows/floors.py` | `board_names` becomes `board_rows` (raw name, model id) | ok |
| `src/app/workflows/rank.py` | SWE-bench and Aider split; external Epoch boards credited | ok |
| `src/app/workflows/refresh.py` | `LinkedRow`, `board_identities`, `board_respellings`, the guards typed | M1 |
| `src/app/workflows/registry.py` | #129, #162 and #130 rules; `_DASH_EFFORT`; a moving alias; 75 names | M4 |
| `src/app/workflows/subscribe.py` | plan ties broken by `plan_id`; `first_cheapest_plan` | M2 |
| `tests/unit/test_access.py` | follows the GPT-5 join | ok |
| `tests/unit/test_attribution_terms.py` | new: the #124 strings | M6 |
| `tests/unit/test_build.py` | #106 | ok |
| `tests/unit/test_display_names.py` | #112's remainder; the artifact test through `reconcile` | ok |
| `tests/unit/test_moving_aliases.py` | `mistral-medium3` | ok |
| `tests/unit/test_pareto_dominance.py` | #101 | M2 |
| `tests/unit/test_recommend.py` | follows the SWE-bench / Aider split | ok |
| `tests/unit/test_refresh_board_ids.py` | new: #100 / D-179 | ok |
| `tests/unit/test_registry.py` | #129, #162 | ok |
| `tests/unit/test_registry_derived.py` | #130 | ok |

## K.8 contract drift check

The milestone plan's contracts (`m19-plan.md:142-154`) and the wave plan's (`m19-wave-1-plan.md:46-51`),
`grep -n` at `a460f5e`:

```
src/app/workflows/registry.py:310:_EFFORT_SUFFIX = re.compile(r"(?P<separator>[-_])(?P<effort>max|xhigh|high|medium|low)\Z", re.I)
src/app/workflows/registry.py:501:_LATEST_TOKEN = re.compile(re.escape(_LATEST_SUFFIX) + r"(?:-(?!v\d)|\Z)")
src/app/workflows/registry.py:557:DISPLAY_NAMES: dict[str, str] = {
src/app/workflows/registry.py:689:def claude_word_order(name: str) -> str:
src/app/workflows/subscribe.py:286:def _pareto(rows: list[PlanRank]) -> list[PlanRank]:
src/app/workflows/subscribe.py:293:        key=lambda r: (-r.score, r.monthly_usd, r.plan_id),
src/app/workflows/rank.py:47:ATTRIBUTIONS = (
src/app/workflows/rank.py:59:SOURCE_ATTRIBUTION: dict[str, str] = {
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
tests/conftest.py:218:def pytest_configure(config: pytest.Config) -> None:
ios/ModelRanking/Engine/AnswerPlan.swift:173:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/Engine/FrontDoor.swift:278:public struct GapRegisterStore {
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:526:enum ModelOutputBoundary {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
```

- Every declared symbol exists, with the same name and shape. `_pareto`'s key moves from `r.plan` to
  `r.plan_id`: that is #101's planned change, not drift.
- `tests/conftest.py`'s line moved since the `0198eb3` pin, but the file is untouched in this range.
- `ARENA_ATTRIBUTION` moves to `board_tables` and is re-exported by `rank`, so
  `from app.workflows.rank import ARENA_ATTRIBUTION` still works. `floors.board_names` is removed.
  `git grep` finds no other caller.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/registry.py:516`, `:292-295`. **Fine-tune prices reach curated models.**
  The `ft:` refusal is only on the derive path. Curated rules match by `search`, so
  `ft:gpt-4o-2024-08-06` and `-11-20`, `ft:gpt-4.1-2025-04-14` and `ft:o4-mini-2025-04-16` feed their
  base models' price medians at about 2x. This wave's new rules add `ft:gpt-4.1-mini-2025-04-14` and
  `ft:gpt-4.1-nano-2025-04-14` to that list. The two-stage median absorbs them today: 10 or more
  aliases sit at the base price. A bug: a fine-tune is its owner's model (D-157). The fix is to
  refuse `ft:` in `canonicalize_with_reason`, as the derive path does.

## Risks queued to next M

- **R1** `src/app/workflows/refresh.py:235-246`. **How often links change on real nights.** M1 bites
  only if a quarter of a board's rows change link state in one night. What would show it: a refresh
  record that refuses with "would lose N of M rows" on a night with no re-spelling, or two
  consecutive artifacts where many Arena rows move between unlinked and linked.
- **R2** `src/app/workflows/registry.py:416-419`. **Not every `-high` is a reasoning effort.** Arena's
  `ppl-sonar-pro-high` and `ppl-sonar-reasoning-pro-high` now derive `ppl-sonar-pro` (and its
  reasoning twin) at effort `high`. There, `high` is Perplexity's search-context size. Both are
  unlinked today, so nothing is served. The comment "no product ends in `-high`" is broader than the
  data. What would show it: a price alias that derives `ppl-sonar-pro`.
- **R3** first night after merge. **26 model ids join or split, and 97 display names move.** Anything
  the phone keeps that is keyed on an old id (`o3-mini-high`, `gpt5-2025-08-07`, `claude3-opus20240229`,
  ...) is orphaned until its next fetch, and W2's #138 keys cards on the model id. What would show it:
  the owner's first-night read (`m19-wave-1-plan.md:54-55`) finding a held card or standing under a
  retired id.

## Gates and probes run

- `make check-fast` (with the guard-bin stubs on `PATH`): **PASS** in 59.6 s. Lint, typecheck,
  records, test (1915 passed, 25 skipped; no artifact test skipped), client-decls and swift-test.
- `pytest -m artifact` on the wave's test files: 1 passed (`test_display_names.py:124`, against this
  seat's `advisor.db`).
- Old vs new `reconcile` over a copy of `advisor.db`, and a first-night simulation (live = the served
  artifact, candidate = efforts re-inferred and re-reconciled): scratchpad scripts, nothing written to
  the worktree.
- **Mutants**, each planted in place and restored. After each one, `shasum` matched the pre-plant
  value and `git diff --stat` was empty. `git status` is clean apart from this file.
  1. `subscribe.py:445`, `:450` back to `(r.monthly_usd, r.plan)`: **survived**, 1906 passed (M2).
  2. `subscribe.py:483` back to `(r.monthly_usd, r.plan, r.plan_id)`: **survived**, 1906 passed (M2).
  3. `refresh.py:245`, linked rows by raw name: caught by 4 tests in `test_refresh_board_ids.py`.
  4. `refresh.py:245`, one copy per model: caught by `[more rows for the same models]`.
  5. `registry.py:510` without `_DASH_EFFORT`: caught by `test_registry_derived.py:250` (2 cases).
  6. `build.py:793`, note disabled: caught by `test_build.py:569`.
  7. `registry.py:111-113`, any-minor GPT-5 variant rules restored: caught by
     `test_registry.py:35`.
- Checksums before and after: `subscribe.py` `adf005fd`, `refresh.py` `58c083ce`, `registry.py`
  `550a283e`, `build.py` `a74c9ea7`.
