---
record_type: wave
id: m16-wave-3-close
status: draft
process_version: v6.0
date: 2026-09-23
---
# Wave-Close Checklist — M16 Wave 3, numbers that follow one rule

**A source outage no longer blanks the surfaces that source feeds, and every floor follows one rule.**
Every source carries its last good data for 30 days from its last served arrival (D-156, W-116);
past that its surfaces drop and the refresh publishes the rest instead of refusing. Every floor is the
top third of its board's rows (D-148), re-derived from the served artifact; one pick changed, as the
owner ruled.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m16-plan.md` §2 W3 "(risk: **MED**)"; branch plan `docs/plans/m16-wave-3-plan.md` (deleted before merge) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Each phase red-first in its own commit, then green: `test_carry_forward.py` (P1), `test_refresh_carry.py` (P2), `test_nightly_refresh.py` (P3), `test_survey_floors.py` (P4), `test_floor_rule.py` (P6). `/repo-review` after P1 found two defects (a non-JSON `Infinity`, an untested Epoch carry path), both fixed with tests. `make check` at `dcc68fa`: pytest 1067 passed / 15 skipped, Swift 268, conformance 14 PASS, client-decls PASS | ✅ |
| 3 | Review per tier: MED → ONE combined reviewer | Three rounds, each by an independent seat (`seat: independent`). `docs/reviews/m16-wave-3-review.md`: BLOCKING (2 BLOCKING, 3 MAJOR), fixed in `f2e29ff`. `docs/reviews/m16-wave-3-rereview.md`: BLOCKING (the exemption excused whole surfaces), fixed in `ea41412..a061dfc` by judging an expiry night against the live artifact minus the expired rows (`refresh._served_without`). `docs/reviews/m16-wave-3-rereview-2.md`: **PASS-WITH-MINORS**, no BLOCKING or MAJOR; its three MINORs fixed red-first in `08a0658..dcc68fa`, its two NITs recorded there | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | Not owed at MED. The one security-relevant edge, opening the live artifact from the build, uses `open_readonly` (INV-23) -- caught by `tests/unit/test_readonly_uri.py` when a hand-built URI was first written | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | Author mutants, each restored byte-identical by an md5-checked script: in `src/app/workflows/build.py` the age limit ignored, a required source not carried, rows not copied, the Epoch board path not carried; in `src/app/workflows/refresh.py` the D-128 exemption removed, a carried source counted as arrived, a refused cycle counted as an arrival (this one survived first and got `test_only_a_served_cycle_counts_as_an_arrival`). All RED. Fix rounds, same protocol: the baseline replaced by live, deleting every row, the median judged against live, pricing rows kept, `px_median` not re-derived, the carried-insert guard removed or not re-resetting, the future-stamp clamp removed or unbounded, the names guard on the baseline, the blind-median fallback removed (this one survived first and got `test_an_expiry_night_does_not_admit_a_price_jump_either`). All RED. The independent sets are in the three reviews | ✅ |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint | REQ-REF-009 (`docs/prd.md`): `tests/unit/test_refresh_carry.py` runs the real `refresh()` with the real `build.main`; `test_carry_forward.py` drives `build()` and `build.main`. D-148 floors: `tests/unit/test_floor_rule.py` against `categories.py` | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | No new invariant. INV-23 (read-only artifact access) is reused, and its gate (`tests/unit/test_readonly_uri.py`) fired on this wave's first draft; the new baseline `refresh._served_without` also opens the served file through `open_readonly` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | **One, disclosed in session when it happened.** A narrow `ruff --fix --select` stripped needed `noqa` comments from `scripts/client_decl_gate.py` and `scripts/journey.py`; `git checkout HEAD --` restored the two files. The autofix was the only uncommitted change in either file, so nothing else was lost, but it is the command this row forbids. After that, every mutant was restored from a byte copy and md5-compared by script | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Where a source's rows can come from, enumerated in `build.py`: a fresh fetch, or `Carry.restore` from the live artifact at the three failure sites (`_ingest_sources`, `_ingest_bundles`, `_ingest_boards`), each with a test | ✅ |
| 9b | Scope & draft PR | Draft PR #3. Planned vs delivered: all six phases delivered. Deferred with a record: W-127 (six surfaces' tie margins follow an interval rule D-148 clause 2 does not name) and W-128 (the floor record is compared with code, not with a fresh measurement), both to the M16 closure; W-124 extended with the `.last-ok`/`.sources` scratch files | ✅ |
| 9a | Economy | `git diff --shortstat df4bfc7..dcc68fa`: 23 files, +2610/−69, of which tests and records are +2103/−16 (three review files alone are over 900 lines). Code: about +500. VARIANCE noted: two features and a measurement in one wave, as the milestone plan grouped them, and three review rounds | ✅ |
| 9 | Skipped/waived ledger + run summary | `gates run: make check (pytest 1067/15, Swift 268, conformance 14 PASS, client-decls, check-records, wave-check-all) · make falsify deps slopsquat PASS · make secrets FAILED on an UNTRACKED file in the owner's working tree (`epb.html`, 2 generic-api-key findings; not in the branch, not written by this wave), escalated to the owner; the branch itself: gitleaks detect --log-opts origin/main..HEAD, 22 commits, no leaks · gates SKIPPED: none · outcome: draft PR #3, owner merges` | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-09-23 · Wave commit range: `df4bfc7..dcc68fa`

## Wave footprint — RECORD ONLY

```
Touched:        src/app/workflows/{build,refresh,categories,recommend}.py · src/app/adapter/nightly.py
                scripts/survey_boards.py · tests/unit/test_{carry_forward,refresh_carry,survey_floors,
                floor_rule,nightly_refresh,categories,recommend_assistant}.py
                docs/{decisions,prd,warnings.ledger}.md · docs/research/m16-w3-floor-table-2026-09-23.md
Mutant set author: the lead agent (self-designed, supporting evidence only) and the independent seat
                (docs/reviews/m16-wave-3-review.md)
Observed RED:   refresh.py `if code in (EXIT_PUBLISHED, EXIT_UNCHANGED)` -> `if True` failed
                test_only_a_served_cycle_counts_as_an_arrival[2] and [3]: a refused and a failed cycle
                moved the arrival time
Owner instruction: "if its data does not arrive, its last data stays valid. If the data is about a
                month old, the list drops. If the data updates within that month, nothing happens and it
                joins the calculations." (D-144 ruling, translated from Turkish) -- delivered as D-156.
                And D-148: "every row in the list" -- delivered as the rows-rule floors.
K.8 contracts:  /v1 unchanged (D-156 clause 4). /health gains refresh_carried, refresh_expired
                (additive). The refresh record gains sources_last_ok, carried, expired. build.main gains
                --carry-from and --last-ok.
Closure rounds: (filled at the M16 closure)
Hand-kept lists: NONE added. The floors are compared with the measurement record by a test, not kept
                by hand beside it.
```
