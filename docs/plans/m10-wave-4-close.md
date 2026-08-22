---
record_type: wave
id: m10-wave-4-close
status: draft
process_version: v5.0
date: 2026-08-22
---
# Wave-Close Checklist — M10 Wave 4 (closure)

> **STATUS: CLOSED 2026-08-22.** Stage 4.0 returned **BLOCKING**, and the blocking finding was a
> defect this repository had already fixed once and written a docstring about. It is fixed, gated
> and recorded as W-052. Nothing deploys at this milestone, so 4.3 does not run and D-123 stays
> undischarged for a third milestone — stated, not implied.

## What the wave delivered

- **Stage 4.0 security review** over the whole M10 surface: `docs/reviews/m10-security-review.md`.
  One BLOCKING (fixed), three MINOR (ledgered as W-053, W-054).
- **The one definition of a read-only artifact handle**: `src/app/workflows/schema.py::open_readonly`,
  called by the adapter, the refresh and the calibration script.
- **The gate that stops it recurring**: `tests/unit/test_readonly_uri.py` — a case per measured
  bypass, a fixture-blindness guard, and an `ast` check across `src/` and `scripts/`.
- **Capture**: this record, `docs/closure-report-m10.md`, `docs/retrospectives/m10-retrospective.md`,
  `docs/process-log.md`, `docs/EXPERIENCE.md`, `note.txt`.

**Measured at the closing tree:** `make check` exit **0** · **666 passed / 12 skipped** ·
ruff, mypy (33 files), gitleaks clean · `check_records` PASS across 48 records ·
`coverage-floor` PASS · `wave-check-all` PASS · `conformance-gate` PASS.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m10-plan.md` §W4 records **LOW** for the wave; the REVIEW it runs was tiered **HIGH** in `docs/reviews/m10-security-review.md` because the milestone added an on-device model in front of the catalogue | ✅ |
| 2 | Dev-test loop ran — V3C-68 | The blocking finding went reproduce → fix → gate → fault-inject inside this wave: `src/app/workflows/schema.py`, `tests/unit/test_readonly_uri.py` | ✅ |
| 3 | Review per tier — V3C-78 | `docs/reviews/m10-security-review.md`. **K.7 NOT satisfied** — self-review, declared in the record's own header rather than left for a reader to notice. This is the FOURTH such bypass; `C2b` fired at M8 and named M9 as when the CONTROL would be reviewed, and M9 closed without doing it | WAIVED — NO-ENVIRONMENT (no second seat in this session); ledgered as W-055 |
| 4 | Fault injection — V3C-72 | 3 mutants on the fix in `src/app/workflows/schema.py` and `src/app/workflows/refresh.py`, 3 killed, md5 restore verified. 12 mutants across M10-W3 and W4 in total, 12 killed | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | `docs/coverage-by-req.md` trace below; every M10 REQ-ID names its citing file | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` — REQ-RTR-001..004, REQ-ANM-001, REQ-GRD-002, REQ-GRD-003, REQ-EVI-002, all added at their own wave | ✅ |
| 7 | Gates green at the closing tree | figures above, from `make check` at this tree | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` D-132 (upward-anomaly axis) at W2. None new at W4: the read-only construction is an invariant (INV-23) that already existed, and re-ruling it would imply it was ever in doubt | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-037, W-050, W-051 **FIXED**; W-052 **FIXED**; W-053, W-054 **ACCEPTED** with owning milestone M11 | ✅ |
| 10 | Plan promises delivered | `docs/plans/m10-plan.md` §3 — all four waves. The one plan item NOT delivered is the schedule being loaded, which the plan assigns to the OWNER | ✅ |

## The finding this wave should be remembered for

**A fix that lives in one module is not a fix.** The correct read-only construction, and a
docstring describing precisely what goes wrong without it, had been in `adapter/main.py` since M6.
Three milestones later a new module wrote the broken form back — with a comment defending the
choice. The defence was half-right: the refresh genuinely must not import the adapter (D-116,
REQ-REF-007). What made it a defect is that "avoid a dependency" was allowed to justify a private
copy of a security-relevant construction, when the available third option — move the definition
somewhere both may reach — satisfied both rules at once.

The generalisable form, and it is new to this project's taxonomy: **a boundary rule and a
single-definition rule will eventually collide, and the collision is always resolved by moving the
definition, never by duplicating it.** A duplicate is how a boundary rule silently converts into a
correctness bug three milestones downstream.

## What is NOT closed

- **D-123 / W-030 / W-031** — nothing is deployed. Third milestone. Stage 4.3 did not run.
- **W-053, W-054** — accepted, owned by M11.
- **W-035, W-036, W-038, W-039, W-044** — carried, reasons unchanged.
- **The 12-hour schedule is not loaded.** `launchctl load -w deploy/com.hcs.modelranking.refresh.plist`
  is the owner's, and W-054 records that every M10 security verdict describes code rather than
  operation until it runs.
- **GPF-001..006** — General_Pipeline's, handed back.

---

Touched: `docs/closure-report-m10.md`, `docs/plans/m10-wave-4-close.md`, `docs/process-log.md`, `docs/retrospectives/m10-retrospective.md`, `docs/reviews/m10-security-review.md`, `docs/warnings.ledger.md`, `note.txt`, `scripts/arena_calibration.py`, `src/app/adapter/main.py`, `src/app/workflows/refresh.py`, `src/app/workflows/schema.py`, `tests/unit/test_readonly_uri.py`

K.8 contracts: `app.workflows.schema.open_readonly` is NEW and load-bearing — every read-only artifact handle in the repository goes through it, enforced by a gate. `adapter.main.open_readonly` keeps its name and INV-23 docstring and now delegates. Frozen surfaces untouched: `/v1` payload (D-115/D-125), CLI vocabulary (D-118), refresh exit codes (D-129), D-104.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Wave commit range: `dc8e19e..HEAD`
