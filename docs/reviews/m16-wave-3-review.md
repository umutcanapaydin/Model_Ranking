---
record_type: review
id: m16-wave-3-review
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M16-W3 — independent review: carry-forward (D-156) and one floor rule (D-148 applied)

**Seat:** independent (Code-Reviewer + Tester combined, risk tier MED; I wrote none of this wave).
**Change:** branch `enhancement/m16-w3-one-rule`, draft PR #3, `git diff origin/main...HEAD`
(`a382bbe..ca7e29f`). I read the policy only from `git show origin/main:subagent-profiles/Code-Reviewer.md`
and `git show origin/main:subagent-profiles/Tester.md`. Author family and reviewer family were not
given to this seat (fallback: same session tooling). My context was fresh.

**Snapshot.** Every result below is against these md5s: `build.py` `03cace81...`, `refresh.py` `89ea163f...`,
`nightly.py` `8f61e040...`, `categories.py` `60e4b764...`, `survey_boards.py` `e9a536a2...`, the floor
record `3a48589c...`. The owner's `advisor.db` / `.refresh.json` were `ef9e48a9...` / `7e0355ed...`
before and after my work. I read them only as copies under the session scratch directory. I started
nothing on :8080 and left no process running. `origin/main` was checked out with
`git worktree add --detach` into scratch and removed afterwards. Every mutant was applied to a copy of
the tree by a script, run, restored, and md5-checked byte-identical.

## Verdict

**BLOCKING — 2 BLOCKING, 3 MAJOR, 5 MINOR, 4 NIT.**

The carry mechanics work. I measured a failed source's rows being copied, re-reconciled and published
beside fresh data. The arrival clock does not restart when the seconds differ (E10). The D-148 floors
match `survey_boards.py --floors` on the served artifact to the decimal. On the `/v1` path the floor
change alters exactly the picks the record names.

The two BLOCKING findings are tests. The two D-156 invariants that make the rule mean anything are
held by tests that pass whatever the code does:
- "a carry does not restart the 30 days"
- "every other blinding is still refused"

Separately, one source's expiry still freezes the refresh (MAJOR-1). `/health` also stops telling
the truth after any cycle that does not serve (MAJOR-2).

## Suite result (run by me)

- `make -o install check` stopped at `wave-check-all`. The only failing record is the UNTRACKED
  `docs/plans/m16-wave-3-close.md`, which is the author's close in progress and not part of the
  branch. It fails V3C-69 because it cites no review yet. Every gate before it passed:
  - ruff: "All checks passed!"
  - mypy: "no issues found in 34 source files"
  - pytest: **1046 passed, 15 skipped**, coverage 89.54%
  - `coverage-floor`, `check_records`, the self-test, `install-check` and `shell-dialect` all passed.
- `.venv/bin/python conformance/run-all.py`: **PASS**, 14 tests, 0 failing.
- The mutant baseline on the scratch copy (with a copy of `advisor.db` present) also gave 1046
  passed / 15 skipped.

## Findings

### BLOCKING-1 — "A carried source does not restart its 30 days" is held by a test that passes whatever the code does

`tests/unit/test_refresh_carry.py:92-101` runs two cycles and asserts that swebench's
`sources_last_ok` stamp is unchanged. The stamp is `at` at one-second resolution
(`refresh.py:570-571`). Both cycles of the test land in the same second, so the stamp cannot change,
whatever `write_status` does.

- **Measured (E11):** first stamp `2026-09-23T00:45:23+00:00`; the second cycle's record is
  `at_iso 2026-09-23T00:45:23.638+00:00`.
- **Mutant M26** (`last_ok.update` over `(*outcome.arrived, *outcome.carried)`, so a carry restarts
  the clock every night and no list ever drops) → **GREEN, 1046 passed.**
- **Mutant M10** (every candidate source counted as arrived) → **GREEN.**

