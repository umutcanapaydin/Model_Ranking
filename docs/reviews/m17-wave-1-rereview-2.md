---
record_type: review
id: m17-wave-1-rereview-2
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M17-W1 second fix round -- independent re-review (commits ea883a3..1976ed3)

**Seat:** independent (Code-Reviewer + Tester combined). I wrote none of this round, none of the
round before it and none of the wave.

**Scope:** `git log 9cf2b0d..HEAD` on `enhancement/m17-w1-fixes`, HEAD `1976ed3`, base `main` =
`e66a2b3`. Four commits:
- `ea883a3` adds mutant-killer tests for MINOR-R1, R2 and R3, and fixes NIT-R2, NIT-1, NIT-3 and
  BLOCKING-R1.
- `222feea` adds the red tests for the owner's board guard.
- `cf0941a` adds the guard, the D-159 "Owner ruling" amendment and ledger rows W-132 and W-133.
- `1976ed3` commits the previous re-review (`docs/reviews/m17-wave-1-rereview.md`).

**What I read it against:** the previous re-review's findings; D-132, D-156, D-157, D-158 and D-159
with all amendments (`docs/decisions.md:1287-1328`, `:2517-2751`); REQ-GRD-001 (`docs/prd.md:424`);
the ledger template's C2b rule (`git show main:docs/warnings.ledger.template.md`).

**Policy:**
- Read only from `git show main:subagent-profiles/Code-Reviewer.md` and `.../Tester.md`.
- `git diff --stat 9cf2b0d..HEAD -- subagent-profiles AGENTS.md .agents .claude permission-matrix.md
  docs/security-baseline.md .path-refs-allow .github` is empty.
- Nothing in the diff addresses a reviewer, so there is no injection-class finding.

**Families:** the commits carry `GP-Agent: claude-code/local-lane`, and this seat is also Claude. No
second family was available, so this is the fallback. My context was fresh: I did not see the
author's session.

**How I worked:**
- **The copy.** I used an existing clean clone at HEAD `1976ed3` with local `main` = `e66a2b3`. It
  holds only tracked files. My scratch files lived in a separate seat directory outside the clone.
- **The artifact.** I copied the owner's `advisor.db` (md5 `214139e9...`) and
  `advisor.db.refresh.json` (`d729a3f6...`) into the clone with `cp`. Both md5s in the owner's
  repository were unchanged at the end. All simulations below ran on further copies of that copy.
  The clone's copy was also unchanged at the end.
- **The venv.** I built a fresh one in the clone (`make install`). `app.workflows.refresh.__file__`
  resolves inside the clone.
- **The red commit.** I replayed `222feea` from a `git archive` export, with `PYTHONPATH` pointing at
  the export's `src` (checked: `app.__file__` resolved in the export).
- **No state changes.** I made no git state change and no commit. After every step,
  `git status --short` in the clone was empty. The only file I leave in the clone is this one.

**Snapshot.** For every file I mutated, the md5 equals `git show HEAD:<file>` at the start and after
every mutant:

| File | md5 |
|---|---|
| `refresh.py` | `1921ddd1` |
| `floors.py` | `b469894b` |
| `recommend.py` | `059ca5c1` |
| `Language.swift` | `47919093` |

## Verdict

**PASS WITH FINDINGS: 0 BLOCKING, 1 MAJOR, 3 MINOR, 4 NIT.**

**Every fix this round claims closes its finding, with evidence** (see the disposition table):
- **BLOCKING-R1.** The merge gate is green on a clean checkout.
- **The fingerprint.** It now pins every surface's floor to its published precision.
- **The no-floor fact.** Its shape is pinned on the engine side.
- **The reason codes.** The engine's codes are tied to the app's `PickReason`.
- **The stale inventory.** `test_why_facts` passes on an artifact whose own board is empty.

**The owner's board guard.** It does what the ruling's words say:
- It refuses a flood.
- It lets a returning board through.
- It shares one helper with D-132 without changing D-132's message.
- `222feea` is red for exactly the stated reason.

**It has one design gap that the owner should see before merge (MAJOR-1).** The guard watches only
growth.
- **The shrink is unguarded.** A board can shrink with nothing watching. On the owner's artifact,
  that moves `coding`'s floor further than the flood that prompted the ruling.
- **The recovery is refused.** When the upstream restores the board, the guard refuses it, and it
  keeps refusing every night after that.
