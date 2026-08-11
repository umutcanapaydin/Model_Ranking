# HANDOVER — v3.1 provenance material (2026-07-03)

> Append-only provenance for the v3.1 increment, following `HANDOVER-v3-material.md`.
> Full decision record: `General_Pipeline/v3.1-ratification.md` · candidates:
> `General_Pipeline/v3-candidate-register.md` **Increment 4**.

## Source

ONE project — but a special one: **hcs_maas_vib** (HCS MaaS control plane; FastAPI wrapping
One API [MIT, pinned SHA]; M0–M4 closed, 171 tests, 23 agent sessions) is the **first project
executed ON GP v3 itself**. Its 19 findings split into (a) field validation of the v3 adopt set —
all 6 bumps confirmed, five sharpened, none contradicted — and (b) new candidates V3C-69..81.
**Interim harvest:** the project was unfinished (through M4); a final re-harvest is owed at
project close. Plus two owner directives: OD-1 (living EXPERIENCE.md) and OD-2 (executable
wave/milestone checklists), ratified for weight/placement per the V3C-68 precedent.

## Council

11 voting seats + non-voting chair, blind-parallel, 2026-07-03 (Frontend + Cloud sat out —
owned no candidates; council-design §7). Splits S1–S4 settled by the owner same day:
no new gate (reserve preserved) · money rule adopted domain-scoped · customer-view generator
deferred · EXPERIENCE freshness BLOCKING at handover.

## What v3.1 adds (all placements in this package)

- `docs/wave-checklist.template.md` (V3C-69) — filled+committed per wave close; evidence-referent
  rows; skipped/waived ledger; accretion valve.
- `docs/EXPERIENCE.template.md` (V3C-81) — living per-project experience doc; closure-checklist
  line; quarterly-handover skill now BLOCKS without a fresh dated entry.
- `subagent-profiles/Tester.md` — fault-injection protocol (V3C-72, fused with the F17
  revert-in-place rule).
- Risk-tiered review depth (V3C-78) amending V3C-68 — design §0, P-005 ADR, wave-checklist row 1/3;
  with the escaped-blocker tripwire and the security auto-escalation rubric.
- `docs/security-baseline.md` §v3.1 — built≠wired (V3C-73), security-invariant negative tests
  (V3C-74), idempotency different-payload pattern (V3C-75), money integer-minor-units
  (V3C-77, domain-scoped), plus the B1/B2/B3 sharpenings.
- `docs/license-review.template.md` — consumption-posture field (V3C-71, folded into V3C-70's
  day-0 sign-off).
- `.agents/rules/practices.md` §v3.1 — hermetic gate recipe (B5), in-place revert rule (B6).
- retrospect skill — carried-question slot (V3C-79; buckets + retired count already existed).
- `★ v3.1 RATIFIED` seed block in `playbook-seeds.md` (append-only) + P-005 in `docs/decisions.md`.

## Caveats for the next maintainer

1. **Self-validation cap (council-design §5.6 amendment):** "validates-GP" evidence from projects
   run ON GP cannot alone escalate anything past template weight. This batch was one project, one
   org, one gateway family — the seats named it (4 of 11 independently).
2. **Gateway-family contamination:** hcs_maas_vib wraps One API → its gateway findings corroborate
   the Agent-Native/LLM-Ops theme but are NOT the awaited 2nd independent ecosystem. Theme stays
   candidate; V3C-46 sharpened (settle() + durable-intent journal) awaiting real independence.
3. **Owed:** final hcs_maas_vib re-harvest at project close; v3.2's retro must report the retired
   count of v3.1's OWN additions (accretion-cap promise); V3C-76 promotes fast on a 2nd ecosystem.
4. **Deck not regenerated** (owner rule: only on request). `GP-v3-presentation.html` still
   describes v3; update when asked.
