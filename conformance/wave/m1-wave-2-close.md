---
record_type: wave
id: m1-wave-2-close
status: ratified
process_version: v6.3
date: 2026-09-23
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run. -->
# Wave-Close Checklist — M1 Wave 2

> **Copy to `docs/plans/m{N}-wave-{W}-close.md`, fill, and COMMIT at every wave close** (`/close-wave`
> does this). **Cadence binds to artifacts:** every OUTWARD deliverable (patch, package, report, tool,
> answer-doc delivered outside the team) is a wave close, so this checklist runs — chat messages don't
> count.
> **The wave gate is agent-side:** this checklist + the two fresh-eyes reviews + green checks pinned to
> the closing tree. The human who merges the wave's draft PR reviews it there. Escalate-NOW events
> (AGENTS.md §3) halt to the owner immediately.
> The wave does not close until every row is ✅ or has an explicit WAIVED entry (row 9).
> Rows marked *(plan-tag)* are derived from the plan's risk tags — do not hand-copy; if the plan
> tags a pass, it appears here and blocks (the failure mode: a tagged pulled-forward security pass
> silently skipped).
>
> **Evidence rule (anti-theater):** every ✅ cites a FRESH, SCOPED referent — a commit in this
> wave's range, a test-run on this wave's code, a review file for THIS wave. A referent outside
> the wave's commit range is invalid.
>
> **Accretion valve:** adding a row to this template requires naming the incident that triggered
> it; prefer one-in-one-out. ≤12 rows, always.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches authz/secrets/crypto/input-parsing/egress) | `docs/plans/m1-plan.md:31` — MED | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | `tests/unit/test_quota_read.py:14` run in this wave (commit a1b2c3d) | ✅ |
| 3 | Code-Reviewer and Tester ran as **two separate subagents** via `/close-wave`, every wave, every tier; neither verdict BLOCKING (`make wave-check` reads both). HIGH additionally: row 4. Reviewer countersigns 2 randomly-chosen rows of THIS checklist against the actual artifacts (anti self-attestation) | `conformance/reviews/m1-wave-2-review.md` + `conformance/reviews/m1-wave-2-tester.md` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | N/A — MED wave, no HIGH slice (`docs/plans/m1-plan.md:31`) | ✅ |
| 5 | Tester fault-injection on the 1–2 most load-bearing behaviors: break → RED confirmed; restore reproduces pre-injection BYTES (md5), never re-derived; after any FIX round, replay the previous round's mutant set — the independent set's survivors where one exists → reverted byte-identical (md5); every stay-GREEN fault got its mandatory new test. **HIGH only, advisory:** if a mutation runner is wired, mutant kill-rate on changed code recorded beside the verdict — never blocks | `tests/unit/test_quota_read.py:14` went RED on the `>=` → `>` mutant; restored md5 matches | ✅ |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint (not a unit shim) — "built ≠ wired" | `tests/unit/test_quota_read.py:14` through `GET /quota` | ✅ |
| 7 | New/changed security invariants added to the release's invariants list with their NEGATIVE test | `docs/security-invariants.md:9` — tenant scope on reads | ✅ |
| 8 | No `git checkout`/`restore` was run on uncommitted work this wave (reverts were in-place + hash-verified) | `conformance/reviews/m1-wave-2-tester.md` — reverts in place | ✅ |
| 9c | **Invariant hardening:** if this wave hardens a shared invariant (auth/tenancy/money), the producer list is enumerated FROM CODE (create/rotate/import/…) with a citing test per producer; missing tests recorded as tracked gaps; security sign-off on auth-class | N/A — no shared invariant hardened (`docs/plans/m1-plan.md:31`) | ✅ |
| 9b | **Scope & draft PR:** scope row appended — planned vs delivered vs deferred vs the approved plan (append-only); the wave's work is committed on `wave/m{N}-w{W}` and its DRAFT PR is open | `docs/plans/m1-plan.md:40` + draft PR #12 | ✅ |
| 9a | **Economy:** wave diff within ~≤400 changed lines OR variance noted (WARN, not block); projected token spend within the milestone budget line, else pause + variance note | `git diff --stat a1b2c3d..f4e5d6c` = 2 files, +61 | ✅ |
| 9 | **Skipped/waived/BYPASSED ledger + run summary:** first the RUN LINE — `gates run: <list> · gates SKIPPED: <list> · tokens/cost: <n> · outcome: <shipped or abandoned>` (a wave that burned budget and produced nothing is invisible in git otherwise). Then list every check that did NOT run this wave — legitimate skips (N/A, no environment) AND pressure bypasses — one-line reason + rough cost (minutes) each, and append each as a row in `docs/control-events.csv` (kind `skip` or `bypass`). A SKIPPED or WAIVED row says PRESSURE or NO-ENVIRONMENT. The SAME control recorded three times turns `make wave-check` red: the CONTROL goes under review, not the people. Bypasses are also EXPERIENCE findings (`control-bypass`) | `gates run: lint typecheck test check gate · gates SKIPPED: none · tokens/cost: 41k · outcome: shipped` — no skips or bypasses | ✅ |

Filled by: `lead agent` · Date: `2026-09-23` · Wave commit range: `a1b2c3d..f4e5d6c`

## Wave footprint — RECORD ONLY, no rule attached

**Fill these from the actual diff at close, not from the plan.** Plan-time paths are a prediction;
close-time paths are a measurement, and the difference is where defects live.

```
Touched:        src/app/quota/read.py, tests/unit/test_quota_read.py
Mutant set author: Tester subagent (independent — authored no line of the diff)
Observed RED:   flipped `>=` to `>` in read.py:88 → `test_quota_boundary` failed on the boundary assertion
Owner instruction: "the tenant admin sees their own quota" (translated) → delivered: GET /quota returns caller-tenant rows only
K.8 contracts:  NONE — read path only
Hand-kept lists: NONE
```

**On `Hand-kept lists`.** Name the artefact or write NONE — deliberately **not** a yes/no box: a
denylist does not feel like a denylist while you are writing it, it feels like being thorough.
Naming forces you to look at the thing. This line is a detection aid, not a gate: when you write a
rule that bans a specific literal or shape, the check that enforces it ships in the same change.

**Why the footprint exists.** Whether waves can run as parallel subagents depends on data nobody has
yet: do waves touch disjoint file sets, and do they share contracts? These lines answer it with a
measurement instead of an intuition. `make wave-check` requires them filled; no rule compares them
across waves.
