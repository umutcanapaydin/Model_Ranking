---
record_type: review
id: devflow-v7.1-upgrade-rereview
status: draft
process_version: v7.1
date: 2026-10-15
seat: independent
---
# DevFlow v6.6 -> v7.1 upgrade (D-199): independent Code-Reviewer seat, round 2

**Independent:** yes

**Reviewed head:** c87a4b13f95502e2b8aea274c842b6669cd01e1b

**Seat:** the same independent Code-Reviewer seat as round 1 (`docs/reviews/devflow-v7.1-upgrade-review.md`). I
wrote none of the code in the fixes. My policy came from `main` (`.claude/agents/Code-Reviewer.md`,
`.agents/rules/practices.md`, `.agents/rules/review-seats.md`), not from the branch. **Author family / reviewer
family:** Claude / Claude, the same family; no second family was available.

**Subject:** PR #281, branch `upgrade/devflow-v7.1`, commits `18ebafd..c87a4b1`:
- `ff7e315`: the round-1 verdict, committed. I checked that its body is unchanged and that only the
  "Dispositions" table was added after it.
- `fcd0592` (red test) and `c0a97ac` (fix): MAJOR-1.
- `46834a4`: D-200, D-005 and D-006 restored, and the README.
- `cad66fa`: M1.
- `c87a4b1`: the dispositions table.

**Scope:** as asked, I re-verify BLOCKING-1, MAJOR-1, M1 and M3. The other round-1 dispositions are read and
noted. M2 is left to the Security-Reviewer.

**Method:**
- **Own worktree.** A fresh detached worktree at `c87a4b1` in a `mktemp` directory, with its own venv
  (`make install`: marker `v7.1 · manifest a41de86d4696`). `advisor.db` was copied read-only from the author's
  tree, with md5 `495755d517aeb1e6943a8e3fb936658c` before and after.
- **Probes and mutants.** Direct probes of `skip_ledger_problems`. Six in-place mutants, each restored with
  its md5 verified; `git status` was clean afterwards.
- **Full gate.** `make check`.
- I wrote nothing in the author's tree but this file. The worktree is removed.

## Status of the round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| BLOCKING-1 | **closed** (ruled by the owner) | See below. D-200 clause 1 (`docs/decisions.md:5221-5224`) states the ruling and its main cost accurately. D-199 carries `Amended by D-200` (`docs/decisions.md:5203`). The code is unchanged, which is what remedy (c) means. NIT-B is a wording gap in the cost clause. |
| MAJOR-1 | **closed** | `scripts/wave_check.py:750-753`. Tests: `tests/unit/test_wave_check_m21_rules.py:297` and `:308`. Probes and mutants R1, R2 and R5 below. NIT-A is a residual edge. |
| M1 | **closed** | `tests/unit/test_check_records_v1_s1_wiring.py`. R3 (Mu8, the V1 call) and R4 (the S1 call) each fail exactly one of its two tests. |
| M3 | **closed** | Below `## D-005` and `## D-006`, the text at `c87a4b1` equals `main`'s, line for line. The only differences are the added `**Amended at `v7.1`**` blocks (`docs/decisions.md:95,97,119`). "Kept as written" is now true. |
| M2 | open, deferred | Left to the Security-Reviewer seat by the author. I did not re-verify it. |
| NIT 1 | closed | `README.md:1` says v7.1. |
| NIT 2-4 | accepted by the author | As in the dispositions table. Nothing to re-verify. |
| K1 | filed | #282 is open, labelled `bug` and `severity:medium` (`gh issue view 282`). |
| K2-K4 | handed to the owner | -- |
| R1 | accepted, not closed | See NIT-C. |

**BLOCKING-1: what D-200 says, and whether it is accurate.**
- **Context.** It names both changes: a `review` row citing an id resets the count; the rows rewritten from
  `within-scope`, and the row a docs-only commit needs, are such rows; and nothing checks that the cited
  decision exists. Accurate.
- **Clause 1.** It replaces the owner's rule of 2026-10-10 and keeps the rewritten rows. The cost it accepts
  is "one `review` row citing any id clears a struck control, and only a reader of
  `docs/control-events.csv` sees it". Accurate.
- **Mitigation and Revisit.** Both name the right failure signal.
- The ruling itself is the owner's, and I do not re-argue it.

