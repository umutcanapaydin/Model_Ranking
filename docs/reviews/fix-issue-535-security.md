---
record_type: review
id: fix-issue-535-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Security Review — fix-issue-535

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need-branch` says `none`, and the owner asked for this seat because the change widens a privacy control's allowlist, D-180)
**Independent:** yes. I wrote neither the change nor the issue, and I have not reviewed this code before.
**Date:** 2026-10-31
**Release range:** 290557c..3ba886f (one commit, `3ba886f`)
**Reviewed head:** 3ba886f5db71a7e9aead15aa1820f5aa2d9e1020
**Risk tier:** MEDIUM (a privacy-gate allowlist entry; the brief declares no HIGH paths, `docs/project-brief.md:110`)

## Verdict
PASS

One exact entry, `"Date.<="`, is added to the standings sink's own list and nowhere else. It is a pure comparison of two
values. The gate is green in all four configurations for the right reason: without the entry it is red in all four, and
`unseen_permissions` holds the entry, because the entry is seen on the shipping client. The same toolchain move binds
the same operator in one other file, `KeptAnswers.swift`, which is not a sink and has no Foundation list. Nothing that
belongs on a list passes silently. No better-scoped remedy exists inside the gate's current model.

Worked in `/private/tmp/claude-501/-Users-umutcanapaydin-Desktop-ILGAR-model-ranking/cbf5c80e-9000-4990-acff-ddcfbf8972cf/scratchpad/sec-535`
at `3ba886f` (detached), with its own `.venv` (`make install`) and a copy of `advisor.db` (D-174). My probe
(`scratchpad/sec535-tools/facts.py`) lived outside the tree. It imported the gate, dumped each configuration's resolved
facts, and re-ran `problems()` with the entry removed in memory. No file in the tree was changed, and `git status` stayed
clean. Toolchain: `xcrun swiftc` from Xcode's default toolchain, Apple Swift 6.4.2 (swiftlang-6.4.2.1.9).

## Findings

### BLOCKING
- none

### MINOR
- none

### PASS
- scripts/client_decl_gate.py:1391-1393: the entry is harmless. `Foundation.Date.<=` compares two `Date` values,
  which are value types that hold a time interval. It reads no file, writes nothing, touches no shared state and reaches
  no network. The sink already lists `Date.init(` and `Date.timeIntervalSince` (:1390). Both call sites,
  `ios/ModelRanking/Engine/StandingsStore.swift:126` and `:148` (`fetchedAt <= now`), are unchanged since #288 and #314.
  The comment gives the reason and the ruling, as the #363 precedent does (:1371-1373).
- Scope: the entry sits in `SINK_FOUNDATION_ALLOWED["StandingsStore.swift"]` only, and the engine client's list
  (:1367-1386) is unchanged. `_sink_module_problem` (:3405) matches a symbol exactly, or as a dotted prefix of an entry.
  The new entry therefore admits only `Date.<=` itself and the bare `Date`, which `Date.init(` already admitted. It does
  not admit `Date.<` (that would need the prefix `Date.<.`), `Date.>=`, or any other member.
- The gate passes for the right reason. `make client-decls` at the head:
  `client-decls PASS: 23 client file(s) in 4 configuration(s) -- simulator, release: 3310; simulator, debug: 3315; device, release: 3310; device, debug: 3315`.
  With the entry removed from the list in memory, `problems()` reports
  ``StandingsStore.swift: `Foundation.Date.<=` is not on the list of Foundation declarations a privacy sink may reference``
  in all four configurations. With the entry present, `unseen_permissions()` returns `[]` in all four, and that check
  (:3157-3158) tests `Foundation.Date.<=` against the found facts. So if the binding moves back, the entry is reported
  as stale.
- Other comparisons in the sinks (all four configurations agree):
  - `StandingsStore.swift` binds `Foundation.Date.<=`, `Swift.Comparable.<` and `Swift.Comparable.>=`. The last two are
    the `TimeInterval` comparisons at :126 and :150. Neither is in `SINK_MODULES` or `SINK_SWIFT_REFUSED`.
  - `EngineClient.swift` has no `Date` operator. It binds only `Swift.Equatable.==`, `Swift.Int.<`, `Swift.Int.==`,
    `Swift.Int64.<=`, `Swift.Optional.==` and `Swift.String.==`.
  - No `Date.<`, `Date.>`, `Date.>=` or `Date.==` resolves to Foundation in either sink.
  - The toolchain move shows in one other file: `KeptAnswers.swift` binds `Foundation.Date.<=` at
    `ios/ModelRanking/Engine/KeptAnswers.swift:68`. That file is not in `SINK_FILES` (:327-330) or in
    `STORE_FOUNDATION_ALLOWED` (only `FrontDoor.swift`), so no Foundation list governs it, by design. The only
    Foundation references it has are `Date.<=` and `Date.timeIntervalSince`.
  - The sink-runs check (`SINK_RUNS_ALLOWED`) sees operators (it records `Swift.Equatable.==` for code a sink runs). It
    reports no `Foundation.Date.<=`, so the sink does not run `KeptAnswers.usable`.
- Remedy: the issue offers an alternative, mapping an operator's resolution to one allowance whichever module declares
  it. That would widen the control for every operator and every type. Rewriting the Swift source to dodge the binding
  would hide a control's subject. The list has no per-function granularity, so a one-member entry with its reason is the
  narrowest change available, and it matches the #363 precedent.
- The other changed file, `docs/process-log.md`, is prose only, with no secret or high-entropy string. The change adds
  no import or dependency.

## Gates passed
- [x] Secret scan green (`make secrets` at 3ba886f: "no leaks found", 23.26 MB scanned)
- [x] `make deps` (pip-audit) green: "No known vulnerabilities found"
- [x] `make slopsquat` green: "slopsquat PASS: 20 declared dependency(ies), 0 suspect" (no new import)
- [x] `conformance` green: "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)"
- [x] Default-deny preserved for new external surfaces (no new surface; the sink list widens by one exact, inert member)
- [x] Permission-matrix not violated (no destructive op, no hook, CI or workflow file touched)
- [x] Prompt-injection hygiene: not applicable (no external content consumed)
- [x] Auth/PII checks: not applicable (no auth, PII, payment or migration path; no HIGH path declared)
- [x] SAST: not applicable to a one-member data edit (no executable Python changed)

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #535 "a reviewed edit adds `Foundation.Date.<=` to `SINK_FOUNDATION_ALLOWED` with its reason" → scripts/client_decl_gate.py:1391-1393
- #535 "`make client-decls` green in all four configurations" → `make client-decls` at 3ba886f, PASS line quoted above (the issue's own red check, scripts/client_decl_gate.py:3608 `main`)
- the entry is held, not vacuous → scripts/client_decl_gate.py:3157-3158 (`unseen_permissions`: seen in all four), and scripts/client_decl_gate.py:3399-3409 (`_sink_module_problem`: red in all four without it)
- `<`, `>`, `>=`, `==` on Date need no entry → no Foundation `Date` operator other than `<=` is resolved in either sink (fact dump, all four configurations)

## Risks queued
- **R1** The issue says Xcode 27.2 (27B52) was unchanged since 2026-10-23, and the release Tester's `make check` passed
  this gate earlier the same day. The commit and the issue name no component that moved, so the cause of the rebinding
  is unexplained. This is not a security defect in the sink: the gate failed closed and was reviewed. But a privacy gate
  whose outcome moves with host state nobody recorded can move the other way too. Recording `xcrun swiftc --version`
  and the SDK build in the gate's PASS line would let the next move be traced. This fits as a follow-up issue, not this fix.
- **R2** Pre-existing, as the issue notes: CI does not run `client-decls`, so a toolchain-driven move like this one is
  caught only on a Mac session. This is unchanged by the branch.
