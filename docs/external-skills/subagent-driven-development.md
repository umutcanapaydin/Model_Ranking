# subagent-driven-development

> Reference copy from `obra/superpowers` v5.1.0 (`skills/subagent-driven-development/SKILL.md`), captured 2026-05-27.
> See `docs/external-skills/README.md` for context. Read-only — do not activate as our project skill.

---

**name:** subagent-driven-development
**description:** Use when executing implementation plans with independent tasks in the current session

## Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.

## When to Use

```
Have implementation plan? → Tasks mostly independent? → Stay in this session?
                                                       → YES: subagent-driven-development
                                                       → NO (parallel session): executing-plans
                                       → NO (tightly coupled): Manual execution or brainstorm first
                          → NO: Manual execution or brainstorm first
```

vs. **Executing Plans** (parallel session):

- Same session (no context switch)
- Fresh subagent per task (no context pollution)
- Two-stage review after each task: spec compliance first, then code quality
- Faster iteration (no human-in-loop between tasks)

## The Process

**Per Task:**

1. Dispatch implementer subagent (`./implementer-prompt.md`)
2. If implementer asks questions → answer, re-dispatch
3. Implementer implements, tests, commits, self-reviews
4. Dispatch spec reviewer subagent (`./spec-reviewer-prompt.md`)
5. If spec reviewer finds gaps → implementer fixes, re-review
6. Dispatch code quality reviewer subagent (`./code-quality-reviewer-prompt.md`)
7. If code quality reviewer finds issues → implementer fixes, re-review
8. Mark task complete in TodoWrite

**Outer loop:**

- Read plan, extract all tasks with full text, note context, create TodoWrite
- For each task: run per-task process
- After all tasks: dispatch final code reviewer for entire implementation
- Use `superpowers:finishing-a-development-branch`

## Model Selection

Use the least powerful model that can handle each role to conserve cost and increase speed.

**Mechanical implementation tasks** (isolated functions, clear specs, 1-2 files): use a fast, cheap model. Most implementation tasks are mechanical when the plan is well-specified.

**Integration and judgment tasks** (multi-file coordination, pattern matching, debugging): use a standard model.

**Architecture, design, and review tasks:** use the most capable available model.

**Task complexity signals:**

- Touches 1-2 files with a complete spec → cheap model
- Touches multiple files with integration concerns → standard model
- Requires design judgment or broad codebase understanding → most capable model

## Handling Implementer Status

Implementer subagents report one of four statuses. Handle each appropriately:

**DONE:** Proceed to spec compliance review.

**DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If the concerns are about correctness or scope, address them before review. If they're observations (e.g., "this file is getting large"), note them and proceed to review.

**NEEDS_CONTEXT:** The implementer needs information that wasn't provided. Provide the missing context and re-dispatch.

**BLOCKED:** The implementer cannot complete the task. Assess the blocker:

- If it's a context problem, provide more context and re-dispatch with the same model
- If the task requires more reasoning, re-dispatch with a more capable model
- If the task is too large, break it into smaller pieces
- If the plan itself is wrong, escalate to the human

Never ignore an escalation or force the same model to retry without changes. If the implementer said it's stuck, something needs to change.

## Prompt Templates

(Source repo contains these; not captured here.)

- `./implementer-prompt.md` — Dispatch implementer subagent
- `./spec-reviewer-prompt.md` — Dispatch spec compliance reviewer subagent
- `./code-quality-reviewer-prompt.md` — Dispatch code quality reviewer subagent

## Advantages

vs. **Manual execution:**

- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)
- Subagent can ask questions (before AND during work)

vs. **Executing Plans:**

- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Efficiency gains:**

- No file reading overhead (controller provides full text)
- Controller curates exactly what context is needed
- Subagent gets complete information upfront
- Questions surfaced before work begins (not after)

**Quality gates:**

- Self-review catches issues before handoff
- Two-stage review: spec compliance, then code quality
- Review loops ensure fixes actually work
- Spec compliance prevents over/under-building
- Code quality ensures implementation is well-built

**Cost:**

- More subagent invocations (implementer + 2 reviewers per task)
- Controller does more prep work (extracting all tasks upfront)
- Review loops add iterations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**

- Start implementation on main/master branch without explicit user consent
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make subagent read plan file (provide full text instead)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance (spec reviewer found issues = not done)
- Skip review loops (reviewer found issues = implementer fixes = review again)
- Let implementer self-review replace actual review (both are needed)
- Start code quality review before spec compliance is ✅ (wrong order)
- Move to next task while either review has open issues

## Integration

**Required workflow skills:**

- `superpowers:using-git-worktrees` — Ensures isolated workspace (creates one or verifies existing)
- `superpowers:writing-plans` — Creates the plan this skill executes
- `superpowers:requesting-code-review` — Code review template for reviewer subagents
- `superpowers:finishing-a-development-branch` — Complete development after all tasks

**Subagents should use:**

- `superpowers:test-driven-development` — Subagents follow TDD for each task

**Alternative workflow:**

- `superpowers:executing-plans` — Use for parallel session instead of same-session execution