**MAJOR-1: measured at `c87a4b1`.** In each case, a close for `m30-w2` lists `make ui-test` as skipped.

| The ledger holds | Result |
|---|---|
| `ui-test,m30-w1,skip,no simulator` | finding (on `18ebafd` this case was covered) |
| a row for `m30-w2` itself | covered |
| a row marked ``wave was `m30` `` under `m30-w4`, as the upgrade moved them | covered |
| a row marked ``wave was `m30-closure` `` | finding, held by the test at `:308` |

The real ledger has exactly two rows with a milestone-only marker (`docs/control-events.csv:27,28`, both
`m21`). With the moved-row branch removed (R5), `make wave-check-all` fails on one record, so the branch is
both needed and live.

## Mutants (in place in the worktree, each restored, md5 verified)

| # | Mutation | Killing check | Result |
|---|---|---|---|
| R1 | `wave_check.py:753`: drop `and moved in ...` (the fix reverted) | `test_wave_check_m21_rules.py` | **RED**: `test_a_row_for_another_wave_of_the_milestone_does_not_count` |
| R2 | `wave_check.py:750`: `moved = ""` | same | **RED**: same test |
| R3 | `check_records.py`: `findings += version_rule(root)` -> `[]` (Mu8) | `test_check_records_v1_s1_wiring.py` | **RED**: `test_main_reports_a_brief_whose_version_is_not_the_installed_one` |
| R4 | `check_records.py`: `findings += session_numbers(root)` -> `[]` | same | **RED**: `test_main_reports_a_session_number_used_twice` |
| R5 | `wave_check.py:753`: the moved-row branch -> `or False` | `test_wave_check_m21_rules.py`; `make wave-check-all` | **RED** (`:297`) / **RED** (1 record failed) |

All 6 runs turned red: R1 to R4 once each, and R5 against both of its checks.

## New findings

### NITs

- **NIT-A** -- The upgrade's marker can be copied into a new row. `scripts/wave_check.py:750-753` matches
  the marker as free text in the reason, with no date bound.
  - Measured: a row `ui-test,m30-w1,skip,"no sim [rewritten at the DevFlow v7.1 upgrade, D-199: wave was
    `m30`]",2026-11-01` covers `m30-w2`.
  - It takes a deliberately false row, which a reader of the ledger would see, so this is a NIT.
  - *Remedy:* also require the row's date to be on or before 2026-10-15, the upgrade's date. The two real
    rows are dated 2026-10-10.
- **NIT-B** -- D-200's cost clause (`docs/decisions.md:5223-5224`) names the struck-control case only. It
  does not name the case round 1 measured: an in-scope row (the docs-only `review` row the gate requires)
  resets a running count before it reaches three. With four bypasses and one such row between them, nothing
  strikes.
  - The Context paragraph implies it, so this is a wording gap, not an inaccuracy.
  - *Remedy (optional):* one clause, "and a docs-only or red-commit `review` row restarts a running count
    too".
- **NIT-C** -- The dispositions table marks R1 "Closed by D-200 and the MAJOR-1 fix"
  (`docs/reviews/devflow-v7.1-upgrade-review.md:325`). Half of R1's risk (reset by any `review` row) is
  accepted by D-200 clause 1, not closed, and D-200's own Mitigation describes the signal R1 named.
  - *Remedy:* say "MAJOR-1 half closed; BLOCKING-1 half accepted (D-200)".

## Gate result (worktree at `c87a4b1`, macOS, Python 3.14 venv)

`make check` exit 0:
- **session-check:** PASS.
- **ruff:** clean.
- **mypy:** no issues in 49 files.
- **pytest:** 3032 passed, 27 skipped. Coverage 92.19%.
- **coverage-floor:** PASS, 49 modules.
- **check_records:** PASS. Self-test: 0 problems.
- **install-check:** PASS.
- **wave-check-all:** 68 validated, 20 out of scope.
- **conformance:** 26 tests, 0 failing.
- **swift-test:** 637, plus SlowTier 7 of 7.
- **client-decls:** 21 files in 4 configurations.

## Verdict

**PASS WITH FINDINGS** -- 0 BLOCKING, 0 MAJOR, 0 MINOR, 3 NIT.

BLOCKING-1 is closed by the owner's ruling (D-200), and MAJOR-1, M1 and M3 are closed by fixes, each with a
test that kills its mutant. M2 stays with the Security-Reviewer.
