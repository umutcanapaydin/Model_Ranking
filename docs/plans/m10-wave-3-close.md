---
record_type: wave
id: m10-wave-3-close
status: draft
process_version: v5.0
date: 2026-08-22
---
# Wave-Close Checklist — M10 Wave 3 (the guards, and the name that was only half a name)

> **STATUS: CLOSED 2026-08-22.** Three carried warnings discharged (W-037, W-050, W-051). The
> wave's finding is not any of the three guards; it is that **the accessor REQ-EVI-002 asked for
> already existed and the defect it was written against was still running** — in
> `scripts/arena_calibration.py`, the script whose entire purpose is to recompute a calibration
> record. A name is not a control until something is required to call it.

## What the wave delivered

- **REQ-GRD-002** — an aggregate row bound across pages: `src/app/clients/arena.py`,
  `_MAX_MERGED_ROWS = 2_000`.
- **REQ-GRD-003** — environment assumptions become checks: `src/app/workflows/refresh.py`,
  `environment_problems` plus a NaN-safe `write_status`.
- **REQ-EVI-002** — the ranked population is named AND reached:
  `src/app/workflows/rank.py::ranked_population`, `scripts/arena_calibration.py`.

**Measured, not reported:** `make check` exit **0** · **660 passed / 12 skipped** (655 at wave
start) · ruff, mypy, gitleaks clean · `check_records` PASS across 47 records · `coverage-floor`
PASS (33 modules) · `wave-check-all` PASS (15 v5.0 records) · `conformance-gate` PASS.

Fault injection (V3C-72, mutate in place, confirm RED, restore, verify md5, `python -B`):
**9 mutants over the wave delta, 9 killed.** Six on the guards, three on REQ-EVI-002 — including
one that gives the calibration script its own SQL again, which is the shape W-037 records.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m10-plan.md` §W3 records **MED**: bounds on an untrusted remote reader plus a refusal path, no scoring-path change (D-122) | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix on each of the three, in `src/app/clients/arena.py`, `src/app/workflows/refresh.py` and `scripts/arena_calibration.py`. The row bound was written twice: the first value was arithmetically unreachable | ✅ |
| 3 | Review per tier — V3C-78 | Single combined pass at MED under D-122 (`docs/decisions.md` D-122), plus the author's fault injection below | ✅ |
| 4 | Fault injection — V3C-72 | 9 mutants, 9 killed, md5 restore verified on `src/app/clients/arena.py`, `src/app/workflows/refresh.py`, `scripts/arena_calibration.py`. Three of them re-introduce W-037 into the calibration script | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-GRD-002: `test_arena_client.py` row-cap and page-cap tests · REQ-GRD-003: `test_refresh.py` environment tests · REQ-EVI-002: `tests/unit/test_ranked_population.py`, five tests | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-GRD-002, REQ-GRD-003, REQ-EVI-002 all marked **W3 DONE** with their citing files | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · 660 passed / 12 skipped · `scripts/check_records.py` PASS (47) · `scripts/coverage_floor.py` PASS (33) · `scripts/conformance_gate.py` PASS | ✅ |
| 8 | ADRs for decisions made | None new. The two bounds' relationship is recorded in place at `src/app/clients/arena.py` and in W-050 (`docs/warnings.ledger.md`) rather than as an ADR — it is an arithmetic fact about one client, not a project ruling | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-037, W-050, W-051 all **FIXED**, each carrying the file that discharges it | ✅ |
| 10 | Plan promises delivered | All three W3 items in `docs/plans/m10-plan.md` §W3; nothing deferred out of this wave | ✅ |

## The three findings this wave should be remembered for

**1. A bound placed where nothing can reach it.** The first row cap was 5,000. `_MAX_PAGES` is 50
and `_PAGE` is 100 — the page walk cannot produce 5,000 rows, so the new guard was decorative. It
was caught by trying to write a test that fires it, not by reading it. This is the same family as
*a control cited but not run*, one level further in: **a control that runs and cannot trigger.**

**2. Fixing one bound broke the other's test — honestly.** With a reachable row cap, full pages
trip 2,000 rows at page 21 and a short page ends the walk, so `_MAX_PAGES` is now unreachable in
normal operation. The test does not pretend otherwise: it raises the row bound to reach the page
cap, and says in place that this is the only honest way to exercise a backstop. The alternative —
a fixture quietly shaped to make the guard look live — is the *fixture blindness* defect this
project has now recorded seven times.

**3. The record's own tool carried the defect the record describes.** W-037 says thresholds were
calibrated against the wrong population three times. `scripts/arena_calibration.py` — written to
make that record recomputable — was still computing its cut table and value-window sizing from the
raw board. The named accessor had existed since M9 and nothing was required to call it. **A name
without a caller is a glossary entry.** The gate now fails any script under `scripts/` that sizes
a threshold without importing `ranked_population` (V4C-49: ship the gate with the rule).

## What is NOT closed, stated rather than implied

- **W-030 / W-031** — still need a deploy; nothing is on Fly.io (D-123, undischarged for a third
  milestone).
- **W-035, W-036, W-038, W-039, W-044** — carried into W4 with reasons.
- **The 12-hour schedule is still not loaded.** `launchctl load` is the owner's command and is
  deliberately deferred until the coding is done (owner ruling, 2026-08-22).
- **GPF-001..006** — handed back to General_Pipeline, not this project's to close.

---

Touched: `docs/plans/m10-wave-3-close.md`, `docs/prd.md`, `docs/warnings.ledger.md`, `scripts/arena_calibration.py`, `src/app/clients/arena.py`, `src/app/workflows/refresh.py`, `tests/unit/test_arena_client.py`, `tests/unit/test_ranked_population.py`, `tests/unit/test_refresh.py`

K.8 contracts: `app.workflows.rank.ranked_population` (now load-bearing — a gate requires callers), `app.clients.arena._paginate` bounds. Frozen surfaces untouched: `/v1` payload (D-115/D-125), CLI vocabulary (D-118), refresh exit codes (D-129).

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Wave commit range: `dc8e19e..HEAD`
