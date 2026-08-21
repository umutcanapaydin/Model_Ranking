---
record_type: wave
id: m9-wave-1-close
status: ratified
process_version: v5.0
date: 2026-08-21
---
# Wave-Close Checklist — M9 Wave 1 (one refresh cycle, by hand)

> **CLOSED 2026-08-21.** The wave delivered `python -m app.workflows.refresh` and, more usefully,
> found four defects in its own new code — three of them by fault injection and one by a test the
> wave was writing anyway. **None was found by reading it.**

## What the wave delivered

A refresh cycle that builds a candidate, decides whether anything a user would notice changed, and
publishes or discards. It calls `build.py`'s own entry point rather than reimplementing any of its
safety: two publish paths would be two definitions of "safe to serve".

Verified against LIVE sources, not only fixtures: the first cycle published (upstream pricing had
genuinely moved), the second reported unchanged with identical fingerprints, exit 1.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m9-plan.md` §2 records W1 **MED**: new code that REPLACES the served artifact, reusing the build's safety rather than adding a second publish path | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → fault-inject → fix, four times over `src/app/workflows/refresh.py`. Each of the four defects below was found by the loop, not by review | ✅ |
| 3 | Review per tier — V3C-78 / D-122 | **WAIVED under PRESSURE**, 2026-08-21, recorded as a `control-bypass` under V4C-13. MED tier, single pass, and the author's own fault injection stood in. **The M9 plan §4 requires an independent seat on W2 specifically**, because M8 measured what three consecutive bypasses cost — that commitment is not weakened here | WAIVED — PRESSURE, D-122 |
| 4 | Fault injection — V3C-72 | **14 mutants over `src/app/workflows/refresh.py`; 14 killed after four rounds of strengthening.** First pass killed 3 of 8. `src/app/workflows/refresh.py` md5-verified restored after every mutant | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | `tests/unit/test_refresh.py`, 24 tests. REQ-REF-001: four "live artifact untouched" cases plus no-candidate-survives. REQ-REF-002: seven fingerprint cases, each proven RED against a mutant. REQ-REF-006: a swap under `TestClient`. REQ-REF-007 structural: an AST check | ✅ |
| 6 | New REQ-IDs in the PRD, at the wave not at closure | `docs/prd.md` — REQ-REF-001..007 written at W1, **before any code**. M8 added its REQ-IDs at W2 and recorded that as a shortfall; this is that lesson applied | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **611 passed / 12 skipped** · coverage 87.8% against the 85% floor · `refresh.py` at **95%** against the 60% per-module floor · ruff and mypy clean · `check_records` and `wave-check-all` PASS | ✅ |
| 8 | ADRs for decisions made | None yet. The three decisions M9 must make are named in `docs/plans/m9-plan.md` §5 and belong to W2, deliberately unmade while they are still abstract | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` unchanged by this wave; no new warning. The four defects were fixed inside the wave that made them, which is where a defect should die | ✅ |
| 10 | Plan promises delivered | `docs/plans/m9-plan.md` §2 W1 asked for the cycle plus a PINNED hot swap. Both delivered | ✅ |

## The four defects this wave found in its own code

**1. A corrupt candidate would have been PUBLISHED over a working artifact.** `serving_fingerprint`
caught `sqlite3.DatabaseError` per category and treated it as "this surface is empty" — so a file of
random bytes produced a perfectly plausible fingerprint of *every surface empty*, compared unequal to
the live artifact, and published. A defensive catch that turns a fatal condition into a believable
result. Found by a test asserting the outcome, then pinned a second time at the layer itself,
because two guards covering each other is also how both get deleted.

**2. The fingerprint masked price changes a user can read.** It re-rounded `blended_per_m` to one
decimal, while `rank.py` already rounds it to the two the product prints (`$8.55/1M`). A one-cent
move — visible on the screen — fingerprinted as unchanged and would never have published. **Rounding
twice at different precisions is not extra safety; it is a second, quieter output boundary that
disagrees with the real one.** The surviving mutant was the signal that the LINE was wrong, not that
the test was weak.

**3. The command printed two JSON documents.** The build reports to stdout and so did the refresh, so
the first real CLI run produced `JSONDecodeError: Extra data: line 115`. For a command whose entire
purpose is to run unattended and be read by something that is not a human, its result was
unparseable. The build's report is diagnostics and now goes to stderr.

**4. The injection seam bound at definition time — for the FOURTH time in this project.** `builder`
defaulted to `build_main` in the signature, so patching the module attribute did nothing and every
CLI test ran the real build against the real network. **It was written into the module whose
docstring says the parameter is "read at CALL time".** The claim and the code disagreed inside the
same sentence. The tell was wall-clock: the suite took 12.58 s, and 0.34 s once the seam worked.

## What is NOT closed

- **W2 owns the refusal rule**, and until it exists this cycle will publish a candidate that is
  WORSE than the live artifact. That is the milestone's central risk and it is open by design.
- **The three §5 decisions are unmade**, deliberately, while they are still abstract.
- `refresh.py` is at 95%; the uncovered lines are the publish-failure branch and `__main__`.

---

Touched: `docs/prd.md`, `docs/plans/m9-plan.md`, `src/app/workflows/refresh.py`, `tests/unit/test_refresh.py`

K.8 contracts: none moved. `/v1` untouched; D-124's window remains SPENT. `build.py` is CALLED, not modified.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-21 · Wave commit range: `1fd9df4..HEAD`
