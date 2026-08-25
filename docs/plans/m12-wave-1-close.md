---
record_type: wave
id: m12-wave-1-close
status: draft
process_version: v5.0
date: 2026-08-25
---
# Wave-Close Checklist — M12 Wave 1 (foundations that were false)

> **STATUS: CLOSED 2026-08-25.** Four things this repository asserted and did not have. First in
> the milestone because everything after it is written on top of them — and because a K.8 line
> naming a frozen contract that does not exist gets copied into the next plan, and the one after.

## What the wave delivered

- **D-119 and D-120 written**, dated today, describing contracts in force since M6. Thirty files
  cited them; `decisions.md` went D-118 → D-121.
- **`tests/unit/test_adr_citations.py`** — the gate ships with the rule (V4C-49). Fails any
  citation to an unwritten ADR in the project band, and any unexplained gap in the numbering.
- **`make gate` exits 0** on a clean tree for the first time.
- **`C2b` counts controls and can be discharged.** `tests/unit/test_c2b_counter.py`, 9 tests.
- **The Turkish case-folding defect fixed before Turkish ships**, with the test that catches its
  regression rather than the tests that merely describe the property.

**Measured at the closing tree:** `make check` exit **0** · `make gate` exit **0** ·
**726 Python passed / 12 skipped** (714 at wave start) · **64 Swift tests** (59 at start) ·
ruff, mypy, gitleaks clean · `check_records` PASS across 68 records · `check-records-selftest`
PASS · `wave-check-all` PASS · `conformance-gate` PASS.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m12-plan.md` §3 records W1 **MED** (gate-definition changes plus a shipped-behaviour fix) | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Reproduce → fix → prove on each of the four: `docs/decisions.md`, `Makefile`, `scripts/check_records.py`, `ios/ModelRanking/Engine/Router.swift`. Every finding was measured before it was fixed | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-council-senior-swe.md` and `docs/reviews/m11-council-senior-mobile.md`, both `seat: independent` — this wave implements THEIR findings, so the review preceded the code | ✅ |
| 4 | Fault injection — V3C-72 | **13 mutants, 13 killed** across `docs/decisions.md` (3), `scripts/check_records.py` (4), `ios/ModelRanking/Engine/Router.swift` (3, then 2 re-run), md5 restore verified on every file | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-GOV-001: `tests/unit/test_adr_citations.py`, `tests/unit/test_c2b_counter.py`, and the rewritten `--self-test` probe · REQ-LOC-002: `ios/EngineTests/OwnerSessionDefectTests.swift` | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-GOV-001 and REQ-LOC-002, both marked DONE with their citing files | ✅ |
| 7 | Gates green at the closing tree | figures above, from `make check` and `make gate` at this tree | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-119**, **D-120** — written, not decided: they record decisions taken at M6 | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-076, W-077, W-078, W-079 raised and **FIXED** | ✅ |
| 10 | Plan promises delivered | `docs/plans/m12-plan.md` §W1 — all five items | ✅ |

## The three findings this wave should be remembered for

**1. A test can be blind to its ENVIRONMENT, not just its data.** The Turkish fix was made, tested
four ways, and a mutant restoring `Locale.current` still passed every one of them — because this
machine's process locale folds like English, so the wrong implementation returns the right answer.
The behavioural tests described the property and could not detect its loss. Only asserting the
CHOICE — a named `filterLocale` constant — kills it. **Twelve milestones of fixture blindness in
this project have been about data; this one was about the room.**

**2. A finding that cannot be discharged is an alarm, not a control.** `C2b` was rebuilt to count
controls rather than provenance, and the second half matters as much: naming the ADR that reviewed
the control satisfies it. K.7 reached three, the control was reviewed, D-133 is the outcome, and
the rows that cite it pass. A trigger with no way to say *"done, here it is"* gets silenced, and the
silencing is never the part that gets recorded.

**3. A council finding is evidence, not a verdict.** The seat that found D-119/D-120 also reported
P-002 and P-003 as phantoms citing 7 and 5 files. They are reserved mirrors, explained in
`decisions.md` itself, and every "citation" was the substring `P-002` inside `REQ-APP-002`. Caught
by re-measuring with word boundaries **before** writing two ADRs that already had a status. The
gate now matches on word boundaries and says why (W-077).

## What is NOT closed

- **The `3` divergence** in the exit-code contract is recorded in D-120 as known, not resolved.
  Both consumers already depend on their number; changing one to tidy a document would break a
  caller. It needs a migration and belongs in a plan.
- **W-074** — no shell linting. Offered to the owner and declined; stays open by his decision.
- W-057, W-058, W-060, W-030, W-031, W-035, W-036, W-040, W-054 — carried.

---

Touched: `Makefile`, `docs/decisions.md`, `docs/plans/m12-wave-1-close.md`, `docs/prd.md`, `docs/warnings.ledger.md`, `ios/EngineTests/OwnerSessionDefectTests.swift`, `ios/ModelRanking/Engine/Router.swift`, `scripts/check_records.py`, `tests/unit/test_adr_citations.py`, `tests/unit/test_c2b_counter.py`

K.8 contracts: **D-119 and D-120 now exist** — the frozen CLI exit-code contract 26 files already deferred to is finally readable, with its one divergence named. `C2b`'s key changed from provenance to control identifier; any record asserting it fired before today was asserting something impossible. Frozen surfaces untouched: `/v1` payload, D-104, the refresh exit codes (D-120 documents them, does not move them).

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25 · Wave commit range: `d13c810..HEAD`
