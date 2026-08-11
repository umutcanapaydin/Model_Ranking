# HANDOVER — v3.3 provenance material (2026-07-05)

> Append-only provenance for the v3.3 increment, following `HANDOVER-v3.2-material.md`.
> Full record: `General_Pipeline/v3.3-ratification.md` · register **Increment 6**.

## Source

**Owner directive OD-4** (2026-07-05, fully delegated to the chair): "human review between
milestones, not between waves; each wave is tested and those tests fix things already — my local
tests and make-test runs happen at each milestone." Plus the **closure of the hcs_maas_vib final
harvest**: the closing EXPERIENCE file arrived md5-identical to the Increment-4 interim — the
project ended at M4, the interim WAS final, zero new findings, obligation CLOSED.

## Council

7 seats blind-parallel (6 core + AgentOps), all decisions by the chair as the owner's delegated
proxy. Convergent shape; one genuine split (commit mechanics) chair-ruled: owner keeps ALL git
authorship via ~30s labeled checkpoint commits per wave — the never-touch-git rule stands, and
**commit authorship is the bright line: an agent commit on main = A1 = explicit owner ADR.**

## What v3.3 changes

One thing, wired deeply: **operating mode A0.5 (ACTIVE — PROVISIONAL)**. Waves close agent-side
(fresh-eyes reviews per tier, green checks pinned to the closing tree, committed evidence-cited
checklist, HIGH-tier pulled-forward security pass); the owner runs a capped, time-boxed milestone
session (report + per-wave diffs + his own tests + the commits). Escalate-NOW list; assumption
ledger activated; per-wave table + decisions-on-your-behalf + fix-rate-baseline line in the
closure report; reviewer countersign; semantic-security items; milestone cap ~4–6 waves/~2k lines;
automatic reversion tripwire. Retired: the owner-per-wave review/test/sign-off lines (net down).

## Caveats for the next maintainer

1. **A0.5 is PROVISIONAL on single-project evidence.** The Skeptic's dissent is recorded in the
   ratification: the "owner wave passes added little" premise comes from ONE project, and the
   owner reversed his own 48-hour-old ruling. The tripwire is the answer — it must actually be
   honored: first escaped blocker an owner wave-pass would plausibly have caught → wave cadence,
   automatically, no debate. A0.5 earns permanence only by surviving two milestones on the NEXT project.
2. **The fix-rate-vs-baseline line in the closure report is the falsifier.** If it can't be
   computed (no baseline data), say so in the report — don't fake it.
3. **Standing obligations carried:** v3.2 retro owes the v3.1 retired-count report; Agent-Native
   theme still awaits a 2nd independent ecosystem; A1/A2 remain NOT active (north star only).
4. **Deck not regenerated** (owner rule). `GP-v3-presentation.html` still describes v3.
