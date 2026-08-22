---
record_type: wave
id: m9-wave-3-close
status: ratified
process_version: v5.0
date: 2026-08-22
---
# Wave-Close Checklist — M9 Wave 3 (unattended: the schedule, the lock, and the three owed tests)

> **CLOSED 2026-08-22.** W3 was planned as "the 12-hour schedule and how a person finds out it
> stopped". It became mostly the three findings an independent seat left behind — which is the
> right order, because a scheduler is what turns concurrency from exotic into ordinary.

## What the wave delivered

Exclusive locking, a refusal counter the record can actually carry, escalation in `runner`, a
`launchd` schedule the owner installs with one command, and tests for the two clauses that were
marked MET without one.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m9-plan.md` §2 records W3 **MED**; re-tiered up in practice under V4C-50, since W-047's fix is concurrency control on the artifact publish path and a concurrency fix takes harsher verification than the defect | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → fault-inject → fix on `src/app/workflows/refresh.py`. The pid-liveness rule came out of writing the SIGKILL test: without it one kill wedges the refresh for two hours | ✅ |
| 3 | Review per tier — V3C-78 / D-122 | **The independent seat ran on W2 and its findings ARE this wave** (`docs/reviews/m9-wave-2-review.md`). W3's own delta has had the author's fault injection and no second seat; recorded as a `control-bypass` under V4C-13 rather than counted as reviewed | WAIVED — PRESSURE, D-122 |
| 4 | Fault injection — V3C-72 | **8 mutants over the W3 delta, 8 killed**, `src/app/workflows/refresh.py` md5-verified restored after each. One needed its anchor corrected — the counter expression spans lines and the first replacement matched nothing, which is a mis-aimed mutant rather than a surviving one | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-REF-005: `runner`'s escalation path plus `tests/unit/test_refresh.py::test_consecutive_refusals_are_counted_and_reset`. W-047: four tests — lock held, dead holder reclaimed, live holder respected, baseline replaced mid-cycle. W-048: a real SIGKILL in a subprocess, and a reader held open across the swap | ✅ |
| 6 | REQ-IDs current in the PRD | `docs/prd.md` REQ-REF-005 **MET agent-side**; REQ-REF-007 **PARTIAL** and honest about which half | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **638 passed / 12 skipped** · `refresh.py` 93% against the 60% per-module floor · ruff, mypy, `check_records`, `wave-check-all` clean · `plutil -lint` on the plist OK | ✅ |
| 8 | ADRs for decisions made | None new; `docs/decisions.md` unchanged by this wave. D-130 already ruled the schedule; this wave implements it. **D-130's claim to answer plan §5.2 "in part" was wrong and is corrected in W-046 rather than in the ADR**, which stays as written | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: **W-046, W-047, W-048 all RESOLVED**. No new warning opened | ✅ |
| 10 | Plan promises delivered | `docs/plans/m9-plan.md` §2 W3 asked for the schedule and the answer to "how does a person find out this stopped". Both delivered; the install itself is one owner command and deliberately not run by the agent | ✅ |

## The two findings this wave should be remembered for

**1. A SIGKILL would have wedged the refresh for two hours, and only writing the test showed it.**
The lock has a staleness threshold so one kill cannot block forever — but two hours on a twelve-hour
schedule is a skipped cycle for a process that is already gone. The lock holder writes its pid, so
a lock belonging to a process that no longer exists is now reclaimed at once. **The test came first
and the design changed because of it**, which is the order this project keeps saying it wants and
rarely gets.

**2. The lock stops two refreshes and cannot stop a person.** `build.py` is a command a human runs,
and an independent seat demonstrated one publishing a score of 95.0 mid-cycle only for the refresh
to overwrite it with its own candidate — a decision that was sound about an artifact which no longer
existed. The baseline is re-read immediately before the rename now, and a cycle that finds it moved
refuses. **Mutual exclusion between the things you control is not the same as knowing the world
held still.**

## What is NOT closed

- **The schedule is not installed.** The plist ships and `launchctl load` is the owner's command;
  loading a background job onto someone's machine is not an agent's decision.
- **REQ-REF-007 is half met**, and the half that is missing cannot be met while the owner's Mac is
  both the serving host and the only host there is.
- **W3's own delta has had no independent seat.** Row 3.

---

Touched: `deploy/com.hcs.modelranking.refresh.plist`, `docs/prd.md`, `docs/warnings.ledger.md`, `runner`, `src/app/workflows/refresh.py`, `tests/unit/test_refresh.py`

K.8 contracts: none moved. `/v1` untouched; D-124's window remains SPENT. `build.py` is CALLED, not modified.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Wave commit range: `1ba8bd9..HEAD`
