# Subagent profiles

Four profiles ship. Each file says in its own header when it fires and what it must not do; this
file does not repeat that, because a table restating four headers is a fifth copy that goes stale.

| profile | fires |
|---|---|
| `Code-Reviewer.md` | per wave, after the wave's code is written |
| `Tester.md` | per wave, after Code-Reviewer clears |
| `Security-Reviewer.md` | once per milestone, at closure, BLOCKING before any deploy |
| `Explorer.md` | read-only, any time exploration would touch more than three files |

The first three are mandatory (P-004, which supersedes D-005's composition). The Explorer is
mandatory for the exploration it names and optional otherwise.

**The one rule that makes any of them work: a reviewer never reviews its own code** (K.7). Dispatch
a fresh subagent. This was the fourth-most reproduced finding across nine projects, and it is the
only thing here with no mechanical enforcement — nothing can tell whether the subagent you
dispatched wrote the wave.

## Adding a profile

A new profile is CANDIDATE until all four hold:

1. used in ≥2 milestones,
2. caught ≥1 BLOCKING or MINOR,
3. a retrospective marked it PULLED-WEIGHT,
4. the owner approved graduation, with an ADR.

Two profiles caught 24 cycles of issues in Phase-1 with no role profiles at all, using bar-explicit
prompts. A profile earns its place by adding a *lens* — security asks different questions than code
review — never as ceremony. Do not ship a dozen profiles against a future need; the consortium that
designed this looked at frameworks shipping 12 to 21 and declined.

**Retirement is the same discipline running backwards**, and it is the half people skip: a profile
that has not fired in 90 days comes out at the quarterly handover. The `cycle-close` skill asks.

## Dispatch anti-patterns

- Dispatching Code-Reviewer to the subagent that wrote the code — no fresh eyes, and the whole
 gate collapses to self-assessment.
- Running Security-Reviewer before the per-commit gate is green. It is a second pass, not the first.
- Editing a profile mid-milestone. Profiles are governed; a change needs an ADR.
