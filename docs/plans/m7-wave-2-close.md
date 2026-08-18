---
record_type: wave
id: m7-wave-2-close
status: draft
process_version: v5.0
date: 2026-08-18
---
# Wave-Close Checklist — M7 Wave 2 (the medians leave the read path)

> **STATUS: CLOSED 2026-08-18.** Scoring path, so FULL depth under **D-122**. The wave's whole
> claim is that the engine computes exactly what it computed before while no longer writing, and
> that claim is settled by a value-for-value comparison rather than by a green suite.

## What the wave delivered

`recommend()` called `build_price_medians`, which runs `DELETE FROM px_median` + `INSERT`. A read
API rewrote an operator table on every request and could not be driven from a read-only handle at
all — the defect **W-017** contained and D-116 named a condition of go-live. The medians were only
ever persisted at READ time because there was no BUILD time to persist them at; W1 created one.

**Parity, measured against a baseline captured before the change:**

| Property | Result |
|---|---|
| Price medians | **72 models, identical value for value** |
| Recommendation output | **9 of 9 shapes byte-identical** (3 tasks × 3 budgets) |
| Connection used | **read-only** — impossible before this wave |
| Database after 5 requests | byte-identical |

## The door this wave opened, closed in the same wave

With the build elsewhere, an artifact can reach the serving path with `px_median` empty, and
`rank.py` JOINs that table — zero rows, `recommend()` returns None, `/v1` answers **200 with no
picks**. That is precisely the artifact W-023 shipped. Four boundaries now refuse instead:

- `require_price_medians` raises and names the build command;
- the **startup probe** gains a fourth check, so the process will not BOOT on an unservable
  artifact rather than failing per request;
- the **CLI exits 2, not 1** — exit 1 means "no model fits this budget", a RESULT computed from
  evidence, and telling an operator their budget was too tight when the database was never finished
  is the same false-cause defect at a different boundary;
- **`/v1` returns 503** `evidence_unavailable`, the class M6 already defined for a database it
  cannot read, and deliberately does not publish the remedy to callers.

| # | Check | Evidence | ✅ |
|---|---|---|---|
| 1 | Risk tier — V3C-78 / D-122 | Scoring path ⇒ FULL depth. `rank.py`, `recommend.py` and the `/v1` error contract all changed | ✅ |
| 2 | REQ-CAN-003 unchanged, value for value | 72 medians and 9 recommendation shapes identical against a pre-change baseline (`src/app/workflows/rank.py::build_price_medians`, called from `src/app/workflows/build.py`) | ✅ |
| 3 | REQ-API-008 has citing tests able to fail | `test_unbuilt_evidence.py` (8 tests), `test_api_v1.py::test_an_unbuilt_artifact_is_refused_rather_than_answered_empty`, `test_cli_e2e.py::test_cli_an_unbuilt_artifact_exits_2_not_1` | ✅ |
| 4 | Fault injection — V3C-72 | `m7w2_lead_faultinject.py`: 11 mutants, 7 killed first pass; all four survivors given mandatory tests in `tests/unit/test_unbuilt_evidence.py`; **11/11** after | ✅ |
| 5 | Gates green | `make check` exit 0 · 483 passed / 12 skipped | ✅ |
| 6 | Tests whose MEANING changed are documented as inversions | Three, in `tests/unit/test_recommend.py`, `tests/unit/test_api_v1.py` and `tests/integration/test_cli_e2e.py`: an empty database used to mean "nothing ranks here" and now means "this artifact was never built". Each carries the reasoning in its docstring rather than being edited quietly | ✅ |

## What this wave should be remembered for

**Two of the four stay-green mutants were failures of my own testing, not of the code.**

**M11** reverted the no-evidence predicate to the one the security seat had already proven wrong in
W1 — a fix I shipped and never tested. The seat found it, I fixed it, and nothing pinned it.

**M3** stayed green because **my own test drove the wrong path**. It was named for the narrowing
that keeps a corrupt database from being reported as merely unbuilt, and it used a junk file — which
raises `DatabaseError`, never entering the `OperationalError` clause the mutant edits. A LOCKED
database is the case that actually goes through it. A test can be named for a control, be about the
control, and never execute it.

**And one mutant I counted as a survivor was equivalent:** `(False and X) or Y` still evaluates `Y`.
A mutant that changes no behaviour proves nothing about the test that "survived" it, and counting it
as a gap would have sent me looking for a hole that was not there.

---

Touched: `src/app/adapter/main.py`, `src/app/workflows/rank.py`, `src/app/workflows/recommend.py`, `tests/integration/test_cli_e2e.py`, `tests/unit/test_api_config.py`, `tests/unit/test_api_v1.py`, `tests/unit/test_effort.py`, `tests/unit/test_recommend.py`, `tests/unit/test_recommend_assistant.py`, `tests/unit/test_subscribe.py`, `tests/unit/test_unbuilt_evidence.py`
(11 files changed, 538 insertions(+), 29 deletions(-))

K.8 contracts: `recommend()` no longer writes (REQ-API-007); `rank.require_price_medians` NEW; the CLI's exit-code contract gains 2 for an unbuilt artifact; `/v1` gains 503 for the same. `/v1`'s SUCCESS payload is unchanged (D-115 intact).

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-18 · Wave commit range: `95d206e..fb258f3`

> Added at M7 closure after `scripts/wave_check.py` failed all four of this milestone's wave records
> on exactly these three lines. The gate exists, it works, and `make check` does not run it — the
> same shape this project has spent five milestones finding in its code, here in its records.
> Ledgered as **W-032**; wiring `make wave-check` into `make check` is a gate-definition change and
> therefore the owner's.
