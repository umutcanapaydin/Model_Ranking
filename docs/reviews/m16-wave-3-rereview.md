---
record_type: review
id: m16-wave-3-rereview
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M16-W3 -- independent re-review of the fix round (D-156 amendment, commit f2e29ff)

**Seat:** independent (Code-Reviewer + Tester combined; I wrote none of this wave or its fixes).
**Scope:** the fix round `ca7e29f..f2e29ff` (one commit; HEAD moved to `486b765` during the review, a docs-only record of the owner's acceptance), read against the first review
`docs/reviews/m16-wave-3-review.md` and the D-156 amendment at the end of `docs/decisions.md`.
**Policy:** read only from `git show origin/main:subagent-profiles/Code-Reviewer.md` and `.../Tester.md`.
**Families:** the author is recorded as Claude, and this seat is also Claude. No second family was
available to this seat, so this is the fallback. My context was fresh: I did not see the author's
session.

**Snapshot.** Every result below is against these md5s:
- `build.py` `0e21ff0b...`
- `refresh.py` `6fe5284d...`
- `nightly.py` `ae5f03c4...`
- `survey_boards.py` `e9a536a2...`

The owner's `advisor.db` and `.refresh.json` were `ef9e48a9...` and `7e0355ed...` before and after my
work. I read them only as copies in the session scratch directory. I did the following there:
- applied every mutant to a copy of the tree, one at a time;
- ran each mutant against the full suite unless a row says otherwise;
- restored each file and md5-checked it byte-identical by script.

The scenario scripts ran on the same copy, with the real `refresh()` and the real `build.main`, and
fake upstreams. I started nothing on :8080. I left no process and no repository file behind except
this one.

## Verdict

**BLOCKING -- 1 BLOCKING, 1 MAJOR, 3 MINOR, 3 NIT.**

**What the fix round got right.** Everything the first review measured as broken is fixed in the
code. The re-run shows:
- All of that review's surviving mutants now go red: M4, M10, M11, M18, M19, M22, M24, M25 and M26.
- The build is the one source of truth for arrived, carried and expired. The E1 boundary night now
  publishes.
- `/health` stays true across failed, refused and unchanged cycles (E2, E8, E9, measured end to end).
- All 19 sources pass the e6 loop on the served artifact.

**What still blocks.** The MAJOR-1 fix is not held where it acts. Two mutants survive:
- Reverting the cycle to the `primary_source` exemption (N5).
- Excusing every surface whenever anything expires (N15).

The new rule also excuses too much. On the night a secondary source expires, it lifts D-128 for the
WHOLE surface. I measured a truncated `swebench` feed blinding `coding` (44 -> 0 models) and being
published on that night, while it is refused on every other night.

## Suite result (run by me)

In the working tree I ran `make -o install lint typecheck test coverage-floor`:
- ruff "All checks passed!"
- mypy "Success: no issues found in 34 source files"
- pytest **1054 passed, 15 skipped**, total coverage 89.61%
- `coverage-floor PASS: 34 module(s)`

Touched modules: `build.py` 92%, `refresh.py` 96%, `nightly.py` 99%. Two uncovered spans matter:
- `build.py:278-283` is the new carried-insert guard. No test ever executes it (NIT-1).
- `refresh.py:795` is the malformed-key branch of `_read_build_sources`.

The scratch copy's baseline matched: 1054 passed, 15 skipped. `check_records` and
`conformance/run-all.py` results with this file present are at the end.

## Disposition of the first review's findings

| First review | Disposition | Evidence I ran |
|---|---|---|
| BLOCKING-1 (the carry clock is held by a test that cannot fail) | **CLOSED** | `test_refresh_carry.py:109` seeds arrivals ten days back (`_first_cycle`). M10 and M26 are both RED on `test_a_carry_keeps_its_clock_and_an_arrival_moves_it` and on `:89`. |
| BLOCKING-2 (the rule that every other blinding is refused has no test) | **CLOSED, for a night with no expiry** | `:140` keeps the source live and young and makes the carry impossible. The M11 analog (excuse every live source that did not arrive) is RED on that test, and on 6 tests in `test_refresh.py`. On a night when something DOES expire, the exemption is unpinned: see BLOCKING-1 below. |
| MAJOR-1 (an expired `epoch_swe_bench_verified` refuses every cycle) | **Fixed in code; the fix is not held (BLOCKING-1); over-broad (MAJOR-1)** | e6 re-run on a copy of the served artifact: all 19 of 19 sources publish when their rows are deleted with the wave's `excused`. `epoch_swe_bench_verified` excuses `coding`, which loses 12 of 44 models. Mutant N5 (the cycle uses `primary_source` again) is GREEN, with 1054 passed. |
| MAJOR-2 (`/health` describes the cycle, not what is served) | **CLOSED** | See the three sequences listed below this table. N1, N2, N3, N4 and N8 are each RED. Transitions that are still unpinned: MINOR-2. |
| MAJOR-3 (a failing board or bundle never carries) | **CLOSED** | M18 is RED on `test_carry_forward.py:224[epoch_gpqa]`. M19 is RED on `[epoch_deepswe_external]`. |
| MINOR-1 (expiry decided twice; the boundary night is refused) | **CLOSED** | E1, `last_ok` 30 days and 30 minutes old, optional source: exit 0 "the served content changed", with `expired={'swebench': ...}` (it was exit 3 in the first review). `refresh.py` no longer imports `CARRY_MAX_AGE`. |
| MINOR-2 (arrival inferred from stamps; a future stamp carries forever) | **CLOSED for arrival.** The future-stamp half is changed, and the change is a new MINOR-1. | Arrival now comes from `BuildReport.sources_json()` (`build.py:109-118`). E4, an arrival stamp 400 days ahead with rows 10 days old: carried, with `/health` "swebench 10.0d". E3b is now a failed cycle (MINOR-1 below). |
| MINOR-3 (two subscription Budget Picks the owner did not see) | **CLOSED** | Both rows are in `docs/research/m16-w3-floor-table-2026-09-23.md`, and commit `486b765` (docs only, landed during this review) records the owner's acceptance. D-148's Applied note (`decisions.md:2129`) still says "one pick changes"; the record carries the correction. |
| MINOR-4 (the mutants M4, M22, M24 and M25 walked through) | **CLOSED** for all four mutants. The last bullet is **STILL OPEN** (MINOR-3 below). | M4 is RED on `:246`. M22 is RED on `test_refresh_carry.py:89`. M24 and M25 are RED on `test_survey_floors.py::test_only_the_surfaces_own_source_and_metric_count`. |
| MINOR-5 (no test cites REQ-REF-009) | **CLOSED** | `test_carry_forward.py:1`, `test_refresh_carry.py:1` and `test_nightly_refresh.py:548` all cite it. |
| NIT-1 (scratch left behind by a killed cycle) | **OPEN-RECORDED** | W-124 names `.last-ok` and `.sources`, with the same remedy and the same owner. |
| NIT-2 (stale mirrors of the floor rule) | **CLOSED** | `rank.py` docstring; `recommend.py:43` `MIN_QUALITY_PCT = 65.4`, pinned by `test_recommend.py`. |
| NIT-3 (the carried insert has no guard) | **CLOSED in code, untested** (NIT-1 below) | S8: when a trigger aborts the carried insert, the build degrades (`carried={}`, 0 aider rows in scores and in pricing). N10 and N11 are GREEN, and coverage never reaches `build.py:278-283`. |
| NIT-4 (which rows the rows rule counts) | **CLOSED** | Stated under "Which rows count" in the floor record. |

**Sequences behind MAJOR-2.** All three were measured end to end:
- **E2, carried then not served:** swebench is carried and published. The next cycles are unchanged
  (exit 1) and then refused (exit 3), and `carried` stays intact through both. A failed cycle
  (exit 2) keeping `carried` is held by `test_refresh_carry.py:173`, which goes red on N2.
- **E8, a required source expires:** the cycle exits 2 and the record says `expired={'swebench': <stamp>}`.
  `/health` shows "swebench 31.0d".
- **E9, an optional source expires:** it expires and is published, and the next night is unchanged.
  `/health` still says "swebench 45.0d". The night it arrives, it is removed from the list.

## Mutants

The first review's survivors were re-run on the new code. The N-series attacks the new code. Where a
first-review mutant targeted deleted code (`_sources_after_build`), I rebuilt it against the code
that now does the job.

| # | Mutant | Result |
|---|---|---|
| M4 | carried rows keep the live `model_id` | RED `test_a_carried_row_takes_its_model_id_from_this_build_not_the_live_one` |
| M10 | carried sources reported as arrived (`sources_json`) | RED `test_a_carry_keeps_its_clock…`, `test_the_2026_09_20_incident…` |
| M11 | (rebuilt) every live source that did not arrive is excused | RED `test_a_blinding_that_is_not_an_expiry_is_still_refused` + 6 in `test_refresh.py` |
| M18 | a failing board ignores the carry | RED `…directory_present_is_carried[epoch_gpqa]` |
| M19 | a failing bundle ignores the carry | RED `…[epoch_deepswe_external]` |
| M22 | (rebuilt) the carried stamp is "now" (age 0) | RED `test_the_2026_09_20_incident…` |
| M24 | survey drops the metric predicate | RED `test_only_the_surfaces_own_source_and_metric_count` |
| M25 | survey drops the source predicate | RED (same) |
| M26 | a carried source's clock restarts | RED `test_a_carry_keeps_its_clock…`, `test_the_2026_09_20_incident…` |
| N1 | a failed cycle drops the build's `expired` | RED `test_a_required_source_past_its_age_fails…` |
| N2 | `carried` is always this cycle's | RED `test_a_failed_cycle_still_reports_what_is_served_as_carried` |
| N3 | `expired` not kept across cycles | RED `test_an_expired_source_stays_listed_until_it_arrives` |
| N4 | `expired` popped on an arrival that is not served | RED (same) |
| **N5** | **the cycle excuses by `primary_source` again (MAJOR-1 reverted)** | **GREEN, 1054 passed** (BLOCKING-1) |
| N6 | `_surfaces_fed_by` reads the candidate, not the live artifact | RED `test_an_expired_source_drops_its_surface…` |
| N7 | a future stamp counts as an age | RED `test_an_unreadable_arrival_falls_back_to_the_rows_own_stamp` |
| N8 | the failure report is not attached to the BuildError | RED `test_a_required_source_past_its_age_fails…` |
| N9 | no `--report-out` passed | RED `test_a_source_that_arrives_is_recorded_as_arrived` |
| **N10** | **the carried insert is unguarded** | **GREEN** (NIT-1) |
| **N11** | **the guard does not re-reset the source** | **GREEN** (NIT-1) |
| **N12** | **an unchanged cycle forgets `carried`** | **GREEN** (MINOR-2) |
| **N13** | **`carried` not filtered against `expired`** | **GREEN** (MINOR-2) |
| N14 | no stamp recorded for a carried or expired source | RED `test_the_2026_09_20_incident…` |
| **N15** | **`_surfaces_fed_by` excuses EVERY surface once anything is fed** | **GREEN, 1054 passed** (BLOCKING-1) |
| N16 | `/health` age is always 0 | RED `test_health_names_each_carried_and_expired_source_with_its_age` |
| **N17** | **a refused cycle records no `expired`** | **GREEN** (MINOR-2; either behaviour is unpinned) |
| **N18** | **an unreadable report is read as "all required sources arrived"** | **GREEN** (MINOR-2) |
| N19 | no fallback to the rows' stamp | RED `test_an_unreadable_arrival_falls_back…` |

**Totals:** 28 mutants, 20 RED and 8 GREEN. Every one of the first review's survivors is now killed.

## Findings

### BLOCKING-1 -- the MAJOR-1 fix is not held by any test of the cycle, and the exemption's scope is unpinned

The first review's symptom was a CYCLE that refused every night when `epoch_swe_bench_verified`
expired. The fix is one line at `refresh.py:910`, which feeds `_surfaces_fed_by` (`:803`) into
`degradations`. The only test is `test_refresh_carry.py:222`, and it calls the function directly.
- **N5**, which puts back `frozenset(n for n, s in CATEGORIES.items() if s.primary_source in expired)`
  at `:910`, is **GREEN: 1054 passed**. The fix can be reverted and nothing notices. Every cycle test
  expires `swebench`, and `swebench` is `coding`'s primary source, so the old rule and the new rule
  agree on every cycle any test runs.
- **N15** makes `_surfaces_fed_by` return all 14 surfaces once any benchmark is fed. It is **GREEN**.
  The test asserts only `"coding" in result` and the empty case. It never asserts that a surface
  the source did not feed stays refusable.

So the claim at `test_refresh_carry.py:140`, that every other blinding is still refused, holds only
on a night when nothing expires. On an expiry night the exemption can be widened to every surface,
and the suite stays green. This is the base-pinned Tester profile, §2: a fix without a failing test
of the reported symptom. It is also §1, a test that does not assert what it claims ("every surface
its rows fed", which the test holds only as "at least those").

*Remedy:* add two cycle tests, both through `refresh()`.
1. A live artifact holding `epoch_swe_bench_verified` rows on `coding`'s benchmark, 45 days old,
   with those rows removed from the candidate. Assert that the cycle PUBLISHES. It must go red on N5.
2. The same expiry night, with a surface the source does NOT feed blinded for another reason. Assert
   `EXIT_REFUSED`. It must go red on N15.

### MAJOR-1 -- an expiry excuses the whole surface, so a secondary source's expiry lifts D-128 from the fresh primary source too

`degradations` skips an excused surface entirely (`refresh.py:202`, `:219`), on both the model count
and the budget axis. Since the amendment, a surface is excused when ANY expired source's rows fed its
primary board. That includes a secondary source that contributed a minority of the rows.

**Measured.** Both scenarios are in scratch.
- **S5, fakes, the real `refresh()` and `build.main`.** The live artifact holds one
  `epoch_swe_bench_verified` row on `coding`'s benchmark, 45 days old. `swebench` blinds for a reason
  that is NOT an expiry (its carry is made impossible). The result is **exit 0 "the served content
  changed"**, and the live artifact now has 0 `swebench` rows. Without the 45-day row, the identical
  cycle is exit 3 (this is `test_refresh_carry.py:140`).
- **Served artifact (copy).** `epoch_swe_bench_verified` expires on the same night that `swebench`
  answers with 3 of its 173 rows. Its `minimum_rows` is 1, so the build accepts that.
  - `coding` goes from 44 models to 0.
  - With the wave's `excused={'coding'}`, the result is **PUBLISHES**.
  - Without the exemption, the result is "coding answered with 44 models and would now answer
    nothing", plus three budget lines.
- **All nine `epoch_*` sources expiring together.** This is one Epoch bundle directory gone for over
  30 days. It excuses 8 surfaces, among them `coding`, whose primary source is the REQUIRED `swebench`.

The window is one night per expiry: once the candidate publishes, the expired rows are gone, and the
next night nothing is excused. It needs a coincidence. But on that night it breaks two things:
- D-156 clause 3's own words ("and still refuses every other blinding").
- The first review's stated remedy ("limit the exemption to the loss those rows account for").

The amendment does not state this cost.

*Remedy:* excuse only the loss the expired rows account for. For example, compare against a live
summary computed with the expired sources' rows removed, rather than skipping the surface. Or record
the whole-surface cost in the amendment for the owner to accept. The S5 cycle becomes the test.

### MINOR-1 -- a stamp from the future now EXPIRES a source rather than carrying it, and `/health` prints negative ages

`Carry._age` returns `None` for a negative age (`build.py:225`). The fallback is the rows' own
`observed_at`. But the same clock that wrote the arrival also wrote those rows, so after a clock step
both are in the future, and `age is None` means expired (`build.py:266`).
- **E3b:** rows and arrivals 1 hour ahead, then required `swebench` fails. The result is **exit 2**,
  the live artifact is untouched, and the record says `expired={'swebench': <future stamp>}`.
  `/health` shows **"swebench -0.0d"** under expired. In the first review the same input carried.
- **S9:** `nightly._aged({"a": <2 days ahead>})` gives `"a -2.0d"` (`nightly.py:181` has no guard).

This needs a clock that stepped back by more than the time since the last arrival, which is more
than a day for nightly cycles. When it happens, a required source failing inside that window
freezes the refresh until real time catches up.

*Remedy:* treat a future stamp as age 0 (young, carry), and have `_aged` print `?d` for a negative
age.

### MINOR-2 -- state transitions of the record that no test pins

- **N12:** an UNCHANGED cycle that drops `carried` is GREEN. Unchanged is the ordinary state during
  an outage. In E2 seq2 ("the same failure again"), exit 1 kept `carried` correctly, but nothing
  pins it. The regression would erase the carry from `/health` on every quiet night.
- **N18:** reading an unreadable report as "everything arrived" is GREEN. The docstring's "empty is
  the safe reading" (`refresh.py:782`) is never asserted.
- **S7:** with a torn or deleted report on a served cycle, the record says `carried={}` while the live
  artifact serves the carried `swebench` rows. The clocks stay safe, because arrived is empty. A
  torn report needs a partial write that does not raise, so this is unlikely. A report stale from
  another cycle is impossible by construction: `mkstemp` names are unique and unlinked in `finally`.
- **N13 and N17:** whether a refused cycle records `expired`, and whether `carried` is cleaned
  against it, are unpinned either way.

*Remedy:* one `write_status`-level assertion each for N12 and N13, plus a cycle test with a builder
that deletes the report, asserting that no clock moves and nothing is excused.

### MINOR-3 -- (first review MINOR-4, last bullet, STILL OPEN) the floor gate holds code == record, never record == measurement

`test_floor_rule.py` compares `categories.py` with the research record only. The fix round neither
addressed nor recorded this. Today the record IS the measurement: I regenerated
`survey_boards.py --floors` on a copy of the served artifact, and 14 of 14 surfaces match the
record's `board rows` and `D-148 (rows)` columns. So this is a gate gap, not a wrong floor.

### NIT-1 -- the NIT-3 guard has no test, and it is silent

N10 (guard removed) and N11 (no re-reset) are both GREEN, and `build.py:278-283` is never executed.
In S8 the behaviour is right, but the operator action reads only the source's own error. Nothing
says a carry was attempted and failed. `since` also keeps a stray entry for the source.

### NIT-2 -- after a cycle that is not served, `expired` can list a source whose rows are still served

In E8, the required `swebench` expires, the cycle exits 2, and the live artifact keeps its 2 carried
rows. The record lists swebench under `expired` and drops it from `carried`. The same happens for an
optional source's expiry in a refused candidate. That is defensible (the data is past 30 days), but
the amendment says the record "describes what is SERVED". Say which one `expired` means.

### NIT-3 -- `.sources` scratch file can leak before the `try`

`refresh.py:860` creates the report file. The `.last-ok` `mkstemp` and `json.dump` at `:865-870`
run before the `try` whose `finally` removes both. If either raises (ENOSPC), the `.sources` file
stays. This is the same class as W-124: append it there.

## Tester protocol on load-bearing paths (atomic log)

The load-bearing behaviours I chose:
- the carry clock
- the exemption's two halves
- what the record says is served
- the future-stamp rule
- the carried-insert guard

For each mutant in the table, a mutation script in the session scratch directory did the following:
1. Read the target file and took its md5.
2. Replaced exactly one unique string, refusing if it did not match exactly once.
3. Ran `pytest -n auto` on the copy, with `-x` for the full-suite pass, and without `-x` on the four
   carry test files for the rows that name several tests.
4. Wrote the original bytes back.
5. Asserted the md5 equal.

No restore failed. The repository tree was never mutated: `git status --short` was the same before
and after, apart from this file.

## Gates with this file present

- `.venv/bin/python scripts/check_records.py --root .` gives "check_records PASS [repo]: no findings"
  (exit 0). The self-test gives "self-test PASS: 0 problem(s)".
- `.venv/bin/python conformance/run-all.py` gives "conformance PASS: 14 test(s) derived from
  conformance/, 0 failing" (exit 0).

## What I did not check

- `make swift-test` and `client-decls`. The fix round touches no Swift, and `/v1` is unchanged.
- Any live network cycle, or the real Epoch bundle directory. Every cycle ran on fakes or on copies.
- `wave-check-all`. It fails on the untracked `docs/plans/m16-wave-3-close.md` by design, until its
  review row is filled, and I ignored it as instructed.
- Whether the owner's acceptance quoted in `486b765` was given as written.
- Security aspects (Stage 4.0), and the D-148 floor values beyond the 14-row record comparison above.
- Whether a real NTP step of more than a day is plausible on the owner's Mac (MINOR-1's premise).
