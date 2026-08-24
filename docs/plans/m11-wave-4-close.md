---
record_type: wave
id: m11-wave-4-close
status: ratified
process_version: v5.0
date: 2026-08-23
---
# Wave-Close Checklist — M11 Wave 4 (closure)

> **STATUS: CLOSED 2026-08-23.** Stage 4.0 returned **CONDITIONAL PASS** from a seat that wrote
> none of the code — the first closure review in this project's history run under D-133. The
> blocking finding was in the K.7 gate itself, which could be switched off by renaming a table cell.

## What the wave delivered

- **Stage 4.0 security review** across `1069907..HEAD`: `docs/reviews/m11-security-review.md`,
  `seat: independent`. 1 BLOCKING, 2 MAJOR, 10 MINOR.
- **W-072 fixed** — the seat gate no longer asks about row labels; the rule is record-level.
- **W-073 fixed** — `scripts/simulator_session.sh` actually stops the engine it started.
- **W-074 escalated** — no shell linting anywhere in this repository.
- **Capture** — `docs/retrospectives/m11-retrospective.md`, `docs/process-log.md`,
  `docs/EXPERIENCE.md`, `docs/plans/m12-inputs.md`, `docs/closure-report-m11.md`, `note.txt`.

**Measured at the closing tree:** `make check` exit **0** · **714 Python passed / 12 skipped** ·
**59 Swift tests** · ruff, mypy, gitleaks clean · `check_records` PASS across **61** records ·
`coverage-floor` PASS · `wave-check-all` PASS (19 v5.0) · `conformance-gate` PASS.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m11-plan.md` §W4 records **LOW** for the wave; the REVIEW it runs was scoped to the whole milestone surface | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Reproduce → fix → prove in `scripts/wave_check.py` and `scripts/simulator_session.sh`; both findings were reproduced before being fixed and re-proven after | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-security-review.md`, `seat: independent`, run under D-133 by a session that authored none of the code | ✅ |
| 4 | Fault injection — V3C-72 | The seat ran 4 mutations and restored all 4 with md5 verified. This wave's own repairs were proven against 4 row labels and 19 real records (`scripts/wave_check_all.py`) | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | `tests/unit/test_review_seat_gate.py` grew to 20, including `test_renaming_the_review_row_cannot_switch_the_gate_off` and its fixture-blindness pair | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | None new at W4. `docs/prd.md` REQ-RUN-002 was ADDED here and marked **NOT MET** rather than backfilled — it was a W3 promise that never became a row (W-071) | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · 714 passed / 12 skipped · 59 Swift · `scripts/check_records.py` PASS (61) · `scripts/wave_check_all.py` PASS (19) · `scripts/conformance_gate.py` PASS · `scripts/coverage_floor.py` PASS | ✅ |
| 8 | ADRs for decisions made | None new at W4; `docs/decisions.md` D-133 (W1, K.7 in a single-agent lane) and D-134 (W3, a sibling resource is not a payload revision) are this milestone's rulings | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — 27 closed this milestone, W-072/W-073 fixed here, W-074 escalated | ✅ |
| 10 | Plan promises delivered | `docs/plans/m11-plan.md` — W1, W2, W3, W3.5, W4 delivered; **REQ-RUN-002 NOT delivered** and named in the closure report §0.2 rather than left to be noticed | WAIVED — ledgered as W-071, owner action |

## The finding this wave should be remembered for

**A gate whose scope is set by free text a filler chooses is a gate the filler can switch off
without meaning to.** The K.7 seat gate found its subject by grepping a row's NAME cell. Rename row
3 to "Fresh eyes per tier" and the gate skipped the record entirely — reproduced against a copy of
a real wave-close record, exit 0, no review cited and none in existence. `AGENTS.md` and the
function's own comment both claimed it could not pass silently.

The test written to catch exactly this used the label `Fresh-eyes code REVIEW`, which still
contains the word. It proved case-insensitivity and not label-independence: **fixture blindness in
the test guarding the gate guarding the reviews.**

The repair was not a longer list of labels. The question moved to one the record answers as a
whole — cite an independent review, or name the ledger row for the bypass — and neither half can be
renamed away.

## What is NOT closed

- **REQ-RUN-002 / W-071 / W-054** — the refresh has never run unattended. Owner command.
- **W-074** — no shell linting. Gate-definition change, owner's.
- **W-058** — `/health.evidence` in the deploy gate, waiting on a deploy.
- **D-123 / W-030 / W-031** — nothing deployed, fourth milestone.
- **W-057, W-060, W-035, W-036, W-040** — carried with reasons.

---

Touched: `docs/EXPERIENCE.md`, `docs/closure-report-m11.md`, `docs/plans/m11-wave-4-close.md`, `docs/plans/m12-inputs.md`, `docs/prd.md`, `docs/process-log.md`, `docs/retrospectives/m11-retrospective.md`, `docs/reviews/m11-security-review.md`, `docs/warnings.ledger.md`, `note.txt`, `scripts/simulator_session.sh`, `scripts/wave_check.py`, `tests/unit/test_review_seat_gate.py`

K.8 contracts: `scripts/wave_check.py::review_seat_problems` changed from a row-level to a RECORD-level rule — every v5.0 wave close now depends on it differently. Frozen surfaces untouched: `/v1` payload (verified byte-identical), D-104, refresh exit codes.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-23 · Wave commit range: `9178a73..HEAD`
