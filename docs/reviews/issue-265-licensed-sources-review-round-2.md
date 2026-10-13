---
record_type: review
id: issue-265-licensed-sources-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# Independent review, round 2: #265, the unlicensed sources move to licensed data (D-194)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `015cfa4..b8f5de4`
**Risk tier:** MEDIUM

## Verdict
MINOR

Every round-1 finding is fixed in substance. Three new minor findings remain: the ARC-AGI-2
comparison is misaligned for runs made before ARC Prize revised five tasks, three planted faults
still survive, and D-194's cost counts do not reproduce. None of them changes a served number
today.

How the review was done:
- **Commits.** I read the three commits in the range (`e42ee05` red, `1f70333` fix, `b8f5de4` docs)
  against round 1 and D-194.
- **Network.** I made 6 read-only GETs: the `data/evaluation` commit history of `arcprize/ARC-AGI-2`,
  its root listing and `LICENSE` at `f3283f72`, task `4a21e3da` at `f3283f72` and at `14fba875`, and
  GPT-4.1's attempt file for that task at revision `026789c1`.
- **Engine checks.** I ran the startup preflight, `standings_problem`, `board_standings` and the
  refresh's publish gates (`degradations`, `upward_anomalies`). They ran over copies of `main`'s
  served artifact (sha256 `80fa996a…`) and of the branch artifact (`98ebbbd7…`), with this branch's
  code, and for the rollback direction with `main`'s code (`w-main-measure/src` on this worktree's
  own venv).
- **Faults.** I planted 17 faults, each restored from its bytes and checked by sha256: 14 were
  killed and 3 survived (N2).
- **Tests.** The unit suite passes: 2690 passed, 9 skipped. `git status` was clean at the end, apart
  from this file.

## Round 1's findings

| Finding | Status | Evidence |
|---|---|---|
| B1 | Fixed | GPT-5 Pro is at 13.3 and Claude Sonnet 4.5 (32k) at 14.7. The unmarked settings land near ARC Prize's published semi-private figures (Haiku 4.5 32k 5.1, Grok 4 Fast 4.6). A `null` mark is never a 0 unless the answer is wrong (planted `return False` is killed). A residual misalignment for pre-revision runs is N1. |
| B2 | Fixed | **Startup on `main`'s artifact:** the preflight and `standings_problem` print no problem. **Payload:** it credits `arc_prize_leaderboard`, `terminal_bench_2` and `openrouter` with D-193's licences. **Branch artifact:** its payload carries no retired citation or credit. **First refresh:** the candidate over `main`'s artifact passes both publish gates (no degradation, no upward anomaly). **Rollback:** `main`'s code refuses the new artifact (`unattributed evidence source 'arc_agi_2'`), and its hand refresh over it passes the gates. So the runbook's transition and rollback notes are correct (with R1). |
| M1 | Fixed | `calibrate_surface.py --binomial-tasks 120` on the branch artifact reproduces the record: 24 ranked, floor 27.4, stderr 4.392, close_call 8.8, window 9.5. `computer-use` reproduces 21 / 3.3 / 10.0. |
| M2 | Fixed | `..`, `%2e%2e`, `//`, another directory and a sibling repository are all refused after `httpx.URL` normalisation. A non-default port passes, which is harmless: same host, and the fetch has its own host list. |
| M3 | Partly | 6 of the 7 survivors are killed now. The `type == "file"` filter still survives (N2). |
| M4 | Partly | Both causes are named, and the budget crossings reproduce exactly: Opus 5.5 $7.40 to $8.40; GLM-5.1, 5.2 and 5.3 and Qwen2.5 VL 72B leave `low`; Mistral Medium 2505 enters it. The counts do not reproduce (N3). |
| M5 | Fixed | `hy4-preview` is Tencent again. No model or alias in either artifact is newly matched by `hy4`/`hunyuan`. `ModelFamilies.swift` equals the generator's output (`test_model_families`), and neither word is an English word a question would carry. |
| M6 | Fixed | Every setting carries its latest `start_timestamp` date, and the row stores it, for example Opus 4.8 at 2026-05-29. The aggregation itself is untested (N2). |
| K1 | Filed | #266 is open. |
| R1 | Accepted | Unchanged. |

### BLOCKING

None.

### MINOR

