# Wave 2 Code Re-review (m5)

**Reviewer:** Code-Reviewer subagent (fresh eyes; authored no W2 code)  
**Date:** 2026-08-16  
**Protected base:** `96ba91d`  
**Checkpoint:** `964a389` plus the current fix delta  
**Risk tier:** HIGH  

## Verdict

**PASS**

The original `m5-wave-2-review.md` remains intact as the audit record of four BLOCKING findings
and one MINOR. Independent re-review found every item closed and found no new blocker.

## Closed findings

1. **D-109 artifact rounding — CLOSED.** `rank.py:206-246` rounds `score`,
   `secondary_score`, and `higher_effort_score` once at the JSON/CSV boundary while retaining raw
   internal values. `test_effort.py:303-322` and an independent probe require published
   `60.6 / 11.8 / 75.6` while the row remains `60.555 / 11.755 / 75.555`.
2. **No-higher disclosure — CLOSED.** `recommend.py:155-159` now says exactly that no comparable
   higher-effort result exists **in the same harness and source**. The Claude fixture contains a
   lower-effort row plus foreign-harness `max=99` and foreign-source `max=98`; both the model CLI
   (`test_effort.py:245-269`) and subscription CLI (`test_effort.py:272-300`) require the exact,
   identity-scoped Turkish sentence.
3. **Higher-effort identity — CLOSED.** `rank.py:56-79,169-198` and
   `subscribe.py:188-215` constrain higher evidence to the selected harness and source. An
   independent same-identity probe selected `max=70` and rejected foreign `99/98` values.
4. **Coverage effort test gap — CLOSED.** The live entrypoint test at
   `test_effort.py:325-386` proves a `max`-only plan is unscoreable for the data-owned `high`
   category, then scoreable after insertion of a matching `high` row. This locks the predicate at
   `coverage.py:103-144`.
5. **Schema migration comment — CLOSED.** `schema.py:143-147` now describes the migration as
   row-preserving and explicitly acknowledges the authorized effort table rebuild.

## Requirement and contract evidence

- **REQ-CAN-005:** `test_schema.py:54-100` and `test_effort.py:25-73,325-398` cover migration,
  effort resolution/storage, category filtering, and live coverage behavior.
- **REQ-REC-011:** `test_effort.py:245-300` covers both shipped recommendation entrypoints,
  high-only ordering, same-identity range evidence, and truthful disclosure.
- **K.8:** no contract drift remains. The score identity, data-owned effort policy, D-109 boundary,
  and model/plan equivalence are aligned; no hardened producer is left without a citing test.

## Verification

- Focused effort suite with the owner-mounted Epoch bundle: **18 passed**.
- Changed-surface suite: **49 passed**.
- Full suite: **241 passed, 5 expected network-contract skips**.
- Ruff, Black, mypy, and `git diff --check`: clean.

The re-review is PASS. W2 may proceed to the separate Tester gate.