The code itself is right. With the seconds apart (E10: `last_ok` pre-set to 2026-09-01, rows aged an
hour), `arrived=('aider','litellm')` and swebench stays at `2026-09-01`. But REQ-REF-009 lists "the
30 days not restarted by a carry" as cited, and nothing holds it. Under the base-pinned Tester profile
§1, a test that does not assert the claimed behaviour is BLOCKING.

*Remedy:* pre-seed `sources_last_ok` with an old stamp (as in E10), or inject `clock`, then assert
that the carried source keeps its old stamp and the arrived ones advance. Confirm it goes red on M10
and M26.

### BLOCKING-2 — "Every other blinding is still refused" has no test that can fail; the exemption can be widened freely

`tests/unit/test_refresh_carry.py:124-138` claims to pin that an optional source whose rows vanished
without aging out is still refused. The test deletes swebench from the LIVE artifact first, so the
live `coding` surface already answers nothing. There is no blinding to refuse, and the test asserts
only that `expired` is empty. That is trivially true, because `_sources_after_build` iterates live
stamps (`refresh.py:806-811`).

- **Measured (E5):** the cycle exits **1 "nothing a user would notice changed"**, not a refusal.
- **Mutant M11** (`refresh.py:810` → `if age is not None:`, so every source that is absent from the
  candidate counts as "expired" and its surfaces are excused whatever its age) → **GREEN, 1046
  passed.**

M7 (excuse every surface) is caught only because it excuses surfaces that have no source at all.
D-156 clause 3's "still refuses every other blinding" is the safety half of the exemption, and
nothing holds it.

*Remedy:* keep the source in the live artifact with a YOUNG arrival. Make the carry impossible (for
example, the live rows unreadable to `restore`, or `last_ok` young while the build is not handed
`--carry-from`). Assert `EXIT_REFUSED` and that the live file is byte-identical. Confirm it goes red
on M11.

### MAJOR-1 — An expired `epoch_swe_bench_verified` still refuses every cycle: REQ-REF-009 is false for one source

`refresh.py:897-898` excuses only the surfaces whose `primary_source` expired. The ranking selects by
BENCHMARK with no source predicate (`rank.py`, and the note at `main.py:759-767`), and
`epoch_swe_bench_verified` feeds `coding` (SWE-bench Verified) while no surface names it as primary.

**Measured on a copy of the served artifact (scratch script "e6").** For each of the 19 sources I deleted that
source's rows and ran `degradations(live, candidate, excused)` with the wave's own `excused`:
- 18 sources publish.
- `epoch_swe_bench_verified` gives **"REFUSED: coding would lose 12 of 44 models (27%, at or over the
  25% limit)"**.

So the Epoch bundle missing for over 30 days (a moved directory, a broken file) makes the refresh
refuse **every night until the bundle returns**, throwing away fresh LiteLLM, OpenRouter and
SWE-bench data. That is exactly the 2026-09-20 freeze D-156 was written to end. D-156 clause 3 and
REQ-REF-009 ("the refresh publishes the rest rather than refusing") both claim otherwise.

*Remedy:* derive `excused` from what the expired source actually feeds, not from `primary_source`.
For example, map the live artifact's `SELECT DISTINCT benchmark FROM scores WHERE source IN expired`
to surfaces by `primary_benchmark`, and limit the exemption to the loss those rows account for. Add
a test that runs the `e6` loop over every declared source.

### MAJOR-2 — `/health`'s carry disclosure describes the last CYCLE, not the served artifact

D-156 clause 4 and "The cost" make `/health` the only place a month-old price or score shows.
`write_status` writes `outcome.carried` / `outcome.expired` from the current cycle (`refresh.py:599-600`),
and every failed outcome is built without them. I measured three problems:

- **E2:** cycle 2 carries swebench and publishes, and `/health` shows `refresh_carried: "swebench 0.0d"`.
  Cycle 3 fails (build exit 2), and `refresh_carried` is now `''`. The live artifact still serves the
  carried swebench rows (2 rows, `MAX(observed_at)` from the earlier fetch).
