# HANDOVER — v3.5 provenance material (2026-07-27)

> Append-only provenance for the v3.5 increment, following `HANDOVER-v3.4-material.md`.
> Full record: `General_Pipeline/v3.5-ratification.md` · register **Increment 9**.

## Source — the best evidence GP has ever had

`POST-PROD-FIX-HARVEST_hcs_maas_vib.md`: 7 defects AFTER "build complete" (9/9 milestones, all
gates green) on a customer-operated, air-gapped Huawei CCE cluster with a partner-owned build
pipeline. **Zero caught by automated gates; 100% boundary defects** (code↔own-config,
code↔packaging, wave-seam, code↔human, tooling↔reality, process↔phase-shape). 563 unit tests were
CORRECTLY green. Bonus validation: the field team independently derived the fixpack shape
(F33/DEP-3) without seeing v3.4 — the strongest convergence GP has recorded.

## Council

5 seats blind-parallel (SRE, Skeptic, QM, Security, DevOps); chair decided under owner delegation.
Notable rulings: V3C-106 demoted from mandatory to default-expected (a "mandatory deliverable" is
a gate in a trenchcoat); V3C-104 split (grep line now, format at second partner); V3C-102 narrowed
to its two mechanical rules; V3C-107 added mid-council by the DevOps seat. **Skeptic's dissent on
record: two cuts in one week is justified once (new evidence class) and is NOT precedent.**

## What v3.5 adds (all placements — net new package files: 0)

check-templates + cold-start make targets & §B.3 rows (V3C-99) · human-path criterion (V3C-100) ·
producer enumeration with verdict section + security sign-off (V3C-101) · never-parse-bounded-
prefix + revision stamps (V3C-102n) · ready≠alive + channel-constrained diagnosable fail-closed
(V3C-103) · boundary-grep delivery line (V3C-104s) · artifact-bound cadence rebind (V3C-105) ·
journey tester as default-expected deliverable with QM bar + Security custody (V3C-106) ·
boot-prerequisite ownership rule (V3C-107). P-009 ADR.

## Caveats for the next maintainer

1. **Single-project, single-stack dataset** (FastAPI/Postgres/k8s, one partner). The stack-
   conditional phrasings ("where persistence exists", "where the platform distinguishes") are
   deliberate — don't harden them into universals until a second stack reports.
2. **The Makefile targets are guidance stubs** — each project wires check-templates/cold-start/
   journey to its own settings module and datastore. The CI job spec is template-owned; projects
   override env only.
3. **V3C-106 rot risk:** if the journey script decays into a smoke ping or becomes advisory, it's
   dead by Q4 (QM). It gates 4.3 and every fixpack, and skips are recorded.
4. **Still owed:** the project's EXPERIENCE.md rev 4 (narrative F32–F40) for the archive · the
   v3.1 retirement count at the first v3.3+ retro · V3C-104 full format awaits a second partner.
5. **Deck not regenerated** (owner rule).
