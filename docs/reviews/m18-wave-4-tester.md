---
record_type: review
id: m18-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# Wave 4 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records.
It is not one of the wave's two Code-Reviewer seats.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `d528fd3..4d07e50`: 15 commits, 33 files. `d528fd3` is the head of `wave/m18-w1`
(PR #99, unmerged), which this wave is stacked on. The range holds the plan and D-173 (`faf3242`),
four red-then-fix pairs, round 1 of the code review (`5807fbe`, BLOCKING), its red-then-fix pair
(`81a3942` → `77d3b2f`), round 2 (`ddf8443`, PASS-WITH-MINORS) and its fix (`4d07e50`). `4d07e50`
came after both reviews, so this seat is the only one that has tested it.
**Risk tier:** HIGH (`docs/plans/m18-wave-4-plan.md:11`). It touches `src/app/adapter/main.py` and
`src/app/clients/**`, which are security globs.
**Code-Reviewer verdict:** PASS-WITH-MINORS (`docs/reviews/m18-wave-4-review.md`, round 2, `ddf8443`).
By D-172 there is no security seat on the wave. The fault injection below is the HIGH tier's owed one.
**Model routing (HIGH, advisory):**
- Author family: Claude (the commits carry `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from `.claude/agents/Tester.md`, `.agents/rules/practices.md` and
  `permission-matrix.md` §11, all read from `d528fd3` with `git show`. (`docs/permission-matrix.md`
  does not exist at the base; the matrix is `permission-matrix.md` at the root.) It then read the
  plans, D-173, the eleven issues, both review rounds and the diff. It has no memory of any authoring
  or reviewing session.
**Base-pinned policy:** `git diff --stat d528fd3..4d07e50 -- .claude .agents permission-matrix.md
.github epb.html or.md AGENTS.md` is empty.

## Verdict
PASS-WITH-MINORS

**Nothing blocks.** I found the following:
1. Every acceptance check in the wave plan has a citing test that passes.
2. Each check was also run through its live entry point:
   1. real uvicorn engines on 127.0.0.1;
   2. `refresh()` on copies of the served artifact.
3. Each red commit fails where it should.
4. No touched module lost coverage.
5. Both gates pass.

The behaviour the wave promises is correct everywhere I probed it.

**Nine MINORs (T1 to T9). Each is a fault that stayed green**, and each comes with a test.
1. Each test was written in a scratch copy of `4d07e50` and is green there.
2. Each was shown red on its fault in that copy.
3. The author lands them in this wave, or files them.

The nine:
- **T1:** "ties are ordered by model id" is held only as "a re-spelling moves nothing". A
  tie-break on the table's insertion order, or on the id descending, passes the whole suite.
- **T2:** the value and budget picks' half of #44 is held only on the helper `first_cheapest`.
  1. Its red was an `ImportError`.
  2. Putting the pre-fix lines back at either call site passes the whole suite.
- **T3:** #45's discount is tested with one resolved row per source. A discount of one per source
  passes. The real boards resolve 7 to 9 per source.
- **T4:** the `-latest-video` pin that round 2's M12 asked for cannot fail. `video` is a modality
  word, so the name derives nothing for another reason. The `(?!v)` mutant still survives, as in
  round 2.
- **T5:** a refused night's re-spellings are not held. Dropping them from the refusal passes.
- **T6:** round 2's M8(1) is still open. Its mutant `m-42-baseline` survives: an expiry night's
  accessibility loss is judged against the live artifact and the night is refused. The new test
  calls `degradations` by hand. It never runs the night.
- **T7:** no test sets `MODEL_RANKING_MAX_RANKED_ROWS`. A bound that ignores its variable, in the
  engine and the child alike, passes the B1 test.
- **T8:** the `/v1/boards` memo's eviction is not held. Without it, the engine keeps about 2.3 MB per
  published night for as long as it runs.
- **T9:** the #76 guard scans only the top level of `scripts/` and `deploy/`. The retired installer
  placed in `scripts/simtools/` passes.

**What was run.**
- `make check-fast`: rc 0. `make wave-check-all`: rc 0.
- Every red commit in the range was replayed on `git archive` copies, with a scratch HOME.
- **55 faults were injected in the worktree.** 41 were killed, 3 are equivalent (N1, N2, N3) and 11
  survived. The 11 survivors are the subject of T1 to T9.
- A 56th fault, on a scratch copy, checks the M9 fix. It was killed.
- **Advisory kill rate: 41 of 52 non-equivalent faults, 78.8 %.** With the nine proposed tests
  added, it is 52 of 52.

## Acceptance-criterion coverage (REQUIRED)

Every test named below is GREEN at `4d07e50`. Line numbers are at `4d07e50`. The fault ids are
defined under "Fault injection".

The "entry" column says how the test reaches the behaviour:
- **real path:** the code that serves or refreshes, driven end to end;
- **unit:** the function itself, called directly.

The "live" column is this seat's own run through the entry point a user or the night actually uses.

| criterion (plan phase, D-173 clause) | citing test (file:line) | entry | faults it kills | live check by this seat | status |
|---|---|---|---|---|---|
| P1 #44: two tied models whose display names swap alphabetical order keep their positions (cl. 1) | `test_rank.py:262` (#44, D-173 clause 1) | real path: ingest, reconcile, the serving query | R1 | `/v1/recommendations` base against head: 33 of 42 answers identical. The other 9 (`expert`, `mathematics`, `abstract`) differ only in tie order, with identical picks. At head, all 50 runs of equal raw score on the served artifact are in id order. At base they were in display order, and 16 of the 50 move | GREEN; R2, R3 survive: **T1** |
| P1 #44: a full tie on the frontier keeps the ranking's order (cl. 1) | `test_pareto_dominance.py:181` | unit | F1, F2 | as above | GREEN |
| P1 #44: the value and cheapest picks break a price tie in the ranking's order (cl. 1) | `test_pareto_dominance.py:196` | unit: the helper alone | P1, P4 | no price tie among the served picks | GREEN; P2, P3 survive: **T2** |
| P1 #45: a derived `_high` row stored as `high` is not counted unknown | `test_build.py:498` (REQ-CAN-005); control `:516` | real path: `build()` with the fake upstreams | E1, E2, E3 | not possible offline (the build needs the network) | GREEN; E5 survives: **T3**; E4 equivalent: **N1** |
| P1 #48: `grok-4.20-beta-latest-reasoning` derives nothing; `chatgpt-4o-latest-20250326` still derives (cl. 8) | `test_moving_aliases.py:94` (#48, D-166, REQ-CAN-001), `:103` | unit: `derive_identity` | L1, L3, L4, L5 | The artifact has 107 names containing `latest`. 7 derive at base and 5 at head: the two grok names drop. The dated releases and the `@latest` route decorations are unchanged | GREEN; L2 survives: **T4** |
| P2 #39: a candidate that only re-spells N models moves no guard, and its record lists the changes (cl. 2) | `test_refresh.py:1685` (REQ-CAN-001), `:1700` (through `refresh()` and the record) | real path | G1, G2, G3, G4, G6, G7, R4 | `refresh()` on the served artifact with every display re-spelled. Head publishes and records 301 re-spellings. Base refuses ("abstract would be 71 of 71 models this artifact has never seen") | GREEN; G5 survives: **T5** |
| P2 #42: a candidate with 1 of 219 accessibility values is refused, naming the attribute; a normal night publishes (cl. 3) | `test_refresh.py:1736` (8→1 and 8→6 refused, 8→7 not) | unit: `degradations` on two fingerprinted artifacts | A1, A2, A3, A4 | `refresh()` on the served artifact. 225 → 1 is refused: "accessibility values would fall from 225 to 1 models". A night that moves one score publishes. At base the 225 → 1 night published | GREEN |
| P2 #42 on an expiry night (D-156 clause 3, REQ-REF-009) | `test_refresh.py:1799` (REQ-REF-009) | unit: `_served_without` and `degradations`, by hand | A6, A1, A4 | `refresh()` on the served artifact with `epoch_access` reported expired: publishes at head | GREEN; A5 survives: **T6** |
| P2 #57: a candidate past a serving bound is refused with the bound named; a first artifact too (cl. 4) | `test_refresh.py:1752` (answer rows), `:1769` (standings), `:1784` (first artifact) | real path: `refresh()` | B1, B2, B3, B7 | `refresh()` on the served artifact with `MODEL_RANKING_MAX_RANKED_ROWS=10`. Head refuses ("ranks 314 models; this process refuses past 10") and the live file is unchanged. Base published | GREEN |
| #57, round 1's B1: the nightly child checks the bounds the engine serves under | `test_nightly_refresh.py:581` | real path: a real child through `NightlyRefresh.run_once` | B4, B5 | n/a | GREEN; B6 survives: **T7** |
| #57: the engine's boot check reads the same function | `test_stage40_minors.py:57`; `test_board_standings.py:330`, `:467` | real path: `validate_startup_config` | B8, B9 | n/a | GREEN |
| REQ-REF-007: nothing the refresh loads imports `app.adapter` (round 1 M3, round 2 M9) | `test_refresh.py:294`, `:311` | real path: a fresh interpreter | H1 (on a scratch copy, run without the copy's `src` on the path) | n/a | GREEN; M9 is fixed |
| P3 #55: a second `/v1/boards` request does not rebuild (cl. 5) | `test_board_standings.py:237` (REQ-API-001); `:251` (a replaced artifact); `:274` (a publish during a build) | real path: the ASGI app | M1, M2, M3 | Real engine: the first request took 53 ms and the second 6 ms (base: 60 and 48 ms). After an `os.replace` publish, the removed board is gone on the next request. `chmod 000` answers 503, and 200 again after `chmod 644` | GREEN; M4 equivalent: **N2**; M5 survives: **T8** |
| P3 #55: a gzip request gets the compressed body with every security header; a non-gzip request is unchanged (cl. 5) | `test_board_standings.py:306` (REQ-API-001) | real path | Z1, Z2 | Real engine: 513,532 bytes become 38,311 on the wire. The decompressed body equals the identity body. The headers match the identity response's, apart from `content-encoding`: `vary: Accept-Encoding` and `nosniff` are both kept. The identity bytes equal base's. `/health` (89 B), `/v1/budgets` and a 404 are not compressed. `/v1/categories` and `/v1/recommendations` are | GREEN; Z3 equivalent: **N3** |
| P3 #77: D-173 records why unselectable boards stay (cl. 6) | `docs/decisions.md:3437-3440` | a ruling; no code | n/a | n/a | MET |
| P4 #71: a forced interleaving (EBADF after the close) still reports the deadline | `test_fetch_bounds.py:310` | unit: `fetch_bounded_bytes` against a stand-in client | D1, D2 | Ten runs each way, deterministic. With head's tests and base's `protocols.py`, 10 of 10 fail. At head, 10 of 10 pass. The original flaky case (`_header_drip`) passed in all 18 full parallel runs this seat made | GREEN |
| P4 #79: `RUN_CONTRACT_TESTS=1` tests for the Epoch boards and `model_metadata.csv`, skipped otherwise | `tests/integration/test_epoch_bundle_contract.py:30`, `:52` (#79, REQ-CI-001) | the live bundle through `fetch_bundle` and the real parsers | n/a | Without the switch, 2 skipped with the stated reason. With it, run once: 2 passed in 1.4 s. 25 skipped on this Mac matches `docs/skip-budget.txt` | GREEN |
| P4 #76: the retired installer is gone, and a test fails if a script installs `com.hcs.modelranking.refresh` (cl. 7) | `test_engine_service.py:509` | a scan of the tree | X1 | the four scripts and the plist are absent at head | GREEN; X2 survives: **T9** |

**The scoped REQ-IDs** (`docs/plans/m18-plan.md:33`):
- **REQ-CAN-001:** `test_moving_aliases.py:94` and `test_refresh.py:1685` cite it. Both are GREEN.
- **REQ-API-001:** `test_board_standings.py:237` and `:306` cite it. Both are GREEN.
- **REQ-REF-009:** `test_refresh.py:1799` cites it. That test holds the baseline, not the night
  (**T6**). The requirement's existing cycle-level citing tests are GREEN and kill A7:
  `test_refresh_carry.py:89`, `test_carry_forward.py:60`, `:84` and `test_nightly_refresh.py:542`.
- **REQ-ING-004:** no W4 test cites it. Its existing citing tests are GREEN:
  `test_schema.py:31`, `test_aider_ingest.py:77`, `test_litellm_ingest.py:61`, `:74` and
  `test_arena_client.py:175`. The wave changes no provenance code. See **N4**.

**The PRD's evidence pointers.** Round 2's M10 named eight `file:line` pointers in `docs/prd.md`
that the wave's test edits had moved. `4d07e50` re-pointed them. I resolved each of the thirteen
`test_refresh.py` and `test_nightly_refresh.py` pointers to its enclosing `def`, at `d528fd3` and at
`4d07e50`. Every one names the same test at both refs.

## Red→green on reported symptoms

How the replay was run:
- Each commit was extracted with `git archive` into a scratch tree, with the served artifact
  copied in.
- `PYTHONPATH` pointed at that tree's `src`, and HOME was a scratch folder.
- "Items" counts the parametrized cases of the tests that the red commit adds.

| pair | items: red / fix | notes |
|---|---|---|
| `6858d30` → `293c918` | 6 of 8 FAIL / 8 PASS | The two that pass on red are correct controls: `nobody_resolves` (a positive control) and `grok-4.20-reasoning-latest` (a trailing `-latest`, already refused). The rank failure is the symptom itself: `['gpt-5', 'claude-4.5-opus'] == ['claude-4.5-opus', 'gpt-5']` |
| `e4e2695` → `293c918` | 7 of 9 FAIL / 9 PASS | The pick test is red by `ImportError: cannot import name 'first_cheapest'`, not by an assertion (**T2**) |
| `35c87e9` → `4a47877` | 5 of 6 FAIL / 6 PASS | `re_spells_names_moves_no_guard` is red by `ImportError` (`display_changes`). Its cycle twin reproduces #39 by behaviour: "coding would be 12 of 12 models this artifact has never seen". The 8→7 case passes on red, as a control should |
| `1d7cfaa` → `6c0c242` | 2 of 3 FAIL / 3 PASS | `a_replaced_artifact_is_built_again` passes on red. With no memo, every request rebuilds, so it is a correct control |
| `baebf92` → `5623f4b` | 2 of 2 FAIL / 2 PASS | #71 fails with the reported message: `probe fetch failed: OSError: [Errno 9] Bad file descriptor` |
| `81a3942` → `77d3b2f` | 3 of 11 FAIL / 11 PASS | B1: the child saw `500/25000/5000` against `1000/30000/10`. M1: `swebench` was still served. R3: `gpt-4o-latest-v2`. The M3, M4 and R2 tests pass on red, as their commit says: they pin behaviour that was already there |
| `4d07e50` (tests and fix in one commit) | its new and changed tests run on `77d3b2f`'s `src`: 8 of 9 PASS | These pin round 2's minors. They are not red-first, and the commit does not claim they are. The ninth fails only because `_DEFAULTS` did not exist yet |

**Weakened or deleted tests.** I read every line the range removes under `tests/`.
- **`test_refresh_job_install.py` (4 tests) and
  `test_the_retirement_script_removes_what_the_installer_installed`:** they pinned the files #76
  deletes. They go with those files.
- **`test_equal_scores_and_equal_prices_break_on_name`:** it becomes
  `..._keep_the_rankings_order`. Its assertion flips from `["a", "b"]` to `["b", "a"]`. That is the
  behaviour D-173 clause 1 changes, not a weakening.
- **The standings default pin:** it now reads `serving_bounds._DEFAULTS` instead of a regex over
  the source. It checks the same value, 25000.

No test was skipped or weakened. The two new skips are the env-gated contract tests, and they are
in the skip budget (73 → 75).

## Suite result
- **`make check-fast` at `4d07e50`: PASS, rc 0, in 84 s.** This seat's guards were in front (see
  Safety). No guard fired.
  - lint, typecheck and records: PASS.
  - test: **1592 passed, 25 skipped**. Total coverage 91.70 %. `coverage-floor`: PASS, 42 modules.
  - client-decls: PASS, 15 files in 4 configurations.
  - swift-test (parallel): PASS, 363 tests, exactly the manifest.
- **`make wave-check-all`: PASS, rc 0.** 48 records validated.
- **Coverage on touched code** (permission-matrix §11).
  - Method: `pytest tests -n auto --cov=src/app --cov-branch`, with `MODEL_RANKING_REQUIRE_ARTIFACT=1`
    and a scratch HOME.
  - It ran on `git archive` copies of `d528fd3` and `4d07e50`, each with the same artifact (sha256
    `5c6977a9c67c…`).
  - Base: 1569 passed, 23 skipped. Head: 1592 passed, 25 skipped.

| module | base `d528fd3` | head `4d07e50` | change |
|---|---|---|---|
| `adapter/main.py` | 97.27 % (433 st / 12 miss; 116 br / 3) | 98.04 % (399 / 8; 110 / 2) | +0.77 |
| `adapter/nightly.py` | 99.62 % | 99.63 % | +0.01 |
| `clients/protocols.py` | 100.00 % | 100.00 % | 0 |
| `workflows/build.py` | 94.93 % | 95.06 % | +0.13 |
| `workflows/rank.py` | 97.47 % | 97.50 % | +0.03 |
| `workflows/recommend.py` | 95.39 % | 95.42 % | +0.03 |
| `workflows/refresh.py` | 95.96 % | 96.11 % | +0.15 |
| `workflows/registry.py` | 98.72 % | 98.72 % | 0 |
| `workflows/serving_bounds.py` (new) | n/a | 95.51 % (77 / 4; 12 / 0) | new |
| total | 91.57 % | 91.70 % | +0.13 |

No touched module dropped.
- `serving_bounds.py:110-111` and `:136-137` are its four missed lines. They are the `sqlite3.Error`
  arms that `main.py` missed at base, moved with the code.
- `main.py`'s misses fall from 12 to 8, and `serving_bounds.py` misses 4. That is the same 12.

## Mocks / contract tests
- **Epoch bundle (#79).** The canonical path is the real `fetch_bundle` and the real parsers. The
  unit tests feed them fixtures. The new contract test reads the live bundle through the same
  download and the same parsers, and it passed live once here. No parallel fake was added.
- **httpx under `bounded_get` (#71).** `_ClosingRaces` (`test_fetch_bounds.py:284`) stands in for
  `httpx.Client` in one test.
  - It forces one interleaving, a read that fails only after `close()`, which the module's
    canonical transport cannot produce.
  - It is a fault-injection double for that interleaving, not a second fake of an upstream. I do not
    count it as a parallel mock.
- **launchd.** No new stub. The #76 test reads the tree and runs nothing.
- **No new external integration.**

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T1** `src/app/workflows/rank.py:332`; `tests/unit/test_rank.py:262`. **"Ties are ordered by model id" is held only as "a re-spelling moves nothing".**
   1. D-173 clause 1 says a tie is ordered by model id. The picks take "the first row in the ranking's
      order (score, then id)".
   2. The only test re-spells two tied models and asserts that the order did not change. Any key
      the re-spelling does not touch passes it.
   3. Fault R2 (`ORDER BY b.best DESC, m.rowid`) passed the whole suite (1592 passed). So did fault
      R3 (`m.id DESC`).
   4. R2 is the one that matters. `models` is a rowid table that `INSERT OR REPLACE` refills on every
      build, so its order is the order the build registered the models in. A tie would then move
      whenever the registration order moves, with nothing measured. That is #44's symptom by
      another key.
   5. The code is right today. On the served artifact, every run of equal raw score is in id order
      at head (50 of 50).
   6. **The fix:** `test_a_tie_is_ordered_by_id_whatever_order_the_models_were_registered_in`,
      below. It gives the table an insertion order opposite to the ids and asserts the ids'
      order. It kills R2 and R3.
- **T2** `src/app/workflows/recommend.py:507`, `:511`; `tests/unit/test_pareto_dominance.py:196`. **The picks' half of #44 is held on the helper, not on the picks.**
   1. `first_cheapest` is tested alone. Fault P2 restores the base's exact line at the value pick's
      call site (`min(value_pool, key=lambda r: (r.blended_per_m, r.model))`). Fault P3 does the
      same at the budget pick's. Each passed the whole suite.
   2. The helper's test went red at `e4e2695` by `ImportError`. So no test ever failed on the picks'
      pre-fix code path, which the profile's red→green rule asks for (practices.md, "Tests are the
      truth signal").
   3. **Why only MINOR:** the reported symptom of #44 is the ranking's tie order, and that was
      reproduced by assertion (`test_rank.py:262`, red at `6858d30`). The picks are D-173's own
      extension of it, and they are right at head.
   4. **The fix:** `test_the_value_and_budget_picks_take_a_price_tie_in_the_rankings_order`, below.
      It runs `recommend()` on two models tied on score and price, re-spelled so that their names
      sort against their ids. It is red on the pre-fix lines at either call site (P2, P3).
- **T3** `src/app/workflows/build.py:188`; `tests/unit/test_build.py:498`. **The discount's arithmetic is tested with one row.**
   1. Fault E5 counts at most one resolved row per source (`resolved[...] = 1`). It passed the whole
      suite.
   2. #45 measured 7 such rows for aider and 9 for each agent board. Under E5 those sources would
      still report 6 and 8 unknown efforts, which is the overcount #45 was filed for.
   3. **The fix:** `test_every_suffix_the_reconcile_resolves_leaves_the_count`, below. Two derived
      rows resolve and one stays unknown, so the count must be exactly 1. It kills E5.
- **T4** `src/app/workflows/registry.py:446`, `:203-206`; `tests/unit/test_moving_aliases.py:93`; `docs/decisions.md:3448`. **Round 2's M12 pin cannot fail, and D-173 clause 8's example is the same false case.**
   1. `4d07e50` added `gpt-4o-latest-video` to pin the `v`-word edge. `video` is in
      `_MODALITY_TOKENS` (`registry.py:204`), so `derive_identity` returns None at its first line,
      before the `-latest` rule runs.
   2. Fault L2 is round 2's `r3-loose` mutant, `(?:-(?!v)|\Z)`. It still passed the whole suite.
      Under it, `openai/gpt-4o-latest-vibe` and `gpt-4o-latest-voice` derive ids. Measured.
   3. Round 2's own suggestion, `-latest-vision`, is a modality word too (`registry.py:205`).
   4. D-173 clause 8 gives `-latest-video` as its example of the edge.
   5. **The fix:** `test_a_latest_token_followed_by_a_v_word_is_refused_by_the_token`, below. It
      asserts first that the name without `-latest` derives, so the None can only be the token's.
      It kills L2. Replace `-latest-video` in the existing list and in clause 8.
- **T5** `src/app/workflows/refresh.py:1196`, `:764`. **A refused night's re-spellings are not held.**
   1. `write_status` says "a refused night lists it too", and `_cycle` passes `renamed` on its
      refusal.
   2. Fault G5 drops it from the refusal. It passed the whole suite. Only the publishing path is
      tested (`test_refresh.py:1700`).
   3. D-173 clause 2 records a display change "in the refresh record as information". On a refused
      night that record is the operator's only account of the night.
   4. **The fix:** `test_a_refused_night_still_records_its_re_spellings`, below. It kills G5.
- **T6** `src/app/workflows/refresh.py:900`, `:1161`; `tests/unit/test_refresh.py:1799`. **Round 2's M8(1) is not closed: the expiry night is still not run, and its mutant survives.**
   1. Round 2 asked for "one test [that] drives `_cycle` with `epoch_access` expired and asserts
      that the night publishes". `4d07e50` instead calls `degradations(_served_without(...), fresh)`
      by hand.
   2. Fault A5 replays round 2's `m-42-baseline`: `_reason_to_refuse` adds the accessibility
      reasons judged against the live artifact. It passed the whole suite, as it did in round 2.
   3. Under A5, every night after `model_metadata.csv` ages out is refused for a loss D-156
      clause 3 excuses. That is the freeze D-128 warns of, on the path REQ-REF-009 exists for.
   4. The REQ-REF-009 citation sits on the test that does not run the night.
   5. This is the third time the gap has been named (round 1 M4(3), round 2 M8(1), here).
   6. The behaviour is right today. `refresh()` on the served artifact with `epoch_access`
      reported expired publishes at head.
   7. **The fix:** `test_an_accessibility_expiry_night_publishes_through_the_cycle`, below. It runs
      `refresh()` with a build report naming `epoch_access` expired. It kills A5. Move or add the
      REQ-REF-009 citation there.
- **T7** `src/app/workflows/serving_bounds.py:68`; `tests/unit/test_nightly_refresh.py:599`. **`MODEL_RANKING_MAX_RANKED_ROWS` is never set by a test, and the B1 test cannot see a bound that ignores its variable.**
   1. The B1 test compares the child's bounds with the parent's own `bounds_from_env()`. A bound
      read from its default on both sides compares equal.
   2. Fault B6 makes the ranked bound ignore its variable, in the engine and the child alike. It
      passed the whole suite.
   3. No test anywhere sets this variable: `test_stage40_minors.py` patches the module attribute
      instead. The other two variables are set by `test_refresh.py:1757` and `:1773`.
   4. This is round 2's M6 option 2 ("asserts that every `ServingBounds` field moved"). `4d07e50`
      took option 1. That closes drift between the names, but not this case.
   5. The behaviour is right today. With the variable set to 10, `refresh()` refuses at head.
   6. **The fix:** `test_the_child_reads_every_bound_from_its_own_variable`, below. It asserts that
      the child's values are the overrides. It kills B6.
- **T8** `src/app/adapter/main.py:1422-1423`. **The memo's eviction is not held.**
   1. Fault M5 removes `if len(_BOARDS_MEMO) > 2: _BOARDS_MEMO.clear()`. It passed the whole suite.
   2. Every nightly publish is a new artifact identity (D-129 publishes by replacing the file).
   3. Measured with `tracemalloc` on the served artifact, one kept payload is about **2.3 MB**. That is
      roughly 70 MB a month for an engine the service keeps running.
   4. D-173 clause 5 says "memoised on the artifact's identity" and says nothing about the bound.
   5. **The fix:** `test_the_boards_memo_keeps_no_more_than_a_few_artifacts`, below. It publishes
      six artifacts under one client. It kills M5.
- **T9** `tests/unit/test_engine_service.py:515`. **The #76 guard reads only the top level of `scripts/` and `deploy/`.**
   1. `folder.iterdir()` does not descend. `scripts/` already has two subfolders (`router_probe/`,
      `simtools/`).
   2. Fault X2 puts the base's `scripts/enable_refresh.sh` back as `scripts/simtools/enable_refresh.sh`.
      It passed the whole suite.
   3. Fault X1 restores the plist at `deploy/`. It is killed.
   4. **The fix:** `rglob("*")` with `__pycache__` skipped, below. It is green at head and kills X2.

## Notes (no change required by this verdict)

- **N1** **Equivalent: E4** (`build.py:175`, counting every `unspecified` row, suffix or not).
   1. The reconcile writes an effort only in `_register_derived` (`registry.py:599`). It writes the
      effort a `_UNDERSCORE_EFFORT` or `_PAREN_EFFORT` suffix states, from `EFFORT_LEVELS`.
   2. `resolve_effort` matches the same suffixes (`_EFFORT_SUFFIX`, `_PAREN_EFFORT`, the same five
      levels).
   3. So a row the reconcile resolves was always one the ingest counted. Widening the filter
      changes no count on any input I could build.
- **N2** **Equivalent: M4** (round 2's `m1-second-read`). Without the identity re-read after the
  build, a payload built across a publish is filed under the retired key.
   1. That key carries the old inode, ctimes and size, and nothing can produce it again.
   2. APFS does not reuse an inode number soon after the file goes.
   3. I agree with round 2: the re-read is defence in depth, not a gap.
- **N3** **Equivalent: Z3** (`minimum_size=0`). Compressing responses under 1 KB breaks nothing
  D-173 clause 5 states.
   1. The clause promises compression at 1 KB or more. It does not forbid it below.
   2. Every client that sends `Accept-Encoding: gzip` must decode it. The live probe shows the
      1 KB line is applied as designed.
- **N4** **REQ-ING-004 is proven, but no W4 record says so.** Round 2's M8(3) asked for one of two
  things: cite REQ-ING-004 where the wave touches provenance, or record why it is out of scope.
  `4d07e50` did neither, and its message does not mention it.
   1. The requirement's existing citing tests are GREEN (listed above), and the wave changes no
      provenance code. So this is not a missing citing test.
   2. The wave-close should record M8 part by part: (1) is **T6**, (2) is fixed, (3) is this note.
      Otherwise `make wave-check` will read M8 as fixed whole.
   3. The nearest apt home for a citation is the #79 contract test, which reads only the documented
      raw-data endpoint (D-101).
- **N5** **The live engines and the refresh probes ran on archive copies, never on the worktree.**
  The fault runs were mutating the worktree at the time, so the probes could not use it. The
  copies are byte-identical to the commits (`git archive`).

## K.9 candidates spotted outside this wave's scope
- none

## Fault injection (HIGH: mandatory)

**Harness:** scratch `w4t/mut.py`. For each fault it does the following:
1. It checks every file it touches against `HEAD`: `git hash-object` must equal
   `git rev-parse HEAD:<file>`.
2. It records each file's sha256 and saves its bytes.
3. It makes exact string edits, each required to match exactly once. All 53 edits were dry-run
   first, for the match count and for syntax.
4. It runs the targeted test files with `-n auto`. If nothing fails, it runs the whole of `tests/`
   with `-n auto` and `MODEL_RANKING_REQUIRE_ARTIFACT=1`.
5. It writes the original bytes back **in place**, never with `git checkout` or `restore`.
6. It asserts three things: sha256 equals the pre-edit hash, `git hash-object` equals HEAD's blob,
   and `git diff --quiet` holds with `git status --porcelain` empty.

X1 and X2 instead create an untracked file and delete it, and then assert an empty
`git status --porcelain --untracked-files=all`. All 55 rows of the log (`w4t/logs/mutants.jsonl`)
say `restored: true`.

After the run, all 669 tracked files match the sha256 baseline taken before the first fault
(`shasum -c`: 669 OK). `git status --porcelain` was empty and `git diff --quiet` held. Every kill
is a test assertion: no fault was killed by an import or collection error.

**Restore hashes** (sha256 prefix, pre = post, and the HEAD blob that `git hash-object` matched):

| file | faults | sha256 (pre = post) | HEAD blob |
|---|---|---|---|
| `src/app/workflows/rank.py` | 4 | `5bd30f9e7683` | `60b5fc0742` |
| `src/app/workflows/recommend.py` | 6 | `e794a9fcdce5` | `80b08cb345` |
| `src/app/workflows/build.py` | 5 | `cdfb667fdcc1` | `d75faa3d15` |
| `src/app/workflows/registry.py` | 5 | `4b946c023969` | `6d41cc1be3` |
| `src/app/workflows/refresh.py` | 18 | `227db22ab772` | `c91b92c7d8` |
| `src/app/adapter/nightly.py` | 2 | `37da5291cd75` | `c571a46f9b` |
| `src/app/workflows/serving_bounds.py` | 2 | `03150e0c3a16` | `a401c323d7` |
| `src/app/adapter/main.py` | 9 | `18b4c67caebe` | `a5b6a281bc` |
| `src/app/clients/protocols.py` | 2 | `974ccf567b84` | `7e36ee6a1f` |
| untracked: `deploy/com.hcs.modelranking.refresh.plist`, `scripts/simtools/enable_refresh.sh` | 2 | created, then removed; `git status --porcelain` empty | n/a |
| scratch copy only: `w4t/trees/prop/src/app/workflows/serving_bounds.py` (H1) | 1 | `03150e0c3a16` (pre = post) | not in the worktree |

**The faults.** "Whole suite" means 1592 passed, 25 skipped.

| id | the fault | result | killed by |
|---|---|---|---|
| R1 | rank: ties by display name again | KILLED | `test_rank.py:262` |
| R2 | rank: ties by rowid (the order the models were registered in) | **SURVIVED** (whole suite) | **T1** |
| R3 | rank: ties by id descending | **SURVIVED** (whole suite) | **T1** |
| R4 | `ranked_with_ids` hands the display name as the id | KILLED | `test_refresh.py:1685`, `:1700` |
| F1 | frontier: a full tie broken by display name again | KILLED | `test_pareto_dominance.py:181` |
| F2 | frontier: rows reversed before the stable sort | KILLED | `test_pareto_dominance.py:181` |
| P1 | `first_cheapest`: a price tie broken by display name | KILLED | `test_pareto_dominance.py:196` |
| P2 | the value pick's call site restored to the base's name key (helper intact) | **SURVIVED** (whole suite) | **T2** |
| P3 | the budget pick's call site restored to the base's name key (helper intact) | **SURVIVED** (whole suite) | **T2** |
| P4 | `first_cheapest`: the last of equal prices wins | KILLED | `test_pareto_dominance.py:196` |
| E1 | the discount is never applied | KILLED | `test_build.py:498` |
| E2 | the unconfirmed rows are read after the reconcile | KILLED | `test_build.py:498` |
| E3 | every counted row is discounted, resolved or not | KILLED | `test_build.py:516` |
| E4 | every `unspecified` row is counted, suffix or not | SURVIVED, equivalent | **N1** |
| E5 | at most one resolved row discounted per source | **SURVIVED** (whole suite) | **T3** |
| L1 | only a trailing `-latest` moves (pre-#48) | KILLED | `test_moving_aliases.py:94` |
| L2 | any word starting with `v` after `-latest` derives (round 2's `r3-loose`) | **SURVIVED** (whole suite) | **T4** |
| L3 | a name ending in `-latest` derives again | KILLED | `test_moving_aliases.py:85`, `:108`, `:123` |
| L4 | a version after `-latest` no longer derives | KILLED | `test_moving_aliases.py:103` |
| L5 | the token is looked for only at the start of the name | KILLED | `test_moving_aliases.py:85`, `:108`, `:123` |
| G1 | the surface rosters are compared by display name again | KILLED | `test_refresh.py:1685`, `:1700` |
| G2 | `display_changes` reports nothing | KILLED | `test_refresh.py:1685`, `:1700` |
| G3 | the record's `renamed` list is always empty | KILLED | `test_refresh.py:1700` |
| G4 | a published night drops its re-spellings | KILLED | `test_refresh.py:1700` |
| G5 | a refused night drops its re-spellings | **SURVIVED** (whole suite) | **T5** |
| G6 | `display_changes` lists the unchanged names | KILLED | `test_refresh.py:1685`, `:1700` |
| G7 | `displays` keyed by display, not id | KILLED | `test_refresh.py:1685`, `:1700` |
| A1 | the accessibility guard removed | KILLED | `test_refresh.py:1736`, `:1799` |
| A2 | exactly a quarter lost no longer refuses (`<=` → `<`) | KILLED | `test_refresh.py:1736` |
| A3 | the limit is three quarters lost, not one | KILLED | `test_refresh.py:1736` |
| A4 | the summary never counts accessibility values | KILLED | `test_refresh.py:1736`, `:1799` |
| A5 | expiry night: accessibility judged against the live artifact, not the baseline (`m-42-baseline`) | **SURVIVED** (whole suite) | **T6** |
| A6 | expiry night: the baseline keeps the expired source's `access` rows | KILLED | `test_refresh.py:1799`; `test_refresh_carry.py:449`, `:514` |
| A7 | expiry night: no baseline at all | KILLED | `test_refresh_carry.py:124`, `:251`; `test_refresh_boards.py:147` (and 2 more) |
| B1 | the refresh never checks the bounds | KILLED | `test_refresh.py:1752`, `:1769`, `:1784` |
| B2 | the bounds skipped on a first artifact | KILLED | `test_refresh.py:1784` |
| B3 | `_cycle` does not hand the candidate to the check | KILLED | `test_refresh.py:1752`, `:1769`, `:1784` |
| B4 | the child's allowlist drops the bound variables (round 1's B1) | KILLED | `test_nightly_refresh.py:581` |
| B5 | the child's allowlist carries two of the three | KILLED | `test_nightly_refresh.py:581` |
| B6 | `MODEL_RANKING_MAX_RANKED_ROWS` ignored, in the engine and the child alike | **SURVIVED** (whole suite) | **T7** |
| B7 | the refresh checks the defaults, not the environment | KILLED | `test_refresh.py:1752`, `:1769`, `:1784` |
| B8 | `egress_problems` drops the ranked-model bound | KILLED | `test_stage40_minors.py:57` |
| B9 | the engine checks standings against the answer bound | KILLED | `test_board_standings.py:330`, `:467` |
| M1 | no memo lookup | KILLED | `test_board_standings.py:237` |
| M2 | the memo keyed on the path, not the artifact's identity | KILLED | `test_board_standings.py:251`, `:274` |
| M3 | the identity read after the open (round 2's `m1-order`) | KILLED | `test_board_standings.py:274` |
| M4 | the identity not re-read after the build (round 2's `m1-second-read`) | SURVIVED, equivalent | **N2** |
| M5 | the memo never evicted | **SURVIVED** (whole suite) | **T8** |
| Z1 | no compression middleware | KILLED | `test_board_standings.py:306` |
| Z2 | a threshold so high that nothing compresses | KILLED | `test_board_standings.py:306` |
| Z3 | threshold 0: every response compressed | SURVIVED, equivalent | **N3** |
| D1 | "late" decided after the close (pre-#71) | KILLED | `test_fetch_bounds.py:310` |
| D2 | never "late" | KILLED | `test_fetch_bounds.py:310` |
| X1 | the retired plist back in `deploy/` | KILLED | `test_engine_service.py:509` |
| X2 | the retired installer back, one folder down (`scripts/simtools/`) | **SURVIVED** (whole suite) | **T9** |
| H1 | scratch copy: `serving_bounds.py` imports `app.adapter`; run without the copy's `src` on the path, with the venv installed from the clean worktree | KILLED (`['app.adapter']`) | `test_refresh.py:294` (round 2's M9 is fixed) |

## Tests added/extended this review

**None in the repository.** This seat may change only this file. Each test below was written into a
scratch copy of `4d07e50` (scratch `w4t/trees/prop`; the whole diff is `w4t/logs/proposed-tests.diff`).
- **Green with the tests in place:**
  1. Each is GREEN there.
  2. The copy's whole suite passes: 1601 passed, 25 skipped.
  3. `ruff check` passes on every file touched.
- **Red on its fault:** each was run against the fault it is written for, in that copy. Each goes
  red by assertion (`w4t/logs/propcheck.json`):
  1. R2 and R3 by T1;
  2. P2 and P3 by T2;
  3. E5 by T3;
  4. L2 by T4;
  5. G5 by T5;
  6. A5 by T6;
  7. B6 by T7;
  8. M5 by T8;
  9. X2 by T9.
- **Restored:** every fault was then restored and checked by sha256.

**T1 and T2.** In `tests/unit/test_rank.py`, with a shared helper:
```python
def _tied_pair(pricing: str = PRICING) -> sqlite3.Connection:
    """Claude 4.5 Opus and GPT-5 tied on SWE-bench Verified, through the real ingest and reconcile."""
    conn = connect()
    scores = json.dumps({"leaderboards": [{"name": "Verified", "results": [
        {"name": "live-SWE-agent + Claude 4.5 Opus", "resolved": 74.4, "date": "2025-09-01"},
        {"name": "mini-SWE-agent + GPT-5", "resolved": 74.4, "date": "2025-09-01"},
    ]}]})
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    build_price_medians(conn)
    return conn


def test_a_tie_is_ordered_by_id_whatever_order_the_models_were_registered_in() -> None:
    """W4 Tester T1 (#44, D-173 clause 1): the test above proves a re-spelling moves nothing; this
    proves the order IS the id's. A key that is stable but is not the id -- the order the models were
    registered in, or the id descending -- passed every test."""
    conn = _tied_pair()
    ids = [model_id for (model_id,) in conn.execute("SELECT id FROM models ORDER BY id").fetchall()]
    for index, model_id in enumerate(ids):  # the table's own order becomes the reverse of the ids'
        conn.execute("UPDATE models SET rowid = ? WHERE id = ?", (10_000 - index, model_id))
    ids_by_display = dict(conn.execute("SELECT display, id FROM models").fetchall())
    order = [ids_by_display[row.model] for row in coding_ranking(conn)]
    assert len(order) == 2
    assert order == sorted(order)


def test_the_value_and_budget_picks_take_a_price_tie_in_the_rankings_order() -> None:
    """W4 Tester T2 (#44, D-173 clause 1): `first_cheapest` is tested alone; this holds the two picks
    that call it. Two models tied on score AND price, re-spelled so that their names sort against
    their ids: every pick names the first by id."""
    from app.workflows.recommend import recommend

    price = {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05}
    conn = _tied_pair(json.dumps({"gpt-5": price, "claude-4-5-opus": price}))
    conn.execute("UPDATE models SET display = 'Zz ' || display WHERE id = (SELECT min(id) FROM models)")
    conn.execute("UPDATE models SET display = 'Aa ' || display WHERE id = (SELECT max(id) FROM models)")
    (first,) = conn.execute("SELECT display FROM models ORDER BY id LIMIT 1").fetchone()
    answer = recommend(conn, "unlimited", "coding")
    assert answer is not None and answer.frontier_size == 2
    assert [pick.model for pick in answer.picks] == [first, first, first]
```

**T3.** In `tests/unit/test_build.py`:
```python
def test_every_suffix_the_reconcile_resolves_leaves_the_count() -> None:
    """W4 Tester T3 (#45, REQ-CAN-005): the test above resolves one row in a source; the real boards
    resolve several (aider 7, each agent board 9, #45). A discount of one per source passed."""
    pricing = json.loads(PRICING)
    pricing["openai/gpt-6-astra"] = {"mode": "chat", "input_cost_per_token": 1e-06, "output_cost_per_token": 4e-06}
    aider = json.dumps([
        {"model": "gpt-5 (high)", "pass_rate_2": 61.0, "edit_format": "diff"},
        {"model": "claude-4-5-opus", "pass_rate_2": 70.5, "edit_format": "diff"},
        {"model": "gpt-6-astra_high", "pass_rate_2": 55.0, "edit_format": "diff"},
        {"model": "gpt-6-astra_low", "pass_rate_2": 41.0, "edit_format": "diff"},
        {"model": "zorblax-9_high", "pass_rate_2": 30.0, "edit_format": "diff"},
    ])
    conn = connect(":memory:")
    report = _build(conn, sources=_sources(pricing=json.dumps(pricing), aider=aider))
    stored = dict(conn.execute("SELECT raw_name, effort FROM scores WHERE raw_name LIKE 'gpt-6-astra_%'").fetchall())
    assert stored == {"gpt-6-astra_high": "high", "gpt-6-astra_low": "low"}
    (aider_report,) = [r for r in report.sources if r.source == "aider"]
    assert aider_report.effort_unknown == 1  # zorblax-9_high, and only it
```

**T4.** In `tests/unit/test_moving_aliases.py`. Also replace `gpt-4o-latest-video` at `:93`, and
the example in D-173 clause 8:
```python
@pytest.mark.parametrize("name", ["openai/gpt-4o-latest-vibe", "gpt-5-latest-venus"])
def test_a_latest_token_followed_by_a_v_word_is_refused_by_the_token(name: str) -> None:
    """W4 Tester T4 (#48, D-173 clause 8): `gpt-4o-latest-video` derives nothing because `video` is a
    modality word (`registry._MODALITY_TOKENS`), not because of the token, so it cannot hold the
    `v`-word edge. The same name without `-latest` derives, so the None here is the token's."""
    assert derive_identity(name.replace("-latest", "", 1)) is not None, "the case would test another rule"
    assert derive_identity(name) is None
```

**T5 and T6.** In `tests/unit/test_refresh.py`:
```python
def test_a_refused_night_still_records_its_re_spellings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W4 Tester T5 (#39, D-173 clause 2): `write_status` says a refused night lists them too, and the
    cycle passes them on its refusal. Nothing held either."""
    import json

    live = _wide(tmp_path / "advisor.db", models=12)
    monkeypatch.setenv("MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS", "11")

    def renaming(argv: list[str]) -> int:
        _renamed(Path(argv[argv.index("--db") + 1]))
        return 0

    outcome, code = refresh(live, builder=renaming)
    assert code == EXIT_REFUSED, outcome.reason
    record = json.loads((tmp_path / "advisor.db.refresh.json").read_text(encoding="utf-8"))
    assert "Probe 00 -> Renamed probe-00" in record["renamed"]


def test_an_accessibility_expiry_night_publishes_through_the_cycle(tmp_path: Path) -> None:
    """W4 Tester T6 (#42, D-156 clause 3, REQ-REF-009): the test above calls `degradations` with the
    baseline by hand. This runs the night: `epoch_access` has aged out, its values leave on purpose,
    and the cycle publishes rather than refusing."""
    import json

    live = _accessible(tmp_path / "advisor.db", values=8)

    def expiring(argv: list[str]) -> int:
        _accessible(Path(argv[argv.index("--db") + 1]), values=0)
        Path(argv[argv.index("--report-out") + 1]).write_text(json.dumps(
            {"arrived": [], "carried": {}, "expired": {"epoch_access": None}, "since": {}}), encoding="utf-8")
        return 0

    outcome, code = refresh(live, builder=expiring)
    assert code == EXIT_PUBLISHED, outcome.reason
```

**T7.** In `tests/unit/test_nightly_refresh.py`. It could instead replace the last assertion of
`:581`:
```python
def test_the_child_reads_every_bound_from_its_own_variable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W4 Tester T7 (#57, D-173 clause 4): the B1 test compares the child with the parent's own
    reading, so a bound that ignores its variable in both passes it. Each bound the child checks
    must be the value its variable set."""
    from app.workflows import serving_bounds

    overrides = {name: 1000 + index for index, name in enumerate(serving_bounds.BOUND_VARIABLES)}
    for name, value in overrides.items():
        monkeypatch.setenv(name, str(value))
    seen = tmp_path / "bounds.json"
    code = ("import dataclasses, json; from app.workflows.serving_bounds import bounds_from_env; "
            f"json.dump(dataclasses.asdict(bounds_from_env()), open({str(seen)!r}, 'w'))")
    assert asyncio.run(_child(tmp_path, code).run_once("nightly")) == 0
    assert sorted(json.loads(seen.read_text(encoding="utf-8")).values()) == sorted(overrides.values())
```

**T8.** In `tests/unit/test_board_standings.py`:
```python
def test_the_boards_memo_keeps_no_more_than_a_few_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W4 Tester T8 (#55, D-173 clause 5): every nightly publish is a new artifact identity, and one
    payload holds about 2.3 MB on today's artifact. Without its clear the memo keeps one per night
    for the life of the engine; nothing held the clear."""
    from app.adapter import main as adapter

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    client = TestClient(adapter.app)
    for night in range(6):
        published = tmp_path / f"night-{night}.db"
        _seeded_db(published)
        published.replace(db)
        assert client.get("/v1/boards").status_code == 200
    assert len(adapter._BOARDS_MEMO) <= 3
```

**T9.** In `tests/unit/test_engine_service.py:515`, replace the iteration:
```python
        for path in sorted(folder.rglob("*"))  # W4 Tester T9: every folder below, not the top only
        if path.is_file() and path.suffix != ".md"  # what runs or installs, not what describes it
        and "__pycache__" not in path.parts
```

## Safety (this seat's rules)

- **Neither installer script was executed by this seat.**
  1. `scripts/install_engine_service.sh` and `scripts/remove_engine_service.sh` ran only inside
     `tests/unit/test_engine_service.py`, with its `_install` stubs and its scratch HOME.
  2. That happened in the gate and in the fault runs.
  3. No fault touched either installer.
- **No `launchctl`, `xcodebuild` or `simctl` ran, and nothing ran on the simulator.**
  1. The provided `guard-bin` was first on PATH in every command.
  2. This seat added an `xcrun` filter that refuses `simctl`, `xcodebuild` and `devicectl`.
     `client-decls` used `xcrun` only for `--show-sdk-path` and `swiftc -typecheck`.
  3. `swift test` ran on macOS only, as a `check-fast` leg.
  4. Each guard was fired once, on purpose, to prove it refuses: `launchctl print` exited 97, and
     `xcrun simctl list` exited 97. Neither fired otherwise.
- **Nothing bound beyond loopback, and nothing bound 8080.**
  1. A `sitecustomize` guard was on `PYTHONPATH` for every Python run.
  2. It refuses five things: a bind that is not 127.0.0.1, localhost or ::1; port 8080; ports up to
     8100 other than 0; a connect to a non-loopback address; and DNS for a real name. Each refusal
     raises an exception and is logged. None calls `abort`.
  3. It was fired on purpose once per rule (0.0.0.0:8150, 127.0.0.1:8080, 127.0.0.1:8050, a LAN
     address, `example.com`, 1.1.1.1). The log was then cleared.
  4. After that it logged **nothing** across the gate, all 55 fault runs, the coverage runs and the
     probes.
  5. The live engines bound 127.0.0.1:8171-8174 only. Each was stopped with SIGTERM (exit -15), and
     a connect afterwards was refused.
- **The network.** No test reached it. The one exception was a single `RUN_CONTRACT_TESTS=1` run of
  `tests/integration/test_epoch_bundle_contract.py`, with the guard's network rule lifted for that
  run only. The bodies of the wave's eleven issues and the titles of #100 to #106 were read with
  `gh issue view`. That is a read, and nothing was written.
- **Changes.** No commit, no push, no GitHub write.
  1. The only tracked change in the worktree is this file.
  2. Every fault was reverted in place and checked byte-identical (table above). No `git checkout`
     or `restore` was used.
  3. `epb.html`, `or.md` and `.github/**` were not touched.
  4. Scratch work is under the session scratchpad's `w4t/` folder.