- **The message is false.** The refusal says those names were "never seen", but the artifact served
  them two nights earlier.

**The guard is a per-night rate limit, not a bound on the floor** (MINOR-1). Its quarter is not
pinned by any test (MINOR-2). It was adopted without the measurement of ordinary movement that
D-132's own method puts first (MINOR-3).

## Disposition of the previous re-review's findings

| Finding | Status | Evidence |
|---|---|---|
| **BLOCKING-R1** (records leg red on a clean checkout) | **CLOSED** | `docs/reviews/m17-wave-1-review.md:53`, `:453`, `:472` reworded. `git grep` over HEAD for the two file names returns nothing. `make check-fast` records leg: "test-documented-paths PASS: 3732 path reference(s) ... 0 dangling"; `make check`: the same, "conformance PASS: 14 test(s) ... 0 failing" |
| **OWNER-R1** (the D-159 correction without the owner) | **RULED and implemented** | `docs/decisions.md:2739-2751` records the ruling. The guard is at `refresh.py:145-167` and `:197-200`, `floors.py:42-49`. Residuals: MAJOR-1, MINOR-1, MINOR-3 |
| **MINOR-R1** (per-surface coverage and precision of the fingerprint) | **CLOSED** | `test_floor_served.py:164`, parametrized over all 14 surfaces with a 50.2 to 50.3 move. Mutant R4 (whole points) is RED on 14; R5 (only `coding`) is RED on 13 |
| **MINOR-R2** (the fact's shape; no contract test) | **CLOSED** | `test_floor_served.py:150` requires the exact dict (E3 and E5 are RED). `test_ios_client_contract.py:998` reads both vocabularies: C1 (Swift raw value renamed) and C2 (an engine code renamed) are both RED |
| **MINOR-R3** (stale `test_why_facts` inventory) | **CLOSED** | `test_why_facts.py:27-28`, `:107`. I re-ran the previous seat's failing case, a copy of the owner's artifact with `coding`'s 173 own-board rows deleted, swapped in and restored by md5: **34 passed** (it was 4 failed) |
| **MINOR-R4** (CAT-10 artifact-only) | **ESCALATED as W-132**, legitimately (see NIT-1) | `docs/warnings.ledger.md:178`. V3C-02 has exactly two prior ACCEPTED rows (W-043, W-048; W-111 is FIXED), so a third acceptance would fire C2b. The template's answer at three is "review the control", which is the owner's call |
| **MINOR-R5** (PR evidence overstated) | **Not verifiable by this seat** | It concerns PR #12's description. The clone's origin is the owner's local repository, which I may not touch |
| **MINOR-R6** (the MINOR-5 question recorded only in the PR) | **CLOSED as W-133** | `docs/warnings.ledger.md:179`. For its status word, see NIT-1 |
| **NIT-R1** (W-128 "independent") | **OPEN** | The W-128 row is unchanged in this range. Cosmetic |
| **NIT-R2** (cycle test precondition) | **CLOSED** | `test_floor_served.py:222-247` asserts that neither `surfaces` nor `models` moved and that the floor rose |
| NIT-1 (`survey_boards.floors` docstring) | **CLOSED** | `scripts/survey_boards.py:178-179` |
| NIT-3 (read-write handle on the artifact) | **CLOSED** | `tests/unit/test_categories.py:331` opens `mode=ro` |

## MAJOR

### MAJOR-1 -- the board guard watches only growth, so a board that shrank unguarded is refused when it comes back, every night

**Where:**
- `src/app/workflows/refresh.py:197-200` applies `_mostly_new` to `board`, which only counts names
  ADDED.
- `refresh.py:153-154` skips an emptied board as "`degradations`' business". For a board that is not
  true: `degradations` (`refresh.py:220-252`) reads ranked counts and budget counts, never a board.
- Nothing refuses a board that loses rows while the ranked rows stay. `swebench`'s `minimum_rows` is
  1 (`src/app/workflows/sources.py:144`).

**Scenario, measured on a copy of the owner's artifact.** The SWE-bench upstream stops listing its
older entries (every `run_date` before 2025-06-01: 85 rows, all unpriced, so no ranked row moves).
- **Night 1, board 173 to 88 names:**
  - ranked `coding` stays 44 to 44;
  - `degradations` = `[]` and `upward_anomalies` = `[]`;
  - the floor moves **65.4 to 71.4**;
  - it **publishes**. That is a bigger floor move than the 60-row flood (65.4 to 71.3) that the owner
    ruled against.
- **Night 2, the upstream restores the entries:** `upward_anomalies` returns *"coding's board would
  be 85 of 173 names this artifact has never seen (49%, over the 25% limit)"*. That is a **refusal**,
  and the sentence is false: the artifact served all 85 names two nights earlier.
- **Every later night:** the live artifact is still the shrunk one, so the same refusal repeats, and
  anything new the upstream adds only raises the share. The refresh is frozen for all 14 surfaces
  and every price until someone publishes by hand.

**Reproduced through the real `refresh()` and `build.main`.** I used a scratch test in the clone,
deleted after the run, with the repository's own helpers (`_first_cycle`, `_swebench_with`,
`_sources`, `_use`):
- night 1: exit 0, "the served content changed", board 18 to 2, floor 22.0 to 79.2, ranked 2 to 2;
- nights 2 and 3: exit 3, "coding's board would be 16 of 18 names this artifact has never seen
  (89%, over the 25% limit)".

