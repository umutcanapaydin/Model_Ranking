---
record_type: wave
id: m7-wave-1-close
status: draft
process_version: v5.0
date: 2026-08-18
---
# Wave-Close Checklist — M7 Wave 1 (the build pipeline becomes product code)

> **STATUS: CLOSED 2026-08-18**, at the owner's ruling, with the remainder ledgered rather than
> carried into a fourth review round. Three seats ran three rounds and closed **thirty BLOCKING
> findings**, none of them found by the author. The wave closes on **D-122**, which the wave itself
> produced: review depth now follows what the code can get wrong, and this wave's own arithmetic is
> the evidence — findings went 14 → 8 across rounds two and three, and every round after the first
> found defects the author had introduced while fixing the previous one.

## What the wave delivered

The evidence database's build pipeline existed only as a ~30-line heredoc inside
`.github/workflows/contract-tests.yml`: invisible to `ruff`, `mypy`, `pytest` and coverage, writing
to a throwaway file, on a Monday cron that had never fired in this repository's history. That is why
`advisor.db` sat on the pre-M5 schema — **nothing rebuilt it** (W-023).

It is now `src/app/workflows/build.py` with a CLI entry point, and the heredoc is deleted rather
than left as a second copy. `src/app/workflows/sources.py` names the five remote dependencies and
two local bundles once; `build.py` and `scripts/smoke_deps.py` both derive from it, and
`tests/unit/test_sources.py` produces the client list from `src/app/clients/` with `ast` so the
registry cannot silently disagree with the tree.