- **E8:** a REQUIRED source past 30 days fails the cycle, and `/health` gives `refresh_last: "failed"`,
  `refresh_expired: ''`. The only place the word "expired" appears is the build's stderr.
- **E9:** an optional source expires and shows `refresh_expired: "swebench 45.0d"` for exactly one
  night. On the next cycle it shows `''` although the surface is still dropped.

A refused cycle writes the refused CANDIDATE's carry set, which is not what is served.

*Remedy:*
- Carry `carried` forward from the previous record on every cycle that does not serve, as
  `last_published_at` already is.
- Record the build's expired set on the failed path (the build knows it: `BuildReport.expired`).
- Keep an expired source listed until it arrives again.
- Add a test for each of the three.

### MAJOR-3 — A board or bundle that FAILS (as opposed to having no directory) is never shown to carry

Every source carries (ruled 2026-09-23). The realistic Epoch outage is a directory that is present
but holds a missing or malformed file, which takes the `except` path at `build.py:323` (boards) and
`build.py:379` (bundles). Only the no-directory path is tested
(`test_an_epoch_board_or_bundle_is_carried_when_its_directory_is_missing`).

- **Mutant M18** (a failing board ignores the carry) → **GREEN**.
- **Mutant M19** (the same for a bundle) → **GREEN**.

Half of "every source carries" for 9 of the 19 sources is unproven.

*Remedy:* one test per path: a bundle directory where one board's file is corrupt, then assert that
board is carried and not reported missing.

### MINOR-1 — The build and the refresh decide "expired" twice, with different arithmetic; one boundary night is refused

The build expires on the unrounded age against `now` at build start (`build.py:215`, `:243`). The
refresh rounds to 0.1 day against `now` after the build (`refresh.py:784`, `:810`).

**E1:** with `last_ok` 30 days 30 minutes old, the build drops the source but the refresh sees 30.0,
which is not over 30. So nothing is excused, and the cycle is **REFUSED (exit 3)** with a D-128
reason naming `coding` and `expired: {}`. Any age in (30, 30.05] days does this. It heals the next
night. It is also DevFlow §3.5's one fact in two places: the refresh re-infers what the build already
knows.

*Remedy:* have the build write its `carried` / `expired` to a file the refresh reads, rather than
re-deriving them.

### MINOR-2 — Arrival is inferred from stamp equality; a clock step poisons the record, and a future stamp carries forever

`refresh.py:798-799` treats "stamp equals the candidate's newest" as having arrived.

- **E3b:** live rows stamped one hour ahead (the previous cycle ran on a fast clock), then swebench
  fails. The result is `arrived=('swebench',)` and `carried={'aider': 22.0, 'litellm': 22.0}`. The
  failed source's 30 days RESTART, and the two sources that did arrive keep their old clock.
- **E4:** a `sources_last_ok` stamp 400 days in the future gives `carried {'swebench': -400.0}` and
  `/health` `"swebench -400.0d"`. A negative age is never expired (`build.py:243`).

Two cycles in the same second cannot happen in production: the lock is held and a build takes
seconds, since `RunContext` stamps at build start.

*Remedy:* take arrival from the build's own report (see MINOR-1), and treat a negative age as
unknown (fall back to the row stamp).

### MINOR-3 — The floor record's "one pick changes" is true of `/v1` only; the subscription CLI changes two Budget Picks it does not name

I re-ran `recommend()` and `recommend_subscription()` for every surface and budget, from
`origin/main` (worktree) and HEAD, on a read-only copy of the artifact:
- **`/v1` picks:** only `agentic-coding` medium and unlimited change, Budget Pick Grok 4.5 → GPT-5.6
  Sol. That is exactly the record.
- **Subscriptions:** `agentic-coding` medium Budget Pick goes Perplexity Pro ($20, 53.8) → **Google AI
  Plus ($4.99, 11.8) with "WARNING: no plan in this budget clears the 64.4 points…"**. At unlimited
  it goes Perplexity Pro → ChatGPT Pro ($100).

