# M1 Wave 4 — Combined Code-Reviewer + Tester report (fresh eyes, LOW tier)
Reviewer: independent subagent. Date: 2026-08-10. Verified by execution (fallback repro,
corrupt-db repro, tie stability x5, UTF-8 locale checks).

## VERDICT: CHANGES REQUIRED → fixes applied same-wave → re-verified green
BLOCKING-1: budget_pick fallback emitted a FALSE why (claimed the 65% floor was met when it
wasn't) → fixed: floor_met branch with explicit UYARI disclosure + regression test
(test_budget_pick_warns_when_quality_floor_unmet).
MINOR-1: corrupt DB crashed with exit 1 (colliding with the no-eligible contract) → fixed:
sqlite3.Error → JSON error + exit 2 + test (exit codes: 0=ok, 1=no eligible, 2=usage/db error).
MINOR-2: edge tests missing → added: non-empty-ranking→None, fallback branch, corrupt-db,
invalid --budget.
MINOR-3: e2e clobbered PYTHONPATH → fixed: prepend.

Confirmed correct by reviewer: VALUE_WINDOW anchor (frontier[0] IS the top-score eligible row),
close_call frontier-only design, no score÷price anywhere, V4C-50 satisfied (4 tests through the
real python -m entry point), px_median write-on-read consistent with D-100 disposable DB.

## Post-review live-run finding (lead agent, logged for closure)
First REAL end-to-end run caught a data condition all fixtures missed: Aider lists the same model
across multiple runs → UNIQUE violation, loud SourceError (control worked as designed). Fixed with
the same keep-best dedupe as swebench + live-run regression test. Lesson for EXPERIENCE: a fixture
models the data you imagined; the first live run is a mandatory closure step.