**Measured on the artifact, read back from the file rather than reported by the writer:** 73 models,
72 price medians, six sources (litellm 2194, openrouter 389, swebench 173, aider 68,
epoch_swe_bench_verified 33, epoch_deepswe_external 49). Serving it returns 3 picks on `coding` and
3 on `agentic-coding`, where the shipped artifact previously returned **0 on both** — M6's Ruling A
was true in the contract and empty in the data until this wave.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m7-plan.md` §2 records W1 **HIGH** (new production entry point + untrusted remote input). Both triggers were real: the entry point is the first code in this project that fetches five remote sources and reads an unpacked third-party bundle | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix, three times over (`src/app/workflows/build.py`, `src/app/workflows/sources.py`). The author's own round found the last surviving mutant (the module-resolution predicate living inside its own test) | ✅ |
| 3 | Review per tier — V3C-78 | **Three seats, three rounds.** Code-Reviewer, Tester and a pulled-forward Security pass, each with fresh eyes (K.7 — none authored the code). Records: `docs/reviews/m7-wave-1-review.md`, `m7-wave-1-tester.md`, `m7-wave-1-security.md` and their three re-reviews | ✅ |
| 4 | Fault injection — V3C-72 | Author: `m7w1_lead_faultinject.py`, 15 mutants over the fix delta, 14 killed first pass, 15/15 after extracting the survivor's predicate. Tester seat: **55 mutants round one (26 stayed green), 63 round two (41 killed as submitted, 54 after its own 7 tests)**. Every stay-green mutant received its mandatory test | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-ING-012: `test_build.py::test_build_produces_an_artifact_that_can_actually_answer` + the CLI tests. REQ-ING-013: the eleven failure tests in `test_build_artifact_safety.py`, each verified RED against its mutant. W-023: `test_api_config.py::test_the_repositorys_own_artifact_is_checked_not_assumed`, **inverted** at this wave — it used to assert the artifact was broken and went red the moment it was fixed | ✅ |
| 6 | New REQ-IDs in the PRD, at the wave not at closure | `docs/prd.md` REQ-ING-012 and REQ-ING-013, added during W1 to avoid the F-1 drift the M4 gate raised | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **474 passed / 12 skipped** (396 at wave start) · `ruff` clean · `mypy` clean across 31 files · `gitleaks` clean · `check_records` PASS across 33 records | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-121** (a source may be optional, but a blind surface may never be silent) — amended the same day when the security seat proved its justifying claim was contradicted inside its own payload. **D-122** (review depth by blast radius) | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: W-023 **closed**; W-026, W-027, W-028, W-029 opened — two escalated to the owner as gate-definition changes, two ACCEPTED with reasons | ✅ |
| 10 | Plan promises delivered | **NOT fully.** `docs/plans/m7-plan.md` §5 assigned "coverage / roster-staleness CI legs, never run" to W1; `.github/workflows/contract-tests.yml:14-17` is byte-identical to `9f4471d`. Ledgered as **W-027** with the one-line owner remedy, rather than quietly dropped | WAIVED — ledgered as W-027 |

## The three findings this wave should be remembered for

**1. An injection point that cannot be injected.** `build()` bound its source list as a DEFAULT
ARGUMENT, which binds at definition time — so a test that believed it was using fakes reached the
real network, and only a live upstream outage revealed it. **The author then wrote the identical
bug into `_ingest_bundles` twenty minutes later**, inside the wave that fixed it.

**2. A new branch silently inherits the old branch's tests.** The Tester seat's phrasing. The fix
for a false "nothing fits your budget" message added a no-evidence branch ABOVE it; the assertion
that used to cover the budget branch moved onto the new one, six mutants of the old branch stayed
green, and no test was edited by anyone. Nothing in this project's gates can see coverage move.

**3. A record that asserts a control which is not there.** The D-121 amendment claimed the test file
"also asserts that a surface WITH evidence still gets the budget sentence". It did not. This is the
records-versus-reality defect the project has spent four milestones on, committed by the author in
the sentence documenting the fix.

## What is NOT closed, stated rather than implied

- **W-024** — arena has been down on an upstream HTTP 500 for the duration of this wave. Handled by
  D-121, not resolved: the artifact ships without it and `assistant` discloses that it has no
  evidence to rank.
- **W-026 / W-027** — owner decisions, both gate-definition changes under AGENTS.md §3.
- **W-028 / W-029** — ACCEPTED with reasons: one stray workspace file after a SIGKILL, and a guard
  that skips in a clean checkout because CI cannot verify an artifact it does not have.
- **The workflow has still never run.** W1 delivered a workflow that would now survive a run; the
  run itself is `gh workflow run contract-tests.yml` and belongs to the owner.

---

Touched: `.github/workflows/contract-tests.yml`, `docs/decisions.md`, `docs/plans/m7-wave-1-close.md`, `docs/prd.md`, `docs/reviews/m7-wave-1-rereview.md`, `docs/reviews/m7-wave-1-review.md`, `docs/reviews/m7-wave-1-security-rereview.md`, `docs/reviews/m7-wave-1-tester-rereview.md`, `docs/reviews/m7-wave-1-tester.md`, `docs/warnings.ledger.md`, `scripts/check_records.py`, `scripts/slopsquat_check.py`, `scripts/smoke_deps.py`, `scripts/wave_check.py`, `src/app/adapter/main.py`, `src/app/clients/litellm.py`, `src/app/workflows/build.py`, `src/app/workflows/sources.py`, `tests/unit/test_api_config.py`, `tests/unit/test_build.py`, `tests/unit/test_build_artifact_safety.py`, `tests/unit/test_ci_argument_drift.py`, `tests/unit/test_empty_answer_reasons.py`, `tests/unit/test_parser_envelopes.py`, `tests/unit/test_sources.py`
(25 files changed, 4486 insertions(+), 126 deletions(-))

K.8 contracts: `app.workflows.sources` (NEW registry), `app.workflows.build` (NEW entry point), `contract-tests.yml` build step. Frozen surfaces untouched: `/v1` payload (D-115), CLI vocabulary (D-118), `schema migrate` exit codes (D-120).

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-18 · Wave commit range: `9f4471d..95d206e`

> Added at M7 closure after `scripts/wave_check.py` failed all four of this milestone's wave records
> on exactly these three lines. The gate exists, it works, and `make check` does not run it — the
> same shape this project has spent five milestones finding in its code, here in its records.
> Ledgered as **W-032**; wiring `make wave-check` into `make check` is a gate-definition change and
> therefore the owner's.
