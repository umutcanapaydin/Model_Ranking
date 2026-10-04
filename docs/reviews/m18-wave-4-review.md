---
record_type: review
id: m18-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W4 Code Review: the engine and data backlog

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `d528fd3..5623f4b`: 10 commits, 30 files, +832 / -433. `d528fd3` is the head of
`wave/m18-w1` (PR #99, unmerged), which this wave is stacked on. Only W4's range is reviewed.
**Risk tier:** HIGH (`docs/plans/m18-wave-4-plan.md:11`; `m18-plan.md:89` says MED, and the wave
plan raises it because the diff touches `src/app/adapter/main.py` and `src/app/clients/**`)
**Model routing (HIGH, advisory):** author-family: claude-opus / reviewer-family: claude-opus (fallback: no second family available)
**Fresh context:** this seat started with none of the authoring context. I read the plans and D-173
first, then the code and the tests. The one-line commit subjects were visible in `git log` from the
start; I read the full commit messages only after the code, when I matched the red commits to their
fixes.

**Summary.** One finding blocks. The refresh now checks its candidate against the serving bounds
(#57), but in production the refresh runs as the engine's child, and the child's allowlisted
environment drops the three bound variables. So the child always judges against the defaults, not
the bounds the engine serves under. I drove it through `NightlyRefresh.run_once`, the production
path, in both directions:
1. If the owner raises a bound, which is what every bound message tells him to do, every night is
   refused. The product freezes.
2. If he lowers one, the night publishes an artifact the next restart refuses.

The fix is a few lines (**B1**). The rest holds up. `/v1` changes no field and no route: 36 of 45
route answers parse to the same JSON as the base, and the other 9 differ only in the order of tied rows.
Every red commit fails on its own tree and passes on its fix. The import boundary holds, the gzip
middleware sits inside the Host check, and the accessibility guard is excused correctly on an expiry
night.

Five findings are MINOR:
1. **M1.** The `/v1/boards` memo can serve a retired artifact; a forced interleaving shows it.
2. **M2.** D-173 overstates two clauses and leaves D-154 un-amended.
3. **M3.** No test would catch the refresh importing the adapter through `serving_bounds`.
4. **M4.** Three of the wave's own acceptance cases are untested.
5. **M5.** Records drift.

**Policy.** The profile (`.claude/agents/Code-Reviewer.md`) and `.agents/rules/practices.md` were
read from `d528fd3`. At that ref the matrix is `permission-matrix.md` at the repository root, and
`docs/permission-matrix.md` does not exist. `git diff --stat d528fd3..5623f4b -- .claude .agents
permission-matrix.md .github Dockerfile fly.toml epb.html or.md AGENTS.md` is empty, and
`docs/decisions.md` only gains lines (0 removed).

**How I worked.**
- **Gate**, at `5623f4b` with the worktree's own `.venv`. `make` was not used, so that `install`
  writes nothing.
  - pytest `-n auto` with `MODEL_RANKING_REQUIRE_ARTIFACT=1`: **1584 passed, 25 skipped**. The 25
    is the owner's-Mac figure `docs/skip-budget.txt:26` now states.
  - ruff and mypy (strict): PASS.
  - `check_records.py`, `wave_check_all.py`, `shell_dialect_check.sh`, `conformance/run-all.py`
    and the module coverage floor: PASS.
  - The Swift legs were not run: the range changes no Swift file.
- **Red first.** I ran each red commit's tests on a `git archive` of its tree in the scratchpad, not
  in a git worktree, with this worktree's venv and `PYTHONPATH=<tree>/src`.
  - `6858d30`: 6 failed. `e4e2695` (the second P1 red; the brief's "bcf..."): 7 failed. Fix
    `293c918`: 56 passed.
  - `35c87e9`: 5 of 6 failed (the 8→7 accessibility case passes by design). Fix `4a47877`: 6 passed.
  - `1d7cfaa`: 2 of 3 failed (the replaced-artifact case passes without a memo). Fix `6c0c242`: 3 passed.
  - `baebf92`: 2 failed. Fix `5623f4b`: 2 passed.
  - The #71 test, 25 runs each: red 0/25, fix 25/25.
- **Probes**, in-process TestClient or plain Python, against copies of the served artifact in the
  scratchpad. Nothing bound a socket.
  - `/v1` at base vs head: 45 route answers.
  - The engine's egress messages under three env overrides, base vs head.
  - The memo under a forced publish.
  - The accessibility guard on an expiry night.
  - The fingerprint across two unchanged nights.
  - An upstream re-spelling against the board guards.
  - The nightly child's bounds, run twice through `NightlyRefresh.run_once`: once with a raised
    bound, once with a lowered one.
- **Mutants: 9**, each applied in place and restored from the original bytes. After each I checked
  `git hash-object` against `HEAD:<file>` and `git diff --quiet`. 7 were killed. 2 survived: the
  import-boundary one (**M3**) and the first-artifact bound skip (**M4**).
- **Contract test, once:** `RUN_CONTRACT_TESTS=1` on `tests/integration/test_epoch_bundle_contract.py`:
  2 passed.
- **Read only:** GitHub issues #39, #42, #44, #57 (and its comments), #76, #77 and #79.
- **Not done, by this seat's rules:**
  - no run of `install_engine_service.sh` or `remove_engine_service.sh`, except inside
    `tests/unit/test_engine_service.py` (scratch HOME, `test_engine_service.py:106`);
  - no `launchctl`, `xcodebuild`, `simctl`, nothing on the simulator, nothing in `~/Library`;
  - no server; no commit, push or GitHub write.
- **Tree.** Clean apart from this file. The probe scripts and extracted trees are in the scratchpad
  (`cr4-*`).

## Verdict
BLOCKING

**One BLOCKING, five MINOR.** **B1** must be fixed before the wave closes; a new Code-Reviewer then
reads the new range. I recommend fixing M1 to M4 in the same round: each is a few lines, and the
round is owed anyway.
- **B1.** The refresh child never sees the engine's bound overrides. A raised bound freezes every
  night, and a lowered one publishes past the engine.
- **M1.** The `/v1/boards` memo stats the artifact after opening it, so a publish in between files
  the retired payload under the new artifact's key.
- **M2.** D-173 against the ADRs it amends:
  - clause 1's "fingerprint moves that night" is not what happens;
  - clause 2 covers only the surfaces' rosters;
  - clause 7 removes D-154 clause 4's script without amending D-154;
  - no amended ADR carries a note.
- **M3.** REQ-REF-007's test is one level deep. A `serving_bounds` import of the adapter survives the
  suite.
- **M4.** Untested: the standings bound and the metric refusal at refresh, the first-artifact bound,
  and the accessibility guard on an expiry night.
- **M5.** Records:
  - none of W4's four REQ-IDs is cited by a test;
  - a stale test docstring;
  - a history line in a live README.

**K.9:** K1 (the subscription engine still ties by plan name), K2 (picks are compared by display
name), K3 (the coverage register cites deleted files).
**Risks:** R1 (`run.reports` keeps the pre-reconcile count), R2 (the #71 red rests on a sleep), R3
(`-latest-v2` derives nothing).

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `src/app/adapter/nightly.py:83-89`, `:258`; `src/app/workflows/serving_bounds.py:6-8`, `:44-58`; `src/app/workflows/refresh.py:893-895`; `docs/decisions.md:3416-3418`. **The refresh's bound check reads defaults in production, never the engine's bounds.**

  The refresh checks the candidate with `egress_problems(candidate, bounds_from_env())`
  (`refresh.py:893`). `bounds_from_env` reads three variables (`serving_bounds.py:55-57`). The
  scheduled refresh runs only as the engine's child (D-154, REQ-REF-008). Its environment is
  `{name: os.environ[name] for name in CHILD_ENV}` (`nightly.py:258`), and `CHILD_ENV`
  (`nightly.py:87-89`) does not name `MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS`,
  `MODEL_RANKING_MAX_PUBLISHED_STANDINGS_ROWS` or `MODEL_RANKING_MAX_RANKED_ROWS`. Its comment still
  says "The refresh reads no environment variable of its own" (`:83`). So the child always sees
  500 / 25,000 / 5,000, whatever the engine serves under.

  Measured through `NightlyRefresh.run_once` (the production path, a real child process with the
  allowlisted environment; `cr4-probe-childenv*.py`). The builder writes a prepared candidate (a
  copy of the served artifact, or the `_wide` test fixture), so nothing is fetched.
  1. **Raised bound.** The engine's `MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS=1000`, and the engine
     would serve the 501-row candidate (`egress_problems` empty). The child printed
     `ServingBounds(answer_rows=500, …)` and exited 3, two nights running: "refused: the candidate
     is past a bound the engine serves under — … 501 ranking rows … refuses past 500". The engine
     serves under 1000. The message tells the owner to raise the variable he has already raised.
     This is the freeze D-128 names as the failure to fear, and it is a regression: at `d528fd3` the
     refresh checked no bound (`git show d528fd3:src/app/workflows/refresh.py | grep -c egress` → 0),
     so this configuration published.
  2. **Lowered bound.** The engine's `MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS=10`, and the engine
     would refuse the candidate at boot. The child saw 500 and exited 0 (published). Afterwards the
     served artifact is past the engine's bound. The next restart refuses it: #57's I-5 restart loop,
     which D-173 clause 4 exists to prevent.

  The wave's own words state the opposite. `serving_bounds.py:6-8`: "so the two cannot disagree:
  both read `bounds_from_env`". D-173 clause 4 says the startup check's bounds run on the candidate.
  `test_refresh.py:1734-1748` cannot see this, because it calls `refresh()` in-process after
  `monkeypatch.setenv`, sharing the parent's environment. The practice it breaks is L.9, config
  reaches the process (`.agents/rules/practices.md`, "What is running is not what you built").

  **Why BLOCKING.**
  1. It is a control whose fail direction is wrong both ways (permission matrix §11): it fails open
     when a bound is lowered and closed, nightly, when one is raised.
  2. #57's criterion, "the refresh runs the same bound checks", is unmet on the only path that runs
     it.
  3. Nothing is wrong today, because no override is set anywhere (`git grep MODEL_RANKING_MAX --
     scripts deploy ios/app.sh` is empty). But the first time the owner follows a bound's own
     advice, the product freezes.

  **The fix.**
  1. `serving_bounds` names its variables once (for example a `BOUND_VARS` tuple that
     `bounds_from_env` reads).
  2. `nightly.CHILD_ENV` includes them. The adapter may import a workflow; the reverse stays
     forbidden.
  3. Correct the comment at `nightly.py:83`.
  4. Add a red-first test through the child. For example, drive `run_once` with an override set and
     a command that prints `bounds_from_env()`, or assert that `CHILD_ENV` contains every name
     `bounds_from_env` reads, derived rather than listed.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/adapter/main.py:1408-1422`. **The `/v1/boards` memo can file a retired artifact's payload under the new artifact's key.**

  The route opens the artifact (`:1408`) and only then stats it for the key (`:1411`). The refresh
  publishes by `os.replace`. A publish that lands between the two leaves the connection reading the
  old inode while the key names the new file. The old payload is then stored under the new key
  (`:1421`) and served for the new artifact's whole life, until the next publish or restart. The
  comment above the memo (`:1389-1391`) names exactly the failure the key exists to prevent.
  `_database_unusable` does it in the safe order: stat first (`:349`), then probe.

  Forced interleaving (`cr4-probe-memo.py`): `open_readonly` is wrapped to publish once, right after
  it opens. The second request, on the new file, returned the retired payload (`2nd == retired
  payload: True`). The board the new artifact dropped (`arena_text_non_english`) was still served.
  The window is two syscalls, at most one publish a night, and one phone that fetches daily, so it is
  rare. It is still the D-129 shape this module's comments keep paying for.

  A second, smaller race in the same lines: `key in _BOARDS_MEMO` (`:1412`) and `_BOARDS_MEMO[key]`
  (`:1414`) are two steps, and another worker's `clear()` (`:1420`) between them raises `KeyError`,
  which becomes a 500.

  **The fix:**
  1. Compute the key before `open_readonly`, or re-stat after building and store only when the key
     is unchanged.
  2. Read with `.get(key)`.
  3. A test like `test_a_replaced_artifact_is_built_again` with the publish forced between open and
     stat.

- **M2** `docs/decisions.md:3399`, `:3405-3412`, `:3428-3431`, `:3434`; `:2383`; `:2418`. **D-173 does not yet match the ADRs it amends.**

  1. **Clause 1, "D-164's fingerprint moves with it that night" (`:3408`).** Both sides are
     fingerprinted by the running code every cycle (`refresh.py:1075`, `:1148`), so a tie-order change
     never reads as a change. On the served artifact the digest is `9c71af2a…` at base and `eb8e816f…`
     at head. Two head cycles over identical content both exited 1, unchanged. The served order of
     tied rows changes when the engine restarts on the new release, not on a night, and no publish
     follows. The sentence should say that.
  2. **Clause 2, "The night-to-night roster guards compare model ids" (`:3409`), and the mitigation
     "If a guard compares names again, a cosmetic re-spelling can refuse a night" (`:3434`).** Only
     `ServingSummary.models`, each surface's ranked roster, moved to ids (`refresh.py:492`). The
     guards on each surface's own board (D-159, `refresh.py:219`, `:288`) and on every declared board
     (D-164 clause 2, `:227`, `:293`) still compare raw names.

     Probe (`cr4-respell`): I re-spelled the raw names on `coding`'s board, keeping every model id.
     The ranked ids were equal and there were no display changes, yet the night was refused both
     ways: "coding's board would lose 77 of 173 names", and "would be 77 of 173 names this artifact
     has never seen". That is D-164 clause 2 by design, and the guard's own message says a renamed
     set "is published by hand" (`refresh.py:221-222`). But D-173 reads as if a cosmetic re-spelling
     can no longer refuse a night. Say that clause 2 covers the surfaces' ranked rosters and that the board guards keep raw names
     (D-164), or file the extension.
  3. **Clause 7 removes `scripts/retire_refresh.sh`, the script D-154 clause 4 names (`:2383`).** D-173's
     header lists D-128, D-132, D-164 and D-167 (`:3399`), not D-154. The fact that makes removal
     safe, that the owner's Mac has no such job (measured), appears only in commit `5623f4b`'s
     message. A record should carry it.
  4. **No amended ADR carries a note.** The project appends one to the ADR it amends: D-154's
     "*Amended 2026-09-29 … D-170*" (`:2418`). D-128, D-132, D-164, D-167 and D-154 get none, so a
     reader of D-164 clause 2 or D-154 clause 4 finds a rule that no longer holds as written.

- **M3** `tests/unit/test_refresh.py:293-312`. **REQ-REF-007's guard reads only `refresh.py`'s own imports.**

  The test parses `src/app/workflows/refresh.py` with `ast` and checks its direct imports. This wave
  put a new module on the refresh's import path, `serving_bounds`, whose docstring cites REQ-REF-007
  (`serving_bounds.py:10-11`). Today the boundary holds transitively: a fresh interpreter that imports
  `app.workflows.refresh` and `app.workflows.serving_bounds` loads no `app.adapter` module and no
  `fastapi`.

  The mutant `from app.adapter import nightly` added to `serving_bounds.py` loads `app.adapter` into
  the refresh, and it **survived the full suite** (1584 passed). `test_nightly_refresh.py:353` checks
  the other direction.

  **The fix:** a subprocess test that imports `app.workflows.refresh` and asserts no `app.adapter*`
  key in `sys.modules`.

- **M4** `tests/unit/test_refresh.py:1734-1748`; `src/app/workflows/refresh.py:891-893`; `docs/plans/m18-wave-4-plan.md:58`. **Three of the wave's own acceptance cases have no test.**

  1. **P2's check is named for the standings bound.** The plan reads: "A candidate past
     `MAX_PUBLISHED_STANDINGS_ROWS` is refused with the bound named". The test drives
     `MAX_PUBLISHED_RANKING_ROWS` instead. No test drives the standings leg, or #57's "worse than
     filed" half (a metric `/v1/boards` refuses, through `standings_problem`'s `ValueError` branch),
     through the refresh. Both share `egress_problems` with the boot check, which the boot tests
     cover.
  2. **"On a first artifact too" (`refresh.py:891-892`) is unpinned.** The mutant that skips the
     check when `live is None` survived the full suite.
  3. **The accessibility guard on an expiry night has no test.** It is correct: `_served_without`
     drops `access` with the expired source, so the baseline counts 0. Measured on the served
     artifact: live 225, baseline 0, candidate 0. `_reason_to_refuse` returns None with the baseline
     and refuses without it. But only the baseline's digest is pinned
     (`test_refresh_carry.py:449`).

- **M5** `tests/unit/test_pareto_dominance.py:191-193`; `scripts/README.md:37-38`; `docs/plans/m18-plan.md:33`. **Records drift.**

  1. **None of the four REQ-IDs `m18-plan.md:33` scopes to W4** (REQ-ING-004, REQ-REF-009,
     REQ-CAN-001, REQ-API-001) is cited by the wave's tests (seed E.2). They cite D-173 and issue
     numbers. The only REQ citations are REQ-CAN-005 (`test_build.py:499`) and REQ-CI-001 (the
     contract test). The natural homes:
     1. REQ-CAN-001 → `test_moving_aliases.py:93`;
     2. REQ-API-001 → `test_board_standings.py:274`;
     3. REQ-REF-009 → M4's expiry-night test.
  2. **A stale docstring.** It still justifies the frontier's key by agreement with
     `min(value_pool, key=(blended_per_m, model))`, which this wave replaced with `first_cheapest`.
  3. **A history line in a live document.** `scripts/README.md:37-38` says the refresher "were
     removed at M18-W4". The practice is that READMEs describe what is, not how it got there. "The
     engine service runs the nightly refresh; there is no separate launchd refresher" says the same
     thing as a fact.

### PASS (what looks good)

- **`/v1` is unchanged except in encoding and tie order.**
  - Base vs head on the served artifact, 45 route answers (categories, budgets, boards, and every
    task × budget): 36 parse to equal JSON. The other 9 are `abstract`, `expert` and `mathematics`
    at each budget, where models tie, and their lists hold the same rows in a different order.
  - Every pick names the same model.
  - `RankingRow` and `serialize.py` are untouched. The id travels beside the row
    (`rank.py:279-361`), not in it.
  - `/health`'s keys are unchanged.
- **The engine boots with the same bounds and the same words.** With all three overrides set, the
  values and `_egress_problems`' three messages are identical at base and head, and so are the
  defaults (500 / 25,000 / 5,000). `main.py` keeps the module constants and thin wrappers, so the
  existing monkeypatching tests still bind.
- **The gzip middleware is in the right place.**
  - The user middleware runs `_no_sniff` → `_known_host` → `GZipMiddleware`, outermost first, so a
    foreign Host is refused (400, `nosniff`, not compressed) before compression runs.
  - Each compressed answer keeps `nosniff`, and its decoded body equals the identity body.
  - `/v1/boards` is 513,532 bytes raw and 38,311 bytes on the wire (7.5%; D-173 says "about a
    tenth").
  - Answers of 1 KB or more now carry `Vary: Accept-Encoding` in both modes. That is correct
    HTTP, and the only header a non-gzip client sees change.
  - The phone checks its 4 MB ceiling after URLSession decompresses (`Models.swift:400`).
- **The memo's key and bound are otherwise right.**
  - Its key is `_artifact_key` (inode, ctime, mode).
  - A refusal is never stored.
  - The open still runs first, so a vanished or `chmod 000` artifact answers 503 before any hit.
  - A payload holds 2.3 MB on the served artifact, so three entries is about 7 MB today and about
    24 MB at the 25,000-position bound.
- **#71 is right, and its test is deterministic on the fix.** `timed_out` is read before the close
  (`protocols.py:132`).
  - A worker that finishes inside the deadline is joined, and its answer is returned.
  - One that finishes between the join and the check is treated as finished, as before.
  - One still alive is "late", whatever it records after the close.
  - The test's worker blocks on `closed.wait(5)` until `close()`, so `is_alive()` is True when the
    fix asks.
- **#45 counts the right rows.**
  - The rowids are taken before reconcile and compared after it. Reconcile only `UPDATE`s scores
    (`registry.py:599`, `:603`), so the rowids hold.
  - `UPDATE OR IGNORE` leaves a conflicting row unspecified, and it stays counted.
  - A carried source has no report, so its resolved rows discount nothing.
- **#48's token rule is tight.** `-latest` followed by `-` or the end refuses derivation. A date
  joined by the normaliser (`latest20250326`, `latest2025-03-26`) still derives. A curated rule still
  wins (D-166 clause 2).
- **The fingerprint moves once and stays put.** It is stable across two reads on head. `ORDER BY
  b.best DESC, m.id` is a total order, because `id` is the primary key. No new digest input varies
  by night: `displays` and `accessible` are not hashed, and the accessibility values already were.
- **The refresh imports nothing from the adapter, transitively** (but see M3).
- **The accessibility guard** uses D-128's quarter with D-128's `<=` boundary. The mutant to `<`
  is killed (8→6). It runs against the D-156 baseline, so an expiry is excused exactly.
- **#76 is clean in the live documents.** No live instruction tells anyone to install or run the
  removed scripts: README, AGENTS.md, architecture, the owner's page and the roadmap.
  - `scripts/README.md` now lists the service scripts.
  - The PRD's REQ-REF-005 row no longer points at a removed script.
  - What remains is history (closure reports, handovers, the ledger), the dated coverage register
    (**K3**) and D-154's body (**M2**(3)).
- **#79** follows the existing contract-test shape, is skipped without `RUN_CONTRACT_TESTS=1`, and
  passed live once here. The skip budget moves 73 → 75, matching the observed 25 on this Mac.
- **Discipline.**
  - Every fix was red first (verified above).
  - No fix changed an assertion to make itself pass. Three edits to tests are worth a line in the
    close record:
    1. the red `e4e2695` reverses one existing assertion (`test_pareto_dominance.py:201`, name order
       to ranking order), as D-173 clause 1 decides;
    2. `4a47877` moves the default's source pin to `serving_bounds` with the constant;
    3. `5623f4b` narrows the #76 red test to non-`.md` files, because the new README must name the
       label.
  - No drive-by edits: every file maps to a phase, P0 to P4.
  - Duplication went down: the bounds now have one definition.
  - No new `noqa`, `type: ignore` or hard-coded path.
  - All 10 commits carry `GP-Agent:` / `GP-Task:` and no AI attribution.
  - The plan amendment moves #74 and #56 to W2 (`m18-plan.md:200-202`).

## Producers of hardened invariant(s)

Producers of hardened invariant(s), from the code, with the citing test for each producer and the
gaps:

| producer | invariant | citing test | gap |
|---|---|---|---|
| `rank.py:332` (`ORDER BY b.best DESC, m.id`) | a tie's order never follows a spelling (#44) | `test_rank.py:262` | none |
| `recommend.py:320-323` (`first_cheapest`), `:507`, `:511`; `:331-334` (frontier key) | the picks and the frontier keep the ranking's order (#44) | `test_pareto_dominance.py:181`, `:204` | the subscription engine (**K1**) |
| `standings.py:108` (boards by `r.model`, the id; unchanged) | board positions by id (#44, D-167) | existing `test_board_standings.py` | none |
| `refresh.py:492-493`, `:251-258`, `:1162`, `:764` | the surface rosters compare ids; a re-spelling is recorded (#39) | `test_refresh.py:1667`, `:1682` | board guards keep raw names (**M2**(2)) |
| `refresh.py:296-304`, `:511-523` | accessibility loses no more than a quarter (#42) | `test_refresh.py:1718` | expiry night (**M4**(3)) |
| `serving_bounds.py:44-58`, `:139-165`; `refresh.py:891-895` | the candidate is checked against the engine's bounds (#57) | `test_refresh.py:1734`; `test_board_standings.py:527` | the child's environment (**B1**); standings and metric legs, first artifact (**M4**(1), (2)) |
| `main.py:208-233`, `:464-470` | the engine boots on the same bounds and messages | `test_board_standings.py:298`, `:320`, `:435`, `:527` | none |
| `main.py:1389-1422` (memo) | `/v1/boards` is built once per artifact (#55) | `test_board_standings.py:237`, `:251` | publish between open and stat (**M1**) |
| `main.py:666` (gzip) | encoding only, security headers kept (#55) | `test_board_standings.py:274` | none |
| `build.py:167-192`, `:750-752` | unknown efforts counted after reconcile (#45) | `test_build.py:498`, `:516` | `run.reports` (**R1**) |
| `registry.py:446`, `:474` | a `-latest` token derives no model (#48) | `test_moving_aliases.py:93`, `:100` | `-latest-v2` (**R3**) |
| `protocols.py:129-137` | late is decided at the deadline (#71) | `test_fetch_bounds.py:310` | none |
| removal of the four scripts and the plist | nothing installs the retired refresher (#76) | `test_engine_service.py:509` | none |
| `refresh.py:41-52` imports, `serving_bounds.py:22-25` | the refresh imports nothing from `app.adapter` (REQ-REF-007) | `test_refresh.py:293` | one level only (**M3**) |

## Acceptance criteria evidence

The W4 criterion is "Every engine and data bug the waves filed is fixed red-first or ruled"
(`m18-plan.md:33`). Here it is per issue:
- **#44** → `rank.py:332`, `recommend.py:320-334`, `:507`, `:511` → `test_rank.py:262`,
  `test_pareto_dominance.py:181`, `:204`. Red: `6858d30` and `e4e2695`; fix: `293c918`.
- **#45** → `build.py:167-192`, `:750-752` → `test_build.py:498` (cites REQ-CAN-005), `:516`.
  Red: `6858d30`; fix: `293c918`.
- **#48** → `registry.py:446`, `:474` → `test_moving_aliases.py:93`, `:100`. Red: `6858d30`; fix:
  `293c918`.
- **#39** → `rank.py:279-361`, `refresh.py:251-258`, `:492-493`, `:764`, `:1162` →
  `test_refresh.py:1667`, `:1682`. Red: `35c87e9`; fix: `4a47877`.
- **#42** → `refresh.py:296-304` → `test_refresh.py:1718`. Red: `35c87e9`; fix: `4a47877`.
- **#57** → `serving_bounds.py`, `refresh.py:891-895`, `main.py:464-470` → `test_refresh.py:1734`.
  Red: `35c87e9`; fix: `4a47877`. **Unmet in production (B1)**; gaps in M4.
- **#55** → `main.py:666`, `:1389-1422` → `test_board_standings.py:237`, `:251`, `:274`. Red:
  `1d7cfaa`; fix: `6c0c242`. Race in M1.
- **#77** → ruled by D-173 clause 6 (`decisions.md:3424-3427`). There is no code; D-167 clause 1
  stands. The measured payload agrees (38,311 bytes on the wire).
- **#71** → `protocols.py:129-137` → `test_fetch_bounds.py:310`. Red: `baebf92`; fix: `5623f4b`;
  25/25 each way.
- **#79** → `tests/integration/test_epoch_bundle_contract.py:30`, `:52`;
  `docs/skip-budget.txt:19-28`. It passed live once with `RUN_CONTRACT_TESTS=1`.
- **#76** → the deletions; `scripts/README.md:27-38`; `docs/prd.md:409` →
  `test_engine_service.py:509`. Red: `baebf92`; fix: `5623f4b`.
- **#74, #56** → moved to W2 by the plan amendment (`m18-plan.md:200-202`). They are not owed here.

The scoped REQ-IDs. No test cites them (**M5**(1)), so the evidence is by issue:
- **REQ-CAN-001** → #48: `test_moving_aliases.py:93`.
- **REQ-CAN-005** (the issue's own) → #45: `test_build.py:498`.
- **REQ-API-001** → `/v1` unchanged (the 45-answer probe) and `test_board_standings.py:274`.
- **REQ-REF-009** → the expiry baseline excuses the accessibility guard: probe only (**M4**(3)).
- **REQ-ING-004** → nothing in this wave changes provenance. The contract tests at
  `test_epoch_bundle_contract.py:30`, `:52` are the nearest.

## The trace from D-173, clause by clause

- **Clause 1** (ties by id; picks by the ranking's order) → `test_rank.py:262`,
  `test_pareto_dominance.py:181`, `:204`. The fingerprint sentence is inaccurate (**M2**(1)).
  Coherent with D-167 clause 3, which already breaks the phone's ties by id.
- **Clause 2** (roster guards by id) → `test_refresh.py:1667`, `:1682`. It covers D-128's and D-132's
  surface rosters. D-159's and D-164's board guards keep raw names (**M2**(2)).
- **Clause 3** (accessibility loss guard) → `test_refresh.py:1718`. It uses D-128's quarter and
  boundary, and is coherent with D-156 through `_served_without` (probe). The expiry night has no
  test (**M4**(3)).
- **Clause 4** (bounds at refresh) → `test_refresh.py:1734`. **Not true on the production path
  (B1).**
- **Clause 5** (memo, gzip, no ETag) → `test_board_standings.py:237`, `:251`, `:274`. Memo race in
  **M1**.
- **Clause 6** (unselectable boards stay) → a ruling with no code. It is coherent with D-167 clause 1
  ("every board with at least one rankable model").
- **Clause 7** (retired installer removed) → `test_engine_service.py:509`. It is coherent with D-170
  and D-154 in substance, but D-154 clause 4 is left naming a removed script (**M2**(3)).

## K.8 contract drift check

`git grep -n` at `5623f4b`, for the plan's symbols (`m18-wave-4-plan.md:62-70`) and the new ones:
```
src/app/adapter/main.py:464:def _egress_problems(db: Path) -> list[str]:
src/app/adapter/main.py:666:app.add_middleware(GZipMiddleware, minimum_size=1024)
src/app/adapter/main.py:1392:_BOARDS_MEMO: dict[tuple[str | int, ...], dict[str, Any]] = {}
src/app/adapter/main.py:1396:def boards() -> Any:
src/app/clients/protocols.py:129:    worker.join(total)
src/app/clients/protocols.py:132:    timed_out = worker.is_alive()
src/app/workflows/build.py:167:def _unconfirmed_suffix_rows(conn: sqlite3.Connection) -> dict[int, str]:
src/app/workflows/build.py:179:def _discount_resolved_efforts(
src/app/workflows/rank.py:270:def category_ranking(conn: sqlite3.Connection, spec: CategorySpec) -> list[RankingRow]:
src/app/workflows/rank.py:279:def ranked_with_ids(conn: sqlite3.Connection, spec: CategorySpec) -> list[tuple[str, RankingRow]]:
src/app/workflows/rank.py:332:        ORDER BY b.best DESC, m.id  -- #44 (D-173): a tie is ordered by id, never by a spelling
src/app/workflows/recommend.py:320:def first_cheapest(rows: list[RankingRow]) -> RankingRow:
src/app/workflows/refresh.py:251:def display_changes(live: ServingSummary, candidate: ServingSummary) -> list[str]:
src/app/workflows/refresh.py:399:    models: dict[str, frozenset[str]]
src/app/workflows/registry.py:446:_LATEST_TOKEN = re.compile(re.escape(_LATEST_SUFFIX) + r"(?:-|\Z)")
src/app/workflows/serving_bounds.py:44:def bounds_from_env() -> ServingBounds:
src/app/workflows/serving_bounds.py:139:def egress_problems(db: Path, bounds: ServingBounds) -> list[str]:
```
- `ORDER BY b.best DESC, m.display` became `m.id`, as decision 1 says.
- `ServingSummary.models` keeps its name and type. Its meaning changes from names to ids, and its only
  reader is `upward_anomalies` (`refresh.py:212`).
- `_egress_problems(db)` and `boards()` keep their signatures.
- `category_ranking` keeps its signature and return type, now a wrapper over `ranked_with_ids`.
- `/v1` adds no field and no route. Compression is negotiated, and tie order changes as decided.
- The environment variable names are unchanged. Their reach into the nightly child is **B1**.

**Verdict: OK** for symbol drift. B1 is a behaviour finding, not a renamed contract.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/subscribe.py:290`, `:437`, `:442`; `tests/unit/test_pareto_dominance.py:213`. **The subscription engine still breaks ties by plan name, #44's class.** `_pareto` sorts by `(-score, monthly_usd, plan)`, and the value and cheapest picks use `(monthly_usd, plan)`. `test_the_subscription_frontier_orders_the_same_way` now pins the opposite rule to the model frontier test at `:181`, so its name is false. Plans are curated, so a rename needs a commit, which makes this lower risk than #44. Enhancement.
- **K2** `src/app/workflows/recommend.py:561`, `:568`, `:585`, `:596`; `src/app/workflows/schema.py:25-29`. **Whether a pick is the quality pick is decided by display name** (`value.model == quality.model`). The schema does not make `models.display` unique. Two ids sharing a display would suppress the value or cheapest trade-off sentence. None share one in the served artifact today (queried). Bug, latent.
- **K3** `docs/coverage-by-req.md:64`, `:131`, `:174`. **The coverage register cites files and a test this wave deleted** as evidence for REQ-REF-005, REQ-RUN-002 and REQ-ING-010: the plist, `refresh_job.sh`, `enable_refresh.sh`, `install_refresh_wrapper.sh` and `test_refresh_job_install.py`. Row 64 still calls the plist "one owner command from live". The register is pinned to an M9 tree, but nothing marks the rows as historical. Docs.

## Risks queued to next M

- **R1** `src/app/workflows/build.py:752`, `:470-473`. **`run.reports` keeps the pre-reconcile `effort_unknown`.** `report.sources` is replaced with discounted copies. The `SourceReport` objects appended to `run.reports` at ingest are not, so the two lists now disagree. Nothing reads `run.reports` today (`git grep "\.reports\b" -- src` shows writes only), and `build.py:470-472` already names this class. What would show it: anything that starts reading `run.reports`' counts.
- **R2** `tests/unit/test_fetch_bounds.py:297`, `:307`. **The #71 red rests on a 50 ms sleep.** The fix's green is deterministic. But the test fails on the old code only if the worker exits during `close()`'s sleep. Under heavy load it could pass on the old code (0/25 here). What would show it: re-running the red on a loaded machine.
- **R3** `src/app/workflows/registry.py:446`. **A `v`-prefixed version after `-latest-` derives nothing** (`gpt-5-latest-v2` → None, while `gpt-5-latest-2` and `foo-latest.1` derive). Yet `test_moving_aliases.py:101` says "A date or version after the alias names one release". Unmeasured whether any upstream spells one. What would show it: a `-latest-v…` name in the build's unmatched list.
