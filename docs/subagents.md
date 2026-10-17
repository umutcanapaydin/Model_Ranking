# Subagent profiles

Four profiles ship. Each file says in its own header when it fires and what it must not do; this
file does not repeat that, because a table restating four headers is a fifth copy that goes stale.

| profile | dispatched by |
|---|---|
| `Code-Reviewer.md` | `/close-wave`, `/fix-issue` |
| `Tester.md` | `/close-wave` (heavy), `/going-live` (light) |
| `Security-Reviewer.md` | `/close-wave` (heavy), `/fix-issue` and `/work-enhancement` (light), `/going-live` (both) |
| `Explorer.md` | any session, when exploration would touch more than three files |

When each fires, per mode: `.agents/rules/issues.md`, "Two working modes".

The first three are mandatory (D-005 in `docs/decisions.md`). The Explorer is mandatory for the
exploration it names and optional otherwise.

**The one rule that makes any of them work: a reviewer never reviews its own code** (K.7). Dispatch
a fresh subagent. It is the one rule here with no mechanical enforcement — nothing can tell
whether the subagent you dispatched wrote the wave.

A reviewer run by a second agent tool (`.agents/rules/two-tools.md`) leaves no dispatch record and no
transcript. Its verdict file is recorded by the human who merges the PR, and says so.

## Why the profiles read what they read

A profile is loaded on every spawn, so it carries the rule and one clause of why; the evidence lives
here, read by the owner, not by each reviewer.

- **Tester once per milestone, not per wave.** In the field the per-wave Tester was the costliest
  review per real defect (41M and 57M tokens, against 1.9M–5.2M for the Code-Reviewer); four Tester
  verdicts in a row in one wave were BLOCKING on unproven behaviour, never on a defect, and the one
  real defect would have surfaced three waves later anyway (D-005).
- **Security at computed moments.** The highest-yield review per token (0.6M–2.4M tokens per real
  fix), and the one agents skipped when it was left to them. Heavy mode ran it per wave until the
  owner's ruling of 2026-10-16 moved it to the milestone's last wave. External context the profile
  used to quote: Veracode 2025 (45% of AI-generated code with an OWASP Top 10 flaw), Lovable
  CVE-2025-48757 (PII exposed across 170 of 1,645 apps), and Replit's database deleted through a
  "code freeze".
- **AI-generation smells in the Code-Reviewer.** GitClear measured eight times more duplicated blocks
  in AI-assisted code; CodeRabbit 1.7 times more issues per change.
- **What each profile is handed:** named sections instead of whole files — the Code-Reviewer
  two sections of `practices.md` and only the cited ADRs, the Security-Reviewer four sections of
  `permission-matrix.md` and four gate result lines instead of the gate's whole log (about 2.5k
  tokens per spawn each). A reviewer may still open anything; the dispatch says where to start.

## Adding a profile

A new profile is CANDIDATE until all four hold:

1. used in ≥2 milestones,
2. caught ≥1 BLOCKING or MINOR,
3. its verdicts changed what shipped at least once (a finding that was fixed),
4. the owner approved graduation, with an ADR.

A profile earns its place by adding a *lens* — security asks different questions than code review —
never as ceremony. Do not ship a dozen profiles against a future need.

**Retirement is the same discipline running backwards**, and it is the half people skip: a profile
this project added that has not fired by the end of the work comes out in the diet; one DevFlow ships
is reported upstream instead (`make install-check` counts them). The `cycle-close` skill asks.

## Dispatch anti-patterns

- Dispatching Code-Reviewer to the subagent that wrote the code — no fresh eyes, and the whole
  gate collapses to self-assessment.
- Running Security-Reviewer before the per-commit gate is green. It is a second pass, not the first.
- Editing a profile mid-milestone. Profiles are governed; a change needs an ADR.