The research record says "No Best Value or Best Quality changes anywhere". That is true, but the
subscription Budget Pick changes are not in the table the owner ruled from. D-148's "Applied" note
repeats "one pick changes".

*Remedy:* add the two subscription rows to the record, and state the owner's ruling covers them (or
put them back to the owner).

### MINOR-4 — Test gaps the mutants walked through (besides the BLOCKING and MAJOR ones)

- **M4** (carried rows keep the live `model_id` instead of NULL, `build.py:232`) → GREEN. `reconcile`
  only UPDATEs rows it matches, so a carried row whose alias the current registry drops would keep a
  stale id. `test_the_carried_rows_join_the_calculations` compares NULL counts, which M4 preserves.
- **M22** (carried age always 0, `refresh.py:804`) → GREEN. `test_refresh_carry.py:89` asserts `< 1`.
- **M24 / M25** (survey drops the `metric` or `source` predicate, `survey_boards.py:198`) → GREEN.
  M25 would count 206 rows for `coding` instead of 173, because `epoch_swe_bench_verified` shares the
  benchmark.
- `test_floor_rule.py` holds code == record, not record == measurement. A survey that drifted and
  regenerated the record passes it.

*Remedy:* one assertion each. Plant a second-source row and an off-metric row in
`test_survey_floors.py`.

### MINOR-5 — No test cites REQ-REF-009

`grep -rn REQ-REF-009 tests` returns nothing (the tests cite D-156). This is the same gap the W2
review raised as MINOR-5 for REQ-REF-008, which W2 then fixed. *Remedy:* cite it in the three
modules' docstrings.

### NIT-1 — A killed cycle leaves `advisor.db.*.last-ok` next to the candidate

`refresh.py:853` creates a second uniquely named scratch file, and only the `finally` removes it.
This is the same class as W-124: append it there.

### NIT-2 — Two stale mirrors of the floor rule

- `rank.py:243-244` still says the ranked population "is the population every threshold in
  `categories.py` describes". D-148 says floors are board rows.
- `recommend.py:43` `MIN_QUALITY_PCT = 65.0` still mirrors `coding`'s old floor (now 65.4). Its Elo
  sibling was updated, and it is pinned at 65.0 by `test_recommend.py:251`. It is used only in
  docstrings and tests.

### NIT-3 — A carried insert is outside the `sqlite3.Error` guard

`build.py:251`: if a later schema adds a NOT NULL column without a default, carrying any source fails
the whole build (exit 2) instead of degrading. This is hypothetical today.

### NIT-4 — `test_survey_floors.py:66-67` pins an interpretation D-148 does not state

The test counts one raw name at two efforts as two rows. D-148 says "one per raw name". On the served
artifact the two readings coincide: raw names are unique per row on all 14 boards (measured). Say
which one the rule means.

## Mutants (applied to a scratch copy, full suite `pytest -n auto -x`, restored, md5-verified)

