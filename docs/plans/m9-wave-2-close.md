---
record_type: wave
id: m9-wave-2-close
status: ratified
process_version: v5.0
date: 2026-08-22
---
# Wave-Close Checklist — M9 Wave 2 (the refusal rule: what an unattended refresh may NOT do)

> **CLOSED 2026-08-22.** The wave the plan called "the one that matters", because this is the
> control that makes unattended operation safe — and it fails in two directions, one of which
> looks exactly like success.

## What the wave delivered

`degradations()` and a fourth outcome. A refresh now REFUSES to publish a candidate that is worse
than what is being served: a surface that would go blind, or any surface losing more than a quarter
of its ranked models (**D-128**). Every cycle writes a durable record beside the artifact
(**D-129**), and `runner` reads it — including how long ago it ran, because a refresh that stopped
entirely is invisible unless something compares a timestamp to a clock.

Verified on the LIVE artifact, not only fixtures: one cycle published, the record was written, and
`advisor.db` still holds its 73 models.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m9-plan.md` §2 records W2 **HIGH** — this is the scoring path's supply line, and a wrong threshold in either direction damages the product silently | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → fault-inject → fix on `src/app/workflows/refresh.py`. The first mutant pass killed 5 of 9 and every survivor was a test defect, not a code defect | ✅ |
| 3 | Review per tier — V3C-78 / D-122 | **WAIVED under PRESSURE**, 2026-08-22, `control-bypass` under V4C-13. `docs/plans/m9-plan.md` §4 requires an independent seat on THIS wave specifically, and it did not run: the owner instructed the session to continue without stopping. **This is the fourth consecutive bypass across M8-M9 and the commitment is recorded as OWED, not as satisfied** — the plan's requirement stands and W3 or closure must discharge it | WAIVED — PRESSURE, D-122, **owed to W2** |
| 4 | Fault injection — V3C-72 | **10 mutants over the W2 delta; 10 killed** after one round of test strengthening. `src/app/workflows/refresh.py` md5-verified restored after each | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-REF-003: `tests/unit/test_refresh.py` — blinded surface refused, 33% loss refused and NAMED, 8% loss published, falling scores published. REQ-REF-004: the record written on published/unchanged/failed/refused, naming the surface, and never left half-written | ✅ |
| 6 | REQ-IDs current in the PRD | `docs/prd.md` REQ-REF-003 and -004 marked MET at this wave | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **620 passed / 12 skipped** · coverage 87.8% against the 85% floor · `refresh.py` at **96%** · ruff, mypy, `check_records`, `wave-check-all` all clean | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-128** (refuse on a blinded surface or a quarter lost), **D-129** (the record is a file and `runner` makes it visible), **D-130** (`launchd`, because a missed trigger must be caught up). All three were the plan's §5 questions, answered in the abstract before a concrete case made them tempting | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` unchanged; no new warning. The wave's defects were test defects and died inside the wave that made them | ✅ |
| 10 | Plan promises delivered | `docs/plans/m9-plan.md` §2 W2 asked for the degradation guard at full depth. Delivered, except the independent seat in row 3 | ✅ |

## The finding this wave should be remembered for

**Three mutants on the threshold survived because the fixture could not reach it.** The `coding`
surface in the shared fixture ranks THREE models — and with three, "loses more than a quarter" and
"loses everything" are the same event. So the shrinkage branch never executed: the test that
believed it was proving the threshold was tripping the blinded-surface branch beside it, and
mutants setting the limit to 100% (refuse nothing) and 0% (refuse everything) both passed.

**A test that reaches the wrong branch proves the wrong rule**, and it reads identically to one
that works. The fix was a twelve-model fixture where one lost model (8%) and four lost models (33%)
fall on opposite sides of the line — which is the second time this milestone that a mutant survived
because of what the DATA could not express rather than what the assertion said.

## What is NOT closed

- **The independent review owed on this wave.** Row 3. Recorded as owed rather than waived away.
- **W3 owns the schedule and the alert channel.** Until then the refusal is recorded and nobody is
  told unless they run `runner`; D-129 states that limit rather than hiding it.
- **`MAX_SURFACE_LOSS` is a judgement, not a measurement.** D-128 says so and names the reasoning;
  it is one constant to move.

---

Touched: `.gitignore`, `docs/decisions.md`, `docs/prd.md`, `runner`, `src/app/workflows/refresh.py`, `tests/unit/test_refresh.py`

K.8 contracts: none moved. `/v1` untouched; D-124's window remains SPENT. `build.py` is CALLED, not modified.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Wave commit range: `6e1d418..HEAD`