**Why it matters:**
- **The two directions are inconsistent.** D-132 is "a surface may not change by more than a
  quarter, in either direction", and its name axis is safe only because D-128 bounds the shrink at
  the same quarter. A ranked roster can lose at most a quarter, so its recovery is always under the
  limit. The board axis has no such pair.
- **This change introduces the freeze.** Before it, the shrink and the recovery both published.
- **D-128 names the freeze as the failure to fear.**

**Fix (the owner's call, since the guard is owner-ruled).** Either option closes it:
1. Add the shrink half: refuse a board that would lose more than a quarter of its names, mirroring
   D-128. The recovery from any shrink the refresh allowed then stays under the limit.
2. Record the residual (a shrink publishes, and its recovery needs a hand-publish) in D-159 and in
   the ledger with an owning milestone.

In either case:
- Correct the comment at `refresh.py:154` for the board call.
- Word the refusal "names this board does not carry now". "Never seen" is not what the code
  measures.

## MINOR

### MINOR-1 -- the guard limits a night's growth, not the floor; the record reads as if the gap were closed

**Where:** `docs/decisions.md:2743-2751`. It reports the owner's example (60 rows moved `coding` 65.4
to 71.3), and then describes the guard as the answer to it.

**Measured on a copy of the owner's artifact:**
- **57 unpriced rows (scores 90.00 to 90.56) on `coding`:** the floor moves 65.4 to **74.4**, and
  `upward_anomalies` = `[]`, `degradations` = `[]`.
- **The same with 60 rows:** refused, as "60 of 233 names (25.8%)". The ruling's own example is
  caught by three rows.
- **A second night, 76 more rows on top of the 57:** the floor reaches **90.3**, still no refusal. A
  board may add up to a third of itself each night.

**Why it matters:** the owner asked "should we prevent this?". The guard slows a floor-moving
injection; it does not prevent it. That is the same residual D-132 accepts for ranked names, and it
is acceptable for a "simple guard", but it should be written down.

**Fix:** one sentence in the D-159 amendment, or a ledger row naming the residual and its owning
milestone.

### MINOR-2 -- the quarter on the board axis is not pinned by any test

**Mutants:**
- **B2** makes the board axis fire only above HALF new names. It stays GREEN on the full suite.
- **B4** turns `>` into `>=`. It is GREEN too, and it also touches D-132's axis through the shared
  helper.

**Why the suite misses them:** the tests sit far from the limit.
- `test_floor_served.py:267` adds 60 names to a board of 23, which is 72%.
- `:288` adds 30 to 18, which is 62%.
- `:279` adds 2 to 22, which is 8%.

**Consequence:** under B2, the owner's own 60-row example (25.8%) would pass.

**Killer:** a scratch test, K2, builds a live board whose size is a multiple of three, then requires
that adding exactly a third passes and adding one more is refused. It passes on HEAD and is RED on
both B2 and B4. I deleted it after the run. It belongs in `test_floor_served.py`.

### MINOR-3 -- ordinary movement on boards was not measured before the threshold was chosen; the classes it will refuse are unrecorded

D-132's method puts the measurement first ("What ordinary movement actually is, measured ... comes
first"). REQ-GRD-001 (`docs/prd.md:424`) still says "Two axes ... ordinary movement MEASURED at 0% on
both". The third axis appears neither there nor in any measurement.