| # | Mutant | Result |
|---|---|---|
| M1 | never expire (`build.py:243`) | RED `test_a_source_older_than_a_month_is_not_carried` |
| M2 | report carried, insert nothing | RED `test_a_failed_required_source_is_carried…` |
| M3 | a required source fails even when carried | RED (same) |
| M4 | carried rows keep the live `model_id` | **GREEN** (MINOR-4) |
| M5 | age ignores the arrival record | RED |
| M6 | age fallback takes MIN(observed_at) | GREEN, equivalent (a source's rows always share one stamp) |
| M7 | excuse every surface | RED `test_refresh.py::test_a_candidate_that_blinds_a_surface_is_refused` |
| M8 | excuse nothing | RED `test_an_expired_source_drops_its_surface…` |
| M9 | refused/failed cycles count as arrivals | RED `test_only_a_served_cycle_counts_as_an_arrival[2,3]` |
| M10 | every candidate source counts as arrived | **GREEN** (BLOCKING-1) |
| M11 | anything absent counts as expired | **GREEN** (BLOCKING-2) |
| M12 | the refresh hands the build no carry | RED `test_the_2026_09_20_incident…` |
| M13 | `/health` says nothing | RED `test_health_names_each_carried…` |
| M14 | the refresh forgets the arrival record | RED |
| M15 | the build ignores `--last-ok` | RED |
| M16 | refresh expiry ignores the arrival record | RED |
| M17 | no-bundle-dir path ignores carry | RED |
| M18 | a failing board ignores carry | **GREEN** (MAJOR-3) |
| M19 | a failing bundle ignores carry | **GREEN** (MAJOR-3) |
| M20 | pricing not carried | RED `test_pricing_is_carried_like_evidence` |
| M21 | budget axis not excused | RED |
| M22 | carried age reported as 0 | **GREEN** (MINOR-4) |
| M23 | survey floor over distinct models | RED `test_the_rows_rule_takes_the_top_third…` |
| M24 | survey drops the metric predicate | **GREEN** (MINOR-4) |
| M25 | survey drops the source predicate | **GREEN** (MINOR-4) |
| M26 | a carried source's clock restarts | **GREEN** (BLOCKING-1) |
| M27 | a required expiry's error loses "expired" | RED |

27 mutants: 17 RED, 1 equivalent, 9 survived. The scenario scripts E1-E11 and "e6" ran on
scratch copies; their outputs are quoted in the findings.

## Acceptance-criterion evidence

- **P1, carry in the build:** `tests/unit/test_carry_forward.py`.
  - Carried: `:59`. Expired, required: `:84`. Expired, optional: `:93`. Fresh: `:108`.
  - No live artifact: `:115`. Epoch without a directory: `:173`. Pricing: `:141`.
  - Green, and red on M1-M3, M5, M17, M20. The failing-board and failing-bundle path is unproven
    (MAJOR-3).
- **P2, the refresh:**
  - The incident is replayed at `test_refresh_carry.py:76`. Green, and red on M12.
  - Expired published: `:106`. Red on M8, M14-M16, M21.
  - The clock and the exemption guards are vacuous (BLOCKING-1/2).
- **P3, disclosure:** `test_nightly_refresh.py:543`. Formatting only. The record's semantics are
  wrong after a non-serving cycle (MAJOR-2).
- **P4, survey:** `test_survey_floors.py`. It reproduces the record's 14 rows exactly on a copy of
  the artifact, and `parse_rate_board` keep-best is tested. The predicates are unpinned (MINOR-4).
- **P5/P6, floors:** `test_floor_rule.py`, where the code equals the record on all 14 surfaces. The
  `/v1` pick change matches the record; subscriptions do not (MINOR-3).

## K.8 contract drift check

`grep -n "refresh_carried\|refresh_expired" src/`:

```
src/app/adapter/nightly.py:347:            "refresh_carried": _aged(record.get("carried") if record else None),
src/app/adapter/nightly.py:348:            "refresh_expired": _aged(record.get("expired") if record else None),
```

The four keys of D-154 are unchanged, and the two new ones are additive, as D-156 clause 4 says. `/v1`
is untouched: no diff under `src/app/adapter/main.py` or `ios/`. OK.

## K.9 candidates outside this wave

- `docs/plans/m16-wave-3-close.md` (untracked) fails `wave-check-all` V3C-69 until it cites this file.
- W-127's claim that the eight M8 surfaces follow clause 2 was not re-derived by me (below).

## What I did not check

- `make swift-test` and `client-decls`: `make check` stopped before them, and the wave touches no
  Swift.
- Any live network cycle: every refresh ran on fakes or copies.
- W-127's statement about which surfaces' margins follow clause 2: I did not re-derive the M8
  candidate-count sizing.
- Security aspects (Stage 4.0).
- Whether the owner's in-session rulings quoted in D-156 and the floor record were given as written.
