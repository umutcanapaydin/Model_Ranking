# External Skills — reference copies from obra/superpowers

> Captured 2026-05-27 from `https://github.com/obra/superpowers` (v5.1.0) via Claude in Chrome.
> These are NOT bundled / activated for our agent. They are reference material for the D-A pipeline draft and for the M6 subagent-dispatch experiment.

## Why these are in the repo

We reviewed `obra/superpowers` and `automazeio/ccpm` as part of the 2026-05-27 source review (see `docs/process-log.md` S20-bis when added). The user explicitly asked for the code-review skill; three more skills were captured at the same time because they form the same workflow cluster and we will likely adapt them in M6.

## What we captured

| File | Source path in obra/superpowers | Why we kept it |
|---|---|---|
| `requesting-code-review.md` | `skills/requesting-code-review/SKILL.md` | User-requested. Two-stage review pattern (spec compliance + code quality). Relates to our seed E.4 candidate and closure-checklist §A. |
| `subagent-driven-development.md` | `skills/subagent-driven-development/SKILL.md` | Core pattern we want to try in M6 (Insight workflow). Per-task fresh subagent + two-stage review + continuous execution without human checkpoints. |
| `using-git-worktrees.md` | `skills/using-git-worktrees/SKILL.md` | Required dependency of subagent-driven-development. Detect-then-create isolation pattern. |
| `writing-plans.md` | `skills/writing-plans/SKILL.md` | Their version of our 5-line AGENTS.md §3.2 rule, fleshed out with task templates (2-5 min granularity, TDD step structure). |

## How to use these

These files are **read-only reference**:

- **Do not** activate them as our project skills (we have our own AGENTS.md + playbook-seeds.md).
- **Do** read them when designing M6+ workflows where we want to try parallel subagent execution.
- **Do** cite them in process-log entries or seeds when adopting their patterns (e.g. "follows superpowers `subagent-driven-development` pattern" or "adapted from superpowers `writing-plans` task structure").

## License attribution

`obra/superpowers` is MIT-licensed. Re-distribution as reference copies inside this repo is allowed under that license. See `https://github.com/obra/superpowers/blob/main/LICENSE`.

## When to refresh

These files are pinned to `superpowers v5.1.0` captured on 2026-05-27. To refresh:

1. Re-fetch each SKILL.md from the same paths.
2. Diff against the captured version.
3. Update this README's "captured" date if any file changed.

## What we are NOT taking

- The full Superpowers harness / plugin install — we have our own house rules (AGENTS.md) and don't want two competing systems.
- The complete 13-skill set — we picked the 4 relevant to our current trajectory.
- The brainstorming / TDD / debugging skills — our existing discipline (numbered REQ-IDs, ADRs, closure-checklist, playbook-seeds) already covers these spaces in a project-tailored way.
