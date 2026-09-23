---
record_type: wave
id: wave-checklist-template
status: draft
process_version: v6.6
date: 2026-09-23
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run. -->
# Wave-Close Checklist — M{N} Wave {W}

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
| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches authz/secrets/crypto/input-parsing/egress) | plan `file:line` | |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | test-run ref | |
| 3 | Code-Reviewer and Tester ran as **two separate subagents** via `/close-wave`, every wave, every tier; neither verdict BLOCKING, and each declares `**Independent:** yes` — its reviewer wrote none of this wave's code (`make wave-check` reads both). An author who reviewed marks this row WAIVED, with a row for this wave in `docs/control-events.csv`. HIGH additionally: row 4. Reviewer countersigns 2 randomly-chosen rows of THIS checklist against the actual artifacts (anti self-attestation) | `docs/reviews/m{N}-wave-{W}-review.md` + `-tester.md` | |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | review file | |
| 5 | Tester fault-injection on the 1–2 most load-bearing behaviors: break → RED confirmed; restore reproduces pre-injection BYTES (md5), never re-derived; after any FIX round, replay the previous round's mutant set — the independent set's survivors where one exists → reverted byte-identical (md5); every stay-GREEN fault got its mandatory new test. **HIGH only, advisory:** if a mutation runner is wired, mutant kill-rate on changed code recorded beside the verdict — never blocks | tester log + new test refs (+ kill-rate line at HIGH) | |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint (not a unit shim) — "built ≠ wired" | test `file:line` | |
| 7 | New/changed security invariants added to the release's invariants list with their NEGATIVE test | `security-invariants` row | |
| 8 | No `git checkout`/`restore` was run on uncommitted work this wave (reverts were in-place + hash-verified) | tester/reviewer attestation | |
| 9c | **Invariant hardening:** if this wave hardens a shared invariant (auth/tenancy/money), the producer list is enumerated FROM CODE (create/rotate/import/…) with a citing test per producer; missing tests recorded as tracked gaps; security sign-off on auth-class | producer list + test refs | |
| 9b | **Scope & draft PR:** scope row appended — planned vs delivered vs deferred vs the approved plan (append-only); the wave's work is committed on `wave/m{N}-w{W}` and its DRAFT PR is open | plan ref + PR number | |
| 9a | **Economy:** wave diff within ~≤400 changed lines OR variance noted (WARN, not block); projected token spend within the milestone budget line, else pause + variance note | diffstat + cost-log ref | |
| 9 | **Skipped/waived/BYPASSED ledger + run summary:** first the RUN LINE — `gates run: <list> · gates SKIPPED: <list> · tokens/cost: <n> · outcome: <shipped or abandoned>` (a wave that burned budget and produced nothing is invisible in git otherwise). Then list every check that did NOT run this wave — legitimate skips (N/A, no environment) AND pressure bypasses — one-line reason + rough cost (minutes) each, and append each as a row in `docs/control-events.csv` (kind `skip` or `bypass`). A SKIPPED or WAIVED row says PRESSURE or NO-ENVIRONMENT. The SAME control recorded three times turns `make wave-check` red: the CONTROL goes under review, not the people. Bypasses are also EXPERIENCE findings (`control-bypass`) |  |  |

Filled by: `<agent>` · Date: `<YYYY-MM-DD>` · Wave commit range: `<start>..<end>`

## Review findings — each one fixed here, filed, or refused

One row per id in the two verdicts' MINOR, K.9 and queued-risk sections (`/close-wave` step 6).
A finding fixed in this wave is not filed; one the wave does not fix leaves it as an issue —
`bug` with a severity, or `enhancement`. `make wave-check` refuses a close that leaves one out.
No findings → keep the header and write none below it.

| finding | disposition |
|---|---|
| review M1 | fixed `<sha>` |
| tester M1 | #<issue> |
| review K1 | refused — <why the finding is wrong, in a sentence> |

## Wave footprint — RECORD ONLY, no rule attached

**Fill these from the actual diff at close, not from the plan.** Plan-time paths are a prediction;
close-time paths are a measurement, and the difference is where defects live.

```
Touched:        <paths this wave actually changed — `git diff --name-only <start>..<end>`>
Mutant set author: <who designed the fault-injection set; self-designed = supporting evidence only>
Observed RED:   <the mutation + which assertion failed for the cited reason; N/A-with-reason if no code row>
Owner instruction: <the owner's words, VERBATIM, that this wave implements — and one line mapping the delivery to those words>
K.8 contracts:  <shared interfaces this wave changed, or NONE — the symbols other waves depend on>
Stopped at three attempts: <#issue per problem this wave gave up on after three failed attempts (`.agents/rules/practices.md`), or NONE>
Hand-kept lists: <NAME the hand-kept enumeration this wave adds — the list that sits beside the thing it guards and must be updated by hand when that thing changes — or NONE>
```

**On `Hand-kept lists`.** Name the artefact or write NONE — deliberately **not** a yes/no box: a
denylist does not feel like a denylist while you are writing it, it feels like being thorough.
Naming forces you to look at the thing. This line is a detection aid, not a gate: when you write a
rule that bans a specific literal or shape, the check that enforces it ships in the same change.

**Why the footprint exists.** Whether waves can run as parallel subagents depends on data nobody has
yet: do waves touch disjoint file sets, and do they share contracts? These lines answer it with a
measurement instead of an intuition. `make wave-check` requires them filled; no rule compares them
across waves.
