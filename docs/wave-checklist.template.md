# Wave-Close Checklist — M{N} Wave {W} (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

> **Copy to `docs/plans/m{N}-wave-{W}-close.md`, fill, and COMMIT at every wave close.**
> **v3.5 cadence rebind (V3C-105): every OUTWARD deliverable (patch, package, report, tool,
> answer-doc delivered outside the team) = a wave close → this checklist runs** — cadence binds to
> artifacts, not phase events (chat messages don't count).
> **v3.3 (OD-4/A0.5): NO owner review at wave close** — this checklist + the fresh-eyes agent
> reviews + green pinned checks ARE the wave gate; the owner reviews per MILESTONE. Escalate-NOW
> events (AGENTS.md §3) halt to the owner immediately.
> The wave does not close until every row is ✅ or has an explicit WAIVED entry in the ledger.
> Rows marked *(plan-tag)* are derived from the plan's risk tags — do not hand-copy; if the plan
> tags a pass, it appears here and blocks (the F15 failure mode: a tagged pulled-forward security
> pass silently skipped).
>
> **Evidence rule (anti-theater):** every ✅ cites a FRESH, SCOPED referent — a commit in this
> wave's range, a test-run on this wave's code, a review file for THIS wave. A referent outside
> the wave's commit range is invalid.
>
> **Accretion valve:** adding a row to this template requires naming the incident that triggered
> it (see the v3.1 rows below for the pattern); prefer one-in-one-out. ≤12 rows, always.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches authz/secrets/crypto/input-parsing/egress) — V3C-78 | plan `file:line` | |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) — V3C-68 | test-run ref | |
| 3 | Review per tier: LOW/MED → ONE combined reviewer; HIGH → Code-Reviewer + Tester separately — V3C-78. **v3.3: reviewer countersigns 2 randomly-chosen rows of THIS checklist against the actual artifacts (anti self-attestation)** | review file(s) + countersign note | |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE — V3C-68/F15 | review file | |
| 5 | Tester fault-injection on the 1–2 most load-bearing behaviors: break → RED confirmed → reverted byte-identical (md5); every stay-GREEN fault got its mandatory new test — V3C-72/F5. **v4.0 (V4C-01, HIGH only, ADVISORY):** if a mutation runner is wired, mutant kill-rate on changed code recorded beside the verdict — never blocks | tester log + new test refs (+ kill-rate line at HIGH) | |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint (not a unit shim) — V3C-02 + V3C-73/F6 ("built ≠ wired") | test `file:line` | |
| 7 | New/changed security invariants added to the milestone invariants list with their NEGATIVE test — V3C-74/F7 | `security-invariants` row | |
| 8 | No `git checkout`/`restore` was run on uncommitted work this wave (reverts were in-place + hash-verified) — V3C-06/F17 | tester/reviewer attestation | |
| 9c | **Invariant hardening (v3.5, V3C-101 — origin FIX-03 cross-wave seam):** if this wave hardens a shared invariant (auth/tenancy/money), the producer list is enumerated FROM CODE (create/rotate/import/…) with a citing test per producer; missing tests recorded as tracked gaps; security sign-off on auth-class | producer list + test refs | |
| 9b | **Scope & checkpoint (v3.3, V3C-90/OD-4 — origin: F17 uncommitted-loss class + cross-wave honesty):** scope row appended — planned vs delivered vs deferred vs the signed plan (append-only); owner's labeled checkpoint commit exists for this wave (`wip(m{N}-w{W}): checkpoint — NOT reviewed`) | plan ref + commit sha | |
| 9a | **Economy (v3.2, V3C-85/86 — origin: DORA −7.2% on large changes; token-budget circuit breaker):** wave diff within ~≤400 changed lines OR variance noted (WARN, not block); projected token spend within the milestone budget line, else pause + variance note | diffstat + cost-log ref | |
| 9 | **Skipped/waived/BYPASSED ledger + run summary (v4.1, V4C-13 + V4C-40-lite — friction & spend telemetry):** first the RUN LINE — `gates run: <list> · gates SKIPPED: <list> · tokens/cost: <n> · outcome: <shipped|abandoned>` (a wave that burned budget and produced nothing is invisible in git otherwise — survivorship bias). Then: list every check that did NOT run this wave — legitimate skips (tier-down, N/A) AND pressure bypasses — one-line reason + rough cost (minutes) each. Bypasses are first-class EXPERIENCE findings; the SAME control bypassed 3× triggers review of the CONTROL, not just the people (field origin: HIGH/auth fix shipped unreviewed, support-phase psychology) | — | |

**Escaped-blocker tripwire (V3C-78):** if a blocker escapes a tiered-down (LOW/MED) wave, the
project reverts to full per-wave Code+Tester review until the next milestone closes clean.

Filled by: `<agent>` · Date: `<YYYY-MM-DD>` · Wave commit range: `<start>..<end>`
