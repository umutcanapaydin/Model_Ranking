---
record_type: wave
id: m6-wave-4-close
status: draft
process_version: v5.0
date: 2026-08-17
---
# Wave-Close Checklist — M6 Wave 4 (the deploy ADR that was never written)

> **STATUS: CLOSED 2026-08-17**, folded into the milestone closure. W4 is a records-and-readiness
> wave: it produced one ADR, one gate that had never run, and two proposals. Its review is the
> Stage-4.0 closure security pass, which covers the whole milestone surface including this wave —
> dispatching a separate per-wave seat for four documents and a smoke script would have been
> ceremony, and that judgement is recorded here rather than left implicit.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan — V3C-78 | `docs/plans/m6-plan.md` §4 records W4 **LOW-MED** unless the diff crosses an auto-HIGH boundary. It does not: no authz, no schema change, no crypto. The new code is one smoke script that makes outbound calls on the OWNER's machine and never in the serving path | ✅ |
| 2 | Per-agent dev-test loop ran — V3C-68 | `make smoke-deps` was a deliberate loud failure until `docs/smoke-deps.sh` existed. Written, run, and **wrong on the first attempt in the way the gate exists to catch** — see row 5. Rewritten to invoke each dependency through its own client; first real PASS across five dependencies | ✅ |
| 3 | Review per tier — V3C-78 | Covered by the Stage-4.0 closure security review over `1faaf77..HEAD`, which includes this wave and was asked specifically to judge the deploy proposals and the smoke script. Recorded as a deliberate fold, not a skip | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass | N/A — `docs/plans/m6-plan.md` §3 tags W1 and W3, not W4. The Stage-4.0 pass covers this surface | N/A |
| 5 | Tester fault-injection; every stay-GREEN fault got its mandatory test — V3C-72/F5 | **The wave's own defect was found by running the gate, not by a mutant.** `docs/smoke-deps.sh` v1 typed its endpoints in and reported a 404 for a working dependency — it said `main/` where `src/app/clients/swebench.py` says `master/`. Its docstring said *"a smoke test against a URL nobody calls proves the network works and nothing else"* and then did exactly that. Fourth instance this milestone of typed-out-list-is-a-denylist. The replacement derives every endpoint by importing the client. No mutant would have caught it: the script was internally consistent | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the LIVE entrypoint — V3C-02 | W4 adds no REQ-ID. Its artefacts are an ADR (**D-116**, closing PRD OQ-3), a gate (`make smoke-deps`, whose citing evidence is its own PASS output against five live dependencies), and two proposals. `docs/coverage-by-req.md` traces the milestone's nine criteria with DERIVED line numbers | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test — V3C-74/F7 | None added. One recorded: **W-021**, `.github/CODEOWNERS` owns every path to a placeholder that assigns nobody — a K.10 boundary that has read as installed since bootstrap. Not deleted by the agent; removing a boundary is the owner's call | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work — V3C-06/F17 | None run this wave. Commits under D-117, gate green at each | ✅ |
| 9c | Invariant hardening — V3C-101 | N/A — 2026-08-17. No auth, tenancy or money invariant touched. The money-adjacent surface (`fly.toml` concurrency limits) is a PROPOSAL and binds nothing | N/A |
| 9b | Scope & checkpoint — V3C-90/OD-4 | **Planned** (`docs/plans/m6-plan.md` §3 W4): a real ADR closing OQ-3 · deploy artefacts as proposals · Stage 4.3 readiness walked without going live · watch the CI legs. **Delivered:** all four. **Deferred:** the coverage and roster-staleness CI legs still have not RUN — `contract-tests.yml` is a Monday cron and no Monday has passed since it was written. Watching them is carried to M7, and saying so is better than claiming a leg green that has never executed. **Checkpoint commit:** agent, under D-117 | ✅ |
| 9a | Economy — V3C-85/86 | `git diff 915e97b..HEAD --stat` — 27 files, mostly records. Within the ≈60k W4 budget line | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary — V4C-13 | `gates run: lint · typecheck · black · mypy · test (354 passed / 12 skipped) · check-records (32 records) · check-records-selftest · install-check · conformance (6 of 7) · wave-check · smoke-deps (first PASS) · gitleaks (clean, first time) · gates SKIPPED: a per-wave review seat, folded into Stage 4.0 by the judgement in row 3 · tokens/cost: within the W4 line · outcome: SHIPPED and CLOSED`. **No pressure bypass** | ✅ |

**Escaped-blocker tripwire (V3C-78):** none.

## Wave footprint — RECORD ONLY, no rule attached (v5.0)

```
Touched:        .github/CODEOWNERS · .gitleaks.toml · Dockerfile · conformance/wave/m1-wave-2-close.md · docs/architecture.md · docs/decisions.md · docs/gp-field-findings.md · docs/plans/m4-plan.md · docs/plans/m6-plan.md · docs/plans/m6-wave-3-close.md · docs/prd.md · docs/reviews/m6-wave-3-review.md
                (`git diff --name-only 915e97b..HEAD`, 27 paths)
K.8 contracts:  CHANGED — `schema migrate` gained exit code 3 (D-120), a new value on the frozen
                CLI-exit-code contract; the code review caught it shipping without an ADR. NEW:
                `Dockerfile` and `fly.toml` as PROPOSALS, and `scripts/smoke_deps.py`, which is the
                first code in this repository whose job is to make live network calls at a gate.
Closure rounds: 1 — this wave produced no BLOCKING of its own; the milestone's ten came from W1-W3.
```

### Where this wave got stuck, and for how long

| | |
|---|---|
| Elapsed, W3 close (`164d79f`) to now | **~332 min**, and most of it is not this wave's work — it spans the three W3 re-review rounds that ran while W4 proceeded in parallel. **Corrected from a first draft that said 835 min**, which measured from W3's START commit and would have attributed the whole of W3 to W4. Recorded because three review seats have now caught this author shipping a number that did not hold, and the fix is to stop shipping unchecked ones |
| Gate that consumed it | **none — the time went into the ADR and the smoke gate**, and the smoke gate cost two attempts because the first one was wrong |
| The real cost | writing `docs/smoke-deps.sh` twice. The first version was a shell script with the endpoints typed in, and it took a live run to disprove |

**Across four waves.** W1 52 min / 9 paths / 3 review rounds · W2 74 min / 29 paths / 2 rounds ·
W3 HIGH tier / 10 paths / 4 rounds · W4 / 27 paths / 0 rounds.

**A caveat the footprint data needs, or the next reader will draw the wrong conclusion.** These
elapsed figures are commit-to-commit wall clock on a session where waves overlapped with reviews
running in the background. They are an upper bound on a wave, not its cost, and W4's especially:
it ran alongside three W3 re-review rounds. What the numbers DO support is the shape — duration
tracks review rounds, not paths touched.
**The pattern the footprint data shows is that wave duration tracks REVIEW ROUNDS, not paths
touched.** W2 touched three times W1's files and cost one fewer round. W4 touched the most records
and needed none. The variable is how much of the wave was new behaviour the author had to get right
first time.

Filled by: `Claude (lead agent, local lane under D-114/D-117)` · Date: `2026-08-17` · Wave commit range: `915e97b..working tree`