**Board names are not ranked names.** They include every effort variant (Epoch's
`gpt-5.6-sol_xhigh`) and SWE-bench's agent prefix, so they move far more than the canonical names
D-132 measured.

**Evidence from the owner's artifact.** There are no two nightly artifacts to compare, so I used
`run_date` as a lower bound on arrival. Board sizes and allowed new names per night:
- `search` 34 names, 11 new allowed;
- `search_factuality` 32 names, 10 new allowed;
- `document` 44 names, 14 new allowed;
- `agentic-coding` 49 names, 16 new allowed;
- the largest boards allow 57 to 173.

**Single days pass.** The largest one-day increment in 2026:
- GPQA 35 of 256 (14%);
- AIME 39 of 231 (17%);
- TerminalBench 8 of 58 (14%);
- SWE-bench 11 of 171 (6%).

**Epoch campaigns sit at the limit.** The 2026-08-06/07 effort sweep, mostly new `_none`, `_low` and
`_minimal` variants:
- **GPQA:** 62 names, 24% (the limit is 64).
- **AIME:** 63 names, **27%** (the limit is 56). It would be refused if one bundle update carried
  both days.

**A carried Epoch bundle that returns (D-156 with D-158):** a 14-day outage followed by a return is
28% on `expert` and **32%** on `mathematics`, so it is refused. D-158 itself (`docs/decisions.md:2669`)
measured a fresh bundle growing five boards by 18 to 50%, and the guard would refuse the ones above a
third.

**An upstream respelling.** Simulated on a copy: Epoch ECI's `_` becomes `-`, the separator spelling
D-157's grammar already unifies.
- `everyday`'s board: "284 of 521 names ... (55%)", **refused**.
- The floor is unchanged, since the scores are the same.
- `degradations` and D-132's ranked axis are silent.
- The guard therefore refuses a candidate that cannot move the floor it exists to protect.

**What the refusals are not.** None of these is a wrong publish. D-159's amendment accepts that "a
legitimate jump is published by hand". But no runbook says how, and no ledger row or revisit trigger
counts how often it happens.

**Fix:**
- Add the board axis and its citing tests to REQ-GRD-001.
- Record the expected refusal classes (Epoch campaigns, a carry that returns, a respelling) with a
  revisit trigger.
- Consider firing the board axis only when the floor also moved. That is its stated purpose, and it
  would remove the respelling class and part of the others.

## NITs

- **NIT-1 (ledger wording).** Three small problems in `docs/warnings.ledger.md:178-179`:
  - **W-133's status.** It is `ESCALATED` although its own text says the owner ruled ("the anchor
    moves with the floor"). What remains is scheduled work with an owning milestone: ACCEPTED, or
    OPEN until the next change.
  - **W-132's escalation record.** It names none. The template's ESCALATED column asks for one; a
    pointer to where the owner is asked would do.
  - **W-132's direction.** It says "a board that rises past a window would turn the owner's run
    red". It is the other way round: `assert spec.value_window < floor`
    (`tests/unit/test_categories.py:343`) fails when a floor FALLS to its window. Today's floors are
    10 to 30 times their windows (for example `coding` 65.4 against 6.0), so the signal is
    near-vacuous either way.
- **NIT-2 (`floors.py:43-45` docstring).** It says a name-based set means "an upstream that relabels a
  harness or an effort on rows it already had is not read as a board of new rows". That holds only
  when the PROJECT re-derives those columns: mutant F2 (by row) is killed by
  `test_refresh.py::test_a_freshness_or_provenance_update_is_published[harness-other]`. Upstream,
  the raw name carries them:
  - Epoch: `gpt-5.6-sol_xhigh`, whose effort column is `xhigh`;
  - SWE-bench: "agent + model", whose harness is split from the name (`swebench.py:94`).
