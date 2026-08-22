---
record_type: wave
id: m11-wave-1-close
status: draft
process_version: v5.0
date: 2026-08-22
---
# Wave-Close Checklist — M11 Wave 1 (the reviewer is somebody else)

> **STATUS: CLOSED 2026-08-22.** The first wave in this project's history reviewed by a seat that
> did not write the code and left a file. It returned **BLOCKING — 3 blocking, 5 major, 5 minor**,
> and every blocking finding was in the machinery built to enforce K.7 itself. The rule paid for
> itself inside the wave that created it.

## What the wave delivered

- **D-133** — in the local single-agent lane, K.7 means a separate SESSION reading policy from the
  protected base ref, and the review is a FILE.
- `scripts/wave_check.py::review_seat_problems` — a self-review cannot close a wave green, a waived
  review row must name a ledger row, and a citation to a review that does not exist fails in
  EVERY era.
- `scripts/check_records.py` — `seat` in the schema, `review` and `plan` added to `RECORD_TYPES`,
  two conformance fixtures for R6.
- `.governed-records` — `docs/reviews/` from M8 onward is governed for the first time.
- **W-055 closed** by owner ruling; **W-056 opened and closed** in the same wave.

**Measured at the closing tree:** `make check` exit **0** · **683 Python passed / 12 skipped**
(676 at wave start) · **18 Swift tests** · ruff, mypy, gitleaks clean · `check_records` PASS across
**57** records (50 at wave start) · `wave-check-all` PASS · `conformance-gate` PASS.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m11-plan.md` §3 records W1 **MED** (gate-definition change) | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix in `scripts/wave_check.py`, `scripts/check_records.py`, then a full remediation round against the independent seat's findings | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-wave-1-review.md`, `seat: independent`. Returned BLOCKING; all 3 blocking, all 5 major and 4 of 5 minor are fixed in this wave, and N1 is recorded below as accepted | ✅ |
| 4 | Fault injection — V3C-72 | **8 mutants over the remediated delta, 8 killed**, md5 restore verified on `scripts/wave_check.py`, `scripts/check_records.py`, `.governed-records`. One of them re-disconnects the gate from `main()`, which is the seat's MAJOR-2 | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-REV-001: `tests/unit/test_review_seat_gate.py`, 17 tests including two through the real entry point. The seat ran its own 7-mutant battery and reported 6 of 7 killed by the intended test | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-REV-001 | ✅ |
| 7 | Gates green at the closing tree | figures above, from `make check` at this tree | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-133**, with the owner's attribution clause | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-055 **FIXED** by ruling, W-056 raised and **FIXED**, W-057 opened for N1 | ✅ |
| 10 | Plan promises delivered | `docs/plans/m11-plan.md` §3 W1 — all three items | ✅ |

## The three findings this wave should be remembered for

**1. Two absences cancelling into a green gate.** `record_type: review` was missing from
`RECORD_TYPES`, and `.governed-records` never named `docs/reviews/`. Either alone would have been
loud; together they were silent, because the 44 files carrying the illegal type were never scanned.
Adding `seat` to the schema without noticing would have made D-133's own mandated frontmatter
**unrepresentable**: declare `review` and R2 fires, declare anything else and R6 fires.

**2. A fix that hid the record it was fixing.** The broken-citation check ran *after* the
`WAIVED`/`SKIPPED` early exit. The W-056 remediation then set the offending row to WAIVED — and
dropped the `docs/reviews/` prefix the citation regex needs. The record that motivated this entire
gate became invisible to it, twice over, by way of its own fix. The scan now runs on every line in
every era before any status filter.

**3. A gate that was never reached through the command that runs it.** Every test called
`review_seat_problems` directly, so disconnecting it from `main()` left pytest, `wave_check_all.py`
and `check_records.py` all green. *A control cited but not run* — inside the wave built to stop
exactly that. Two end-to-end tests now go red when it is unwired, and a mutant proves it.

## What is NOT closed

- **W-057 (N1)** — `milestone=None` cannot occur through `main()`, which rejects any name the
  milestone regex would not match. The parametrised case pins a state the entry point cannot
  produce. ACCEPTED: the direction (unknown era ⇒ strictest rules) is what the comment claims, and
  removing the case would make the function's contract depend on its only caller.
- **The gate does not prove independence and does not claim to.** D-133 says so in its own text.
- W-030, W-031, D-123, W-035, W-036, W-039, W-044, W-053, W-054 — carried, unchanged by this wave.

---

Touched: `.governed-records`, `AGENTS.md`, `.agents/rules/practices.md`, `conformance/fail/bad-seat.md`, `conformance/fail/seat-on-nonreview.md`, `docs/decisions.md`, `docs/plans/m11-plan.md`, `docs/plans/m11-wave-1-close.md`, `docs/plans/m8-wave-5-close.md`, `docs/prd.md`, `docs/reviews/m11-wave-1-review.md`, `docs/warnings.ledger.md`, `scripts/check_records.py`, `scripts/wave_check.py`, `tests/unit/test_review_seat_gate.py`

K.8 contracts: `scripts/wave_check.py::review_seat_problems` is NEW and every wave close now depends on it. `.governed-records` widened — `docs/reviews/m8-*`, `m9-*`, `m1[0-9]-*` are governed records for the first time. Frozen surfaces untouched: `/v1` payload, CLI vocabulary, refresh exit codes, D-104.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Wave commit range: `1069907..HEAD`
