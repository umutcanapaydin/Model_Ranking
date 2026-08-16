---
record_type: fixpack
id: fixpack-template
status: draft
process_version: v5.0
date: 2026-08-12
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run,
     which is exactly what shipped in v4.3.1. -->
# Fixpack — {vX.Y.Z+1} (v4.0; V3C-98 + V4C-07/08 — Stage 5 Maintenance Loop; THE DEPLOY GATE)

> **Copy to `docs/fixpack-{N}.md`. Deploy is BLOCKED until every row is complete.** One page.
> A fix wave is a WAVE — the normal wave checklist + fresh-eyes bench apply (reference, not
> restated here). This doc adds only the fix-specific evidence and the owner's out-of-sandbox gate.
> **Caps:** ≤5 fixes OR ~400 net changed lines; a HIGH/⛔ fix ships in a pack of ONE.
> **Scope rule:** a fix wave only turns a red test green — never new behavior.

## Header

- Pack ID: `fixpack-{N}` · Version: `{vX.Y.Z+1}` (stamped into `/health` build)
- Date: `<...>` · Deploy target: `<...>` · Emergency? `<no | YES + "why this can't wait": ...>`
- Surface tags: `<module/file-cluster per fix — feeds the N=3 fix-on-fix counter>`
- Migration status: `<NONE | migration ID + reversibility note; irreversible ⇒ roll-forward plan>`
- Rollback plan: previous image `<tag>` retained · rollback command: `<written out>`
- Expected post-deploy health signals: `<which probes change, which must stay flat>`

## Fixes (one row each — every cell is a referent, not a claim)

| # | Bug ref | Exploitable? | Red test (permanent, tagged) | Fix commit | Tier | CR | Tester | Gate that should have caught it + lesson (1 line → EXPERIENCE) |
|---|---|---|---|---|---|---|---|---|
| 1 | `<link>` | `<no/YES→escalated>` | `<test file:name>` | `<sha>` | `<L/M/H>` | `<PASS ref>` | `<PASS ref>` | `<gate: ... / lesson: ...>` |

## Security floor (unconditional)

- [ ] gitleaks + SCA on the pack commits — clean
- [ ] **Full security-invariant negative suite GREEN** on the final bundled build
- [ ] Diff-scoped security read done (reachable diff, not just changed lines) — `<ref>`
- [ ] ⛔-glob intersection: `<none | YES → full HIGH review + owner line-by-line done>`
- [ ] built≠wired re-checked on touched/mediating controls

## Test bar

- [ ] Every red test added to the PERMANENT regression suite (bug-ID tagged)
- [ ] Affected-flow E2E per fix (Tester-defined scope)
- [ ] **Full regression GREEN once on the exact final bundled build** — `<run ref>`
- [ ] LOW-tier valve applied? `<no | yes: combined reviewer; owner verify batched at pack level>`

## Owner out-of-sandbox verification (BLOCKING — no signature, no deploy)

*(In the owner's REAL local environment — outside any sandbox.)*

| # | Reproduced original bug on PRE-fix build ✓ | Symptom GONE on fixpack build ✓ | Notes |
|---|---|---|---|
| 1 | `<✓ + repro steps used>` | `<✓>` | |

- [ ] Local `make test` + pack smoke list run on owner machine — summary: `<...>` · build hash verified: `<hash>`
- **Owner signature:** `<initials / date>`

## Deploy & watch (rides Stage 4.3 + these)

- [ ] 4.3 gate passed (new SHA live via /health; restart ≠ rebuild)
- [ ] **Fix probe:** each previously-broken behavior exercised in prod — new behavior confirmed
- [ ] ~~**v3.5 (V3C-106):** `make journey URL=<deployed>` re-run green after the pack lands ~~ — **REMOVED at the v5 control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything.
- [ ] Watch window `<30–60 min; longer for HIGH>` clean — errors/logs flat → pack CLOSED
- [ ] **v4.0 (V4C-07):** scheduled journey run confirmed ACTIVE post-pack (same script, on cadence, named on-call owner, flake/mute policy; result lands in this watch record) — monitoring-as-code, not a one-shot
- [ ] **v4.0 (V4C-08, stack-conditional):** if the platform supports canary/pre-post verify, the pack rode it; note: *a rollback that has never fired is a doc, not a control* — rollback rehearsed once per supported stack: `<date/ref | N/A + why>`
- [ ] If emergency: deferred steps listed + **48h retroactive full close** scheduled: `<items + deadline>`

## Capture coupling (deploy condition — the mechanical harvest)

- [ ] The per-fix lesson lines above are APPENDED to `docs/EXPERIENCE.md` (dated, pack-ID keyed)
- [ ] 3-strikes check: `<any gate at 3 misses within 2 packs? → gate-change proposal required>`
- [ ] Fix-on-fix check: `<any surface at N=3? → surface LOCKED, refactor milestone required>`