- **N1** `scripts/derive_arc_public_eval.py:84,94,102-103` (positional pairing, `_unscorable`), `scripts/derive_arc_public_eval.py:126-128` (`_solutions` reads `commits/main`), `docs/decisions.md:4872-4876`.
  **Problem.** An unmarked attempt is compared with the solution at the same list position, taken
  from today's `ARC-AGI-2`.
  - **Measured.** On 2025-05-15 ARC Prize removed the *first* test pair from five evaluation tasks
    (`4a21e3da`, `abc82100`, `b6f77b65`, `f560132c`, `faa9f03d`; commits `124910ab`…`2c42f4d6`).
    It also edited a task on 2025-04-17.
  - **GPT-4.1's settings ran on 2025-04-14, before both.** In `gpt-4-1-2025-04-14/4a21e3da.json`,
    pair 0 (21×21, the removed test, `metadata.pair_index` 0) is compared with today's only
    solution (20×20, the old test 1). Pair 1, which *is* today's test, is counted "unscorable".
  - **What the record calls them.** The record's `unscorable: 30` are 5 tasks × 2 attempts in each
    of the three GPT-4.1 settings. They are a misalignment, not a missing solution, and
    `_unscorable`'s docstring still says "none is expected". D-194 states the 16,664/16,681
    agreement and is silent on both.
  - **The 17 disagreements are not itemised.** Two of them are in kept settings (Gemini 3 Deep
    Think, GPT-5.1 high), so they cannot be audited.
  **Effect today.** None served. The GPT-4.1 rows are unreconciled: ARC spells `gpt-4-1-…`, and
  the rule is `gpt[-_ ]?4\.1`. Every other unmarked setting ran after 2025-05-15, and pair_index
  equals the position in every file I read. Keeping ARC Prize's mark where it disagrees is right,
  and the comparison is not systematically broken: 0.1 % disagreement, and plausible scores for
  the unmarked settings.
  **Failure scenario.** A registry rule that learns ARC's `gpt-4-1` spelling serves GPT-4.1 at
  "0 % correct". That number was measured against a task set it never ran, with 5 tasks
  misaligned and their denominators from the old pair count. Likewise, a re-derivation after
  ARC-AGI-2 changes again silently re-scores every unmarked setting against the new solutions.
  **Fix.**
  - Pair by `metadata.pair_index`.
  - Leave out an unmarked setting whose latest run predates the last change to `data/evaluation`
    (or one with any unscorable attempt), as `left_out_as_unscorable`. The alternative is to score
    it against the solutions at the commit in force on its run date.
  - Pin the solutions commit as a constant instead of reading `commits/main`.
  - Record each disagreement as (setting, task, pair, mark).
  - Say in D-194 what the 30 are.

- **N2** `tests/unit/test_terminalbench_4.py:172`, `tests/unit/test_arc_agi_2.py:138`, `scripts/derive_arc_public_eval.py:109-115`. Three planted faults survive the wave's tests (and `test_ios_client_contract.py`).
  1. **`entry.get("type") == "file"` replaced by `True`.** The test's directory entry is named
     `nested`, so the `.json` name filter drops it anyway. This is round 1's M3 survivor, claimed
     fixed.
  2. **`task_score` pairing every pair with `expected[0]`.** The two-pair test uses the same grid
     for both solutions.
  3. **`_latest_run` returning `min` instead of `max`.** The record test checks only that each
     date has 10 characters.
  **Failure scenario.** A refactor that reads directories as submissions, or that mis-pairs
  multi-pair tasks (N1's own class of fault), or that dates a setting by its first run, passes CI.
  **Fix.**
  - Name the directory entry `nested.json`.
  - Give the two-pair case two different solution grids, with an answer that matches only the
    second.
  - Add a `_latest_run` test with two dates.

- **N3** `docs/decisions.md:4899-4902` (D-194, "The cost"). The counts do not reproduce on the artifact this branch built (the seat's `advisor.db`, byte-identical to the author's `w-licensed/advisor.db`) against `main`'s served copy.
  - 316 models are priced, not 314.
  - 146 have a non-LiteLLM price, not 142 (`main`: 172, as stated).
  - Blended price medians moved more than 20 % for 43 models, 37 of them up, not 54 and 46. Input
    medians alone give 55 and 47. Either the figures are from a pre-fix build, or they are measured
    on another axis that the ADR does not name.
  - **Already correct:** the lost prices (`minimax-m1`, `gpt-3.5-turbo-0613`), the `:batch`
    count (65 aliases, 62 models), the crossings, and the 21/24 ranked models.
  **Failure scenario.** The ADR's cost line is the owner's record of what the move changed for
  readers, and a reader re-measuring it finds other numbers.
  **Fix.** Re-measure on the committed build and name the axis ("blended").

## K.9 candidates spotted outside this wave's scope

None.

## Risks queued to next M

- **R1** `docs/release-testflight.md:50-55`. Between the first install past D-194 and the first refresh that publishes, the new code over `main`'s artifact answers `abstract` and `computer-use` with nothing. Measured: `fingerprint_of` gives both 0 models, because their primary sources, `arc_agi_2` and `terminalbench_4`, are not in that artifact. The runbook says only that the old artifact "boots … and refreshes".
  - **Normally.** The #258 startup catch-up closes the gap within minutes.
  - **If that first refresh fails.** That is a GitHub or models.dev failure, with nothing to carry.
    The two surfaces then stay dark on the Mac until the next night. The Fly deploy is not
    affected, because it refuses data another release built.
  - **What would show the risk is real.** A startup cycle that records a failure on the install
    day. The runbook should then say the two surfaces are dark until a cycle publishes.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| N1 | Fixed. Pairs are matched by `metadata.pair_index`; the solutions are pinned (`SOLUTIONS_COMMIT`); a setting with an unmarked attempt run before 2025-05-15 is left out (GPT-4.1's three); each disagreement is named. Re-derived: all 16,681 marks agree (the 17 were the positional pairing), none unscorable, no kept score moved. D-194 says so. | `b7993a8` red, `27f9547` fix, this docs commit |
| N2 | Fixed. The directory entry is named `nested.json`; a two-pair task has two solutions matched by pair index; `_latest_run` is tested with two dates. | `b7993a8` |
| N3 | Fixed. D-194's cost counts are measured on the branch's last build: 316 priced, 146 with a second price, 43 moved more than 20 % (37 up), four prices lost. The budget crossings are unchanged. | this docs commit |
| R1 | Stated in the runbook: until the first refresh publishes, `abstract` and `computer-use` say on the Mac that they have no evidence. | this docs commit |
