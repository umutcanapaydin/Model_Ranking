# Subagent Profiles (Pipeline v3)

> **v3 change (V3C-68).** The **per-wave** fresh-eyes gate is now **Code-Reviewer + Tester** (Stage 3a + 3b). The **Security-Reviewer** moved out of the per-wave gate to **milestone closure (Stage 4.0)**, where it is **BLOCKING before the deploy/go-live step**. Each implementing agent also runs a per-agent **dev-test loop** during the wave (Stage 2). Baseline templates ship pre-filled; Stage 1 milestone planning may override the source.

---

## Current profiles (MANDATORY per D-005)

| Profile | When it fires | Skill invocation | Source baseline | Override at plan? |
|---|---|---|---|---|
| `Code-Reviewer.md` | **Stage 3a**, after every wave | `/review` skill | superpowers `requesting-code-review.md` + K.7 pattern | YES (Stage 1 §"Subagent profile source") |
| `Tester.md` ★ NEW v3 | **Stage 3b**, after Code-Reviewer passes (per wave) | the Tester profile via the test-and-commit / repo-review surface | V3C-68 + V3C-02 + E.5; K.7 fresh-eyes | YES (same) |
| `Security-Reviewer.md` | **Stage 4.0** (milestone closure, BLOCKING before deploy) — moved from per-wave in v3 | `/security-review` skill | F.6/F.7/F.8 + Lovable + Replit lessons + `docs/security-baseline.md` (V3C-11/12/13/51/56) | YES (same) |

| `Explorer.md` ★ NEW v3.2 | any time exploration is needed (pre-plan sweeps, "where is X handled"); MANDATORY for >3-file exploration | dispatched by the controller with a named deliverable | V3C-85; read-only; ≤2k-token summary cap | YES (same) |

These three profiles (+ the read-only Explorer) are the mandatory profiles in v3. Other profiles (Architect, Docs-Writer, Migration-Specialist, etc.) are project-specific and may be added on a milestone-by-milestone basis as CANDIDATE.

**Why Security moved (V3C-68):** reviewing the whole milestone's surface once gives more context and fewer redundant passes (security 1×/milestone vs ×waves), and it is safe because **nothing ships mid-milestone** — waves don't deploy, so the closure security review always precedes any go-live. Always-on catastrophe-class guardrails (no committed secrets, no destructive ops) still apply during every wave. A wave that touches auth/PII/payment/crypto/migration MAY pull a security pass forward (HIGH-risk trigger, permission-matrix); the closure review still runs regardless.

---

## Stage 1 source-choice flow

At the start of each milestone, the plan (`docs/plans/m{N}-plan.md`) must declare the source for each profile:

```
## Subagent profile source (this milestone)
Code-Reviewer:    A
Tester:           A
Security-Reviewer: A
(Custom profile additions, if any:)
```

Source options:
- **A. Superpowers SKILL baseline.** Use the profile as-shipped (default; lowest friction).
- **B. Claude generate fresh.** Have Claude write a milestone-specific profile from scratch. Use when domain is unusual.
- **C. Codex generate fresh.** Same prompt to OpenAI Codex. Use for A/B test or when working on Codex platform.
- **D. Mix per profile.** E.g., Code-Reviewer: A (baseline), Security-Reviewer: B (Claude fresh).

If source is B/C/D, regenerate the profile file at `subagent-profiles/m{N}/<Profile>.md` before Stage 2 wave dispatch. Plan records the override + rationale + generation prompt.

---

## When to add a new profile (L' — CANDIDATE per playbook-seeds.md)

A new profile graduates from CANDIDATE to mandatory only when:
1. Used in ≥2 milestones successfully
2. Catches ≥1 BLOCKING or MINOR
3. G.12 retrospective marks `PULLED-WEIGHT`
4. User approves graduation via `playbook-seeds.md` update + new ADR (D-NNN)

Phase-1 lesson (K.4 / K.6): generic subagents with bar-explicit prompts caught 24 cycles of issues without role profiles. Role profiles are useful when they add a specific lens (security has different concerns than code review) — not as ceremony.

Anti-pattern (from consortium): Don't ship 12-21 BMAD-style profiles "just in case." Two profiles are enough until evidence demands more.

---

## Anti-patterns of profile dispatch

- ❌ Dispatching Code-Reviewer for the same subagent that wrote the code (no fresh-eyes; defeats K.7)
- ❌ Letting Security-Reviewer review WITHOUT the per-commit gate already passing (Security-Reviewer is a second pass, not the first)
- ❌ Adding profiles "just in case" — earn promotion via ≥2 milestones of PULLED-WEIGHT
- ❌ Editing a profile mid-milestone without an ADR (profiles are governed; not free-form)

---

## Invocation via skills (v3)

The mandatory profiles are invoked via skills / surfaces:
- `/review` skill (in `.claude/skills/repo-review/`) loads Code-Reviewer.md content + runs review (Stage 3a, per wave)
- the **Tester** profile drives the wave's tests red→green (Stage 3b, per wave) via the `/test-and-commit` + `/repo-review` surfaces
- `/security-review` skill (a Claude Code built-in, wrapped by our profile content) runs at **Stage 4.0 milestone closure**, BLOCKING before deploy

The skill is the INVOCATION SURFACE; the profile is the CONTENT. Consortium decision (Q-resolution): our profiles wrap built-ins; built-ins are not used standalone.