- **NIT-3 (the refusal's framing).** The board refusal is prefixed "the candidate improved in a way
  ordinary upstream movement does not produce" (`refresh.py:803-808`). A respelling or a recovery
  (MAJOR-1) is not an improvement, and "this artifact has never seen" is per board, not per artifact:
  a name on AIME's board is "never seen" on GPQA's.
- **NIT-4 (two queries for one board).** `board_names` repeats `board_scores`' WHERE clause
  (`floors.py:36-37` and `:46-47`) instead of sharing it. If one drifts, the guard reads a different
  set than the floor. Mutant F1 is killed only because the returning-board fixture happens to move
  rows to another source on the same benchmark.
  - **An unpinned assumption.** The guard also relies on each board having one row per raw name,
    which is true today only because every parser dedupes by name (`swebench.py` `best`,
    `epoch.py:202-208`, `epoch_board.py:215-217`, `arena.py`). A parser that kept one row per
    scaffold would let rows move the floor with no new name.
  - **Where it belongs:** K.9.

## Hardened-invariant producer section (Code-Reviewer §2a-bis)

**Invariant (D-159 owner ruling): each cycle judges every surface's own board, by raw name, against
the served board. More than a quarter new is refused, and a board returning from empty passes.**

**Producers of `ServingSummary.board`.** `git grep -n "board_names(\|board=" -- src` at HEAD:
```
src/app/workflows/floors.py:42:def board_names(conn: sqlite3.Connection, spec: CategorySpec) -> frozenset[str]:
src/app/workflows/refresh.py:419:        boards[name] = board_names(conn, spec)
src/app/workflows/refresh.py:429:        board=boards,
```
`serving_summary` is the only producer. It feeds:
- `fingerprint_of` (the live artifact and the candidate);
- `_served_without` (the expiry baseline, which the board axis deliberately does not read, like
  D-132's names).

A hand-built `ServingSummary` defaults to empty boards (`refresh.py:353`), which the axis treats as
returning.

| Producer / path | Citing test | Gap |
|---|---|---|
| `serving_summary` board collection, `refresh.py:419` | `test_floor_served.py:267`, `:288`, `:304` (mutants S1, S2 RED) | none |
| `board_names`, `floors.py:42` | `test_floor_served.py:304` (F1 RED); `test_refresh.py` harness-other (F2 RED) | shares no query with `board_scores` (NIT-4) |
| board axis, `refresh.py:197` | `test_floor_served.py:267`, `:279`, `:288` (B1, B5 RED) | the quarter (MINOR-2); the shrink (MAJOR-1) |
| returning exemption, `refresh.py:155` | `test_floor_served.py:304`; `test_refresh.py` surface-returning (B3 RED) | none |
| expiry night (D-156) | `test_refresh_carry.py` secondary expiry (B5 RED) | a primary board that expires is skipped by `if not now` (correct), and its return passes by `if not was` (tested) |

**Interactions I checked:**
- **D-156 carry.** Carried rows are the live artifact's own rows, so they add no name.
- **D-156 expiry.** The candidate board is empty, so it is skipped. Its return is exempt.
- **D-157 derived registry.** `board_names` reads `raw_name`, never `model_id`, so no registry change
  can trip it.
- **D-158 bundle.** See MINOR-3: an outage followed by a return is the realistic refusal.

## Mutants

**How each mutant ran:**
- One at a time, in place, in the clone.
- The harness replaced one exact string, and refused any string that did not match exactly once.
- Each ran the full suite (`tests`, `-n auto`, `MODEL_RANKING_REQUIRE_ARTIFACT=1`, the owner's
  artifact present).
- Each change was string-replaced back, and the md5 compared with the value taken before. **All 17
  restores were byte-identical** (15 mutants, plus B2 and B4 re-run with the scratch killer K2).
- Baseline before the mutants: 1207 passed, 15 skipped, 0 failed.

| # | Mutant (load-bearing line) | Result |
|---|---|---|
| B1 | `refresh.py:197` board axis never runs | RED, 2 (`test_floor_served.py:267`, `:288`) |
| **B2** | `refresh.py:198` board axis fires only above 50% new | **GREEN, full suite.** RED on scratch K2 (MINOR-2) |
| B3 | `refresh.py:155` returning exemption removed | RED, 3 (`test_floor_served.py:304`, `test_refresh.py` surface-returning, `test_epoch_bundle_fetch.py` bundle cycle) |
| **B4** | `refresh.py:161` `>` to `>=` (both axes) | **GREEN, full suite.** RED on scratch K2 (MINOR-2) |
| B5 | `refresh.py:160` counts names LOST instead of added | RED, 4 (incl. `test_refresh_carry.py` secondary expiry) |
| S1 | `refresh.py:419` board read as the ranked names | RED, 3 |
| S2 | `refresh.py:419` `coding`'s board always empty | RED, 3 |
| F1 | `floors.py:47` source filter dropped | RED, 1 (`test_floor_served.py:304`) |
| F2 | `floors.py:47` by row (`raw_name` plus harness), not by name | RED, 1 (`test_refresh.py` harness-other) |
| E3 | `recommend.py:581` fact without `unit` | RED, 1 (`test_floor_served.py:150`) |
| E5 | `recommend.py:581` fact with an extra `floor: None` | RED, 1 (`test_floor_served.py:150`) |
| R4 | `refresh.py:415` floor hashed to whole points | RED, 14 (`test_floor_served.py:164`, every surface) |
| R5 | `refresh.py:415` only `coding`'s floor hashed | RED, 13 |
| C1 | `Language.swift:42` raw value `no_floor` (Python suite only) | RED, 1 (`test_ios_client_contract.py:998`) |
| C2 | `recommend.py:582` `nothing_clears_the_floor` | RED, 4 (incl. `test_ios_client_contract.py:998`, `test_why_facts.py`) |

**Totals:** 15 mutants give 13 RED and 2 GREEN. None is equivalent. Both GREEN mutants are closed by
the scratch killer K2, which passes on HEAD and was deleted after use.

**Kill rate, for the Tester profile's advisory:** 13/15 on the suite as committed, 15/15 with K2.

## Red to green, replayed

- **`222feea` (red), from a `git archive` export:** `tests/unit/test_floor_served.py` gives 2 failed,
  25 passed.
  - `test_a_board_flooded_with_rows_it_has_never_seen_is_refused` fails with `AssertionError: []`
    (`:276`): `upward_anomalies` objects to nothing.
  - `test_the_refresh_refuses_a_flooded_board_end_to_end` fails with `AssertionError: the served
    content changed` (`:300`): `refresh()` published where 3 was expected.
  - This is exactly the commit message's stated reason.
  - The pace test passes at `222feea`, as it should (there is nothing to refuse).
- **HEAD:** everything passes.
- **`test_a_board_that_returns_is_not_refused` (`:304`).** It first appears in the green commit. It
  guards an exemption, so it cannot be red before the guard exists. Mutant B3 is its red.
- **`ea883a3`'s tests are mutant killers,** honestly described in the commit message as passing on
  the fix they guard. R4, R5, E3, C1 and C2 above are their red.

## Gates

**`make check-fast`** in the clone (tracked files plus the owner's `advisor.db`): **exit 0**,
"check-fast PASS in 42s", 44.7 s wall.
- **records PASS:** "conformance PASS: 14 test(s) ... 0 failing", with test-documented-paths
  "0 dangling".
- **client PASS:** "client-decls PASS: 11 client file(s) in 4 configuration(s)".
- **python PASS:**
  - pytest: **1207 passed, 15 skipped**, total coverage 90%;
  - "coverage-floor PASS: 36 module(s), floor 60%, 1 exempt".
- **swift PASS:** "swift-test (parallel) PASS: 268 test(s), exactly the ones named in
  ios/EngineTests/test-manifest.txt".

**`make check`** (the merge gate): **exit 0**, 1:16.9 wall.
- **Static checks:** ruff "All checks passed!"; mypy "Success: no issues found in 36 source files".
- **pytest:** **1207 passed, 15 skipped**, coverage 90%.
- **Touched modules:** `refresh.py` 96%, `floors.py` 100%, `recommend.py` 95%.
- **coverage-floor PASS.**
- **wave-check-all:** "43 v5.0/v6.0 record(s) validated".
- **conformance:** 14 tests, 0 failing; test-documented-paths "0 dangling".
- **swift-test:** "PASS: 268 test(s)".
- **client-decls PASS.**

**The skips:** the 15 skips are the network contract tests (`RUN_CONTRACT_TESTS`) and the
`EPOCH_DATA_DIR` tests. Every artifact test ran.

## K.9 candidates outside this round's scope

- **One board query for the floor and the guard.** `floors.py` could share the WHERE clause, with a
  test that one row per raw name holds on every board (NIT-4).
- **A runbook entry for "publish a refused candidate by hand".** D-132 and now D-159 both rely on it,
  and I found no written procedure in `docs/`.

## What I did not check

- **A live refresh against real upstreams, or two consecutive real nightly artifacts.** MINOR-3's
  movement figures are estimates from `run_date`, which bounds arrival from below.
- **Whether the owner's rulings quoted in D-159 and W-133 were given as recorded.** They are in
  session and in PR #12, which this seat cannot reach.
- **The app on a device, or the Swift suite under mutant C1.** The previous seat ran the Swift side
  of that mutant.
- **Security (Stage 4.0).**
