# HANDOVER — v3.4 provenance material (2026-07-17)

> Append-only provenance for the v3.4 increment, following `HANDOVER-v3.3-material.md`.
> Full record: `General_Pipeline/v3.4-ratification.md` · register **Increment 8**.

## Source

**Owner directive OD-6:** post-deployment bug fixing becomes a GP discipline. Field basis:
HCS MaaS (the first GP production project) accumulated **~5 fix deployments + numerous bugs after
go-live**, handled ad-hoc — GP's stages previously ended at go-live. Evidence is VERBAL; the
uploaded EXPERIENCE file was md5-identical to the interim for the THIRD time. That repeated
capture failure became the council's central finding.

## Council

5 seats blind-parallel (QM, SRE, Security, SW, Skeptic); chair synthesis under the established
delegation pattern. Convergent; the Skeptic's hard objection ("the real failure is capture, not
machinery") was accepted and shaped the cut: **capture is now mechanical** (fixpack lessons append
to EXPERIENCE.md as a deploy condition) and **the standalone memory-based harvest session is
RETIRED** — a real retirement in exchange for the new stage.

## What v3.4 adds

**Stage 5 — Maintenance Loop** (V3C-98; written as reuse — a fix wave IS a wave). Three genuinely
new elements: red-test intake (the failing test is the frozen spec; fixes only turn red tests
green), the **fixpack** (`docs/fixpack.template.md` — release unit AND deploy gate: caps, security
floor, full regression on the bundle, migration/rollback plan, fix probe + watch window, emergency
path with never-skipped floor + 48h retro-close debt), and the **owner's out-of-sandbox
verification** (BLOCKING: reproduce pre-fix → gone post-fix → local tests → sign). Plus:
3-strikes gate-attribution → gate-change proposal; N=3 fix-on-fix → surface locks, refactor via a
normal milestone. P-008 ADR; closure-checklist §D.

## Caveats for the next maintainer

1. **All thresholds are pre-field:** caps (≤5/~400), watch windows (30–60 min), N=3, 3-strikes,
   >1 emergency/month — tune after 3 real fixpacks (P-008 revisit clause).
2. **The capture coupling is the point.** If fixpack→EXPERIENCE appending gets skipped in
   practice, v3.4 added ceremony while leaving the observed failure untouched — it is
   deploy-blocking for exactly this reason. Watch it.
3. **Owed:** the HCS post-prod WRITTEN harvest (bug list, root causes, gate attributions — the
   first real fix-rate dataset) · the v3.1 retirement count at the first v3.3+ project retro
   (now two versions overdue; must not slide again).
4. **Repair note:** the `## §0 — Changelog` heading in `pipeline-design.md` was accidentally
   consumed during the v3.3 cut (content intact, heading lost); restored in v3.4. The v3.3
   package retains the defect per the never-edit-prior-versions rule.
5. **Deck not regenerated** (owner rule). `GP-v3-presentation.html` still describes v3.
