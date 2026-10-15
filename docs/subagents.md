# Subagent profiles

Four profiles ship. Each file says in its own header when it fires and what it must not do; this
file does not repeat that, because a table restating four headers is a fifth copy that goes stale.

| profile | fires |
|---|---|
| `Code-Reviewer.md` | heavy mode: every wave close; a fix when `make review-need` says `code-reviewer` |
| `Tester.md` | once per milestone close, in either mode — heavy: at the plan's last wave close (`/close-wave`); light: before a release, on everything merged since its last verdict (`docs/reviews/release-tester.md`; the release row in `docs/closure-checklist.md` §E.1 cites it) |
| `Security-Reviewer.md` | either mode: a wave or fix when `make review-need` says `security`; before every deploy (the deploy gate refuses without it); the release at Stage 5.1 — verdict before a deploy in `docs/reviews/release-security.md` |
| `Explorer.md` | read-only, any time exploration would touch more than three files |

The first three are mandatory (D-005 in `docs/decisions.md`). The Explorer is mandatory for the
exploration it names and optional otherwise.

**The one rule that makes any of them work: a reviewer never reviews its own code** (K.7). Dispatch
a fresh subagent. It is the one rule here with no mechanical enforcement — nothing can tell
whether the subagent you dispatched wrote the wave.

A reviewer run by a second agent tool (AGENTS.md §2a) leaves no dispatch record and no
transcript. Its verdict file is recorded by the human who merges the PR, and says so.

## Adding a profile

A new profile is CANDIDATE until all four hold:

1. used in ≥2 milestones,
2. caught ≥1 BLOCKING or MINOR,
3. its verdicts changed what shipped at least once (a finding that was fixed),
4. the owner approved graduation, with an ADR.

A profile earns its place by adding a *lens* — security asks different questions than code review —
never as ceremony. Do not ship a dozen profiles against a future need.

**Retirement is the same discipline running backwards**, and it is the half people skip: a profile
that has not fired by the end of the work comes out in the diet. The `cycle-close` skill asks.

## Dispatch anti-patterns

- Dispatching Code-Reviewer to the subagent that wrote the code — no fresh eyes, and the whole
  gate collapses to self-assessment.
- Running Security-Reviewer before the per-commit gate is green. It is a second pass, not the first.
- Editing a profile mid-milestone. Profiles are governed; a change needs an ADR.
